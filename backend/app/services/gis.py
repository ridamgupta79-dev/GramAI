"""ARCHITECTURE.md §3.4 — GIS Engine (in-memory demo implementation).

Location hierarchy + POI radius queries.

For the prototype, synthetic POIs are generated relative to the selected
village coordinates. Production swaps the in-memory demo data for real
OpenStreetMap/Overpass + PostGIS data while keeping the same interface.
"""

from __future__ import annotations

import math
from functools import lru_cache

from app.services.location_data import hierarchy, village_by_id

EARTH_RADIUS_KM = 6371.0


def haversine_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Calculate the great-circle distance between two coordinates."""

    p1 = math.radians(lat1)
    p2 = math.radians(lat2)

    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = (
        math.sin(dp / 2) ** 2
        + math.cos(p1)
        * math.cos(p2)
        * math.sin(dl / 2) ** 2
    )

    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _pois_for_village(lat: float, lon: float) -> list[dict]:
    """Generate deterministic synthetic POIs around a village.

    These are DEMO/SYNTHETIC businesses used for the prototype.
    They are not real businesses and should not be presented as
    verified real-world listings.

    The offsets are intentionally small so the POIs fall within
    the selected village's local market area.
    """

    base = [
        # (name, layer, latitude offset, longitude offset)
        (
            "GramAI Demo Kirana Store",
            "competitor",
            0.010,
            0.008,
        ),
        (
            "GramAI Demo Agri Traders",
            "competitor",
            -0.014,
            0.012,
        ),
        (
            "GramAI Demo General Store",
            "competitor",
            0.022,
            0.018,
        ),
        (
            "GramAI Demo Weekly Market",
            "market",
            0.030,
            -0.020,
        ),
        (
            "GramAI Demo Mandi",
            "mandi",
            0.080,
            0.060,
        ),
        (
            "GramAI Demo Seeds & Fertilizer",
            "supplier",
            0.006,
            -0.010,
        ),
        (
            "GramAI Demo Dairy Collection Center",
            "supplier",
            -0.008,
            0.005,
        ),
    ]

    return [
        {
            "name": name,
            "layer": layer,
            "lat": round(lat + dlat, 5),
            "lon": round(lon + dlon, 5),
            "synthetic": True,
        }
        for name, layer, dlat, dlon in base
    ]


def nearby(
    village_id: int | None = None,
    lat: float | None = None,
    lon: float | None = None,
    radius_km: float = 10.0,
    layers: list[str] | None = None,
) -> dict:
    """Return synthetic POIs within a geographic radius.

    Location priority:
    1. Explicit latitude/longitude
    2. Village ID resolved through the location hierarchy

    Production implementation can replace the synthetic POI generator
    with PostGIS ST_DWithin queries without changing this API contract.
    """

    # Resolve coordinates from village ID when explicit coordinates
    # were not provided.
    if (lat is None or lon is None) and village_id is not None:
        village = village_by_id(village_id)

        if not village:
            return {
                "center": None,
                "pois": [],
                "density": {},
            }

        lat = village["lat"]
        lon = village["lon"]

    # Cannot perform a geographic query without coordinates.
    if lat is None or lon is None:
        return {
            "center": None,
            "pois": [],
            "density": {},
        }

    # Generate demo POIs around the selected village.
    demo_pois = _pois_for_village(lat, lon)

    wanted = set(
        layers
        or [
            "markets",
            "competitors",
            "suppliers",
        ]
    )

    layer_map = {
        "markets": {"market"},
        "mandis": {"mandi"},
        "competitors": {"competitor"},
        "suppliers": {"supplier"},
    }

    allowed: set[str] = set()

    for requested_layer in wanted:
        allowed.update(
            layer_map.get(
                requested_layer,
                {requested_layer.rstrip("s")},
            )
        )

    pois: list[dict] = []
    counts: dict[str, int] = {}

    for poi in demo_pois:
        if poi["layer"] not in allowed:
            continue

        distance = haversine_km(
            lat,
            lon,
            poi["lat"],
            poi["lon"],
        )

        if distance <= radius_km:
            pois.append(
                {
                    **poi,
                    "distance_km": round(distance, 2),
                }
            )

            layer = poi["layer"]
            counts[layer] = counts.get(layer, 0) + 1

    # Area of the search radius.
    area = math.pi * radius_km**2

    competitor_count = counts.get(
        "competitor",
        0,
    )

    supplier_count = counts.get(
        "supplier",
        0,
    )

    density = {
        "competitors_per_km2": round(
            competitor_count / area,
            4,
        ),
        "suppliers_per_km2": round(
            supplier_count / area,
            4,
        ),
        "counts": counts,
    }

    return {
        "center": {
            "lat": lat,
            "lon": lon,
        },
        "radius_km": radius_km,
        "pois": sorted(
            pois,
            key=lambda p: p["distance_km"],
        ),
        "density": density,
        "data_source": "synthetic_demo",
    }


def locations(
    state: str | None = None,
    district: str | None = None,
    block: str | None = None,
) -> dict:
    """Cascading location selects — ARCHITECTURE.md GET /api/geo/locations."""

    h = hierarchy()

    if state and district and block:
        return {
            "villages": h.get(
                state,
                {},
            ).get(
                district,
                {},
            ).get(
                block,
                [],
            )
        }

    if state and district:
        return {
            "blocks": list(
                h.get(
                    state,
                    {},
                ).get(
                    district,
                    {},
                ).keys()
            )
        }

    if state:
        return {
            "districts": list(
                h.get(
                    state,
                    {},
                ).keys()
            )
        }

    return {
        "states": list(h.keys()),
    }
