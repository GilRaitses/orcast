"""Tests for the data/design layer: bases, simulate, tide phase, binning."""

import math

import numpy as np
import pandas as pd

from modeling.bases import (
    fourier_columns,
    split_coefficients,
    evaluate_kernel,
    kernel_curve,
)
from modeling.simulate import thinning, rate_from_kernels, simulate_binned_dataset
from modeling.tide_phase import TidalPhase
from modeling.design import build_design, event_times_hours
from modeling.timeutil import from_hours, to_hours
from src.aws_backend.kernel_model.serve import FourierKernel


# --- bases -------------------------------------------------------------------

def test_fourier_columns_shape_and_mean_zero():
    phase = np.linspace(0, 1, 1000, endpoint=False)
    X, names = fourier_columns(phase, n_harmonics=3)
    assert X.shape == (1000, 6)
    assert names == ["cos_1", "sin_1", "cos_2", "sin_2", "cos_3", "sin_3"]
    assert np.allclose(X.mean(axis=0), 0.0, atol=1e-9)


def test_split_coefficients_and_serve_consistency():
    coefs = np.array([0.5, 0.2, -0.3, 0.1])  # cos_1, sin_1, cos_2, sin_2
    cos, sin = split_coefficients(coefs, n_harmonics=2)
    assert cos == [0.5, -0.3]
    assert sin == [0.2, 0.1]

    # The offline evaluator and the shipped serving kernel must agree.
    kernel = FourierKernel(cos=cos, sin=sin)
    phases = np.linspace(0, 1, 50, endpoint=False)
    offline = evaluate_kernel(phases, cos, sin)
    served = np.array([kernel.value(p) for p in phases])
    assert np.allclose(offline, served, atol=1e-12)


def test_kernel_curve_is_mean_zero():
    _, values = kernel_curve(cos=[0.7, -0.2], sin=[0.4], n_points=500)
    assert abs(values.mean()) < 1e-9


# --- simulate ----------------------------------------------------------------

def test_thinning_recovers_expected_count():
    rng = np.random.default_rng(0)
    rate, T = 3.0, 1000.0
    times = thinning(lambda t: rate, 0.0, T, lam_max=rate, rng=rng)
    # Expected ~ rate*T = 3000; allow generous Poisson tolerance.
    assert abs(times.size - rate * T) < 5 * math.sqrt(rate * T)
    assert np.all(np.diff(times) > 0)


def test_rate_from_kernels_matches_manual():
    phases = {"diel": np.array([0.0, 0.25, 0.5])}
    kernels = {"diel": {"cos": [0.5], "sin": [0.0]}}
    rate = rate_from_kernels(intercept=-1.0, kernels=kernels, phases=phases)
    expected = np.exp(-1.0 + 0.5 * np.cos(2 * np.pi * phases["diel"]))
    assert np.allclose(rate, expected)


def test_simulate_binned_dataset_shape_and_nonneg():
    rng = np.random.default_rng(1)
    phases = {"diel": rng.uniform(size=200)}
    kernels = {"diel": {"cos": [0.4], "sin": [0.1]}}
    y = simulate_binned_dataset(-2.0, kernels, phases, exposure=np.ones(200), rng=rng)
    assert y.shape == (200,)
    assert np.all(y >= 0)


# --- tide phase --------------------------------------------------------------

def _current_records(period_h=12.42, n_days=6, step_h=0.5, phase0=0.0):
    records = []
    t0 = to_hours("2026-01-01T00:00:00+00:00")
    n = int(n_days * 24 / step_h)
    for i in range(n):
        t = t0 + i * step_h
        v = math.sin(2 * math.pi * ((t - t0) / period_h) + phase0)
        records.append({"t": from_hours(t).isoformat(), "value": v})
    return records, t0


def test_tidal_phase_zero_at_flood_onset():
    records, t0 = _current_records()
    tide = TidalPhase.from_records(records)
    assert tide.onsets.size >= 4
    # Phase right after an onset is near 0; a quarter period later near 0.25.
    onset = tide.onsets[1]
    assert tide.phase(onset + 1e-3) < 0.05
    assert abs(tide.phase(onset + 12.42 / 4) - 0.25) < 0.1


def test_tidal_phase_in_unit_interval_and_value_interp():
    records, t0 = _current_records()
    tide = TidalPhase.from_records(records)
    samples = tide.phases([t0 + h for h in range(0, 100)])
    assert np.all((samples >= 0) & (samples < 1.0))
    assert tide.value_at(t0 + 0.0) is not None


# --- design ------------------------------------------------------------------

def _detections(station, start_iso, n, step_h=1.0, lat=48.5, lng=-123.0):
    t0 = to_hours(start_iso)
    return [
        {
            "t": from_hours(t0 + i * step_h).isoformat(),
            "id": f"{station}-{i}",
            "station": station,
            "latitude": lat,
            "longitude": lng,
            "confirmed": True,
        }
        for i in range(n)
    ]


def test_build_design_counts_and_default_effort():
    recs = _detections("haro_strait", "2026-06-01T00:00:00+00:00", n=48, step_h=1.0)
    df = build_design({"haro_strait": recs}, bin_hours=1.0)

    assert set(["station", "t", "y", "exposure", "log_exposure", "diel", "lunar", "season", "tide"]).issubset(df.columns)
    # Every detection should be counted exactly once.
    assert df["y"].sum() == 48
    # No uptime supplied -> continuous-coverage assumption, exposure == bin width.
    assert np.allclose(df["exposure"], 1.0)
    assert df.attrs["effort_assumed_continuous"] is True
    assert np.all((df["diel"] >= 0) & (df["diel"] < 1.0))
    assert np.all((df["season"] >= 0) & (df["season"] < 1.0))


def test_build_design_uses_uptime_and_drops_offline_bins():
    recs = _detections("haro_strait", "2026-06-01T00:00:00+00:00", n=10, step_h=1.0)
    # Station goes offline for a long stretch after t0+5h.
    t0 = to_hours("2026-06-01T00:00:00+00:00")
    uptime = [
        {"t": from_hours(t0 - 1).isoformat(), "station": "haro_strait", "up": 1},
        {"t": from_hours(t0 + 5).isoformat(), "station": "haro_strait", "up": 0},
        {"t": from_hours(t0 + 200).isoformat(), "station": "haro_strait", "up": 1},
    ]
    df = build_design({"haro_strait": recs}, uptime_by_station={"haro_strait": uptime}, bin_hours=1.0)
    assert df.attrs["effort_assumed_continuous"] is False
    # Bins during the offline stretch (exposure 0) are dropped.
    assert df["exposure"].min() > 0


def test_event_times_hours_sorted_and_confirmed_filter():
    recs = [
        {"t": "2026-06-01T02:00:00+00:00", "confirmed": False},
        {"t": "2026-06-01T00:00:00+00:00", "confirmed": True},
        {"t": "2026-06-01T01:00:00+00:00", "confirmed": True},
    ]
    all_ev = event_times_hours(recs)
    assert all_ev.size == 3
    assert np.all(np.diff(all_ev) > 0)
    confirmed = event_times_hours(recs, confirmed_only=True)
    assert confirmed.size == 2
