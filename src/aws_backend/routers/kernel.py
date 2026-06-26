"""Kernel-forecast read + human-promotion endpoints (H0 orchestrator surface).

These power three demo surfaces:

* ``GET  /api/gates``               -- the fitness-gate record + confidence,
* ``GET  /api/provenance``          -- why a map cell is hot (cell -> kernels ->
                                       gates -> nearby evidence),
* ``GET  /api/decision-records``    -- the human promotion audit log,
* ``POST /api/decision-records``    -- record a human promote/hold decision
                                       (keyed; the consequential human step).

The forecast itself is served by the existing ``/forecast/*`` routes; this
router adds the provenance + gate + human-oversight layer. Coefficients and the
gate report are produced offline by ``modeling/fit_kernels.py`` and loaded here
through the stdlib-only serving module.

Decision records are persisted through the configured storage backend. In AWS
mode this is the DynamoDB ``decision-records`` table; local/dev mode uses the
in-memory storage backend.
"""

from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth import ReviewerIdentity, require_api_key, require_signed_in, require_trusted_reviewer, reviewer_identity
from ..config import settings
from ..geo_region import in_bounds
from ..kernel_model.serve import (
    KernelForecaster,
    load_fitted_kernels,
    load_fit_report,
    load_pending_approval,
    load_promotion,
)
from ..spatial_enrichment import load_cells_from_store, lookup_cell
from ..timeseries import build_timeseries_store

router = APIRouter()

# Written by modeling/fit_kernels.py alongside the coefficients (dev/local).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_FIT_REPORT_PATH = _REPO_ROOT / "data" / "models" / "fit_report.json"
_spatial_cells_cache: Optional[List[Dict[str, Any]]] = None


def _spatial_cells() -> List[Dict[str, Any]]:
    global _spatial_cells_cache
    if _spatial_cells_cache is None:
        try:
            store = build_timeseries_store(settings)
            _spatial_cells_cache = load_cells_from_store(store)
        except Exception:
            _spatial_cells_cache = []
    return _spatial_cells_cache


def _spatial_provenance(lat: float, lng: float, report: Dict[str, Any]) -> Dict[str, Any]:
    cell = lookup_cell(lat, lng, cells=_spatial_cells())
    summary = report.get("spatial_covariates") or {}
    active = summary.get("status") == "active" or bool(cell.get("available"))
    return {
        "modeled": False,
        "covariates_active": active,
        "cell_id": cell.get("cell_id"),
        "depth_m": cell.get("depth_m"),
        "nearest_shore_m": cell.get("nearest_shore_m"),
        "inside_land": cell.get("inside_land", False),
        "note": (
            "Intensity is temporal-only; bathymetry/shoreline covariates are "
            "stored for spatial integrity metadata but are not yet fitted as s_space."
        ),
    }

def _get_storage():
    """Lazy storage accessor so this router imports without the ingestion stack."""
    from ..state import storage
    return storage


def _load_fit_report() -> Optional[Dict[str, Any]]:
    """Gate report from S3 in aws mode, else the local file written by the fit."""
    return load_fit_report()


def effective_confidence(
    report: Optional[Dict[str, Any]],
    promotion: Optional[Dict[str, Any]],
) -> Optional[float]:
    """The confidence a consumer should trust.

    Equals ``promotion.effective_confidence`` when a promotion marker exists and
    is promoted; otherwise the raw fit confidence. Shared by /api/gates and
    /api/provenance so the two surfaces never disagree.
    """
    report = report or {}
    raw = report.get("confidence")
    if (
        promotion
        and promotion.get("promoted")
        and promotion.get("effective_confidence") is not None
    ):
        return promotion.get("effective_confidence")
    return raw


