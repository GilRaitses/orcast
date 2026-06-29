"""Detection-triggered average (reverse correlation) for continuous covariates.

Ported from INDYsim ``compute_reverse_correlation.py``. For covariates that are
continuous rather than evented (current speed, tide height, water temperature),
the detection-triggered average is the mean covariate trajectory in a window
around each detection; under standard assumptions it recovers the linear kernel.
A shuffled baseline (random detection times) gives a per-lag z-score and null.

Known limitation (see docs/methodology/INDYSIM_AUDIT.md): this is the *un-whitened*
STA. When covariates are correlated (tide and current co-vary) a whitened STA /
spike-triggered covariance is needed to separate them; that is tracked as
follow-up, not implemented here.
"""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np


def detection_triggered_average(
    event_times: np.ndarray,
    cov_times: np.ndarray,
    cov_values: np.ndarray,
    lags: np.ndarray,
) -> np.ndarray:
    """Mean covariate value at ``event_time - lag`` across detections, per lag."""
    event_times = np.asarray(event_times, dtype=float)
    cov_times = np.asarray(cov_times, dtype=float)
    cov_values = np.asarray(cov_values, dtype=float)
    lags = np.asarray(lags, dtype=float)
    if event_times.size == 0:
        return np.full(lags.shape, np.nan)

    sta = np.empty(lags.shape)
    for i, lag in enumerate(lags):
        sampled = np.interp(event_times - lag, cov_times, cov_values)
        sta[i] = float(np.mean(sampled))
    return sta


def shuffled_baseline(
    n_events: int,
    cov_times: np.ndarray,
    cov_values: np.ndarray,
    lags: np.ndarray,
    n_shuffles: int = 200,
    rng: Optional[np.random.Generator] = None,
) -> Dict[str, np.ndarray]:
    """Mean/std STA under random detection times (the null), per lag."""
    rng = rng or np.random.default_rng()
    cov_times = np.asarray(cov_times, dtype=float)
    t_lo, t_hi = cov_times.min(), cov_times.max()

    draws = np.empty((n_shuffles, lags.size))
    for s in range(n_shuffles):
        fake = rng.uniform(t_lo, t_hi, size=n_events)
        draws[s] = detection_triggered_average(fake, cov_times, cov_values, lags)
    return {"mean": draws.mean(axis=0), "std": draws.std(axis=0)}


def reverse_correlation(
    event_times: np.ndarray,
    cov_times: np.ndarray,
    cov_values: np.ndarray,
    lags: np.ndarray,
    n_shuffles: int = 200,
    rng: Optional[np.random.Generator] = None,
) -> Dict[str, object]:
    """STA with a shuffled-baseline z-score per lag (significant where |z| large)."""
    event_times = np.asarray(event_times, dtype=float)
    lags = np.asarray(lags, dtype=float)
    sta = detection_triggered_average(event_times, cov_times, cov_values, lags)
    null = shuffled_baseline(event_times.size, cov_times, cov_values, lags,
                             n_shuffles=n_shuffles, rng=rng)
    std = np.where(null["std"] > 0, null["std"], np.nan)
    z = (sta - null["mean"]) / std
    return {
        "lags": lags,
        "sta": sta,
        "null_mean": null["mean"],
        "null_std": null["std"],
        "z": z,
        "max_abs_z": float(np.nanmax(np.abs(z))) if z.size else 0.0,
    }
