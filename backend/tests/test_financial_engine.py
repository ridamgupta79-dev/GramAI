"""ARCHITECTURE.md §3.3 — Financial Engine unit tests (pure functions)."""
import pytest

from app.services.financial import (
    amortization_schedule, break_even_month, cashflow_projection,
    monthly_emi, mudra_tier, quote, working_capital_estimate,
)


def test_mudra_tiers():
    assert mudra_tier(40_000) == "Shishu"
    assert mudra_tier(50_000) == "Shishu"
    assert mudra_tier(50_001) == "Kishore"
    assert mudra_tier(500_000) == "Kishore"
    assert mudra_tier(800_000) == "Tarun"
    assert mudra_tier(1_000_000) == "Tarun"


def test_emi_zero_interest():
    assert monthly_emi(120_000, 0, 12) == pytest.approx(10_000)


def test_emi_known_value():
    # ₹10L @ 9.5% for 60 months ≈ 20,957 (standard amortization)
    emi = monthly_emi(1_000_000, 9.5, 60)
    assert 20_500 < emi < 21_400


def test_schedule_fully_amortizes():
    rows = amortization_schedule(100_000, 8.0, 24)
    assert len(rows) == 24
    assert rows[-1]["closing_balance"] == pytest.approx(0, abs=0.5)
    principal_sum = sum(r["principal"] for r in rows)
    assert principal_sum == pytest.approx(100_000, abs=0.5)


def test_moratorium_interest_only():
    rows = amortization_schedule(100_000, 8.0, 24, moratorium_months=6)
    mor = [r for r in rows if r["phase"] == "moratorium"]
    rep = [r for r in rows if r["phase"] == "repayment"]
    assert len(mor) == 6 and len(rep) == 18
    assert all(r["principal"] == 0 for r in mor)
    assert all(r["payment"] == r["interest"] for r in mor)
    assert rows[-1]["closing_balance"] == pytest.approx(0, abs=0.5)


def test_quote_matches_spec_example():
    q = quote(project_cost=1_000_000, margin_pct=25, interest_rate=9.5,
              tenure_months=60)
    assert q.loan_amount == 750_000
    assert q.emi > 0
    assert q.total_interest > 0


def test_break_even():
    # Fixed 200k; contribution 20/unit × 500 units = 10k/month → 20 months
    assert break_even_month(200_000, 50, 30, 500) == 20
    assert break_even_month(200_000, 30, 30, 500) is None  # no contribution


def test_cashflow_projection_shape():
    cf = cashflow_projection(1_000_000, 750_000, 9.5, 60, 6,
                             80_000, 45_000, years=3)
    assert len(cf["years"]) == 3
    y1 = cf["years"][0]
    for key in ("revenue", "operating_expenses", "debt_service",
                "net_cash_flow", "cumulative_cash"):
        assert key in y1


def test_working_capital():
    assert working_capital_estimate(30_000, months=6) == 180_000
