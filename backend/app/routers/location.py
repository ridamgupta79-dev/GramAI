"""Location resolver — cascading village/block/district lookup.

Backed by a seeded LGD-style dataset (JSON) for demo purposes; swap for
Postgres-backed LGD data in production.
"""

import json
import os
from functools import lru_cache
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.services.location_data import hierarchy

router = APIRouter()

_DATA_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "locations.json",
)


@lru_cache
def _load_locations() -> dict:
    path = os.path.abspath(_DATA_PATH)

    if not os.path.exists(path):
        return {}

    with open(path, encoding="utf-8") as f:
        return json.load(f)


@router.get("/states")
def states() -> list[str]:
    return sorted(_load_locations().keys())


@router.get("/districts")
def districts(state: str) -> list[str]:
    data = _load_locations()

    if state not in data:
        raise HTTPException(
            404,
            f"Unknown state: {state}",
        )

    return sorted(data[state].keys())


@router.get("/blocks")
def blocks(
    state: str,
    district: str,
) -> list[str]:
    data = _load_locations()

    try:
        return sorted(
            data[state][district].keys()
        )
    except KeyError:
        raise HTTPException(
            404,
            "Unknown state/district",
        )


@router.get("/villages")
def villages(
    state: str,
    district: str,
    block: str,
) -> list[str]:
    data = _load_locations()

    try:
        return sorted(
            data[state][district][block]
        )
    except KeyError:
        raise HTTPException(
            404,
            "Unknown block",
        )


def _resolve_village(
    state: str,
    district: str,
    block: str,
    village: str,
) -> dict | None:
    """Resolve a village name to its seeded village object."""

    h = hierarchy()

    state_data = h.get(state)

    if not state_data:
        return None

    district_data = state_data.get(district)

    if not district_data:
        return None

    villages_data = district_data.get(block)

    if not villages_data:
        return None

    for item in villages_data:
        if item["name"] == village:
            return item

    return None


@router.get("/profile")
def profile(
    state: str,
    district: str,
    block: str,
    village: Optional[str] = None,
) -> dict:
    """Resolve location and return its demo demographic profile."""

    data = _load_locations()

    base = (
        data
        .get(state, {})
        .get(district, {})
        .get(block)
    )

    if base is None:
        raise HTTPException(
            404,
            "Unknown location",
        )

    result = {
        "state": state,
        "district": district,
        "block": block,
        "village": village,
        "block_population": 120_000,
        "urbanization_factor": 0.25,
        "literacy_rate": 0.68,
        "main_occupations": [
            "agriculture",
            "animal husbandry",
            "small trade",
        ],
    }

    if village:
        resolved = _resolve_village(
            state,
            district,
            block,
            village,
        )

        if not resolved:
            raise HTTPException(
                404,
                "Unknown village",
            )

        result["village_id"] = resolved["id"]
        result["latitude"] = resolved["lat"]
        result["longitude"] = resolved["lon"]
        result["village_population"] = resolved[
            "population"
        ]

    return result