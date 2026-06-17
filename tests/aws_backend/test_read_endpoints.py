from fastapi.testclient import TestClient

from src.aws_backend.main import app, run_ingestion
from src.aws_backend.models import ValidationStatus


def test_verified_sightings_excludes_rejected():
    run_ingestion(include_live=False)
    client = TestClient(app)

    all_sightings = client.get("/api/sightings").json()["sightings"]
    verified = client.get("/api/verified-sightings").json()

    rejected = [s for s in all_sightings if s["cross_validation"]["status"] == ValidationStatus.REJECTED.value]
    tentative = [s for s in all_sightings if s["cross_validation"]["status"] == ValidationStatus.TENTATIVE.value]

    for sighting in verified["sightings"]:
        assert sighting["validation_status"] in {ValidationStatus.VERIFIED.value, ValidationStatus.LIKELY.value}

    if rejected or tentative:
        assert verified["total_count"] < len(all_sightings)


def test_realtime_events_honest_fields():
    run_ingestion(include_live=False)
    client = TestClient(app)
    body = client.get("/api/realtime/events").json()

    assert body["data_freshness"] == "historical"
    assert body["stream_active"] is False
    if body["events"]:
        event = body["events"][0]
        assert event["event_type"] == "sighting"
        assert "hydrophone" not in event
        assert "callType" not in event


def test_live_hydrophones_static_catalog():
    client = TestClient(app)
    body = client.get("/api/live-hydrophones").json()
    assert body["source"] == "static_catalog"
    assert body["live_status_check"] is False


def test_health_includes_sources():
    run_ingestion(include_live=False)
    client = TestClient(app)
    health = client.get("/health").json()
    assert health["status"] in {"healthy", "degraded"}
    assert "sources" in health


def test_api_status_lists_deprecated_routes():
    client = TestClient(app)
    body = client.get("/api/status").json()
    assert "/api/predictions" in body["deprecated_routes"]
    assert "/api/reports/probability" in body["endpoints"]
