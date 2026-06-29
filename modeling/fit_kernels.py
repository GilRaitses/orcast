"""End-to-end offline fit: data -> design -> fit -> gates -> coefficients + report.

Pulls the time-series store, builds the binned design, fits the joint Poisson
GLM, runs every fitness gate (Level 1 PSTH null, Level 2 held-out CV, the
time-rescaling GOF, PIT calibration, and PSTH-vs-kernel consistency), then emits

* ``data/models/fitted_kernels.json`` -- coefficients the service loads,
* kernel-curve and time-rescaling figures, and
* ``docs/methodology/KERNEL_FIT_STATUS.md`` -- an honest per-gate report,
  including "insufficient data" when that is the truth.

Run offline (never in the request path):

    .venv-modeling/bin/python -m modeling.fit_kernels --years 3

To read the production S3 store, set ``ORCAST_STORAGE_BACKEND=aws`` plus AWS
credentials; otherwise the in-memory store is used (and the report will say so).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.aws_backend import covariates
from src.aws_backend.config import settings
from src.aws_backend.timeseries import build_timeseries_store

from .ais_noise import log_detectability
from .bases import evaluate_kernel
from .design import build_design, phase_coverage, season_phase_hours
from .effort import station_log_effort, FALLBACK_CONTINUOUS
from .estimator import fit_glm, make_fit_predict, FittedModel
from .psth import psth, psth_with_null
from .psth_vs_kernel import psth_vs_kernel
from .tide_phase import TidalPhase, HarmonicTidalPhase
from .timeutil import from_hours, to_hours
from .validation.crossval import assign_time_blocks, block_cv
from .validation.diagnostics import model_metrics, randomized_pit
from .validation.time_rescaling import run_time_rescaling, plot_time_rescaling

# Stream identifiers (mirrors src/aws_backend/ingest_timeseries.py).
ACOUSTIC = "acoustic_detections"
ACOUSTIC_REVIEWED = "orcahello_reviewed_detector_outcomes"
WATER_LEVEL = "env_water_level"
CURRENTS = "env_currents"
STATION_UPTIME = "station_uptime"
NDBC_MET = "noaa_ndbc_stdmet"
SPATIAL_GRID = "spatial_grid_covariates"
OBIS_VERIFIED = "obis_verified"
INATURALIST_VERIFIED = "inaturalist_verified"

CYCLIC = ("diel", "tide", "lunar", "season")

REPO_ROOT = Path(__file__).resolve().parents[1]
# Output base is overridable so the fit can run in a read-only Lambda image
# (point ORCAST_FIT_OUTPUT_DIR at /tmp there; artifacts then sync to S3).
_OUTPUT_DIR = Path(os.getenv("ORCAST_FIT_OUTPUT_DIR", str(REPO_ROOT)))
COEFF_PATH = _OUTPUT_DIR / "data" / "models" / "fitted_kernels.json"
REPORT_JSON_PATH = _OUTPUT_DIR / "data" / "models" / "fit_report.json"
FIT_PLAN_PATH = _OUTPUT_DIR / "data" / "models" / "fit_plan.json"
SNAPSHOT_MANIFEST_PATH = _OUTPUT_DIR / "data" / "models" / "snapshot_manifest.json"
_SNAPSHOT_REGISTRY: Dict[str, Dict[str, Any]] = {}
CURRENT_POINTER_PATH = _OUTPUT_DIR / "data" / "models" / "current.json"
FIG_DIR = _OUTPUT_DIR / "docs" / "methodology" / "figures" / "kernels"
REPORT_PATH = _OUTPUT_DIR / "docs" / "methodology" / "KERNEL_FIT_STATUS.md"

# Minimums below which a fit is not attempted (reported as insufficient data).
MIN_DETECTIONS = 300
MIN_BINS = 500

# Negative binomial (NB2) is the primary family: acoustic detection counts are
# overdispersed relative to Poisson, which fails the Poisson GOF gates. Poisson
# is still fit alongside it for the report's overdispersion comparison.
PRIMARY_FAMILY = "negbin"

# A cyclic covariate whose observed phase support covers less than this fraction
# of its cycle is treated as extrapolated and excluded from the fit/serving.
MIN_PHASE_COVERAGE = 0.9

# --- TA5 smoothness (roughness) prior -------------------------------------- #
# A soft second-derivative penalty on the Fourier kernel coefficients (a
# variance reducer on the EXISTING kernels, not added flexibility). The strength
# is chosen by NESTED block_cv inside each training fold over this grid; lambda=0
# recovers the unpenalized fit exactly. The integrate is OPT-IN: the prior is OFF
# by default so the served default fit stays byte-identical (charter B.4). Turn
# it on with run_fit(smoothness_prior=True) or ORCAST_SMOOTHNESS_PRIOR=1, and
# re-measure on the SERVED store under the G2 gate before any promotion (B.3).
# See research/signal_modeling/graduation/TA5_shape_priors.md.
SMOOTHNESS_LAMBDA_GRID = (0.0, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1)
SMOOTHNESS_ORDER = 2


def _smoothness_prior_enabled() -> bool:
    return os.getenv("ORCAST_SMOOTHNESS_PRIOR", "").strip().lower() in ("1", "true", "yes", "on")


# --- TA2 clean-baseline enablers ------------------------------------------- #
# Partial-pooling random station intercept (ridge 1/tau^2 on all-station
# deviations) + a flat nested-CV ridge (1/s_k^2) on the kernel coefficients,
# selected by nested block_cv over this grid. Enablers, not levers: neither
# promotes. OFF by default so the served fit stays byte-identical (B.4); opt in
# with run_fit(baseline_enablers=True) or ORCAST_BASELINE_ENABLERS=1.
# See research/signal_modeling/graduation/TA2_hierarchical_nb.md.
# tau is the random-intercept group SD (station penalty = 1/(tau^2*nobs), so tau
# carries its log-rate-SD meaning). The kernel ridge grid is in nested-CV-selected
# normalized units (gentle, comparable to the TA5 smoothness scale); 0.0 lets the
# selector decline the extra flat ridge.
BASELINE_POOLING_TAU_GRID = (0.25, 0.5, 1.0, 2.0)
BASELINE_RIDGE_LAMBDA_GRID = (0.0, 0.01, 0.03)


def _baseline_enablers_enabled() -> bool:
    return os.getenv("ORCAST_BASELINE_ENABLERS", "").strip().lower() in ("1", "true", "yes", "on")


def _wide_window():
    return datetime(1970, 1, 1, tzinfo=timezone.utc), datetime(2100, 1, 1, tzinfo=timezone.utc)


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_hex(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _content_id(prefix: str, payload: Any) -> str:
    return f"{prefix}_{_sha256_hex(payload)[:16]}"


def _records_digest(records: List[dict]) -> str:
    return _sha256_hex(records)


def _fit_plan(bin_hours: float) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "schema_version": "orcast/fit_plan/v1",
        "model": "negbin_glm_lnp",
        "bin_hours": float(bin_hours),
        "covariates_candidate": list(CYCLIC),
        "exclusion_rules": [
            "drop tide when currents do not overlap acoustic detections",
            f"drop cyclic covariates when phase coverage < {MIN_PHASE_COVERAGE:.2f}",
        ],
        "minimums": {"detections": MIN_DETECTIONS, "station_bins": MIN_BINS},
        "gates": [
            "level1_psth_phase_shuffle",
            "time_blocked_cv",
            "held_out_pit",
            "time_rescaling_in_sample",
            "psth_vs_kernel_diagnostic",
        ],
        "primary_family": PRIMARY_FAMILY,
        "confidence_policy": (
            "CV or time-rescaling required before nonzero confidence; PIT credit "
            "requires time-rescaling; Level 1 null can add support."
        ),
    }
    body["fit_plan_id"] = _content_id("fitplan", body)
    return body


def _stream_manifest(stream: str, station: str, records: List[dict]) -> Dict[str, Any]:
    return {
        "stream": stream,
        "station": station,
        "record_count": len(records),
        "span": _span(records),
        "sha256": _records_digest(records),
    }


def _snapshot_manifest(
    acoustic: Dict[str, List[dict]],
    uptime: Dict[str, List[dict]],
    currents: List[dict],
    fit_plan_id: str,
    bin_hours: float,
    reviewed: Optional[Dict[str, List[dict]]] = None,
    ndbc: Optional[Dict[str, List[dict]]] = None,
    spatial_grid: Optional[List[dict]] = None,
    validation: Optional[Dict[str, List[dict]]] = None,
) -> Dict[str, Any]:
    streams: List[Dict[str, Any]] = []
    for station, records in sorted(acoustic.items()):
        streams.append(_stream_manifest(ACOUSTIC, station, records))
    for station, records in sorted(uptime.items()):
        streams.append(_stream_manifest(STATION_UPTIME, station, records))
    if currents:
        streams.append(_stream_manifest(CURRENTS, "pooled", currents))
    for station, records in sorted((reviewed or {}).items()):
        streams.append(_stream_manifest(ACOUSTIC_REVIEWED, station, records))
    for station, records in sorted((ndbc or {}).items()):
        streams.append(_stream_manifest(NDBC_MET, station, records))
    if spatial_grid:
        streams.append(_stream_manifest(SPATIAL_GRID, "san_juan_pilot", spatial_grid))
    for stream_name, grouped in sorted((validation or {}).items()):
        for station, records in sorted(grouped.items()):
            streams.append(_stream_manifest(stream_name, station, records))

    spans = [s["span"] for s in streams if s.get("span")]
    start = min((s[0] for s in spans), default=None)
    end = max((s[1] for s in spans), default=None)
    body: Dict[str, Any] = {
        "schema_version": "orcast/snapshot_manifest/v1",
        "fit_plan_id": fit_plan_id,
        "data_window": {
            "start": start,
            "end": end,
            "bin_hours": float(bin_hours),
            "timezone": "UTC",
            "streams": sorted({s["stream"] for s in streams}),
        },
        "streams": streams,
        "ingest_run_ids": [],
    }
    body["snap_id"] = _content_id("snap", body)
    return body


def freeze_dataset_snapshot(store, bin_hours: float = 1.0, write_outputs: bool = True) -> Dict[str, Any]:
    """Materialize snapshot_manifest.json and pin stream payloads for replay."""
    start, end = _wide_window()
    acoustic, uptime, currents = read_streams(store, start, end)
    reviewed, ndbc, spatial_grid, validation = read_auxiliary_streams(store, start, end)
    fit_plan = _fit_plan(bin_hours)
    manifest = _snapshot_manifest(
        acoustic=acoustic,
        uptime=uptime,
        currents=currents,
        fit_plan_id=str(fit_plan["fit_plan_id"]),
        bin_hours=bin_hours,
        reviewed=reviewed,
        ndbc=ndbc,
        spatial_grid=spatial_grid,
        validation=validation,
    )
    manifest["frozen_data"] = {
        "acoustic": acoustic,
        "uptime": uptime,
        "currents": currents,
        "reviewed": reviewed,
        "ndbc": ndbc,
        "spatial_grid": spatial_grid,
        "validation": validation,
    }
    if write_outputs:
        _write_snapshot_manifest(manifest, versioned=True)
        _write_fit_plan(fit_plan)
    _SNAPSHOT_REGISTRY[str(manifest["snap_id"])] = manifest
    return manifest


def load_snapshot_manifest(snap_id: str) -> Optional[Dict[str, Any]]:
    if snap_id in _SNAPSHOT_REGISTRY:
        return _SNAPSHOT_REGISTRY[snap_id]
    versioned = SNAPSHOT_MANIFEST_PATH.parent / "snapshots" / snap_id / "manifest.json"
    if versioned.exists():
        manifest = json.loads(versioned.read_text())
        _SNAPSHOT_REGISTRY[snap_id] = manifest
        return manifest
    if SNAPSHOT_MANIFEST_PATH.exists():
        manifest = json.loads(SNAPSHOT_MANIFEST_PATH.read_text())
        if manifest.get("snap_id") == snap_id:
            _SNAPSHOT_REGISTRY[snap_id] = manifest
            return manifest
    return None


def read_streams_from_snapshot(manifest: Dict[str, Any]):
    """Return stream tuples from a frozen manifest payload."""
    frozen = manifest.get("frozen_data") or {}
    acoustic = frozen.get("acoustic") or {}
    uptime = frozen.get("uptime") or {}
    currents = frozen.get("currents") or []
    reviewed = frozen.get("reviewed") or {}
    ndbc = frozen.get("ndbc") or {}
    spatial_grid = frozen.get("spatial_grid") or []
    validation = frozen.get("validation") or {}
    return acoustic, uptime, currents, reviewed, ndbc, spatial_grid, validation


def _representation_payload(
    model: FittedModel,
    coeff_payload: Dict[str, Any],
    report: Dict[str, object],
    bin_hours: float,
) -> Dict[str, Any]:
    return {
        "schema_version": "orcast/representation/v1",
        "model": "negbin_glm_lnp",
        "family": model.family,
        "bin_hours": float(bin_hours),
        "covariates_fit": list(model.covariates),
        "covariates_excluded": report.get("covariates_excluded", {}),
        "coefficients": {
            "intercept": coeff_payload.get("intercept"),
            "station_effects": coeff_payload.get("station_effects"),
            "kernels": coeff_payload.get("kernels"),
            "dispersion_alpha": report.get("dispersion_alpha"),
        },
    }


def _run_manifest(report: Dict[str, object], coeff_payload: Dict[str, Any]) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "schema_version": "orcast/fit_run/v1",
        "snap_id": report.get("dataset_snapshot_id"),
        "repr_id": report.get("repr_id"),
        "fit_plan_id": report.get("fit_plan_id"),
        "generated_at": report.get("generated_at"),
        "data_window": report.get("data_window"),
        "input_hashes": report.get("input_hashes"),
        "output_hashes": {
            "fitted_kernels": _sha256_hex(coeff_payload),
            "fit_report": _sha256_hex(report),
        },
        "status": report.get("status"),
        "confidence": report.get("confidence"),
    }
    body["run_id"] = _content_id("run", body)
    return body


def _span(records: List[dict]):
    """(min_iso, max_iso) over a record list, or None when empty/unparseable."""
    hours = []
    for r in records:
        t = r.get("t")
        if t is None:
            continue
        try:
            hours.append(to_hours(t))
        except (ValueError, TypeError):
            continue
    if not hours:
        return None
    return from_hours(min(hours)).isoformat(), from_hours(max(hours)).isoformat()


def _spans_overlap(a, b) -> bool:
    if not a or not b:
        return False
    a0, a1 = to_hours(a[0]), to_hours(a[1])
    b0, b1 = to_hours(b[0]), to_hours(b[1])
    return a0 <= b1 and b0 <= a1


def read_streams(store, start: datetime, end: datetime):
    """Read acoustic (spike trains), uptime (effort) and currents (tide)."""
    def safe_list(stream):
        try:
            return store.list_stations(stream)
        except Exception:
            return []

    def safe_series(stream, station):
        try:
            return store.get_series(stream, station, start, end)
        except Exception:
            return []

    acoustic = {st: safe_series(ACOUSTIC, st) for st in safe_list(ACOUSTIC)}
    acoustic = {st: recs for st, recs in acoustic.items() if recs}
    uptime = {st: safe_series(STATION_UPTIME, st) for st in safe_list(STATION_UPTIME)}
    uptime = {st: recs for st, recs in uptime.items() if recs}

    currents: List[dict] = []
    for st in safe_list(CURRENTS):
        currents.extend(safe_series(CURRENTS, st))
    if not currents:
        for st in safe_list(WATER_LEVEL):
            currents.extend(safe_series(WATER_LEVEL, st))
    return acoustic, uptime, currents


def read_auxiliary_streams(store, start: datetime, end: datetime):
    """Read P0 auxiliary streams used for QC, detectability, spatial, validation."""

    def safe_list(stream):
        try:
            return store.list_stations(stream)
        except Exception:
            return []

    def safe_series(stream, station):
        try:
            return store.get_series(stream, station, start, end)
        except Exception:
            return []

    reviewed = {
        st: safe_series(ACOUSTIC_REVIEWED, st)
        for st in safe_list(ACOUSTIC_REVIEWED)
    }
    reviewed = {st: recs for st, recs in reviewed.items() if recs}

    ndbc = {st: safe_series(NDBC_MET, st) for st in safe_list(NDBC_MET)}
    ndbc = {st: recs for st, recs in ndbc.items() if recs}

    spatial_grid: List[dict] = []
    for st in safe_list(SPATIAL_GRID):
        spatial_grid.extend(safe_series(SPATIAL_GRID, st))

    validation: Dict[str, Dict[str, List[dict]]] = {}
    for stream in (OBIS_VERIFIED, INATURALIST_VERIFIED):
        grouped = {st: safe_series(stream, st) for st in safe_list(stream)}
        grouped = {st: recs for st, recs in grouped.items() if recs}
        if grouped:
            validation[stream] = grouped

    return reviewed, ndbc, spatial_grid, validation


def _level0_detector_qc(reviewed: Dict[str, List[dict]]) -> Dict[str, object]:
    records = [record for recs in reviewed.values() for record in recs]
    if not records:
        return {
            "status": "not_available",
            "truth_label": "planned",
            "reason": "No reviewed OrcaHello outcome labels are available in the time-series store.",
            "required_before_full_confidence": True,
        }

    from collections import Counter

    counts = Counter(str(record.get("outcome") or "unknown") for record in records)
    total = len(records)
    reviewed_total = total - counts.get("unreviewed", 0)
    confirmed = counts.get("confirmed", 0)
    false_pos = counts.get("false_positive", 0)
    per_station: Dict[str, Dict[str, int]] = {}
    for station, station_records in reviewed.items():
        per_station[station] = dict(Counter(str(r.get("outcome") or "unknown") for r in station_records))

    false_positive_rate = (
        false_pos / reviewed_total if reviewed_total else None
    )
    return {
        "status": "active",
        "truth_label": "live",
        "outcome_counts": dict(counts),
        "n_reviewed_labels": total,
        "confirmed_fraction": round(confirmed / total, 4) if total else None,
        "false_positive_rate": round(false_positive_rate, 4) if false_positive_rate is not None else None,
        "unknown_fraction": round(counts.get("unknown", 0) / total, 4) if total else None,
        "per_station": per_station,
        "required_before_full_confidence": True,
    }


def _spatial_covariate_summary(spatial_grid: List[dict]) -> Dict[str, object]:
    if not spatial_grid:
        return {
            "status": "not_available",
            "truth_label": "planned",
            "reason": "No spatial grid covariates are stored for the pilot region.",
        }
    depths = [r["depth_m"] for r in spatial_grid if r.get("depth_m") is not None]
    shores = [r["nearest_shore_m"] for r in spatial_grid if r.get("nearest_shore_m") is not None]
    return {
        "status": "active",
        "truth_label": "live",
        "cell_count": len(spatial_grid),
        "depth_m_min": min(depths) if depths else None,
        "depth_m_max": max(depths) if depths else None,
        "nearest_shore_m_min": min(shores) if shores else None,
        "nearest_shore_m_max": max(shores) if shores else None,
    }


def _detectability_summary(ndbc: Dict[str, List[dict]]) -> Dict[str, object]:
    records = [record for recs in ndbc.values() for record in recs]
    if not records:
        return {
            "status": "not_available",
            "truth_label": "planned",
            "reason": "No NDBC detectability covariates are stored.",
        }
    span = _span(records)
    return {
        "status": "active",
        "truth_label": "live",
        "record_count": len(records),
        "stations": sorted(ndbc.keys()),
        "span": span,
        "note": "Used as detectability/noise metadata; not yet a fitted animal-behavior kernel.",
    }


def _validation_summary(validation: Dict[str, Dict[str, List[dict]]]) -> Dict[str, object]:
    if not validation:
        return {
            "status": "not_available",
            "truth_label": "planned",
            "reason": "No held-out external validation records are stored.",
        }
    by_stream = {
        stream: sum(len(recs) for recs in grouped.values())
        for stream, grouped in validation.items()
    }
    return {
        "status": "active",
        "truth_label": "live",
        "record_counts": by_stream,
        "note": "Held-out validation only; not used for temporal kernel fitting.",
    }


def _station_intensity_fn(
    model: FittedModel,
    station: str,
    lat: float,
    lng: float,
    tide: Optional[TidalPhase],
    uptime: Optional[Dict[str, List[dict]]] = None,
    detection_times: Optional[np.ndarray] = None,
    effort_fallback: str = FALLBACK_CONTINUOUS,
    noise_by_station: Optional[Dict[str, object]] = None,
    ais_kappa: float = 0.0,
):
    """Continuous intensity (per hour) for a station from the fitted kernels.

    The observed point process has conditional intensity
    ``lambda_obs(t) = exp(b0 + a_station + kernels) * E(t)`` where ``E(t)`` is the
    relative observation effort (1 = fully up, ~0 = detector down). The
    ``station_log_effort`` term adds ``log E(t)`` to the log-rate so the
    time-rescaling integral does not accumulate hazard across verified downtime.
    With ``uptime=None`` or non-binding/continuous effort it adds ``0.0`` and is a
    strict no-op (it differs from the per-bin ``log(exposure)`` only by the
    constant ``log(bin_hours)`` the intercept already absorbs, so it is NOT
    re-added here).
    """
    base = model.intercept + model.station_effects.get(station, 0.0)

    def intensity(t_hours: np.ndarray) -> np.ndarray:
        t_hours = np.atleast_1d(np.asarray(t_hours, dtype=float))
        log_rate = np.full(t_hours.shape, base)
        phases: Dict[str, np.ndarray] = {}
        if "diel" in model.kernels:
            phases["diel"] = np.array([covariates.diel_phase(from_hours(t), lng) for t in t_hours])
        if "lunar" in model.kernels:
            phases["lunar"] = np.array([covariates.lunar_phase(from_hours(t))["phase"] for t in t_hours])
        if "season" in model.kernels:
            phases["season"] = np.array([season_phase_hours(t) for t in t_hours])
        if "tide" in model.kernels and tide is not None:
            phases["tide"] = tide.phases(t_hours)
        for name, ph in phases.items():
            k = model.kernels[name]
            log_rate = log_rate + evaluate_kernel(ph, k.cos, k.sin)
        log_rate = log_rate + station_log_effort(
            uptime, station, t_hours,
            fallback=effort_fallback, detection_times=detection_times,
        )
        # TA3: add log D_ais on the SAME integration grid as the design offset, so
        # the time-rescaling compensator does not accumulate hazard during heavy
        # vessel masking. No-op (adds 0.0) when no index / kappa<=0.
        if noise_by_station and ais_kappa > 0:
            log_rate = log_rate + log_detectability(
                noise_by_station, station, t_hours, kappa=ais_kappa,
            )
        return np.exp(log_rate)

    return intensity


def run_fit(
    store,
    bin_hours: float = 1.0,
    write_outputs: bool = True,
    make_figures: bool = True,
    dataset_snapshot_id: Optional[str] = None,
    smoothness_prior: Optional[bool] = None,
    baseline_enablers: Optional[bool] = None,
    noise_by_station: Optional[Dict[str, object]] = None,
    ais_kappa: float = 0.0,
) -> Dict[str, object]:
    """Fit and gate the kernels; return a structured report dict.

    ``smoothness_prior`` opts into the TA5 roughness prior (default OFF, falling
    back to ``ORCAST_SMOOTHNESS_PRIOR``); when on, the Fourier kernel
    coefficients are ridge-penalized with the strength chosen by nested
    ``block_cv``. The default (OFF) keeps the served fit byte-identical (B.4).

    ``baseline_enablers`` opts into the TA2 clean-baseline enablers (default OFF,
    falling back to ``ORCAST_BASELINE_ENABLERS``): the partial-pooling random
    station intercept + nested-CV ridge on the kernel coefficients, plus the
    cloglog presence COMPANION readout. Neither promotes; the goal is a
    fold-stable, calibrated baseline that future covariates are judged against.

    ``noise_by_station`` / ``ais_kappa`` are the TA3 AIS detectability wire: a
    per-station proximity-noise index folded into the exposure (B.2 effort term).
    The default (``None`` / ``0.0``) is a strict no-op; a real AIS index is an
    operator-/deploy-gated build (TA3 §2).
    """
    use_smoothness = _smoothness_prior_enabled() if smoothness_prior is None else bool(smoothness_prior)
    use_baseline = _baseline_enablers_enabled() if baseline_enablers is None else bool(baseline_enablers)
    fit_plan = _fit_plan(bin_hours)
    if dataset_snapshot_id:
        manifest = load_snapshot_manifest(dataset_snapshot_id)
        if manifest is None:
            raise ValueError(f"Unknown dataset_snapshot_id: {dataset_snapshot_id}")
        acoustic, uptime, currents, reviewed, ndbc, spatial_grid, validation = read_streams_from_snapshot(manifest)
        snapshot_manifest = manifest
        if manifest.get("fit_plan_id"):
            fit_plan = {"fit_plan_id": manifest["fit_plan_id"]}
    else:
        start, end = _wide_window()
        acoustic, uptime, currents = read_streams(store, start, end)
        reviewed, ndbc, spatial_grid, validation = read_auxiliary_streams(store, start, end)
        snapshot_manifest = _snapshot_manifest(
            acoustic=acoustic,
            uptime=uptime,
            currents=currents,
            fit_plan_id=str(fit_plan["fit_plan_id"]),
            bin_hours=bin_hours,
            reviewed=reviewed,
            ndbc=ndbc,
            spatial_grid=spatial_grid,
            validation=validation,
        )

    n_detections = sum(len(v) for v in acoustic.values())
    report: Dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "storage_backend": settings.storage_backend,
        "fit_plan_id": fit_plan["fit_plan_id"],
        "fit_plan_uri": f"file://{FIT_PLAN_PATH}",
        "dataset_snapshot_id": snapshot_manifest["snap_id"],
        "snapshot_manifest_uri": f"file://{SNAPSHOT_MANIFEST_PATH}",
        "data_window": snapshot_manifest["data_window"],
        "input_hashes": {
            stream["stream"] + ":" + stream["station"]: stream["sha256"]
            for stream in snapshot_manifest["streams"]
        },
        "ingest_run_ids": snapshot_manifest["ingest_run_ids"],
        "n_stations_acoustic": len(acoustic),
        "n_detections": n_detections,
        "n_stations_uptime": len(uptime),
        "n_current_records": len(currents),
        "bin_hours": bin_hours,
        # Disclosure: acoustic "detections" are UNREVIEWED model candidates
        # (OrcaHello/Orcasound), not human-confirmed events. Serving must say so.
        "detections_unreviewed_candidates": True,
        "level0_detector_qc": _level0_detector_qc(reviewed),
        "spatial_covariates": _spatial_covariate_summary(spatial_grid),
        "detectability_covariates": _detectability_summary(ndbc),
        "external_validation": _validation_summary(validation),
    }

    # Tide phase: prefer the harmonic constituent model (defined for every
    # timestamp, so it clears the L2 phase-coverage gate); fall back to the
    # onset-interpolation TidalPhase when the harmonic fit is unavailable or its
    # reconstruction is poor (R^2 <= 0.5), never silently using a bad fit.
    tide = None
    tide_model_used = "none"
    tide_reconstruction_r2 = None
    if currents:
        harmonic = HarmonicTidalPhase.from_records(currents)
        if harmonic is not None and harmonic.reconstruction_r2 > 0.5:
            tide = harmonic
            tide_model_used = "harmonic"
            tide_reconstruction_r2 = harmonic.reconstruction_r2
        else:
            tide = TidalPhase.from_records(currents)
            tide_model_used = "onset_interpolation"
            if harmonic is not None:
                tide_reconstruction_r2 = harmonic.reconstruction_r2
    report["tide_model"] = tide_model_used
    report["tide_reconstruction_r2"] = tide_reconstruction_r2
    report["tide_onsets_detected"] = int(tide.onsets.size) if tide else 0

    # Temporal coverage: the tide kernel is only meaningful when the current
    # series overlaps the acoustic detections. Disclose the spans and overlap.
    acoustic_span = _span([r for recs in acoustic.values() for r in recs])
    currents_span = _span(currents)
    report["acoustic_span"] = acoustic_span
    report["currents_span"] = currents_span
    report["tide_overlaps_acoustic"] = bool(_spans_overlap(acoustic_span, currents_span))

    if n_detections < MIN_DETECTIONS:
        report["status"] = "insufficient_data"
        report["reason"] = (
            f"only {n_detections} acoustic detections available "
            f"(need >= {MIN_DETECTIONS} before a temporal fit is credible)"
        )
        if write_outputs:
            _write_fit_plan(fit_plan)
            _write_snapshot_manifest(snapshot_manifest)
            _write_report(report)
            _write_report_json(report)
            _maybe_write_s3()
        return report

    df = build_design(
        acoustic, uptime, tide_phase=tide, bin_hours=bin_hours,
        noise_by_station=noise_by_station, ais_kappa=ais_kappa,
    )
    report["ais_effort"] = {
        "active": bool(noise_by_station and ais_kappa > 0),
        "kappa": float(ais_kappa),
        "coverage": "us_side_partial" if (noise_by_station and ais_kappa > 0) else None,
        "note": "AIS detectability folded into exposure (B.2 effort term, 0 added presence params). "
                "Default no-op; a real AIS index is an operator-gated build (TA3 §2). When inactive, "
                "log E remains flat under the current disjoint/constant station_uptime.",
    }
    report["n_bins"] = int(len(df))
    report["effort_assumed_continuous"] = bool(df.attrs.get("effort_assumed_continuous", True))

    if len(df) < MIN_BINS:
        report["status"] = "insufficient_data"
        report["reason"] = f"only {len(df)} station-bins after binning (need >= {MIN_BINS})"
        if write_outputs:
            _write_fit_plan(fit_plan)
            _write_snapshot_manifest(snapshot_manifest)
            _write_report(report)
            _write_report_json(report)
            _maybe_write_s3()
        return report

    # --- Decide which covariates are actually fittable ------------------------
    # Start from the cyclic set, then drop covariates that are unmeasurable or
    # extrapolated, recording WHY so the report and serving disclose it.
    fit_covariates, cov_notes = _select_covariates(df, report)
    report["covariates_excluded"] = cov_notes

    # --- Level 1: PSTH + phase-shuffle null per covariate --------------------
    rng = np.random.default_rng(0)
    level1: Dict[str, dict] = {}
    for cov in CYCLIC:
        if cov not in df.columns or not np.all(np.isfinite(df[cov].to_numpy(dtype=float))):
            continue
        res = psth_with_null(
            df[cov].to_numpy(dtype=float), df["y"].to_numpy(dtype=float),
            df["exposure"].to_numpy(dtype=float), n_bins=24, n_boot=300, n_shuffles=500, rng=rng,
        )
        level1[cov] = {
            "modulation": res["modulation"],
            "null_z": res["null"]["z"],
            "null_p": res["null"]["p_value"],
            "beats_null": res["null"]["beats_null"],
        }
    report["level1_psth"] = level1
    # Cross-station consistency of the marginal PSTH is the L1 reproducibility
    # criterion. With a single station it is NOT testable -- abstain rather than
    # pass a weaker single-station proxy.
    report["level1_cross_station"] = _cross_station_consistency(df, fit_covariates)

    # --- Level 2: joint GLM (NB2 primary, Poisson alongside for comparison) ---
    # TA5 smoothness prior (opt-in, default OFF -> byte-identical served fit).
    # When on, the served coefficients are fit at a single lambda chosen by
    # nested block_cv on the full training data; the CV/PIT gates below select
    # lambda per-fold so the reported held-out numbers reflect the penalized
    # model honestly (no peeking).
    smooth_grid = SMOOTHNESS_LAMBDA_GRID if use_smoothness else None
    baseline_grid = (
        {"pooling_tau": BASELINE_POOLING_TAU_GRID, "ridge_lambda": BASELINE_RIDGE_LAMBDA_GRID}
        if use_baseline else None
    )
    selected_lambda_full = 0.0
    baseline_hypers_full = {"pooling_tau": 0.0, "ridge_lambda": 0.0}
    if use_smoothness:
        from .estimator import _select_smoothness_lambda
        selected_lambda_full = _select_smoothness_lambda(
            df, tuple(fit_covariates), PRIMARY_FAMILY, SMOOTHNESS_LAMBDA_GRID,
            n_harmonics=2, smoothness_order=SMOOTHNESS_ORDER,
        )
    if use_baseline:
        from .estimator import _select_baseline_hypers
        tau_full, ridge_full = _select_baseline_hypers(
            df, tuple(fit_covariates), PRIMARY_FAMILY, baseline_grid, n_harmonics=2,
        )
        baseline_hypers_full = {"pooling_tau": tau_full, "ridge_lambda": ridge_full}

    _model_kwargs = dict(smoothness_lambda=selected_lambda_full, smoothness_order=SMOOTHNESS_ORDER)
    if use_baseline:
        _model_kwargs.update(
            use_station_effects="partial_pool" if baseline_hypers_full["pooling_tau"] > 0 else True,
            pooling_tau=baseline_hypers_full["pooling_tau"],
            ridge_lambda=baseline_hypers_full["ridge_lambda"],
        )
    model = fit_glm(df, covariates=tuple(fit_covariates), n_harmonics=2, family=PRIMARY_FAMILY, **_model_kwargs)
    poisson_model = fit_glm(df, covariates=tuple(fit_covariates), n_harmonics=2, family="poisson")
    report["family"] = model.family
    report["dispersion_alpha"] = model.dispersion_alpha
    report["pearson_dispersion"] = model.pearson_dispersion
    report["poisson_pearson_dispersion"] = poisson_model.pearson_dispersion
    report["covariates_fit"] = model.covariates
    report["intercept"] = model.intercept
    report["station_effects"] = model.station_effects

    mu = model.predict(df)
    report["metrics"] = model_metrics(
        df["y"].to_numpy(dtype=float), mu, df["exposure"].to_numpy(dtype=float),
        n_params=len(model.column_names),
    )

    # Held-out time-blocked CV (uses the primary family). With the prior on,
    # lambda is selected by nested block_cv inside each outer training fold; the
    # per-fold picks are captured for the honesty report.
    cv_selection_log: List[float] = []
    baseline_selection_log: List[dict] = []
    cv = block_cv(
        df,
        make_fit_predict(
            covariates=tuple(model.covariates), n_harmonics=2, family=PRIMARY_FAMILY,
            smoothness_lambda_grid=smooth_grid, smoothness_order=SMOOTHNESS_ORDER,
            selection_log=(cv_selection_log if use_smoothness else None),
            baseline_grid=baseline_grid,
            baseline_selection_log=(baseline_selection_log if use_baseline else None),
        ),
        n_blocks=5,
    )
    report["cv"] = {
        "n_folds": cv["n_folds"], "n_pass": cv["n_pass"],
        "mean_deviance_skill": cv["mean_deviance_skill"],
        "gate_pass": cv["gate_pass"], "null_test": cv.get("null_test", {}),
    }
    report["cv"]["per_fold_deviance_skill"] = [f.get("deviance_skill") for f in cv.get("folds", [])]
    report["smoothness_prior"] = _smoothness_prior_report(
        use_smoothness, df, tuple(model.covariates), selected_lambda_full, cv_selection_log, cv,
    )
    report["baseline_enablers"] = _baseline_enablers_report(
        use_baseline, df, tuple(model.covariates), baseline_hypers_full, baseline_selection_log, cv,
    )
    report["baseline_scorecard"] = {
        "climatology": {
            "status": "live",
            "mean_deviance_skill": cv["mean_deviance_skill"],
            "folds_passing": cv["n_pass"],
            "n_folds": cv["n_folds"],
        },
        "single_covariate": {"status": "planned"},
        "persistence": {"status": "planned"},
        "recent_density": {"status": "planned"},
    }

    # PIT calibration on HELD-OUT folds for both families: the headline gate is
    # the NB PIT (primary); the Poisson PIT is reported so overdispersion is
    # visible (Poisson typically fails, NB recovers calibration).
    report["pit"] = _held_out_pit(
        df, tuple(model.covariates), PRIMARY_FAMILY, n_blocks=5, seed=1,
        smoothness_lambda_grid=smooth_grid, baseline_grid=baseline_grid,
    )
    report["pit_poisson"] = _held_out_pit(df, tuple(model.covariates), "poisson", n_blocks=5, seed=11)
    if use_baseline:
        report["presence_reframe"] = _presence_reframe(df, tuple(model.covariates), n_blocks=5)
    report["overdispersion"] = {
        "poisson_pearson_dispersion": poisson_model.pearson_dispersion,
        "nb_dispersion_alpha": model.dispersion_alpha,
        "poisson_pit_calibrated": report["pit_poisson"].get("calibrated"),
        "nb_pit_calibrated": report["pit"].get("calibrated"),
        "note": (
            "Negative binomial (NB2) absorbs the count overdispersion that makes "
            "the Poisson PIT/time-rescaling gates fail on the single-station data."
        ),
    }

    # PSTH-vs-kernel consistency is a DIAGNOSTIC, not a fitness gate: a correctly
    # de-confounded joint kernel can legitimately diverge from the marginal PSTH
    # under correlated covariates, so it must not penalise confidence.
    consistency: Dict[str, dict] = {}
    for cov in model.covariates:
        c = psth_vs_kernel(df, model, cov, n_bins=24, n_boot=200, rng=np.random.default_rng(2))
        consistency[cov] = {"correlation": c.get("correlation"), "agrees": c.get("agrees")}
    report["psth_vs_kernel_diagnostic"] = consistency

    # Time-rescaling GOF (pooled rescaled IEIs across stations). In-sample: the
    # intensity is the full-data fit, so this is labelled in_sample for honesty.
    tr = _time_rescaling_report(
        model, acoustic, tide, bin_hours, uptime=uptime,
        noise_by_station=noise_by_station, ais_kappa=ais_kappa,
    )
    tr["in_sample"] = True
    tr["evaluation_scope"] = "in_sample"
    report["time_rescaling"] = tr

    # Bin-level timing GOF readout (item 3b / RD): the held-out NB PIT + CV
    # deviance skill surfaced together as the DEFINITION of the alternative
    # bin-level timing gate, with the Poisson PIT as the overdispersion contrast.
    # ADOPTED (2026-06-27 supervisor decision, B.1; see DECISION_RECORD):
    # ``ADOPT_BIN_LEVEL_TIMING_GATE = True`` in _confidence_from_gates, so the
    # served timing gate accepts EITHER event-level Exp(1) rescaling OR the
    # bin-level NB-PIT readout passing. (This comment previously said "NOT
    # adopted / flag defaults OFF" -- stale; DE2 row M2.)
    tr["bin_count_gof"] = _bin_level_timing_readout(report)

    # --- confidence from gates ----------------------------------------------
    report["confidence"] = _confidence_from_gates(report)
    report["status"] = "fitted"
    coeff_payload = _fitted_payload(model, report["confidence"], report, bin_hours)
    representation = _representation_payload(model, coeff_payload, report, bin_hours)
    repr_id = _content_id("repr", representation)
    report["repr_id"] = repr_id
    report["kernel_version"] = repr_id
    coeff_payload["version"] = repr_id
    coeff_payload["repr_id"] = repr_id
    report["artifact_uris"] = {
        "fitted_kernels": f"representations/{repr_id}/fitted_kernels.json",
        "representation": f"representations/{repr_id}/representation.json",
    }
    run_manifest = _run_manifest(report, coeff_payload)
    report["run_id"] = run_manifest["run_id"]
    coeff_payload["run_id"] = run_manifest["run_id"]
    report["artifact_uris"]["fit_report"] = f"runs/{run_manifest['run_id']}/fit_report.json"
    report["artifact_uris"]["run_manifest"] = f"runs/{run_manifest['run_id']}/manifest.json"

    if write_outputs:
        _write_fit_plan(fit_plan)
        _write_snapshot_manifest(snapshot_manifest)
        _write_coefficients(coeff_payload, representation, run_manifest, report)
        if make_figures:
            _write_figures(model, report)
        _write_report(report)
        _write_report_json(report)
        _maybe_write_s3()

    return report


def _select_covariates(df: pd.DataFrame, report: Dict[str, object]):
    """Choose the covariates to fit/serve; record exclusions and their reasons.

    * Drop ``tide`` when the current series does not overlap the acoustic
      detections in time (the tidal phase aligned to detections is meaningless),
      rather than fitting it and only caveating it.
    * Drop any cyclic covariate whose observed phase support is too incomplete to
      identify its kernel (e.g. season seen over only part of the annual cycle);
      flag ``season_extrapolated`` specifically since it is the common case.
    """
    notes: Dict[str, str] = {}
    coverage: Dict[str, float] = {}
    selected: List[str] = []

    for cov in CYCLIC:
        if cov not in df.columns:
            continue
        values = df[cov].to_numpy(dtype=float)
        if not np.all(np.isfinite(values)):
            notes[cov] = "covariate unavailable (no finite phase, e.g. no tidal series)"
            continue
        if cov == "tide" and not report.get("tide_overlaps_acoustic", False):
            notes[cov] = "dropped: current series does not overlap acoustic detections"
            continue
        cov_fraction = phase_coverage(values, n_bins=12)
        coverage[cov] = cov_fraction
        if cov_fraction < MIN_PHASE_COVERAGE:
            notes[cov] = (
                f"dropped: phase coverage {cov_fraction:.2f} < {MIN_PHASE_COVERAGE:.2f} "
                f"(kernel would be extrapolated)"
            )
            if cov == "season":
                report["season_extrapolated"] = True
                report["season_phase_coverage"] = cov_fraction
            continue
        selected.append(cov)

    report["phase_coverage"] = coverage
    report.setdefault("season_extrapolated", "season" not in selected and "season" in coverage)
    return selected, notes


# Cross-station consistency scoring (Wave 1 agent C's recommendation).
XSTN_BAR = 0.5
# Coarser headline PSTH resolution than the old 24 bins, with a minimum per-bin
# count, so empty-bin -log floors stop dominating the correlation on sparse
# per-station data (agent C). The 8/12/24 sweep is reported alongside.
XSTN_HEADLINE_BINS = 12
XSTN_BIN_SWEEP = (8, 12, 24)
XSTN_MIN_BIN_COUNT = 1.0
XSTN_MIN_STATION_ROWS = 24
XSTN_SPLIT_HALF_REPS = 100


def _binned_log_rate(phase: np.ndarray, y: np.ndarray, exposure: np.ndarray, n_bins: int):
    """Effort-normalised binned log-rate curve + per-bin count (for masking)."""
    phase = np.asarray(phase, dtype=float) % 1.0
    y = np.asarray(y, dtype=float)
    exposure = np.asarray(exposure, dtype=float)
    idx = np.clip((phase * n_bins).astype(int), 0, n_bins - 1)
    counts = np.zeros(n_bins, dtype=float)
    expo = np.zeros(n_bins, dtype=float)
    np.add.at(counts, idx, y)
    np.add.at(expo, idx, exposure)
    rate = np.where(expo > 0, counts / np.maximum(expo, 1e-9), 0.0)
    return np.log(np.clip(rate, 1e-9, None)), counts


def _masked_corr(c1, n1, c2, n2, min_count: float):
    """Correlation over bins with >= ``min_count`` counts in BOTH stations."""
    mask = (n1 >= min_count) & (n2 >= min_count)
    if int(mask.sum()) < 3:
        return None
    a, b = c1[mask], c2[mask]
    if np.std(a) <= 1e-9 or np.std(b) <= 1e-9:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def _station_subframes(df: pd.DataFrame, stations):
    return {st: df[df["station"].astype(str) == st] for st in stations}


def _xstn_mean_corr(subs, cov: str, stations, n_bins: int, min_count: float):
    """Mean pairwise masked cross-station correlation for one covariate."""
    curves = {}
    for st in stations:
        sub = subs[st]
        if len(sub) < XSTN_MIN_STATION_ROWS:
            continue
        curves[st] = _binned_log_rate(
            sub[cov].to_numpy(dtype=float), sub["y"].to_numpy(dtype=float),
            sub["exposure"].to_numpy(dtype=float), n_bins,
        )
    keys = sorted(curves)
    corrs = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            c1, n1 = curves[keys[i]]
            c2, n2 = curves[keys[j]]
            c = _masked_corr(c1, n1, c2, n2, min_count)
            if c is not None:
                corrs.append(c)
    return (float(np.mean(corrs)) if corrs else None), len(curves)


def _xstn_split_half(sub, cov: str, n_bins: int, min_count: float, rng) -> Optional[float]:
    """Within-station split-half PSTH reliability: the reproducibility ceiling."""
    if len(sub) < 2 * XSTN_MIN_STATION_ROWS:
        return None
    phase = sub[cov].to_numpy(dtype=float)
    y = sub["y"].to_numpy(dtype=float)
    exposure = sub["exposure"].to_numpy(dtype=float)
    n = len(sub)
    reps = []
    for _ in range(XSTN_SPLIT_HALF_REPS):
        perm = rng.permutation(n)
        h1, h2 = perm[: n // 2], perm[n // 2:]
        c1, n1 = _binned_log_rate(phase[h1], y[h1], exposure[h1], n_bins)
        c2, n2 = _binned_log_rate(phase[h2], y[h2], exposure[h2], n_bins)
        c = _masked_corr(c1, n1, c2, n2, min_count)
        if c is not None:
            reps.append(c)
    return float(np.mean(reps)) if reps else None


def _xstn_onset_y(sub) -> np.ndarray:
    """Bin-level burst-dedup weights: 1.0 on the ONSET bin of each run of
    consecutive occupied bins (gap <= ``ENCOUNTER_GAP_HOURS``), else 0.0.

    Collapses bursty within-encounter hours to a single encounter onset so the
    cross-station and split-half PSTH reliability can be measured per independent
    ENCOUNTER rather than per bursty detection (synthesis U3; agents RD + RE:
    63-91% of detections fall within 6 min of the prior). This REDUCES the
    effective sample size, so it makes the consistency bar HARDER, not easier --
    it is an honesty correction reported ALONGSIDE the raw-count headline, never
    a way to inflate consistency. ``ENCOUNTER_GAP_HOURS`` is read at call time
    (it is defined later in the module).
    """
    t = sub["t"].to_numpy(dtype=float)
    y = sub["y"].to_numpy(dtype=float)
    order = np.argsort(t, kind="stable")
    occ = y[order] > 0
    w_sorted = np.zeros(order.shape[0], dtype=float)
    occ_pos = np.flatnonzero(occ)
    if occ_pos.size:
        occ_t = t[order][occ_pos]
        keep = np.concatenate(([True], np.diff(occ_t) > float(ENCOUNTER_GAP_HOURS)))
        w_sorted[occ_pos[keep]] = 1.0
    w = np.empty(w_sorted.shape[0], dtype=float)
    w[order] = w_sorted
    return w


def _xstn_classify(mean_corr, split_half, coverage_confound):
    if mean_corr is None:
        return "not_testable", "not testable (too few stations / bins)"
    # Honesty: a coverage confound (stations span different parts of the cycle)
    # undermines the cross-station comparison REGARDLESS of the raw correlation,
    # because the masked correlation is then computed over a shared sub-window
    # only, not the full kernel. Never report it as clean consistency.
    if coverage_confound:
        return ("coverage_confounded",
                "per-station phase coverage differs (stations span different parts of the cycle), so the "
                "cross-station correlation is over the shared window only -> observation-window confound, "
                "NOT demonstrated full-cycle consistency (mean corr=%s is not creditable)"
                % (None if mean_corr is None else round(mean_corr, 4)))
    if mean_corr >= XSTN_BAR:
        return "consistent", "consistent (clears the 0.5 bar with comparable per-station coverage)"
    if split_half is None:
        return "uncertain", "below bar; reliability ceiling unavailable (too few rows to split)"
    if split_half < XSTN_BAR:
        return ("noise_artifact",
                "below bar, but within-station split-half reliability is ALSO below 0.5: the PSTH is "
                "too noisy to reproduce within a single station -> sparse-count / small-sample artifact, "
                "not demonstrated heterogeneity")
    return ("reproducible_divergent",
            "below bar while within-station split-half clears it and coverage is comparable -> "
            "consistent with GENUINE station heterogeneity (model with a station random effect)")


def _cross_station_consistency(df: pd.DataFrame, covariates) -> Dict[str, object]:
    """L1 reproducibility: do per-station marginal PSTH shapes agree?

    Abstains (``testable=False``) with a single station, as required: there is no
    honest cross-station criterion to evaluate, and a single-station proxy would
    overstate reproducibility.

    Scoring follows Wave 1 agent C + W4 item 1 (RE/RB): a coarser headline PSTH
    resolution (12 bins) with a minimum per-bin count, the within-station
    split-half reliability reported as the CEILING (a cross-station correlation
    cannot exceed the noise floor of a station's own PSTH), a partial-pooling/
    shrinkage estimate with the explicit caveat that shrinking toward a shared
    target mechanically inflates the correlation, and a burst-dedup
    encounter-onset re-score per kernel (one onset per run of consecutive
    occupied bins) reported alongside as the harder, per-encounter honesty check
    (U3 -- it reduces effective N and so cannot inflate the bar). The 0.5 bar is
    NEVER forced: each kernel gets an honest verdict (consistent / noise_artifact
    / coverage-confounded / genuine heterogeneity), and ``consistent`` is true
    only if every testable kernel clears the bar with its own split-half ceiling
    also clearing it. This is a reproducibility-criterion fix; it does NOT by
    itself promote confidence.
    """
    stations = sorted(df["station"].astype(str).unique()) if "station" in df.columns else []
    if len(stations) < 2:
        return {"testable": False, "reason": "not testable with 1 station", "n_stations": len(stations)}

    subs = _station_subframes(df, stations)
    # Burst-deduped (encounter-onset) view of the same design: y replaced by the
    # bin-level onset weights so the SAME scorers can report reliability per
    # independent encounter alongside the raw-count headline (item 1 / U3).
    onset_subs = {st: subs[st].assign(y=_xstn_onset_y(subs[st])) for st in stations}
    rng = np.random.default_rng(7)
    per_cov: Dict[str, Optional[float]] = {}
    kernels: Dict[str, dict] = {}
    for cov in covariates:
        if cov not in df.columns:
            continue
        mean_corr, n_used = _xstn_mean_corr(subs, cov, stations, XSTN_HEADLINE_BINS, XSTN_MIN_BIN_COUNT)
        per_cov[cov] = mean_corr
        if mean_corr is None:
            kernels[cov] = {"testable": False, "reason": "< 2 stations with enough rows/bins"}
            continue

        bin_sweep = {}
        for nb in XSTN_BIN_SWEEP:
            mc, _ = _xstn_mean_corr(subs, cov, stations, nb, XSTN_MIN_BIN_COUNT)
            bin_sweep[str(nb)] = None if mc is None else round(mc, 4)

        split_vals = []
        per_station_split = {}
        per_station_cov = {}
        for st in stations:
            sub = subs[st]
            if len(sub) < XSTN_MIN_STATION_ROWS:
                continue
            sh = _xstn_split_half(sub, cov, XSTN_HEADLINE_BINS, XSTN_MIN_BIN_COUNT, rng)
            per_station_split[st] = None if sh is None else round(sh, 4)
            if sh is not None:
                split_vals.append(sh)
            per_station_cov[st] = round(phase_coverage(sub[cov].to_numpy(dtype=float), n_bins=12), 4)
        split_half_mean = float(np.mean(split_vals)) if split_vals else None

        cov_vals = list(per_station_cov.values())
        coverage_confound = bool(cov_vals) and (
            min(cov_vals) < 0.75 or (max(cov_vals) - min(cov_vals)) > 0.34
        )

        # Partial-pooling / shrinkage estimate (reported WITH the caveat that it
        # mechanically inflates correlation; not used to declare consistency).
        shrink = _xstn_shrinkage(subs, cov, stations, XSTN_HEADLINE_BINS)

        # Burst-dedup (encounter-onset) re-score: the same coarse-bin / masked
        # cross-station correlation + split-half ceiling, but counting one
        # encounter onset per run of consecutive occupied bins (U3). It is an
        # honesty check (smaller effective N -> harder), reported alongside.
        onset_corr, _ = _xstn_mean_corr(
            onset_subs, cov, stations, XSTN_HEADLINE_BINS, XSTN_MIN_BIN_COUNT
        )
        onset_split_vals = []
        onset_per_station = {}
        for st in stations:
            osub = onset_subs[st]
            if len(osub) < XSTN_MIN_STATION_ROWS:
                continue
            osh = _xstn_split_half(osub, cov, XSTN_HEADLINE_BINS, XSTN_MIN_BIN_COUNT, rng)
            onset_per_station[st] = None if osh is None else round(osh, 4)
            if osh is not None:
                onset_split_vals.append(osh)
        onset_split_mean = float(np.mean(onset_split_vals)) if onset_split_vals else None
        onset_counts = {st: int(onset_subs[st]["y"].sum()) for st in stations}

        code, label = _xstn_classify(mean_corr, split_half_mean, coverage_confound)
        kernels[cov] = {
            "testable": True,
            "n_stations": n_used,
            "mean_psth_correlation": round(mean_corr, 4),
            "headline_bins": XSTN_HEADLINE_BINS,
            "bin_count_sensitivity": bin_sweep,
            "split_half_reliability": {
                "per_station": per_station_split,
                "mean": None if split_half_mean is None else round(split_half_mean, 4),
            },
            "per_station_phase_coverage": per_station_cov,
            "coverage_confound": coverage_confound,
            "partial_pooling_shrinkage": shrink,
            "burst_dedup_onset": {
                "method": (
                    "bin-level burst-dedup: runs of consecutive occupied %g h bins collapsed to one "
                    "encounter onset; reliability measured per encounter, not per bursty hour (U3). "
                    "Reduces effective N -> makes the bar HARDER; honesty check alongside the headline."
                    % ENCOUNTER_GAP_HOURS
                ),
                "n_onsets_per_station": onset_counts,
                "mean_psth_correlation": None if onset_corr is None else round(onset_corr, 4),
                "split_half_reliability": {
                    "per_station": onset_per_station,
                    "mean": None if onset_split_mean is None else round(onset_split_mean, 4),
                },
            },
            "verdict_code": code,
            "verdict": label,
        }

    testable_kernels = {k: v for k, v in kernels.items() if v.get("testable")}
    consistent = bool(testable_kernels) and all(
        v.get("verdict_code") == "consistent" for v in testable_kernels.values()
    )
    noise = [k for k, v in testable_kernels.items() if v.get("verdict_code") == "noise_artifact"]
    coverage = [k for k, v in testable_kernels.items()
                if v.get("verdict_code") == "coverage_confounded"]
    hetero = [k for k, v in testable_kernels.items()
              if v.get("verdict_code") == "reproducible_divergent"]
    return {
        "testable": True,
        "n_stations": len(stations),
        "consistency_bar": XSTN_BAR,
        "scoring": (
            "coarser PSTH (%d bins, min per-bin count %g) with within-station split-half reliability "
            "as the ceiling, partial-pooling reported with its inflation caveat (agent C), and a "
            "burst-dedup encounter-onset re-score per kernel as the harder honesty check (U3)"
            % (XSTN_HEADLINE_BINS, XSTN_MIN_BIN_COUNT)
        ),
        "mean_psth_correlation": {k: (None if v is None else round(v, 4)) for k, v in per_cov.items()},
        "consistent": consistent,
        "noise_artifact_kernels": noise,
        "coverage_confounded_kernels": coverage,
        "genuine_heterogeneity_kernels": hetero,
        "kernels": kernels,
        "can_clear_0p5_bar_honestly": consistent,
    }


def _xstn_shrinkage(subs, cov: str, stations, n_bins: int) -> Dict[str, object]:
    """Empirical-Bayes shrinkage of station curves toward a count-weighted grand
    mean, then the cross-station correlation of the shrunken curves.

    CAVEAT (kept in the output): shrinking every station toward a SHARED target
    injects a common component that mechanically raises the pairwise correlation,
    so a large value here is an upper bound on what pooling could buy, NOT evidence
    the stations agree. Read it against the split-half ceiling.
    """
    curves = {}
    counts = {}
    for st in stations:
        sub = subs[st]
        if len(sub) < XSTN_MIN_STATION_ROWS:
            continue
        logr, cnt = _binned_log_rate(
            sub[cov].to_numpy(dtype=float), sub["y"].to_numpy(dtype=float),
            sub["exposure"].to_numpy(dtype=float), n_bins,
        )
        curves[st] = logr
        counts[st] = float(sub["y"].sum())
    keys = sorted(curves)
    if len(keys) < 2:
        return {"mean_corr": None, "note": "needs >= 2 stations", "caveat": "shrinkage inflates correlation"}
    n = np.array([max(counts.get(s, 0.0), 0.0) for s in keys])
    w_target = n / n.sum() if n.sum() > 0 else np.ones(len(keys)) / len(keys)
    grand = np.zeros_like(curves[keys[0]])
    for s, w in zip(keys, w_target):
        grand = grand + w * curves[s]
    k = float(np.median(n)) if n.size else 0.0
    shrunk = {}
    for s in keys:
        denom = counts.get(s, 0.0) + k
        w_s = counts.get(s, 0.0) / denom if denom > 0 else 0.0
        shrunk[s] = w_s * curves[s] + (1.0 - w_s) * grand
    corrs = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = shrunk[keys[i]], shrunk[keys[j]]
            if np.std(a) > 1e-9 and np.std(b) > 1e-9:
                corrs.append(float(np.corrcoef(a, b)[0, 1]))
    return {
        "mean_corr": round(float(np.mean(corrs)), 4) if corrs else None,
        "pooling_constant_k": round(k, 2),
        "caveat": "shrinkage toward a shared target mechanically inflates cross-station correlation; "
                  "not evidence of agreement, read against the split-half ceiling",
    }


def _held_out_pit(
    df: pd.DataFrame,
    covariates,
    family: str,
    n_blocks: int = 5,
    seed: int = 1,
    smoothness_lambda_grid: Optional[List[float]] = None,
    baseline_grid: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    """Pooled randomized-PIT KS-vs-uniform test on held-out time blocks.

    For each time block the model is fit on the other blocks and the PIT is
    computed on the held-out counts against that fold's predictive law (NB2 when
    ``family == 'negbin'``). Pooling across folds gives an out-of-sample
    calibration gate rather than the optimistic in-sample one.

    When ``smoothness_lambda_grid`` (TA5) or ``baseline_grid`` (TA2) is set, the
    per-fold model selects those hypers by nested ``block_cv`` inside that fold's
    training data, so the calibration verdict reflects the penalized predictive
    law.
    """
    from scipy import stats
    from .estimator import _select_smoothness_lambda, _select_baseline_hypers

    rng = np.random.default_rng(seed)
    times = df["t"].to_numpy(dtype=float)
    blocks = assign_time_blocks(times, n_blocks)
    work = df.assign(_block=blocks)
    pit_chunks: List[np.ndarray] = []
    for b in sorted(set(blocks.tolist())):
        test = work[work["_block"] == b]
        train = work[work["_block"] != b]
        if len(test) == 0 or len(train) == 0:
            continue
        try:
            lam = 0.0
            if smoothness_lambda_grid is not None:
                lam = _select_smoothness_lambda(
                    train, tuple(covariates), family, smoothness_lambda_grid,
                    n_harmonics=2, smoothness_order=SMOOTHNESS_ORDER,
                )
            extra = {}
            if baseline_grid is not None:
                tau, rl = _select_baseline_hypers(train, tuple(covariates), family, baseline_grid, n_harmonics=2)
                extra = dict(
                    use_station_effects="partial_pool" if tau > 0 else True,
                    pooling_tau=tau, ridge_lambda=rl,
                )
            m = fit_glm(
                train, covariates=tuple(covariates), n_harmonics=2, family=family,
                smoothness_lambda=lam, smoothness_order=SMOOTHNESS_ORDER, **extra,
            )
            mu = m.predict(test)
        except Exception:
            continue
        alpha = m.dispersion_alpha or 0.0
        pit_chunks.append(randomized_pit(test["y"].to_numpy(dtype=float), mu, rng=rng, alpha=alpha))

    if not pit_chunks:
        return {"held_out": True, "n": 0, "calibrated": False, "error": "no usable folds"}
    pit = np.concatenate(pit_chunks)
    ks = stats.kstest(pit, "uniform")
    return {
        "held_out": True,
        "family": family,
        "n": int(pit.size),
        "ks_stat": float(ks.statistic),
        "ks_pval": float(ks.pvalue),
        "calibrated": bool(ks.pvalue > 0.05),
    }


def _presence_reframe(
    df: pd.DataFrame, covariates, n_blocks: int = 5,
) -> Dict[str, object]:
    """TA2 cloglog presence COMPANION head (report-only; never the served count).

    Fits a complementary-log-log Binomial GLM on the bin-level presence indicator
    ``1[y>0]`` with the SAME Fourier design + ``log E`` offset, and scores it on
    held-out time blocks by Brier + log-loss SKILL vs a per-effort presence
    climatology (``p = 1 - exp(-rate * E)``). This is the well-posed presence
    question for an overdispersed bursty stream; it is reported alongside the
    count gates and is kept STRICTLY distinct from the NO-GO zero-inflated/hurdle
    COUNT upgrade (TA2 §2) -- it does not feed the served intensity or confidence.
    """
    import statsmodels.api as sm
    from .estimator import _build_features

    eps = 1e-9
    stations = sorted(df["station"].astype(str).unique()) if "station" in df.columns else []

    def design(d: pd.DataFrame, cols=None) -> pd.DataFrame:
        X = pd.DataFrame(index=d.index)
        X["const"] = 1.0
        for st in stations[1:]:
            X[f"st__{st}"] = (d["station"].astype(str) == st).astype(float)
        X = pd.concat([X, _build_features(d, covariates, 2)], axis=1)
        return X if cols is None else X.reindex(columns=cols, fill_value=0.0)

    times = df["t"].to_numpy(dtype=float)
    blocks = assign_time_blocks(times, n_blocks)
    work = df.assign(_block=blocks)

    def _logloss(y, p):
        p = np.clip(p, eps, 1 - eps)
        return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))

    def _brier(y, p):
        return float(np.mean((np.clip(p, eps, 1 - eps) - y) ** 2))

    ll_m: List[float] = []; ll_b: List[float] = []
    br_m: List[float] = []; br_b: List[float] = []
    n_folds = 0; folds_pos = 0
    for b in sorted(set(blocks.tolist())):
        test = work[work["_block"] == b]; train = work[work["_block"] != b]
        if len(test) == 0 or len(train) == 0:
            continue
        ytr = (train["y"].to_numpy(dtype=float) > 0).astype(float)
        yte = (test["y"].to_numpy(dtype=float) > 0).astype(float)
        if ytr.sum() == 0 or len(set(ytr.tolist())) < 2:
            continue
        off_tr = np.log(np.clip(train["exposure"].to_numpy(dtype=float), eps, None))
        off_te = np.log(np.clip(test["exposure"].to_numpy(dtype=float), eps, None))
        Xtr = design(train)
        Xte = design(test, cols=list(Xtr.columns))
        try:
            res = sm.GLM(
                ytr, Xtr,
                family=sm.families.Binomial(sm.families.links.CLogLog()),
                offset=off_tr,
            ).fit()
            p = np.asarray(res.predict(Xte, offset=off_te), dtype=float)
        except Exception:
            continue
        rate = max(ytr.sum() / max(np.exp(off_tr).sum(), eps), eps)
        p_base = 1.0 - np.exp(-rate * np.exp(off_te))
        lm, lb = _logloss(yte, p), _logloss(yte, p_base)
        bm, bb = _brier(yte, p), _brier(yte, p_base)
        ll_m.append(lm); ll_b.append(lb); br_m.append(bm); br_b.append(bb)
        n_folds += 1
        if lm < lb:
            folds_pos += 1

    if n_folds == 0:
        return {"head": "cloglog_presence", "testable": False,
                "reason": "no usable folds (presence indicator degenerate)"}
    logloss_skill = 1.0 - (float(np.mean(ll_m)) / max(float(np.mean(ll_b)), 1e-12))
    brier_skill = 1.0 - (float(np.mean(br_m)) / max(float(np.mean(br_b)), 1e-12))
    return {
        "head": "cloglog_presence",
        "testable": True,
        "scope": "held_out",
        "n_folds": n_folds,
        "folds_logloss_beats_climatology": f"{folds_pos}/{n_folds}",
        "logloss_skill_vs_climatology": round(logloss_skill, 4),
        "brier_skill_vs_climatology": round(brier_skill, 4),
        "note": "COMPANION presence head (1[y>0], cloglog, log E offset) scored vs a per-effort "
                "presence climatology; reported alongside the count gates, NOT the served intensity "
                "and NOT the NO-GO zero-inflated/hurdle count upgrade (TA2 §2). Does not affect confidence.",
    }


def _across_fold_lower_bound(per_fold: List[float], floor_reference: float = 0.078) -> Optional[float]:
    """One-sided 95% across-fold lower bound mean - t_{K-1,0.95} * SE (G2 §1B).

    ``floor_reference`` is unused in the arithmetic; it documents the G2 bar that
    this bound is compared against (>= +0.078 = the experiment level).
    """
    vals = [v for v in per_fold if isinstance(v, (int, float))]
    k = len(vals)
    if k < 2:
        return None
    from scipy import stats

    arr = np.asarray(vals, dtype=float)
    se = float(arr.std(ddof=1)) / math.sqrt(k)
    t = float(stats.t.ppf(0.95, k - 1))
    return float(arr.mean() - t * se)


def _smoothness_prior_report(
    enabled: bool,
    df: pd.DataFrame,
    covariates,
    selected_lambda_full: float,
    per_fold_selected_lambda: List[float],
    cv: Dict[str, object],
) -> Dict[str, object]:
    """Honest TA5 smoothness-prior block for the gate report.

    When OFF, records only ``enabled: False`` (the served default fit is
    byte-identical). When ON, records the lambda grid, the full-data selected
    lambda, the per-fold nested picks, the across-fold lower bound, and the
    hard ``n_harmonics=1`` control skill (TA5 §3: the gain must be graded
    shrinkage of the whole kernel shape, not merely a smaller harmonic count).
    """
    if not enabled:
        return {
            "enabled": False,
            "note": "TA5 smoothness prior OFF (default); served fit is byte-identical (B.4). "
                    "Opt in via run_fit(smoothness_prior=True) or ORCAST_SMOOTHNESS_PRIOR=1.",
        }
    per_fold_skill = [f.get("deviance_skill") for f in cv.get("folds", [])]
    # Hard n_harmonics=1 control (UNPENALIZED): the honesty contrast for the gain.
    try:
        control = block_cv(
            df,
            make_fit_predict(covariates=tuple(covariates), n_harmonics=1, family=PRIMARY_FAMILY),
            n_blocks=5,
        )
        control_skill = control.get("mean_deviance_skill")
        control_pass = f"{control.get('n_pass')}/{control.get('n_folds')}"
    except Exception:
        control_skill = None
        control_pass = None
    return {
        "enabled": True,
        "order": SMOOTHNESS_ORDER,
        "penalty": "ridge on Fourier coefs with weight lambda * h^(2*order) (const/station unpenalized)",
        "lambda_grid": list(SMOOTHNESS_LAMBDA_GRID),
        "selected_lambda_full_data": selected_lambda_full,
        "per_fold_selected_lambda": list(per_fold_selected_lambda),
        "selection": "nested block_cv inside each training fold (CV + PIT); "
                     "single nested selection on the full data for the served coefficients",
        "cv_mean_deviance_skill": cv.get("mean_deviance_skill"),
        "cv_per_fold_deviance_skill": per_fold_skill,
        "cv_folds_passing": f"{cv.get('n_pass')}/{cv.get('n_folds')}",
        "across_fold_lower_bound": _across_fold_lower_bound(per_fold_skill),
        "n_harmonics_1_control": {
            "mean_deviance_skill": control_skill,
            "folds_passing": control_pass,
            "note": "hard 1-harmonic drop (unpenalized); a much smaller gain here attributes the "
                    "prior's lift to GRADED shrinkage of the whole kernel shape, not fewer harmonics.",
        },
        "curve_disclosure": "penalized kernel curves are smoothness-regularized PREDICTIVE objects, "
                            "NOT unbiased PSTH shapes; serving may use them, publication as unbiased "
                            "tuning shapes must not (TA5 §4).",
    }


def _baseline_enablers_report(
    enabled: bool,
    df: pd.DataFrame,
    covariates,
    hypers_full: Dict[str, float],
    per_fold_hypers: List[dict],
    cv: Dict[str, object],
) -> Dict[str, object]:
    """Honest TA2 clean-baseline-enablers block for the gate report.

    When OFF, records only ``enabled: False`` (served fit byte-identical). When
    ON, records the full-data and per-fold (tau, ridge) selections, the held-out
    CV skill + per-fold spread (the fold-stability claim), and a fixed-effect
    contrast so the reviewer can see the worst-fold swing the partial pool cures.
    """
    if not enabled:
        return {
            "enabled": False,
            "note": "TA2 baseline enablers OFF (default); served fit is byte-identical (B.4). "
                    "Opt in via run_fit(baseline_enablers=True) or ORCAST_BASELINE_ENABLERS=1.",
        }
    per_fold_skill = [f.get("deviance_skill") for f in cv.get("folds", [])]
    # Fixed-effect contrast (unpenalized, reference coding): the fold-stability
    # baseline the partial pool is measured against.
    try:
        fe = block_cv(
            df,
            make_fit_predict(covariates=tuple(covariates), n_harmonics=2, family=PRIMARY_FAMILY,
                             use_station_effects=True),
            n_blocks=5,
        )
        fe_skill = fe.get("mean_deviance_skill")
        fe_per_fold = [f.get("deviance_skill") for f in fe.get("folds", [])]
        fe_min = min([v for v in fe_per_fold if isinstance(v, (int, float))], default=None)
    except Exception:
        fe_skill = fe_per_fold = fe_min = None
    pp_min = min([v for v in per_fold_skill if isinstance(v, (int, float))], default=None)
    return {
        "enabled": True,
        "method": "partial-pooling random station intercept (ridge 1/tau^2 on all-station deviations) "
                  "+ flat nested-CV ridge (1/s_k^2) on the kernel coefficients",
        "pooling_tau_grid": list(BASELINE_POOLING_TAU_GRID),
        "ridge_lambda_grid": list(BASELINE_RIDGE_LAMBDA_GRID),
        "selected_full_data": hypers_full,
        "per_fold_selected": list(per_fold_hypers),
        "cv_mean_deviance_skill": cv.get("mean_deviance_skill"),
        "cv_per_fold_deviance_skill": per_fold_skill,
        "cv_worst_fold": pp_min,
        "fixed_effect_contrast": {
            "cv_mean_deviance_skill": fe_skill,
            "cv_per_fold_deviance_skill": fe_per_fold,
            "cv_worst_fold": fe_min,
        },
        "interpretation": "ENABLER, not a lever -- does not promote. The partial pool shrinks "
                          "sparse/held-out stations to the population mean, removing the fixed-effect "
                          "reference-coding worst-fold swing; the ridge restores calibration. The point "
                          "is a fold-stable, calibrated baseline future covariates are judged against.",
    }


# Within-encounter detections (IEI <= this) are collapsed to a single
# encounter-onset event for the burst-dedup time-rescaling re-score (Wave 1
# agent B's recommended fix). 1.0 h == the bin resolution: the smooth hourly
# intensity cannot resolve sub-bin within-burst chatter, so it is scored at the
# encounter-onset / bin-count level instead.
ENCOUNTER_GAP_HOURS = 1.0


def _encounter_onsets(events: np.ndarray, gap_hours: float = ENCOUNTER_GAP_HOURS) -> np.ndarray:
    """Collapse within-burst detections to encounter onsets.

    Keeps the first detection of every run whose successive IEIs are all
    <= ``gap_hours`` (a refractory/encounter window), discarding the within-burst
    repeats that a smooth conditional intensity provably cannot reproduce.
    """
    ev = np.sort(np.asarray(events, dtype=float))
    if ev.size == 0:
        return ev
    keep = np.concatenate([[True], np.diff(ev) > float(gap_hours)])
    return ev[keep]


def _scaled_intensity(intensity, scale: float):
    """Return ``lambda(t) * scale`` (a per-station rate-level renormalisation)."""
    def scaled(t_hours):
        return np.asarray(intensity(t_hours), dtype=float) * float(scale)
    return scaled


def _raw_iei_cv(events: np.ndarray):
    """Coefficient of variation of the raw inter-event intervals (1.0 = Poisson)."""
    ev = np.sort(np.asarray(events, dtype=float))
    iei = np.diff(ev)
    iei = iei[iei > 0]
    if iei.size == 0:
        return None
    mean = float(iei.mean())
    return float(iei.std() / mean) if mean > 0 else None


def _pooled_ks_exp(pooled: List[float]):
    """(n, mean, ks_pval, pass, frac_under_0p05) for a pool of rescaled IEIs."""
    arr = np.asarray(pooled, dtype=float)
    arr = arr[arr > 0]
    if arr.size < 20:
        return {"n": int(arr.size), "ks_exp_pval": None, "pass_exp": None}
    from scipy import stats
    ks = stats.kstest(arr, "expon", args=(0, 1))
    return {
        "n": int(arr.size),
        "mean": float(arr.mean()),
        "ks_exp_pval": float(ks.pvalue),
        "pass_exp": bool(ks.pvalue > 0.05),
        "frac_under_0p05": float(np.mean(arr < 0.05)),
    }


def _fit_hawkes1(events: np.ndarray):
    """MLE of a single-exponential Hawkes conditional intensity (DIAGNOSTIC).

    ``lambda*(t) = mu + alpha*beta*sum_{t_i < t} exp(-beta (t - t_i))``. The
    branching ratio (expected offspring per event) of this kernel is exactly
    ``alpha``; ``alpha in (0, 1)`` keeps the process sub-critical. Fitted by
    L-BFGS-B with a multistart over ``beta`` (the Ogata O(n) recursion for the
    log-likelihood). This is used ONLY as the event-level GOF diagnostic that
    explains WHY a smooth conditional intensity cannot pass Exp(1) on this
    detector-chatter stream; it is never added to the served intensity.
    """
    from scipy.optimize import minimize

    ev = np.sort(np.asarray(events, dtype=float))
    if ev.size < 20:
        return None
    ev = ev - ev[0]
    T = float(ev[-1])
    dt = np.diff(ev)
    if T <= 0:
        return None

    def neg_ll(params):
        mu, alpha, beta = params
        if mu <= 0 or alpha <= 0 or alpha >= 1 or beta <= 0:
            return 1e12
        # Ogata recursion for A_k = sum_{i<k} exp(-beta (t_k - t_i)).
        a = 0.0
        log_sum = math.log(mu)  # first event: intensity = mu (A_0 = 0)
        for d in dt:
            a = math.exp(-beta * d) * (1.0 + a)
            lam = mu + alpha * beta * a
            if lam <= 0:
                return 1e12
            log_sum += math.log(lam)
        compensator = mu * T + alpha * float(np.sum(1.0 - np.exp(-beta * (T - ev))))
        return -(log_sum - compensator)

    n = ev.size
    mu0 = n / T if T > 0 else 1.0
    best = None
    for beta0 in (0.5, 1.0, 4.0, 12.0, 48.0):
        x0 = [max(mu0 * 0.5, 1e-6), 0.5, beta0]
        try:
            res = minimize(
                neg_ll, x0, method="L-BFGS-B",
                bounds=[(1e-9, None), (1e-6, 0.999), (1e-6, None)],
            )
        except Exception:  # noqa: BLE001
            continue
        if res.success or np.isfinite(res.fun):
            if best is None or res.fun < best.fun:
                best = res
    if best is None:
        return None
    mu, alpha, beta = (float(best.x[0]), float(best.x[1]), float(best.x[2]))
    return {"mu": mu, "branching_ratio": alpha, "beta": beta, "neg_ll": float(best.fun)}


def _hawkes1_rescaled(events: np.ndarray, mu: float, alpha: float, beta: float) -> np.ndarray:
    """Compensator increments tau_k between consecutive events under a fitted
    single-exponential Hawkes intensity (Exp(1) under a correct model).

    ``tau_k = mu*dt_k + alpha*(1 + S_{k-1})*(1 - exp(-beta*dt_k))`` where
    ``S_{k-1} = sum_{i <= k-1} exp(-beta (t_{k-1} - t_i)) = 1 + A_{k-1}`` is the
    excitation carried into the interval (Ogata recursion).
    """
    ev = np.sort(np.asarray(events, dtype=float))
    if ev.size < 2:
        return np.asarray([], dtype=float)
    dt = np.diff(ev)
    taus = np.empty(dt.shape[0], dtype=float)
    a = 0.0          # A_{k-1}: excitation from events strictly before t_{k-1}
    for k, d in enumerate(dt):
        s_prev = 1.0 + a  # include the event at t_{k-1} itself
        taus[k] = mu * d + alpha * s_prev * (1.0 - math.exp(-beta * d))
        a = math.exp(-beta * d) * (1.0 + a)
    return taus[taus > 0]


def _time_rescaling_report(model, acoustic, tide, bin_hours, uptime=None,
                           noise_by_station=None, ais_kappa: float = 0.0):
    """Time-rescaling GOF, event-level AND encounter-onset (burst-dedup) level.

    The acoustic detection stream is clustered (within-encounter chatter seconds
    apart), so a smooth Poisson/NB conditional intensity cannot pass an
    event-level Exp(1) KS regardless of the covariate list, effort, or grid
    (Wave 1 agent B: a constant-rate Poisson fails identically; ~82% of pooled
    rescaled IEIs sit at ~0). The honest re-score recommended there collapses
    within-burst detections to encounter onsets (>1 h apart) and tests THAT
    process, with the per-station rate level renormalised to the onset count so
    the test isolates encounter TIMING from the detection-count level the kernels
    were fit to. The verdict is recorded honestly: ``pass`` only if a legitimate
    scope clears p>0.05, else ``withheld`` with the clustering reason (B.3) -- the
    gate is never tuned to pass.
    """
    from .design import event_times_hours

    pooled: List[float] = []
    pooled_encounter: List[float] = []
    pooled_hawkes: List[float] = []
    hawkes_per_station = {}
    per_station = {}
    for station, records in acoustic.items():
        events = event_times_hours(records)
        if events.size < 20:
            continue
        lat = float(np.median([r["latitude"] for r in records if r.get("latitude") is not None] or [48.5]))
        lng = float(np.median([r["longitude"] for r in records if r.get("longitude") is not None] or [-123.0]))
        intensity = _station_intensity_fn(
            model, station, lat, lng, tide, uptime=uptime, detection_times=events,
            noise_by_station=noise_by_station, ais_kappa=ais_kappa,
        )
        res = run_time_rescaling(events, intensity=intensity, grid_step=bin_hours, min_ieis=20)
        if "rescaled_ieis" in res:
            pooled.extend(np.asarray(res["rescaled_ieis"]).tolist())

        # Encounter-onset (burst-dedup) re-score.
        onsets = _encounter_onsets(events, ENCOUNTER_GAP_HOURS)
        encounter = {"n_onsets": int(onsets.size), "encounter_gap_hours": ENCOUNTER_GAP_HOURS}
        if onsets.size >= 20:
            scale = onsets.size / float(events.size)  # level -> onset rate
            enc_intensity = _scaled_intensity(intensity, scale)
            enc_res = run_time_rescaling(onsets, intensity=enc_intensity, grid_step=bin_hours, min_ieis=20)
            if "rescaled_ieis" in enc_res:
                pooled_encounter.extend(np.asarray(enc_res["rescaled_ieis"]).tolist())
            encounter.update({
                "ks_exp_pval": enc_res.get("ks_exp_pval"),
                "pass_exp": enc_res.get("pass_exp"),
                "rescaled_iei_mean": enc_res.get("rescaled_iei_mean"),
                "n_rescaled_ieis": enc_res.get("n_rescaled_ieis"),
            })

        # Self-exciting (Hawkes) event-level GOF DIAGNOSTIC (item 3a / agent RD).
        # The textbook GOF for a clustered point process is time-rescaling with
        # the FULL conditional intensity (Brown et al. 2002); a self-exciting
        # intensity is that correct law. We fit it per station and pool the
        # compensator-rescaled IEIs, but keep the event-level Exp(1) verdict
        # WITHHELD: the branching ratio (0.79-0.96 on the dense stations) shows
        # 79-96% of detections are self-excited detector repeat-triggering on a
        # single encounter, so even the correct conditional intensity leaves
        # heavier-than-exponential residual structure. The Hawkes result is the
        # DIAGNOSTIC that explains why event-level Exp(1) is the wrong test here,
        # not a served covariate and not a gate.
        hawkes_fit = _fit_hawkes1(events)
        hawkes = {"fitted": bool(hawkes_fit is not None)}
        if hawkes_fit is not None:
            h_resc = _hawkes1_rescaled(
                events, hawkes_fit["mu"], hawkes_fit["branching_ratio"], hawkes_fit["beta"]
            )
            if h_resc.size:
                pooled_hawkes.extend(h_resc.tolist())
            h_ks = _pooled_ks_exp(h_resc.tolist())
            hawkes.update({
                "branching_ratio": round(hawkes_fit["branching_ratio"], 4),
                "beta_per_hour": round(hawkes_fit["beta"], 4),
                "mu_per_hour": hawkes_fit["mu"],
                "ks_exp_pval": h_ks.get("ks_exp_pval"),
                "pass_exp": h_ks.get("pass_exp"),
                "rescaled_iei_mean": h_ks.get("mean"),
                "frac_under_0p05": h_ks.get("frac_under_0p05"),
                "n_rescaled_ieis": h_ks.get("n"),
            })
        hawkes_per_station[station] = hawkes

        per_station[station] = {
            "pass_exp": res.get("pass_exp"),
            "ks_exp_pval": res.get("ks_exp_pval"),
            "n_rescaled_ieis": res.get("n_rescaled_ieis"),
            "raw_iei_cv": _raw_iei_cv(events),
            "encounter_onset": encounter,
            "self_exciting_hawkes": hawkes,
        }

    event_pool = _pooled_ks_exp(pooled)
    enc_pool = _pooled_ks_exp(pooled_encounter)
    hawkes_pool = _pooled_ks_exp(pooled_hawkes)

    out: Dict[str, object] = {
        "per_station": per_station,
        "pooled_n": event_pool.get("n"),
        "pooled_mean": event_pool.get("mean"),
        "pooled_ks_exp_pval": event_pool.get("ks_exp_pval"),
        "pooled_pass_exp": event_pool.get("pass_exp"),
        "pooled_frac_under_0p05": event_pool.get("frac_under_0p05"),
        "encounter_level": {
            "method": "burst-dedup to encounter onsets (IEI > %.2f h) + per-station level "
                      "renormalisation; isolates encounter timing from detection-count level" % ENCOUNTER_GAP_HOURS,
            "encounter_gap_hours": ENCOUNTER_GAP_HOURS,
            "pooled_n": enc_pool.get("n"),
            "pooled_mean": enc_pool.get("mean"),
            "pooled_ks_exp_pval": enc_pool.get("ks_exp_pval"),
            "pooled_pass_exp": enc_pool.get("pass_exp"),
            "pooled_frac_under_0p05": enc_pool.get("frac_under_0p05"),
        },
        # Self-exciting (Hawkes) event-level GOF DIAGNOSTIC (item 3a / agent RD).
        # Reported to explain WHY the event-level Exp(1) verdict is withheld: the
        # correct self-exciting law removes the near-zero IEI spike (pooled
        # frac<0.05 collapses, mean recenters to ~1.0) but still does not clear
        # Exp(1), because the residual within-encounter spacing is detector
        # repeat-triggering, not the animal signal. The branching ratios quantify
        # that self-excitation. This is a diagnostic only; it does NOT change the
        # served intensity, the timing verdict, or confidence.
        "self_exciting": {
            "method": "per-station single-exponential Hawkes MLE; compensator-rescaled IEIs pooled and "
                      "KS vs Exp(1). branching_ratio = expected self-excited offspring per event (alpha).",
            "per_station": {st: h for st, h in hawkes_per_station.items()},
            "branching_ratios": {
                st: h.get("branching_ratio") for st, h in hawkes_per_station.items() if h.get("fitted")
            },
            "pooled_n": hawkes_pool.get("n"),
            "pooled_mean": hawkes_pool.get("mean"),
            "pooled_ks_exp_pval": hawkes_pool.get("ks_exp_pval"),
            "pooled_pass_exp": hawkes_pool.get("pass_exp"),
            "pooled_frac_under_0p05": hawkes_pool.get("frac_under_0p05"),
            "diagnostic_only": True,
            "interpretation": (
                "event-level Exp(1) is inappropriate for a detector-chatter stream: a branching ratio "
                "near 1 means detections are dominated by self-excited repeat-triggering on a single "
                "encounter, so no smooth/self-exciting conditional intensity reproduces the within-"
                "encounter timing. The event-level verdict stays WITHHELD (B.3); bin-level GOF is the "
                "honest timing readout (see bin_count_gof)."
            ),
        },
    }

    # Honest verdict: pass only if a legitimate scope genuinely clears p>0.05;
    # otherwise withheld with the clustering reason (charter B.3) -- never tune.
    event_pass = bool(event_pool.get("pass_exp"))
    enc_pass = bool(enc_pool.get("pass_exp"))
    if event_pass:
        out["verdict"] = "pass"
        out["verdict_scope"] = "event_level"
    elif enc_pass:
        out["verdict"] = "pass"
        out["verdict_scope"] = "encounter_level"
        out["verdict_reason"] = (
            "event-level Exp(1) fails on the clustered detection stream, but the "
            "encounter-onset (burst-deduped) process clears the KS at the bin/encounter resolution."
        )
    else:
        out["verdict"] = "withheld"
        out["verdict_scope"] = "neither"
        out["verdict_reason"] = (
            "detection burstiness/clustering: a smooth conditional intensity cannot reproduce "
            "within-encounter inter-event intervals (event-level KS p=0; a constant-rate Poisson "
            "fails identically per Wave 1 diagnostic), and the burst-deduped encounter-onset process "
            "still does not clear Exp(1) on the current data. Time-rescaling is WITHHELD with the "
            "clustering reason rather than tuned to pass (B.3); bin-level calibration is gated "
            "separately by the held-out NB PIT."
        )
    return out


# --------------------------------------------------------------------------- #
# Bin-level timing gate (item 3b / agent RD) -- DEFINED but NOT ADOPTED.
#
# ADOPTING this gate is the one change in W4 that could let L2 earn timing
# credit on the current data, so it is GATED: it is a recorded SUPERVISOR
# decision (HANDOFF_CHARTER B.1), never a refit side effect. The flag below
# DEFAULTS OFF, so the served timing gate stays the event-level Exp(1)
# time-rescaling pass and ``effective_confidence`` is UNCHANGED (0.0). Do not
# flip this on outside a recorded supervisor decision via
# ``src/aws_backend/promotion/supervisor.py``.
#
# Honest framing for that decision (must be recorded as such, not as "time-
# rescaling passed"): event-level Exp(1) is INAPPROPRIATE for a detector-chatter
# stream -- the Hawkes branching ratio (0.79-0.96) shows the event-level timing
# is dominated by self-excited detector repeat-triggering, not the animal
# signal, so the GOF is scored at the SERVED target (per-bin counts) instead.
#
# LOAD-BEARING: the bin-level criterion is (held-out NB PIT calibrated) AND
# (held-out CV mean-deviance-skill > climatology). The NB PIT alone is
# near-automatic under NB's free dispersion (alpha absorbs the overdispersion),
# so it must be PAIRED with the non-automatic CV-skill gate; dropping the
# CV-skill pairing would make the gate near-automatic and over-credit the model.
#
# RECORDED SUPERVISOR DECISION (2026-06-27, operator "approved adoption"):
# the bin-level timing criterion is ADOPTED as the served timing gate, on the
# honest framing above (event-level Exp(1) is inappropriate for a detector-
# chatter stream; the GOF is scored at the served per-bin-count target). This
# is the recorded decision required by B.1. It does NOT by itself promote: the
# served single-station fit has CV mean-deviance-skill < 0, so the load-bearing
# CV-skill half FAILS and timing_gate stays False -> effective_confidence stays
# 0.0. The gate only earns credit once the served fit's held-out CV-skill is
# positive (the 4-station experiment is +0.078 but is NOT served until the
# deploy-gated 3-node production ingest lands). Promotion remains data-earned.
ADOPT_BIN_LEVEL_TIMING_GATE = True


def _bin_level_timing_gate(report: Dict[str, object]) -> bool:
    """The bin-level timing criterion (DEFINITION only; adoption is gated).

    Passes iff the held-out NB PIT is calibrated AND the held-out CV
    mean-deviance-skill beats climatology (> 0). Both are required: the PIT is
    near-automatic alone, the CV-skill pairing is the load-bearing, non-automatic
    half.
    """
    pit = report.get("pit", {}) if isinstance(report.get("pit"), dict) else {}
    cv = report.get("cv", {}) if isinstance(report.get("cv"), dict) else {}
    calibrated = bool(pit.get("calibrated"))
    skill = cv.get("mean_deviance_skill")
    skill_beats = isinstance(skill, (int, float)) and skill > 0
    return bool(calibrated and skill_beats)


def _bin_level_timing_readout(report: Dict[str, object]) -> Dict[str, object]:
    """Surface the bin-level timing GOF (RD): held-out NB PIT + CV skill, with
    the Poisson PIT as the overdispersion contrast. This is the bin-level gate
    DEFINITION; ``adopted`` reflects ``ADOPT_BIN_LEVEL_TIMING_GATE`` (True since
    the 2026-06-27 supervisor decision, B.1), under which the served timing gate
    accepts EITHER event-level Exp(1) OR this bin-level readout passing."""
    pit = report.get("pit", {}) if isinstance(report.get("pit"), dict) else {}
    pit_pois = report.get("pit_poisson", {}) if isinstance(report.get("pit_poisson"), dict) else {}
    cv = report.get("cv", {}) if isinstance(report.get("cv"), dict) else {}
    return {
        "definition": "bin-level timing gate = held-out NB PIT calibrated AND held-out CV "
                      "mean-deviance-skill > climatology (both required; CV-skill pairing is load-bearing).",
        "nb_pit_calibrated": pit.get("calibrated"),
        "nb_pit_ks_pval": pit.get("ks_pval"),
        "poisson_pit_calibrated": pit_pois.get("calibrated"),
        "poisson_pit_ks_pval": pit_pois.get("ks_pval"),
        "cv_mean_deviance_skill": cv.get("mean_deviance_skill"),
        "cv_beats_climatology": isinstance(cv.get("mean_deviance_skill"), (int, float))
                                and cv.get("mean_deviance_skill") > 0,
        "bin_level_verdict": "pass" if _bin_level_timing_gate(report) else "fail",
        "adopted": ADOPT_BIN_LEVEL_TIMING_GATE,
        "note": "Adoption is a recorded supervisor decision (B.1). ADOPT_BIN_LEVEL_TIMING_GATE is "
                "True (2026-06-27), so the served timing gate passes on EITHER event-level Exp(1) OR "
                "this bin-level NB-PIT readout; confidence still requires the other gates (CV skill, "
                "calibration) and a supervisor decision. Event-level Exp(1) alone is inappropriate for "
                "a detector-chatter stream (see time_rescaling.self_exciting branching ratios).",
    }


# --- Graduated confidence mapping constants (evidence-scaled, more conservative) ---
# Rationale: with ADOPT_BIN_LEVEL_TIMING_GATE = True the previous flat
# 0.25-per-quarter sum became a step function -- a single served fit whose
# held-out CV mean-deviance-skill ticked positive fired all four quarters at
# once and slammed confidence to 1.0 (verified: cv skill +0.078 -> 1.0). That is
# a binary cliff, not earned evidence. The mapping below keeps every gate
# pass/fail definition and the hard floor unchanged, but makes the dominant
# CV/timing contribution a bounded, saturating function of the held-out CV
# mean-deviance-skill MAGNITUDE, with PIT-calibration and Level-1 retained as
# smaller boolean modifiers (PIT still gated on the timing gate, as before), and
# the served confidence hard-capped strictly below 1.0.
_CONF_SKILL_TAU = 0.12      # CV mean-deviance-skill scale: skill ~ TAU earns ~63% of the evidence cap.
_CONF_EVIDENCE_CAP = 0.50   # Max contribution of the joint CV/timing evidence block.
_CONF_PIT_BONUS = 0.15      # Calibration modifier, awarded only when the timing gate passes.
_CONF_LEVEL1_BONUS = 0.10   # Marginal-PSTH (Level-1) modifier.
_CONF_CAP = 0.75            # Hard ceiling on served confidence (strictly < 1.0).


def _confidence_from_gates(report: Dict[str, object]) -> float:
    """Confidence from passed gates, graduated by held-out effect size.

    Joint-gate requirement (unchanged). The marginal-PSTH null (Level 1) and the
    PSTH-vs-kernel diagnostic describe single covariates, not the joint forecast,
    so they cannot by themselves earn confidence. We require at least one joint
    gate -- held-out CV skill OR the time-rescaling GOF -- before awarding
    anything; otherwise confidence is 0. The PSTH-vs-kernel consistency is a
    diagnostic and never contributes.

    Timing gate (item 3b / RD, unchanged). The served timing gate is the
    event-level Exp(1) time-rescaling pass OR -- once
    ``ADOPT_BIN_LEVEL_TIMING_GATE`` is True (a recorded supervisor decision, B.1)
    -- the bin-level criterion (NB PIT calibrated AND held-out CV skill >
    climatology). This function does NOT alter which gates pass or fail.

    Graduated mapping (NEW -- more conservative, evidence-scaled). The previous
    code summed four independent flat 0.25 quarters, so the first served fit with
    any positive held-out skill jumped straight to 1.0. That is a step function,
    not earned evidence. Instead:

      s          = max(cv_mean_deviance_skill, 0)          # held-out effect size
      skill_sat  = 1 - exp(-s / TAU)                       # saturating in [0, 1)
      gate_factor= 0.5*cv_pass + 0.5*timing_gate           # {0.5, 1.0} past the floor
      evidence   = EVIDENCE_CAP * gate_factor * skill_sat  # bounded, increasing in s
      pit        = PIT_BONUS    if (timing_gate and pit.calibrated) else 0
      level1     = LEVEL1_BONUS if any Level-1 kernel beats its null else 0
      confidence = min(CONF_CAP, evidence + pit + level1)

    Properties / assumptions:
      * Hard floor preserved exactly: no joint gate -> 0.0.
      * The dominant term scales with the held-out CV-skill magnitude through a
        saturating map, so a marginal +0.0x skill earns only a modest confidence
        and a large, robust skill approaches the evidence cap -- no cliff.
      * Reaching the full evidence cap requires BOTH joint gates (gate_factor=1);
        a lone passing gate is trusted only half as far.
      * PIT and Level-1 stay as bounded boolean modifiers, gated exactly as
        before (PIT only when the timing gate passes).
      * Served confidence is hard-capped at CONF_CAP (< 1.0): a limited-coverage
        temporal model that has not cleared event-level timing GOF (Hawkes
        self-excitation dominates the event stream) must not express full
        certainty; the cap is only approached as skill grows large and stable.
      * Monotonic and deterministic: confidence is non-decreasing in CV skill and
        depends only on the report's recorded numbers.

    Calibration of TAU. The supervisor promotion threshold is 0.6
    (_PROMOTE_CONFIDENCE). With both gates, a calibrated PIT, and a beaten
    Level-1 null, confidence crosses 0.6 only at CV skill ~= +0.144 -- roughly
    double the +0.078 multi-station experiment margin -- so crossing 0.6 means a
    robust positive skill, not a single lucky fold. The current served
    single-station fit (CV skill -0.047) stays at 0.0.
    """
    cv = report.get("cv", {})
    cv_skill = cv.get("mean_deviance_skill") if isinstance(cv, dict) else None
    cv_pass = bool(cv.get("gate_pass")) if isinstance(cv, dict) else False
    if isinstance(cv_skill, (int, float)) and cv_skill <= 0:
        cv_pass = False
    tr_pass = bool(report.get("time_rescaling", {}).get("pooled_pass_exp"))
    # The served timing gate is event-level Exp(1) ONLY. The bin-level criterion
    # is wired in but switched OFF by default (adoption is a supervisor decision,
    # B.1), so with the flag OFF timing_gate == tr_pass and nothing changes.
    timing_gate = tr_pass or (ADOPT_BIN_LEVEL_TIMING_GATE and _bin_level_timing_gate(report))
    if not (cv_pass or timing_gate):
        return 0.0

    # Held-out effect size drives the dominant CV/timing evidence term through a
    # saturating map. Only positive skill contributes magnitude; the floor above
    # already guarantees a joint gate holds.
    s = float(cv_skill) if isinstance(cv_skill, (int, float)) and cv_skill > 0 else 0.0
    skill_sat = 1.0 - math.exp(-s / _CONF_SKILL_TAU)
    gate_factor = 0.5 * float(cv_pass) + 0.5 * float(timing_gate)
    score = _CONF_EVIDENCE_CAP * gate_factor * skill_sat

    # Calibration (PIT uniformity) only counts when the conditional intensity's
    # event TIMING is not rejected. NB's free dispersion makes PIT-uniformity
    # near-automatic, so crediting PIT while the timing gate fails would
    # over-credit a model whose timing is demonstrably wrong. Gate PIT on the
    # timing gate (event-level today; bin-level only on an adopted supervisor
    # decision -- and even then paired with the non-automatic CV-skill gate).
    if timing_gate and report.get("pit", {}).get("calibrated"):
        score += _CONF_PIT_BONUS
    level1 = report.get("level1_psth", {})
    if any(v.get("beats_null") for v in level1.values()):
        score += _CONF_LEVEL1_BONUS
    return round(min(_CONF_CAP, score), 2)


def _write_fit_plan(plan: Dict[str, object]) -> None:
    FIT_PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIT_PLAN_PATH.write_text(json.dumps(plan, indent=2, default=str))


def _write_snapshot_manifest(manifest: Dict[str, object], versioned: bool = False) -> None:
    SNAPSHOT_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, default=str))
    snap_id = manifest.get("snap_id")
    if versioned and snap_id:
        versioned_path = SNAPSHOT_MANIFEST_PATH.parent / "snapshots" / str(snap_id) / "manifest.json"
        versioned_path.parent.mkdir(parents=True, exist_ok=True)
        versioned_path.write_text(json.dumps(manifest, indent=2, default=str))


def _write_level0_artifact(report: Dict[str, object]) -> None:
    """Standalone Level 0 detector QC artifact alongside fit_report."""
    qc = report.get("level0_detector_qc")
    if not isinstance(qc, dict):
        return
    path = REPORT_JSON_PATH.parent / "level0_detector_qc.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = {
        "schema_version": "orcast/level0_detector_qc/v1",
        "generated_at": report.get("generated_at"),
        "dataset_snapshot_id": report.get("dataset_snapshot_id"),
        "level0_detector_qc": qc,
    }
    path.write_text(json.dumps(body, indent=2, default=str))
    run_id = report.get("run_id")
    if run_id:
        run_dir = REPORT_JSON_PATH.parent / "runs" / str(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "level0_detector_qc.json").write_text(json.dumps(body, indent=2, default=str))


def _write_report_json(report: Dict[str, object]) -> None:
    """Machine-readable gate report served by the /api/gates endpoint."""
    REPORT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(report, indent=2, default=str)
    REPORT_JSON_PATH.write_text(body)
    run_id = report.get("run_id")
    if run_id:
        run_dir = REPORT_JSON_PATH.parent / "runs" / str(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "fit_report.json").write_text(body)
    _write_level0_artifact(report)


def _maybe_write_s3() -> None:
    """In aws mode, upload the fitted coefficients + gate report to the models bucket.

    The serving module reads these S3 objects in production
    (``src/aws_backend/kernel_model/serve.py``).
    """
    if settings.storage_backend.lower() != "aws":
        return
    try:
        import boto3
        from src.aws_backend.kernel_model.serve import COEFFICIENTS_S3_KEY, FIT_REPORT_S3_KEY

        s3 = boto3.client("s3", region_name=settings.aws_region)
        bucket = settings.models_bucket
        extra: List[tuple[Path, str]] = []
        report = json.loads(REPORT_JSON_PATH.read_text()) if REPORT_JSON_PATH.exists() else {}
        fit_plan_id = report.get("fit_plan_id")
        snap_id = report.get("dataset_snapshot_id")
        repr_id = report.get("repr_id")
        run_id = report.get("run_id")
        if fit_plan_id:
            extra.append((FIT_PLAN_PATH, f"fit_plans/{fit_plan_id}/fit_plan.json"))
        if snap_id:
            extra.append((SNAPSHOT_MANIFEST_PATH, f"snapshots/{snap_id}/manifest.json"))
        if repr_id:
            repr_dir = COEFF_PATH.parent / "representations" / str(repr_id)
            extra.extend([
                (repr_dir / "fitted_kernels.json", f"representations/{repr_id}/fitted_kernels.json"),
                (repr_dir / "representation.json", f"representations/{repr_id}/representation.json"),
            ])
        if run_id:
            run_dir = COEFF_PATH.parent / "runs" / str(run_id)
            extra.extend([
                (run_dir / "fit_report.json", f"runs/{run_id}/fit_report.json"),
                (run_dir / "manifest.json", f"runs/{run_id}/manifest.json"),
            ])
        extra.append((CURRENT_POINTER_PATH, "models/current.json"))
        for path, key in (
            (COEFF_PATH, COEFFICIENTS_S3_KEY),
            (REPORT_JSON_PATH, FIT_REPORT_S3_KEY),
            *extra,
        ):
            if path.exists():
                s3.put_object(
                    Bucket=bucket, Key=key,
                    Body=path.read_bytes(), ContentType="application/json",
                )
    except Exception as exc:  # never let upload failure mask a successful fit
        print(f"[fit_kernels] S3 artifact upload skipped: {exc}")


def _fitted_payload(
    model: FittedModel,
    confidence: float,
    report: Dict[str, object],
    bin_hours: float,
) -> Dict[str, Any]:
    payload = model.to_fitted_dict(confidence=confidence)
    payload["fitted_at"] = datetime.now(timezone.utc).isoformat()
    payload["bin_hours"] = float(bin_hours)
    payload["version"] = report.get("repr_id") or payload.get("version")
    # Disclosure fields the serving layer can surface alongside the forecast.
    payload["acoustic_span"] = report.get("acoustic_span")
    payload["detections_unreviewed_candidates"] = bool(
        report.get("detections_unreviewed_candidates", True)
    )
    payload["season_extrapolated"] = bool(report.get("season_extrapolated", False))
    payload["covariates_excluded"] = report.get("covariates_excluded", {})
    # TA5: a penalized fit's kernel curves are smoothness-regularized predictive
    # objects, not unbiased PSTH shapes -- surface that to serving (B.1 honesty).
    payload["smoothness_regularized"] = bool(getattr(model, "penalized", False))
    payload["smoothness_lambda"] = float(getattr(model, "smoothness_lambda", 0.0))
    payload["repr_id"] = report.get("repr_id")
    payload["run_id"] = report.get("run_id")
    payload["dataset_snapshot_id"] = report.get("dataset_snapshot_id")
    return payload


def _write_coefficients(
    coeff_payload: Dict[str, Any],
    representation: Dict[str, Any],
    run_manifest: Dict[str, Any],
    report: Dict[str, object],
) -> None:
    COEFF_PATH.parent.mkdir(parents=True, exist_ok=True)
    COEFF_PATH.write_text(json.dumps(coeff_payload, indent=2))
    repr_id = str(report["repr_id"])
    run_id = str(report["run_id"])
    repr_dir = COEFF_PATH.parent / "representations" / repr_id
    run_dir = COEFF_PATH.parent / "runs" / run_id
    repr_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    (repr_dir / "fitted_kernels.json").write_text(json.dumps(coeff_payload, indent=2, default=str))
    (repr_dir / "representation.json").write_text(json.dumps(representation, indent=2, default=str))
    (run_dir / "manifest.json").write_text(json.dumps(run_manifest, indent=2, default=str))
    CURRENT_POINTER_PATH.write_text(json.dumps({
        "repr_id": repr_id,
        "run_id": run_id,
        "fitted_kernels": f"representations/{repr_id}/fitted_kernels.json",
        "fit_report": f"runs/{run_id}/fit_report.json",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2))


def _write_figures(model: FittedModel, report: Dict[str, object]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    curves = model.kernel_curves()
    for name, c in curves.items():
        fig, ax = plt.subplots(figsize=(6, 4))
        phase = np.array(c["phase"])
        ax.plot(phase, c["value"], color="C0", lw=2, label=f"k_{name}")
        if "ci_lo" in c:
            ax.fill_between(phase, c["ci_lo"], c["ci_hi"], color="C0", alpha=0.2, label="95% CI")
        ax.axhline(0.0, color="0.6", lw=0.8, ls="--")
        ax.set_xlabel(f"{name} phase (0-1)")
        ax.set_ylabel("log-rate contribution")
        ax.set_title(f"Fitted kernel: {name}")
        ax.legend()
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        fig.savefig(FIG_DIR / f"{name}_kernel.png", dpi=150, bbox_inches="tight")
        plt.close(fig)


def _fmt(value, nd=3):
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.{nd}f}"
    return str(value)


def _write_report(report: Dict[str, object]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    lines.append("# Kernel fit status")
    lines.append("")
    lines.append("Auto-generated by `modeling/fit_kernels.py`. Each gate is reported honestly,")
    lines.append("including when there is not yet enough data to fit. See")
    lines.append("[CALIBRATION_STUDIES.md](CALIBRATION_STUDIES.md) for the leveled plan and")
    lines.append("[INDYSIM_AUDIT.md](INDYSIM_AUDIT.md) for the ported methods.")
    lines.append("")
    lines.append(f"- Generated: {report.get('generated_at')}")
    lines.append(f"- Storage backend: `{report.get('storage_backend')}`")
    lines.append(f"- Status: **{report.get('status')}**")
    lines.append("")

    lines.append("## Data inventory")
    lines.append("")
    lines.append(f"- Acoustic stations: {report.get('n_stations_acoustic')}")
    lines.append(f"- Acoustic detections: {report.get('n_detections')}")
    lines.append(f"- Uptime stations: {report.get('n_stations_uptime')}")
    lines.append(f"- Current/water-level records: {report.get('n_current_records')}")
    lines.append(f"- Tidal flood onsets detected: {report.get('tide_onsets_detected')}")
    acs = report.get("acoustic_span")
    crs = report.get("currents_span")
    if acs:
        lines.append(f"- Acoustic coverage: {acs[0]} -> {acs[1]}")
    if crs:
        lines.append(f"- Current coverage: {crs[0]} -> {crs[1]}")
    if acs and crs and not report.get("tide_overlaps_acoustic", False):
        lines.append("")
        lines.append("> The current series does not overlap the acoustic detections in time, so")
        lines.append("> the tidal phase aligned to these detections is not meaningful. The tide")
        lines.append("> covariate is therefore EXCLUDED from the fit and from serving (not merely")
        lines.append("> caveated) until overlapping current data is wired.")
    lines.append("")
    lines.append("> Detections are UNREVIEWED model candidates (OrcaHello/Orcasound), not")
    lines.append("> human-confirmed events; the fit and forecast inherit that caveat.")
    if "n_bins" in report:
        lines.append("")
        lines.append(f"- Station-bins after binning: {report.get('n_bins')}")
        lines.append(f"- Effort assumed continuous (no uptime): {_fmt(report.get('effort_assumed_continuous'))}")
    lines.append("")

    if report.get("status") == "insufficient_data":
        lines.append("## Result")
        lines.append("")
        lines.append(f"Not fitted: {report.get('reason')}.")
        lines.append("")
        lines.append("The pipeline is validated on synthetic data (`modeling/tests/`); it will")
        lines.append("produce kernels and gate results as soon as enough real history is wired.")
        REPORT_PATH.write_text("\n".join(lines) + "\n")
        return

    lines.append(f"## Confidence: {report.get('confidence')}")
    lines.append("")
    lines.append("Confidence is awarded only once a JOINT-model gate holds (held-out CV skill")
    lines.append("OR the time-rescaling GOF); the marginal-PSTH null and the PSTH-vs-kernel")
    lines.append("diagnostic cannot earn confidence on their own. It drives how sharply the")
    lines.append("forecast renders, not whether it is shown.")
    lines.append("")

    excluded = report.get("covariates_excluded", {})
    if excluded:
        lines.append("### Covariates excluded from the fit")
        lines.append("")
        for cov, why in excluded.items():
            lines.append(f"- `{cov}`: {why}")
        lines.append("")
    if report.get("season_extrapolated"):
        cov_frac = report.get("season_phase_coverage")
        frac_txt = f" (phase coverage {cov_frac:.2f})" if isinstance(cov_frac, (int, float)) else ""
        lines.append(f"> Season is EXTRAPOLATED{frac_txt}: the data span only part of the annual")
        lines.append("> cycle, so the season kernel is excluded from the fit and confidence.")
        lines.append("")

    lines.append("## Level 1: PSTH vs phase-shuffle null")
    lines.append("")
    lines.append("| Covariate | Modulation | Null z | Null p | Beats null |")
    lines.append("|---|---|---|---|---|")
    for cov, v in report.get("level1_psth", {}).items():
        lines.append(f"| {cov} | {_fmt(v['modulation'])} | {_fmt(v['null_z'],2)} | {_fmt(v['null_p'])} | {_fmt(v['beats_null'])} |")
    lines.append("")
    xstn = report.get("level1_cross_station", {})
    if xstn:
        if not xstn.get("testable", False):
            lines.append(f"- Cross-station consistency: not testable ({xstn.get('reason')}).")
        else:
            lines.append(f"- Cross-station consistency: {_fmt(xstn.get('consistent'))} "
                         f"across {xstn.get('n_stations')} stations.")
        lines.append("")

    fam = report.get("family", "poisson")
    fam_label = "negative binomial (NB2)" if fam == "negbin" else "Poisson"
    lines.append(f"## Level 2: joint GLM -- {fam_label}")
    lines.append("")
    m = report.get("metrics", {})
    lines.append(f"- Family: {fam_label}")
    if report.get("dispersion_alpha") is not None:
        lines.append(f"- NB dispersion alpha (Var = mu + alpha*mu^2): {_fmt(report.get('dispersion_alpha'))}")
    lines.append(f"- Covariates fit: {', '.join(report.get('covariates_fit', []))}")
    lines.append(f"- Intercept (log-rate, reference station): {_fmt(report.get('intercept'))}")
    lines.append(f"- McFadden pseudo-R^2 vs climatology: {_fmt(m.get('mcfadden_r2'))}")
    lines.append(f"- Deviance: {_fmt(m.get('deviance'),1)}; AIC: {_fmt(m.get('aic'),1)}")
    lines.append("")

    ov = report.get("overdispersion", {})
    if ov:
        lines.append("### Overdispersion (why NB is primary)")
        lines.append("")
        lines.append(f"- Poisson Pearson dispersion phi: {_fmt(ov.get('poisson_pearson_dispersion'))} "
                     f"(>> 1 means overdispersed)")
        lines.append(f"- NB dispersion alpha: {_fmt(ov.get('nb_dispersion_alpha'))}")
        lines.append(f"- Held-out PIT calibrated -- Poisson: {_fmt(ov.get('poisson_pit_calibrated'))}; "
                     f"NB: {_fmt(ov.get('nb_pit_calibrated'))}")
        lines.append("")

    cv = report.get("cv", {})
    lines.append("### Held-out time-blocked CV")
    lines.append("")
    lines.append(f"- Folds passing (model beats climatology): {cv.get('n_pass')}/{cv.get('n_folds')}")
    lines.append(f"- Mean deviance skill: {_fmt(cv.get('mean_deviance_skill'))}")
    lines.append(f"- Gate pass: {_fmt(cv.get('gate_pass'))}")
    nt = cv.get("null_test", {})
    if nt:
        lines.append(f"- Binomial null p: {_fmt(nt.get('p_value'))} ({nt.get('interpretation')})")
    lines.append("")

    tr = report.get("time_rescaling", {})
    scope = "in-sample" if tr.get("in_sample") else "held-out"
    lines.append(f"### Time-rescaling goodness-of-fit (Brown 2002) -- {scope}")
    lines.append("")
    lines.append(f"- Pooled rescaled IEIs: {tr.get('pooled_n')}")
    if tr.get("pooled_pass_exp") is not None:
        lines.append(f"- Pooled mean (expect 1.0): {_fmt(tr.get('pooled_mean'))}")
        lines.append(f"- Pooled KS vs Exp(1) p: {_fmt(tr.get('pooled_ks_exp_pval'))}")
        lines.append(f"- Pass: {_fmt(tr.get('pooled_pass_exp'))}")
    else:
        lines.append("- Not enough rescaled IEIs to test.")
    lines.append("")

    pit = report.get("pit", {})
    pit_p = report.get("pit_poisson", {})
    scope = "held-out" if pit.get("held_out") else "in-sample"
    lines.append(f"### PIT calibration -- {scope}")
    lines.append("")
    lines.append(f"- {report.get('family', 'poisson')} (primary): KS vs Uniform p "
                 f"{_fmt(pit.get('ks_pval'))}; calibrated: {_fmt(pit.get('calibrated'))}")
    if pit_p:
        lines.append(f"- poisson (comparison): KS vs Uniform p {_fmt(pit_p.get('ks_pval'))}; "
                     f"calibrated: {_fmt(pit_p.get('calibrated'))}")
    lines.append("")

    lines.append("### PSTH vs joint-kernel consistency (DIAGNOSTIC, not a gate)")
    lines.append("")
    lines.append("A correctly de-confounded joint kernel can legitimately diverge from the")
    lines.append("marginal PSTH under correlated covariates, so this does not gate confidence.")
    lines.append("")
    lines.append("| Covariate | Correlation | Agrees |")
    lines.append("|---|---|---|")
    for cov, v in report.get("psth_vs_kernel_diagnostic", {}).items():
        lines.append(f"| {cov} | {_fmt(v.get('correlation'))} | {_fmt(v.get('agrees'))} |")
    lines.append("")

    lines.append("## Artifacts")
    lines.append("")
    lines.append("- Coefficients: `data/models/fitted_kernels.json` (loaded by")
    lines.append("  `src/aws_backend/kernel_model/serve.py`).")
    lines.append("- Kernel-curve figures: `docs/methodology/figures/kernels/`.")
    lines.append("")

    REPORT_PATH.write_text("\n".join(lines) + "\n")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Fit orcast forecast kernels offline.")
    parser.add_argument("--bin-hours", type=float, default=1.0)
    parser.add_argument("--no-figures", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)

    store = build_timeseries_store(settings)
    report = run_fit(
        store, bin_hours=args.bin_hours,
        write_outputs=not args.no_write, make_figures=not args.no_figures,
    )
    print(json.dumps({k: v for k, v in report.items()
                      if k not in ("station_effects",)}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
