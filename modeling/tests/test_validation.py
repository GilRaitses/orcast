"""Synthetic correctness tests for the validation toolkit.

The toolkit is the set of fitness-gate enforcers, so these tests check that each
gate (a) passes when the model is right and (b) fails when it is wrong.
"""

import numpy as np
import pandas as pd

from modeling.validation.time_rescaling import run_time_rescaling
from modeling.validation.diagnostics import (
    poisson_deviance,
    deviance_residuals,
    mcfadden_r2,
    poisson_loglik,
    null_loglik,
    pit_uniformity,
)
from modeling.validation.null_tests import binomial_pass_test, permutation_null, modulation_depth
from modeling.validation.crossval import assign_time_blocks, block_cv


def _homogeneous_poisson(rate, T, rng):
    times, t = [], 0.0
    while t < T:
        t += rng.exponential(1.0 / rate)
        if t < T:
            times.append(t)
    return np.array(times)


def _inhomogeneous_poisson(intensity_fn, T, lam_max, rng):
    """Thinning: simulate an inhomogeneous Poisson process on [0, T]."""
    times, t = [], 0.0
    while t < T:
        t += rng.exponential(1.0 / lam_max)
        if t < T and rng.uniform() < intensity_fn(t) / lam_max:
            times.append(t)
    return np.array(times)


# --- time-rescaling ----------------------------------------------------------

def test_time_rescaling_passes_for_correct_constant_rate():
    rng = np.random.default_rng(0)
    rate = 2.0
    events = _homogeneous_poisson(rate, T=2000.0, rng=rng)
    res = run_time_rescaling(events, intensity=lambda t: np.full_like(t, rate), grid_step=0.05)
    assert res["pass_exp"] is True
    assert abs(res["rescaled_iei_mean"] - 1.0) < 0.1


def test_time_rescaling_fails_for_wrong_rate():
    rng = np.random.default_rng(1)
    events = _homogeneous_poisson(2.0, T=2000.0, rng=rng)
    # Rescale with a 5x-too-high intensity: rescaled IEIs are not Exp(1).
    res = run_time_rescaling(events, intensity=lambda t: np.full_like(t, 10.0), grid_step=0.05)
    assert res["pass_exp"] is False


def test_time_rescaling_inhomogeneous_true_vs_mean():
    rng = np.random.default_rng(2)
    base, amp, omega = 3.0, 0.8, 2 * np.pi / 24.0
    intensity = lambda t: base * (1 + amp * np.sin(omega * t))
    events = _inhomogeneous_poisson(intensity, T=4000.0, lam_max=base * (1 + amp), rng=rng)

    true_fit = run_time_rescaling(events, intensity=lambda t: intensity(t), grid_step=0.05)
    mean_fit = run_time_rescaling(events, intensity=lambda t: np.full_like(t, base), grid_step=0.05)

    assert true_fit["pass_exp"] is True
    assert mean_fit["pass_exp"] is False


# --- binomial pass test ------------------------------------------------------

def test_binomial_modest_pass_not_significant():
    res = binomial_pass_test(7, 12)
    assert res["significant_at_alpha_05"] is False
    assert 0.0 <= res["ci_95_lower"] <= res["ci_95_upper"] <= 1.0


def test_binomial_all_pass_significant():
    res = binomial_pass_test(12, 12)
    assert res["significant_at_alpha_05"] is True


# --- permutation null --------------------------------------------------------

def test_permutation_null_detects_signal_and_ignores_noise():
    rng = np.random.default_rng(3)
    # Strongly modulated PSTH should beat a flat shuffle null.
    real = np.array([1.0, 4.0, 8.0, 4.0, 1.0, 0.5])
    observed = modulation_depth(real)

    def shuffle_flat(r):
        return modulation_depth(r.uniform(0.9, 1.1, size=real.size))

    signal = permutation_null(observed, shuffle_flat, n_shuffles=500, rng=rng)
    assert signal["beats_null"] is True

    # A flat observed statistic should not beat the same null.
    flat_obs = modulation_depth(np.full(real.size, 1.0))
    noise = permutation_null(flat_obs, shuffle_flat, n_shuffles=500, rng=rng)
    assert noise["beats_null"] is False


# --- diagnostics -------------------------------------------------------------

def test_poisson_deviance_zero_at_perfect_fit():
    y = np.array([0.0, 1.0, 3.0, 7.0])
    assert poisson_deviance(y, y) < 1e-6


def test_deviance_residual_sign_follows_error():
    y = np.array([5.0, 1.0])
    mu = np.array([2.0, 4.0])
    res = deviance_residuals(y, mu)
    assert res[0] > 0  # under-predicted
    assert res[1] < 0  # over-predicted


def test_mcfadden_r2_rewards_better_model():
    rng = np.random.default_rng(4)
    x = rng.uniform(size=400)
    mu_true = np.exp(-1.0 + 2.0 * x)
    y = rng.poisson(mu_true).astype(float)
    ll_model = poisson_loglik(y, mu_true)
    ll_null = null_loglik(y)
    assert 0.0 < mcfadden_r2(ll_model, ll_null) < 1.0


def test_pit_calibrated_for_true_model_and_not_for_wrong():
    rng = np.random.default_rng(5)
    mu = np.full(3000, 4.0)
    y = rng.poisson(mu).astype(float)
    good = pit_uniformity(y, mu, rng=np.random.default_rng(6))
    bad = pit_uniformity(y, np.full_like(mu, 1.0), rng=np.random.default_rng(7))
    assert good["calibrated"] is True
    assert bad["calibrated"] is False


# --- cross-validation --------------------------------------------------------

def test_assign_time_blocks_contiguous():
    t = np.arange(100.0)
    blocks = assign_time_blocks(t, 5)
    assert set(blocks) == {0, 1, 2, 3, 4}
    # Blocks must be monotonic in time (contiguous, no interleaving).
    assert np.all(np.diff(blocks) >= 0)


def test_block_cv_covariate_model_beats_climatology():
    rng = np.random.default_rng(8)
    n = 2000
    t = np.sort(rng.uniform(0, 1000, size=n))
    x = np.sin(2 * np.pi * t / 24.0)
    mu = np.exp(0.5 + 1.2 * x)
    y = rng.poisson(mu).astype(float)
    df = pd.DataFrame({"t": t, "y": y, "x": x, "exposure": 1.0})

    def fit_predict(train, test):
        # Fit log-linear y ~ x by simple Poisson IRLS-free closed-ish form:
        # use numpy polyfit on log(y+1) as a cheap stand-in estimator.
        coef = np.polyfit(train["x"], np.log(train["y"] + 1.0), 1)
        return np.exp(np.polyval(coef, test["x"]))

    res = block_cv(df, fit_predict, n_blocks=5)
    assert res["gate_pass"] is True
    assert res["mean_deviance_skill"] > 0.0


def test_block_cv_climatology_does_not_beat_itself():
    rng = np.random.default_rng(9)
    n = 1500
    t = np.sort(rng.uniform(0, 1000, size=n))
    y = rng.poisson(3.0, size=n).astype(float)
    df = pd.DataFrame({"t": t, "y": y, "exposure": 1.0})

    def fit_predict(train, test):
        return np.full(len(test), train["y"].mean())

    res = block_cv(df, fit_predict, n_blocks=5)
    # Predicting the train mean barely differs from the climatology baseline;
    # it must not pass the "beats climatology" gate.
    assert res["gate_pass"] is False
