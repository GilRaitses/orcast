from fastapi.testclient import TestClient

from src.aws_backend.main import app, run_ingestion


def test_health_and_seeded_sightings():
    run_ingestion(include_live=False)
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"
    assert health.json()["sightings_loaded"] > 0

    sightings = client.get("/api/verified-sightings")
    assert sightings.status_code == 200
    body = sightings.json()
    assert body["total_count"] > 0
    assert "validation_status" in body["sightings"][0]


def test_hotspots_forecast_and_probability_report():
    run_ingestion(include_live=False)
    client = TestClient(app)

    hotspots = client.get("/api/hotspots")
    assert hotspots.status_code == 200
    hotspot_body = hotspots.json()
    assert hotspot_body["total_count"] > 0
    assert 0 <= hotspot_body["hotspots"][0]["probability"] <= 1

    forecast = client.post("/forecast/quick", json={"lat": 48.5158, "lng": -123.1526})
    assert forecast.status_code == 200
    assert 0 <= forecast.json()["prediction"]["probability"] <= 1

    report = client.post("/api/reports/probability", json={"min_confidence": 0.0})
    assert report.status_code == 200
    report_body = report.json()["report"]
    assert report_body["report_id"].startswith("report_")
    assert report_body["hotspots"]

    retrieved = client.get(f"/api/reports/{report_body['report_id']}")
    assert retrieved.status_code == 200
    assert retrieved.json()["report"]["report_id"] == report_body["report_id"]

