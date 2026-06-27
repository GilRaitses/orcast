import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.aws_backend.main import app
from src.aws_backend.sources.community import CommunitySubmissionAdapter
from src.aws_backend.state import storage
from tests.aws_backend.conftest_governance import governance_headers


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

    approve = client.post(
        f"/api/community/submissions/{submission_id}/approve",
        headers=governance_headers(),
    )
    assert approve.status_code == 200
    assert approve.json()["status"] == "approved"

    listed = client.get("/api/community/submissions?status=approved")
    assert listed.status_code == 200
    body = listed.json()
    assert body["total_count"] == 1
    assert body["submissions"][0]["id"] == submission_id


def test_moderation_stamps_reviewer_identity_and_reason():
    client = TestClient(app)
    submit = client.post(
        "/api/community/sightings",
        json=_payload(latitude=48.5, longitude=-123.1),
    )
    submission_id = submit.json()["id"]

    approve = client.post(
        f"/api/community/submissions/{submission_id}/approve",
        json={"reason": "credible shore report"},
        headers=governance_headers(
            reviewer_id="user_123",
            reviewer_email="moderator@example.com",
        ),
    )
    assert approve.status_code == 200
    body = approve.json()
    assert body["status"] == "approved"
    assert body["reviewed_by"] == "user_123"
    assert body["reviewer_email"] == "moderator@example.com"
    assert body["review_reason"] == "credible shore report"


def test_approve_missing_returns_404():
    client = TestClient(app)
    response = client.post(
        "/api/community/submissions/does-not-exist/approve",
        headers=governance_headers(),
    )
    assert response.status_code == 404


def test_double_approve_returns_409():
    client = TestClient(app)
    submission_id = client.post(
        "/api/community/sightings",
        json=_payload(latitude=48.5, longitude=-123.1),
    ).json()["id"]
    assert client.post(
        f"/api/community/submissions/{submission_id}/approve",
        headers=governance_headers(),
    ).status_code == 200
    retry = client.post(
        f"/api/community/submissions/{submission_id}/approve",
        headers=governance_headers(),
    )
    assert retry.status_code == 409
    assert "already reviewed" in retry.json()["detail"].lower()


def test_double_reject_returns_409():
    client = TestClient(app)
    submission_id = client.post(
        "/api/community/sightings",
        json=_payload(latitude=48.5, longitude=-123.1),
    ).json()["id"]
    assert client.post(
        f"/api/community/submissions/{submission_id}/reject",
        headers=governance_headers(),
    ).status_code == 200
    retry = client.post(
        f"/api/community/submissions/{submission_id}/reject",
        headers=governance_headers(),
    )
    assert retry.status_code == 409


def test_approve_without_reviewer_returns_401_when_api_key_configured():
    with patch.dict(os.environ, {"ORCAST_API_KEY": "test-secret-key"}, clear=False):
        client = TestClient(app)
        submission_id = client.post("/api/community/sightings", json=_payload()).json()["id"]
        resp = client.post(
            f"/api/community/submissions/{submission_id}/approve",
            headers={"X-ORCAST-Key": "test-secret-key"},
        )
        assert resp.status_code == 401


def test_aws_storage_moderation_uses_pending_condition():
    from src.aws_backend.storage import AwsStorage

    store = AwsStorage.__new__(AwsStorage)
    store.community_table = MagicMock()
    from src.aws_backend.models import CommunitySubmission, CommunitySubmissionStatus
    from datetime import datetime, timezone

    pending = CommunitySubmission(
        id="sub1",
        place="Test",
        observed_at=datetime.now(timezone.utc),
        status=CommunitySubmissionStatus.PENDING,
    )
    store.get_community_submission = MagicMock(return_value=pending)
    store.update_community_submission_status("sub1", "approved", reviewed_by="u1")
    _, kwargs = store.community_table.put_item.call_args
    assert kwargs["ConditionExpression"] == "#st = :pending"


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

    client.post(f"/api/community/submissions/{with_coords}/approve", headers=governance_headers())
    client.post(f"/api/community/submissions/{without_coords}/approve", headers=governance_headers())

    adapter = CommunitySubmissionAdapter()
    result = adapter.fetch()
    sightings = adapter.normalize(result)

    assert len(sightings) == 1
    assert sightings[0].source == "community"
    assert sightings[0].sighting_id == f"community:{with_coords}"
    assert result.skipped_count == 1
