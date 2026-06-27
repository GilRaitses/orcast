"""Harmonic tide predictor for current-like time series.

This fits a fixed constituent basis (M2/S2/N2/K1/O1 plus mean) by least squares
and reports reconstruction R^2 as a basic numerical-sanity check. It is a
harmonic predictor, not observed current measurements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple

import numpy as np


DEFAULT_CONSTITUENT_PERIODS_HOURS: Dict[str, float] = {
    "M2": 12.4206,
    "S2": 12.0,
    "N2": 12.6583,
    "K1": 23.9345,
    "O1": 25.8193,
}


@dataclass(frozen=True)
class Constituent:
    name: str
    period_hours: float


class HarmonicTide:
    """Least-squares harmonic tide model with fixed astronomical periods."""

    def __init__(self, periods_hours: Dict[str, float] | None = None) -> None:
        periods = dict(periods_hours or DEFAULT_CONSTITUENT_PERIODS_HOURS)
        if "M2" not in periods:
            raise ValueError("HarmonicTide requires an M2 constituent for phase output.")
        self._constituents: Tuple[Constituent, ...] = tuple(
            Constituent(name=k, period_hours=float(v)) for k, v in periods.items()
        )
        self._coef: np.ndarray | None = None
        self._reconstruction_r2: float = float("nan")

    @property
    def reconstruction_r2(self) -> float:
        return float(self._reconstruction_r2)

    def fit(self, times_hours: Iterable[float], values: Iterable[float]) -> "HarmonicTide":
        t = np.asarray(list(times_hours), dtype=float).reshape(-1)
        y = np.asarray(list(values), dtype=float).reshape(-1)
        if t.size != y.size:
            raise ValueError("times_hours and values must have the same length.")
        if t.size == 0:
            raise ValueError("fit requires at least one sample.")

        keep = np.isfinite(t) & np.isfinite(y)
        t = t[keep]
        y = y[keep]
        if t.size == 0:
            raise ValueError("fit received no finite samples.")

        X = self._design_matrix(t)
        coef, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        self._coef = coef

        y_hat = X @ coef
        ss_res = float(np.sum((y - y_hat) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        if ss_tot <= 0.0:
            self._reconstruction_r2 = 1.0 if ss_res <= 1e-12 else 0.0
        else:
            self._reconstruction_r2 = 1.0 - ss_res / ss_tot
        return self

    def predict(self, times_hours: Iterable[float]) -> np.ndarray:
        coef = self._require_fit()
        t = np.asarray(list(times_hours), dtype=float).reshape(-1)
        X = self._design_matrix(t)
        return X @ coef

    def phase(self, times_hours: Iterable[float]) -> np.ndarray:
        """Tidal phase in [0,1), derived from the fitted M2 constituent."""
        coef = self._require_fit()
        t = np.asarray(list(times_hours), dtype=float).reshape(-1)

        m2_index = next(i for i, c in enumerate(self._constituents) if c.name == "M2")
        a = float(coef[1 + 2 * m2_index])
        b = float(coef[1 + 2 * m2_index + 1])
        omega = 2.0 * np.pi / self._constituents[m2_index].period_hours

        amp = float(np.hypot(a, b))
        if amp <= 1e-12:
            return np.mod(t / self._constituents[m2_index].period_hours, 1.0)

        # With s(t) = a cos(wt) + b sin(wt), this maps phase=0 to an upward
        # mean crossing of the M2 component.
        delta = np.arctan2(a, b)
        return np.mod((omega * t + delta) / (2.0 * np.pi), 1.0)

    def _design_matrix(self, times_hours: np.ndarray) -> np.ndarray:
        cols = [np.ones(times_hours.shape[0], dtype=float)]
        for constituent in self._constituents:
            omega = 2.0 * np.pi / constituent.period_hours
            theta = omega * times_hours
            cols.append(np.cos(theta))
            cols.append(np.sin(theta))
        return np.column_stack(cols)

    def _require_fit(self) -> np.ndarray:
        if self._coef is None:
            raise RuntimeError("HarmonicTide must be fit before predict/phase.")
        return self._coef
