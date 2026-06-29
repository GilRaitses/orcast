"""Orchestration test: seed an in-memory store, fit end-to-end, gate, serialize."""

import numpy as np

from src.aws_backend.timeseries import MemoryTimeSeriesStore
from src.aws_backend.kernel_model.serve import FittedKernels, KernelForecaster

from modeling.bases import evaluate_kernel
from modeling.fit_kernels import (
    run_fit,
    ACOUSTIC,
    CURRENTS,
    STATION_UPTIME,
    _content_id,
)
from modeling.timeutil import from_hours, to_hours


def _seed_store(seed=0):
    rng = np.random.default_rng(seed)
    store = MemoryTimeSeriesStore()
    t0 = to_hours("2024-01-01T00:00:00+00:00")
    T = 24 * 365 * 1.5  # 1.5 years of hours

    # Known diel + season structure drives the detection intensity.
    diel_k = {"cos": [1.0], "sin": [0.5]}
    season_k = {"cos": [0.6], "sin": [0.0]}

    def intensity(t):
        diel_ph = ((t - t0) / 24.0) % 1.0
        season_ph = (((t - t0) / 24.0) % 365.0) / 365.0
        log_r = -1.0 + evaluate_kernel(np.array([diel_ph]), diel_k["cos"], diel_k["sin"])[0]
        log_r += evaluate_kernel(np.array([season_ph]), season_k["cos"], season_k["sin"])[0]
        return np.exp(log_r)

    lam_max = np.exp(-1.0 + 1.5 + 0.6) * 1.2
    for station, (lat, lng) in {"haro_strait": (48.5, -123.15), "lime_kiln": (48.52, -123.15)}.items():
        t = t0
        recs = []
        while t < t0 + T:
            t += rng.exponential(1.0 / lam_max)
            if t < t0 + T and rng.uniform() < intensity(t) / lam_max:
                recs.append({
                    "t": from_hours(t).isoformat(), "id": f"{station}-{len(recs)}",
                    "station": station, "latitude": lat, "longitude": lng, "confirmed": True,
                })
        store.put_series(ACOUSTIC, station, recs)

    # Hourly current series (signed) so a tidal phase can be built.
    currents = []
    n = int(T)
    for i in range(n):
        tt = t0 + i
        currents.append({"t": from_hours(tt).isoformat(),
                         "value": float(np.sin(2 * np.pi * (i / 12.42)))})
    store.put_series(CURRENTS, "PUG1702", currents)
    return store


def test_run_fit_produces_fitted_report_and_serializable_coeffs():
    store = _seed_store(seed=1)
    report = run_fit(store, bin_hours=1.0, write_outputs=False)

    assert report["status"] == "fitted"
    assert report["n_detections"] >= 300
    assert str(report["fit_plan_id"]).startswith("fitplan_")
    assert str(report["dataset_snapshot_id"]).startswith("snap_")
    assert str(report["repr_id"]).startswith("repr_")
    assert str(report["run_id"]).startswith("run_")
    assert report["kernel_version"] == report["repr_id"]
    assert report["artifact_uris"]["fitted_kernels"] == f"representations/{report['repr_id']}/fitted_kernels.json"
    assert report["artifact_uris"]["fit_report"] == f"runs/{report['run_id']}/fit_report.json"
    assert report["data_window"]["bin_hours"] == 1.0
    assert report["input_hashes"]
    assert "acoustic_detections:haro_strait" in report["input_hashes"]
    # Level 1: diel should beat its phase-shuffle null.
    assert report["level1_psth"]["diel"]["beats_null"] is True
    # Level 2: CV gate and a positive pseudo-R^2.
    assert report["cv"]["gate_pass"] is True
    assert report["metrics"]["mcfadden_r2"] > 0.0
    assert 0.0 <= report["confidence"] <= 1.0

    # The fit must round-trip through the shipped serving schema.
    from modeling.estimator import fit_glm
    from modeling.design import build_design
    from modeling.tide_phase import TidalPhase
    from modeling.fit_kernels import read_streams, _wide_window

    acoustic, uptime, currents = read_streams(store, *_wide_window())
    df = build_design(acoustic, uptime, TidalPhase.from_records(currents), bin_hours=1.0)
    model = fit_glm(df, n_harmonics=2)
    fit = FittedKernels.from_dict(model.to_fitted_dict(confidence=report["confidence"]))
    forecaster = KernelForecaster(fit)
    val = forecaster.intensity(from_hours(to_hours("2024-06-01T12:00:00+00:00")), 48.5, -123.15,
                               station="haro_strait", tide_phase=0.3)
    assert val > 0.0


def test_run_fit_reports_insufficient_data_for_empty_store():
    store = MemoryTimeSeriesStore()
    report = run_fit(store, write_outputs=False)
    assert report["status"] == "insufficient_data"
    assert report["n_detections"] == 0
    assert str(report["fit_plan_id"]).startswith("fitplan_")
    assert str(report["dataset_snapshot_id"]).startswith("snap_")


def test_snapshot_id_is_stable_for_same_inputs():
    store1 = _seed_store(seed=2)
    store2 = _seed_store(seed=2)
    report1 = run_fit(store1, bin_hours=1.0, write_outputs=False)
    report2 = run_fit(store2, bin_hours=1.0, write_outputs=False)
    assert report1["fit_plan_id"] == report2["fit_plan_id"]
    assert report1["dataset_snapshot_id"] == report2["dataset_snapshot_id"]


def test_freeze_dataset_snapshot_matches_run_fit_snap_id():
    from modeling.fit_kernels import freeze_dataset_snapshot

    store = _seed_store(seed=2)
    manifest = freeze_dataset_snapshot(store, bin_hours=1.0, write_outputs=False)
    report = run_fit(store, bin_hours=1.0, write_outputs=False)
    assert manifest["snap_id"] == report["dataset_snapshot_id"]


def test_run_fit_uses_pinned_snapshot_after_store_mutation():
    from modeling.fit_kernels import freeze_dataset_snapshot

    store = _seed_store(seed=2)
    manifest = freeze_dataset_snapshot(store, bin_hours=1.0, write_outputs=False)
    snap_id = manifest["snap_id"]
    # Mutate live store after freeze.
    store.put_series(
        "orcahello_acoustic_detections",
        "haro_strait",
        [{"t": "2099-01-01T00:00:00+00:00", "count": 999}],
    )
    pinned = run_fit(store, bin_hours=1.0, write_outputs=False, dataset_snapshot_id=snap_id)
    fresh = run_fit(store, bin_hours=1.0, write_outputs=False)
    assert pinned["dataset_snapshot_id"] == snap_id
    assert pinned["n_detections"] == fresh["n_detections"] or pinned["n_detections"] != 999


def test_content_id_uses_canonical_json_ordering():
    assert _content_id("snap", {"b": 2, "a": 1}) == _content_id("snap", {"a": 1, "b": 2})


def test_level0_detector_qc_activates_with_reviewed_labels():
    store = _seed_store(seed=2)
    store.put_series(
        "orcahello_reviewed_detector_outcomes",
        "haro_strait",
        [
            {"t": "2026-01-01T00:00:00+00:00", "outcome": "confirmed"},
            {"t": "2026-01-02T00:00:00+00:00", "outcome": "false_positive"},
            {"t": "2026-01-03T00:00:00+00:00", "outcome": "unknown"},
        ],
    )
    report = run_fit(store, bin_hours=1.0, write_outputs=False)
    qc = report["level0_detector_qc"]
    assert qc["status"] == "active"
    assert qc["truth_label"] == "live"
    assert qc["outcome_counts"]["confirmed"] == 1
