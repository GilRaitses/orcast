"""Tests for streamed narration (/api/interactions/narrate/stream).

No live calls: the Bedrock client is monkeypatched and the session store is a
MagicMock. Covers the chunk-parsing generator, the SSE endpoint framing, the
persist-once-at-end durability, and the auth gate.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.aws_backend.main import app

client = TestClient(app)

SESSION = "00000000-0000-0000-0000-000000000003"
API_KEY = "test-orcast-key"


def _delta(text: str) -> dict:
    return {
        "chunk": {
            "bytes": json.dumps(
                {"type": "content_block_delta", "delta": {"type": "text_delta", "text": text}}
            ).encode()
        }
    }


def _control(event_type: str) -> dict:
    return {"chunk": {"bytes": json.dumps({"type": event_type}).encode()}}


def test_bedrock_guide_stream_parses_text_deltas():
    """Only content_block_delta/text_delta events produce tokens; control events ignored."""
    from src.aws_backend.exploration import guide

    fake_client = MagicMock()
    fake_client.invoke_model_with_response_stream.return_value = {
        "body": [
            _control("message_start"),
            _control("content_block_start"),
            _delta("Hello "),
            # a non-text delta (e.g. input_json_delta) must be skipped
            {"chunk": {"bytes": json.dumps({"type": "content_block_delta", "delta": {"type": "other"}}).encode()}},
            _delta("world"),
            _control("content_block_stop"),
            _control("message_stop"),
        ]
    }
    with patch("boto3.client", return_value=fake_client):
        out = "".join(guide._bedrock_guide_stream({"user_message": "hi"}, "sys", "model-x"))
    assert out == "Hello world"


def test_narrate_stream_requires_api_key():
    with patch("src.aws_backend.auth.settings") as mock_settings:
        mock_settings.api_key = API_KEY
        resp = client.post(
            "/api/interactions/narrate/stream",
            json={
                "session_id": SESSION,
                "message": "Plan a visit",
                "agent": {"instructions": "x", "skills": ["fetch_gates"]},
            },
        )
    assert resp.status_code == 401


@patch("src.aws_backend.routers.interactions.assert_turn_quota")
@patch("src.aws_backend.routers.interactions.settings")
@patch("src.aws_backend.exploration.guide._bedrock_guide_stream")
@patch("src.aws_backend.casting.concierge._resolve_cast_agent")
@patch("src.aws_backend.routers.interactions.SessionStore")
@patch("src.aws_backend.routers.interactions.aurora_configured", return_value=True)
@patch("src.aws_backend.auth.settings")
def test_narrate_stream_emits_frames_and_persists_once(
    mock_auth_settings,
    mock_cfg,
    mock_store_cls,
    mock_resolve,
    mock_stream,
    mock_settings,
    mock_quota,
):
    """meta -> token -> done framing, prefetched metadata in meta, one persist."""
    mock_auth_settings.api_key = API_KEY
    mock_settings.enable_bedrock = True
    mock_settings.bedrock_sighting_model_id = "fallback-model"
    mock_settings.stream_max_seconds = 30

    store = MagicMock()
    store.session_exists.return_value = True
    mock_store_cls.return_value = store

    agent = MagicMock()
    agent.instructions = "inline planner"
    agent.model = {"model_id": "test-model"}
    mock_resolve.return_value = (agent, None)

    mock_stream.return_value = iter(["Hello ", "world"])

    resp = client.post(
        "/api/interactions/narrate/stream",
        headers={"X-ORCAST-Key": API_KEY},
        json={
            "session_id": SESSION,
            "message": "Plan a visit",
            "agent": {"instructions": "x", "skills": ["fetch_gates"]},
            "skill_plan": ["fetch_gates"],
            "context": {"gates": {"status": "success"}},
            "citations": [{"label": "Gates", "href": "/gates"}],
            "deep_links": [{"label": "Open gates", "href": "/gates"}],
            "tools_used": ["fetch_gates"],
            "gate_ids": ["G1"],
            "provenance_refs": ["P1"],
        },
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    body = resp.text
    assert "event: meta" in body
    assert "event: token" in body
    assert "event: done" in body
    # citations/deep_links ride the meta event (byte-identical to panels-first)
    assert '"citations"' in body
    assert "/gates" in body
    # the streamed prose
    assert "Hello " in body
    assert "world" in body
    # the model from the resolved agent appears in meta
    assert "test-model" in body

    # exactly one durable exchange, persisted at stream end
    assert store.save_interaction_exchange.call_count == 1
    _, kwargs = store.save_interaction_exchange.call_args
    assert kwargs["interaction_id"]
    persisted_guide = store.save_interaction_exchange.call_args[0][2]
    assert persisted_guide.reply == "Hello world"


@patch("src.aws_backend.routers.interactions.assert_turn_quota")
@patch("src.aws_backend.routers.interactions.settings")
@patch("src.aws_backend.exploration.guide._bedrock_guide_stream")
@patch("src.aws_backend.casting.concierge._resolve_cast_agent")
@patch("src.aws_backend.routers.interactions.SessionStore")
@patch("src.aws_backend.routers.interactions.aurora_configured", return_value=True)
@patch("src.aws_backend.auth.settings")
def test_narrate_stream_error_persists_nothing(
    mock_auth_settings,
    mock_cfg,
    mock_store_cls,
    mock_resolve,
    mock_stream,
    mock_settings,
    mock_quota,
):
    """A mid-stream Bedrock failure emits an error frame and writes no DB turn."""
    mock_auth_settings.api_key = API_KEY
    mock_settings.enable_bedrock = True
    mock_settings.bedrock_sighting_model_id = "fallback-model"
    mock_settings.stream_max_seconds = 30

    store = MagicMock()
    store.session_exists.return_value = True
    mock_store_cls.return_value = store

    agent = MagicMock()
    agent.instructions = "inline planner"
    agent.model = {"model_id": "test-model"}
    mock_resolve.return_value = (agent, None)

    def _boom():
        yield "partial "
        raise RuntimeError("bedrock blew up")

    mock_stream.return_value = _boom()

    resp = client.post(
        "/api/interactions/narrate/stream",
        headers={"X-ORCAST-Key": API_KEY},
        json={
            "session_id": SESSION,
            "message": "Plan a visit",
            "agent": {"instructions": "x", "skills": ["fetch_gates"]},
            "skill_plan": ["fetch_gates"],
            "context": {"gates": {"status": "success"}},
            "citations": [],
            "deep_links": [],
            "tools_used": ["fetch_gates"],
            "gate_ids": [],
            "provenance_refs": [],
        },
    )
    assert resp.status_code == 200
    body = resp.text
    assert "event: error" in body
    assert "event: done" not in body
    # no partial DB turn on failure
    assert store.save_interaction_exchange.call_count == 0


@patch("src.aws_backend.routers.interactions.assert_turn_quota")
@patch("src.aws_backend.casting.concierge._resolve_cast_agent")
@patch("src.aws_backend.routers.interactions.SessionStore")
@patch("src.aws_backend.routers.interactions.aurora_configured", return_value=True)
@patch("src.aws_backend.auth.settings")
def test_narrate_stream_enforces_turn_quota(
    mock_auth_settings, mock_cfg, mock_store_cls, mock_resolve, mock_quota
):
    """WS6 B1: a streamed turn is gated by the per-session turn quota (429)."""
    from src.aws_backend.exploration.limits import ExploreLimitError

    mock_auth_settings.api_key = API_KEY
    store = MagicMock()
    store.session_exists.return_value = True
    mock_store_cls.return_value = store
    mock_quota.side_effect = ExploreLimitError("turn_quota", "Max turns per session")

    resp = client.post(
        "/api/interactions/narrate/stream",
        headers={"X-ORCAST-Key": API_KEY},
        json={
            "session_id": SESSION,
            "message": "Plan a visit",
            "agent": {"instructions": "x", "skills": ["fetch_gates"]},
        },
    )
    assert resp.status_code == 429
    assert resp.json()["detail"]["error"] == "turn_quota"
    # quota rejection happens before any agent resolution / streaming
    mock_resolve.assert_not_called()


@patch("src.aws_backend.routers.interactions._stream_semaphore")
@patch("src.aws_backend.routers.interactions.settings")
@patch("src.aws_backend.routers.interactions.assert_turn_quota")
@patch("src.aws_backend.casting.concierge._resolve_cast_agent")
@patch("src.aws_backend.routers.interactions.SessionStore")
@patch("src.aws_backend.routers.interactions.aurora_configured", return_value=True)
@patch("src.aws_backend.auth.settings")
def test_narrate_stream_busy_when_concurrency_capped(
    mock_auth_settings,
    mock_cfg,
    mock_store_cls,
    mock_resolve,
    mock_quota,
    mock_settings,
    mock_sem,
):
    """WS6 M3: when no concurrency slot is free, emit a busy error and persist nothing."""
    mock_auth_settings.api_key = API_KEY
    mock_settings.enable_bedrock = True
    store = MagicMock()
    store.session_exists.return_value = True
    mock_store_cls.return_value = store
    agent = MagicMock()
    agent.instructions = "inline"
    agent.model = {"model_id": "test-model"}
    mock_resolve.return_value = (agent, None)
    mock_sem.acquire.return_value = False  # pool saturated

    resp = client.post(
        "/api/interactions/narrate/stream",
        headers={"X-ORCAST-Key": API_KEY},
        json={
            "session_id": SESSION,
            "message": "Plan a visit",
            "agent": {"instructions": "x", "skills": ["fetch_gates"]},
        },
    )
    assert resp.status_code == 200
    body = resp.text
    assert "stream_busy" in body
    assert "event: done" not in body
    assert store.save_interaction_exchange.call_count == 0
    # a refused stream must not release a slot it never took
    mock_sem.release.assert_not_called()


@patch("src.aws_backend.routers.interactions.assert_turn_quota")
@patch("src.aws_backend.routers.interactions.settings")
@patch("src.aws_backend.exploration.guide._bedrock_guide_stream")
@patch("src.aws_backend.casting.concierge._resolve_cast_agent")
@patch("src.aws_backend.routers.interactions.SessionStore")
@patch("src.aws_backend.routers.interactions.aurora_configured", return_value=True)
@patch("src.aws_backend.auth.settings")
def test_narrate_stream_wall_clock_cap(
    mock_auth_settings,
    mock_cfg,
    mock_store_cls,
    mock_resolve,
    mock_stream,
    mock_settings,
    mock_quota,
):
    """WS6 M3: a stream over the per-stream wall-clock cap errors and persists nothing."""
    mock_auth_settings.api_key = API_KEY
    mock_settings.enable_bedrock = True
    mock_settings.bedrock_sighting_model_id = "fallback-model"
    mock_settings.stream_max_seconds = -1  # deadline already passed -> cap trips immediately
    store = MagicMock()
    store.session_exists.return_value = True
    mock_store_cls.return_value = store
    agent = MagicMock()
    agent.instructions = "inline"
    agent.model = {"model_id": "test-model"}
    mock_resolve.return_value = (agent, None)
    mock_stream.return_value = iter(["one ", "two ", "three"])

    resp = client.post(
        "/api/interactions/narrate/stream",
        headers={"X-ORCAST-Key": API_KEY},
        json={
            "session_id": SESSION,
            "message": "Plan a visit",
            "agent": {"instructions": "x", "skills": ["fetch_gates"]},
        },
    )
    assert resp.status_code == 200
    body = resp.text
    assert "event: error" in body
    assert "event: done" not in body
    assert store.save_interaction_exchange.call_count == 0
