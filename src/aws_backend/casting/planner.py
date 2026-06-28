"""Keyed surface planner — deterministic UI intent + skill plan."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .models import ManagedAgent
from .panels import validate_panels
from .policy import filter_deep_links, validate_skill_plan
from .registry import ManagedAgentStore

logger = logging.getLogger(__name__)

UI_INTENT_VERSION = "1.0.0"
DEFAULT_PLANNER_ID = "surface-planner-v1"

# The four orienting-question branches. The contract enum lives in the browser
# (web/lib/trips/model.ts JourneyBranch); these strings mirror it exactly.
JOURNEY_BRANCHES = ("visiting", "here-now", "kayak", "curious")


@dataclass
class PlanResult:
    ui_intent: Dict[str, Any]
    prepare: Any
    resolved_spec_hash: str


def _message_tokens(message: str) -> str:
    return message.lower()


# --------------------------------------------------------------------------- #
# Corridor <-> connections seam adapter (the reconciled field + assembly layer)
# --------------------------------------------------------------------------- #
#
# RECONCILIATION. The corridor model (modeling/traffic/corridor.py) landed
# PER-ROUTE and with different field names than connections documents:
#
#     corridor.predict_eta(route_id, depart_dt) -> {
#         "eta_minutes": float | None,
#         "interval": {"low_minutes": float, "high_minutes": float} | None,
#         "basis": {"method": str, "n_samples": int, ...},   # a dict, not a str
#         "label": "MODELED",
#     }
#
# but connections.plan_connection consumes a SINGLE-CORRIDOR callable matching
# the documented contract its _build_drive_leg reads:
#
#     predict_eta(depart_dt) -> {
#         "eta": float | None,                 # not "eta_minutes"
#         "interval": [low_minutes, high_minutes] | None,   # a list, not a dict
#         "basis": str | None,                 # a flat string, not a dict
#     }
#
# This adapter closes the gap at the wiring layer so no phase-A module is
# rewritten. It owns the multi-segment assembly that connections expects to be
# done for it: it sums the southern measured-segment predictions resolved via
# wsdot_traffic.corridor_route_ids(), maps eta_minutes -> eta and the interval
# dict -> a [low, high] list, flattens the basis dict's method into a string,
# and ADDS the always-modeled northern Arlington -> Anacortes free-flow leg that
# WSDOT TravelTimes never covers. connections then surfaces the northern leg as
# a modeled segment and labels the whole drive leg MODELED, so the drive can
# never read as measured.

# Modeled free-flow estimate for the unmeasured northern leg. WSDOT TravelTimes
# coverage on I-5 ends near Arlington around milepost 208, so the final ~40 mi
# of SR 20 / I-5 to Anacortes has no measured product and is always modeled.
_NORTHERN_LEG_MINUTES = 40.0
_NORTHERN_LEG_INTERVAL: Tuple[float, float] = (35.0, 52.0)


def aggregate_corridor_eta(
    depart_dt: datetime,
    *,
    route_ids: List[int],
    predict_route_eta: Callable[..., Dict[str, Any]],
) -> Dict[str, Any]:
    """Sum the per-route corridor model into the documented drive-total shape.

    Returns ``{"eta", "interval", "basis"}`` where ``eta`` is total minutes (or
    ``None`` when no southern segment produced an estimate), ``interval`` is
    ``[low, high]`` minutes (or ``None``), and ``basis`` is a flat string. When
    no southern segment resolves, the result is unknown rather than "just the
    northern leg" so a partial corridor never understates the drive.
    """
    southern_etas: List[float] = []
    low_sum = 0.0
    high_sum = 0.0
    methods: List[str] = []

    for rid in route_ids:
        try:
            result = predict_route_eta(rid, depart_dt) or {}
        except Exception as exc:  # a sibling producer may raise; degrade to skip
            logger.warning("planner: corridor predict_eta(%s) failed: %s", rid, exc)
            continue
        eta = result.get("eta_minutes")
        if not isinstance(eta, (int, float)) or isinstance(eta, bool):
            continue
        southern_etas.append(float(eta))
        interval = result.get("interval")
        if (
            isinstance(interval, dict)
            and isinstance(interval.get("low_minutes"), (int, float))
            and isinstance(interval.get("high_minutes"), (int, float))
        ):
            low_sum += float(interval["low_minutes"])
            high_sum += float(interval["high_minutes"])
        else:
            # No segment interval -> use the point estimate so the summed band
            # stays consistent rather than silently shrinking.
            low_sum += float(eta)
            high_sum += float(eta)
        basis = result.get("basis")
        if isinstance(basis, dict) and isinstance(basis.get("method"), str):
            methods.append(basis["method"])

    if not southern_etas:
        return {"eta": None, "interval": None, "basis": None}

    total_eta = sum(southern_etas) + _NORTHERN_LEG_MINUTES
    total_low = low_sum + _NORTHERN_LEG_INTERVAL[0]
    total_high = high_sum + _NORTHERN_LEG_INTERVAL[1]

    if methods and all(m == "modeled_history" for m in methods):
        basis = "modeled_history"
    else:
        # Any segment that leaned on the latest-measured fallback (or had no
        # history bucket) downgrades the honesty of the whole drive estimate.
        basis = "modeled_fallback_latest_measured"

    return {
        "eta": round(total_eta, 1),
        "interval": [round(total_low, 1), round(total_high, 1)],
        "basis": basis,
    }


def _corridor_eta_adapter() -> Callable[[datetime], Dict[str, Any]]:
    """Return a ``predict_eta(depart_dt)`` callable wrapping the real corridor.

    Resolves the corridor model and the corridor route ids lazily so this
    planner module stays importable when the modeling package or the WSDOT
    client is absent, and so a thin-history / missing-log runtime degrades to an
    honest "unknown" drive rather than raising.
    """

    def adapter(depart_dt: datetime) -> Dict[str, Any]:
        try:
            from modeling.traffic import corridor
            from src.aws_backend.sources import wsdot_traffic
        except Exception as exc:  # pragma: no cover - exercised when sibling absent
            logger.debug("planner: corridor adapter unavailable (%s)", exc)
            return {"eta": None, "interval": None, "basis": None}
        try:
            route_ids = wsdot_traffic.corridor_route_ids()
        except Exception as exc:
            logger.warning("planner: corridor_route_ids failed: %s", exc)
            route_ids = []
        return aggregate_corridor_eta(
            depart_dt, route_ids=route_ids, predict_route_eta=corridor.predict_eta
        )

    return adapter


def _connection_clients() -> Any:
    """Wire the production connection clients with the corridor adapter swapped in.

    ``ConnectionClients.default()`` would resolve the raw PER-ROUTE
    ``corridor.predict_eta`` (wrong arity and field names for the connections
    contract), so the adapter replaces it with the reconciled single-corridor
    callable. The WSF / flight / seaplane adapters keep their default wiring and
    degrade to empty when their access codes are unset.
    """
    from .trips.connections import ConnectionClients

    clients = ConnectionClients.default()
    clients.predict_eta = _corridor_eta_adapter()
    return clients


def build_connection_plan(
    branch: str,
    message: str,
    focus: Optional[Dict[str, Any]],
    connection_clients: Any = None,
) -> Optional[Dict[str, Any]]:
    """Assemble the labeled connection plan for a visiting / here-now branch.

    The connection intent (route, terminals, departure time) rides the turn on
    ``focus["connection"]``; absent specifics yield an honest "unknown" plan
    rather than a fabricated one. ``connection_clients`` is injected in tests so
    the assembly runs offline with no live source calls.
    """
    from .trips.connections import plan_connection

    clients = connection_clients or _connection_clients()
    intent: Dict[str, Any] = {}
    if focus and isinstance(focus.get("connection"), dict):
        intent = dict(focus["connection"])
    intent.setdefault("mode", "ferry")
    intent.setdefault("ferry", intent.get("ferry") or {})
    intent["branch"] = branch
    intent.setdefault("question", message)
    try:
        return plan_connection(intent, clients=clients)
    except Exception as exc:  # assembly must never fail the planner turn
        logger.warning("planner: plan_connection failed: %s", exc)
        return None


# --------------------------------------------------------------------------- #
# Branch panel-prop defaults (presentational seeds; honesty labels travel here)
# --------------------------------------------------------------------------- #

_DEFAULT_SIDEQUESTS: List[Dict[str, Any]] = [
    {
        "id": "listen-hydrophone",
        "kind": "hydrophone",
        "title": "Listen to a live hydrophone",
        "prompt": (
            "Drop onto a live Orcasound feed and listen for calls, then bring "
            "what you hear into a planned trip."
        ),
        "honestyLabel": "measured",
        "invite": {"label": "Plan a listening trip", "redirectTo": "/explore"},
    },
    {
        "id": "replay-sighting",
        "kind": "sighting-replay",
        "title": "Replay a recent sighting",
        "prompt": (
            "Step back through a recently verified sighting on the map, then "
            "turn it into a route you can follow."
        ),
        "honestyLabel": "published",
        "invite": {"label": "Plan around this sighting", "redirectTo": "/explore"},
    },
    {
        "id": "explain-cell",
        "kind": "cell-score",
        "title": "Explain a cell score",
        "prompt": (
            "See why a map cell scores the way it does from its kernel "
            "contributions, then plan a visit to a strong cell."
        ),
        "honestyLabel": "modeled",
        "invite": {"label": "Plan a visit", "redirectTo": "/explore"},
    },
]

_DEFAULT_KAYAK_SAFETY: List[str] = [
    "Check the marine forecast before launching.",
    "Stay within your group's paddling range.",
    "Treat unknown windows as unsafe, not as safe water.",
]


def _sidequest_props(focus: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    override = (focus or {}).get("sidequests")
    items = override if isinstance(override, list) and override else _DEFAULT_SIDEQUESTS
    tier = (focus or {}).get("viewer_tier") or "anonymous-public"
    return {
        "items": items,
        "viewerTier": tier,
        "confirm": {
            "label": "Authorize this charter",
            "reason": "Sign in to authorize this charter without leaving the scene",
            "redirectTo": "/explore",
        },
        "note": "Each detour ends by inviting you into the trip platform.",
    }


def _kayak_props(focus: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    override = (focus or {}).get("kayak")
    if isinstance(override, dict):
        props = dict(override)
        props.setdefault("safety", _DEFAULT_KAYAK_SAFETY)
        props.setdefault("windows", props.get("windows") or [])
        return props
    # No server-side tide series supplied: render windows as unknown, never safe.
    return {"windows": [], "safety": _DEFAULT_KAYAK_SAFETY}


def _branch_signal(focus: Optional[Dict[str, Any]]) -> Optional[str]:
    """Read the orienting-question branch from the turn, if present and valid.

    The branch rides ``focus["branch"]`` (already threaded through
    ``plan_interaction``); an absent or unrecognized value falls back to the
    keyword planner so this is a strictly additive seam.
    """
    if not focus:
        return None
    raw = focus.get("branch")
    if not isinstance(raw, str):
        return None
    branch = raw.strip().lower()
    return branch if branch in JOURNEY_BRANCHES else None


def _keyword_plan(
    text: str,
) -> Tuple[List[str], List[Dict[str, Any]], List[Dict[str, str]]]:
    """Today's deterministic keyword rules (governance / default surfaces)."""
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
    return skill_plan, panels, deep_links


