import json
import math
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from src.aws_backend.kernel_model import serve
from src.aws_backend.kernel_model.serve import (
    FittedKernels,
    FourierKernel,
    KernelForecaster,
    S3ReadError,
    load_fitted_kernels,
)
from src.aws_backend.main import app


def test_fourier_kernel_wraps_and_is_periodic():
    kernel = FourierKernel(cos=[0.5], sin=[0.2])
    assert math.isclose(kernel.value(0.0), kernel.value(1.0), abs_tol=1e-12)
    assert math.isclose(kernel.value(0.25), kernel.value(1.25), abs_tol=1e-12)


def test_fourier_kernel_mean_centred_over_cycle():
    kernel = FourierKernel(cos=[0.7, -0.3], sin=[0.4])
    samples = [kernel.value(i / 1000.0) for i in range(1000)]
    assert abs(sum(samples) / len(samples)) < 1e-6


def test_load_missing_returns_none(tmp_path):
    assert load_fitted_kernels(tmp_path / "nope.json") is None


def test_load_roundtrip(tmp_path):
    payload = {
        "version": "test",
        "intercept": -2.0,
        "bin_hours": 1.0,
        "station_effects": {"haro_strait": 0.5},
        "kernels": {"diel": {"cos": [0.3], "sin": [0.1]}},
    }
    path = tmp_path / "fitted_kernels.json"
    path.write_text(json.dumps(payload))

    fit = load_fitted_kernels(path)
    assert isinstance(fit, FittedKernels)
    assert fit.intercept == -2.0
    assert fit.station_effects["haro_strait"] == 0.5
    assert "diel" in fit.kernels


def test_load_current_pointer_for_coefficients_and_fit_report(tmp_path, monkeypatch):
    current = tmp_path / "current.json"
    coeff = tmp_path / "representations" / "repr_a" / "fitted_kernels.json"
    report = tmp_path / "runs" / "run_a" / "fit_report.json"
    coeff.parent.mkdir(parents=True)
    report.parent.mkdir(parents=True)
    coeff.write_text(json.dumps({
        "version": "repr_a",
        "intercept": -2.0,
        "kernels": {"diel": {"cos": [0.3], "sin": [0.1]}},
    }))
    report.write_text(json.dumps({"status": "fitted", "repr_id": "repr_a", "run_id": "run_a"}))
    current.write_text(json.dumps({
        "repr_id": "repr_a",
        "run_id": "run_a",
        "fitted_kernels": "representations/repr_a/fitted_kernels.json",
        "fit_report": "runs/run_a/fit_report.json",
    }))
    monkeypatch.setattr(serve, "DEFAULT_CURRENT_POINTER_PATH", current)
    monkeypatch.setattr(serve, "DEFAULT_COEFFICIENTS_PATH", tmp_path / "legacy.json")

    fit = load_fitted_kernels()
    assert fit is not None
    assert fit.version == "repr_a"
    assert serve.load_fit_report()["run_id"] == "run_a"


def test_forecaster_intensity_uses_intercept_station_and_kernels():
    fit = FittedKernels(
        intercept=-2.0,
        kernels={"diel": FourierKernel(cos=[0.5])},
        station_effects={"haro_strait": 0.3},
    )
    forecaster = KernelForecaster(fit)
    when = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)

    base = forecaster.log_intensity(when, 48.5, -123.0)
    with_station = forecaster.log_intensity(when, 48.5, -123.0, station="haro_strait")
    assert math.isclose(with_station - base, 0.3, abs_tol=1e-9)

    # Unknown station contributes no effect.
    assert forecaster.log_intensity(when, 48.5, -123.0, station="ghost") == base

    assert forecaster.intensity(when, 48.5, -123.0) > 0.0


def test_forecaster_tide_phase_is_optional_and_applied():
    fit = FittedKernels(
        intercept=-1.0,
        kernels={"tide": FourierKernel(cos=[0.4])},
    )
    forecaster = KernelForecaster(fit)
    when = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)

    # Without a tide phase the tide kernel is skipped (only intercept remains).
    assert math.isclose(forecaster.log_intensity(when, 48.5, -123.0), -1.0, abs_tol=1e-9)
    # With a tide phase the kernel contributes.
    shifted = forecaster.log_intensity(when, 48.5, -123.0, tide_phase=0.0)
    assert math.isclose(shifted, -1.0 + 0.4, abs_tol=1e-9)


