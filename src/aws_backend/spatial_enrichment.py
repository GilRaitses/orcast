"""Per-cell spatial covariates for the San Juan forecast grid.

Combines committed bathymetry, the land mask, and shoreline distance into one
record per water grid cell. Used for provenance/spatial integrity metadata and
future ``s_space`` modeling.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .geo_region import SAN_JUAN_BOUNDS, in_bounds, is_in_water, nearest_shore_m
from .sources.bathymetry import BathymetryAdapter

SPATIAL_GRID_STREAM = "spatial_grid_covariates"
DEFAULT_GRID_STATION = "san_juan_pilot"
DEFAULT_STEP_DEGREES = 0.05

_grid_cache: Dict[str, Any] = {"loaded_at": None, "cells": []}


def cell_id_for(lat: float, lng: float) -> str:
    return f"{lat:.3f}:{lng:.3f}"


def build_grid_cells(
    step_degrees: float = DEFAULT_STEP_DEGREES,
    bathymetry: Optional[BathymetryAdapter] = None,
) -> List[Dict[str, Any]]:
    """Build spatial covariate records for every in-water grid point."""
    bathy = bathymetry or BathymetryAdapter()
    bathy.load()
    now = datetime.now(timezone.utc).isoformat()
    cells: List[Dict[str, Any]] = []

    lat = SAN_JUAN_BOUNDS.min_lat
    while lat <= SAN_JUAN_BOUNDS.max_lat + 1e-9:
        lng = SAN_JUAN_BOUNDS.min_lng
        while lng <= SAN_JUAN_BOUNDS.max_lng + 1e-9:
            if is_in_water(lat, lng):
                cells.append(
                    {
                        "t": now,
                        "id": cell_id_for(lat, lng),
                        "cell_id": cell_id_for(lat, lng),
                        "lat": round(lat, 6),
                        "lng": round(lng, 6),
                        "depth_m": bathy.depth_at(lat, lng),
                        "nearest_shore_m": nearest_shore_m(lat, lng),
                        "inside_land": False,
                        "source": "orcast_spatial_enrichment",
                        "bathymetry_source": bathy.summary().get("source"),
                    }
                )
            lng += step_degrees
        lat += step_degrees
    return cells


def lookup_cell(lat: float, lng: float, cells: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Return the nearest grid cell covariates for a coordinate."""
    if not in_bounds(lat, lng):
        return {"available": False, "reason": "outside_pilot_region"}

    target_id = cell_id_for(lat, lng)
    source_cells = cells if cells is not None else _grid_cache.get("cells") or []
    for cell in source_cells:
        if cell.get("cell_id") == target_id:
            return {"available": True, **cell}

    bathy = BathymetryAdapter()
    return {
        "available": True,
        "cell_id": target_id,
        "lat": round(lat, 6),
        "lng": round(lng, 6),
        "depth_m": bathy.depth_at(lat, lng),
        "nearest_shore_m": nearest_shore_m(lat, lng),
        "inside_land": not is_in_water(lat, lng),
        "source": "orcast_spatial_enrichment",
    }


def load_cells_from_store(store, station: str = DEFAULT_GRID_STATION) -> List[Dict[str, Any]]:
    """Load cached spatial grid records from the time-series store."""
    start = datetime(1970, 1, 1, tzinfo=timezone.utc)
    end = datetime(2100, 1, 1, tzinfo=timezone.utc)
    try:
        records = store.get_series(SPATIAL_GRID_STREAM, station, start, end)
    except Exception:
        records = []
    _grid_cache["cells"] = list(records)
    _grid_cache["loaded_at"] = datetime.now(timezone.utc).isoformat()
    return _grid_cache["cells"]
