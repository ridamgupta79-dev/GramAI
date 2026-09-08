"""ARCHITECTURE.md §5 — Users endpoints (me, dashboard, activity)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db import Analysis, Report, User, get_db
from app.services.schemes import SCHEMES

router = APIRouter()


@router.get("/me")
def me(user: User = Depends(get_current_user)) -> dict:
    return {"id": user.id, "mobile": user.mobile, "full_name": user.full_name,
            "role": "user", "preferred_lang": user.preferred_lang,
            "profile_completeness": 70}


@router.patch("/me")
def patch_me(body: dict, user: User = Depends(get_current_user),
             db: Session = Depends(get_db)) -> dict:
    allowed = {"full_name", "preferred_lang"}
    for k, v in body.items():
        if k in allowed:
            setattr(user, k, v)
    db.commit()
    return {"id": user.id, "mobile": user.mobile, "full_name": user.full_name,
            "role": "user", "preferred_lang": user.preferred_lang,
            "profile_completeness": 70}


@router.get("/me/dashboard")
def dashboard(user: User = Depends(get_current_user),
              db: Session = Depends(get_db)) -> dict:
    recent = (db.query(Report).filter(Report.user_id == user.id)
              .order_by(Report.created_at.desc()).limit(5).all())
    latest = (db.query(Analysis).filter(Analysis.user_id == user.id,
                                        Analysis.status == "completed")
              .order_by(Analysis.created_at.desc()).first())
    return {
        "viability_score": latest.viability_score if latest else 85,
        "recent_reports": [{"id": r.id, "title": r.title} for r in recent],
        "schemes_carousel": [
            {"slug": s["slug"], "name": s["name"],
             "interest_guidance": s["interest_guidance"]}
            for s in SCHEMES[:4]
        ],
    }


@router.get("/me/activity")
def activity(user: User = Depends(get_current_user),
             db: Session = Depends(get_db)) -> list[dict]:
    rows = (db.query(Analysis).filter(Analysis.user_id == user.id)
            .order_by(Analysis.created_at.desc()).limit(20).all())
    acts = [{"action": "analysis.created", "detail": f"{r.sector} analysis",
             "ts": r.created_at.timestamp()} for r in rows]
    if not acts:
        from app.db import SessionLocal
        return [{"action": "welcome", "detail": "Account created", "ts": 0}]
    return acts
