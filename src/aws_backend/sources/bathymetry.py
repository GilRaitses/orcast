"""San Juan archipelago bathymetry (sea-floor depth) covariate.

This is the static spatial covariate behind ``s_space`` in
``docs/methodology/FORECAST_KERNELS.md`` (habitat / channel / depth prior).

The depth grid is a committed asset at ``data/geo/san_juan_bathymetry.json``
clipped to the pilot bounding box (``SAN_JUAN_BOUNDS`` in
``..geo_region``). It is a real gridded relief subset (NOAA NGDC ETOPO1,
1 arc-minute, served via the GCOOS ERDDAP griddap) with ``depth_m`` carrying
the ETOPO ``altitude`` value: negative metres are below sea level (water),
positive metres are island land elevation. No depths are synthesized here.

Mirrors the committed-asset + permissive-degrade pattern used by the land
mask loader in ``..geo_region``: if the asset is missing the adapter logs a
warning and behaves as an empty grid (``load() -> []``, ``depth_at() -> None``)
so nothing hard-fails on a missing file.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from typing import Dict, List, Optional

from ..config import settings

logger = logging.getLogger(__name__)

_ASSET_RELATIVE = ("data", "geo", "san_juan_bathymetry.json")


def _resolve_asset_path() -> Path:
    """Resolve the committed bathymetry asset (mirrors geo_region's loader)."""
    repo_path = Path(settings.repo_root).joinpath(*_ASSET_RELATIVE)
    if repo_path.exists():
        return repo_path
    # Fallback: walk up from this module (src/aws_backend/sources) to repo root.
    module_relative = Path(__file__).resolve().parents[3].joinpath(*_ASSET_RELATIVE)
    return module_relative


class BathymetryAdapter:
    """Nearest-grid-point sea-floor depth lookup for the San Juan region.

    ``depth_m`` follows the asset convention: negative metres are below sea
    level. ``depth_at`` returns the depth of the nearest grid point (by simple
    great-circle-ish nearest distance) for an in-grid query, else ``None``.
    """

    source_name = "bathymetry"
    reliability = 0.7

    def __init__(self, asset_path: Optional[Path] = None) -> None:
        self._asset_path = Path(asset_path) if asset_path is not None else None
        self._meta: Dict[str, object] = {}
        self._points: List[Dict[str, float]] = []
        self._loaded = False

    # -- Loading ---------------------------------------------------------------
    def load(self) -> List[Dict[str, float]]:
        """Return the grid as a list of ``{lat, lng, depth_m}`` dicts.

        Reads the committed asset on first call and caches it. Returns ``[]``
        (and logs a warning) if the asset is missing or unparseable.
        """
        if self._loaded:
            return self._points

        path = self._asset_path or _resolve_asset_path()
        if not path.exists():
            logger.warning(
                "Bathymetry asset not found at %s; depth covariate is empty (depth_at returns None)",
                path,
            )
            self._loaded = True
            return self._points

        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, ValueError) as exc:  # pragma: no cover - defensive
            logger.warning("Failed to load bathymetry asset at %s: %s; depth covariate is empty", path, exc)
            self._loaded = True
            return self._points

        points: List[Dict[str, float]] = []
        for raw in data.get("points", []) if isinstance(data, dict) else []:
            try:
                points.append(
                    {
                        "lat": float(raw["lat"]),
                        "lng": float(raw["lng"]),
                        "depth_m": float(raw["depth_m"]),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue

        if not points:
            logger.warning("Bathymetry asset at %s contained no usable points", path)

        self._meta = {
            "source": data.get("source") if isinstance(data, dict) else None,
            "dataset": data.get("dataset") if isinstance(data, dict) else None,
            "bounds": data.get("bounds") if isinstance(data, dict) else None,
            "resolution_deg": data.get("resolution_deg") if isinstance(data, dict) else None,
        }
        self._points = points
        self._loaded = True
        return self._points

    # -- Queries ---------------------------------------------------------------
    def depth_at(self, lat: float, lng: float) -> Optional[float]:
        """Depth (metres, negative below sea level) of the nearest grid point.

        Returns ``None`` if the grid is empty/missing or the query coordinate is
        non-finite. Nearest is by simple equirectangular distance, which is
        accurate at this latitude/extent and avoids a hard dependency on the
        haversine in ``geo_region``.
        """
        points = self.load()
        if not points:
            return None
        try:
            lat = float(lat)
            lng = float(lng)
        except (TypeError, ValueError):
            return None
        if not (math.isfinite(lat) and math.isfinite(lng)):
            return None

        cos_lat = math.cos(math.radians(lat))
        best_depth: Optional[float] = None
        best_dist = math.inf
        for point in points:
            d_lat = point["lat"] - lat
            d_lng = (point["lng"] - lng) * cos_lat
            dist = d_lat * d_lat + d_lng * d_lng
            if dist < best_dist:
                best_dist = dist
                best_depth = point["depth_m"]
        return best_depth

    # -- Summary ---------------------------------------------------------------
    def summary(self) -> Dict[str, object]:
        """Return grid metadata + depth extent: source, point_count, min/max, bounds."""
        points = self.load()
        depths = [p["depth_m"] for p in points]
        return {
            "source": self._meta.get("source"),
            "point_count": len(points),
            "min_depth_m": min(depths) if depths else None,
            "max_depth_m": max(depths) if depths else None,
            "bounds": self._meta.get("bounds"),
        }
