from fastapi.testclient import TestClient

from src.aws_backend.main import app, run_ingestion


def _fit_report():
    return {
        "status": "fitted",
        "confidence": 0.7,
        "generated_at": "2026-01-01T00:00:00Z",
        "repr_id": "repr_abc",
        "run_id": "run_abc",
        "dataset_snapshot_id": "snap_abc",
        "fit_plan_id": "fitplan_abc",
        "family": "negbin",
        "covariates_fit": ["diel"],
        "level1_psth": {"diel": {"beats_null": True}},
        "cv": {"gate_pass": True, "mean_deviance_skill": 0.2},
        "pit": {"calibrated": True},
        "time_rescaling": {"pooled_pass_exp": True},
        "psth_vs_kernel_diagnostic": {"diel": {"correlation": 0.8, "agrees": True}},
        "metrics": {"mcfadden_r2": 0.1},
        "artifact_uris": {
            "fit_report": "runs/run_abc/fit_report.json",
            "fitted_kernels": "representations/repr_abc/fitted_kernels.json",
        },
    }


def test_review_dossier_latest_and_export(monkeypatch):
    from src.aws_backend.routers import review_dossier as rd

    run_ingestion(include_live=False)
    monkeypatch.setattr(rd, "_load_fit_report", lambda: _fit_report())
    monkeypatch.setattr(rd, "load_fitted_kernels", lambda: None)
    monkeypatch.setattr(rd, "load_promotion", lambda: {"promoted": True, "effective_confidence": 1.0})
    monkeypatch.setattr(
        rd,
        "load_pending_approval",
        lambda: {
            "task_token": "SUPER-SECRET-CALLBACK-TOKEN",
            "recommendation": {"recommendation": "promote", "rationale": "passes"},
        },
    )

    client = TestClient(app)
    latest = client.get("/api/review-dossier/latest")
    assert latest.status_code == 200
    dossier = latest.json()["dossier"]
    assert dossier["provenance"]["snap_id"] == "snap_abc"
    assert dossier["provenance"]["repr_id"] == "repr_abc"
    assert dossier["provenance"]["run_id"] == "run_abc"
    assert dossier["gate_decision"]["gates"]["consistency"]["diel"]["agrees"] is True
    assert "task_token" not in str(dossier)
    assert dossier["prov"]["edges"]

    exported = client.get(f"/api/review-dossier/{dossier['dossier_id']}/export")
    assert exported.status_code == 200
    packet = exported.json()["export"]
    assert packet["export_type"] == "audit_packet"
    assert packet["dossiers"][0]["dossier_id"] == dossier["dossier_id"]
    assert "SUPER-SECRET-CALLBACK-TOKEN" not in str(packet)


def test_review_dossier_export_redacts_pii(monkeypatch):
    from src.aws_backend.models import DecisionRecord, DecisionVerdict
    from src.aws_backend.routers import review_dossier as rd
    from src.aws_backend.state import storage

    run_ingestion(include_live=False)
    storage.put_decision_record(
        DecisionRecord(
            id="d-pii",
            verdict=DecisionVerdict.PROMOTE,
            reviewer="reviewer@example.com",
            reviewer_email="reviewer@example.com",
            reason="private rationale",
        )
    )
    monkeypatch.setattr(rd, "_load_fit_report", lambda: _fit_report())
    monkeypatch.setattr(rd, "load_fitted_kernels", lambda: None)
    monkeypatch.setattr(rd, "load_promotion", lambda: None)
    monkeypatch.setattr(rd, "load_pending_approval", lambda: None)

    client = TestClient(app)
    packet = client.get("/api/review-dossier/latest/export").json()["export"]
    assert packet["pii_redacted"] is True
    blob = str(packet)
    assert "reviewer@example.com" not in blob
    assert "private rationale" not in blob


def test_unredacted_export_requires_signed_in(monkeypatch):
    import os
    from unittest.mock import patch

    from src.aws_backend.routers import review_dossier as rd

    run_ingestion(include_live=False)
    monkeypatch.setattr(rd, "_load_fit_report", lambda: _fit_report())
    monkeypatch.setattr(rd, "load_fitted_kernels", lambda: None)
    monkeypatch.setattr(rd, "load_promotion", lambda: None)
    monkeypatch.setattr(rd, "load_pending_approval", lambda: None)

    with patch.dict(os.environ, {"ORCAST_API_KEY": "audit-key"}, clear=False):
        client = TestClient(app)
        denied = client.get(
            "/api/review-dossier/latest/export?redact_pii=false",
            headers={"X-ORCAST-Key": "audit-key"},
        )
        assert denied.status_code == 401
