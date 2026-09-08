"""Seeded location data with LGD-style codes and coordinates.

Demo dataset; production loads from Census/LGD into PostGIS.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "locations.json")


@lru_cache
def hierarchy() -> dict:
    path = os.path.abspath(_DATA_PATH)
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    out: dict = {}
    vid = 1000
    for state, districts in raw.items():
        out[state] = {}
        for district, blocks in districts.items():
            out[state][district] = {}
            for block, villages in blocks.items():
                out[state][district][block] = []
                for i, village in enumerate(villages):
                    vid += 1
                    out[state][district][block].append({
                        "id": vid, "name": village,
                        "lat": round(18.40 + (vid % 50) * 0.01, 4),
                        "lon": round(73.85 + (vid % 37) * 0.011, 4),
                        "population": 1200 + (vid % 17) * 350,
                    })
    return out


def village_by_id(village_id: int) -> dict | None:
    for districts in hierarchy().values():
        for blocks in districts.values():
            for villages in blocks.values():
                for v in villages:
                    if v["id"] == village_id:
                        return v
    return None
