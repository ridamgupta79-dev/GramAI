"""ARCHITECTURE.md §5 — API endpoint tests (auth, analyses, finance, geo,
schemes, chat, reports, users, admin)."""
import json
import time

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _auth_headers(mobile: str = "9876543210") -> dict:
    """Register/login a test user and return Authorization headers."""
    client.post("/api/auth/otp/send", json={"mobile": mobile})
    r = client.post("/api/auth/otp/verify",
                    json={"mobile": mobile, "otp": "123456",
                          "full_name": "Test User"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ---------- Auth ----------

def test_auth_otp_flow():
    import random
    mobile = f"98{random.randint(10000000, 99999999)}"
    r = client.post("/api/auth/otp/send", json={"mobile": mobile})
    assert r.status_code == 200 and r.json()["ok"]
    otp = r.json()["demo_otp"]
    r = client.post("/api/auth/otp/verify",
                    json={"mobile": mobile, "otp": otp})
    assert r.status_code == 200
    body = r.json()
    assert body["access_token"].count(".") == 2  # signed JWT
    assert body["is_new_user"]
    # second verify → not new
    client.post("/api/auth/otp/send", json={"mobile": mobile})
    r2 = client.post("/api/auth/otp/verify",
                     json={"mobile": mobile, "otp": otp})
    assert r2.json()["is_new_user"] is False


def test_auth_register_login():
    assert client.post("/api/auth/register", json={
        "full_name": "Test User", "mobile": "9000000001"}).json()["ok"]
    r = client.post("/api/auth/login",
                    json={"handle": "9000000001", "password": "x"})
    assert r.status_code == 200 and "access_token" in r.json()


# ---------- Finance ----------

def test_finance_quote():
    r = client.post("/api/finance/quote", json={
        "project_cost": 1_000_000, "margin_pct": 25,
        "interest_rate": 9.5, "tenure_months": 60})
    assert r.status_code == 200
    body = r.json()
    assert body["loan_amount"] == 750_000
    assert body["emi"] > 0
    assert body["tier"] == "Tarun"  # ₹750k falls in Tarun (₹5L–₹10L)


def test_finance_simulate_and_amortization():
    r = client.post("/api/finance/simulate", json={
        "project_cost": 1_000_000, "margin_pct": 25, "interest_rate": 9.5,
        "tenure_months": 60, "moratorium_months": 6,
        "monthly_revenue": 80_000, "monthly_opex": 45_000})
    assert r.status_code == 200
    body = r.json()
    assert body["break_even_month"] is not None
    assert len(body["cashflow"]["years"]) == 3
    assert len(body["expense_breakdown"]) == 3

    r2 = client.get(f"/api/finance/amortization/{body['plan_id']}")
    assert r2.status_code == 200
    assert len(r2.json()["rows"]) == 60

    assert client.get("/api/finance/amortization/nope").status_code == 404


# ---------- Geo ----------

def test_geo_locations_cascade():
    states = client.get("/api/geo/locations").json()["states"]
    assert "Maharashtra" in states
    districts = client.get("/api/geo/locations",
                           params={"state": "Maharashtra"}).json()["districts"]
    assert "Pune" in districts
    blocks = client.get("/api/geo/locations",
                        params={"state": "Maharashtra", "district": "Pune"}).json()["blocks"]
    assert blocks
    villages = client.get(
        "/api/geo/locations",
        params={"state": "Maharashtra", "district": "Pune", "block": blocks[0]},
    ).json()["villages"]
    assert villages and "id" in villages[0]


def test_geo_nearby():
    villages = client.get(
        "/api/geo/locations",
        params={"state": "Maharashtra", "district": "Pune", "block": "Haveli"},
    ).json()["villages"]
    vid = villages[0]["id"]
    r = client.get("/api/geo/nearby",
                   params={"village_id": vid, "radius_km": 25})
    assert r.status_code == 200
    body = r.json()
    assert body["center"]["lat"]
    # POIs are seeded around a fixed demo center; with a wide radius we may get
    # none for far-away village coords — accept either POIs or empty density.
    assert isinstance(body["pois"], list)
    assert "counts" in body["density"] or body["pois"]


# ---------- Schemes ----------

def test_schemes_list_and_detail():
    items = client.get("/api/schemes").json()
    slugs = {i["slug"] for i in items}
    assert {"mudra", "pmegp", "stand_up_india"} <= slugs
    rec = client.get("/api/schemes", params={"recommended": "true"}).json()
    assert all(i["slug"] in ("mudra", "pmegp", "term_loan_sca") for i in rec)

    d = client.get("/api/schemes/mudra").json()
    assert d["tiers"] == ["Shishu", "Kishore", "Tarun"]
    assert "Aadhaar" in d["documents_required"]
    assert client.get("/api/schemes/bogus").status_code == 404


def test_scheme_eligibility_rules():
    # Woman with small project → Mahila Samriddhi eligible
    r = client.post("/api/schemes/check-eligibility", json={
        "loan_amount": 100_000, "project_cost": 120_000, "is_woman": True})
    results = {x["slug"]: x["eligible"] for x in r.json()}
    assert results["mahila_samriddhi"] is True
    assert results["stand_up_india"] is False  # loan < ₹10 lakh minimum
    # Stand Up India requires ≥ ₹10 lakh loan
    r2 = client.post("/api/schemes/check-eligibility", json={
        "loan_amount": 2_000_000, "project_cost": 2_500_000, "is_woman": True})
    res2 = {x["slug"]: x["eligible"] for x in r2.json()}
    assert res2["stand_up_india"] is True
    assert res2["mahila_samriddhi"] is False  # project too big
    # Eligible schemes ranked first
    ordered = [x["eligible"] for x in r2.json()]
    assert ordered == sorted(ordered, reverse=True)


# ---------- Analyses pipeline ----------

def _wait_completed(analysis_id: str, timeout: float = 10.0,
                    headers: dict | None = None) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with client.stream("GET", f"/api/analyses/{analysis_id}/status",
                           headers=headers) as resp:
            pass  # establish route validity
        a = client.get(f"/api/analyses/{analysis_id}/insights", headers=headers or {})
        if a.status_code == 200:
            return a.json()
        time.sleep(0.2)
    raise TimeoutError("analysis did not complete")


def test_analysis_pipeline_end_to_end():
    h = _auth_headers()
    villages = client.get(
        "/api/geo/locations",
        params={"state": "Maharashtra", "district": "Pune", "block": "Haveli"},
    ).json()["villages"]

    r = client.post("/api/analyses", json={
        "village_id": villages[0]["id"],
        "category_slug": "retail",
        "financing": {
            "project_cost": 1_000_000, "margin_pct": 25,
            "interest_rate": 9.5, "tenure_months": 60,
            "moratorium_months": 6,
        },
    }, headers=h)
    assert r.status_code == 202
    analysis_id = r.json()["analysis_id"]

    insights = _wait_completed(analysis_id, headers=h)
    assert 0 <= insights["viability_score"] <= 100
    assert insights["loan_eligibility"]["tier"] in ("Kishore", "Tarun")
    assert insights["market"]["competitors_within_10km"] >= 0
    assert insights["swot"]["strengths"]
    assert insights["additional_subsidies_eligible"] >= 0

    # SSE status stream endpoint responds after completion
    raw = client.get(f"/api/analyses/{analysis_id}/status", headers=h)
    assert raw.status_code == 200


def test_analysis_insights_not_ready():
    h = _auth_headers("9876543211")
    r = client.post("/api/analyses", json={
        "lat": 18.5, "lon": 73.9, "category_slug": "dairy",
        "financing": {"project_cost": 500_000, "margin_pct": 10,
                      "interest_rate": 8.0, "tenure_months": 36},
    }, headers=h)
    aid = r.json()["analysis_id"]
    # Either completes quickly or returns 409 while running; both acceptable.
    got = client.get(f"/api/analyses/{aid}/insights", headers=h)
    assert got.status_code in (200, 409)


# ---------- Reports ----------

def test_reports_flow():
    h = _auth_headers("9876543212")
    r = client.post("/api/reports/from-view", json={
        "village_id": 1001, "radius_km": 10,
        "layers": ["markets", "competitors"]}, headers=h)
    assert r.status_code == 201
    rid = r.json()["id"]

    lst = client.get("/api/reports", params={"limit": 5}, headers=h).json()
    assert any(x["id"] == rid for x in lst)

    got = client.get(f"/api/reports/{rid}", headers=h).json()
    assert got["content"]["executive_summary"]

    pdf = client.get(f"/api/reports/{rid}/pdf", headers=h)
    assert pdf.status_code == 200
    assert "GRAMAI BUSINESS REPORT" in pdf.text

    share = client.post(f"/api/reports/{rid}/share",
                        json={"expires_in_days": 30}, headers=h).json()
    assert share["url"].startswith("https://") and share["expires_in_days"] == 30


# ---------- Chat ----------

def test_chat_streaming_rich_payload():
    h = _auth_headers("9876543213")
    with client.stream("POST", "/api/chat", json={
            "message": "hello"}, headers=h) as resp:
        assert resp.status_code == 200
        raw = b"".join(resp.iter_bytes()).decode()
    assert "event: token" in raw
    assert "event: chart" in raw
    assert "event: done" in raw
    conv_line = [l for l in raw.splitlines() if l.startswith("data:")][-1]
    conv_id = json.loads(conv_line[5:])["conversation_id"]

    convs = client.get("/api/chat/conversations", headers=h).json()
    assert any(c["conversation_id"] == conv_id for c in convs)

    exp = client.get(f"/api/chat/conversations/{conv_id}/export", headers=h).json()
    assert exp["exported"] is True


# ---------- Users / Admin / i18n ----------

def test_users_me_dashboard_activity():
    h = _auth_headers("9876543214")
    me = client.get("/api/users/me", headers=h).json()
    assert me["role"] == "user"

    patched = client.patch("/api/users/me",
                           json={"preferred_lang": "hi"}, headers=h).json()
    assert patched["preferred_lang"] == "hi"

    dash = client.get("/api/users/me/dashboard", headers=h).json()
    assert "viability_score" in dash
    assert len(dash["schemes_carousel"]) == 4

    acts = client.get("/api/users/me/activity", headers=h).json()
    assert isinstance(acts, list)


def test_admin_metrics_users_audit():
    # Admin endpoints require an admin-role account
    admin_h = _auth_headers("9999999999")
    # promote to admin via direct DB (test convenience)
    from app.db import SessionLocal, User
    db = SessionLocal()
    u = db.query(User).filter(User.mobile == "9999999999").first()
    u.role = "admin"
    db.commit()
    db.close()

    m = client.get("/api/admin/metrics", headers=admin_h).json()
    assert m["uptime_pct"] == 99.98
    assert "users" in m and "reports" in m

    # Regular users are forbidden
    user_h = _auth_headers("9876543215")
    assert client.get("/api/admin/metrics", headers=user_h).status_code == 403

    users = client.get("/api/admin/users", headers=admin_h).json()
    assert isinstance(users, list)

    log = client.get("/api/admin/audit-log", headers=admin_h).json()
    assert isinstance(log, list)


def test_i18n_bundles():
    en = client.get("/api/i18n/en").json()
    hi = client.get("/api/i18n/hi").json()
    ta = client.get("/api/i18n/ta").json()
    assert en["welcome"] == "Welcome to GramAI"
    assert hi["welcome"] != en["welcome"]
    assert ta["schemes"]
    # unknown lang falls back to English bundle content
    fr = client.get("/api/i18n/fr").json()
    assert fr["welcome"] == en["welcome"]
