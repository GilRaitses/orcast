from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from ..models import ForecastQuickRequest, SpatialForecastRequest
from ..scoring import MODEL_VERSION, probability_at_location, spatial_forecast_grid
from ..state import ensure_hotspots, noaa
from ..storage import model_to_dict

router = APIRouter()


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
    grid = spatial_forecast_grid(
        request.lat,
        request.lng,
        request.radius_km,
        hotspots,
        env,
        step_degrees=max(0.01, request.grid_resolution),
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
