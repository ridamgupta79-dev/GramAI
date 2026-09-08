"""ARCHITECTURE.md §5 — Analyses orchestrator with SSE stage progress.

In-process worker (thread) replaces Celery/Redis for the demo; the API
contract matches the architecture spec exactly. Analyses persist in the DB
and are scoped to the authenticated user.
"""

from __future__ import annotations

import asyncio
import json
import threading
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.api.reports import save_report
from app.db import Analysis, Report, User, get_db
from app.services import advisory, financial, gis, schemes as scheme_svc
from app.services.location_data import village_by_id


router = APIRouter()


STAGES = [
    ("demographics", 25),
    ("competitors", 50),
    ("financial_feasibility", 75),
    ("llm_advisory", 100),
]


# Live pipeline state (transient); durable state lives in the DB.
_RUNSTATE: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class Financing(BaseModel):
    project_cost: float = Field(gt=0)
    margin_pct: float = Field(ge=0, le=90, default=10)
    interest_rate: float = Field(gt=0, le=30, default=9.5)
    tenure_months: int = Field(gt=0, le=360, default=60)
    moratorium_months: int = Field(default=0, ge=0, le=24)


class AnalysisRequest(BaseModel):
    village_id: Optional[int] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    category_slug: str = "retail"

    # Applicant profile used for personalized scheme matching
    is_woman: bool = False
    is_scst: bool = False
    previous_tarun_repaid: bool = False

    financing: Financing


# ---------------------------------------------------------------------------
# Analysis pipeline
# ---------------------------------------------------------------------------

