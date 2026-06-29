"""Tests for managed agent registry CRUD."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from src.aws_backend.casting.models import load_seed_agent
from src.aws_backend.main import app

client = TestClient(app)


@patch("src.aws_backend.routers.managed_agents._store")
@patch("src.aws_backend.auth.settings")
def test_list_managed_agents_requires_key(mock_settings, mock_store):
    mock_settings.api_key = "test-key"
    mock_store.list_agents.return_value = [{"id": "explore-guide-v1", "version": "1.0.0"}]

    resp = client.get("/api/managed-agents")
    assert resp.status_code == 401

    resp = client.get("/api/managed-agents", headers={"X-ORCAST-Key": "test-key"})
    assert resp.status_code == 200
    assert resp.json()["agents"][0]["id"] == "explore-guide-v1"


@patch("src.aws_backend.routers.managed_agents._store")
@patch("src.aws_backend.auth.settings")
def test_get_managed_agent(mock_settings, mock_store):
    mock_settings.api_key = "test-key"
    agent = load_seed_agent("explore-guide-v1")
    mock_store.get.return_value = agent

    resp = client.get(
        "/api/managed-agents/explore-guide-v1",
        headers={"X-ORCAST-Key": "test-key"},
    )
    assert resp.status_code == 200
    body = resp.json()["agent"]
    assert body["id"] == "explore-guide-v1"
    assert "fetch_gates" in body["skills"]
    assert body["spec_hash"]


@patch("src.aws_backend.routers.managed_agents._store")
@patch("src.aws_backend.auth.settings")
def test_upsert_managed_agent(mock_settings, mock_store):
    mock_settings.api_key = "test-key"
    seed = load_seed_agent("explore-guide-v1")

    resp = client.post(
        "/api/managed-agents",
        headers={"X-ORCAST-Key": "test-key"},
        json=seed.to_dict(),
    )
    assert resp.status_code == 200
    mock_store.put.assert_called_once()
