"""ARCHITECTURE.md §3.3 — Financial Engine (pure Python, deterministic).

Monthly reducing-balance engine per the architecture spec:
- Loan = cost × (1 − margin%)
- EMI = P·r(1+r)^n / ((1+r)^n − 1), r = monthly rate, n = months
- Amortization schedule, moratorium (interest-only) handling
- Working capital, break-even, 3-yr cash-flow projection
- MUDRA tier routing (Shishu < ₹50k, Kishore ₹50k–₹5L, Tarun ₹5L–₹10L)
No LLM involved.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# ---------- MUDRA tiers ----------

def mudra_tier(loan_amount: float) -> str:
    if loan_amount <= 50_000:
        return "Shishu"
    if loan_amount <= 500_000:
        return "Kishore"
    if loan_amount <= 1_000_000:
        return "Tarun"
    return "Above MUDRA"


# ---------- Core computations ----------

def monthly_emi(principal: float, annual_rate_pct: float, tenure_months: int) -> float:
    r = annual_rate_pct / 100.0 / 12.0
    if principal <= 0 or tenure_months <= 0:
        return 0.0
    if r == 0:
        return principal / tenure_months
    return principal * r * (1 + r) ** tenure_months / ((1 + r) ** tenure_months - 1)


def amortization_schedule(principal: float, annual_rate_pct: float,
                          tenure_months: int,
                          moratorium_months: int = 0) -> list[dict]:
    """Monthly schedule. During moratorium: interest-only payments."""
    r = annual_rate_pct / 100.0 / 12.0
    rows: list[dict] = []
    balance = principal
    repay_months = max(tenure_months - moratorium_months, 1)
    emi = monthly_emi(balance, annual_rate_pct, repay_months)

    for m in range(1, tenure_months + 1):
        interest = balance * r
        if m <= moratorium_months:
            principal_part = 0.0
            payment = interest
            phase = "moratorium"
        else:
            principal_part = min(emi - interest, balance)
            payment = interest + principal_part
            phase = "repayment"
        opening = balance
        balance = max(balance - principal_part, 0.0)
        rows.append({
            "month": m, "opening_balance": round(opening, 2),
            "interest": round(interest, 2), "principal": round(principal_part, 2),
            "payment": round(payment, 2), "closing_balance": round(balance, 2),
            "phase": phase,
        })
    return rows


def break_even_month(fixed_cost: float, price_per_unit: float,
                     variable_cost_per_unit: float,
                     units_per_month: int) -> int | None:
    """Months to recover fixed cost from unit contribution margin."""
    contribution = price_per_unit - variable_cost_per_unit
    if contribution <= 0 or units_per_month <= 0:
        return None
    months = fixed_cost / (contribution * units_per_month)
    return max(1, -(-int(months * 100) // 100)) if months > 0 else 1


def cashflow_projection(project_cost: float, loan_amount: float,
                        annual_rate_pct: float, tenure_months: int,
                        moratorium_months: int, monthly_revenue: float,
                        monthly_opex: float, years: int = 3) -> dict:
    """Yearly cash-flow projection with seasonality and debt service."""
    schedule = amortization_schedule(loan_amount, annual_rate_pct,
                                     tenure_months, moratorium_months)
    yearly: list[dict] = []
    cum = -project_cost
    for y in range(1, years + 1):
        months = range((y - 1) * 12 + 1, y * 12 + 1)
        revenue = sum(monthly_revenue * (1.15 ** (y - 1)) for _ in months)
        opex = sum(monthly_opex * (1.08 ** (y - 1)) for _ in months)
        debt_service = sum(s["payment"] for s in schedule if s["month"] in months)
        net = revenue - opex - debt_service
        cum += net
        yearly.append({
            "year": y, "revenue": round(revenue), "operating_expenses": round(opex),
            "debt_service": round(debt_service), "net_cash_flow": round(net),
            "cumulative_cash": round(cum),
        })
    return {"years": yearly}


def working_capital_estimate(monthly_opex: float, months: int = 6) -> float:
    return round(monthly_opex * months, 2)


@dataclass
class Quote:
    loan_amount: float
    emi: float
    total_interest: float
    tier: str
    schedule: list[dict] = field(default_factory=list)


def quote(project_cost: float, margin_pct: float, interest_rate: float,
          tenure_months: int, moratorium_months: int = 0) -> Quote:
    """Live EMI preview — ARCHITECTURE.md POST /api/finance/quote."""
    margin_pct = min(max(margin_pct, 0.0), 90.0)
    loan = project_cost * (1 - margin_pct / 100.0)
    schedule = amortization_schedule(loan, interest_rate, tenure_months,
                                     moratorium_months)
    total_interest = round(sum(r["interest"] for r in schedule), 2)
    emi = next((r["payment"] for r in schedule if r["phase"] == "repayment"), 0.0)
    return Quote(loan_amount=round(loan, 2), emi=round(emi, 2),
                 total_interest=total_interest,
                 tier=mudra_tier(loan), schedule=schedule)
