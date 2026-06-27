"""M-L1 diagnostic: WHY are the per-kernel cross-station PSTH correlations low?

The joint fit's ``_cross_station_consistency`` (``modeling/fit_kernels.py``)
reports per-kernel cross-station PSTH correlations below the 0.5 consistency bar
(the second Level 2 blocker). This is a STANDALONE diagnostic that MIRRORS that
logic (it does not edit it) and decomposes the mean. Per W4 item 1 (RE/RB) it
scores at the COARSER headline resolution (12 bins, was 24) with a minimum
per-bin count, mirroring ``fit_kernels.XSTN_HEADLINE_BINS`` / the masked
correlation, and reports:

* per-kernel, per-station effort-normalized PSTH log-rate curves (+ per-bin counts),
* the full per-kernel pairwise MASKED cross-station correlation matrix (only bins
  with >= MIN_BIN_COUNT counts in both stations enter the correlation),
* which station pairs and which kernels drag the mean down,
* the effect of effort normalization (flat vs ``exposure``; Agent A's
  ``modeling/effort.py`` is consumed IF present, otherwise stated unavailable),
* the effect of partial pooling (sample-size-weighted shrinkage toward the grand
  mean) -- reported WITH the caveat that shrinkage mechanically inflates the
  cross-station correlation, so it is not a clean "fix",
* a within-station split-half reliability ceiling and a bin-count sensitivity
  sweep, which together separate GENUINE station heterogeneity from a sparse-count
  / small-sample PSTH-noise artifact,
* a burst-dedup encounter-onset re-score (one onset per run of consecutive
  occupied bins) reported alongside as the harder, per-encounter honesty check
  (U3 -- it reduces effective N and so cannot inflate the bar).

It builds the SAME multi-station memory store as
``modeling/studies/level2_multistation.py`` (production ``haro_strait`` stream
from S3 + the cached OrcaHello index for orcasound_lab / north_san_juan_channel /
andrews_bay + S3 env_currents + station_uptime), but it runs NO heavy fit: it only
builds the design matrix and computes PSTHs. It writes no production store or model
artifact and promotes no confidence.

Run under .venv-modeling with the AWS env (charter B.4):

    ORCAST_STORAGE_BACKEND=aws \
    ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads \
    AWS_REGION=us-west-2 PYTHONPATH=. \
    .venv-modeling/bin/python -m modeling.studies.cross_station_consistency
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

import modeling.fit_kernels as fk
from modeling.design import build_design, event_times_hours, phase_coverage
from modeling.psth import psth
from modeling.tide_phase import HarmonicTidalPhase, TidalPhase
from src.aws_backend.config import settings
from src.aws_backend.timeseries import MemoryTimeSeriesStore, build_timeseries_store

from .common import ORCAHELLO_CACHE, STATION_COORDS

_WIDE0 = datetime(1970, 1, 1, tzinfo=timezone.utc)
_WIDE1 = datetime(2100, 1, 1, tzinfo=timezone.utc)
ACOUSTIC = "acoustic_detections"
CURRENTS = "env_currents"
UPTIME = "station_uptime"

CONSISTENCY_BAR = 0.5
# W4 item 1 (RE/RB): a COARSER headline PSTH resolution than the old 24 bins,
# with a minimum per-bin count, so empty-bin -log floors stop dominating the
# correlation on sparse per-station data. Mirrors fit_kernels.XSTN_HEADLINE_BINS.
N_BINS = 12           # mirrors fit_kernels._cross_station_consistency (was 24)
MIN_BIN_COUNT = 1.0   # minimum per-bin count for a bin to enter the correlation
BIN_SWEEP = (8, 12, 24)
MIN_STATION_ROWS = 24  # mirrors _cross_station_consistency
# Encounter-onset (burst-dedup) window: runs of consecutive occupied bins within
# this gap collapse to one onset (mirrors fit_kernels.ENCOUNTER_GAP_HOURS = 1.0).
ENCOUNTER_GAP_HOURS = 1.0
N_SPLIT_HALF = 200    # bootstrap reps for the within-station reliability ceiling
REPORT_PATH = Path(__file__).resolve().parent / "reports" / "cross_station_consistency.json"

# Agent A (Wave 1) owns modeling/effort.py + WIRING-effort.md. It runs in parallel
# with this agent, so it may not exist yet; this study consumes it ONLY if present.
try:  # pragma: no cover - optional dependency on a parallel-wave module
    from modeling.effort import (  # type: ignore
        FALLBACK_CONTINUOUS,
        FALLBACK_DETECTION_DENSITY,
        effort_summary,
        exposure_for_bins,
    )
    _EFFORT_AVAILABLE = True
except Exception:  # noqa: BLE001 - any import failure means "not ready this wave"
    _EFFORT_AVAILABLE = False


# --------------------------------------------------------------------------- #
# Data assembly (same provenance as level2_multistation.py)
# --------------------------------------------------------------------------- #
def _cached_acoustic_by_station() -> Dict[str, List[dict]]:
    """Cached OrcaHello index records enriched with station coords, grouped by station."""
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


def _build_multistation_store():
    """Mirror level2_multistation.run(): haro_strait (S3) + cached 3 nodes + currents + uptime."""
    src = build_timeseries_store(settings)
    if settings.storage_backend.lower() != "aws":
        return None, "needs ORCAST_STORAGE_BACKEND=aws + the raw-payload bucket to read haro_strait + currents"

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
    return mem, None


def _read_streams(mem) -> Tuple[Dict[str, List[dict]], Dict[str, List[dict]], List[dict]]:
    acoustic: Dict[str, List[dict]] = {}
    for st in mem.list_stations(ACOUSTIC):
        acoustic[st] = mem.get_series(ACOUSTIC, st, _WIDE0, _WIDE1)
    uptime: Dict[str, List[dict]] = {}
    for st in mem.list_stations(UPTIME):
        uptime[st] = mem.get_series(UPTIME, st, _WIDE0, _WIDE1)
    currents: List[dict] = []
    for st in mem.list_stations(CURRENTS):
        currents.extend(mem.get_series(CURRENTS, st, _WIDE0, _WIDE1))
    return acoustic, uptime, currents


def _select_tide(currents: List[dict]):
    """Same tide-model selection as run_fit: harmonic if R^2>0.5 else onset, else none."""
    if not currents:
        return None, "none", None
    harmonic = HarmonicTidalPhase.from_records(currents)
    if harmonic is not None and harmonic.reconstruction_r2 > 0.5:
        return harmonic, "harmonic", harmonic.reconstruction_r2
    tide = TidalPhase.from_records(currents)
    r2 = harmonic.reconstruction_r2 if harmonic is not None else None
    return tide, "onset_interpolation", r2


# --------------------------------------------------------------------------- #
# PSTH curve helpers (mirror the _cross_station_consistency log-rate curve)
# --------------------------------------------------------------------------- #
def _log_rate_curve(phase: np.ndarray, y: np.ndarray, exposure: np.ndarray, n_bins: int):
    """Effort-normalized binned log-rate curve + per-bin count.

    Mirrors ``fit_kernels._binned_log_rate``: returns ``(log_rate, counts)`` so
    the correlation can be masked to bins with a minimum per-bin count (W4 item
    1), instead of letting empty-bin -log floors create spurious correlation.
    """
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


def _masked_corr(c1, n1, c2, n2, min_count: float = MIN_BIN_COUNT) -> Optional[float]:
    """Correlation over bins with >= ``min_count`` counts in BOTH stations."""
    mask = (np.asarray(n1) >= min_count) & (np.asarray(n2) >= min_count)
    if int(mask.sum()) < 3:
        return None
    a, b = np.asarray(c1)[mask], np.asarray(c2)[mask]
    if np.std(a) <= 1e-9 or np.std(b) <= 1e-9:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def _onset_y(sub) -> np.ndarray:
    """Bin-level burst-dedup weights aligned to ``sub`` row order (W4 item 1).

    1.0 on the ONSET bin of each run of consecutive occupied bins (gap <=
    ``ENCOUNTER_GAP_HOURS``), else 0.0. Mirrors ``fit_kernels._xstn_onset_y``:
    reliability is then measured per independent encounter, not per bursty hour
    (U3). It reduces effective N, so it makes the bar HARDER -- an honesty
    correction reported alongside the raw-count headline.
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


