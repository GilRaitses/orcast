"""M-L2 time-rescaling diagnostic (Wave 1, agent B): WHY is pooled KS p=0?

The multi-station experiment (`level2_multistation.py`) flips held-out skill
positive (+0.078, 4/5 folds) but Level 2 still FAILS because the pooled
time-rescaling KS vs Exp(1) is p=0.0. This study isolates the cause WITHOUT
editing the convergence files. It reads, but never edits:

* `modeling/validation/time_rescaling.py` (`run_time_rescaling`, `time_rescaling_test`),
* `modeling/fit_kernels.py` (`_station_intensity_fn`, `_time_rescaling_report`,
  `_select_covariates`, `read_streams`, `PRIMARY_FAMILY`),
* `modeling/studies/level2_multistation.py` (the memory-store recipe is mirrored,
  not imported-and-mutated).

It reconstructs the same 4-station memory store the experiment uses (production
`haro_strait` acoustic_detections from S3 + cached OrcaHello index for the other
three in-region nodes + S3 env_currents/station_uptime), fits the identical NB2
joint GLM, then runs five diagnostic probes:

  A. Reproduce the per-station + pooled KS exactly as `_time_rescaling_report`.
  B. Per-station vs pooled (leave-one-out pooled KS; raw-IEI burstiness stats).
  C. Effort sensitivity:
       c1 constant-rescale each station's intensity to mean rescaled IEI == 1
          (does fixing only the LEVEL pass? isolates level vs shape),
       c2 uptime-gated intensity (integrate the cumulative hazard only over
          station-ON time, using the S3 station_uptime carry-forward step;
          flat-effort fallback where uptime is absent -- stated per station).
  D. Grid/bin resolution sweep (`grid_step` in 0.05..1.0h).
  E. Conditional-intensity construction: compare the fitted-kernel intensity to a
     homogeneous-Poisson constant-rate intensity (same events). If the constant
     rate fails the SAME way, the kernels are not the cause -- the point-process
     clustering is.

Honesty (charter B.1-B.3): this reports measured KS p-values. If the data cannot
support a passing time-rescaling GOF honestly, it says so and names the most
likely single fix for the Wave 2 integrator; it does not tune the gate.

Run (charter B.4/B.5; upload disabled, write_outputs unused -- no fit artifact
is written, no production store is touched):

    ORCAST_STORAGE_BACKEND=aws \
    ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads \
    AWS_REGION=us-west-2 PYTHONPATH=. \
    .venv-modeling/bin/python -m modeling.studies.time_rescaling_diag
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

import modeling.fit_kernels as fk
from modeling.design import build_design, event_times_hours
from modeling.estimator import fit_glm
from modeling.tide_phase import HarmonicTidalPhase, TidalPhase
from modeling.validation.time_rescaling import cumulative_hazard, run_time_rescaling
from src.aws_backend.config import settings
from src.aws_backend.timeseries import MemoryTimeSeriesStore, build_timeseries_store

# Coordinate with agent A's effort / log E module when it is in the tree. It owns
# the uptime<->acoustic station-key crosswalk (the uptime stream is keyed
# rpi_orcasound_lab, the acoustic stream haro_strait/orcasound_lab) that a naive
# uptime.get(station) misses. When absent, the effort probe falls back to a flat
# (continuous) effort and states it.
try:
    from modeling import effort as effort_mod  # agent A, Wave 1
except Exception:  # pragma: no cover - module is local-only and may not be landed
    effort_mod = None

from .common import ORCAHELLO_CACHE, STATION_COORDS

_WIDE0 = datetime(1970, 1, 1, tzinfo=timezone.utc)
_WIDE1 = datetime(2100, 1, 1, tzinfo=timezone.utc)
ACOUSTIC = "acoustic_detections"
CURRENTS = "env_currents"
UPTIME = "station_uptime"
BIN_HOURS = 1.0
MIN_IEIS = 20  # matches _time_rescaling_report

REPORTS_DIR = Path(__file__).resolve().parent / "reports"
REPORT_PATH = REPORTS_DIR / "time_rescaling_diag.json"


# --------------------------------------------------------------------------- #
# Data assembly (mirrors level2_multistation.run(); does NOT import-and-mutate)
# --------------------------------------------------------------------------- #
def _cached_acoustic_by_station() -> Dict[str, List[dict]]:
    if not ORCAHELLO_CACHE.exists():
        return {}
    raw = json.loads(ORCAHELLO_CACHE.read_text(encoding="utf-8"))
    out: Dict[str, List[dict]] = {}
    for row in raw.get("records", []):
        key = str(row.get("key", ""))
        coords = STATION_COORDS.get(key)
        t = row.get("t")
        if not coords or not t:
            continue
        out.setdefault(key, []).append(
            {"t": t, "station": key, "latitude": coords[0], "longitude": coords[1], "id": row.get("id")}
        )
    return out


def _build_memory_store() -> MemoryTimeSeriesStore:
    src = build_timeseries_store(settings)
    mem = MemoryTimeSeriesStore()
    haro = src.get_series(ACOUSTIC, "haro_strait", _WIDE0, _WIDE1)
    mem.put_series(ACOUSTIC, "haro_strait", haro)
    for station, recs in _cached_acoustic_by_station().items():
        if station == "haro_strait":
            continue
        mem.put_series(ACOUSTIC, station, recs)
    for st in src.list_stations(CURRENTS):
        mem.put_series(CURRENTS, st, src.get_series(CURRENTS, st, _WIDE0, _WIDE1))
    for st in src.list_stations(UPTIME):
        mem.put_series(UPTIME, st, src.get_series(UPTIME, st, _WIDE0, _WIDE1))
    return mem


def _fit(mem: MemoryTimeSeriesStore):
    """Reproduce run_fit's tide/design/covariate/NB2 path for the model object."""
    fk._maybe_write_s3 = lambda: None  # defensive: never touch the model bucket
    acoustic, uptime, currents = fk.read_streams(mem, _WIDE0, _WIDE1)

    tide = None
    tide_model = "none"
    if currents:
        harmonic = HarmonicTidalPhase.from_records(currents)
        if harmonic is not None and harmonic.reconstruction_r2 > 0.5:
            tide, tide_model = harmonic, "harmonic"
        else:
            tide, tide_model = TidalPhase.from_records(currents), "onset_interpolation"

    df = build_design(acoustic, uptime, tide_phase=tide, bin_hours=BIN_HOURS)
    report_stub: Dict[str, object] = {
        "tide_overlaps_acoustic": bool(
            fk._spans_overlap(fk._span([r for recs in acoustic.values() for r in recs]), fk._span(currents))
        )
    }
    fit_covariates, _ = fk._select_covariates(df, report_stub)
    model = fit_glm(df, covariates=tuple(fit_covariates), n_harmonics=2, family=fk.PRIMARY_FAMILY)
    return model, acoustic, uptime, tide, tide_model, list(fit_covariates)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _station_coords(records: List[dict]) -> Tuple[float, float]:
    lat = float(np.median([r["latitude"] for r in records if r.get("latitude") is not None] or [48.5]))
    lng = float(np.median([r["longitude"] for r in records if r.get("longitude") is not None] or [-123.0]))
    return lat, lng


