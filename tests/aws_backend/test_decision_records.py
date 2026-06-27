import os
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.aws_backend.main import app, run_ingestion
from src.aws_backend.models import DecisionRecord, DecisionVerdict
from src.aws_backend.storage import AwsStorage, MemoryStorage
from tests.aws_backend.conftest_governance import governance_headers


def test_put_get_decision_record():
    store = MemoryStorage()
    record = DecisionRecord(id="d1", verdict=DecisionVerdict.PROMOTE, reviewer="gil", reason="gates pass")
    store.put_decision_record(record)

    got = store.get_decision_record("d1")
    assert got is not None
    assert got.verdict == DecisionVerdict.PROMOTE
    assert got.reviewer == "gil"
    assert store.get_decision_record("missing") is None


def test_list_decision_records_recent_first():
    store = MemoryStorage()
    store.put_decision_record(DecisionRecord(id="a", verdict=DecisionVerdict.HOLD))
    store.put_decision_record(DecisionRecord(id="b", verdict=DecisionVerdict.PROMOTE))

    records = store.list_decision_records()
    assert len(records) == 2
    # Most recent first (b was written second).
    assert records[0].id == "b"


def test_verdict_enum_round_trips_through_dict():
    record = DecisionRecord(id="d2", verdict=DecisionVerdict.REJECT, reason="CV fails")
    payload = record.model_dump(mode="json")
    assert payload["verdict"] == "reject"
    assert DecisionRecord(**payload).verdict == DecisionVerdict.REJECT


def test_aws_storage_decision_record_is_write_once():
    """put_decision_record must guard with attribute_not_exists(pk)."""
    store = AwsStorage.__new__(AwsStorage)  # bypass boto3 __init__
    store.decision_records_table = MagicMock()
    store.put_decision_record(DecisionRecord(id="d1", verdict=DecisionVerdict.PROMOTE))

    _, kwargs = store.decision_records_table.put_item.call_args
    assert kwargs["ConditionExpression"] == "attribute_not_exists(pk)"


def test_decision_records_get_requires_key_when_configured():
    """The audit log read is keyed in production."""
    run_ingestion(include_live=False)
    with patch.dict(os.environ, {"ORCAST_API_KEY": "audit-key"}, clear=False):
        client = TestClient(app)
        assert client.get("/api/decision-records").status_code == 401
        ok = client.get("/api/decision-records", headers={"X-ORCAST-Key": "audit-key"})
        assert ok.status_code == 200


def test_decision_record_task_token_never_serialized_and_server_stamped(monkeypatch):
    """task_token is dropped from output; gates_summary/kernel_version are server-set."""
    from src.aws_backend.routers import kernel as kr

    run_ingestion(include_live=False)
    # No fit report -> server stamp is None, proving the client body is ignored.
    monkeypatch.setattr(kr, "_load_fit_report", lambda: None)
    client = TestClient(app)

    resp = client.post(
        "/api/decision-records",
        json={
            "verdict": "promote",
            "reviewer": "gil",
            "reason": "gates pass",
            "task_token": "SUPER-SECRET-CALLBACK-TOKEN",
            "gates_summary": {"spoofed": True},
            "kernel_version": "client-claims-v999",
        },
        headers=governance_headers(reviewer_id="user_test", reviewer_email="gil@example.com"),
    )
    assert resp.status_code == 200
    record = resp.json()["record"]
    assert "task_token" not in record
    assert record["gates_summary"] is None
    assert record["kernel_version"] is None

    listing = client.get("/api/decision-records").json()
    assert listing["total_count"] >= 1
    for r in listing["records"]:
        assert "task_token" not in r