def _build_caveats(report: Dict[str, Any]) -> List[str]:
    """Human-readable honesty caveats derived from the fit report."""
    caveats: List[str] = []
    if report.get("tide_overlaps_acoustic") is False:
        caveats.append(
            "Tide kernel is not meaningful (currents do not overlap the acoustic detections)"
        )
    n_stations = report.get("n_stations_acoustic")
    if isinstance(n_stations, (int, float)) and n_stations <= 1:
        caveats.append("Single station")
    if report.get("effort_assumed_continuous") is True:
        caveats.append("Effort assumed continuous (not effort-corrected)")
    if report.get("detections_unreviewed_candidates") is True:
        level0 = report.get("level0_detector_qc") or {}
        if isinstance(level0, dict) and level0.get("status") == "active":
            caveats.append(
                "Spike-train fit uses unreviewed acoustic candidates; Level 0 QC reports reviewed outcome mix separately."
            )
        else:
            caveats.append(
                "Acoustic detections are unreviewed candidates; Level 0 detector QC is not yet available."
            )
    # Season partial-cycle caveat, if the report exposes one (tolerate absence).
    if report.get("season_extrapolated"):
        caveats.append(
            "Season kernel extrapolated beyond observed coverage (partial annual cycle)"
        )
    elif report.get("season_partial_cycle"):
        caveats.append(
            "Season kernel covers only a partial annual cycle"
        )
    # Time-rescaling (in-sample event-timing GoF) did not pass: be explicit that
    # calibration is instead assessed out-of-sample via PIT.
    time_rescaling = report.get("time_rescaling")
    if isinstance(time_rescaling, dict) and not time_rescaling.get("pooled_pass_exp"):
        caveats.append(
            "In-sample event-timing goodness-of-fit (time-rescaling) still fails; "
            "calibration is assessed via held-out PIT."
        )
    # Marginal cross-validation skill: the model is barely beating climatology.
    cv = report.get("cv")
    if isinstance(cv, dict):
        skill = cv.get("mean_deviance_skill")
        if isinstance(skill, (int, float)) and skill < 0:
            caveats.append(
                "Mean held-out deviance skill is negative; fold-majority CV pass should be treated cautiously."
            )
        elif isinstance(skill, (int, float)) and skill < 0.05:
            caveats.append("Cross-validation skill is marginal (near climatology).")
    return caveats


def _report_consistency(report: Dict[str, Any]) -> Any:
    """Return PSTH-vs-kernel diagnostic under the stable API key."""
    return report.get("consistency") or report.get("psth_vs_kernel_diagnostic")


def _enrich_cv_display(cv: Any) -> Any:
    """Add UI-aligned display_status for fold-majority vs mean-skill honesty (G3-D-01)."""
    if not isinstance(cv, dict):
        return cv
    out = dict(cv)
    gate_pass = out.get("gate_pass")
    skill = out.get("mean_deviance_skill")
    if gate_pass is False:
        out["display_status"] = "fail"
        out["display_pass"] = False
    elif gate_pass is True:
        if isinstance(skill, (int, float)) and skill < 0:
            out["display_status"] = "caution"
            out["display_pass"] = False
        else:
            out["display_status"] = "pass"
            out["display_pass"] = True
    return out


