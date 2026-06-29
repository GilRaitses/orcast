"""Tests for panel registry and planner validation."""

from __future__ import annotations

import pytest

from src.aws_backend.casting.models import load_seed_agent
from src.aws_backend.casting.panels import load_panel_registry, panel_ids, validate_panels
from src.aws_backend.casting.planner import draft_ui_intent


def test_panel_registry_loads():
    registry = load_panel_registry()
    assert "map_viewport" in registry
    assert "gates_summary" in registry
    assert len(panel_ids()) >= 7


def test_validate_panels_unknown():
    with pytest.raises(ValueError, match="invalid_panels"):
        validate_panels([{"id": "not_a_panel", "surface": "sidebar"}])


def test_planner_seed_has_planner_mode():
    agent = load_seed_agent("surface-planner-v1")
    assert agent.policy.planner_mode is True
    assert "map_viewport" in agent.policy.allowed_panels


def test_draft_ui_intent_with_viewport():
    agent = load_seed_agent("surface-planner-v1")
    intent = draft_ui_intent(
        agent,
        "Explain gates",
        viewport={"lat": 48.55, "lng": -123.05, "zoom": 11},
    )
    assert "map_viewport" in [p["id"] for p in intent["panels"]]
    assert intent["focus"]["cell"] == "48.55,-123.05"
