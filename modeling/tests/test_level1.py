"""Level 1 tests: PSTH recovers rate under non-uniform effort; STA finds signal."""

import numpy as np

from modeling.psth import psth, psth_with_null
from modeling.reverse_corr import reverse_correlation


def test_psth_recovers_true_rate_under_nonuniform_effort():
    rng = np.random.default_rng(0)
    n = 40000
    phase = rng.uniform(size=n)

    # True presence rate (per effort-hour) and a DIFFERENT effort shape.
    true_rate = np.exp(0.5 + np.cos(2 * np.pi * phase))
    effort = 1.0 + 0.8 * np.sin(2 * np.pi * phase)  # non-uniform, different shape
    y = rng.poisson(true_rate * effort).astype(float)

    out = psth(phase, y, effort, n_bins=24, n_boot=200, rng=rng)
    centers = out["phase_centers"]
    true_at_centers = np.exp(0.5 + np.cos(2 * np.pi * centers))

    # Effort-normalized PSTH tracks the true rate, not the effort shape.
    corr_rate = np.corrcoef(out["rate"], true_at_centers)[0, 1]
    assert corr_rate > 0.97

    # A naive count-density (counts per bin, no effort correction) is more
    # contaminated by effort: it must track the true rate strictly worse.
    counts = out["n_per_bin"] * out["rate"]  # reconstruct ~ sum y per bin
    naive = counts / counts.sum()
    corr_naive = np.corrcoef(naive, true_at_centers)[0, 1]
    assert corr_rate > corr_naive


def test_psth_null_detects_real_modulation_and_ignores_flat():
    rng = np.random.default_rng(1)
    n = 20000

    # Modulated presence -> beats the phase-shuffle null decisively.
    phase = rng.uniform(size=n)
    rate = np.exp(0.2 + 1.2 * np.cos(2 * np.pi * phase))
    y = rng.poisson(rate).astype(float)
    real = psth_with_null(phase, y, np.ones(n), n_bins=24, n_boot=100, n_shuffles=300, rng=rng)
    assert real["null"]["beats_null"] is True
    assert real["null"]["z"] > 5.0

    # Flat presence (counts independent of phase) is exchangeable with its own
    # shuffle null, so its modulation sits within the null spread (small z) and
    # far below the modulated case. Use an independent rng + phase so the counts
    # are genuinely phase-independent.
    rng_flat = np.random.default_rng(99)
    phase_flat = rng_flat.uniform(size=n)
    y_flat = rng_flat.poisson(np.full(n, 3.0)).astype(float)
    flat = psth_with_null(phase_flat, y_flat, np.ones(n), n_bins=24, n_boot=100, n_shuffles=300, rng=rng_flat)
    assert flat["null"]["z"] < 3.0
    assert real["null"]["z"] > 10 * max(flat["null"]["z"], 0.1)


def test_reverse_correlation_finds_covariate_signal():
    rng = np.random.default_rng(2)
    # Continuous covariate series (e.g., current speed) over a long span.
    cov_times = np.arange(0.0, 5000.0, 0.25)
    cov_values = np.sin(2 * np.pi * cov_times / 12.42) + 0.3 * rng.standard_normal(cov_times.size)

    # Detections preferentially occur when the covariate is high (thinning).
    base = 0.05
    lam_max = base * np.exp(1.0)
    events = []
    t = 0.0
    while t < cov_times[-1]:
        t += rng.exponential(1.0 / lam_max)
        if t >= cov_times[-1]:
            break
        cov_now = np.interp(t, cov_times, cov_values)
        if rng.uniform() < (base * np.exp(0.9 * cov_now)) / lam_max:
            events.append(t)
    events = np.array(events)

    lags = np.linspace(-3, 3, 25)
    res = reverse_correlation(events, cov_times, cov_values, lags, n_shuffles=200, rng=rng)
    # The covariate is elevated around detections vs the shuffled null.
    assert res["max_abs_z"] > 4.0
    # The STA peaks near lag 0 (detections track the instantaneous covariate).
    assert abs(lags[np.argmax(res["sta"])]) <= 1.0
