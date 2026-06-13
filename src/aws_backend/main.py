from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .models import ForecastQuickRequest, IngestionRun, ProbabilityReportRequest, SourceStatus, SpatialForecastRequest
from .reports import build_probability_report
from .scoring import generate_hotspots, probability_at_location, spatial_forecast_grid
from .sources.inaturalist import INaturalistAdapter
from .sources.local_obis import LocalObisAdapter
from .sources.noaa import NoaaAdapter
from .sources.orcahello import OrcaHelloAdapter
from .sources.orcasound import OrcasoundHydrophoneAdapter
from .storage import StorageBackend, build_storage, model_to_dict
from .validation import cross_validate_sightings, deduplicate_sightings

storage: StorageBackend = build_storage(settings)
noaa = NoaaAdapter()
hydrophones = OrcasoundHydrophoneAdapter()
latest_ingestion_run: IngestionRun | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not storage.list_sightings(limit=1):
        run_ingestion(include_live=False)
    yield


app = FastAPI(
    title="ORCAST AWS Backend",
    description="AWS-native ORCAST sightings, hotspot probability, and report service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "service": "ORCAST AWS Backend",
        "status": "operational",
        "version": "1.0.0",
        "storage_backend": settings.storage_backend,
        "aws_region": settings.aws_region,
        "capabilities": [
            "AWS-compatible storage abstraction",
            "web source sighting ingestion",
            "cross-validation",
            "hotspot probability scoring",
            "probability report generation",
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "storage_backend": settings.storage_backend,
        "sightings_loaded": len(storage.list_sightings(limit=10_000)),
        "hotspots_loaded": len(storage.list_hotspots(limit=1_000)),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/status")
def api_status() -> Dict[str, Any]:
    return {
        "api_version": "1.0.0",
        "backend": "aws",
        "storage_backend": settings.storage_backend,
        "sources": {
            "local_obis": True,
            "inaturalist": settings.enable_live_inaturalist,
            "noaa": settings.enable_live_noaa,
            "orcahello": settings.enable_orcahello,
            "orcasound_hydrophones": True,
        },
        "latest_ingestion_run": model_to_dict(latest_ingestion_run) if latest_ingestion_run else None,
        "endpoints": [
            "/api/sightings",
            "/api/hotspots",
            "/api/reports/probability",
            "/forecast/quick",
            "/forecast/spatial",
        ],
    }


@app.get("/api/sightings")
def list_sightings(limit: int = 500) -> Dict[str, Any]:
    sightings = storage.list_sightings(limit=limit)
    return {
        "status": "success",
        "total_count": len(sightings),
        "sightings": [model_to_dict(sighting) for sighting in sightings],
    }


@app.get("/api/verified-sightings")
def verified_sightings(limit: int = 500) -> Dict[str, Any]:
    sightings = storage.list_sightings(limit=limit)
    return {
        "status": "success",
        "data_source": "aws_backend_normalized",
        "total_count": len(sightings),
        "sightings": [
            {
                "sighting_id": s.sighting_id,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "observation_timestamp": s.timestamp.isoformat(),
                "behavior_primary": s.behavior,
                "pod_size": s.count,
                "data_quality_score": s.cross_validation.score,
                "location_name": s.location_name,
                "validation_status": s.cross_validation.status.value,
            }
            for s in sightings
        ],
    }


@app.post("/api/sightings/ingest")
def ingest_sightings(include_live: bool = True) -> Dict[str, Any]:
    run = run_ingestion(include_live=include_live)
    return model_to_dict(run)


@app.get("/api/live-hydrophones")
def live_hydrophones() -> Dict[str, Any]:
    records = hydrophones.hydrophones()
    return {"status": "success", "total_count": len(records), "data": records, "hydrophones": records}


@app.get("/api/realtime/events")
def realtime_events() -> Dict[str, Any]:
    sightings = storage.list_sightings(limit=25)
    events = [
        {
            "id": sighting.sighting_id,
            "type": "sighting",
            "confidence": sighting.confidence,
            "source": sighting.source,
            "hydrophone": sighting.location_name or sighting.source,
            "hydrophoneId": sighting.source_id,
            "callType": "unknown",
            "location": {"lat": sighting.latitude, "lng": sighting.longitude},
            "timestamp": sighting.timestamp.isoformat(),
        }
        for sighting in sightings
    ]
    return {"status": "success", "events": events, "total_events": len(events), "stream_active": True}


@app.get("/api/environmental")
def environmental() -> Dict[str, Any]:
    env = noaa.current_environment() if settings.enable_live_noaa else NoaaAdapter().current_environment()
    return {"status": "success", "environmental_data": model_to_dict(env)}


@app.get("/api/hotspots")
def list_hotspots(limit: int = 50) -> Dict[str, Any]:
    hotspots = ensure_hotspots()
    return {"status": "success", "total_count": len(hotspots[:limit]), "hotspots": [model_to_dict(h) for h in hotspots[:limit]]}


@app.post("/api/hotspots/recompute")
def recompute_hotspots() -> Dict[str, Any]:
    hotspots = generate_hotspots(storage.list_sightings(limit=10_000))
    storage.put_hotspots(hotspots)
    return {"status": "success", "total_count": len(hotspots), "hotspots": [model_to_dict(h) for h in hotspots]}


@app.post("/forecast/quick")
def quick_forecast(request: ForecastQuickRequest) -> Dict[str, Any]:
    lat = request.latitude if request.latitude is not None else request.lat
    lng = request.longitude if request.longitude is not None else request.lng
    env = noaa.current_environment()
    prediction = probability_at_location(lat, lng, ensure_hotspots(), env)
    return {
        "status": "success",
        "location": {"lat": lat, "lng": lng},
        "prediction": prediction,
        "environmental_conditions": model_to_dict(env),
    }


@app.post("/forecast/spatial")
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
    )
    return {
        "status": "success",
        "center": {"lat": request.lat, "lng": request.lng},
        "radius_km": request.radius_km,
        "grid_points": grid,
        "total_points": len(grid),
        "forecast_id": f"forecast_{uuid.uuid4().hex[:12]}",
        "generation_time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/forecast/current")
def current_forecast() -> Dict[str, Any]:
    hotspots = ensure_hotspots()
    env = noaa.current_environment()
    prediction = probability_at_location(48.5465, -123.0307, hotspots, env)
    return {
        "status": "success",
        "location": {"lat": 48.5465, "lng": -123.0307},
        "prediction": prediction,
        "hotspots": [model_to_dict(h) for h in hotspots[:5]],
        "environmental_conditions": model_to_dict(env),
    }


@app.get("/forecast/status")
def forecast_status() -> Dict[str, Any]:
    return {
        "status": "success",
        "system_status": "operational",
        "model": "aws-deterministic-hotspot-v1",
        "hotspots_available": len(ensure_hotspots()),
        "last_update": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/reports/probability")
def probability_report(request: ProbabilityReportRequest) -> Dict[str, Any]:
    sightings = storage.list_sightings(limit=10_000)
    hotspots = ensure_hotspots()
    report = build_probability_report(request, sightings, hotspots, latest_ingestion_run)
    storage.put_report(report)
    return {"status": "success", "report": model_to_dict(report)}


@app.get("/api/reports/{report_id}")
def get_report(report_id: str) -> Dict[str, Any]:
    report = storage.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"status": "success", "report": model_to_dict(report)}


def ensure_hotspots() -> List[Any]:
    hotspots = storage.list_hotspots(limit=100)
    if hotspots:
        return hotspots
    hotspots = generate_hotspots(storage.list_sightings(limit=10_000))
    storage.put_hotspots(hotspots)
    return hotspots


def run_ingestion(include_live: bool = True) -> IngestionRun:
    global latest_ingestion_run
    run = IngestionRun(run_id=f"ingest_{uuid.uuid4().hex[:12]}")
    adapters = [LocalObisAdapter()]
    if include_live and settings.enable_live_inaturalist:
        adapters.append(INaturalistAdapter())
    if include_live and settings.enable_orcahello:
        adapters.append(OrcaHelloAdapter())

    all_sightings = []
    statuses: List[SourceStatus] = []
    for adapter in adapters:
        result = adapter.fetch()
        normalized = adapter.normalize(result)
        statuses.append(adapter.status(result, len(normalized)))
        all_sightings.extend(normalized)
        if result.error:
            run.errors.append(f"{adapter.source_name}: {result.error}")

    deduped = deduplicate_sightings(all_sightings)
    validated = cross_validate_sightings(deduped)
    storage.put_sightings(validated)
    hotspots = generate_hotspots(validated)
    storage.put_hotspots(hotspots)

    run.statuses = statuses
    run.sightings_ingested = len(all_sightings)
    run.sightings_stored = len(validated)
    run.completed_at = datetime.now(timezone.utc)
    storage.put_ingestion_run(run)
    latest_ingestion_run = run
    return run