def _ks_exp(x: np.ndarray) -> Tuple[Optional[float], Optional[float], int]:
    x = np.asarray(x, dtype=float)
    x = x[x > 0]
    if x.size < MIN_IEIS:
        return None, None, int(x.size)
    ks = stats.kstest(x, "expon", args=(0, 1))
    return float(ks.statistic), float(ks.pvalue), int(x.size)


def _burstiness(events: np.ndarray) -> Dict[str, object]:
    """Raw inter-event statistics. CV>>1 and a near-zero spike => clustered/bursty."""
    ev = np.sort(np.asarray(events, dtype=float))
    iei = np.diff(ev)
    iei = iei[iei > 0]
    if iei.size == 0:
        return {"n_iei": 0}
    mean = float(iei.mean())
    cv = float(iei.std() / mean) if mean > 0 else None
    return {
        "n_iei": int(iei.size),
        "span_hours": float(ev[-1] - ev[0]),
        "raw_iei_median_h": float(np.median(iei)),
        "raw_iei_mean_h": mean,
        "raw_iei_cv": cv,  # 1.0 for a homogeneous Poisson; >1 = bursty/overdispersed
        "frac_iei_under_6min": float(np.mean(iei < 0.1)),  # within-burst detections
        "frac_iei_over_1day": float(np.mean(iei > 24.0)),  # inter-encounter gaps
    }


