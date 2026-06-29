"""Tests for private field journal API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.aws_backend.main import create_app


def test_journal_requires_auth():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/api/journal/entries")
    assert resp.status_code == 401


def test_journal_create_list_publish():
    app = create_app()
    client = TestClient(app)
    headers = {
        "X-ORCAST-Reviewer-Id": "user_journal_test",
        "X-ORCAST-Reviewer-Email": "journal@example.com",
    }

    create = client.post(
        "/api/journal/entries",
        json={"title": "Harbor porpoise?", "place": "San Juan Island", "behavior": "unknown"},
        headers=headers,
    )
    assert create.status_code == 200
    entry_id = create.json()["entry"]["id"]

    listed = client.get("/api/journal/entries", headers=headers)
    assert listed.status_code == 200
    ids = [e["id"] for e in listed.json()["entries"]]
    assert entry_id in ids

    published = client.post(f"/api/journal/entries/{entry_id}/publish", headers=headers)
    assert published.status_code == 200
    assert published.json()["community_submission"]["status"] == "pending"
    assert published.json()["entry"]["community_submission_id"]

    again = client.post(f"/api/journal/entries/{entry_id}/publish", headers=headers)
    assert again.json()["already_published"] is True
