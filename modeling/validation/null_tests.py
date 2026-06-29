"""Null / shuffle controls and the binomial pass-rate test.

Ported from INDYsim ``compute_loeo_null_test.py`` (binomial + Clopper-Pearson)
and ``compute_reverse_correlation.compute_shuffled_baseline`` (shuffle null),
generalized so any PSTH/kernel statistic can be tested against a circular-shift
or permutation null. Every PSTH must beat its phase-shuffled null
(CALIBRATION_STUDIES.md calibration assay #4).
"""

from __future__ import annotations

from typing import Callable, Dict, Optional

import numpy as np
from scipy import stats


def binomial_pass_test(successes: int, trials: int, null_p: float = 0.5) -> Dict[str, object]:
    """One-sided exact binomial test that the pass rate beats chance.

    Returns the p-value, observed rate, and a 95% Clopper-Pearson exact CI. This
    answers "did k of n CV folds beat the null more often than chance?" honestly,
    including when the answer is "no" (the INDYsim posture).
    """
    if trials <= 0:
        return {"successes": successes, "trials": trials, "error": "no trials"}

    result = stats.binomtest(successes, trials, null_p, alternative="greater")
    p_value = float(result.pvalue)
    # Clopper-Pearson exact interval.
    ci_lower = 0.0 if successes == 0 else float(stats.beta.ppf(0.025, successes, trials - successes + 1))
    ci_upper = 1.0 if successes == trials else float(stats.beta.ppf(0.975, successes + 1, trials - successes))

    if p_value < 0.05:
        interpretation = "pass rate significantly exceeds chance"
    elif p_value < 0.10:
        interpretation = "marginal trend above chance"
    else:
        interpretation = "pass rate not significantly different from chance"

    return {
        "successes": int(successes),
        "trials": int(trials),
        "observed_rate": round(successes / trials, 3),
        "null_p": null_p,
        "p_value": round(p_value, 4),
        "ci_95_lower": round(ci_lower, 3),
        "ci_95_upper": round(ci_upper, 3),
        "interpretation": interpretation,
        "significant_at_alpha_05": p_value < 0.05,
    }


def permutation_null(
    observed_stat: float,
    sample_null_stat: Callable[[np.random.Generator], float],
    n_shuffles: int = 1000,
    rng: Optional[np.random.Generator] = None,
) -> Dict[str, object]:
    """Compare an observed statistic to a permutation/shuffle null distribution.

    ``sample_null_stat(rng)`` must return one statistic computed on shuffled
    data. Returns the null mean/std, a z-score, and a one-sided p-value (the
    fraction of null draws >= observed, with the standard +1 correction).
    """
    rng = rng or np.random.default_rng()
    null = np.array([sample_null_stat(rng) for _ in range(n_shuffles)], dtype=float)
    null_mean = float(np.mean(null))
    null_std = float(np.std(null))
    z = (observed_stat - null_mean) / null_std if null_std > 0 else 0.0
    p_value = float((np.sum(null >= observed_stat) + 1) / (n_shuffles + 1))
    return {
        "observed": float(observed_stat),
        "null_mean": null_mean,
        "null_std": null_std,
        "z": float(z),
        "p_value": p_value,
        "n_shuffles": int(n_shuffles),
        "beats_null": bool(p_value < 0.05),
    }


def circular_shift(values: np.ndarray, shift: int) -> np.ndarray:
    """Circularly shift an array (used to break phase alignment while keeping ACF)."""
    return np.roll(np.asarray(values), int(shift))


def modulation_depth(rate_by_bin: np.ndarray) -> float:
    """A simple PSTH modulation statistic: ``std(rate) / mean(rate)``.

    Scale-free, so it is comparable between a real PSTH and shuffled nulls. A
    flat (effort-only) PSTH has near-zero modulation; a real tuning curve does
    not.
    """
    rate = np.asarray(rate_by_bin, dtype=float)
    rate = rate[np.isfinite(rate)]
    if rate.size == 0 or rate.mean() == 0:
        return 0.0
    return float(rate.std() / rate.mean())
