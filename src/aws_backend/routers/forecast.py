from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from ..models import ForecastQuickRequest, SpatialForecastRequest
from ..scoring import MODEL_VERSION, probability_at_location, spatial_forecast_grid
from ..state import ensure_hotspots, noaa
from ..storage import model_to_dict

router = APIRouter()

# Hard cap on spatial-grid size so a large radius + fine resolution cannot
# request an enormous (CPU/memory-blowing) grid.
_MAX_GRID_POINTS = 5000


def _clamp_grid_step(lat: float, radius_km: float, grid_resolution: float) -> float:
    """Return a grid step (degrees) that keeps the grid under the point cap.

    Mirrors the grid extent in ``spatial_forecast_grid`` and widens the step
    when the requested resolution would exceed ``_MAX_GRID_POINTS``.
    """
    step = max(0.01, grid_resolution)
    lat_span = max(radius_km, 0.0) / 111.0
    lng_span = max(radius_km, 0.0) / (111.0 * max(math.cos(math.radians(lat)), 1e-6))
    n_lat = 2.0 * lat_span / step + 1.0
    n_lng = 2.0 * lng_span / step + 1.0
    total = n_lat * n_lng
    if total > _MAX_GRID_POINTS:
        step *= math.sqrt(total / _MAX_GRID_POINTS)
    return step


@router.post("/forecast/quick")
def quick_forecast(request: ForecastQuickRequest) -> Dict[str, Any]:
    lat = request.latitude if request.latitude is not None else request.lat
    lng = request.longitude if request.longitude is not None else request.lng
    env = noaa.current_environment()
    prediction = probability_at_location(lat, lng, ensure_hotspots(), env)
    return {
        "status": "success",
        "location": {"lat": lat, "lng": lng},
        "prediction": prediction,
        "model": MODEL_VERSION,
        "environmental_conditions": model_to_dict(env),
    }


@router.post("/forecast/spatial")
def spatial_forecast(request: SpatialForecastRequest) -> Dict[str, Any]:
    env = noaa.current_environment()
    hotspots = ensure_hotspots()
    step_degrees = _clamp_grid_step(request.lat, request.radius_km, request.grid_resolution)
    grid = spatial_forecast_grid(
        request.lat,
        request.lng,
        request.radius_km,
        hotspots,
        env,
        step_degrees=step_degrees,
        forecast_hours=request.hours,
    )
    return {
        "status": "success",
        "center": {"lat": request.lat, "lng": request.lng},
        "radius_km": request.radius_km,
        "hours": request.hours,
        "model": MODEL_VERSION,
        "grid_points": grid,
        "total_points": len(grid),
        "forecast_id": f"forecast_{uuid.uuid4().hex[:12]}",
        "generation_time": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/forecast/current")
def current_forecast() -> Dict[str, Any]:
    hotspots = ensure_hotspots()
    env = noaa.current_environment()
    prediction = probability_at_location(48.5465, -123.0307, hotspots, env)
    return {
        "status": "success",
        "location": {"lat": 48.5465, "lng": -123.0307},
        "prediction": prediction,
        "model": MODEL_VERSION,
        "hotspots": [model_to_dict(h) for h in hotspots[:5]],
        "environmental_conditions": model_to_dict(env),
    }


@router.get("/forecast/status")
def forecast_status() -> Dict[str, Any]:
    return {
        "status": "success",
        "system_status": "operational",
        "model": MODEL_VERSION,
        "hotspots_available": len(ensure_hotspots()),
        "last_update": datetime.now(timezone.utc).isoformat(),
    }
