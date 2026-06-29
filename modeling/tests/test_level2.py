"""Level 2 tests: the joint Poisson-GLM recovers known kernels and validates."""

import numpy as np
import pandas as pd

from modeling.bases import evaluate_kernel
from modeling.simulate import rate_from_kernels
from modeling.estimator import fit_glm, make_fit_predict
from modeling.psth_vs_kernel import psth_vs_kernel
from modeling.validation.crossval import block_cv
from modeling.validation.time_rescaling import run_time_rescaling


def _synthetic_design(n=12000, n_stations=3, seed=0):
    rng = np.random.default_rng(seed)
    stations = [f"st{i}" for i in range(n_stations)]
    df = pd.DataFrame({
        "station": rng.choice(stations, size=n),
        "t": np.sort(rng.uniform(0, 8760, size=n)),  # one year of hours
        "diel": rng.uniform(size=n),
        "tide": rng.uniform(size=n),
        "lunar": rng.uniform(size=n),
        "season": rng.uniform(size=n),
        "exposure": rng.uniform(0.5, 1.0, size=n),
    })

    true_kernels = {
        "diel": {"cos": [0.9, 0.0], "sin": [0.4, 0.0]},
        "tide": {"cos": [0.0, 0.5], "sin": [0.7, 0.0]},
        "lunar": {"cos": [0.3, 0.0], "sin": [0.0, 0.0]},
        "season": {"cos": [0.6, 0.0], "sin": [0.2, 0.0]},
    }
    true_intercept = -1.5
    true_station = {"st0": 0.0, "st1": 0.5, "st2": -0.4}

    phases = {k: df[k].to_numpy() for k in ["diel", "tide", "lunar", "season"]}
    log_rate = np.full(n, true_intercept)
    for name, spec in true_kernels.items():
        log_rate = log_rate + evaluate_kernel(phases[name], spec["cos"], spec["sin"])
    log_rate = log_rate + df["station"].map(true_station).to_numpy()
    rate = np.exp(log_rate)
    df["y"] = rng.poisson(rate * df["exposure"].to_numpy()).astype(float)
    return df, true_kernels, true_intercept, true_station


def test_glm_recovers_known_kernels():
    df, true_kernels, true_intercept, true_station = _synthetic_design(n=15000, seed=1)
    model = fit_glm(df, n_harmonics=2)

    # Each fitted kernel curve correlates strongly with the truth.
    grid = np.linspace(0, 1, 200, endpoint=False)
    for name, spec in true_kernels.items():
        true_curve = evaluate_kernel(grid, spec["cos"], spec["sin"])
        fit_curve = evaluate_kernel(grid, model.kernels[name].cos, model.kernels[name].sin)
        if np.std(true_curve) < 1e-6:
            continue
        corr = np.corrcoef(true_curve, fit_curve)[0, 1]
        assert corr > 0.95, f"{name} corr {corr}"

    # Intercept and station effects recovered to within a reasonable tolerance.
    assert abs(model.intercept - true_intercept) < 0.2
    for st, eff in true_station.items():
        assert abs(model.station_effects[st] - eff) < 0.2


def test_glm_predict_matches_true_rate():
    df, *_ = _synthetic_design(n=12000, seed=2)
    model = fit_glm(df, n_harmonics=2)
    mu = model.predict(df)
    # Predicted expected counts track observed counts (binned correlation).
    assert np.corrcoef(mu, df["y"].to_numpy())[0, 1] > 0.4
    assert np.all(mu > 0)


def test_psth_vs_kernel_consistency():
    df, *_ = _synthetic_design(n=20000, seed=3)
    model = fit_glm(df, n_harmonics=2)
    res = psth_vs_kernel(df, model, "diel", n_bins=24, n_boot=100)
    assert res["agrees"] is True
    assert res["correlation"] > 0.9


def test_block_cv_with_glm_beats_climatology():
    df, *_ = _synthetic_design(n=12000, seed=4)
    fit_predict = make_fit_predict(n_harmonics=2)
    res = block_cv(df, fit_predict, n_blocks=5)
    assert res["gate_pass"] is True
    assert res["mean_deviance_skill"] > 0.0


def test_time_rescaling_on_recovered_model():
    # End-to-end: simulate a detection train from a known per-station intensity,
    # fit, then check the time-rescaling GOF passes against the fitted intensity.
    rng = np.random.default_rng(5)
    kernels = {"diel": {"cos": [1.0], "sin": [0.5]}}
    intercept = -0.5  # ~0.6 detections/hr baseline

    # Diel phase as a function of absolute hour (24-hour cycle).
    def diel_of(t):
        return (t / 24.0) % 1.0

    def intensity(t):
        ph = np.atleast_1d(diel_of(np.asarray(t, dtype=float)))
        return np.exp(intercept + evaluate_kernel(ph, kernels["diel"]["cos"], kernels["diel"]["sin"]))

    # Thinning simulation over ~2 years of hours.
    T = 17520.0
    lam_max = float(intensity(np.array([0.0]))[0]) * 6
    times, t = [], 0.0
    while t < T:
        t += rng.exponential(1.0 / lam_max)
        if t < T and rng.uniform() < float(intensity(np.array([t]))[0]) / lam_max:
            times.append(t)
    times = np.array(times)

    # Build the binned design from those events and fit.
    edges = np.arange(0, T + 1.0, 1.0)
    counts, _ = np.histogram(times, bins=edges)
    centers = edges[:-1] + 0.5
    df = pd.DataFrame({
        "station": "only",
        "t": centers,
        "diel": diel_of(centers),
        "exposure": 1.0,
        "y": counts.astype(float),
    })
    model = fit_glm(df, covariates=("diel",), n_harmonics=1, use_station_effects=False)

    def fitted_intensity(t):
        ph = (np.asarray(t, dtype=float) / 24.0) % 1.0
        return np.exp(model.intercept + evaluate_kernel(ph, model.kernels["diel"].cos, model.kernels["diel"].sin))

    res = run_time_rescaling(times, intensity=fitted_intensity, grid_step=0.1)
    assert res["pass_exp"] is True
