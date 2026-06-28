"""Tests for keyed surface planner (/api/interactions/plan)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.aws_backend.casting.planner import draft_ui_intent, validate_ui_intent
from src.aws_backend.casting.models import load_seed_agent
from src.aws_backend.main import app

client = TestClient(app)

SESSION = "00000000-0000-0000-0000-000000000002"
API_KEY = "test-orcast-key"


@patch("src.aws_backend.auth.settings")
def test_plan_requires_api_key(mock_settings):
    mock_settings.api_key = API_KEY
    resp = client.post(
        "/api/interactions/plan",
        json={"session_id": SESSION, "message": "Show gates"},
    )
    assert resp.status_code == 401


@patch("src.aws_backend.routers.interactions.plan_interaction")
@patch("src.aws_backend.routers.interactions.SessionStore")
@patch("src.aws_backend.routers.interactions.aurora_configured", return_value=True)
@patch("src.aws_backend.auth.settings")
def test_plan_returns_ui_intent(mock_settings, mock_cfg, mock_store_cls, mock_plan):
    mock_settings.api_key = API_KEY
    store = MagicMock()
    store.session_exists.return_value = True
    mock_store_cls.return_value = store

    from src.aws_backend.casting.concierge import PrepareResult

    mock_plan.return_value = MagicMock(
        ui_intent={
            "version": "1.0.0",
            "planner_agent_id": "surface-planner-v1",
            "skill_plan": ["fetch_gates"],
            "panels": [{"id": "gates_summary", "surface": "sidebar", "priority": 1}],
            "deep_links": [{"label": "Gates", "href": "/gates"}],
        },
        prepare=PrepareResult(
            managed_agent_id="surface-planner-v1",
            agent_version="1.0.0",
            resolved_spec_hash="plannerhash",
            hydration_mode="by_id",
            context={"gates": {"status": "success"}},
            citations=[],
            deep_links=[],
            tools_used=["fetch_gates"],
            gate_ids=[],
            provenance_refs=[],
            steps=[
                {"type": "resolve_agent", "managed_agent_id": "surface-planner-v1"},
                {"type": "plan_output", "skill_plan": ["fetch_gates"], "panel_ids": ["gates_summary"]},
            ],
            annotations=[],
        ),
        resolved_spec_hash="plannerhash",
    )

    resp = client.post(
        "/api/interactions/plan",
        headers={"X-ORCAST-Key": API_KEY},
        json={"session_id": SESSION, "message": "Which gates block promotion?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ui_intent"]["version"] == "1.0.0"
    assert body["ui_intent"]["skill_plan"] == ["fetch_gates"]
    assert body["prepare"]["context"]["gates"]["status"] == "success"
    assert any(s.get("type") == "plan_output" for s in body["prepare"]["steps"])


def test_draft_ui_intent_decision_keywords():
    agent = load_seed_agent("surface-planner-v1")
    intent = draft_ui_intent(agent, "Show decision audit log")
    assert "fetch_decision_records" in intent["skill_plan"]
    panel_ids = [p["id"] for p in intent["panels"]]
    assert "decisions_table" in panel_ids


def test_validate_ui_intent_rejects_unknown_panel():
    agent = load_seed_agent("surface-planner-v1")
    intent = draft_ui_intent(agent, "Show gates")
    intent["panels"].append({"id": "unknown_panel", "surface": "sidebar"})
    try:
        validate_ui_intent(agent, intent)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "invalid_panels" in str(exc)


@patch("src.aws_backend.auth.settings")
def test_narrate_requires_api_key(mock_settings):
    mock_settings.api_key = API_KEY
    resp = client.post(
        "/api/interactions/narrate",
        json={
            "session_id": SESSION,
            "message": "Plan a visit",
            "agent": {"instructions": "x", "skills": ["fetch_gates"]},
        },
    )
    assert resp.status_code == 401


@patch("src.aws_backend.exploration.guide.compose_guide_reply")
@patch("src.aws_backend.casting.concierge._resolve_cast_agent")
@patch("src.aws_backend.routers.interactions.SessionStore")
@patch("src.aws_backend.routers.interactions.aurora_configured", return_value=True)
@patch("src.aws_backend.auth.settings")
def test_narrate_reuses_prepared_context(
    mock_settings, mock_cfg, mock_store_cls, mock_resolve, mock_compose
):
    """Phase-2 narration must reuse the plan's grounded context (no skills re-run)."""
    mock_settings.api_key = API_KEY
    store = MagicMock()
    store.session_exists.return_value = True
    mock_store_cls.return_value = store

    agent = MagicMock()
    agent.instructions = "inline planner"
    agent.model = {"model_id": "test-model"}
    mock_resolve.return_value = (agent, None)

    from src.aws_backend.exploration.models import GuideReply

    mock_compose.return_value = GuideReply(
        reply="hello narration",
        citations=[],
        deep_links=[],
        source="bedrock",
        model="test-model",
        tools_used=["fetch_gates"],
        gate_ids=["G1"],
        provenance_refs=["P1"],
    )

    resp = client.post(
        "/api/interactions/narrate",
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
            "gate_ids": ["G1"],
            "provenance_refs": ["P1"],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["reply"] == "hello narration"
    assert body["source"] == "bedrock"

    # The prepared context is passed straight through as prefetched, proving the
    # narration phase does NOT re-dispatch skills or live source calls.
    _, kwargs = mock_compose.call_args
    prefetched = kwargs["prefetched"]
    assert prefetched[0] == {"gates": {"status": "success"}}
    assert prefetched[4] == ["G1"]
    assert prefetched[5] == ["P1"]
    # And it persists exactly one exchange (durability).
    assert store.save_interaction_exchange.call_count == 1


@patch("src.aws_backend.routers.interactions.assert_turn_quota")
@patch("src.aws_backend.routers.interactions.SessionStore")
@patch("src.aws_backend.routers.interactions.aurora_configured", return_value=True)
def test_public_interaction_still_rejects_t2_skill(mock_cfg, mock_store_cls, mock_turn_quota):
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
                "skills": ["fetch_gates", "fetch_decision_records"],
            },
        },
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"] == "tier_blocked"
