"""Tests for managed agent interactions API."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.aws_backend.casting.concierge import InteractionResult, PrepareResult
from src.aws_backend.exploration.models import GuideReply
from src.aws_backend.main import app

client = TestClient(app)

SESSION = "00000000-0000-0000-0000-000000000001"


@patch("src.aws_backend.routers.interactions.aurora_configured", return_value=False)
def test_interactions_status(mock_cfg):
    resp = client.get("/api/interactions/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "casting_enabled" in body


@patch("src.aws_backend.routers.interactions.assert_turn_quota")
@patch("src.aws_backend.routers.interactions.SessionStore")
@patch("src.aws_backend.routers.interactions.run_interaction")
@patch("src.aws_backend.routers.interactions.aurora_configured", return_value=True)
def test_create_interaction(mock_cfg, mock_run, mock_store_cls, mock_turn_quota):
    store = MagicMock()
    store.session_exists.return_value = True
    mock_store_cls.return_value = store
    mock_run.return_value = InteractionResult(
        guide=GuideReply(
            reply="Cast reply.",
            citations=[{"label": "Gates", "href": "/gates"}],
            deep_links=[{"label": "Gates", "href": "/gates"}],
            source="template",
            model=None,
            tools_used=["fetch_gates"],
            gate_ids=["level1_psth"],
        ),
        interaction_id="11111111-1111-1111-1111-111111111111",
        managed_agent_id="explore-guide-v1",
        agent_version="1.0.0",
        resolved_spec_hash="abc123",
        hydration_mode="by_id",
        skills_invoked=["fetch_gates"],
        steps=[
            {"type": "resolve_agent", "managed_agent_id": "explore-guide-v1"},
            {"type": "skill_invocation", "skill": "fetch_gates", "output_status": "success"},
            {"type": "model_output", "provider": "template", "annotations": []},
        ],
        annotations=[{"type": "gate_citation", "label": "Fitness gates", "href": "/gates"}],
    )

    resp = client.post(
        "/api/interactions",
        json={
            "session_id": SESSION,
            "message": "What gates matter?",
            "agent_id": "explore-guide-v1",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["reply"] == "Cast reply."
    assert body["managed_agent_id"] == "explore-guide-v1"
    assert body["hydration_mode"] == "by_id"
    assert body["resolved_spec_hash"] == "abc123"
    assert body["steps"][0]["type"] == "resolve_agent"
    assert body["annotations"][0]["type"] == "gate_citation"
    store.save_interaction_exchange.assert_called_once()
    assert store.save_interaction_exchange.call_args.kwargs["interaction_steps"] == mock_run.return_value.steps
    mock_run.assert_called_once()
    assert mock_run.call_args.kwargs["session_id"] == SESSION


@patch("src.aws_backend.routers.interactions.SessionStore")
@patch("src.aws_backend.routers.interactions.prepare_interaction")
@patch("src.aws_backend.routers.interactions.aurora_configured", return_value=True)
def test_prepare_interaction(mock_cfg, mock_prepare, mock_store_cls):
    store = MagicMock()
    store.session_exists.return_value = True
    mock_store_cls.return_value = store
    mock_prepare.return_value = PrepareResult(
        managed_agent_id="explore-guide-v1",
        agent_version="1.0.0",
        resolved_spec_hash="abc123",
        hydration_mode="by_id",
        context={"user_message": "Hi", "gates": {"status": "success"}},
        citations=[{"label": "Gates", "href": "/gates"}],
        deep_links=[{"label": "Gates", "href": "/gates"}],
        tools_used=["fetch_gates"],
        gate_ids=["level1_psth"],
        provenance_refs=[],
        steps=[{"type": "resolve_agent", "managed_agent_id": "explore-guide-v1"}],
        annotations=[{"type": "gate_citation", "label": "Fitness gates", "href": "/gates"}],
    )

    resp = client.post(
        "/api/interactions/prepare",
        json={
            "session_id": SESSION,
            "message": "What gates matter?",
            "agent_id": "explore-guide-v1",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["hydration_mode"] == "by_id"
    assert body["context"]["gates"]["status"] == "success"
    assert body["annotations"][0]["type"] == "gate_citation"
    mock_prepare.assert_called_once()


@patch("src.aws_backend.routers.interactions.assert_turn_quota")
@patch("src.aws_backend.routers.interactions.SessionStore")
@patch("src.aws_backend.routers.interactions.run_interaction")
@patch("src.aws_backend.routers.interactions.aurora_configured", return_value=True)
def test_create_interaction_inline_agent(mock_cfg, mock_run, mock_store_cls, mock_turn_quota):
    store = MagicMock()
    store.session_exists.return_value = True
    mock_store_cls.return_value = store
    mock_run.return_value = InteractionResult(
        guide=GuideReply(
            reply="Inline cast reply.",
            citations=[],
            deep_links=[],
            source="template",
            model=None,
            tools_used=["fetch_gates"],
        ),
        interaction_id="22222222-2222-2222-2222-222222222222",
        managed_agent_id="inline-00000000",
        agent_version="inline",
        resolved_spec_hash="inlinehash",
        hydration_mode="inline",
        skills_invoked=["fetch_gates"],
        steps=[{"type": "resolve_agent", "managed_agent_id": "inline-00000000"}],
        annotations=[],
    )

    resp = client.post(
        "/api/interactions",
        json={
            "session_id": SESSION,
            "message": "Hi",
            "agent": {
                "instructions": "Test inline cast.",
                "skills": ["fetch_gates"],
            },
        },
    )
    assert resp.status_code == 200
    assert resp.json()["hydration_mode"] == "inline"
    assert mock_run.call_args.kwargs["inline_agent"] is not None


@patch("src.aws_backend.routers.interactions.assert_turn_quota")
@patch("src.aws_backend.routers.interactions.SessionStore")
@patch("src.aws_backend.routers.interactions.aurora_configured", return_value=True)
def test_inline_agent_rejects_t2_skill_on_public_route(mock_cfg, mock_store_cls, mock_turn_quota):
    store = MagicMock()
    store.session_exists.return_value = True
    mock_store_cls.return_value = store

    resp = client.post(
        "/api/interactions",
        json={
            "session_id": SESSION,
            "message": "Hi",
            "agent": {
                "instructions": "Test inline cast.",
                "skills": ["fetch_gates", "fetch_review_dossier_summary"],
            },
        },
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"] == "tier_blocked"


@patch("src.aws_backend.routers.interactions.assert_turn_quota")
@patch("src.aws_backend.routers.interactions.run_interaction")
@patch("src.aws_backend.routers.interactions.SessionStore")
@patch("src.aws_backend.routers.interactions.aurora_configured", return_value=True)
def test_interaction_unknown_agent(mock_cfg, mock_store_cls, mock_run, mock_turn_quota):
    store = MagicMock()
    store.session_exists.return_value = True
    mock_store_cls.return_value = store
    mock_run.side_effect = LookupError("Managed agent not found: missing-v1")

    resp = client.post(
        "/api/interactions",
        json={
            "session_id": SESSION,
            "message": "Hi",
            "agent_id": "missing-v1",
        },
    )
    assert resp.status_code == 404