def _corr(a: np.ndarray, b: np.ndarray) -> Optional[float]:
    if np.std(a) > 1e-9 and np.std(b) > 1e-9:
        return float(np.corrcoef(a, b)[0, 1])
    return None


def _mean_offdiag(matrix: Dict[str, Dict[str, Optional[float]]]) -> Optional[float]:
    vals = [v for row in matrix.values() for v in row.values() if v is not None]
    return float(np.mean(vals)) if vals else None


def _station_curves(
    df, cov: str, stations: List[str], n_bins: int, flat_effort: bool = False,
    onset: bool = False,
) -> Dict[str, tuple]:
    """Per-station ``(log_rate, counts)`` curves for one covariate (>= MIN_STATION_ROWS rows).

    With ``onset=True`` the detection vector is burst-deduped to encounter onsets
    (W4 item 1) before binning.
    """
    curves: Dict[str, tuple] = {}
    for st in stations:
        sub = df[df["station"].astype(str) == st]
        if len(sub) < MIN_STATION_ROWS:
            continue
        exposure = sub["exposure"].to_numpy(dtype=float)
        if flat_effort:
            exposure = np.ones_like(exposure)
        y = _onset_y(sub) if onset else sub["y"].to_numpy(dtype=float)
        curves[st] = _log_rate_curve(sub[cov].to_numpy(dtype=float), y, exposure, n_bins)
    return curves