def _public_pending_approval(marker: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Return a public-safe pending approval summary with callback secrets removed."""
    if not isinstance(marker, dict):
        return None
    out = {
        k: v
        for k, v in marker.items()
        if k not in {"task_token", "TaskToken", "token"}
    }
    out["has_task_token"] = bool(
        marker.get("task_token") or marker.get("TaskToken") or marker.get("token")
    )
    return out


def _server_gate_stamp(
    report: Optional[Dict[str, Any]],
) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Trusted, server-side ``(gates_summary, kernel_version)`` from the fit.

    The client body is NOT trusted for these: a reviewer cannot claim a fit
    passed gates it did not, or attribute a decision to the wrong model version.
    """
    if not report:
        return None, None
    gates_summary = {
        "status": report.get("status"),
        "confidence": report.get("confidence"),
        "cv_gate_pass": (report.get("cv") or {}).get("gate_pass"),
        "pit_calibrated": (report.get("pit") or {}).get("calibrated"),
        "tide_overlaps_acoustic": report.get("tide_overlaps_acoustic"),
        "n_detections": report.get("n_detections"),
        "generated_at": report.get("generated_at"),
    }
    kernel_version = report.get("version") or report.get("generated_at")
    return gates_summary, kernel_version


def _serialize_decision_record(record: Any) -> Dict[str, Any]:
    """Serialize a DecisionRecord WITHOUT the secret ``task_token``.

    The task token is a Step Functions callback secret; it must never appear in
    the audit-log read surface or the create response.
    """
    from ..storage import model_to_dict

    data = model_to_dict(record)
    data.pop("task_token", None)
    return data


@router.get("/api/gates")
def get_gates() -> Dict[str, Any]:
    """Serve the fitness-gate record and the forecast's earned confidence."""
    report = _load_fit_report()
    if report is None:
        return {
            "status": "not_fitted",
            "message": "No fit report available yet. Run modeling/fit_kernels.py.",
        }
    promotion = load_promotion()
    pending_approval = load_pending_approval()
    return {
        "status": report.get("status", "unknown"),
        "confidence": report.get("confidence"),
        "effective_confidence": effective_confidence(report, promotion),
        "caveats": _build_caveats(report),
        "promotion": promotion,
        "promoted": bool(promotion and promotion.get("promoted")),
        "pending_approval": _public_pending_approval(pending_approval),
        "generated_at": report.get("generated_at"),
        "fit_plan_id": report.get("fit_plan_id"),
        "dataset_snapshot_id": report.get("dataset_snapshot_id"),
        "snap_id": report.get("dataset_snapshot_id"),
        "repr_id": report.get("repr_id"),
        "run_id": report.get("run_id"),
        "artifact_uris": report.get("artifact_uris"),
        "data_inventory": {
            "n_stations_acoustic": report.get("n_stations_acoustic"),
            "n_detections": report.get("n_detections"),
            "acoustic_span": report.get("acoustic_span"),
            "currents_span": report.get("currents_span"),
            "tide_overlaps_acoustic": report.get("tide_overlaps_acoustic"),
            "effort_assumed_continuous": report.get("effort_assumed_continuous"),
        },
        "level0_detector_qc": report.get("level0_detector_qc"),
        "baseline_scorecard": report.get("baseline_scorecard"),
        "gates": {
            "level1_psth": report.get("level1_psth"),
            "cross_validation": _enrich_cv_display(report.get("cv")),
            "time_rescaling": report.get("time_rescaling"),
            "pit": report.get("pit"),
            "consistency": _report_consistency(report),
        },
        "metrics": report.get("metrics"),
        "covariates_fit": report.get("covariates_fit"),
    }


@router.get("/api/provenance")
def get_provenance(
    lat: float = Query(..., description="Latitude of the map cell"),
    lng: float = Query(..., description="Longitude of the map cell"),
    when: Optional[str] = Query(default=None, description="ISO8601 time; defaults to now"),
    station: Optional[str] = Query(default=None),
    tide_phase: Optional[float] = Query(default=None, description="Tidal phase 0-1, if known"),
) -> Dict[str, Any]:
    """Explain a cell: the kernel contributions, gate status, and nearby evidence.

    This is the traceability hero: every number the forecast shows links back to
    a fitted kernel, that kernel's gate verdict, and the raw observations behind
    it. Nothing is asserted without a back-link.
    """
    if not in_bounds(lat, lng):
        raise HTTPException(
            status_code=422,
            detail=(
                "Coordinate is outside the San Juan pilot region; the model is "
                "only fit within these bounds and cannot speak to this location."
            ),
        )

    forecaster = KernelForecaster.from_path()
    if forecaster is None:
        raise HTTPException(status_code=404, detail="No fitted kernels available yet")

    moment = _parse_when(when)
    fit = forecaster.fit
    report = _load_fit_report() or {}
    promotion = load_promotion()
    gate_by_cov = report.get("level1_psth", {})
    consistency = _report_consistency(report) or {}

    phases = forecaster.clock_phases(moment, lat, lng)
    if tide_phase is not None:
        phases["tide"] = float(tide_phase)

    contributions: List[Dict[str, Any]] = []
    for name, kernel in fit.kernels.items():
        phase = phases.get(name)
        if phase is None:
            contributions.append({"kernel": name, "available": False,
                                  "reason": "phase unavailable (e.g., tide needs current state)"})
            continue
        value = kernel.value(phase)
        contributions.append({
            "kernel": name,
            "available": True,
            "phase": round(phase, 4),
            "log_rate_contribution": round(value, 4),
            "beats_null": (gate_by_cov.get(name) or {}).get("beats_null"),
            "null_p": (gate_by_cov.get(name) or {}).get("null_p"),
            "psth_kernel_agreement": (consistency.get(name) or {}).get("correlation"),
        })

    log_intensity = forecaster.log_intensity(moment, lat, lng, station=station, tide_phase=tide_phase)

    nearby_sample = _nearby_sample(lat, lng)
    return {
        "status": "success",
        "cell": {"lat": lat, "lng": lng, "when": moment.isoformat(), "station": station},
        "log_intensity": round(log_intensity, 4),
        "intensity": round(math.exp(log_intensity), 6),
        "confidence": fit.confidence,
        "effective_confidence": effective_confidence(report, promotion),
        "caveats": _build_caveats(report),
        "intercept": fit.intercept,
        "station_effect": fit.station_effects.get(station, 0.0) if station else 0.0,
        "fit_plan_id": report.get("fit_plan_id"),
        "dataset_snapshot_id": report.get("dataset_snapshot_id"),
        "snap_id": report.get("dataset_snapshot_id"),
        "repr_id": report.get("repr_id"),
        "run_id": report.get("run_id"),
        "artifact_uris": report.get("artifact_uris"),
        "kernel_contributions": contributions,
        "spatial": _spatial_provenance(lat, lng, report),
        "nearby_sample": nearby_sample,
        # Back-compat alias; prefer ``nearby_sample`` (this is an unordered
        # proximity sample, not a recency-ranked feed).
        "nearby_evidence": nearby_sample,
        "trace_note": (
            "intensity = exp(intercept + station_effect + sum(kernel "
            "contributions)); nearby_sample lists nearby sightings (unordered "
            "sample), not recent sightings."
        ),
    }


@router.get("/api/decision-records", dependencies=[Depends(require_api_key)])
def list_decision_records() -> Dict[str, Any]:
    """The human promotion audit log (most recent first, keyed: it is an audit log)."""
    records = _get_storage().list_decision_records(limit=200)
    return {
        "status": "success",
        "total_count": len(records),
        "records": [_serialize_decision_record(r) for r in records],
    }


@router.post("/api/decision-records", dependencies=[Depends(require_api_key)])
def create_decision_record(
    payload: Dict[str, Any],
    identity: ReviewerIdentity = Depends(require_trusted_reviewer),
) -> Dict[str, Any]:
    """Record a human promote/hold/reject decision over a gate-passing fit (keyed).

    This is the consequential human-in-the-loop step: automated gates are
    necessary but not sufficient; a reviewer must sign off before confidence is
    promoted. The record is immutable once written. When a Step Functions
    ``task_token`` is supplied, the waiting orchestrator execution is resumed
    (SendTaskSuccess for promote/hold, SendTaskFailure for reject).
    """
    from ..models import DecisionRecord, DecisionVerdict

    verdict = str(payload.get("verdict", "")).lower()
    if verdict not in {"promote", "hold", "reject"}:
        raise HTTPException(status_code=400, detail="verdict must be promote|hold|reject")

    pending_approval = load_pending_approval()
    token = payload.get("task_token") or (
        pending_approval.get("task_token") if isinstance(pending_approval, dict) else None
    )
    # gates_summary and kernel_version are stamped SERVER-SIDE from the current
    # fit report -- never trusted from the client body.
    gates_summary, kernel_version = _server_gate_stamp(_load_fit_report())
    record = DecisionRecord(
        id=f"decision_{uuid.uuid4().hex[:12]}",
        kernel_version=kernel_version,
        verdict=DecisionVerdict(verdict),
        reviewer=identity.display_name,
        reviewer_id=identity.reviewer_id,
        reviewer_email=identity.reviewer_email,
        reviewer_role=identity.reviewer_role,
        reason=payload.get("reason") or "",
        gates_summary=gates_summary,
        supervisor_recommendation=(
            pending_approval.get("recommendation")
            if isinstance(pending_approval, dict)
            else None
        ),
        task_token=token,
    )
    _get_storage().put_decision_record(record)

    promotion_marker: Optional[Dict[str, Any]] = None
    if verdict == "promote":
        from .promotion import apply_promotion_marker

        report = _load_fit_report() or {}
        promotion_marker = apply_promotion_marker(
            decision_id=record.id,
            kernel_version=kernel_version,
            run_id=report.get("run_id"),
            repr_id=report.get("repr_id"),
            reviewer=record.reviewer,
            effective_confidence=float(effective_confidence(report, load_promotion()) or 0.0),
        )

    token_result = _resolve_task_token(token, record) if token else None
    return {
        "status": "success",
        "record": _serialize_decision_record(record),
        "promotion": promotion_marker,
        "orchestrator": token_result,
    }


def _resolve_task_token(token: str, record: Any) -> Dict[str, Any]:
    """Resume the waiting Step Functions execution (best-effort)."""
    verdict = record.verdict.value if hasattr(record.verdict, "value") else str(record.verdict)
    try:
        import boto3
        sfn = boto3.client("stepfunctions", region_name=settings.aws_region)
        if verdict == "reject":
            sfn.send_task_failure(taskToken=token, error="HumanRejected", cause="Reviewer rejected promotion")
            return {"resumed": True, "signal": "task_failure"}
        sfn.send_task_success(
            taskToken=token,
            output=json.dumps({
                "verdict": verdict,
                "decision_id": record.id,
                "kernel_version": record.kernel_version,
                "reviewer": record.reviewer,
            }),
        )
        return {"resumed": True, "signal": "task_success"}
    except Exception as exc:  # never break the human action on a callback hiccup
        return {"resumed": False, "error": str(exc)}


# -- internals ----------------------------------------------------------------
def _parse_when(when: Optional[str]) -> datetime:
    if not when:
        return datetime.now(timezone.utc)
    try:
        dt = datetime.fromisoformat(when.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=400, detail="when must be ISO8601")
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _nearby_sample(lat: float, lng: float, radius_km: float = 15.0, limit: int = 10) -> List[Dict[str, Any]]:
    """Nearby sightings (unordered sample) with source provenance (best-effort).

    This is a proximity sample within ``radius_km`` ordered by distance, NOT a
    recency-ranked feed: do not present these as "recent sightings".

    Imported lazily so this router stays importable without the full ingestion
    stack, and wrapped so a storage hiccup never breaks the provenance trace.
    """
    try:
        from ..state import storage
        from ..storage import model_to_dict
    except Exception:
        return []

    out: List[Dict[str, Any]] = []
    try:
        for s in storage.list_sightings(limit=2000):
            d = _haversine_km(lat, lng, s.latitude, s.longitude)
            if d <= radius_km:
                out.append({
                    "sighting_id": s.sighting_id,
                    "distance_km": round(d, 2),
                    "source": s.source,
                    "timestamp": s.timestamp.isoformat(),
                    "validation_status": s.cross_validation.status.value,
                    "confidence": s.confidence,
                })
    except Exception:
        return out
    out.sort(key=lambda r: r["distance_km"])
    return out[:limit]


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))