def _branch_plan(
    branch: str,
    message: str,
    focus: Optional[Dict[str, Any]],
    connection_clients: Any,
) -> Tuple[List[str], List[Dict[str, Any]], List[Dict[str, str]]]:
    """Per-branch skill plan + panels for the orienting question.

    visiting / here-now consume the connections planner and attach the labeled
    plan to the ``connections_plan`` panel props. kayak calls the tide model
    (windows arrive as server-side props). curious surfaces sidequests + the
    inline auth chip. The forecast stays on the hotspot heuristic; no ML is
    promoted, and only public T0/T1 skills are used so the anonymous route works.
    """
    deep_links: List[Dict[str, str]] = [{"label": "Gates", "href": "/gates"}]

    if branch == "visiting":
        skill_plan = ["fetch_gates", "fetch_hotspots"]
        panels = [
            {"id": "compare_places", "surface": "sidebar", "priority": 1, "props": {"scope": "broad"}},
            {"id": "explore_trace", "surface": "sidebar", "priority": 3},
        ]
        plan = build_connection_plan(branch, message, focus, connection_clients)
        panels.insert(
            1,
            {"id": "connections_plan", "surface": "sidebar", "priority": 2, "props": {"plan": plan}},
        )
        deep_links.append({"label": "Explore", "href": "/explore"})
    elif branch == "here-now":
        skill_plan = ["fetch_gates", "fetch_hotspots", "fetch_provenance"]
        panels = [
            {"id": "local_area", "surface": "sidebar", "priority": 1, "props": {"scope": "focused"}},
            {"id": "provenance_pin", "surface": "map", "priority": 3},
        ]
        plan = build_connection_plan(branch, message, focus, connection_clients)
        panels.insert(
            1,
            {"id": "connections_plan", "surface": "sidebar", "priority": 2, "props": {"plan": plan}},
        )
        deep_links.append({"label": "Explore", "href": "/explore"})
    elif branch == "kayak":
        skill_plan = ["fetch_gates", "fetch_hotspots", "fetch_environmental"]
        panels = [
            {"id": "kayak_plan", "surface": "sidebar", "priority": 1, "props": _kayak_props(focus)},
        ]
        deep_links.append({"label": "Explore", "href": "/explore"})
    else:  # curious
        skill_plan = ["fetch_gates", "fetch_live_hydrophones", "fetch_verified_sightings"]
        panels = [
            {"id": "sidequests", "surface": "sidebar", "priority": 1, "props": _sidequest_props(focus)},
            {"id": "explore_trace", "surface": "sidebar", "priority": 2},
        ]
        deep_links.append({"label": "Explore", "href": "/explore"})

    return skill_plan, panels, deep_links