def _effort_a_curves(
    df, cov: str, stations: List[str], acoustic: Dict[str, List[dict]],
    uptime: Dict[str, List[dict]], n_bins: int, fallback: str,
) -> Dict[str, np.ndarray]:
    """Per-station log-rate curves whose exposure comes from Agent A's effort model.

    Uses ``modeling.effort.exposure_for_bins`` (the corrected ``rpi_*`` station-key
    binding + the chosen fallback) instead of build_design's exposure column, so we
    can measure whether a real effort model moves the cross-station correlation.
    """
    curves: Dict[str, tuple] = {}
    for st in stations:
        sub = df[df["station"].astype(str) == st]
        if len(sub) < MIN_STATION_ROWS:
            continue
        centers = sub["t"].to_numpy(dtype=float)
        events = event_times_hours(acoustic.get(st, []))
        exposure = exposure_for_bins(
            uptime, st, centers, bin_hours=1.0, fallback=fallback, detection_times=events
        )
        exposure = np.clip(np.asarray(exposure, dtype=float), 1e-9, None)
        curves[st] = _log_rate_curve(sub[cov].to_numpy(dtype=float), sub["y"].to_numpy(dtype=float), exposure, n_bins)
    return curves


def _pairwise_matrix(curves: Dict[str, tuple]) -> Dict[str, Dict[str, Optional[float]]]:
    """Pairwise masked cross-station correlation (>= MIN_BIN_COUNT in both)."""
    stations = sorted(curves)
    matrix: Dict[str, Dict[str, Optional[float]]] = {a: {} for a in stations}
    for a, b in combinations(stations, 2):
        (ca, na), (cb, nb) = curves[a], curves[b]
        c = _masked_corr(ca, na, cb, nb, MIN_BIN_COUNT)
        matrix[a][b] = c
        matrix[b].setdefault(a, c)
    return matrix


def _worst_pairs(matrix: Dict[str, Dict[str, Optional[float]]]) -> List[dict]:
    pairs = []
    seen = set()
    for a, row in matrix.items():
        for b, c in row.items():
            key = tuple(sorted((a, b)))
            if c is None or key in seen:
                continue
            seen.add(key)
            pairs.append({"pair": list(key), "corr": round(c, 4)})
    return sorted(pairs, key=lambda d: d["corr"])


def _per_station_mean_corr(matrix: Dict[str, Dict[str, Optional[float]]]) -> Dict[str, Optional[float]]:
    out: Dict[str, Optional[float]] = {}
    for a, row in matrix.items():
        vals = [c for c in row.values() if c is not None]
        out[a] = round(float(np.mean(vals)), 4) if vals else None
    return out


