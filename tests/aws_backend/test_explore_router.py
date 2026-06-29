"""Tests for exploration guide API."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.aws_backend.exploration.models import GuideReply
from src.aws_backend.main import app

client = TestClient(app)


@patch("src.aws_backend.routers.explore.aurora_configured", return_value=False)
def test_explore_status_when_aurora_disabled(mock_cfg):
    resp = client.get("/api/explore/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["aurora_enabled"] is False


@patch("src.aws_backend.routers.explore.aurora_configured", return_value=False)
def test_create_session_503_without_aurora(mock_cfg):
    resp = client.post("/api/explore/sessions", json={})
    assert resp.status_code == 503


@patch("src.aws_backend.routers.explore.assert_turn_quota")
@patch("src.aws_backend.routers.explore.SessionStore")
@patch("src.aws_backend.routers.explore.aurora_configured", return_value=True)
@patch("src.aws_backend.routers.explore.compose_guide_reply")
def test_explore_turn(mock_compose, mock_cfg, mock_store_cls, mock_turn_quota):
    store = MagicMock()
    store.session_exists.return_value = True
    mock_store_cls.return_value = store
    mock_compose.return_value = GuideReply(
        reply="Gate summary here.",
        citations=[{"label": "Gates", "href": "/gates"}],
        deep_links=[{"label": "Gates", "href": "/gates"}],
        source="template",
        model=None,
        tools_used=["fetch_gates"],
        gate_ids=["level1_psth"],
    )

    resp = client.post(
        "/api/explore/turn",
        json={
            "session_id": "00000000-0000-0000-0000-000000000001",
            "message": "What gates matter?",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["reply"] == "Gate summary here."
    assert "fetch_gates" in body["tools_used"]
    store.save_exchange.assert_called_once()
