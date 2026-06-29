"""Build the (station, time-bin) count table the estimator consumes.

Ported in spirit from INDYsim ``prepare_binned_data.py``. Each row is one
station-hour (or ``bin_hours``-wide bin): the detection count ``y``, the
observation effort ``exposure`` (the ``log E`` offset), and the cyclic covariate
phases (diel, tide, lunar, season) at the bin centre.

The critical orcast-specific change over INDYsim is the effort term: INDYsim
assumes uniform exposure, but hydrophone uptime is not uniform, so ``exposure``
is built from the ``station_uptime`` series when available. When uptime is
absent the bin assumes continuous coverage and the frame flags
``effort_assumed_continuous`` so the honesty report can disclose it.
"""

from __future__ import annotations

import math
from datetime import timezone
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.aws_backend import covariates
from .ais_noise import detectability_factor
from .effort import exposure_for_bins, uptime_binds, FALLBACK_CONTINUOUS
from .timeutil import from_hours, to_hours

# Archipelago centroid, used only when a station has no coordinates at all.
_DEFAULT_LAT = 48.5
_DEFAULT_LNG = -123.0


def event_times_hours(records: List[dict], confirmed_only: bool = False) -> np.ndarray:
    """Sorted detection times (hours since epoch) -- the per-station spike train."""
    out: List[float] = []
    for r in records:
        if confirmed_only and not r.get("confirmed"):
            continue
        t = r.get("t")
        if t is None:
            continue
        try:
            out.append(to_hours(t))
        except (ValueError, TypeError):
            continue
    return np.array(sorted(out), dtype=float)


def _station_coords(records: List[dict], override: Optional[Tuple[float, float]]) -> Tuple[float, float]:
    if override is not None:
        return override
    lats = [r["latitude"] for r in records if r.get("latitude") is not None]
    lngs = [r["longitude"] for r in records if r.get("longitude") is not None]
    if lats and lngs:
        return float(np.median(lats)), float(np.median(lngs))
    return _DEFAULT_LAT, _DEFAULT_LNG


def _uptime_step(records: Optional[List[dict]]) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """Sorted (time_hours, up) samples for a carry-forward step function."""
    if not records:
        return None
    pairs = []
    for r in records:
        t = r.get("t")
        if t is None:
            continue
        up = r.get("up")
        if up is None:
            up = 1 if r.get("status") == "online" else 0
        try:
            pairs.append((to_hours(t), float(up)))
        except (ValueError, TypeError):
            continue
    if not pairs:
        return None
    pairs.sort()
    return np.array([p[0] for p in pairs]), np.array([p[1] for p in pairs])


def _exposure_for_bin(center: float, bin_hours: float, step: Optional[Tuple[np.ndarray, np.ndarray]]) -> float:
    """Effort (hours) in a bin: bin width scaled by carry-forward up-status."""
    if step is None:
        return bin_hours  # assume continuous coverage (flagged on the frame)
    times, ups = step
    idx = int(np.searchsorted(times, center, side="right") - 1)
    status = float(ups[idx]) if idx >= 0 else 1.0  # assume up before first poll
    return bin_hours * status


def season_phase_hours(center_hours: float) -> float:
    """Day-of-year mapped to ``[0, 1)`` (Jan 1 == 0). Leap years use 366.

    The single offline source of the season phase; ``fit_kernels`` imports this
    so the design-build and the serving-side intensity share one definition.
    """
    dt = from_hours(center_hours)
    start = dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    days_in_year = 366.0 if _is_leap(dt.year) else 365.0
    elapsed = (dt - start).total_seconds() / 86400.0
    return (elapsed / days_in_year) % 1.0


# Backwards-compatible private alias (kept so existing callers/imports do not break).
_season_phase_hours = season_phase_hours


def _is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def phase_coverage(phase_values, n_bins: int = 12) -> float:
    """Fraction of ``n_bins`` equal-width phase bins that contain >=1 observation.

    A cyclic covariate whose observed phase support is incomplete (e.g. a season
    phase seen only over part of the annual cycle) cannot have its full kernel
    identified; this measures how much of the cycle the data actually span so the
    caller can refuse to fit/serve an extrapolated kernel.
    """
    phase = np.asarray(list(phase_values), dtype=float)
    phase = phase[np.isfinite(phase)]
    if phase.size == 0:
        return 0.0
    phase = phase % 1.0
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(phase, edges[1:-1]), 0, n_bins - 1)
    return float(np.unique(idx).size) / float(n_bins)