# --------------------------------------------------------------------------- #
# Diagnostics that separate heterogeneity from a small-sample artifact
# --------------------------------------------------------------------------- #
def _split_half_reliability(
    df, cov: str, stations: List[str], n_bins: int, seed: int = 0, onset: bool = False
) -> Dict[str, object]:
    """Within-station split-half PSTH correlation: the reproducibility CEILING.

    If a single station cannot reproduce its OWN PSTH shape across two random
    halves of its data, the cross-station correlation is bounded below by noise,
    not by genuine heterogeneity. This is the key artifact discriminator. Scored
    with the same coarse-bin + min-per-bin-count mask as the cross-station
    correlation (W4 item 1); ``onset=True`` burst-dedups to encounter onsets.
    """
    rng = np.random.default_rng(seed)
    per_station: Dict[str, Optional[float]] = {}
    for st in stations:
        sub = df[df["station"].astype(str) == st]
        if len(sub) < 2 * MIN_STATION_ROWS:
            per_station[st] = None
            continue
        phase = sub[cov].to_numpy(dtype=float)
        y = _onset_y(sub) if onset else sub["y"].to_numpy(dtype=float)
        exposure = sub["exposure"].to_numpy(dtype=float)
        n = len(sub)
        reps = []
        for _ in range(N_SPLIT_HALF):
            perm = rng.permutation(n)
            h1, h2 = perm[: n // 2], perm[n // 2:]
            c1, n1 = _log_rate_curve(phase[h1], y[h1], exposure[h1], n_bins)
            c2, n2 = _log_rate_curve(phase[h2], y[h2], exposure[h2], n_bins)
            c = _masked_corr(c1, n1, c2, n2, MIN_BIN_COUNT)
            if c is not None:
                reps.append(c)
        per_station[st] = round(float(np.mean(reps)), 4) if reps else None
    vals = [v for v in per_station.values() if v is not None]
    return {"per_station": per_station, "mean": round(float(np.mean(vals)), 4) if vals else None}


def _shrinkage_corr(curves: Dict[str, np.ndarray], counts: Dict[str, float]) -> Dict[str, object]:
    """Empirical-Bayes shrinkage of each station curve toward a sample-size-weighted
    grand mean, then the cross-station correlation of the shrunken curves.

    CAVEAT (stated in the report): shrinking every station toward a SHARED target
    injects a common component, which mechanically raises the pairwise correlation.
    A large gain here is therefore NOT evidence that the stations agree; it is an
    upper bound on what partial pooling could buy and must be read against the
    split-half ceiling.
    """
    stations = sorted(curves)
    if len(stations) < 2:
        return {"mean_corr": None, "note": "needs >= 2 stations", "caveat": "shrinkage inflates correlation"}
    logr = {s: np.asarray(curves[s][0], dtype=float) for s in stations}
    bincounts = {s: np.asarray(curves[s][1], dtype=float) for s in stations}
    n = np.array([max(counts.get(s, 0.0), 0.0) for s in stations])
    w_target = n / n.sum() if n.sum() > 0 else np.ones(len(stations)) / len(stations)
    grand = np.zeros_like(logr[stations[0]])
    for s, w in zip(stations, w_target):
        grand = grand + w * logr[s]
    k = float(np.median(n)) if n.size else 0.0  # pooling constant ~ typical station size
    shrunk = {}
    for s in stations:
        w_s = counts.get(s, 0.0) / (counts.get(s, 0.0) + k) if (counts.get(s, 0.0) + k) > 0 else 0.0
        shrunk[s] = (w_s * logr[s] + (1.0 - w_s) * grand, bincounts[s])
    matrix = _pairwise_matrix(shrunk)
    return {
        "mean_corr": _mean_offdiag(matrix),
        "pooling_constant_k": round(k, 2),
        "caveat": "shrinkage toward a shared target mechanically inflates cross-station correlation; "
                  "not evidence of agreement, read against the split-half ceiling",
    }


# --------------------------------------------------------------------------- #
# Main study
# --------------------------------------------------------------------------- #
def run() -> Dict[str, object]:
    fk._maybe_write_s3 = lambda: None  # belt-and-suspenders: never touch the model bucket

    mem, err = _build_multistation_store()
    if mem is None:
        return {"status": "insufficient_data", "reason": err, "consistency_bar": CONSISTENCY_BAR}

    acoustic, uptime, currents = _read_streams(mem)
    tide, tide_model, tide_r2 = _select_tide(currents)
    df = build_design(acoustic, uptime, tide_phase=tide, bin_hours=1.0)
    if df.empty:
        return {"status": "insufficient_data", "reason": "empty design matrix", "consistency_bar": CONSISTENCY_BAR}

    stations = sorted(df["station"].astype(str).unique())
    effort_assumed = bool(df.attrs.get("effort_assumed_continuous", True))

    # Tide overlaps acoustic? (drives the tide-covariate selection, like run_fit.)
    a_t = df["t"].to_numpy(dtype=float)
    tide_overlaps = bool(tide is not None and a_t.size > 0)

    # Mirror run_fit's covariate selection so we test exactly the fittable kernels.
    sel_report: Dict[str, object] = {"tide_overlaps_acoustic": tide_overlaps}
    fit_covariates, cov_notes = fk._select_covariates(df, sel_report)

    # Authoritative baseline: call the UNMODIFIED joint-fit routine for the headline
    # numbers, so this study cannot silently disagree with the gate it diagnoses.
    baseline = fk._cross_station_consistency(df, fit_covariates)

    # Per-station detection counts (sum of y) and occupied-bin counts -- the sparsity
    # that the PSTH noise scales with.
    per_station_detections = {
        st: int(df.loc[df["station"].astype(str) == st, "y"].sum()) for st in stations
    }
    per_station_bins = {st: int((df["station"].astype(str) == st).sum()) for st in stations}

    kernels: Dict[str, object] = {}
    for cov in fit_covariates:
        curves = _station_curves(df, cov, stations, N_BINS)
        if len(curves) < 2:
            kernels[cov] = {"testable": False, "reason": "< 2 stations with enough rows"}
            continue
        matrix = _pairwise_matrix(curves)
        mean_corr = _mean_offdiag(matrix)

        # Effort-normalization effect: flat exposure vs the design's exposure offset.
        flat_curves = _station_curves(df, cov, stations, N_BINS, flat_effort=True)
        flat_mean = _mean_offdiag(_pairwise_matrix(flat_curves)) if len(flat_curves) >= 2 else None

        # Agent A's effort model (if present): honest FALLBACK_CONTINUOUS, plus the
        # circular FALLBACK_DETECTION_DENSITY as a sensitivity bound only.
        effort_a_cont = effort_a_dens = None
        if _EFFORT_AVAILABLE:
            ca = _effort_a_curves(df, cov, stations, acoustic, uptime, N_BINS, FALLBACK_CONTINUOUS)
            cd = _effort_a_curves(df, cov, stations, acoustic, uptime, N_BINS, FALLBACK_DETECTION_DENSITY)
            effort_a_cont = _mean_offdiag(_pairwise_matrix(ca)) if len(ca) >= 2 else None
            effort_a_dens = _mean_offdiag(_pairwise_matrix(cd)) if len(cd) >= 2 else None

        # Bin-count sensitivity: coarser bins reduce per-bin sampling noise.
        bin_sweep = {}
        for nb in BIN_SWEEP:
            cs = _station_curves(df, cov, stations, nb)
            bin_sweep[str(nb)] = _mean_offdiag(_pairwise_matrix(cs)) if len(cs) >= 2 else None

        split_half = _split_half_reliability(df, cov, stations, N_BINS)
        shrink = _shrinkage_corr(curves, {s: float(per_station_detections.get(s, 0)) for s in curves})

        # Burst-dedup (encounter-onset) re-score: same coarse-bin / masked
        # correlation + split-half, but one onset per run of consecutive occupied
        # bins (W4 item 1 / U3). Reduces effective N -> harder; honesty check.
        onset_curves = _station_curves(df, cov, stations, N_BINS, onset=True)
        onset_mean = _mean_offdiag(_pairwise_matrix(onset_curves)) if len(onset_curves) >= 2 else None
        onset_split = _split_half_reliability(df, cov, stations, N_BINS, onset=True)
        onset_counts = {st: int(_onset_y(df[df["station"].astype(str) == st]).sum()) for st in stations}

        # Per-station phase coverage: a covariate (esp. season) whose observed phase
        # support differs across stations makes the cross-station PSTH compare
        # DIFFERENT slices of the cycle -- an observation-window confound, not
        # biological heterogeneity. Expose it so the verdict cannot overclaim.
        per_station_cov = {}
        for st in curves:
            sub = df[df["station"].astype(str) == st]
            per_station_cov[st] = round(
                phase_coverage(sub[cov].to_numpy(dtype=float), n_bins=12), 4
            )
        cov_values = list(per_station_cov.values())
        coverage_confound = bool(cov_values) and (min(cov_values) < 0.75 or (max(cov_values) - min(cov_values)) > 0.34)

        code, label = _classify(cov, mean_corr, split_half.get("mean"), coverage_confound)
        kernels[cov] = {
            "testable": True,
            "n_stations": len(curves),
            "headline_bins": N_BINS,
            "min_bin_count": MIN_BIN_COUNT,
            "mean_psth_correlation": None if mean_corr is None else round(mean_corr, 4),
            "correlation_matrix": {
                a: {b: (None if c is None else round(c, 4)) for b, c in row.items()}
                for a, row in matrix.items()
            },
            "per_station_mean_corr": _per_station_mean_corr(matrix),
            "worst_pairs": _worst_pairs(matrix),
            "per_station_phase_coverage": per_station_cov,
            "coverage_confound": coverage_confound,
            "effort_normalization": {
                "exposure_normalized_mean_corr": None if mean_corr is None else round(mean_corr, 4),
                "flat_effort_mean_corr": None if flat_mean is None else round(flat_mean, 4),
                "delta": (None if (mean_corr is None or flat_mean is None) else round(mean_corr - flat_mean, 4)),
                "effort_module_continuous_mean_corr": None if effort_a_cont is None else round(effort_a_cont, 4),
                "effort_module_detection_density_mean_corr": None if effort_a_dens is None else round(effort_a_dens, 4),
            },
            "bin_count_sensitivity": {k: (None if v is None else round(v, 4)) for k, v in bin_sweep.items()},
            "split_half_reliability": split_half,
            "partial_pooling_shrinkage": shrink,
            "burst_dedup_onset": {
                "method": (
                    "bin-level burst-dedup: runs of consecutive occupied %g h bins collapsed to one "
                    "encounter onset; reliability per encounter not per bursty hour (U3). Reduces "
                    "effective N -> makes the bar HARDER; honesty check alongside the headline."
                    % ENCOUNTER_GAP_HOURS
                ),
                "n_onsets_per_station": onset_counts,
                "mean_psth_correlation": None if onset_mean is None else round(onset_mean, 4),
                "split_half_reliability": onset_split,
            },
            "verdict_code": code,
            "verdict": label,
        }

    # Agent A effort diagnostic (binding facts), so the no-op claim is measured, not asserted.
    effort_block: Dict[str, object] = {
        "available": _EFFORT_AVAILABLE,
        "note": (
            "modeling/effort.py (Agent A) consumed via exposure_for_bins for the effort-normalized "
            "PSTH comparison (FALLBACK_CONTINUOUS = honest; FALLBACK_DETECTION_DENSITY = circular, "
            "sensitivity only)." if _EFFORT_AVAILABLE
            else "modeling/effort.py (Agent A) NOT present at run time; effort handled via the "
                 "build_design exposure offset only (flat where station_uptime is absent)."
        ),
    }
    if _EFFORT_AVAILABLE:
        try:
            effort_block["summary"] = effort_summary(uptime, acoustic, bin_hours=1.0)
        except Exception as exc:  # noqa: BLE001
            effort_block["summary_error"] = repr(exc)

    overall = _recommendation(kernels, baseline, effort_assumed, per_station_detections)

    return {
        "status": "ok",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "consistency_bar": CONSISTENCY_BAR,
        "provenance": (
            "DIAGNOSTIC, not a fit. Multi-station design = production haro_strait stream (S3) + "
            "cached OrcaHello index for orcasound_lab/north_san_juan_channel/andrews_bay + S3 "
            "env_currents + station_uptime. No store write, no model artifact, no confidence promotion."
        ),
        "n_stations": len(stations),
        "stations": stations,
        "per_station_detections": per_station_detections,
        "per_station_bins": per_station_bins,
        "effort_assumed_continuous": effort_assumed,
        "effort_module": effort_block,
        "tide_model": tide_model,
        "tide_reconstruction_r2": tide_r2,
        "fit_covariates": list(fit_covariates),
        "covariates_excluded": cov_notes,
        "baseline_cross_station_consistency": baseline,
        "kernels": kernels,
        "recommendation": overall,
    }


def _classify(
    cov: str, mean_corr: Optional[float], split_half_mean: Optional[float], coverage_confound: bool
) -> Tuple[str, str]:
    """Return (verdict_code, human_label).

    Codes:
      not_testable          -- no usable cross-station correlation
      consistent            -- clears the 0.5 bar
      noise_artifact        -- cross < bar AND within-station split-half < bar (noise-bound)
      reproducible_divergent_coverage -- reproducible within station, divergent across, but the
                               per-station phase coverage differs -> observation-window confound,
                               NOT demonstrated biological heterogeneity
      reproducible_divergent -- reproducible within station, divergent across, coverage comparable
                               -> consistent with genuine station heterogeneity
    """
    if mean_corr is None:
        return "not_testable", "not testable"
    # Honesty (mirrors fit_kernels._xstn_classify): a coverage confound (stations
    # span different parts of the cycle) is checked BEFORE the bar, because the
    # masked correlation is then computed over a shared sub-window only, not the
    # full kernel -- so a high value must NOT be reported as clean consistency.
    if coverage_confound:
        return (
            "reproducible_divergent_coverage",
            "per-station phase coverage differs (the stations span different parts of the cycle), so the "
            "cross-station correlation is over the shared window only -> observation-window confound, NOT "
            "demonstrated full-cycle consistency (mean corr=%s is not creditable)"
            % (None if mean_corr is None else round(mean_corr, 4)),
        )
    if mean_corr >= CONSISTENCY_BAR:
        return "consistent", "consistent (clears the 0.5 bar with comparable per-station coverage)"
    if split_half_mean is None:
        return "uncertain", "below bar; reliability ceiling unavailable (too few rows to split)"
    if split_half_mean < CONSISTENCY_BAR:
        return (
            "noise_artifact",
            "below bar, but within-station split-half reliability is ALSO below the bar: the PSTH is "
            "too noisy to reproduce within a single station -> sparse-count / small-sample artifact, "
            "not demonstrated genuine heterogeneity",
        )
    return (
        "reproducible_divergent",
        "below bar while within-station split-half reliability clears it and phase coverage is "
        "comparable across stations -> consistent with GENUINE station heterogeneity (reproducible "
        "yet divergent shapes)",
    )


def _recommendation(
    kernels: Dict[str, object],
    baseline: Dict[str, object],
    effort_assumed: bool,
    per_station_detections: Dict[str, int],
) -> Dict[str, object]:
    testable = {k: v for k, v in kernels.items() if isinstance(v, dict) and v.get("testable")}

    def _by_code(*codes: str) -> List[str]:
        return [k for k, v in testable.items() if v.get("verdict_code") in codes]

    cleared = _by_code("consistent")
    artifact_kernels = _by_code("noise_artifact")
    coverage_kernels = _by_code("reproducible_divergent_coverage")
    hetero_kernels = _by_code("reproducible_divergent")

    # Did coarser bins move things toward the bar? (artifact signature)
    coarse_helps = []
    for k, v in testable.items():
        bs = v.get("bin_count_sensitivity", {}) or {}
        if bs.get("8") is not None and bs.get("24") is not None and bs["8"] - bs["24"] > 0.1:
            coarse_helps.append(k)

    # Did effort normalization matter? (it cannot, where exposure is flat)
    effort_moves = []
    for k, v in testable.items():
        d = (v.get("effort_normalization", {}) or {}).get("delta")
        if d is not None and abs(d) > 0.05:
            effort_moves.append(k)

    sparse_stations = sorted(per_station_detections, key=per_station_detections.get)[:2]

    # Honest top line: the bar is cleared only if EVERY testable kernel already clears it
    # with no noise-bound and no confounded kernels left.
    can_clear = bool(cleared) and not (artifact_kernels or coverage_kernels or hetero_kernels)
    if can_clear:
        verdict = "Cross-station consistency is met for every testable kernel at the current data volume."
    else:
        bits = []
        if artifact_kernels:
            bits.append(
                f"{', '.join(artifact_kernels)} are noise-bound (within-station split-half reliability "
                f"is itself below 0.5, so the cross-station correlation cannot exceed noise)"
            )
        if coverage_kernels:
            bits.append(
                f"{', '.join(coverage_kernels)} is reproducible within a station but the stations span "
                f"different parts of the cycle (observation-window confound), so its low correlation is "
                f"NOT demonstrated biological heterogeneity"
            )
        if hetero_kernels:
            bits.append(
                f"{', '.join(hetero_kernels)} shows reproducible per-station shapes that genuinely differ "
                f"(model with a station random effect, do not force to one kernel)"
            )
        verdict = (
            "NO -- the 0.5 cross-station bar cannot be cleared honestly with the current 4-station data. "
            + "; ".join(bits)
            + ". The path is more detections per station (3-node production ingest, Agent D) + coarser "
            "PSTH bins + partial pooling, re-judged later; not a tuned threshold and not forced consistency."
        )

    return {
        "can_clear_0p5_bar_honestly": bool(can_clear),
        "verdict": verdict,
        "noise_artifact_kernels": artifact_kernels,
        "coverage_confounded_kernels": coverage_kernels,
        "genuine_heterogeneity_kernels": hetero_kernels,
        "kernels_clearing_bar": cleared,
        "coarser_bins_help_kernels": coarse_helps,
        "effort_normalization_moves_kernels": effort_moves,
        "effort_assumed_continuous": effort_assumed,
        "sparsest_stations": sparse_stations,
        "actions": [
            "Aggregate the per-station PSTH at coarser phase resolution (8-12 bins) with a minimum "
            "per-bin count, instead of 24 bins, so empty-bin -log floors stop dominating the correlation.",
            "Raise per-station detection volume via the 3-node production ingest (Agent D) before "
            "re-judging the bar; north_san_juan_channel (~34) and andrews_bay are far too sparse for a "
            "24-bin PSTH.",
            "Score cross-station consistency against the JOINT fitted kernel with a station random "
            "effect (partial pooling / shrinkage), reporting the split-half reliability as the ceiling, "
            "rather than correlating raw per-station marginals.",
            "When Agent A's modeling/effort.py lands, re-run with the real log E offset; here effort "
            "normalization is a near-no-op because exposure is flat wherever station_uptime is absent.",
            "If, after more data, a kernel's reproducible shape still differs across stations, report it "
            "as genuine heterogeneity (station random effect), not a failed gate -- do not force consistency.",
        ],
    }


def _write(report: Dict[str, object]) -> Path:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return REPORT_PATH


if __name__ == "__main__":
    rep = run()
    path = _write(rep)
    if rep.get("status") != "ok":
        print(f"cross_station_consistency: {rep.get('status')} -- {rep.get('reason')} -> {path}")
    else:
        print(f"cross_station_consistency: stations={rep['n_stations']} "
              f"detections={rep['per_station_detections']} -> {path}")
        base = (rep.get("baseline_cross_station_consistency") or {}).get("mean_psth_correlation", {})
        print(f"  baseline per-kernel mean PSTH corr: {base}")
        for cov, v in rep["kernels"].items():
            if isinstance(v, dict) and v.get("testable"):
                sh = v.get("split_half_reliability", {}).get("mean")
                print(f"  {cov}: cross={v['mean_psth_correlation']} split_half_ceiling={sh} "
                      f"-> {v['verdict'][:60]}")
        print(f"  recommendation: {rep['recommendation']['verdict'][:100]}")
