"""Deterministic fallback report generator — used when no LLM is configured."""
from __future__ import annotations

from app.models.schemas import (
    CompetitorMapping, FeasibilityReport, FeasibilityRequest, MarketReach,
    PricingInsight, SWOT,
)

SECTOR_LABELS = {
    "dairy": "dairy farming", "retail": "retail kirana store",
    "textiles": "textile & garment unit", "food_processing": "food processing unit",
    "agriservices": "agri-services centre", "poultry": "poultry farm",
    "handicrafts": "handicrafts workshop", "other": "micro-enterprise",
}


def build_fallback_report(req: FeasibilityRequest, demo: dict,
                          competitors: dict) -> FeasibilityReport:
    sector_label = SECTOR_LABELS.get(req.sector.value, req.sector.value)
    pop5 = int(demo["block_population"] * 0.18)
    pop10 = int(demo["block_population"] * 0.35)

    return FeasibilityReport(
        location=req.location,
        sector=req.sector,
        market_reach=MarketReach(
            estimated_population_5km=pop5,
            estimated_population_10km=pop10,
            target_customer_base=int(pop10 * 0.4),
            primary_distribution_channels=[
                "Weekly village haat / market", "Local kirana retailers",
                "Direct-to-consumer home delivery", "Block-level wholesale market",
            ],
        ),
        opportunity_analysis=[
            f"Demand for quality {sector_label} services in {req.location.block} block "
            f"is underserved given an estimated customer base of ~{int(pop10*0.4):,}.",
            "Limited organised competition within a 10 km radius creates first-mover advantage.",
            "Government scheme backing reduces initial capital burden (90% concessional funding).",
        ],
        swot=SWOT(
            strengths=[
                "Low operating overheads in rural location",
                "Concessional credit at subsidised interest rate",
                "Owner's direct community relationships build trust quickly",
            ],
            weaknesses=[
                "First-time entrepreneur without formal business training",
                "Limited working capital buffer beyond margin contribution",
                "Dependence on seasonal local demand",
            ],
            opportunities=[
                "Growing rural purchasing power and digital payment adoption",
                "Potential tie-ups with SHGs and self-help collectives",
                "Scope to add value-added services over time",
            ],
            threats=[
                "Seasonal demand fluctuation tied to harvest cycles",
                "Supply chain bottlenecks for inputs from distant markets",
                "Entry of better-funded competitors if the niche proves profitable",
            ],
        ),
        threats=[
            "Dependency on single bulk buyer risks income shocks.",
            "Monsoon/harvest seasonality can reduce cash flow by 30–40% in lean months.",
            "Input price volatility squeezes margins; maintain supplier alternatives.",
        ],
        competitor_mapping=CompetitorMapping(**competitors),
        pricing=PricingInsight(
            suggested_price_range="Mid-market: 5–10% below nearest town rates to win share",
            predicted_local_market_value=(
                f"Estimated addressable annual spend of ₹{int(pop10*0.4)*1200:,} "
                f"(~₹1,200/yr per household on this category)"
            ),
            rationale="Based on regional purchasing power proxies (rural per-capita consumption).",
        ),
        summary=(
            f"A {sector_label} venture in {req.location.village or req.location.block} appears "
            f"feasible with {competitors['density_assessment']} competition. With "
            f"₹{req.margin_capital:,.0f} margin you qualify for ~₹{req.margin_capital*9:,.0f} "
            f"in concessional credit. Prioritise working-capital discipline through the "
            f"moratorium period and diversify buyers early."
        ),
    )
