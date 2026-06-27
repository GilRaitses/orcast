"""Read-only data gatherers for the exploration guide (internal only)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..config import settings
from ..geo_region import in_bounds
from ..kernel_model.serve import KernelForecaster, load_fit_report, load_promotion
from ..models import ValidationStatus
from ..sources.noaa import NoaaAdapter
from ..state import ensure_hotspots, get_latest_ingestion_run, hydrophones, noaa, storage
from ..storage import model_to_dict

_VERIFIED_DEFAULT = {ValidationStatus.VERIFIED, ValidationStatus.LIKELY}


def fetch_gates() -> Dict[str, Any]:
    """Summarize fitness gates from the fit report (same facts as GET /api/gates)."""
    report = load_fit_report()
    if not report:
        return {"status": "not_fitted", "message": "No fit report available yet."}

    promotion = load_promotion()
    from ..routers.kernel import effective_confidence, _build_caveats, _report_consistency

    eff = effective_confidence(report, promotion)
    return {
        "status": report.get("status", "unknown"),
        "confidence": report.get("confidence"),
        "effective_confidence": eff,
        "promoted": bool(promotion and promotion.get("promoted")),
        "caveats": _build_caveats(report),
        "gates": {
            "level1_psth": report.get("level1_psth"),
            "cross_validation": report.get("cv"),
            "time_rescaling": report.get("time_rescaling"),
            "pit": report.get("pit"),
            "consistency": _report_consistency(report),
        },
        "repr_id": report.get("repr_id"),
        "run_id": report.get("run_id"),
    }


def fetch_provenance(
    lat: float,
    lng: float,
    when: Optional[str] = None,
) -> Dict[str, Any]:
    """Cell-level provenance (subset of GET /api/provenance)."""
    if not in_bounds(lat, lng):
        return {
            "status": "out_of_region",
            "message": "Coordinate outside San Juan pilot bounds.",
        }

    forecaster = KernelForecaster.from_path()
    if forecaster is None:
        return {"status": "not_fitted", "message": "No fitted kernels available."}

    moment = _parse_when(when)
    fit = forecaster.fit
    report = load_fit_report() or {}
    promotion = load_promotion()
    from ..routers.kernel import effective_confidence

    phases = forecaster.clock_phases(moment, lat, lng)
    contributions: List[Dict[str, Any]] = []
    for name, kernel in fit.kernels.items():
        phase = phases.get(name)
        if phase is None:
            contributions.append({"kernel": name, "available": False})
            continue
        contributions.append(
            {
                "kernel": name,
                "available": True,
                "phase": round(float(phase), 4),
                "value": round(float(kernel.value(phase)), 4),
            }
        )

    intensity = forecaster.intensity(moment, lat, lng, station=None)
    return {
        "status": "success",
        "lat": lat,
        "lng": lng,
        "when": moment.isoformat(),
        "intensity": intensity,
        "effective_confidence": effective_confidence(report, promotion),
        "contributions": contributions,
        "gate_summary": (report.get("level1_psth") or {}),
    }


def fetch_hotspots(limit: int = 10) -> Dict[str, Any]:
    hotspots = ensure_hotspots()
    return {
        "status": "success",
        "total_count": len(hotspots),
        "hotspots": [model_to_dict(h) for h in hotspots[:limit]],
    }


def fetch_forecast_cell(
    lat: float,
    lng: float,
    when: Optional[str] = None,
) -> Dict[str, Any]:
    if not in_bounds(lat, lng):
        return {"status": "out_of_region"}
    forecaster = KernelForecaster.from_path()
    if forecaster is None:
        return {"status": "not_fitted"}
    moment = _parse_when(when)
    intensity = forecaster.intensity(moment, lat, lng, station=None)
    report = load_fit_report() or {}
    promotion = load_promotion()
    from ..routers.kernel import effective_confidence

    return {
        "status": "success",
        "lat": lat,
        "lng": lng,
        "when": moment.isoformat(),
        "intensity": intensity,
        "effective_confidence": effective_confidence(report, promotion),
        "note": "Temporal model only. Does not verify sightings at this pin.",
    }


def _parse_when(when: Optional[str]) -> datetime:
    if not when:
        return datetime.now(timezone.utc)
    text = when.replace("Z", "+00:00")
    return datetime.fromisoformat(text).astimezone(timezone.utc)


def fetch_environmental() -> Dict[str, Any]:
    env = noaa.current_environment() if settings.enable_live_noaa else NoaaAdapter().current_environment()
    return {"status": "success", "environmental_data": model_to_dict(env)}


def fetch_live_hydrophones() -> Dict[str, Any]:
    records = [
        record
        for record in hydrophones.hydrophones()
        if in_bounds(record.get("latitude"), record.get("longitude"))
    ]
    return {
        "status": "success",
        "source": "static_catalog",
        "total_count": len(records),
        "hydrophones": records[:10],
    }


def fetch_realtime_events(limit: int = 25) -> Dict[str, Any]:
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
    ][:limit]
    return {
        "status": "success",
        "events": events,
        "total_events": len(events),
    }


def fetch_data_status() -> Dict[str, Any]:
    from .. import ingest_timeseries

    return ingest_timeseries.timeseries_status()


def fetch_verified_sightings(limit: int = 20) -> Dict[str, Any]:
    all_sightings = storage.list_sightings(limit=10_000)
    filtered = [s for s in all_sightings if s.cross_validation.status in _VERIFIED_DEFAULT][:limit]
    return {
        "status": "success",
        "total_count": len(filtered),
        "sightings": [
            {
                "sighting_id": s.sighting_id,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "observation_timestamp": s.timestamp.isoformat(),
                "validation_status": s.cross_validation.status.value,
                "location_name": s.location_name,
            }
            for s in filtered
        ],
    }


def fetch_ingestion_status() -> Dict[str, Any]:
    run = get_latest_ingestion_run()
    return {
        "status": "success",
        "latest_ingestion": model_to_dict(run) if run else None,
    }


def fetch_snapshot_manifest() -> Dict[str, Any]:
    report = load_fit_report() or {}
    snap_id = report.get("dataset_snapshot_id") or report.get("snap_id")
    return {
        "status": "success" if snap_id else "not_available",
        "snap_id": snap_id,
        "fit_plan_id": report.get("fit_plan_id"),
    }


def fetch_supervisor_recommendation() -> Dict[str, Any]:
    from ..promotion.supervisor import draft_decision

    report = load_fit_report()
    if not report:
        return {"status": "not_fitted"}
    return {"status": "success", "recommendation": draft_decision(report)}


def fetch_pending_approval() -> Dict[str, Any]:
    from ..kernel_model.serve import load_pending_approval

    pending = load_pending_approval()
    if not pending:
        return {"status": "none"}
    public = {k: v for k, v in pending.items() if k != "task_token"}
    return {"status": "success", "pending_approval": public}


def fetch_decision_records(limit: int = 10) -> Dict[str, Any]:
    from ..state import storage

    records = storage.list_decision_records(limit=limit)
    return {
        "status": "success",
        "total_count": len(records),
        "records": [
            {
                "id": r.id,
                "verdict": r.verdict.value if hasattr(r.verdict, "value") else str(r.verdict),
                "reviewer_id": r.reviewer_id,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ],
    }


def fetch_review_dossier_summary() -> Dict[str, Any]:
    return {
        "status": "not_implemented",
        "message": "Use GET /api/review-dossier/latest with API key (Wave J).",
    }
