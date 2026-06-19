import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.aws_backend.main import app
from src.aws_backend.sources.community import CommunitySubmissionAdapter
from src.aws_backend.state import storage


@pytest.fixture(autouse=True)
def reset_storage():
    storage.community_submissions.clear()
    yield
    storage.community_submissions.clear()


def _payload(**overrides):
    body = {
        "place": "Lime Kiln Point",
        "observed_at": "2026-06-19T12:00:00+00:00",
        "behavior": "feeding",
    }
    body.update(overrides)
    return body


def test_public_submit_returns_201_pending():
    client = TestClient(app)
    response = client.post("/api/community/sightings", json=_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["id"]


def test_honeypot_silently_accepted_without_storing():
    client = TestClient(app)
    response = client.post("/api/community/sightings", json=_payload(website="http://spam.example"))
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert len(storage.community_submissions) == 0


def test_oversized_place_returns_422():
    client = TestClient(app)
    response = client.post("/api/community/sightings", json=_payload(place="x" * 201))
    assert response.status_code == 422


def test_admin_list_requires_key_when_configured():
    with patch.dict(os.environ, {"ORCAST_API_KEY": "test-secret-key"}, clear=False):
        client = TestClient(app)

        denied = client.get("/api/community/submissions?status=pending")
        assert denied.status_code == 401

        allowed = client.get(
            "/api/community/submissions?status=pending",
            headers={"X-ORCAST-Key": "test-secret-key"},
        )
        assert allowed.status_code == 200


def test_approve_flow_shows_in_approved_list():
    client = TestClient(app)
    submit = client.post(
        "/api/community/sightings",
        json=_payload(latitude=48.5, longitude=-123.1),
    )
    submission_id = submit.json()["id"]

    approve = client.post(f"/api/community/submissions/{submission_id}/approve")
    assert approve.status_code == 200
    assert approve.json()["status"] == "approved"

    listed = client.get("/api/community/submissions?status=approved")
    assert listed.status_code == 200
    body = listed.json()
    assert body["total_count"] == 1
    assert body["submissions"][0]["id"] == submission_id


def test_approve_missing_returns_404():
    client = TestClient(app)
    response = client.post("/api/community/submissions/does-not-exist/approve")
    assert response.status_code == 404


def test_adapter_normalizes_approved_with_coords_and_skips_without():
    client = TestClient(app)

    with_coords = client.post(
        "/api/community/sightings",
        json=_payload(latitude=48.5, longitude=-123.1),
    ).json()["id"]
    without_coords = client.post(
        "/api/community/sightings",
        json=_payload(place="Unknown spot"),
    ).json()["id"]

    client.post(f"/api/community/submissions/{with_coords}/approve")
    client.post(f"/api/community/submissions/{without_coords}/approve")

    adapter = CommunitySubmissionAdapter()
    result = adapter.fetch()
    sightings = adapter.normalize(result)

    assert len(sightings) == 1
    assert sightings[0].source == "community"
    assert sightings[0].sighting_id == f"community:{with_coords}"
    assert result.skipped_count == 1