def _run_pipeline(
    analysis_id: str,
    user_id: int,
    req: AnalysisRequest,
) -> None:

    from app.db import SessionLocal

    a = _RUNSTATE[analysis_id]
    a["status"] = "running"

    # ================================================================
    # Stage 1: demographics
    # ================================================================

    a["stage"], a["progress_pct"] = "demographics", 25

    # Use the selected village's population from the seeded
    # location dataset.
    #
    # This is DEMO population data. Production will replace it
    # with Census/LGD/local demographic datasets.

    village = (
        village_by_id(req.village_id)
        if req.village_id
        else None
    )

    if village:
        village_population = village["population"]
    else:
        # Fallback for analyses where no village is supplied.
        village_population = 8_000

    # We currently have village-level population data, not a true
    # 10 km population raster/aggregation.
    # Therefore we do not falsely call this "population within 10km".
    population = village_population

    # Prototype target-customer assumption.
    target_customers = int(population * 0.4)

    # ================================================================
    # Stage 2: competitors via GIS radius query
    # ================================================================

    a["stage"], a["progress_pct"] = "competitors", 50

    nearby = gis.nearby(
        village_id=req.village_id,
        lat=req.lat,
        lon=req.lon,
        radius_km=10.0,
        layers=["competitors"],
    )

    competitor_pois = nearby["pois"]
    competitors = len(competitor_pois)

    # Competition density:
    # number of competitors per 1,000 target customers.

    competitors_per_1000_customers = (
        competitors / target_customers * 1000
        if target_customers > 0
        else 0
    )

    # Convert raw competitor count into a business-level
    # competition assessment.

    if competitors == 0:
        competition_level = "Very Low"
    elif competitors_per_1000_customers < 1.5:
        competition_level = "Low"
    elif competitors_per_1000_customers < 3:
        competition_level = "Medium"
    else:
        competition_level = "High"

    # Estimate pricing pressure from competition.

    if competition_level in ("Very Low", "Low"):
        pricing_pressure = "Low"
        market_opportunity = "Strong"

    elif competition_level == "Medium":
        pricing_pressure = "Moderate"
        market_opportunity = "Moderate"

    else:
        pricing_pressure = "High"
        market_opportunity = "Limited"

    # ================================================================
    # Stage 3: financial feasibility
    # ================================================================

    a["stage"], a["progress_pct"] = (
        "financial_feasibility",
        75,
    )

    f = req.financing

    q = financial.quote(
        f.project_cost,
        f.margin_pct,
        f.interest_rate,
        f.tenure_months,
        f.moratorium_months,
    )

    # ---------------------------------------------------------------
    # Prototype financial assumptions
    # ---------------------------------------------------------------
    #
    # These are deliberately explicit so they can later be replaced
    # with sector/location-specific market data.

    monthly_opex = f.project_cost * 0.08
    monthly_revenue = monthly_opex * 1.5

    # Six months of operating expenses as working-capital reserve.

    working_capital = financial.working_capital_estimate(
        monthly_opex,
        months=6,
    )

    # Three-year cash-flow projection.

    cashflow = financial.cashflow_projection(
        project_cost=f.project_cost,
        loan_amount=q.loan_amount,
        annual_rate_pct=f.interest_rate,
        tenure_months=f.tenure_months,
        moratorium_months=f.moratorium_months,
        monthly_revenue=monthly_revenue,
        monthly_opex=monthly_opex,
        years=3,
    )

    # Estimate monthly operating profit before debt service.

    monthly_profit = monthly_revenue - monthly_opex

    # Measure EMI burden against operating profit.

    emi_to_profit_ratio = (
        q.emi / monthly_profit
        if monthly_profit > 0
        else 1.0
    )

    # ================================================================
    # Stage 4: scheme intelligence + risk + advisory
    # ================================================================

    a["stage"], a["progress_pct"] = "llm_advisory", 100

    # ---------------------------------------------------------------
    # Government scheme eligibility
    # ---------------------------------------------------------------

    # At this stage the request model does not yet contain gender,
    # SC/ST or previous Tarun repayment information.
    #
    # Therefore the scheme engine uses its safe defaults:
    # is_woman=False
    # is_scst=False
    # previous_tarun_repaid=False

    elig = scheme_svc.check_eligibility(
        q.loan_amount,
        f.project_cost,
        is_woman=req.is_woman,
        is_scst=req.is_scst,
        previous_tarun_repaid=req.previous_tarun_repaid,
        sector_non_farm=True,
        sector_type=(
            "service"
            if req.category_slug.lower() in {
                "service",
                "services",
            }
            else "business"
        ),
    )

    eligible_count = sum(
        1
        for e in elig
        if e["eligible"]
    )

    # ================================================================
    # Dynamic risk assessment
    # ================================================================

    risk_factors: list[str] = []

    # ---------------------------------------------------------------
    # Risk 1: EMI burden
    # ---------------------------------------------------------------

    if emi_to_profit_ratio > 0.75:
        risk_factors.append(
            "High EMI burden relative to operating profit"
        )

    elif emi_to_profit_ratio > 0.50:
        risk_factors.append(
            "Moderate EMI burden relative to operating profit"
        )

    # ---------------------------------------------------------------
    # Risk 2: competition
    # ---------------------------------------------------------------

    if competition_level == "High":
        risk_factors.append(
            "High local competition"
        )

    elif competition_level == "Medium":
        risk_factors.append(
            "Moderate local competition"
        )

    # ---------------------------------------------------------------
    # Risk 3: working capital
    # ---------------------------------------------------------------

    if working_capital < f.project_cost * 0.15:
        risk_factors.append(
            "Limited working-capital buffer"
        )

    # ---------------------------------------------------------------
    # Risk 4: scheme availability
    # ---------------------------------------------------------------

    if eligible_count == 0:
        risk_factors.append(
            "No matching government scheme identified"
        )

    # Only clearly serious risks count toward the viability score.

    high_risks = sum(
        1
        for risk in risk_factors
        if (
            risk.startswith("High")
            or risk.startswith("Limited")
            or risk.startswith("No matching")
        )
    )

    if high_risks >= 1:
        overall_risk = "high"

    elif risk_factors:
        overall_risk = "moderate"

    else:
        overall_risk = "low"

    risk_profile = {
        "overall": overall_risk,
        "high_risks": high_risks,
        "risk_factors": risk_factors,
    }

    # ================================================================
    # Viability score
    # ================================================================

    score = advisory.viability_score(
        target_customers=target_customers,
        competitors=competitors,
        radius_km=10.0,
        emi_to_profit_ratio=emi_to_profit_ratio,
        schemes_eligible=eligible_count,
        high_risks=high_risks,
    )

    # ================================================================
    # Build insights payload
    # ================================================================

    insights = {

        # ------------------------------------------------------------
        # Overall viability
        # ------------------------------------------------------------

        "viability_score": score["score"],

        "viability_rating": score.get(
            "rating",
            "Moderate",
        ),

        "score_components": score["components"],

        "score_weights": score.get(
            "weights",
            {},
        ),

        "score_breakdown": score.get(
            "weighted_contributions",
            {},
        ),

        "score_inputs": score.get(
            "inputs",
            {},
        ),

        # ------------------------------------------------------------
        # Location intelligence
        # ------------------------------------------------------------

        "location": {
            "village_id": (
                village["id"]
                if village
                else req.village_id
            ),

            "village": (
                village["name"]
                if village
                else None
            ),

            "latitude": (
                village["lat"]
                if village
                else req.lat
            ),

            "longitude": (
                village["lon"]
                if village
                else req.lon
            ),

            "population": population,

            "data_source": "synthetic_demo",
        },

        # ------------------------------------------------------------
        # Loan / financing intelligence
        # ------------------------------------------------------------

        "loan_eligibility": {
            "scheme": (
                "MUDRA"
                if q.tier != "Above MUDRA"
                else "Term Loan"
            ),

            "tier": q.tier,

            "loan_amount": q.loan_amount,

            "emi": q.emi,

            "total_interest": q.total_interest,
        },

        # ------------------------------------------------------------
        # Financial intelligence
        # ------------------------------------------------------------

        "financial": {
            "project_cost": f.project_cost,

            "margin_pct": f.margin_pct,

            "margin_amount": round(
                f.project_cost * f.margin_pct / 100,
                2,
            ),

            "loan_amount": q.loan_amount,

            "monthly_emi": q.emi,

            "monthly_revenue": round(
                monthly_revenue,
                2,
            ),

            "monthly_opex": round(
                monthly_opex,
                2,
            ),

            "monthly_profit": round(
                monthly_profit,
                2,
            ),

            "emi_to_profit_ratio": round(
                emi_to_profit_ratio,
                3,
            ),

            "working_capital_6_months": working_capital,

            "total_interest": q.total_interest,

            "cashflow_projection": cashflow,

            "assumptions": {
                "monthly_opex_pct_of_project_cost": 8,

                "monthly_revenue_multiplier": 1.5,

                "note": (
                    "Revenue and operating-cost figures are "
                    "prototype assumptions and should be replaced "
                    "with sector- and location-specific data."
                ),
            },
        },

        # ------------------------------------------------------------
        # Market intelligence
        # ------------------------------------------------------------

        "market": {
            "population": population,

            "population_scope": "selected_village",

            "target_customer_base": target_customers,

            "competitors_within_10km": competitors,

            "competition_level": competition_level,

            "competitors_per_1000_customers": round(
                competitors_per_1000_customers,
                2,
            ),

            "pricing_pressure": pricing_pressure,

            "market_opportunity": market_opportunity,

            "yoy_growth_pct": 14,

            "gis_data_source": nearby.get(
                "data_source",
                "synthetic_demo",
            ),
        },

        # ------------------------------------------------------------
        # Pricing intelligence
        # ------------------------------------------------------------

        "pricing": {
            "competitor_price": 45,

            "recommended_price": 65,

            "note": (
                "Pricing figures are prototype assumptions. "
                "A production version should derive them from "
                "verified local market data."
            ),
        },

        # ------------------------------------------------------------
        # Risk intelligence
        # ------------------------------------------------------------

        "risk_profile": risk_profile,

        # ------------------------------------------------------------
        # SWOT
        # ------------------------------------------------------------

        "swot": {
            "strengths": [
                "Concessional credit access",
                "Low rural overheads",
            ],

            "weaknesses": [
                "First-time entrepreneur",
                "Thin working-capital buffer",
            ],

            "opportunities": [
                "Growing rural demand",
                "SHG tie-ups",
            ],

            "threats": [
                "Seasonal demand dips",
                "Input price volatility",
            ],
        },

        # ------------------------------------------------------------
        # Additional scheme information
        # ------------------------------------------------------------

        "additional_subsidies_eligible": max(
            eligible_count - 1,
            0,
        ),

        "scheme_matches": elig,
    }

    # ================================================================
    # Complete in-memory pipeline state
    # ================================================================

    a["insights"] = insights
    a["status"] = "completed"

    # ================================================================
    # Persist durably
    # ================================================================

    db = SessionLocal()

    try:
        row = db.get(
            Analysis,
            analysis_id,
        )

        if row:
            row.status = "completed"
            row.viability_score = insights[
                "viability_score"
            ]

        # IMPORTANT:
        # save_report() creates a separate Report ID.
        # Store that ID in the transient analysis state so the
        # frontend can use the correct ID for PDF download.
        report_id = save_report(
            db,
            analysis_id,
            user_id,
            f"{req.category_slug} analysis",
            {
                "insights": insights,
                "request": req.model_dump(),
            },
        )

        a["report_id"] = report_id

        db.commit()

    finally:
        db.close()


