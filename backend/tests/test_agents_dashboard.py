"""Tests for RAG service, agents, and dashboard endpoints."""
from fastapi.testclient import TestClient

from app.main import app
from app.services.rag_service import retrieve

client = TestClient(app)


def _auth_headers(mobile: str = "9988776655") -> dict:
    client.post("/api/auth/otp/send", json={"mobile": mobile})
    r = client.post("/api/auth/otp/verify",
                    json={"mobile": mobile, "otp": "123456",
                          "full_name": "Dash User"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_rag_retrieval():
    docs = retrieve("micro finance scheme interest rate moratorium")
    assert docs[0]["id"] == "micro_finance"
    docs = retrieve("women beneficiary loan")
    ids = {d["id"] for d in docs}
    assert "mahila_samriddhi" in ids or "new_swarnima" in ids


def _generate_dashboard() -> dict:
    h = _auth_headers()
    r = client.post("/api/v1/dashboard/generate", json={
        "location": {"village": "Wadki", "block": "Haveli",
                     "district": "Pune", "state": "Maharashtra"},
        "sector": "dairy",
        "margin_capital": 100_000,
        "gender": "female",
    }, headers=h)
    assert r.status_code == 200
    body = r.json()
    expected_topics = {
        "loan_eligibility", "scheme_recommendation", "market_demand",
        "competitor_map", "swot_analysis", "risk_analysis", "pricing_suggestions",
        "working_capital", "emi_schedule", "cash_flow_forecast", "ai_mentor",
    }
    assert set(body["sections"].keys()) == expected_topics
    # scheme recommendation grounded correctly
    rec = body["sections"]["scheme_recommendation"]["data"]["recommended"][0]
    assert rec["scheme"] == "Term Loan Scheme"
    # women-specific cross-sell present
    schemes = [r2["scheme"] for r2 in body["sections"]["scheme_recommendation"]["data"]["recommended"]]
    assert any("Women" in s or "Mahila" in s for s in schemes)
    return body


def test_dashboard_generate():
    body = _generate_dashboard()
    assert body["report_id"]


def test_dashboard_download_and_apply():
    h = _auth_headers()
    body = _generate_dashboard()
    rid = body["report_id"]
    dl = client.get(f"/api/v1/dashboard/{rid}/download", headers=h)
    assert dl.status_code == 200
    text = dl.text
    assert "LOAN ELIGIBILITY" in text and "EMI SCHEDULE" in text

    ap = client.post("/api/v1/dashboard/apply", json={
        "report_id": rid, "applicant_name": "Test User",
        "phone": "9999999999", "scheme": "Term Loan Scheme",
    }, headers=h)
    assert ap.status_code == 200
    assert ap.json()["application_id"].startswith("APP-")


def test_cashflow_forecast_shape():
    body = _generate_dashboard()
    forecast = body["sections"]["cash_flow_forecast"]["data"]["forecast"]
    assert len(forecast) == 28  # 7 years x 4 quarters
    assert all("cumulative_cash" in row for row in forecast)
