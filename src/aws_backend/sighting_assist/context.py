"""Assemble provenance + gate facts for sighting-assist (no LLM here)."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from ..geo_region import in_bounds
from ..kernel_model.serve import KernelForecaster, load_promotion
from ..routers.kernel import (
    _build_caveats,
    _load_fit_report,
    _nearby_sample,
    _parse_when,
    _report_consistency,
    _spatial_provenance,
    effective_confidence,
)


def build_sighting_context(
    lat: float,
    lng: float,
    *,
    when: Optional[str] = None,
    station: Optional[str] = None,
    message: str = "",
) -> Dict[str, Any]:
    """Structured facts the LLM (or template) may cite — nothing invented upstream."""
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
    report = _load_fit_report() or {}
    promotion = load_promotion()
    gate_by_cov = report.get("level1_psth") or {}
    consistency = _report_consistency(report) or {}
    level0 = report.get("level0_detector_qc") or {}

    phases = forecaster.clock_phases(moment, lat, lng)
    contributions: List[Dict[str, Any]] = []
    for name, kernel in forecaster.fit.kernels.items():
        phase = phases.get(name)
        gate = gate_by_cov.get(name) or {}
        if phase is None:
            contributions.append(
                {
                    "kernel": name,
                    "available": False,
                    "reason": "phase unavailable",
                }
            )
            continue
        contributions.append(
            {
                "kernel": name,
                "available": True,
                "phase": round(float(phase), 4),
                "log_rate_contribution": round(kernel.value(phase), 4),
                "beats_null": gate.get("beats_null"),
                "null_p": gate.get("null_p"),
                "modulation": gate.get("modulation"),
                "psth_kernel_agreement": (consistency.get(name) or {}).get("correlation"),
            }
        )

    log_intensity = forecaster.log_intensity(moment, lat, lng, station=station)
    nearby = _nearby_sample(lat, lng)
    cv = report.get("cv") or {}
    pit = report.get("pit") or {}

    integrity = _build_caveats(report)
    if isinstance(level0, dict) and level0.get("status") == "active":
        integrity = [
            item
            for item in integrity
            if "Level 0 detector QC is not yet" not in item
        ]
        if not any("Level 0 QC" in item for item in integrity):
            integrity.insert(
                2,
                "Spike-train fit uses unreviewed acoustic candidates; Level 0 QC reports reviewed outcome mix separately.",
            )

    return {
        "user_message": (message or "").strip(),
        "cell": {
            "lat": lat,
            "lng": lng,
            "when": moment.isoformat(),
            "station": station,
        },
        "forecast": {
            "log_intensity": round(log_intensity, 4),
            "intensity": round(math.exp(log_intensity), 6),
            "confidence_raw": forecaster.fit.confidence,
            "effective_confidence": effective_confidence(report, promotion),
            "promoted": bool(promotion and promotion.get("promoted")),
            "covariates_fit": report.get("covariates_fit") or [],
        },
        "integrity_conditions": integrity,
        "spatial": _spatial_provenance(lat, lng, report),
        "kernel_contributions": contributions,
        "gates_summary": {
            "level1_psth": gate_by_cov,
            "cross_validation": {
                "n_pass": cv.get("n_pass"),
                "n_folds": cv.get("n_folds"),
                "mean_deviance_skill": cv.get("mean_deviance_skill"),
                "gate_pass": cv.get("gate_pass"),
            },
            "pit_calibrated": pit.get("calibrated"),
            "time_rescaling_pass": (report.get("time_rescaling") or {}).get("pooled_pass_exp"),
        },
        "level0_detector_qc": level0 if isinstance(level0, dict) else {},
        "nearby_sample": nearby,
        "data_inventory": {
            "n_detections": report.get("n_detections"),
            "n_stations_acoustic": report.get("n_stations_acoustic"),
            "tide_overlaps_acoustic": report.get("tide_overlaps_acoustic"),
        },
        "glossary_anchors": {
            "encounter_likelihood": "/glossary#fitness-gates",
            "integrity": "/glossary#integrity-conditions",
            "level0_qc": "/glossary#level0-detector-qc",
            "provenance": "/glossary#provenance",
            "level1_psth": "/glossary#level1-psth",
        },
        "repr_id": report.get("repr_id"),
        "run_id": report.get("run_id"),
    }
