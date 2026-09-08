"""Heuristic competitor density estimator.

Village-level competitor registries don't exist publicly; we estimate using
block population × sector employment share × urbanization factor, clearly
labelled as estimates.
"""
from __future__ import annotations

SECTOR_EMPLOYMENT_SHARE = {
    "dairy": 0.045,
    "retail": 0.060,
    "textiles": 0.030,
    "food_processing": 0.020,
    "agriservices": 0.025,
    "poultry": 0.015,
    "handicrafts": 0.018,
    "other": 0.030,
}


def estimate_competitors(block_population: int, sector: str,
                         urbanization_factor: float) -> dict:
    share = SECTOR_EMPLOYMENT_SHARE.get(sector, 0.03)
    # Roughly 1 enterprise per 12 people employed in the sector; scale down for rural areas.
    raw = block_population * share / 12 * (1 - urbanization_factor * 0.5)
    competitors = max(3, round(raw))
    if competitors < 15:
        density = "low"
    elif competitors < 40:
        density = "medium"
    else:
        density = "high"
    return {
        "estimated_competitors_in_block": competitors,
        "density_assessment": density,
        "notes": (
            f"Heuristic estimate based on block population of {block_population:,}, "
            f"sectoral employment share of {share:.1%} and urbanization factor "
            f"{urbanization_factor:.0%}. Treat as indicative, not surveyed data."
        ),
    }