# -- read_s3_json: 404 (cacheable) vs transient (never cached) ---------------
def test_read_s3_json_genuine_miss_returns_none_and_caches(monkeypatch):
    import boto3
    from botocore.exceptions import ClientError

    serve._s3_cache.clear()
    calls = {"n": 0}

    class FakeS3:
        def get_object(self, Bucket, Key):
            calls["n"] += 1
            raise ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")

    monkeypatch.setattr(boto3, "client", lambda *a, **k: FakeS3())

    assert serve.read_s3_json("models/missing.json", bucket="b") is None
    # Confirmed miss is cached: second call does not hit S3 again.
    assert serve.read_s3_json("models/missing.json", bucket="b") is None
    assert calls["n"] == 1


def test_read_s3_json_transient_raises_and_is_not_cached(monkeypatch):
    import boto3
    from botocore.exceptions import ClientError

    serve._s3_cache.clear()
    calls = {"n": 0}

    class FakeS3:
        def get_object(self, Bucket, Key):
            calls["n"] += 1
            raise ClientError({"Error": {"Code": "AccessDenied"}}, "GetObject")

    monkeypatch.setattr(boto3, "client", lambda *a, **k: FakeS3())

    with pytest.raises(S3ReadError):
        serve.read_s3_json("models/denied.json", bucket="b")
    # An IAM/transient error must NOT pin "not_fitted": a retry hits S3 again.
    with pytest.raises(S3ReadError):
        serve.read_s3_json("models/denied.json", bucket="b")
    assert calls["n"] == 2


# -- /api/gates: caveats + effective_confidence ------------------------------
def _honesty_report():
    return {
        "status": "fitted",
        "confidence": 0.42,
        "tide_overlaps_acoustic": False,
        "n_stations_acoustic": 1,
        "effort_assumed_continuous": True,
        "detections_unreviewed_candidates": True,
        "time_rescaling": {"pooled_pass_exp": False},
        "cv": {"mean_deviance_skill": 0.01},
        "generated_at": "2026-01-01T00:00:00Z",
    }


def test_gates_includes_caveats_and_effective_confidence(monkeypatch):
    from src.aws_backend.routers import kernel as kr

    monkeypatch.setattr(kr, "_load_fit_report", lambda: _honesty_report())
    monkeypatch.setattr(kr, "load_promotion", lambda: None)
    monkeypatch.setattr(kr, "load_pending_approval", lambda: None)

    data = TestClient(app).get("/api/gates").json()
    assert data["effective_confidence"] == 0.42
    caveats = data["caveats"]
    assert any("Tide kernel is not meaningful" in c for c in caveats)
    assert "Single station" in caveats
    assert any("Effort assumed continuous" in c for c in caveats)
    assert any("unreviewed candidates" in c for c in caveats)
    assert any("time-rescaling" in c for c in caveats)
    assert any("Cross-validation skill is marginal" in c for c in caveats)


def test_gates_omits_tr_and_cv_caveats_when_passing(monkeypatch):
    from src.aws_backend.routers import kernel as kr

    report = {
        "status": "fitted",
        "confidence": 0.8,
        "time_rescaling": {"pooled_pass_exp": True},
        "cv": {"mean_deviance_skill": 0.4},
        "generated_at": "2026-01-01T00:00:00Z",
    }
    monkeypatch.setattr(kr, "_load_fit_report", lambda: report)
    monkeypatch.setattr(kr, "load_promotion", lambda: None)
    monkeypatch.setattr(kr, "load_pending_approval", lambda: None)

    data = TestClient(app).get("/api/gates").json()
    caveats = data["caveats"]
    assert not any("time-rescaling" in c for c in caveats)
    assert not any("Cross-validation skill is marginal" in c for c in caveats)


def test_negative_cv_skill_gets_stronger_caveat():
    from src.aws_backend.routers.kernel import _build_caveats

    caveats = _build_caveats({"cv": {"mean_deviance_skill": -0.01}})
    assert any("negative" in c for c in caveats)