def _effort_gated_intensity(
    base_intensity: Callable,
    uptime: Dict[str, List[dict]],
    station: str,
    events: np.ndarray,
) -> Tuple[Callable, bool]:
    """Multiply the fitted intensity by the relative effort fraction E(t) in (0,1].

    The observed point process has conditional intensity
    ``lambda_obs(t) = exp(b0 + kernels) * E(t)``; integrating the cumulative
    hazard only over ON time removes the downtime gaps the flat-effort
    `_station_intensity_fn` wrongly counts as low-rate waiting time.

    Uses agent A's `modeling.effort` (cross-namespace uptime binding +
    documented fallbacks) when present. Returns (intensity, effort_binds), where
    effort_binds is True only when a real uptime series overlaps the detection
    window; otherwise the effort term is flat (continuous) and the intensity is
    unchanged.
    """
    if effort_mod is None:
        return base_intensity, False
    binds = effort_mod.uptime_binds(uptime, station, detection_times=events)

    def gated(t_hours: np.ndarray) -> np.ndarray:
        t_hours = np.atleast_1d(np.asarray(t_hours, dtype=float))
        e = effort_mod.relative_effort(
            t_hours, uptime, station,
            fallback=effort_mod.FALLBACK_CONTINUOUS, detection_times=events,
        )
        return base_intensity(t_hours) * e

    return gated, bool(binds)


def _constant_rate_ks(events: np.ndarray, grid_step: float) -> Dict[str, object]:
    """Time-rescaling against a homogeneous-Poisson constant rate (n/span)."""
    ev = np.sort(np.asarray(events, dtype=float))
    span = float(ev[-1] - ev[0]) if ev.size >= 2 else 0.0
    if span <= 0:
        return {"ks_exp_pval": None, "n_rescaled_ieis": 0}
    rate = float(ev.size / span)
    res = run_time_rescaling(ev, intensity=lambda t: np.full(np.shape(t), rate),
                             grid_step=grid_step, min_ieis=MIN_IEIS)
    return {
        "constant_rate_per_h": rate,
        "ks_exp_pval": res.get("ks_exp_pval"),
        "pass_exp": res.get("pass_exp"),
        "rescaled_iei_mean": res.get("rescaled_iei_mean"),
        "n_rescaled_ieis": res.get("n_rescaled_ieis"),
    }


