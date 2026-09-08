"""ARCHITECTURE.md §5 — Finance endpoints (quote, simulate, amortization)."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import financial

router = APIRouter()

# plan_id -> schedule rows (in-memory; production persists financing_plans)
_PLANS: dict[str, list[dict]] = {}


class QuoteRequest(BaseModel):
    project_cost: float = Field(gt=0)
    margin_pct: float = Field(ge=0, le=90, default=10)
    interest_rate: float = Field(gt=0, le=30)
    tenure_months: int = Field(gt=0, le=360)


class SimulateRequest(QuoteRequest):
    moratorium_months: int = Field(default=0, ge=0, le=24)
    monthly_revenue: float = Field(default=50_000, ge=0)
    monthly_opex: float = Field(default=30_000, ge=0)
    price_per_unit: float = Field(default=50, gt=0)
    variable_cost_per_unit: float = Field(default=30, ge=0)
    units_per_month: int = Field(default=500, gt=0)


@router.post("/quote")
def finance_quote(req: QuoteRequest) -> dict:
    """Live wizard EMI preview — no persistence."""
    q = financial.quote(req.project_cost, req.margin_pct, req.interest_rate,
                        req.tenure_months)
    return {
        "loan_amount": q.loan_amount,
        "emi": q.emi,
        "total_interest": q.total_interest,
        "tier": q.tier,
    }


@router.post("/simulate")
def finance_simulate(req: SimulateRequest) -> dict:
    q = financial.quote(req.project_cost, req.margin_pct, req.interest_rate,
                        req.tenure_months, req.moratorium_months)
    be = financial.break_even_month(
        fixed_cost=req.project_cost * 0.4,
        price_per_unit=req.price_per_unit,
        variable_cost_per_unit=req.variable_cost_per_unit,
        units_per_month=req.units_per_month,
    )
    cf = financial.cashflow_projection(
        req.project_cost, q.loan_amount, req.interest_rate, req.tenure_months,
        req.moratorium_months, req.monthly_revenue, req.monthly_opex,
    )
    wc = financial.working_capital_estimate(req.monthly_opex)
    plan_id = uuid.uuid4().hex[:12]
    _PLANS[plan_id] = q.schedule
    return {
        "plan_id": plan_id,
        "loan_amount": q.loan_amount,
        "emi": q.emi,
        "total_interest": q.total_interest,
        "tier": q.tier,
        "schedule": q.schedule,
        "break_even_month": be,
        "cashflow": cf,
        "working_capital": wc,
        # expense donut data
        "expense_breakdown": [
            {"name": "Principal", "value": round(q.loan_amount)},
            {"name": "Interest", "value": q.total_interest},
            {"name": "Working capital", "value": wc},
        ],
    }


@router.get("/amortization/{plan_id}")
def amortization(plan_id: str) -> dict:
    rows = _PLANS.get(plan_id)
    if rows is None:
        raise HTTPException(404, "Plan not found")
    return {"plan_id": plan_id, "rows": rows}
