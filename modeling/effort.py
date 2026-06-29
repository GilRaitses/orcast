"""Per-station observation effort / ``log E`` model for the conditional intensity.

The forecast kernel model is a point process whose log-rate carries an explicit
observation-effort offset (``FORECAST_KERNELS.md``):

    log lambda(station, t) = b0 + a_station + sum_j kernel_j(phase_j(t)) + log E(station, t)

``build_design`` (``modeling/design.py``) already puts an exposure column on the
binned design and uses ``log(exposure)`` as the GLM offset, but two things are
wrong today and this module fixes both, as a *pure, side-effect-free* API the
integrator wires in:

1. ``build_design`` looks up uptime by the **acoustic** station key
   (``haro_strait``, ``orcasound_lab``), while the ``station_uptime`` stream is
   keyed by hydrophone node id (``rpi_orcasound_lab``, ``rpi_north_sjc``, ...).
   The keys never match, so ``effort_assumed_continuous`` stays ``True`` and the
   offset is flat. :func:`resolve_uptime_records` / :func:`normalize_station_key`
   bridge the two namespaces.
2. ``_station_intensity_fn`` (``modeling/fit_kernels.py``), the conditional
   intensity that ``_time_rescaling_report`` integrates, **ignores effort
   entirely**: it returns ``exp(b0 + a_station + kernels)`` with no ``E(t)`` term.
   For an *observed* point process the conditional intensity is
   ``lambda_obs(t) = exp(b0 + kernels) * E(t)`` where ``E(t)`` is the relative
   instantaneous effort (1 = fully up, 0 = detector down). With ``E(t)`` absent,
   the time-rescaling integral accumulates hazard across detector-down gaps as if
   the silence were a modelled low rate, which biases the rescaled IEIs.
   :func:`station_log_effort` supplies the missing ``log E(t)`` on the
   integration grid so the integrator can multiply it back in.

What this module does NOT do (honesty, charter B.2/B.3): it never fabricates
uptime. Where the ``station_uptime`` stream does not cover the detection window,
or is constant within it, the effort offset is necessarily flat and the relevant
function says so via :func:`effort_summary` rather than inventing an effort
series. A detection-density proxy fallback is provided but is OFF by default and
is explicitly flagged as circular (it conditions effort on the very signal the
kernels model), so it must never be used to earn confidence.

Units, to keep the two call sites consistent:

* :func:`exposure_for_bins` returns **effort-hours per bin** (``bin_hours *
  E_frac``), matching the existing ``exposure`` column whose offset is
  ``log(exposure)``. This is what ``build_design`` consumes.
* :func:`station_log_effort` returns **log of the relative effort fraction**
  ``E_frac in (0, 1]`` (``log E_frac``, so 0 when fully up), matching the
  multiplicative ``E(t)`` correction the intensity function consumes. The
  per-bin ``log(exposure)`` differs from this only by the constant
  ``log(bin_hours)``, which is absorbed into the fitted intercept and therefore
  must NOT be re-added inside the intensity function.

Pure: no I/O, no S3, no global state. ``numpy`` + stdlib + ``modeling.timeutil``
only.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np

from .timeutil import to_hours

# Floor on the relative effort fraction so ``log E`` stays finite when a detector
# is reported down. ``log(1e-3) ~= -6.9``, which makes the effort-corrected
# intensity ~0 across a verified-down interval (hazard effectively does not
# accumulate there) without producing ``-inf``.
DEFAULT_MIN_EFFORT_FRACTION = 1e-3

# Fallback policies when no binding uptime covers a requested time.
FALLBACK_CONTINUOUS = "continuous"          # E_frac = 1 everywhere (today's behaviour, flagged)
FALLBACK_OBSERVED_WINDOW = "observed_window"  # E_frac = 1 within the detection span, floor outside
FALLBACK_DETECTION_DENSITY = "detection_density"  # CIRCULAR proxy, off by default; never for confidence
_FALLBACKS = (FALLBACK_CONTINUOUS, FALLBACK_OBSERVED_WINDOW, FALLBACK_DETECTION_DENSITY)

# Explicit aliases from the uptime-stream node ids / human names to the acoustic
# station keys used by the fit. Anything not listed falls through to the generic
# prefix/normalisation rule in :func:`normalize_station_key`.
_STATION_ALIASES: Dict[str, str] = {
    "rpi_orcasound_lab": "orcasound_lab",
    "orcasound lab": "orcasound_lab",
    "rpi_north_sjc": "north_san_juan_channel",
    "north san juan channel": "north_san_juan_channel",
    "rpi_andrews_bay": "andrews_bay",
    "andrews bay": "andrews_bay",
}

UptimeLike = Union[Dict[str, List[dict]], Sequence[dict], None]


def normalize_station_key(name: Optional[str]) -> str:
    """Canonicalise a station id/name to the acoustic-detection namespace.

    Maps the uptime stream's node ids and human labels onto the acoustic keys:
    ``rpi_orcasound_lab`` / ``"Orcasound Lab"`` -> ``orcasound_lab``,
    ``rpi_north_sjc`` / ``"North San Juan Channel"`` -> ``north_san_juan_channel``,
    ``rpi_andrews_bay`` / ``"Andrews Bay"`` -> ``andrews_bay``. The mapping is
    explicit (``_STATION_ALIASES``) with a generic ``rpi_``/``das_`` prefix-strip
    and whitespace/punctuation normalisation as the fallback. There is no
    ``haro_strait`` uptime node, so ``haro_strait`` normalises to itself and
    resolves to no uptime (honest: the production stream has no uptime series).
    """
    if not name:
        return ""
    raw = str(name).strip().lower()
    if raw in _STATION_ALIASES:
        return _STATION_ALIASES[raw]
    collapsed = raw.replace("-", "_").replace(" ", "_")
    if collapsed in _STATION_ALIASES:
        return _STATION_ALIASES[collapsed]
    for prefix in ("rpi_", "das_", "hydrophone_"):
        if collapsed.startswith(prefix):
            collapsed = collapsed[len(prefix):]
            break
    return _STATION_ALIASES.get(collapsed, collapsed)


def resolve_uptime_records(uptime: UptimeLike, station: str) -> Optional[List[dict]]:
    """Return the uptime record list for an acoustic ``station``, or ``None``.

    Accepts either a list of records already scoped to one station, or a
    ``{station_key: [records]}`` dict (as ``read_streams`` returns it). Dict
    lookup is by exact key first, then by :func:`normalize_station_key` on the
    dict keys, then by the human ``station`` label stored inside the records, so
    the ``rpi_*`` uptime namespace binds to the acoustic namespace.
    """
    if uptime is None:
        return None
    if isinstance(uptime, dict):
        recs = uptime.get(station)
        if recs:
            return list(recs)
        target = normalize_station_key(station)
        for key, candidate in uptime.items():
            if candidate and normalize_station_key(key) == target:
                return list(candidate)
        for candidate in uptime.values():
            if candidate and normalize_station_key(candidate[0].get("station")) == target:
                return list(candidate)
        return None
    records = list(uptime)
    return records or None


def _up_fraction(record: dict) -> Optional[float]:
    """Relative effort in ``[0, 1]`` from one uptime record.

    Prefers an explicit numeric ``up`` (the ingest writes ``1``/``0``; a future
    duty-cycle ingest could write a fraction), else maps ``status == 'online'``
    to 1 and any other status to 0.
    """
    up = record.get("up")
    if up is not None:
        try:
            return float(np.clip(float(up), 0.0, 1.0))
        except (TypeError, ValueError):
            pass
    status = record.get("status")
    if status is not None:
        return 1.0 if str(status).lower() == "online" else 0.0
    return None


def uptime_step(records: Optional[Sequence[dict]]) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """Sorted ``(times_hours, up_fraction)`` samples for a carry-forward step.

    Returns ``None`` when there is no usable sample. ``up_fraction`` is in
    ``[0, 1]``. Mirrors ``design._uptime_step`` but yields a fraction (so a
    future fractional duty cycle is representable) and is importable on its own.
    """
    if not records:
        return None
    pairs: List[Tuple[float, float]] = []
    for r in records:
        t = r.get("t")
        if t is None:
            continue
        frac = _up_fraction(r)
        if frac is None:
            continue
        try:
            pairs.append((to_hours(t), frac))
        except (ValueError, TypeError):
            continue
    if not pairs:
        return None
    pairs.sort()
    return np.array([p[0] for p in pairs], dtype=float), np.array([p[1] for p in pairs], dtype=float)


def _detection_density_fraction(
    times: np.ndarray,
    detection_times: np.ndarray,
    bandwidth_hours: float,
) -> np.ndarray:
    """Smoothed local detection rate normalised to its max, in ``[0, 1]``.

    CIRCULAR effort proxy: it conditions effort on the detections themselves, so
    it cannot legitimately de-bias the same detections. Provided only for the
    explicit, off-by-default ``detection_density`` fallback and never used to
    earn confidence.
    """
    if detection_times.size == 0:
        return np.zeros(times.shape, dtype=float)
    bw = max(float(bandwidth_hours), 1e-6)
    diffs = (times[:, None] - detection_times[None, :]) / bw
    dens = np.exp(-0.5 * diffs * diffs).sum(axis=1)
    peak = float(dens.max())
    if peak <= 0:
        return np.zeros(times.shape, dtype=float)
    return dens / peak


def relative_effort(
    times: Sequence[float],
    uptime: UptimeLike,
    station: str,
    *,
    fallback: str = FALLBACK_CONTINUOUS,
    detection_times: Optional[Sequence[float]] = None,
    min_effort: float = DEFAULT_MIN_EFFORT_FRACTION,
    density_bandwidth_hours: float = 6.0,
) -> np.ndarray:
    """Relative effort fraction ``E_frac in [min_effort, 1]`` at ``times`` (hours).

    When a uptime step covers a time, the carry-forward up-fraction is used
    (times before the first sample assume up=1, matching ``design``). When no
    uptime binds the requested time, the ``fallback`` policy applies:

    * ``continuous`` (default): ``E_frac = 1`` (flat; the honest "assumed
      continuous" behaviour, surfaced by :func:`effort_summary`).
    * ``observed_window``: ``E_frac = 1`` inside ``[min(detection_times),
      max(detection_times)]`` and the floor outside it. Bounds exposure to the
      span the station actually produced data, without inventing sub-window
      uptime. Requires ``detection_times``.
    * ``detection_density``: the circular proxy above. Requires
      ``detection_times``; never use it to credit a fit.

    The result is clipped to ``[min_effort, 1]`` so the downstream ``log E`` is
    finite.
    """
    if fallback not in _FALLBACKS:
        raise ValueError(f"fallback must be one of {_FALLBACKS}, got {fallback!r}")
    t = np.atleast_1d(np.asarray(times, dtype=float))
    step = uptime_step(resolve_uptime_records(uptime, station))

    if step is not None:
        st_t, st_up = step
        idx = np.searchsorted(st_t, t, side="right") - 1
        frac = np.where(idx >= 0, st_up[np.clip(idx, 0, st_up.size - 1)], 1.0)
        return np.clip(frac.astype(float), min_effort, 1.0)

    if fallback == FALLBACK_CONTINUOUS:
        return np.ones(t.shape, dtype=float)

    dets = np.asarray(detection_times if detection_times is not None else [], dtype=float)
    if fallback == FALLBACK_OBSERVED_WINDOW:
        if dets.size == 0:
            return np.ones(t.shape, dtype=float)
        inside = (t >= float(dets.min())) & (t <= float(dets.max()))
        return np.where(inside, 1.0, min_effort).astype(float)

    # FALLBACK_DETECTION_DENSITY
    frac = _detection_density_fraction(t, dets, density_bandwidth_hours)
    return np.clip(frac, min_effort, 1.0)


def station_log_effort(
    uptime: UptimeLike,
    station: str,
    grid_times: Sequence[float],
    *,
    fallback: str = FALLBACK_CONTINUOUS,
    detection_times: Optional[Sequence[float]] = None,
    min_effort: float = DEFAULT_MIN_EFFORT_FRACTION,
    density_bandwidth_hours: float = 6.0,
) -> np.ndarray:
    """``log E(t)`` (relative effort) at ``grid_times`` for the conditional intensity.

    This is the term ``_station_intensity_fn`` is missing: the integrator adds it
    to the kernel log-rate (equivalently multiplies the intensity by
    ``exp(station_log_effort(...))``). Returns ``0.0`` where the station is fully
    up (so it is a no-op there) and a large negative value across verified
    downtime. ``grid_times`` are hours since epoch (the pipeline convention).
    """
    frac = relative_effort(
        grid_times, uptime, station,
        fallback=fallback, detection_times=detection_times,
        min_effort=min_effort, density_bandwidth_hours=density_bandwidth_hours,
    )
    return np.log(np.clip(frac, min_effort, 1.0))


def exposure_for_bins(
    uptime: UptimeLike,
    station: str,
    bin_centers: Sequence[float],
    *,
    bin_hours: float = 1.0,
    fallback: str = FALLBACK_CONTINUOUS,
    detection_times: Optional[Sequence[float]] = None,
    min_effort: float = DEFAULT_MIN_EFFORT_FRACTION,
    density_bandwidth_hours: float = 6.0,
) -> np.ndarray:
    """Effort-hours per bin (``bin_hours * E_frac``) for ``build_design``'s offset.

    Same semantics as the existing ``exposure`` column (offset ``log(exposure)``),
    but with cross-namespace uptime binding (:func:`resolve_uptime_records`) and
    the documented fallbacks. Bins whose effort floors out are returned at
    ``bin_hours * min_effort`` (kept positive so ``log`` is finite); the caller's
    ``min_exposure`` drop still applies downstream.
    """
    frac = relative_effort(
        bin_centers, uptime, station,
        fallback=fallback, detection_times=detection_times,
        min_effort=min_effort, density_bandwidth_hours=density_bandwidth_hours,
    )
    return float(bin_hours) * frac


def uptime_binds(uptime: UptimeLike, station: str, detection_times: Optional[Sequence[float]] = None) -> bool:
    """Does a uptime series exist for ``station`` AND overlap its detection window?

    A series that exists but does not temporally overlap the detections (e.g. a
    2026 uptime window over 2020-2021 detections) does NOT bind: every detection
    bin falls before the first sample and is treated as up=1, i.e. continuous.
    """
    step = uptime_step(resolve_uptime_records(uptime, station))
    if step is None:
        return False
    if detection_times is None:
        return True
    dets = np.asarray(detection_times, dtype=float)
    if dets.size == 0:
        return False
    st_t, _ = step
    return bool((st_t.min() <= dets.max()) and (st_t.max() >= dets.min()))


def effort_summary(
    uptime: UptimeLike,
    acoustic_by_station: Dict[str, List[dict]],
    *,
    bin_hours: float = 1.0,
    fallback: str = FALLBACK_CONTINUOUS,
    min_effort: float = DEFAULT_MIN_EFFORT_FRACTION,
) -> Dict[str, object]:
    """Per-station effort diagnostic over the real detection windows.

    For each acoustic station reports whether a uptime series resolves, whether
    it overlaps the detection window, the carry-forward up fraction, and the
    resulting ``log E`` statistics on the per-bin grid. ``effort_assumed_continuous``
    is true for the station when nothing binds. This is the honest "actual
    numbers" surface; it fabricates nothing.
    """
    from .design import event_times_hours

    import math

    per_station: Dict[str, Dict[str, object]] = {}
    any_binds = False
    for station, records in acoustic_by_station.items():
        events = event_times_hours(records)
        if events.size == 0:
            continue
        lo = math.floor(events.min() / bin_hours) * bin_hours
        hi = math.ceil(events.max() / bin_hours) * bin_hours + bin_hours
        edges = np.arange(lo, hi + bin_hours, bin_hours)
        centers = edges[:-1] + bin_hours / 2.0

        resolved = resolve_uptime_records(uptime, station)
        step = uptime_step(resolved)
        binds = uptime_binds(uptime, station, detection_times=events)
        if binds:
            any_binds = True

        exposure = exposure_for_bins(
            uptime, station, centers, bin_hours=bin_hours,
            fallback=fallback, detection_times=events, min_effort=min_effort,
        )
        log_e = station_log_effort(
            uptime, station, centers,
            fallback=fallback, detection_times=events, min_effort=min_effort,
        )
        frac = exposure / float(bin_hours)

        entry: Dict[str, object] = {
            "n_detections": int(events.size),
            "n_bins": int(centers.size),
            "uptime_resolved": resolved is not None,
            "uptime_binds_window": bool(binds),
            "effort_assumed_continuous": not bool(binds),
            "mean_effort_fraction": float(frac.mean()),
            "min_effort_fraction": float(frac.min()),
            "max_effort_fraction": float(frac.max()),
            "frac_bins_down": float(np.mean(frac < 1.0 - 1e-9)),
            "log_effort_mean": float(log_e.mean()),
            "log_effort_min": float(log_e.min()),
            "log_effort_max": float(log_e.max()),
            "log_effort_std": float(log_e.std()),
            "log_effort_degenerate": bool(log_e.std() < 1e-9),
        }
        if resolved is not None:
            entry["n_uptime_samples"] = int(len(resolved))
            if step is not None:
                st_t, st_up = step
                entry["uptime_up_fraction_mean"] = float(st_up.mean())
                entry["uptime_constant_in_window"] = bool(st_up.std() < 1e-9)
        per_station[station] = entry

    return {
        "fallback": fallback,
        "bin_hours": float(bin_hours),
        "min_effort_fraction": float(min_effort),
        "any_station_uptime_binds": bool(any_binds),
        "per_station": per_station,
    }