# --------------------------------------------------------------------------- #
# Diagnostic
# --------------------------------------------------------------------------- #
def run() -> Dict[str, object]:
    if settings.storage_backend.lower() != "aws":
        return {
            "status": "insufficient_data",
            "reason": "Needs ORCAST_STORAGE_BACKEND=aws + the raw-payload bucket "
                      "(198456344617-us-west-2-orcast-aws-backend-raw-payloads) to read haro_strait + currents.",
        }

    mem = _build_memory_store()
    model, acoustic, uptime, tide, tide_model, covariates_fit = _fit(mem)

    # ---- A + B: per-station baseline (flat effort, grid_step=BIN_HOURS) -------
    per_station: Dict[str, dict] = {}
    pooled_by_station: Dict[str, np.ndarray] = {}
    for station, records in acoustic.items():
        events = event_times_hours(records)
        if events.size < MIN_IEIS:
            per_station[station] = {"n_events": int(events.size), "skipped": "fewer than %d events" % MIN_IEIS}
            continue
        lat, lng = _station_coords(records)
        intensity = fk._station_intensity_fn(model, station, lat, lng, tide)
        res = run_time_rescaling(events, intensity=intensity, grid_step=BIN_HOURS, min_ieis=MIN_IEIS)
        rescaled = np.asarray(res.get("rescaled_ieis", []), dtype=float)
        rescaled = rescaled[rescaled > 0]
        pooled_by_station[station] = rescaled

        # Fitted-intensity modulation across this station's event times: how much
        # shape do the kernels actually impose? ~1.0 => essentially constant.
        lam = np.asarray(intensity(events), dtype=float)
        lam = lam[np.isfinite(lam) & (lam > 0)]
        modulation = float(lam.max() / lam.min()) if lam.size else None

        per_station[station] = {
            "n_events": int(events.size),
            "ks_exp_pval": res.get("ks_exp_pval"),
            "ks_exp_stat": res.get("ks_exp_stat"),
            "pass_exp": res.get("pass_exp"),
            "n_rescaled_ieis": res.get("n_rescaled_ieis"),
            "rescaled_iei_mean": res.get("rescaled_iei_mean"),  # 1.0 if level correct
            "rescaled_iei_std": res.get("rescaled_iei_std"),
            "intensity_modulation_maxmin": modulation,
            "fitted_intensity_mean_per_h": float(np.mean(lam)) if lam.size else None,
            "raw_iei": _burstiness(events),
        }

    pooled = np.concatenate([v for v in pooled_by_station.values() if v.size]) if pooled_by_station else np.array([])
    p_stat, p_pval, p_n = _ks_exp(pooled)
    pooled_block = {
        "pooled_n": p_n,
        "pooled_ks_exp_pval": p_pval,
        "pooled_ks_exp_stat": p_stat,
        "pooled_pass_exp": (p_pval is not None and p_pval > 0.05),
        "pooled_rescaled_iei_mean": float(pooled.mean()) if pooled.size else None,
        "frac_rescaled_under_0p05": float(np.mean(pooled < 0.05)) if pooled.size else None,
    }

    # Leave-one-out pooled KS: is one station dragging the pool?
    loo: Dict[str, object] = {}
    stations_with_data = [s for s, v in pooled_by_station.items() if v.size]
    for drop in stations_with_data:
        rest = np.concatenate([v for s, v in pooled_by_station.items() if v.size and s != drop])
        _, pv, n = _ks_exp(rest)
        loo[f"drop_{drop}"] = {"pooled_ks_exp_pval": pv, "pooled_n": n}

    # ---- C1: constant-rescale to mean rescaled IEI == 1 (level-only fix) ------
    level_only: Dict[str, object] = {}
    rescaled_pool_normed: List[np.ndarray] = []
    for station, rescaled in pooled_by_station.items():
        if rescaled.size < MIN_IEIS:
            continue
        m = float(rescaled.mean())
        normed = rescaled / m if m > 0 else rescaled  # constant intensity scale -> mean 1
        rescaled_pool_normed.append(normed)
        _, pv, _ = _ks_exp(normed)
        level_only[station] = {"rescaled_iei_mean_before": m, "ks_exp_pval_after_level_fix": pv}
    pooled_normed = np.concatenate(rescaled_pool_normed) if rescaled_pool_normed else np.array([])
    _, lvl_pv, lvl_n = _ks_exp(pooled_normed)
    level_only["_pooled"] = {"pooled_ks_exp_pval_after_level_fix": lvl_pv, "pooled_n": lvl_n}

    # ---- C2: effort-corrected intensity (integrate over relative effort) ------
    effort_gated: Dict[str, object] = {}
    gated_pool: List[np.ndarray] = []
    for station, records in acoustic.items():
        events = event_times_hours(records)
        if events.size < MIN_IEIS:
            continue
        lat, lng = _station_coords(records)
        base = fk._station_intensity_fn(model, station, lat, lng, tide)
        gated, effort_binds = _effort_gated_intensity(base, uptime, station, events)
        res = run_time_rescaling(events, intensity=gated, grid_step=BIN_HOURS, min_ieis=MIN_IEIS)
        rescaled = np.asarray(res.get("rescaled_ieis", []), dtype=float)
        rescaled = rescaled[rescaled > 0]
        if rescaled.size:
            gated_pool.append(rescaled)
        effort_gated[station] = {
            "effort_uptime_binds_window": effort_binds,
            "ks_exp_pval": res.get("ks_exp_pval"),
            "pass_exp": res.get("pass_exp"),
            "rescaled_iei_mean": res.get("rescaled_iei_mean"),
            "n_rescaled_ieis": res.get("n_rescaled_ieis"),
        }
    gated_arr = np.concatenate(gated_pool) if gated_pool else np.array([])
    _, gated_pv, gated_n = _ks_exp(gated_arr)
    # Honest binding diagnostic from agent A's module: does any uptime series
    # actually overlap the detection windows? (Cached OrcaHello nodes carry none.)
    if effort_mod is not None:
        eff_summary = effort_mod.effort_summary(uptime, acoustic, bin_hours=BIN_HOURS)
    else:
        eff_summary = {"available": False, "note": "modeling/effort.py (agent A) not in tree at run time"}
    effort_gated["_pooled"] = {
        "pooled_ks_exp_pval": gated_pv,
        "pooled_n": gated_n,
        "effort_module": "modeling.effort (agent A)" if effort_mod is not None else None,
        "any_station_uptime_binds": eff_summary.get("any_station_uptime_binds"),
        "uptime_stream_keys": sorted([s for s in uptime.keys()]),
        "effort_summary": eff_summary,
        "note": "Effort via agent A's cross-namespace resolver; cached OrcaHello nodes have no "
                "station_uptime and there is no haro_strait uptime node, so effort is flat where it "
                "does not bind (stated per station).",
    }

    # ---- D: grid/bin resolution sweep on the pooled KS -----------------------
    grid_sweep: Dict[str, object] = {}
    for gs in (0.05, 0.1, 0.25, 0.5, 1.0):
        pool_gs: List[np.ndarray] = []
        for station, records in acoustic.items():
            events = event_times_hours(records)
            if events.size < MIN_IEIS:
                continue
            lat, lng = _station_coords(records)
            intensity = fk._station_intensity_fn(model, station, lat, lng, tide)
            res = run_time_rescaling(events, intensity=intensity, grid_step=gs, min_ieis=MIN_IEIS)
            r = np.asarray(res.get("rescaled_ieis", []), dtype=float)
            r = r[r > 0]
            if r.size:
                pool_gs.append(r)
        arr = np.concatenate(pool_gs) if pool_gs else np.array([])
        _, pv, n = _ks_exp(arr)
        grid_sweep[f"grid_step_{gs}"] = {"pooled_ks_exp_pval": pv, "pooled_n": n}

    # ---- E: conditional-intensity construction (constant-rate comparison) ----
    construction: Dict[str, object] = {}
    const_pool: List[np.ndarray] = []
    for station, records in acoustic.items():
        events = event_times_hours(records)
        if events.size < MIN_IEIS:
            continue
        cr = _constant_rate_ks(events, BIN_HOURS)
        construction[station] = cr
        # rebuild the constant-rate rescaled IEIs for the pool
        ev = np.sort(events)
        span = float(ev[-1] - ev[0])
        if span > 0:
            rate = ev.size / span
            grid = np.arange(ev[0], ev[-1] + BIN_HOURS, BIN_HOURS)
            cum = cumulative_hazard(ev, grid, np.full(grid.shape, rate))
            r = np.diff(cum)
            r = r[r > 0]
            if r.size:
                const_pool.append(r)
    const_arr = np.concatenate(const_pool) if const_pool else np.array([])
    _, const_pv, const_n = _ks_exp(const_arr)
    construction["_pooled_constant_rate"] = {"pooled_ks_exp_pval": const_pv, "pooled_n": const_n}

    # ---- Recommended fix (named for the Wave 2 integrator) -------------------
    recommended = _recommend(per_station, pooled_block, level_only, effort_gated,
                             grid_sweep, construction)

    return {
        "status": "diagnosed",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provenance": (
            "EXPERIMENT diagnostic: 4-station memory store (production haro_strait acoustic_detections "
            "from S3 + cached OrcaHello index for orcasound_lab/north_san_juan_channel/andrews_bay + S3 "
            "env_currents/station_uptime); NB2 joint GLM identical to level2_multistation; no fit "
            "artifact written, no production store/model bucket touched."
        ),
        "agent_a_effort_module": {
            "effort_py_present": effort_mod is not None,
            "wiring_md_present": Path("modeling/WIRING-effort.md").exists(),
            "note": (
                "modeling/effort.py (agent A) is present and used for the effort probe (C2) via its "
                "cross-namespace uptime resolver and relative_effort/station_log_effort API; "
                "WIRING-effort.md was not yet in the tree at run time."
                if effort_mod is not None else
                "modeling/effort.py (agent A) absent at run time; the effort probe (C2) falls back to a "
                "flat (continuous) effort and states so."
            ),
        },
        "fit_context": {
            "tide_model": tide_model,
            "covariates_fit": covariates_fit,
            "family": fk.PRIMARY_FAMILY,
            "bin_hours": BIN_HOURS,
            "min_ieis": MIN_IEIS,
            "n_stations_acoustic": len(acoustic),
        },
        "A_B_per_station_baseline": per_station,
        "pooled_baseline": pooled_block,
        "B_leave_one_out_pooled": loo,
        "C1_level_only_fix": level_only,
        "C2_effort_gated_intensity": effort_gated,
        "D_grid_resolution_sweep": grid_sweep,
        "E_intensity_construction_constant_rate": construction,
        "recommended_fix": recommended,
    }


