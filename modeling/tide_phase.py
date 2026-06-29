"""Tidal phase from a NOAA current or water-level series.

The tidal cyclic kernel is aligned to a repeating stimulus event. Following
CALIBRATION_STUDIES.md the anchor is the *flood-current onset* (slack-to-flood),
detected as an upward zero-crossing of the signed current velocity
(``env_currents`` ``Velocity_Major``, knots). When only water level is available
the anchor falls back to the rising mean-crossing (water level has no sign).

The phase at a time ``t`` is the fraction of the way from the most recent onset
to the next, in ``[0, 1)``. Outside the observed span it extrapolates with the
mean detected period (or the ~12.42 h semidiurnal period as a last resort).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

import numpy as np

from .timeutil import to_hours
from .tide_harmonic import HarmonicTide

# Mean semidiurnal tidal period (principal lunar M2), hours.
_M2_PERIOD_HOURS = 12.4206


class TidalPhase:
    """Maps timestamps to a tidal phase in ``[0, 1)`` anchored at flood onset."""

    def __init__(self, onsets_hours: Sequence[float], period_hours: float,
                 times_hours: Optional[np.ndarray] = None, values: Optional[np.ndarray] = None) -> None:
        self.onsets = np.asarray(sorted(onsets_hours), dtype=float)
        self.period = float(period_hours) if period_hours > 0 else _M2_PERIOD_HOURS
        self._t = times_hours
        self._v = values

    @classmethod
    def from_records(cls, records: List[dict], signed: Optional[bool] = None) -> "TidalPhase":
        """Build from ``{t, value}`` records (currents or water level).

        ``signed`` forces sign handling; when ``None`` it is inferred (a series
        with negative values is treated as signed current velocity).
        """
        pairs = []
        for r in records:
            t = r.get("t")
            v = r.get("value")
            if t is None or v is None:
                continue
            try:
                pairs.append((to_hours(t), float(v)))
            except (ValueError, TypeError):
                continue
        pairs.sort()
        if len(pairs) < 3:
            return cls(onsets_hours=[], period_hours=_M2_PERIOD_HOURS)

        times = np.array([p[0] for p in pairs])
        values = np.array([p[1] for p in pairs])
        if signed is None:
            signed = bool(np.any(values < 0))

        series = values if signed else values - np.mean(values)
        onsets = _upward_zero_crossings(times, series)
        period = float(np.median(np.diff(onsets))) if onsets.size >= 2 else _M2_PERIOD_HOURS
        return cls(onsets_hours=onsets, period_hours=period, times_hours=times, values=values)

    def phase(self, time_hours: float) -> float:
        """Tidal phase in ``[0, 1)`` at ``time_hours`` (hours since epoch)."""
        if self.onsets.size == 0:
            # No onsets detected: fall back to a fixed-period clock from t=0.
            return (time_hours % self.period) / self.period

        idx = int(np.searchsorted(self.onsets, time_hours, side="right") - 1)
        if idx < 0:
            # Before the first onset: extrapolate backwards by the period.
            delta = (self.onsets[0] - time_hours) % self.period
            return (self.period - delta) % self.period / self.period
        if idx >= self.onsets.size - 1:
            # After the last onset: extrapolate forward by the period.
            return ((time_hours - self.onsets[idx]) % self.period) / self.period
        span = self.onsets[idx + 1] - self.onsets[idx]
        span = span if span > 0 else self.period
        return float((time_hours - self.onsets[idx]) / span)

    def phases(self, times_hours: Sequence[float]) -> np.ndarray:
        return np.array([self.phase(float(t)) for t in times_hours], dtype=float)

    def value_at(self, time_hours: float) -> Optional[float]:
        """Interpolated raw series value at a time (for STA on continuous tide)."""
        if self._t is None or self._v is None or self._t.size == 0:
            return None
        return float(np.interp(time_hours, self._t, self._v))


class HarmonicTidalPhase:
    """Tidal phase from a least-squares harmonic fit (M2/S2/N2/K1/O1).

    ``TidalPhase`` interpolates phase between flood onsets detected in the raw
    current series, so where the series is sparse the phase only spans part of
    the cycle (the L2 coverage exclusion). ``HarmonicTidalPhase`` fits the fixed
    astronomical constituents once and predicts phase for ANY timestamp, so tide
    phase is defined across the whole acoustic span. It exposes the same
    interface as ``TidalPhase`` (``phase``/``phases``/``value_at``/``onsets``)
    so it is a drop-in for the design build and the served intensity.
    """

    def __init__(
        self,
        model: HarmonicTide,
        onsets_hours: Sequence[float],
        period_hours: float,
        times_hours: Optional[np.ndarray] = None,
        values: Optional[np.ndarray] = None,
    ) -> None:
        self.model = model
        self.onsets = np.asarray(sorted(onsets_hours), dtype=float)
        self.period = float(period_hours) if period_hours > 0 else _M2_PERIOD_HOURS
        self._t = times_hours
        self._v = values
        self.reconstruction_r2 = float(getattr(model, "reconstruction_r2", float("nan")))

    @classmethod
    def from_records(cls, records: List[dict], min_samples: int = 24) -> Optional["HarmonicTidalPhase"]:
        """Fit the harmonic model from ``{t, value}`` current records.

        Returns ``None`` when there are too few samples to fit the constituents,
        so the caller can fall back to the onset-based ``TidalPhase``.
        """
        pairs = []
        for r in records:
            t = r.get("t")
            v = r.get("value")
            if t is None or v is None:
                continue
            try:
                pairs.append((to_hours(t), float(v)))
            except (ValueError, TypeError):
                continue
        pairs.sort()
        if len(pairs) < min_samples:
            return None
        times = np.array([p[0] for p in pairs], dtype=float)
        values = np.array([p[1] for p in pairs], dtype=float)
        model = HarmonicTide().fit(times, values)
        # Dense onset detection from the reconstruction, for honest reporting of
        # tide_onsets_detected (not used for phase, which comes from the model).
        dense = np.arange(float(times.min()), float(times.max()), 0.5)
        if dense.size >= 2:
            recon = model.predict(dense)
            onsets = _upward_zero_crossings(dense, recon - float(np.mean(recon)))
        else:
            onsets = np.array([], dtype=float)
        period = float(np.median(np.diff(onsets))) if onsets.size >= 2 else _M2_PERIOD_HOURS
        return cls(model, onsets, period, times, values)

    def phase(self, time_hours: float) -> float:
        return float(self.model.phase([float(time_hours)])[0])

    def phases(self, times_hours: Sequence[float]) -> np.ndarray:
        return np.asarray(self.model.phase([float(t) for t in times_hours]), dtype=float)

    def value_at(self, time_hours: float) -> Optional[float]:
        return float(self.model.predict([float(time_hours)])[0])


def _upward_zero_crossings(times: np.ndarray, series: np.ndarray) -> np.ndarray:
    """Times where ``series`` crosses zero going negative -> positive."""
    onsets: List[float] = []
    for i in range(1, series.size):
        a, b = series[i - 1], series[i]
        if a <= 0.0 < b:
            # Linear interpolation of the crossing time.
            frac = -a / (b - a) if (b - a) != 0 else 0.0
            onsets.append(float(times[i - 1] + frac * (times[i] - times[i - 1])))
    return np.array(onsets, dtype=float)
