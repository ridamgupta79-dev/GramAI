"""ARCHITECTURE.md §5 — Geo endpoints (locations, nearby POIs)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from app.services import gis

router = APIRouter()


@router.get("/locations")
def locations(state: Optional[str] = None, district: Optional[str] = None,
              block: Optional[str] = None) -> dict:
    return gis.locations(state, district, block)


@router.get("/nearby")
def nearby(village_id: Optional[int] = None, lat: Optional[float] = None,
           lon: Optional[float] = None, radius_km: float = 10.0,
           layers: str = "markets,competitors,suppliers") -> dict:
    return gis.nearby(village_id=village_id, lat=lat, lon=lon,
                      radius_km=radius_km, layers=layers.split(","))
