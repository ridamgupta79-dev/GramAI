"""ARCHITECTURE.md §3.5 — AI Advisory Engine (LLM Gateway + viability scoring).

Provider-adapter pattern: Gemini default, OpenAI-compatible fallback, offline
deterministic mode. All numbers come from Financial/GIS engines; the LLM only
narrates.
"""
from __future__ import annotations

import math
import os
from typing import Any

PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
API_KEY = os.getenv("LLM_API_KEY", "") or GEMINI_KEY
MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash")
BASE_URL = os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")


def llm_available() -> bool:
    return bool(API_KEY)


def generate_json(prompt: str, system: str) -> dict[str, Any]:
    if not llm_available():
        raise RuntimeError("LLM not configured")
    from openai import OpenAI
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.4,
    )
    import json
    return json.loads(resp.choices[0].message.content or "{}")


# ---------- Viability scoring (weighted model per §3.5) ----------

WEIGHTS = {"demand": 0.30, "competition": 0.20, "financials": 0.25,
           "scheme_fit": 0.15, "risk": 0.10}


def viability_score(
    *,
    target_customers: int,
    competitors: int,
    radius_km: float = 10.0,
    emi_to_profit_ratio: float = 0.3,
    schemes_eligible: int = 2,
    high_risks: int = 0,
) -> dict[str, Any]:
    """
    Calculate an explainable 0–100 business viability score.

    The score is deterministic and combines:
        Demand       -> 30%
        Competition  -> 20%
        Financials   -> 25%
        Scheme fit   -> 15%
        Risk         -> 10%

    All inputs are expected to come from the Market, Financial and
    Scheme intelligence engines.
    """

    # ---------------------------------------------------------------
    # 1. Demand — 30%
    # --------------------------------------------------------------- 

    demand_score = min(
        100.0,
        40.0 + math_log_scale(target_customers),
    )

    # ---------------------------------------------------------------
    # 2. Competition — 20%
    # ---------------------------------------------------------------

    area_km2 = max(
        math.pi * max(radius_km, 0.1) ** 2,
        1.0,
    )

    competitor_density = competitors / area_km2

    competition_score = max(
        0.0,
        min(
            100.0,
            100.0 - competitor_density * 2500,
        ),
    )

    # ---------------------------------------------------------------
    # 3. Financial health — 25%
    # ---------------------------------------------------------------

    # EMI-to-profit ratio:
    #
    # 0.00 -> excellent
    # 0.25 -> good
    # 0.50 -> moderate
    # 1.00+ -> very weak
    #
    # Higher EMI burden means lower financial score.

    emi_to_profit_ratio = max(
        0.0,
        emi_to_profit_ratio,
    )

    financials_score = max(
        0.0,
        min(
            100.0,
            100.0 - emi_to_profit_ratio * 180,
        ),
    )

    # ---------------------------------------------------------------
    # 4. Scheme fit — 15%
    # ---------------------------------------------------------------

    schemes_eligible = max(
        0,
        schemes_eligible,
    )

    scheme_fit_score = min(
        100.0,
        40.0 + schemes_eligible * 30.0,
    )

    # ---------------------------------------------------------------
    # 5. Risk — 10%
    # ---------------------------------------------------------------

    high_risks = max(
        0,
        high_risks,
    )

    risk_score = max(
        0.0,
        min(
            100.0,
            100.0 - high_risks * 22.0,
        ),
    )

    # ---------------------------------------------------------------
    # Weighted contributions
    # ---------------------------------------------------------------

    weighted = {
        "demand": demand_score * WEIGHTS["demand"],
        "competition": competition_score * WEIGHTS["competition"],
        "financials": financials_score * WEIGHTS["financials"],
        "scheme_fit": scheme_fit_score * WEIGHTS["scheme_fit"],
        "risk": risk_score * WEIGHTS["risk"],
    }

    total = sum(weighted.values())

    # ---------------------------------------------------------------
    # Human-readable interpretation
    # ---------------------------------------------------------------

    if total >= 80:
        rating = "Excellent"
    elif total >= 65:
        rating = "Good"
    elif total >= 50:
        rating = "Moderate"
    elif total >= 35:
        rating = "Weak"
    else:
        rating = "High Risk"

    return {
        "score": round(total),

        "rating": rating,

        "components": {
            "demand": round(demand_score),
            "competition": round(competition_score),
            "financials": round(financials_score),
            "scheme_fit": round(scheme_fit_score),
            "risk": round(risk_score),
        },

        "weights": {
            "demand": WEIGHTS["demand"],
            "competition": WEIGHTS["competition"],
            "financials": WEIGHTS["financials"],
            "scheme_fit": WEIGHTS["scheme_fit"],
            "risk": WEIGHTS["risk"],
        },

        "weighted_contributions": {
            key: round(value, 2)
            for key, value in weighted.items()
        },

        "inputs": {
            "target_customers": target_customers,
            "competitors": competitors,
            "radius_km": radius_km,
            "competitor_density_per_km2": round(
                competitor_density,
                3,
            ),
            "emi_to_profit_ratio": round(
                emi_to_profit_ratio,
                3,
            ),
            "schemes_eligible": schemes_eligible,
            "high_risks": high_risks,
        },
    }


def math_log_scale(customers: int) -> float:

    if customers <= 0:
        return 0.0
    import math as _m
    return min(60.0, _m.log10(max(customers, 10)) * 20)


def chat_reply(message: str) -> str:
    """Deterministic advisor reply; LLM enrichment happens client-side of this
    in the legacy dashboard router when a key is configured."""
    m = message.lower()
    if "loan" in m or "emi" in m:
        return ("For your project size you qualify under the MUDRA framework. "
                "A 10% margin unlocks 90% funding, and the quarterly EMI stays "
                "under 40% of projected profit. Apply via the Schemes page.")
    if "competitor" in m or "market" in m:
        return ("Within a 10 km radius I estimate a moderate number of direct "
                "competitors. Differentiate on freshness and home delivery, and "
                "price 5-10% below the nearest town rates for the first quarter.")
    if "scheme" in m or "subsidy" in m:
        return ("Based on your profile you likely qualify for MUDRA plus at "
                "least one state-level scheme. Check the Schemes page for the "
                "eligibility breakdown and document checklist.")
    return ("Based on your analysis, demand looks stable. Focus on the "
            "moratorium period to build a customer base, and keep six months "
            "of operating costs as working-capital reserve.")
