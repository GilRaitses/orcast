import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.aws_backend.main import app, run_ingestion


def test_post_without_key_allowed_when_unconfigured():
    run_ingestion(include_live=False)
    client = TestClient(app)
    response = client.post("/api/sightings/ingest?include_live=false")
    assert response.status_code == 200


def test_post_without_key_rejected_when_configured():
    run_ingestion(include_live=False)
    with patch.dict(os.environ, {"ORCAST_API_KEY": "test-secret-key"}, clear=False):
        client = TestClient(app)

        denied = client.post("/api/sightings/ingest?include_live=false")
        assert denied.status_code == 401

        allowed = client.post(
            "/api/sightings/ingest?include_live=false",
            headers={"X-ORCAST-Key": "test-secret-key"},
        )
        assert allowed.status_code == 200

        denied_recompute = client.post("/api/hotspots/recompute")
        assert denied_recompute.status_code == 401

        allowed_recompute = client.post(
            "/api/hotspots/recompute",
            headers={"X-ORCAST-Key": "test-secret-key"},
        )
        assert allowed_recompute.status_code == 200
