"""Effort-normalized PSTH for a cyclic covariate (Level 1 estimate).

Ported from INDYsim ``generate_psth_comparison.py`` with the one change orcast
requires: the rate in each phase bin is the detection count divided by the
*observation effort* in that bin (summed ``exposure``), not by a constant frame
rate. Under non-uniform hydrophone uptime this is the difference between a curve
that reflects animal presence and one that reflects when we happened to listen.

The PSTH is the cheapest, most legible kernel estimate; it produces the
publishable rate-vs-phase tuning curve and is the marginal that the joint LNP
fit (Level 2) must agree with.
"""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np

from .validation.null_tests import modulation_depth, permutation_null

_EPS = 1e-9


def psth(
    phase: np.ndarray,
    y: np.ndarray,
    exposure: np.ndarray,
    n_bins: int = 24,
    n_boot: int = 1000,
    rng: Optional[np.random.Generator] = None,
) -> Dict[str, object]:
    """Effort-normalized rate vs phase with bootstrap confidence bands.

    ``rate[b] = sum(y in bin b) / sum(exposure in bin b)``. Confidence bands come
    from resampling the rows with replacement ``n_boot`` times.
    """
    rng = rng or np.random.default_rng()
    phase = np.asarray(phase, dtype=float) % 1.0
    y = np.asarray(y, dtype=float)
    exposure = np.clip(np.asarray(exposure, dtype=float), _EPS, None)

    edges = np.linspace(0.0, 1.0, n_bins + 1)
    centers = 0.5 * (edges[:-1] + edges[1:])
    idx = np.clip(np.digitize(phase, edges[1:-1]), 0, n_bins - 1)

    def _rates(sel: np.ndarray) -> np.ndarray:
        yb = np.bincount(idx[sel], weights=y[sel], minlength=n_bins)
        eb = np.bincount(idx[sel], weights=exposure[sel], minlength=n_bins)
        return yb / np.clip(eb, _EPS, None)

    all_rows = np.arange(phase.size)
    rate = _rates(all_rows)
    counts = np.bincount(idx, minlength=n_bins)

    boot = np.empty((n_boot, n_bins))
    for b in range(n_boot):
        sample = rng.integers(0, phase.size, size=phase.size)
        boot[b] = _rates(sample)
    ci_lo = np.percentile(boot, 2.5, axis=0)
    ci_hi = np.percentile(boot, 97.5, axis=0)

    return {
        "phase_centers": centers,
        "rate": rate,
        "ci_lo": ci_lo,
        "ci_hi": ci_hi,
        "n_per_bin": counts,
        "modulation": modulation_depth(rate),
    }


def psth_with_null(
    phase: np.ndarray,
    y: np.ndarray,
    exposure: np.ndarray,
    n_bins: int = 24,
    n_boot: int = 500,
    n_shuffles: int = 500,
    rng: Optional[np.random.Generator] = None,
) -> Dict[str, object]:
    """PSTH plus a phase-shuffle null on its modulation depth (Level 1 gate).

    The null shuffles the phase labels (breaking the phase<->count relation while
    preserving the marginal distributions) and recomputes the PSTH modulation.
    A real tuning curve must beat this null.
    """
    rng = rng or np.random.default_rng()
    result = psth(phase, y, exposure, n_bins=n_bins, n_boot=n_boot, rng=rng)
    observed = result["modulation"]

    phase = np.asarray(phase, dtype=float) % 1.0
    y = np.asarray(y, dtype=float)
    exposure = np.clip(np.asarray(exposure, dtype=float), _EPS, None)
    edges = np.linspace(0.0, 1.0, n_bins + 1)

    def sample_null(r: np.random.Generator) -> float:
        shuffled = r.permutation(phase)
        idx = np.clip(np.digitize(shuffled, edges[1:-1]), 0, n_bins - 1)
        yb = np.bincount(idx, weights=y, minlength=n_bins)
        eb = np.bincount(idx, weights=exposure, minlength=n_bins)
        return modulation_depth(yb / np.clip(eb, _EPS, None))

    result["null"] = permutation_null(observed, sample_null, n_shuffles=n_shuffles, rng=rng)
    return result
