"""API smoke tests."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_finance_plan_endpoint():
    r = client.post("/api/v1/finance/plan", json={"margin_capital": 100_000})
    assert r.status_code == 200
    body = r.json()
    assert body["project_cost"] == 1_000_000
    assert body["max_loan_amount"] == 900_000
    assert body["scheme"] == "Term Loan Scheme"


def test_location_endpoints():
    states = client.get("/api/v1/location/states").json()
    assert "Maharashtra" in states
    blocks = client.get("/api/v1/location/blocks",
                        params={"state": "Maharashtra", "district": "Pune"}).json()
    assert "Haveli" in blocks


def test_feasibility_report_fallback():
    r = client.post("/api/v1/feasibility/report", json={
        "location": {"village": "Wadki", "block": "Haveli",
                     "district": "Pune", "state": "Maharashtra"},
        "sector": "dairy",
        "margin_capital": 100_000,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["swot"]["strengths"]
    assert body["competitor_mapping"]["estimated_competitors_in_block"] > 0