# ---------------------------------------------------------------------------
# Create analysis
# ---------------------------------------------------------------------------

@router.post("", status_code=202)
def create_analysis(
    req: AnalysisRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:

    analysis_id = uuid.uuid4().hex[:12]

    db.add(
        Analysis(
            id=analysis_id,
            user_id=user.id,
            village="",
            block="",
            district="",
            state="",
            sector=req.category_slug,
            margin_capital=req.financing.project_cost,
            status="queued",
        )
    )

    db.commit()

    _RUNSTATE[analysis_id] = {
        "id": analysis_id,
        "status": "queued",
        "stage": "",
        "progress_pct": 0,
        "request": req.model_dump(),
        "insights": None,
        "report_id": None,
    }

    threading.Thread(
        target=_run_pipeline,
        args=(
            analysis_id,
            user.id,
            req,
        ),
        daemon=True,
    ).start()

    return {
        "analysis_id": analysis_id,
        "status": "queued",
    }


# ---------------------------------------------------------------------------
# SSE analysis progress
# ---------------------------------------------------------------------------

@router.get("/{analysis_id}/status")
async def analysis_status(
    analysis_id: str,
    user: User = Depends(get_current_user),
):
    """SSE stream of stage events until done."""

    if analysis_id not in _RUNSTATE:
        raise HTTPException(
            404,
            "Analysis not found",
        )

    async def event_stream():
        last = ""

        for _ in range(600):
            a = _RUNSTATE[analysis_id]

            payload = {
                "stage": a["stage"],
                "progress": a["progress_pct"],
            }

            key = (
                f"{a['stage']}:{a['progress_pct']}"
            )

            if key != last and a["stage"]:
                last = key

                yield (
                    "event: stage\n"
                    f"data: {json.dumps(payload)}\n\n"
                )

            if a["status"] == "completed":
                done = {
                    "stage": "done",
                    "viability_score": (
                        a["insights"]["viability_score"]
                    ),
                }

                yield (
                    "event: stage\n"
                    f"data: {json.dumps(done)}\n\n"
                )

                return

            await asyncio.sleep(0.1)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
    )