def test_build_caveats_tolerates_missing_and_none_fields():
    from src.aws_backend.routers.kernel import _build_caveats

    # No tr/cv keys at all -> no crash, no extra caveats.
    assert _build_caveats({}) == []
    # Present but None / non-dict -> tolerated.
    assert _build_caveats({"time_rescaling": None, "cv": None}) == []
    # cv present but skill is None -> no marginal-skill caveat.
    out = _build_caveats({"cv": {"mean_deviance_skill": None}})
    assert not any("Cross-validation skill is marginal" in c for c in out)


def test_gates_redacts_pending_approval_task_token(monkeypatch):
    from src.aws_backend.routers import kernel as kr

    monkeypatch.setattr(kr, "_load_fit_report", lambda: _honesty_report())
    monkeypatch.setattr(kr, "load_promotion", lambda: None)
    monkeypatch.setattr(
        kr,
        "load_pending_approval",
        lambda: {
            "task_token": "SUPER-SECRET-CALLBACK-TOKEN",
            "recommendation": {"recommendation": "promote", "rationale": "passes"},
        },
    )

    data = TestClient(app).get("/api/gates").json()
    assert data["pending_approval"]["has_task_token"] is True
    assert "task_token" not in data["pending_approval"]
    assert "SUPER-SECRET-CALLBACK-TOKEN" not in json.dumps(data)


def test_gates_aliases_psth_kernel_diagnostic_to_consistency(monkeypatch):
    from src.aws_backend.routers import kernel as kr

    report = {
        **_honesty_report(),
        "psth_vs_kernel_diagnostic": {
            "diel": {"correlation": 0.63, "agrees": False},
        },
    }
    monkeypatch.setattr(kr, "_load_fit_report", lambda: report)
    monkeypatch.setattr(kr, "load_promotion", lambda: None)
    monkeypatch.setattr(kr, "load_pending_approval", lambda: None)

    data = TestClient(app).get("/api/gates").json()
    assert data["gates"]["consistency"]["diel"]["correlation"] == 0.63


def test_gates_effective_confidence_prefers_promotion(monkeypatch):
    from src.aws_backend.routers import kernel as kr

    monkeypatch.setattr(kr, "_load_fit_report", lambda: _honesty_report())
    monkeypatch.setattr(kr, "load_promotion", lambda: {"promoted": True, "effective_confidence": 0.91})
    monkeypatch.setattr(kr, "load_pending_approval", lambda: None)

    data = TestClient(app).get("/api/gates").json()
    assert data["promoted"] is True
    assert data["effective_confidence"] == 0.91


# -- /api/provenance: spatial honesty + region gate --------------------------
def test_provenance_rejects_out_of_region():
    resp = TestClient(app).get("/api/provenance", params={"lat": 0.0, "lng": 0.0})
    assert resp.status_code == 422


def test_provenance_reports_spatial_not_modeled(monkeypatch):
    from src.aws_backend.routers import kernel as kr

    fit = FittedKernels(
        intercept=-1.0,
        kernels={"diel": FourierKernel(cos=[0.2])},
        confidence=0.3,
    )
    monkeypatch.setattr(
        kr.KernelForecaster,
        "from_path",
        classmethod(lambda cls, path=None: KernelForecaster(fit)),
    )
    monkeypatch.setattr(kr, "_load_fit_report", lambda: {"confidence": 0.3})
    monkeypatch.setattr(kr, "load_promotion", lambda: None)

    resp = TestClient(app).get("/api/provenance", params={"lat": 48.5, "lng": -123.0})
    assert resp.status_code == 200
    data = resp.json()
    assert data["spatial"]["modeled"] is False
    assert "temporal-only" in data["spatial"]["note"]
    assert "nearby_sample" in data
    assert "nearby_evidence" in data  # back-compat alias preserved
    assert data["effective_confidence"] == 0.3


def test_enrich_cv_display_caution_when_negative_skill():
    from src.aws_backend.routers.kernel import _enrich_cv_display

    out = _enrich_cv_display(
        {"gate_pass": True, "mean_deviance_skill": -0.018, "n_pass": 3, "n_folds": 5}
    )
    assert out["display_status"] == "caution"
    assert out["display_pass"] is False


def test_enrich_cv_display_pass_when_skill_non_negative():
    from src.aws_backend.routers.kernel import _enrich_cv_display

    out = _enrich_cv_display({"gate_pass": True, "mean_deviance_skill": 0.12})
    assert out["display_status"] == "pass"
    assert out["display_pass"] is True
