"""Tests for the whale-tagger read API (B-side build order step 1)."""
from fastapi.testclient import TestClient

from src.aws_backend.main import app

client = TestClient(app)

EXAMPLE_ID = "cascadia_2010_k33_test"


def test_list_deployments_includes_simulated_example():
    resp = client.get("/api/dtag/deployments")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["partnership_gated"] is True
    ids = {d["deployment_id"] for d in body["deployments"]}
    assert EXAMPLE_ID in ids
    example = next(d for d in body["deployments"] if d["deployment_id"] == EXAMPLE_ID)
    assert example["simulated"] is True


def test_get_deployment_summary():
    resp = client.get(f"/api/dtag/deployments/{EXAMPLE_ID}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["simulated"] is True
    assert body["total_dives"] >= 1


def test_get_dives_returns_events():
    resp = client.get(f"/api/dtag/dives/{EXAMPLE_ID}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["total_dives"] == len(body["dives"])
    assert body["total_dives"] >= 1


def test_feeding_is_not_trained_with_caveat():
    resp = client.get(f"/api/dtag/feeding/{EXAMPLE_ID}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["model_state"] == "not_trained"
    assert body["uniform_probability"] is True
    assert body["caveat"]
    for seg in body["segments"]:
        assert seg["model_probability"] is None


def test_unknown_deployment_is_not_available():
    resp = client.get("/api/dtag/deployments/does_not_exist")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "not_available"
    assert EXAMPLE_ID in body["available_deployments"]


def test_deprecated_dtag_data_points_to_new_surface():
    resp = client.get("/api/dtag-data")
    assert resp.status_code == 410
    assert resp.json()["detail"]["replacement"] == "/api/dtag/deployments"
