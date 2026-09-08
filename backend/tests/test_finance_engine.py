"""Unit tests for the deterministic finance engine (Module 2)."""
import pytest

from app.finance.engine import compute_loan_plan
from app.models.schemas import SchemeName


def test_micro_finance_routing():
    # Project cost = 1,40,000 exactly -> Micro Finance boundary
    plan = compute_loan_plan(14_000)
    assert plan.scheme == SchemeName.MICRO_FINANCE
    assert plan.project_cost == 140_000
    assert plan.max_loan_amount == 125_000  # capped at scheme max
    assert plan.interest_rate_pa == 6.5
    assert plan.tenure_years == 3
    assert plan.moratorium_months == 3


def test_term_loan_routing():
    plan = compute_loan_plan(100_000)  # ₹10L project, ₹9L loan
    assert plan.scheme == SchemeName.TERM_LOAN
    assert plan.project_cost == pytest.approx(1_000_000)
    assert plan.max_loan_amount == pytest.approx(900_000)
    assert plan.interest_rate_pa == 8.0
    assert plan.tenure_years == 7
    assert plan.moratorium_months == 6


def test_above_cap_advice():
    plan = compute_loan_plan(600_000)  # ₹60L project > ₹50L cap
    assert plan.advice is not None
    assert plan.max_loan_amount == 4_500_000


def test_schedule_structure():
    plan = compute_loan_plan(100_000)
    total_quarters = plan.tenure_years * 4
    assert len(plan.schedule) == total_quarters
    moratorium_qs = -(-plan.moratorium_months // 4)
    assert all(r.phase == "moratorium" for r in plan.schedule[:moratorium_qs])
    assert all(r.phase == "repayment" for r in plan.schedule[moratorium_qs:])
    # Balance fully repaid at end
    assert plan.schedule[-1].closing_balance == pytest.approx(0, abs=1)


def test_totals_consistency():
    plan = compute_loan_plan(50_000)
    principal_paid = sum(r.principal_repaid for r in plan.schedule)
    interest_paid = sum(r.interest_due for r in plan.schedule)
    assert principal_paid == pytest.approx(plan.max_loan_amount, abs=1)
    assert interest_paid == pytest.approx(plan.total_interest, abs=1)
    assert plan.total_repayment == pytest.approx(plan.max_loan_amount + plan.total_interest, abs=1)
