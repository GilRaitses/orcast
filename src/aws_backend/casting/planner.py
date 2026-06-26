"""Keyed surface planner — deterministic UI intent + skill plan."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from .models import ManagedAgent
from .panels import validate_panels
from .policy import filter_deep_links, validate_skill_plan
from .registry import ManagedAgentStore

UI_INTENT_VERSION = "1.0.0"
DEFAULT_PLANNER_ID = "surface-planner-v1"


@dataclass
class PlanResult:
    ui_intent: Dict[str, Any]
    prepare: Any
    resolved_spec_hash: str


def _message_tokens(message: str) -> str:
    return message.lower()


def draft_ui_intent(
    agent: ManagedAgent,
    message: str,
    *,
    viewport: Optional[Dict[str, Any]] = None,
    focus: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Deterministic MVP planner — keyword rules, no LLM tool picking."""
    text = _message_tokens(message)
    skill_plan: List[str] = []
    panels: List[Dict[str, Any]] = []
    deep_links: List[Dict[str, str]] = [{"label": "Gates", "href": "/gates"}]

    if any(k in text for k in ("decision", "audit", "verdict")):
        skill_plan = ["fetch_gates", "fetch_decision_records"]
        panels = [
            {"id": "decisions_table", "surface": "sidebar", "priority": 1},
            {"id": "gates_summary", "surface": "sidebar", "priority": 2, "props": {"emphasis": "caution"}},
        ]
        deep_links.append({"label": "Decisions", "href": "/decisions"})
    elif any(k in text for k in ("dossier", "review")):
        skill_plan = ["fetch_gates", "fetch_review_dossier_summary"]
        panels = [
            {"id": "review_dossier", "surface": "sidebar", "priority": 1},
            {"id": "gates_summary", "surface": "sidebar", "priority": 2},
        ]
        deep_links.append({"label": "Review dossier", "href": "/review-dossier/latest"})
    elif any(k in text for k in ("promotion", "promote", "supervisor", "approval")):
        skill_plan = ["fetch_gates", "fetch_supervisor_recommendation", "fetch_pending_approval"]
        panels = [
            {"id": "gates_summary", "surface": "sidebar", "priority": 1, "props": {"emphasis": "caution"}},
            {"id": "explore_trace", "surface": "sidebar", "priority": 2},
        ]
        deep_links.append({"label": "Moderation", "href": "/moderation"})
    else:
        skill_plan = ["fetch_gates", "fetch_hotspots"]
        panels = [
            {"id": "gates_summary", "surface": "sidebar", "priority": 1},
            {"id": "explore_trace", "surface": "sidebar", "priority": 2},
        ]

    lat = lng = None
    if viewport:
        lat = viewport.get("lat")
        lng = viewport.get("lng")
    if focus and focus.get("cell"):
        try:
            parts = str(focus["cell"]).split(",")
            lat = float(parts[0].strip())
            lng = float(parts[1].strip())
        except (ValueError, IndexError):
            pass

    if lat is not None and lng is not None:
        if "fetch_provenance" not in skill_plan:
            skill_plan.append("fetch_provenance")
        panels.insert(
            0,
            {
                "id": "map_viewport",
                "surface": "map",
                "priority": 0,
                "viewport": {"lat": lat, "lng": lng, "zoom": viewport.get("zoom", 10) if viewport else 10},
            },
        )
        panels.append({"id": "provenance_pin", "surface": "map", "priority": 1})
        deep_links.append(
            {"label": "Explore pin", "href": f"/explore?lat={lat}&lng={lng}"}
        )

    allowed_skills = set(agent.skills)
    skill_plan = [s for s in skill_plan if s in allowed_skills]

    allowed_panels: Set[str] = set(agent.policy.allowed_panels or panel_ids_fallback())
    panels = [p for p in panels if p["id"] in allowed_panels]

    if not skill_plan:
        skill_plan = [s for s in agent.skills if s.startswith("fetch_gates")][:1] or agent.skills[:1]
    if not panels:
        panels = [{"id": "explore_trace", "surface": "sidebar", "priority": 1}]

    intent: Dict[str, Any] = {
        "version": UI_INTENT_VERSION,
        "planner_agent_id": agent.id,
        "skill_plan": skill_plan,
        "panels": panels,
        "deep_links": deep_links,
    }
    if lat is not None and lng is not None:
        intent["focus"] = {"cell": f"{lat},{lng}"}
    return intent


def panel_ids_fallback() -> List[str]:
    from .panels import panel_ids

    return panel_ids()


def validate_ui_intent(agent: ManagedAgent, ui_intent: Dict[str, Any]) -> None:
    if not agent.policy.planner_mode:
        raise ValueError("agent_not_planner")
    skill_plan = [str(s) for s in (ui_intent.get("skill_plan") or [])]
    if not skill_plan:
        raise ValueError("empty_skill_plan")
    validate_skill_plan(skill_plan, public_route=False)
    allowed = set(agent.policy.allowed_panels) if agent.policy.allowed_panels else None
    validate_panels(list(ui_intent.get("panels") or []), allowed=allowed)


def plan_interaction(
    store: ManagedAgentStore,
    *,
    session_id: str,
    agent_id: Optional[str],
    agent_version: Optional[str],
    message: str,
    viewport: Optional[Dict[str, Any]] = None,
    focus: Optional[Dict[str, Any]] = None,
    inline_agent: Optional[Dict[str, Any]] = None,
):
    from .concierge import _resolve_cast_agent, prepare_interaction_with_skills

    agent, _hydration = _resolve_cast_agent(
        store,
        agent_id=agent_id or DEFAULT_PLANNER_ID,
        agent_version=agent_version,
        inline_agent=inline_agent,
        session_id=session_id,
    )
    if not agent.policy.planner_mode:
        raise ValueError("agent_not_planner")

    ui_intent = draft_ui_intent(agent, message, viewport=viewport, focus=focus)
    validate_ui_intent(agent, ui_intent)

    skill_plan = list(ui_intent["skill_plan"])
    deep_links = filter_deep_links(agent, list(ui_intent.get("deep_links") or []))
    ui_intent["deep_links"] = deep_links

    prepare = prepare_interaction_with_skills(
        agent,
        message,
        skill_plan,
        viewport=viewport,
        focus=focus,
    )

    plan_step = {
        "type": "plan_output",
        "planner_agent_id": agent.id,
        "skill_plan": skill_plan,
        "panel_ids": [p["id"] for p in ui_intent.get("panels") or []],
    }
    prepare.steps.insert(1, plan_step)

    return PlanResult(
        ui_intent=ui_intent,
        prepare=prepare,
        resolved_spec_hash=agent.spec_hash(),
    )
