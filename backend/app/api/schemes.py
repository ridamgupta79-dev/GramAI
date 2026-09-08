"""ARCHITECTURE.md §5 — Schemes endpoints (list, detail, eligibility)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.schemes import SCHEMES, check_eligibility, get_scheme

router = APIRouter()


class EligibilityRequest(BaseModel):
    loan_amount: float = Field(gt=0)
    project_cost: float = Field(gt=0)
    is_woman: bool = False
    is_scst: bool = False
    sector_non_farm: bool = True


@router.get("")
def list_schemes(recommended: Optional[bool] = None) -> list[dict]:
    items = [{
        "slug": s["slug"], "name": s["name"], "level": s["level"],
        "min_loan": s["min_loan"], "max_loan": s["max_loan"],
        "interest_guidance": s["interest_guidance"],
    } for s in SCHEMES]
    if recommended:
        items = [i for i in items if i["slug"] in ("mudra", "pmegp", "term_loan_sca")]
    return items


@router.get("/{slug}")
def scheme_detail(slug: str) -> dict:
    s = get_scheme(slug)
    if not s:
        from fastapi import HTTPException
        raise HTTPException(404, f"Unknown scheme: {slug}")
    return {k: v for k, v in s.items() if k != "eligibility_rules"} | {
        "tiers": ["Shishu", "Kishore", "Tarun"] if slug in ("mudra", "pmmy") else [],
    }


@router.post("/check-eligibility")
def eligibility(req: EligibilityRequest) -> list[dict]:
    return check_eligibility(req.loan_amount, req.project_cost,
                             is_woman=req.is_woman, is_scst=req.is_scst,
                             sector_non_farm=req.sector_non_farm)
