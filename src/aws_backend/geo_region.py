"""San Juan archipelago geo helpers: region bounding, land/water testing, and
snap-to-water.

These mirror the frontend rules in ``orcast-angular/src/app/services/geo-region.ts``
so the API itself emits clean data: orcas only on water, the pilot region only.
See ``docs/ux/MAP_DATA_TRUTH.md`` for the rules these implement.

The water/land mask source is ``data/geo/san_juan_land.geojson`` (a
FeatureCollection of island Polygon features with ``[lng, lat]`` rings). If the
file is missing the helpers degrade to permissive behavior (everything in bounds
is treated as water) and log a warning, so ingestion never hard-fails on a
missing mask.
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from .config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RegionBounds:
    min_lat: float
    max_lat: float
    min_lng: float
    max_lng: float


# Approximate San Juan / Orcas / Lopez / Shaw envelope. Any point outside this
# box is excluded from map layers.
SAN_JUAN_BOUNDS = RegionBounds(min_lat=48.40, max_lat=48.70, min_lng=-123.25, max_lng=-122.75)

_GEOJSON_RELATIVE = ("data", "geo", "san_juan_land.geojson")

# Snap-to-water sampling parameters (match the frontend implementation).
_SNAP_STEP_DEG = 0.005  # ~0.5 km
_SNAP_MAX_RINGS = 12  # up to ~6 km out
_SNAP_DIRECTIONS = 16


def _resolve_geojson_path() -> Path:
    repo_path = Path(settings.repo_root).joinpath(*_GEOJSON_RELATIVE)
    if repo_path.exists():
        return repo_path
    # Fallback: walk up from this module to find the repo root.
    module_relative = Path(__file__).resolve().parents[2].joinpath(*_GEOJSON_RELATIVE)
    return module_relative


def _load_land_polygons() -> List[List[Tuple[float, float]]]:
    """Load every polygon ring as a list of ``(lng, lat)`` tuples."""
    path = _resolve_geojson_path()
    if not path.exists():
        logger.warning(
            "San Juan land mask not found at %s; land/water filtering is permissive (all in-bounds points treated as water)",
            path,
        )
        return []
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, ValueError) as exc:  # pragma: no cover - defensive
        logger.warning("Failed to load San Juan land mask at %s: %s; filtering is permissive", path, exc)
        return []

    rings: List[List[Tuple[float, float]]] = []
    for feature in data.get("features", []):
        geometry = feature.get("geometry") or {}
        geom_type = geometry.get("type")
        coords = geometry.get("coordinates") or []
        if geom_type == "Polygon":
            polygons = [coords]
        elif geom_type == "MultiPolygon":
            polygons = coords
        else:
            continue
        for polygon in polygons:
            for ring in polygon:
                cleaned = [(float(pt[0]), float(pt[1])) for pt in ring if len(pt) >= 2]
                if len(cleaned) >= 3:
                    rings.append(cleaned)
    if not rings:
        logger.warning("San Juan land mask at %s contained no usable polygon rings", path)
    return rings


_LAND_RINGS: List[List[Tuple[float, float]]] = _load_land_polygons()


def in_bounds(lat: float, lng: float) -> bool:
    """True when a point is inside the archipelago bounding box."""
    try:
        lat = float(lat)
        lng = float(lng)
    except (TypeError, ValueError):
        return False
    if not (math.isfinite(lat) and math.isfinite(lng)):
        return False
    return (
        SAN_JUAN_BOUNDS.min_lat <= lat <= SAN_JUAN_BOUNDS.max_lat
        and SAN_JUAN_BOUNDS.min_lng <= lng <= SAN_JUAN_BOUNDS.max_lng
    )


def _point_in_ring(lat: float, lng: float, ring: List[Tuple[float, float]]) -> bool:
    """Ray-casting point-in-polygon over a single ``[lng, lat]`` ring."""
    inside = False
    count = len(ring)
    j = count - 1
    for i in range(count):
        xi, yi = ring[i]
        xj, yj = ring[j]
        denom = (yj - yi) or 1e-12
        intersects = (yi > lat) != (yj > lat) and lng < (xj - xi) * (lat - yi) / denom + xi
        if intersects:
            inside = not inside
        j = i
    return inside


def is_on_land(lat: float, lng: float) -> bool:
    """True when a point falls on one of the island landmasses."""
    try:
        lat = float(lat)
        lng = float(lng)
    except (TypeError, ValueError):
        return False
    for ring in _LAND_RINGS:
        if _point_in_ring(lat, lng, ring):
            return True
    return False


def is_in_water(lat: float, lng: float) -> bool:
    """True when a point is in the region and not on land."""
    return in_bounds(lat, lng) and not is_on_land(lat, lng)


def snap_to_water(lat: float, lng: float) -> Tuple[float, float]:
    """Return the point unchanged if it is on water; otherwise nudge it to the
    nearest in-water point by sampling expanding rings (mirrors the frontend).
    Falls back to the original point if no nearby water is found.
    """
    lat = float(lat)
    lng = float(lng)
    if is_in_water(lat, lng):
        return lat, lng

    cos_lat = math.cos(math.radians(lat)) or 1e-12
    for ring in range(1, _SNAP_MAX_RINGS + 1):
        radius = _SNAP_STEP_DEG * ring
        best: Tuple[float, float] | None = None
        best_dist = math.inf
        for d in range(_SNAP_DIRECTIONS):
            angle = (2 * math.pi * d) / _SNAP_DIRECTIONS
            cand_lat = lat + radius * math.cos(angle)
            cand_lng = lng + (radius * math.sin(angle)) / cos_lat
            if is_in_water(cand_lat, cand_lng):
                dist = _distance_km(lat, lng, cand_lat, cand_lng)
                if dist < best_dist:
                    best = (cand_lat, cand_lng)
                    best_dist = dist
        if best is not None:
            return best

    return lat, lng


def filter_and_snap(lat: float, lng: float) -> Optional[Tuple[float, float]]:
    """Region+water gate for a sighting coordinate.

    Returns ``None`` when the point is outside the pilot region (caller should
    drop the record), otherwise returns the coordinate snapped to water. Use for
    sources whose coordinate represents an orca position (OBIS, iNaturalist,
    community). Do not use for fixed-instrument positions such as hydrophones.
    """
    if not in_bounds(lat, lng):
        return None
    return snap_to_water(lat, lng)


def _distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    )
    return 2 * radius * math.asin(min(1.0, math.sqrt(a)))