def test_decision_record_stamps_trusted_reviewer_headers_and_pending_supervisor(monkeypatch):
    """Reviewer identity and supervisor rec are server-stamped, not browser-chosen."""
    from src.aws_backend.routers import kernel as kr

    run_ingestion(include_live=False)
    monkeypatch.setattr(
        kr,
        "_load_fit_report",
        lambda: {
            "status": "fitted",
            "confidence": 0.7,
            "generated_at": "2026-01-01T00:00:00Z",
            "cv": {"gate_pass": True},
            "pit": {"calibrated": True},
        },
    )
    monkeypatch.setattr(
        kr,
        "load_pending_approval",
        lambda: {
            "recommendation": {
                "recommendation": "promote",
                "rationale": "CV and PIT support promotion",
            }
        },
    )
    client = TestClient(app)

    resp = client.post(
        "/api/decision-records",
        json={
            "verdict": "promote",
            "reviewer": "spoofed-browser-reviewer",
            "reason": "Approve",
            "supervisor_recommendation": {"recommendation": "spoofed"},
        },
        headers=governance_headers(
            reviewer_id="user_123",
            reviewer_email="reviewer@example.com",
        ),
    )
    assert resp.status_code == 200
    record = resp.json()["record"]
    assert record["reviewer"] == "reviewer@example.com"
    assert record["reviewer_id"] == "user_123"
    assert record["reviewer_email"] == "reviewer@example.com"
    assert record["reviewer_role"] == "reviewer"
    assert record["supervisor_recommendation"]["recommendation"] == "promote"


def test_promotion_apply_links_to_existing_decision_record(monkeypatch):
    from src.aws_backend.routers import kernel as kr
    from src.aws_backend.routers import promotion as pr

    run_ingestion(include_live=False)
    monkeypatch.setattr(kr, "_load_fit_report", lambda: {"generated_at": "fit-v1"})
    monkeypatch.setattr(pr, "_load_fit_report", lambda: {"generated_at": "fit-v1"})

    client = TestClient(app)
    decision = client.post(
        "/api/decision-records",
        json={"verdict": "promote", "reason": "Approve"},
        headers=governance_headers(reviewer_email="reviewer@example.com"),
    ).json()["record"]

    written = {}
    monkeypatch.setattr(pr, "_write_promotion", lambda marker: written.update(marker))

    resp = client.post(
        "/api/promotion/apply",
        json={"decision_id": decision["id"], "effective_confidence": 1.0},
        headers=governance_headers(reviewer_email="reviewer@example.com"),
    )
    assert resp.status_code == 200
    marker = resp.json()["promotion"]
    assert marker["decision_id"] == decision["id"]
    assert marker["kernel_version"] == "fit-v1"
    assert marker["reviewer"] == "reviewer@example.com"
    assert written["decision_id"] == decision["id"]


def test_promote_decision_record_writes_promotion_marker(monkeypatch, tmp_path):
    from src.aws_backend.routers import kernel as kr

    run_ingestion(include_live=False)
    monkeypatch.setattr(
        kr,
        "_load_fit_report",
        lambda: {
            "generated_at": "fit-v2",
            "run_id": "run_abc",
            "repr_id": "repr_xyz",
            "confidence": 0.82,
        },
    )
    written = {}
    monkeypatch.setattr(
        "src.aws_backend.routers.promotion._write_promotion",
        lambda marker: written.update(marker),
    )

    client = TestClient(app)
    resp = client.post(
        "/api/decision-records",
        json={"verdict": "promote", "reason": "gates pass"},
        headers=governance_headers(reviewer_email="reviewer@example.com"),
    )
    assert resp.status_code == 200
    promotion = resp.json()["promotion"]
    assert promotion["decision_id"] == resp.json()["record"]["id"]
    assert promotion["run_id"] == "run_abc"
    assert promotion["repr_id"] == "repr_xyz"
    assert written["run_id"] == "run_abc"


def test_decision_without_reviewer_returns_401_when_api_key_configured():
    run_ingestion(include_live=False)
    with patch.dict(os.environ, {"ORCAST_API_KEY": "audit-key"}, clear=False):
        client = TestClient(app)
        resp = client.post(
            "/api/decision-records",
            json={"verdict": "hold", "reason": "wait"},
            headers={"X-ORCAST-Key": "audit-key"},
        )
        assert resp.status_code == 401
