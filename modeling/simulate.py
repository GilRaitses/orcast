"""Generative engine: simulate detections from a known intensity.

Ported in spirit from INDYsim ``analytic_hazard.simulate_events_thinning``.
Used two ways:

* synthetic tests -- simulate a detection train from a *known* kernel so the
  estimator and GOF battery can be checked for recovery, and
* null data -- generate draws under a fitted model for posterior-predictive
  checks.

Times are in hours (the orcast pipeline convention); intensities are rates per
hour.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

import numpy as np

from .bases import evaluate_kernel


def thinning(
    intensity_fn: Callable[[float], float],
    t0: float,
    t1: float,
    lam_max: float,
    rng: Optional[np.random.Generator] = None,
) -> np.ndarray:
    """Simulate an inhomogeneous Poisson process on ``[t0, t1]`` by thinning.

    ``intensity_fn(t)`` must be <= ``lam_max`` everywhere on the interval.
    """
    rng = rng or np.random.default_rng()
    times: List[float] = []
    t = float(t0)
    while t < t1:
        t += rng.exponential(1.0 / lam_max)
        if t < t1 and rng.uniform() < intensity_fn(t) / lam_max:
            times.append(t)
    return np.array(times)


def binned_counts(rate_per_bin: np.ndarray, rng: Optional[np.random.Generator] = None) -> np.ndarray:
    """Draw Poisson counts given an expected count per bin (rate x effort)."""
    rng = rng or np.random.default_rng()
    return rng.poisson(np.clip(np.asarray(rate_per_bin, dtype=float), 0.0, None)).astype(float)


def rate_from_kernels(
    intercept: float,
    kernels: Dict[str, Dict[str, List[float]]],
    phases: Dict[str, np.ndarray],
) -> np.ndarray:
    """Compute ``lambda = exp(intercept + sum_k kernel_k(phase_k))`` per row.

    ``kernels`` maps a covariate name to ``{"cos": [...], "sin": [...]}`` and
    ``phases`` maps the same names to phase arrays in ``[0, 1)``.
    """
    n = len(next(iter(phases.values())))
    log_rate = np.full(n, float(intercept))
    for name, spec in kernels.items():
        phase = phases.get(name)
        if phase is None:
            continue
        log_rate = log_rate + evaluate_kernel(phase, spec.get("cos", []), spec.get("sin", []))
    return np.exp(log_rate)


def simulate_binned_dataset(
    intercept: float,
    kernels: Dict[str, Dict[str, List[float]]],
    phases: Dict[str, np.ndarray],
    exposure: np.ndarray,
    rng: Optional[np.random.Generator] = None,
) -> np.ndarray:
    """Simulate detection counts per bin: ``y ~ Poisson(lambda * exposure)``.

    Returns the drawn counts; the caller already holds the phases and exposure
    used to build them (the synthetic ground truth).
    """
    rate = rate_from_kernels(intercept, kernels, phases)
    return binned_counts(rate * np.asarray(exposure, dtype=float), rng=rng)
