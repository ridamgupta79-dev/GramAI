"""ARCHITECTURE.md §5 — Reports endpoints.

DB-backed reports with:
- list
- get
- real PDF generation
- share
- from-view
- persistence helper for analysis pipeline
"""

from __future__ import annotations

import html
import io
import json
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db import Report, User, get_db

router = APIRouter()


# ============================================================
# PDF HELPERS
# ============================================================

def _safe_text(value) -> str:
    """Convert arbitrary report values into safe PDF text."""
    if value is None:
        return "—"

    if isinstance(value, bool):
        return "Yes" if value else "No"

    if isinstance(value, float):
        return f"{value:,.2f}"

    if isinstance(value, int):
        return f"{value:,}"

    return str(value)


def _title(text: str) -> str:
    """Turn snake_case keys into readable titles."""
    return str(text).replace("_", " ").replace("-", " ").title()


def _build_pdf(content: dict, report_title: str) -> bytes:
    """
    Generate a real PDF from the stored report JSON.

    ReportLab is intentionally used here because the prototype needs
    a proper downloadable PDF rather than a text response.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
            KeepTogether,
        )
    except ImportError as exc:
        raise RuntimeError(
            "ReportLab is required for PDF generation. "
            "Install it with: pip install reportlab"
        ) from exc

    buffer = io.BytesIO()

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "GramAITitle",
        parent=styles["Title"],
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        spaceAfter=8,
    )

    subtitle_style = ParagraphStyle(
        "GramAISubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#555555"),
        spaceAfter=20,
    )

    section_style = ParagraphStyle(
        "GramAISection",
        parent=styles["Heading2"],
        fontSize=15,
        leading=19,
        spaceBefore=12,
        spaceAfter=8,
    )

    subsection_style = ParagraphStyle(
        "GramAISubsection",
        parent=styles["Heading3"],
        fontSize=11,
        leading=15,
        spaceBefore=8,
        spaceAfter=5,
    )

    body_style = ParagraphStyle(
        "GramAIBody",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=14,
        spaceAfter=5,
    )

    small_style = ParagraphStyle(
        "GramAISmall",
        parent=styles["BodyText"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#666666"),
    )

    bullet_style = ParagraphStyle(
        "GramAIBullet",
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        bulletIndent=2,
        spaceAfter=3,
    )

    story = []

    # --------------------------------------------------------
    # Cover / Header
    # --------------------------------------------------------

    story.append(Spacer(1, 15 * mm))
    story.append(Paragraph("GRAM AI", title_style))
    story.append(
        Paragraph(
            html.escape(report_title or "Business Feasibility Report"),
            subtitle_style,
        )
    )

    story.append(
        Paragraph(
            "AI-assisted rural business intelligence and feasibility report",
            subtitle_style,
        )
    )

    # --------------------------------------------------------
    # Recursive report renderer
    # --------------------------------------------------------

    def add_value(label: str, value) -> None:
        """Render a scalar key/value pair."""
        label_html = html.escape(_title(label))
        value_html = html.escape(_safe_text(value))

        table = Table(
            [[
                Paragraph(f"<b>{label_html}</b>", body_style),
                Paragraph(value_html, body_style),
            ]],
            colWidths=[55 * mm, 115 * mm],
        )

        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#DDDDDD")),
                ]
            )
        )

        story.append(table)

    def render_value(value, level: int = 0) -> None:
        """Recursively render dictionaries, lists and scalar values."""

        if isinstance(value, dict):
            for key, child in value.items():
                if isinstance(child, (dict, list)):
                    story.append(
                        Paragraph(
                            html.escape(_title(key)),
                            subsection_style if level > 0 else section_style,
                        )
                    )
                    render_value(child, level + 1)
                else:
                    add_value(key, child)

        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    # Render dictionary list items as compact blocks.
                    rows = []

                    for key, child in item.items():
                        if isinstance(child, (dict, list)):
                            rows.append(
                                [
                                    Paragraph(
                                        f"<b>{html.escape(_title(key))}</b>",
                                        body_style,
                                    ),
                                    Paragraph(
                                        html.escape(
                                            json.dumps(
                                                child,
                                                ensure_ascii=False,
                                                default=str,
                                            )
                                        ),
                                        body_style,
                                    ),
                                ]
                            )
                        else:
                            rows.append(
                                [
                                    Paragraph(
                                        f"<b>{html.escape(_title(key))}</b>",
                                        body_style,
                                    ),
                                    Paragraph(
                                        html.escape(_safe_text(child)),
                                        body_style,
                                    ),
                                ]
                            )

                    if rows:
                        table = Table(
                            rows,
                            colWidths=[55 * mm, 115 * mm],
                            repeatRows=0,
                        )

                        table.setStyle(
                            TableStyle(
                                [
                                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#DDDDDD")),
                                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F5F7FA")),
                                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                                ]
                            )
                        )

                        story.append(KeepTogether([table, Spacer(1, 4)]))

                elif isinstance(item, list):
                    render_value(item, level + 1)

                else:
                    story.append(
                        Paragraph(
                            f"• {html.escape(_safe_text(item))}",
                            bullet_style,
                        )
                    )

        else:
            story.append(
                Paragraph(
                    html.escape(_safe_text(value)),
                    body_style,
                )
            )

    # --------------------------------------------------------
    # Main report content
    # --------------------------------------------------------

    if isinstance(content, dict):
        render_value(content)
    else:
        story.append(
            Paragraph(
                html.escape(_safe_text(content)),
                body_style,
            )
        )

    # --------------------------------------------------------
    # Verification / Safety footer
    # --------------------------------------------------------

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            "<b>Important:</b> This report contains prototype estimates, "
            "synthetic/local demo data where applicable, and rule-based "
            "financial calculations. Government scheme eligibility, lending "
            "terms, interest rates and final approval must be verified with "
            "the relevant official source or lending institution before making "
            "financial decisions.",
            small_style,
        )
    )

    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            "Generated by GramAI • Rural Business Intelligence Prototype",
            small_style,
        )
    )

    # --------------------------------------------------------
    # Build PDF
    # --------------------------------------------------------

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=report_title or "GramAI Business Report",
        author="GramAI",
    )

    document.build(story)

    return buffer.getvalue()


# ============================================================
# REPORT LIST
# ============================================================

@router.get("")
def list_reports(
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:

    rows = (
        db.query(Report)
        .filter(Report.user_id == user.id)
        .order_by(Report.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": r.id,
            "analysis_id": r.analysis_id,
            "version": 1,
            "title": r.title,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


# ============================================================
# GET REPORT
# ============================================================

@router.get("/{report_id}")
def get_report(
    report_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:

    rep = db.get(Report, report_id)

    if not rep or rep.user_id != user.id:
        raise HTTPException(404, "Report not found")

    return {
        "id": rep.id,
        "analysis_id": rep.analysis_id,
        "version": 1,
        "title": rep.title,
        "created_at": rep.created_at.timestamp(),
        "content": json.loads(rep.content_json),
    }


# ============================================================
# REAL PDF
# ============================================================

@router.get("/{report_id}/pdf")
def report_pdf(
    report_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:

    rep = db.get(Report, report_id)

    if not rep or rep.user_id != user.id:
        raise HTTPException(404, "Report not found")

    content = json.loads(rep.content_json)

    try:
        pdf_bytes = _build_pdf(
            content=content,
            report_title=rep.title or "GramAI Business Report",
        )
    except RuntimeError as exc:
        raise HTTPException(500, str(exc)) from exc

    filename = (
        f"gramai-business-report-{report_id}.pdf"
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


# ============================================================
# SHARE
# ============================================================

class ShareRequest(BaseModel):
    expires_in_days: int = Field(default=30, ge=1, le=365)


@router.post("/{report_id}/share")
def share_report(
    report_id: str,
    req: ShareRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:

    rep = db.get(Report, report_id)

    if not rep or rep.user_id != user.id:
        raise HTTPException(404, "Report not found")

    token = secrets.token_urlsafe(16)

    # Demo share URL.
    # A production deployment should replace this with the actual
    # application's public share route.
    rep.share_url = f"https://gramai.example/s/{token}"

    db.commit()

    return {
        "url": rep.share_url,
        "expires_in_days": req.expires_in_days,
    }


# ============================================================
# GENERATE REPORT FROM MAP VIEW
# ============================================================

class FromViewRequest(BaseModel):
    village_id: int | None = None
    radius_km: int = Field(default=10, ge=1, le=100)
    layers: list[str] = []


@router.post("/from-view", status_code=201)
def report_from_view(
    body: FromViewRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:

    """Generate a report from the current map view."""

    report_id = uuid.uuid4().hex[:12]

    rep = Report(
        id=report_id,
        analysis_id="map-view",
        user_id=user.id,
        title=f"Market view — village {body.village_id}",
        content_json=json.dumps(
            {
                "executive_summary": (
                    f"Market view report for village {body.village_id} "
                    f"within {body.radius_km} km covering "
                    f"layers {body.layers}."
                ),
                "market_section": {
                    "radius_km": body.radius_km,
                    "layers": body.layers,
                },
            }
        ),
    )

    db.add(rep)
    db.commit()

    return {"id": report_id}


# ============================================================
# SAVE REPORT
# ============================================================

def save_report(
    db: Session,
    analysis_id: str,
    user_id: int,
    title: str,
    content: dict,
) -> str:

    report_id = uuid.uuid4().hex[:12]

    db.add(
        Report(
            id=report_id,
            analysis_id=analysis_id,
            user_id=user_id,
            title=title,
            content_json=json.dumps(
                content,
                ensure_ascii=False,
                default=str,
            ),
        )
    )

    db.commit()

    return report_id
