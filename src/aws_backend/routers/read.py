from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from ..config import settings
from ..geo_region import in_bounds
from ..models import ValidationStatus
from ..sources.noaa import NoaaAdapter
from ..state import ensure_hotspots, get_latest_ingestion_run, hydrophones, noaa, run_ingestion, storage
from ..storage import model_to_dict

router = APIRouter()

_VERIFIED_DEFAULT = {ValidationStatus.VERIFIED, ValidationStatus.LIKELY}
_STATUS_ORDER = {
    ValidationStatus.REJECTED: 0,
    ValidationStatus.TENTATIVE: 1,
    ValidationStatus.LIKELY: 2,
    ValidationStatus.VERIFIED: 3,
}

LIVE_ENDPOINTS = [
    "/",
    "/health",
    "/api/status",
    "/api/sightings",
    "/api/verified-sightings",
    "/api/sightings/ingest",
    "/api/live-hydrophones",
    "/api/realtime/events",
    "/api/environmental",
    "/api/hotspots",
    "/api/hotspots/recompute",
    "/forecast/quick",
    "/forecast/spatial",
    "/forecast/current",
    "/forecast/status",
    "/api/reports/probability",
    "/api/reports/{report_id}",
    "/api/reports/{report_id}.csv",
    "/api/community/sightings",
    "/api/community/submissions",
]

DEPRECATED_ROUTES = {
    "/api/predictions": "/api/reports/probability",
    "/api/behavioral-analysis": "/api/reports/probability",
    "/api/dtag-data": "/api/sightings",
}


def _min_status_threshold(min_status: str) -> set[ValidationStatus]:
    try:
        threshold = ValidationStatus(min_status.lower())
    except ValueError:
        threshold = ValidationStatus.LIKELY
    min_rank = _STATUS_ORDER[threshold]
    return {status for status, rank in _STATUS_ORDER.items() if rank >= min_rank and status != ValidationStatus.REJECTED}


def _health_payload() -> Dict[str, Any]:
    run = get_latest_ingestion_run()
    sources_summary: List[Dict[str, Any]] = []
    degraded = False
    if run:
        for status in run.statuses:
            if status.enabled and not status.available:
                degraded = True
            sources_summary.append(model_to_dict(status))
        if run.errors:
            degraded = True
    overall = "degraded" if degraded else "healthy"
    return {
        "status": overall,
        "storage_backend": settings.storage_backend,
        "sightings_loaded": len(storage.list_sightings(limit=10_000)),
        "hotspots_loaded": len(storage.list_hotspots(limit=1_000)),
        "sources": sources_summary,
        "latest_ingestion_run_id": run.run_id if run else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _stream_active() -> bool:
    run = get_latest_ingestion_run()
    if not run:
        return False
    for status in run.statuses:
        if status.source in {"orcahello", "orcasound"} and status.enabled and status.available and status.record_count > 0:
            return True
    return False


@router.get("/")
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


@router.get("/health")
def health() -> Dict[str, Any]:
    return _health_payload()


@router.get("/api/status")
def api_status() -> Dict[str, Any]:
    run = get_latest_ingestion_run()
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
        "latest_ingestion_run": model_to_dict(run) if run else None,
        "endpoints": LIVE_ENDPOINTS,
        "deprecated_routes": DEPRECATED_ROUTES,
    }


@router.get("/api/sightings")
def list_sightings(limit: int = 500) -> Dict[str, Any]:
    sightings = storage.list_sightings(limit=limit)
    return {
        "status": "success",
        "total_count": len(sightings),
        "sightings": [model_to_dict(sighting) for sighting in sightings],
    }


@router.get("/api/verified-sightings")
def verified_sightings(
    limit: int = 500,
    min_status: Optional[str] = Query(default=None, description="Minimum validation status (verified, likely, tentative)"),
) -> Dict[str, Any]:
    allowed = _min_status_threshold(min_status) if min_status else _VERIFIED_DEFAULT
    all_sightings = storage.list_sightings(limit=10_000)
    filtered = [s for s in all_sightings if s.cross_validation.status in allowed][:limit]
    return {
        "status": "success",
        "data_source": "aws_backend_normalized",
        "min_status": min_status or "likely",
        "total_count": len(filtered),
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
            for s in filtered
        ],
    }


@router.get("/api/live-hydrophones")
def live_hydrophones() -> Dict[str, Any]:
    records = [
        record
        for record in hydrophones.hydrophones()
        if in_bounds(record.get("latitude"), record.get("longitude"))
    ]
    return {
        "status": "success",
        "source": "static_catalog",
        "live_status_check": False,
        "region": "san_juan_islands",
        "total_count": len(records),
        "data": records,
        "hydrophones": records,
    }


@router.get("/api/realtime/events")
def realtime_events() -> Dict[str, Any]:
    sightings = storage.list_sightings(limit=100)
    events = [
        {
            "id": sighting.sighting_id,
            "event_type": "sighting",
            "confidence": sighting.confidence,
            "source": sighting.source,
            "location": {"lat": sighting.latitude, "lng": sighting.longitude},
            "location_name": sighting.location_name,
            "timestamp": sighting.timestamp.isoformat(),
            "validation_status": sighting.cross_validation.status.value,
        }
        for sighting in sightings
        if in_bounds(sighting.latitude, sighting.longitude)
    ][:25]
    return {
        "status": "success",
        "events": events,
        "total_events": len(events),
        "stream_active": _stream_active(),
        "data_freshness": "historical",
    }


@router.get("/api/environmental")
def environmental() -> Dict[str, Any]:
    env = noaa.current_environment() if settings.enable_live_noaa else NoaaAdapter().current_environment()
    return {"status": "success", "environmental_data": model_to_dict(env)}


@router.get("/api/hotspots")
def list_hotspots(limit: int = 50) -> Dict[str, Any]:
    hotspots = ensure_hotspots()
    return {
        "status": "success",
        "total_count": len(hotspots[:limit]),
        "hotspots": [model_to_dict(h) for h in hotspots[:limit]],
    }
