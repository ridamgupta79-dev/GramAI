"""Feasibility report generation — Module 1.

LLM + RAG when configured; deterministic template fallback otherwise.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import FeasibilityReport, FeasibilityRequest
from app.services import llm_service
from app.services.competitor_estimator import estimate_competitors
from app.services.report_fallback import build_fallback_report

router = APIRouter()

SYSTEM_PROMPT = """You are an expert rural business consultant for Indian
micro-enterprise schemes (NSFDC/NBCFDC-style Micro Finance & Term Loan).
Generate a hyper-local business feasibility analysis. Respond ONLY with a JSON
object matching this schema:
{
  "market_reach": {"estimated_population_5km": int, "estimated_population_10km": int,
                   "target_customer_base": int, "primary_distribution_channels": [str]},
  "opportunity_analysis": [str],
  "swot": {"strengths": [str], "weaknesses": [str], "opportunities": [str], "threats": [str]},
  "threats": [str],
  "pricing": {"suggested_price_range": str, "predicted_local_market_value": str, "rationale": str},
  "summary": str
}
Ground every claim in the provided local context. Use simple language suitable
for first-time rural entrepreneurs."""


@router.post("/report", response_model=FeasibilityReport)
def generate_report(req: FeasibilityRequest) -> FeasibilityReport:
    from app.routers.location import profile

    try:
        demo = profile(req.location.state, req.location.district,
                       req.location.block, req.location.village)
    except HTTPException:
        raise

    competitors = estimate_competitors(
        demo["block_population"], req.sector.value, demo["urbanization_factor"]
    )

    if llm_service.llm_available():
        prompt = (
            f"Location: village={req.location.village}, block={req.location.block}, "
            f"district={req.location.district}, state={req.location.state}.\n"
            f"Local context: {demo}\n"
            f"Sector: {req.sector.value}. Beneficiary margin capital: ₹{req.margin_capital:,.0f} "
            f"(implied project cost ₹{req.margin_capital * 10:,.0f}).\n"
            f"Competitor estimate: {competitors}\n"
            f"Produce the feasibility JSON now."
        )
        try:
            data = llm_service.generate_json(prompt, SYSTEM_PROMPT)
        except Exception:
            data = None
    else:
        data = None

    if data is None:
        return build_fallback_report(req, demo, competitors)

    # Merge deterministic competitor mapping (never trust LLM numbers here)
    data["location"] = req.location.model_dump()
    data["sector"] = req.sector.value
    data["competitor_mapping"] = competitors
    return FeasibilityReport.model_validate(data)
