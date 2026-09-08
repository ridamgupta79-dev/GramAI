"""Dashboard API — runs all specialist agents and returns a unified payload."""
from __future__ import annotations

import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.specialists import AiMentorAgent, run_all_agents
from app.api.auth import get_current_user
from app.db import Analysis, Application, Report, User, get_db
from app.models.schemas import LocationInput, Sector

router = APIRouter()


class DashboardRequest(BaseModel):
    location: LocationInput
    sector: Sector
    margin_capital: float
    monthly_operating_cost: Optional[float] = None
    gender: Optional[str] = None
    language: str = "English"


@router.post("/generate")
def generate_dashboard(
    req: DashboardRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    from app.routers.location import profile

    try:
        demo = profile(
            req.location.state,
            req.location.district,
            req.location.block,
            req.location.village,
        )
    except HTTPException:
        raise

    ctx = {
        "location": req.location.model_dump(),
        "sector": req.sector.value,
        "margin_capital": req.margin_capital,
        "monthly_operating_cost": req.monthly_operating_cost,
        "gender": req.gender,
        "language": req.language,
        "demo": demo,
    }

    results = run_all_agents(ctx)

    report_id = uuid.uuid4().hex[:12]

    payload = {
        "report_id": report_id,
        "context": ctx,
        "sections": {
            topic: {
                "data": r.data,
                "narrative": r.narrative,
                "sources": r.sources,
            }
            for topic, r in results.items()
        },
    }

    # Persist durably, scoped to the user.
    db.add(
        Analysis(
            id=report_id,
            user_id=user.id,
            village=ctx["location"]["village"],
            block=ctx["location"]["block"],
            district=ctx["location"]["district"],
            state=ctx["location"]["state"],
            sector=ctx["sector"],
            margin_capital=req.margin_capital,
            status="completed",
            viability_score=max(
                10,
                min(
                    95,
                    100
                    - (
                        payload["sections"]["competitor_map"]["data"].get(
                            "estimated_competitors_in_block",
                            10,
                        )
                        or 10
                    ),
                ),
            ),
        )
    )

    db.add(
        Report(
            id=report_id,
            analysis_id=report_id,
            user_id=user.id,
            title=(
                f"{ctx['sector'].replace('_', ' ')} "
                f"— {ctx['location']['block']}"
            ),
            content_json=json.dumps(payload),
        )
    )

    db.commit()

    return payload


@router.get("/{report_id}")
def get_dashboard(
    report_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    rep = db.get(Report, report_id)

    if not rep or rep.user_id != user.id:
        raise HTTPException(404, "Report not found")

    return json.loads(rep.content_json)


@router.get(
    "/{report_id}/download",
    response_class=PlainTextResponse,
)
def download_report(
    report_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> str:
    """Plain-text business report suitable for print/PDF conversion."""

    rep = db.get(Report, report_id)

    if not rep or rep.user_id != user.id:
        raise HTTPException(404, "Report not found")

    rep_payload = json.loads(rep.content_json)

    ctx = rep_payload["context"]
    loc = ctx["location"]

    lines = [
        "=" * 60,
        "BUSINESS FEASIBILITY & FINANCIAL ROADMAP REPORT",
        "=" * 60,
        (
            f"Location : {loc['village'] or '-'}, "
            f"{loc['block']} Block, "
            f"{loc['district']}, "
            f"{loc['state']}"
        ),
        f"Sector   : {ctx['sector'].replace('_', ' ').title()}",
        f"Margin   : Rs {ctx['margin_capital']:,.0f}",
        "",
    ]

    titles = {
        "loan_eligibility": "LOAN ELIGIBILITY",
        "scheme_recommendation": "SCHEME RECOMMENDATION",
        "market_demand": "MARKET DEMAND",
        "competitor_map": "COMPETITOR MAP",
        "swot_analysis": "SWOT ANALYSIS",
        "risk_analysis": "RISK ANALYSIS",
        "pricing_suggestions": "PRICING SUGGESTIONS",
        "working_capital": "WORKING CAPITAL",
        "emi_schedule": "EMI SCHEDULE",
        "cash_flow_forecast": "CASH FLOW FORECAST",
        "ai_mentor": "MENTOR TIPS",
    }

    for topic, title in titles.items():
        sec = rep_payload["sections"].get(topic)

        if not sec:
            continue

        lines += [
            title,
            "-" * len(title),
        ]

        if sec["narrative"]:
            lines.append(sec["narrative"])

        _render(sec["data"], lines)

        if sec["sources"]:
            lines.append(
                "Sources: " + "; ".join(sec["sources"])
            )

        lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)


def _render(
    data: dict,
    lines: list[str],
    indent: int = 0,
) -> None:
    pad = "  " * indent

    for k, v in data.items():

        if k == "narrative":
            continue

        if isinstance(v, dict):
            lines.append(
                f"{pad}{k.replace('_', ' ').title()}:"
            )

            _render(
                v,
                lines,
                indent + 1,
            )

        elif isinstance(v, list):

            if v and isinstance(v[0], dict):
                lines.append(
                    f"{pad}{k.replace('_', ' ').title()}:"
                )

                _render_list(
                    v,
                    lines,
                    indent + 1,
                )

            else:
                for item in v:
                    lines.append(
                        f"{pad}- {item}"
                    )

        else:
            label = k.replace("_", " ").title()

            if isinstance(v, float):
                lines.append(
                    f"{pad}{label}: {v:,.2f}"
                )

            else:
                lines.append(
                    f"{pad}{label}: {v}"
                )


def _render_list(
    items: list[dict],
    lines: list[str],
    indent: int,
) -> None:
    pad = "  " * indent

    for item in items:
        desc = ", ".join(
            f"{k}: {v}"
            for k, v in item.items()
        )

        lines.append(
            f"{pad}* {desc}"
        )


# ============================================================
# AI Mentor Chat
# ============================================================

class MentorChatRequest(BaseModel):
    question: str
    report_id: Optional[str] = None
    language: str = "English"


@router.post("/mentor")
def mentor_chat(
    req: MentorChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Answer Advisor questions using the user's actual analysis.

    Supports both:
    1. Legacy persisted Report IDs.
    2. New analysis IDs returned by /api/analyses.
    """

    dashboard_ctx = None

    if req.report_id:

        # --------------------------------------------------------
        # 1. Try the normal persisted Report first.
        # --------------------------------------------------------
        rep = db.get(
            Report,
            req.report_id,
        )

        if rep and rep.user_id == user.id:

            content = json.loads(
                rep.content_json
            )

            dashboard_ctx = (
                content.get("sections")
                or content.get("insights")
                or content
            )

        else:

            # ----------------------------------------------------
            # 2. New analysis pipeline.
            #
            # The frontend currently uses analysis_id as the
            # report_id passed to the Advisor.
            # ----------------------------------------------------
            from app.api.analyses import _RUNSTATE

            run = _RUNSTATE.get(
                req.report_id
            )

            if (
                run
                and run.get("status") == "completed"
            ):
                dashboard_ctx = {
                    "analysis": {
                        "data": run.get(
                            "insights"
                        ) or {}
                    }
                }

    # ------------------------------------------------------------
    # Send the grounded context to the Advisor agent.
    # ------------------------------------------------------------
    answer = AiMentorAgent().answer(
        req.question,
        dashboard_ctx or {},
        req.language,
    )

    return {
        "answer": answer
    }


# ============================================================
# Scheme Application
# ============================================================

class ApplyRequest(BaseModel):
    report_id: str
    applicant_name: str
    phone: str
    scheme: str


@router.post("/apply")
def apply_for_scheme(
    req: ApplyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:

    rep = db.get(
        Report,
        req.report_id,
    )

    if not rep or rep.user_id != user.id:
        raise HTTPException(
            404,
            "Report not found",
        )

    application_id = (
        f"APP-{uuid.uuid4().hex[:8].upper()}"
    )

    db.add(
        Application(
            id=application_id,
            user_id=user.id,
            report_id=req.report_id,
            scheme=req.scheme,
            applicant_name=req.applicant_name,
            phone=req.phone,
        )
    )

    db.commit()

    # Demo stub — in production this would POST
    # to the SCA/CA portal.
    return {
        "application_id": application_id,
        "status": "submitted",
        "scheme": req.scheme,
        "message": (
            f"Application {application_id} recorded "
            f"for {req.scheme}. "
            f"Our field coordinator will contact "
            f"{req.applicant_name} at {req.phone} "
            f"with the document checklist "
            f"(Aadhaar, caste/income certificate, "
            f"project report, bank details)."
        ),
    }