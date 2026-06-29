"""Integration test for plan_interaction with in-memory store."""

from __future__ import annotations

from unittest.mock import patch

from src.aws_backend.casting.planner import plan_interaction
from src.aws_backend.casting.registry import MemoryManagedAgentStore


@patch("src.aws_backend.exploration.tools.fetch_gates", return_value={"status": "success", "gates": {}})
@patch(
    "src.aws_backend.exploration.tools.fetch_decision_records",
    return_value={"status": "success", "records": []},
)
def test_plan_interaction_integration(mock_decisions, mock_gates):
    store = MemoryManagedAgentStore()
    result = plan_interaction(
        store,
        session_id="00000000-0000-0000-0000-000000000099",
        agent_id="surface-planner-v1",
        agent_version=None,
        message="Show decision audit log",
        viewport={"lat": 48.55, "lng": -123.05, "zoom": 10},
    )
    assert result.ui_intent["version"] == "1.0.0"
    assert "fetch_decision_records" in result.ui_intent["skill_plan"]
    assert "decisions_table" in [p["id"] for p in result.ui_intent["panels"]]
    assert any(s.get("type") == "plan_output" for s in result.prepare.steps)