# ---------------------------------------------------------------------------
# Get analysis insights
# ---------------------------------------------------------------------------

@router.get("/{analysis_id}/insights")
def analysis_insights(
    analysis_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:

    a = _RUNSTATE.get(analysis_id)

    if a:
        if a["status"] != "completed":
            raise HTTPException(
                409,
                f"Analysis not ready (status={a['status']})",
            )

        # IMPORTANT:
        # Return the actual persisted Report ID along with the insights.
        return {
            **a["insights"],
            "report_id": a.get("report_id"),
        }

    # Fall back to the persisted report.

    rep = (
        db.query(Report)
        .filter(
            Report.analysis_id == analysis_id,
            Report.user_id == user.id,
        )
        .first()
    )

    if not rep:
        raise HTTPException(
            404,
            "Analysis not found",
        )

    content = json.loads(rep.content_json)

    return {
        **content.get("insights", {}),
        "report_id": rep.id,
    }


# ---------------------------------------------------------------------------
# List user's analyses
# ---------------------------------------------------------------------------

@router.get("")
def list_my_analyses(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:

    rows = (
        db.query(Analysis)
        .filter(
            Analysis.user_id == user.id
        )
        .order_by(
            Analysis.created_at.desc()
        )
        .limit(50)
        .all()
    )

    return [
        {
            "id": r.id,
            "sector": r.sector,
            "status": r.status,
            "viability_score": r.viability_score,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]