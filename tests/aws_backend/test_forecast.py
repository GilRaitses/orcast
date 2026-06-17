from fastapi.testclient import TestClient

from src.aws_backend.main import app, run_ingestion


def test_spatial_forecast_hours_changes_output():
    run_ingestion(include_live=False)
    client = TestClient(app)
    base = {"lat": 48.5158, "lng": -123.1526, "radius_km": 5, "grid_resolution": 0.05}

    short = client.post("/forecast/spatial", json={**base, "hours": 6})
    long = client.post("/forecast/spatial", json={**base, "hours": 168})
    assert short.status_code == 200
    assert long.status_code == 200

    short_probs = [p["probability"] for p in short.json()["grid_points"]]
    long_probs = [p["probability"] for p in long.json()["grid_points"]]
    assert max(short_probs) < max(long_probs)


def test_forecast_uses_deterministic_model_label():
    run_ingestion(include_live=False)
    client = TestClient(app)
    status = client.get("/forecast/status").json()
    assert status["model"] == "aws-deterministic-hotspot-v1"


def test_deprecated_routes_return_410():
    client = TestClient(app)
    for path in ["/api/predictions", "/api/behavioral-analysis", "/api/dtag-data"]:
        response = client.get(path)
        assert response.status_code == 410
        detail = response.json()["detail"]
        assert detail["deprecated"] is True
        assert detail["replacement"]