def _recommend(per_station, pooled_block, level_only, effort_gated, grid_sweep, construction) -> Dict[str, object]:
    """Name the single most likely fix, justified by the measured probes."""
    # Burstiness: median CV of raw IEIs across stations (1.0 = Poisson).
    cvs = [v["raw_iei"].get("raw_iei_cv") for v in per_station.values()
           if isinstance(v.get("raw_iei"), dict) and v["raw_iei"].get("raw_iei_cv") is not None]
    median_cv = float(np.median(cvs)) if cvs else None
    near_zero = pooled_block.get("frac_rescaled_under_0p05")
    const_pooled = construction.get("_pooled_constant_rate", {}).get("pooled_ks_exp_pval")
    level_pooled = level_only.get("_pooled", {}).get("pooled_ks_exp_pval_after_level_fix")
    gated_pooled = effort_gated.get("_pooled", {}).get("pooled_ks_exp_pval")
    grid_pvals = [v.get("pooled_ks_exp_pval") for v in grid_sweep.values() if v.get("pooled_ks_exp_pval") is not None]
    grid_best = max(grid_pvals) if grid_pvals else None

    bursty = (median_cv is not None and median_cv > 1.5) or (near_zero is not None and near_zero > 0.2)
    constant_also_fails = const_pooled is not None and const_pooled <= 0.05
    grid_helps = grid_best is not None and grid_best > 0.05
    level_helps = level_pooled is not None and level_pooled > 0.05
    effort_helps = gated_pooled is not None and gated_pooled > 0.05

    if grid_helps and not bursty:
        primary = "finer_integration_grid"
        rationale = (
            f"A finer grid_step lifts the pooled KS to p={grid_best:.3g} (>0.05); the trapezoid "
            "integration at bin_hours=1.0 was the binding error. Pass a finer grid_step to "
            "run_time_rescaling in _time_rescaling_report."
        )
    elif effort_helps and not level_helps:
        primary = "effort_offset_in_conditional_intensity"
        rationale = (
            f"Integrating the cumulative hazard only over station-ON time lifts the pooled KS to "
            f"p={gated_pooled:.3g}; downtime gaps the flat-effort _station_intensity_fn counts as "
            "low-rate waiting time were the driver. Wire agent A's log E so _station_intensity_fn "
            "carries the effort offset."
        )
    elif level_helps and not effort_helps:
        primary = "per_station_intensity_level_calibration"
        rationale = (
            f"Normalising each station's intensity to mean rescaled IEI==1 passes (pooled p={level_pooled:.3g}); "
            "the kernel SHAPE is fine but the per-station rate LEVEL is mis-scaled when pooled. Use a "
            "per-station effort/level offset before pooling."
        )
    elif bursty and constant_also_fails:
        primary = "model_the_clustering_or_score_at_bin_level"
        rationale = (
            f"The acoustic stream is clustered (median raw-IEI CV={median_cv}, "
            f"{near_zero:.0%} of rescaled IEIs <0.05 vs ~5% for Exp(1)); a constant-rate homogeneous "
            f"Poisson fails identically (pooled p={const_pooled:.3g}), so the smooth Fourier kernels are "
            "NOT the cause. A smooth Poisson/NB conditional intensity cannot pass event-level "
            "time-rescaling on a bursty detection stream regardless of effort or grid. The honest fix is "
            "to either model the self-excitation (history/refractory term or a Hawkes-type intensity), "
            "or evaluate GOF at the bin-count level (the NB PIT/dispersion already gated) and deduplicate "
            "bursts to encounter-onset events for time-rescaling, NOT to tune the gate. Effort correction "
            "(agent A) reduces the long-gap tail but will not remove the near-zero spike from within-burst "
            "detections."
        )
    else:
        primary = "effort_offset_in_conditional_intensity"
        rationale = (
            "No single probe cleanly clears p>0.05. The dominant signal is the flat-effort intensity "
            "(_station_intensity_fn ignores station downtime); wire agent A's log E first, then re-test, "
            "and report withheld with the burstiness reason if it still fails."
        )

    return {
        "primary_fix": primary,
        "rationale": rationale,
        "evidence": {
            "median_raw_iei_cv": median_cv,
            "frac_rescaled_under_0p05": near_zero,
            "constant_rate_pooled_ks_pval": const_pooled,
            "level_fix_pooled_ks_pval": level_pooled,
            "effort_gated_pooled_ks_pval": gated_pooled,
            "best_grid_pooled_ks_pval": grid_best,
        },
        "honesty": (
            "If the only thing that 'passes' is constant-rescaling the level or tuning the grid while the "
            "process is demonstrably clustered, that is gate-tuning, not a fix: report L2 time-rescaling "
            "withheld with the clustering reason (charter B.3)."
        ),
    }


def main() -> int:
    report = run()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    if report.get("status") != "diagnosed":
        print(f"time_rescaling_diag: {report.get('status')} -- {report.get('reason')}")
        return 0
    pb = report["pooled_baseline"]
    print(f"time_rescaling_diag -> {REPORT_PATH}")
    print(f"  pooled KS p={pb.get('pooled_ks_exp_pval')} (n={pb.get('pooled_n')}, "
          f"mean={pb.get('pooled_rescaled_iei_mean')})")
    for st, v in report["A_B_per_station_baseline"].items():
        print(f"  {st}: KS p={v.get('ks_exp_pval')} n_ieis={v.get('n_rescaled_ieis')} "
              f"raw_iei_cv={v.get('raw_iei', {}).get('raw_iei_cv') if isinstance(v.get('raw_iei'), dict) else None}")
    print(f"  recommended_fix: {report['recommended_fix']['primary_fix']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