def draft_ui_intent(
    agent: ManagedAgent,
    message: str,
    *,
    viewport: Optional[Dict[str, Any]] = None,
    focus: Optional[Dict[str, Any]] = None,
    connection_clients: Any = None,
) -> Dict[str, Any]:
    """Deterministic MVP planner — keyword rules + the orienting-question branch.

    When the turn carries a valid ``focus["branch"]`` the per-branch builder runs
    (compare-places / local-area / kayak / sidequest); otherwise today's keyword
    rules apply. ``connection_clients`` is injected in tests so the visiting /
    here-now connection assembly runs offline with no live source calls.
    """
    text = _message_tokens(message)
    branch = _branch_signal(focus)
    if branch is not None:
        skill_plan, panels, deep_links = _branch_plan(
            branch, message, focus, connection_clients
        )
    else:
        skill_plan, panels, deep_links = _keyword_plan(text)

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
        if not any(p["id"] == "map_viewport" for p in panels):
            panels.insert(
                0,
                {
                    "id": "map_viewport",
                    "surface": "map",
                    "priority": 0,
                    "viewport": {"lat": lat, "lng": lng, "zoom": viewport.get("zoom", 10) if viewport else 10},
                },
            )
        if not any(p["id"] == "provenance_pin" for p in panels):
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
    if branch is not None:
        intent["branch"] = branch
    if lat is not None and lng is not None:
        intent["focus"] = {"cell": f"{lat},{lng}"}
    return intent


def panel_ids_fallback() -> List[str]:
    from .panels import panel_ids

    return panel_ids()


def validate_ui_intent(
    agent: ManagedAgent, ui_intent: Dict[str, Any], *, public_route: bool = False
) -> None:
    if not agent.policy.planner_mode:
        raise ValueError("agent_not_planner")
    skill_plan = [str(s) for s in (ui_intent.get("skill_plan") or [])]
    if not skill_plan:
        raise ValueError("empty_skill_plan")
    validate_skill_plan(skill_plan, public_route=public_route)
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
    public_route: bool = False,
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
    validate_ui_intent(agent, ui_intent, public_route=public_route)

    skill_plan = list(ui_intent["skill_plan"])
    deep_links = filter_deep_links(agent, list(ui_intent.get("deep_links") or []))
    ui_intent["deep_links"] = deep_links

    prepare = prepare_interaction_with_skills(
        agent,
        message,
        skill_plan,
        viewport=viewport,
        focus=focus,
        public_route=public_route,
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