def build_design(
    acoustic_by_station: Dict[str, List[dict]],
    uptime_by_station: Optional[Dict[str, List[dict]]] = None,
    tide_phase=None,
    bin_hours: float = 1.0,
    station_coords: Optional[Dict[str, Tuple[float, float]]] = None,
    confirmed_only: bool = False,
    min_exposure: float = 1e-6,
    noise_by_station: Optional[Dict[str, Tuple[np.ndarray, np.ndarray]]] = None,
    ais_kappa: float = 0.0,
    linear_by_station: Optional[Dict[str, Dict[str, Tuple[np.ndarray, np.ndarray]]]] = None,
) -> pd.DataFrame:
    """Assemble the binned design matrix across all stations.

    Returns a DataFrame with columns ``station, t, bin_start, y, exposure,
    log_exposure, diel, lunar, season`` and ``tide`` (NaN when no tidal series is
    supplied). Rows with non-positive exposure are dropped.

    TA3 effort: when ``noise_by_station`` (a per-station AIS proximity-noise index)
    and ``ais_kappa > 0`` are supplied, the per-bin exposure is multiplied by the
    detectability factor ``D_ais`` (vessel-noise masking is an effort/exposure
    term, B.2; zero added presence parameters). The default (``None`` / ``0.0``)
    is a strict no-op, so the design is byte-identical until an operator-gated AIS
    index is wired.

    TB2/TB5 aperiodic covariates: ``linear_by_station`` maps
    ``station -> covname -> (sorted_times_hours, values)``; each covariate is
    linearly interpolated onto the bin centres and emitted as an extra column
    (``NaN`` outside the supplied span, so the estimator's finite-guard skips it
    exactly like the ``tide`` NaN path). The default (``None``) is a strict no-op;
    the feed is operator-gated (no reachable SST/currents source here), so this is
    the landed-but-inert join used to MEASURE a covariate once its feed lands.
    """
    uptime_by_station = uptime_by_station or {}
    station_coords = station_coords or {}
    rows: List[dict] = []
    effort_assumed = True  # flips false as soon as any station has real uptime

    for station, records in acoustic_by_station.items():
        events = event_times_hours(records, confirmed_only=confirmed_only)
        if events.size == 0:
            continue

        lat, lng = _station_coords(records, station_coords.get(station))

        # Bin edges spanning the detections, snapped to the bin grid.
        lo = math.floor(events.min() / bin_hours) * bin_hours
        hi = math.ceil(events.max() / bin_hours) * bin_hours + bin_hours
        edges = np.arange(lo, hi + bin_hours, bin_hours)
        counts, _ = np.histogram(events, bins=edges)
        centers = edges[:-1] + bin_hours / 2.0

        # Per-bin observation effort (effort-hours = bin_hours * E_frac) from the
        # station_uptime stream via modeling.effort, which resolves the
        # rpi_*<->acoustic station-key namespaces a naive uptime.get(station)
        # misses. With FALLBACK_CONTINUOUS and no binding uptime this returns
        # bin_hours (E_frac=1), so it is a strict no-op vs the old scalar path.
        exposure_bins = exposure_for_bins(
            uptime_by_station, station, centers,
            bin_hours=bin_hours, fallback=FALLBACK_CONTINUOUS, detection_times=events,
        )
        # TA3: multiply in the AIS detectability factor (B.2 effort term). No-op
        # when no index / kappa<=0 (returns all-ones), so the default is unchanged.
        if noise_by_station and ais_kappa > 0:
            exposure_bins = exposure_bins * detectability_factor(
                noise_by_station, station, centers, kappa=ais_kappa,
            )
        # effort_assumed_continuous is honest: it flips false only when a uptime
        # series both EXISTS and OVERLAPS this station's detection window (a
        # series that exists but is temporally disjoint does not bind).
        if uptime_binds(uptime_by_station, station, detection_times=events):
            effort_assumed = False

        # Aperiodic covariate values interpolated onto the bin centres (NaN outside
        # the supplied span). No-op when no feed is wired for this station.
        lin_cols: Dict[str, np.ndarray] = {}
        if linear_by_station and station in linear_by_station:
            for cov_name, series in linear_by_station[station].items():
                ct, cv = series
                ct = np.asarray(ct, dtype=float)
                cv = np.asarray(cv, dtype=float)
                if ct.size == 0:
                    lin_cols[cov_name] = np.full(centers.shape, math.nan)
                    continue
                vals = np.interp(centers, ct, cv, left=math.nan, right=math.nan)
                lin_cols[cov_name] = vals

        for i, (center, y, exposure) in enumerate(zip(centers, counts, exposure_bins)):
            exposure = float(exposure)
            if exposure <= min_exposure:
                continue
            dt = from_hours(center)
            row = {
                "station": station,
                "t": float(center),
                "bin_start": from_hours(center - bin_hours / 2.0).isoformat(),
                "y": float(y),
                "exposure": exposure,
                "log_exposure": float(np.log(exposure)),
                "diel": float(covariates.diel_phase(dt, lng)),
                "lunar": float(covariates.lunar_phase(dt)["phase"]),
                "season": float(season_phase_hours(center)),
                "tide": float(tide_phase.phase(center)) if tide_phase is not None else math.nan,
            }
            for cov_name, vals in lin_cols.items():
                row[cov_name] = float(vals[i])
            rows.append(row)

    df = pd.DataFrame(rows)
    df.attrs["bin_hours"] = bin_hours
    df.attrs["effort_assumed_continuous"] = effort_assumed
    df.attrs["confirmed_only"] = confirmed_only
    return df
