"""Deterministic financial engine — Module 2.

NEVER route these calculations through the LLM. Pure functions only.
"""
from __future__ import annotations

from app.models.schemas import LoanPlan, RepaymentRow, SchemeName

MICRO_MAX_PROJECT_COST = 140_000.0        # ₹1.40 lakh
TERM_MAX_PROJECT_COST = 5_000_000.0       # ₹50 lakh
MARGIN_FRACTION = 0.10                    # beneficiary contributes 10%
LOAN_FRACTION = 0.90                      # SCA/CA funds 90%

SCHEMES = {
    SchemeName.MICRO_FINANCE: {
        "interest_rate_pa": 6.5,
        "tenure_years": 3,
        "moratorium_months": 3,
        "max_loan": 125_000.0,
    },
    SchemeName.TERM_LOAN: {
        "interest_rate_pa": 8.0,
        "tenure_years": 7,
        "moratorium_months": 6,
        "max_loan": 4_500_000.0,
    },
}


def _quarterly_rate(annual_rate: float) -> float:
    return annual_rate / 100.0 / 4.0


def _build_schedule(principal: float, annual_rate: float, tenure_years: int,
                    moratorium_months: int) -> tuple[list[RepaymentRow], float]:
    """Quarterly reducing-balance EMI schedule with a simple-interest moratorium.

    During moratorium (first `moratorium_months` months = ceil/4 quarters) the
    borrower pays accrued interest only; principal is amortised over remaining
    quarters with a level quarterly payment.
    """
    rate = _quarterly_rate(annual_rate)
    total_quarters = tenure_years * 4
    moratorium_quarters = -(-moratorium_months // 4)  # ceil division
    repayment_quarters = total_quarters - moratorium_quarters

    balance = principal
    rows: list[RepaymentRow] = []
    total_interest = 0.0

    # Moratorium: interest-only payments on full principal
    for q in range(1, moratorium_quarters + 1):
        interest = balance * rate
        total_interest += interest
        rows.append(RepaymentRow(
            quarter=q, opening_balance=round(balance, 2),
            interest_due=round(interest, 2), principal_repaid=0.0,
            total_payment=round(interest, 2), closing_balance=round(balance, 2),
            phase="moratorium",
        ))

    # Level payment amortising principal over remaining quarters
    n = repayment_quarters
    emi = balance * rate * (1 + rate) ** n / ((1 + rate) ** n - 1) if rate > 0 else balance / n

    for i in range(1, n + 1):
        q = moratorium_quarters + i
        interest = balance * rate
        principal_part = min(emi - interest, balance)
        total_interest += interest
        opening = balance
        balance -= principal_part
        rows.append(RepaymentRow(
            quarter=q, opening_balance=round(opening, 2),
            interest_due=round(interest, 2), principal_repaid=round(principal_part, 2),
            total_payment=round(interest + principal_part, 2),
            closing_balance=round(max(balance, 0.0), 2),
            phase="repayment",
        ))

    return rows, total_interest


def compute_loan_plan(margin_capital: float,
                      monthly_operating_cost: float | None = None) -> LoanPlan:
    """Route margin capital to a scheme and produce the full repayment roadmap."""
    project_cost = margin_capital / MARGIN_FRACTION

    if project_cost <= MICRO_MAX_PROJECT_COST:
        scheme = SchemeName.MICRO_FINANCE
        advice = None
    elif project_cost <= TERM_MAX_PROJECT_COST:
        scheme = SchemeName.TERM_LOAN
        advice = None
    else:
        # Above cap: cap at Term Loan maximum and advise
        scheme = SchemeName.TERM_LOAN
        advice = (
            f"Project cost of ₹{project_cost:,.0f} exceeds the ₹50 lakh Term Loan ceiling. "
            f"The plan below is capped at the maximum eligible loan of ₹45 lakh; consider "
            f"phasing the project or supplementing with other schemes."
        )

    cfg = SCHEMES[scheme]
    loan = min(project_cost * LOAN_FRACTION, cfg["max_loan"])

    schedule, total_interest = _build_schedule(
        loan, cfg["interest_rate_pa"], cfg["tenure_years"], cfg["moratorium_months"]
    )
    emi = next((r.total_payment for r in schedule if r.phase == "repayment"), 0.0)

    return LoanPlan(
        project_cost=round(project_cost, 2),
        margin_money=round(margin_capital, 2),
        max_loan_amount=round(loan, 2),
        scheme=scheme,
        interest_rate_pa=cfg["interest_rate_pa"],
        tenure_years=cfg["tenure_years"],
        moratorium_months=cfg["moratorium_months"],
        quarterly_emi=round(emi, 2),
        total_interest=round(total_interest, 2),
        total_repayment=round(loan + total_interest, 2),
        working_capital_estimate=round((monthly_operating_cost or project_cost * 0.02) * 6, 2),
        schedule=schedule,
        advice=advice,
    )
