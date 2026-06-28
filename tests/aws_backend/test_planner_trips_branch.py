"""Tests for the WS-TRIPS phase-B planner branch + corridor<->connections seam.

Offline only. The corridor model and the connection source adapters are stubs
injected through the planner's documented seams, so the suite proves the
reconciled corridor field + per-route assembly produce a labeled connection
plan without any live external call (charter B.8 / CI rule: no live calls).

The reconciliation under test:

- corridor.predict_eta is PER-ROUTE and returns ``eta_minutes`` /
  ``interval={low_minutes, high_minutes}`` / ``basis={method,...}`` (a dict).
- connections.plan_connection consumes a single-corridor ``predict_eta(depart_dt)``
  returning ``eta`` / ``interval=[low, high]`` / ``basis`` (a flat string).
- ``aggregate_corridor_eta`` sums the southern per-route predictions, maps the
  field names, flattens the basis, and adds the always-modeled northern
  Arlington -> Anacortes leg, so the drive leg can never read as measured.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.aws_backend.casting.models import load_seed_agent
from src.aws_backend.casting.planner import (
    aggregate_corridor_eta,
    draft_ui_intent,
    validate_ui_intent,
)
from src.aws_backend.casting.trips import connections as cx
from src.aws_backend.casting.trips.connections import ConnectionClients

# --------------------------------------------------------------------------- #
# Scenario fixtures: "Depart SeaTac 3 pm Friday, catch the 6:30 Anacortes sailing?"
# --------------------------------------------------------------------------- #

DEPART_ISO = "2026-06-27T15:00:00-07:00"
SAILING_ISO = "2026-06-27T18:30:00-07:00"
ARRIVE_ISO = "2026-06-27T19:30:00-07:00"

ROUTE_ID = 9
ANACORTES_TERMINAL = 1
FRIDAY_HARBOR_TERMINAL = 10
VESSEL_ID = 38

# The southern measured corridor route ids the adapter sums over.
SOUTHERN_ROUTE_IDS = [101, 202]

NOW = datetime(2026, 6, 27, 21, 55, 0, tzinfo=timezone.utc)


def _route_eta_stub(route_id, depart_dt):
    """Per-route corridor model output (the REAL corridor shape, not connections').

    eta_minutes (not eta), interval as a {low_minutes, high_minutes} dict (not a
    list), and basis as a {method,...} dict (not a flat string).
    """
    assert route_id in SOUTHERN_ROUTE_IDS
    assert isinstance(depart_dt, datetime)
    return {
        "eta_minutes": 55.0,
        "interval": {"low_minutes": 48.0, "high_minutes": 64.0},
        "basis": {"method": "modeled_history", "n_samples": 6},
        "label": "MODELED",
    }


def _corridor_adapter(depart_dt):
    """The reconciled single-corridor callable connections consumes."""
    return aggregate_corridor_eta(
        depart_dt, route_ids=SOUTHERN_ROUTE_IDS, predict_route_eta=_route_eta_stub
    )


def _schedule_stub(route_id, date):
    return {
        "terminal_combos": [
            {
                "departing_terminal_id": ANACORTES_TERMINAL,
                "departing_terminal_name": "Anacortes",
                "arriving_terminal_id": FRIDAY_HARBOR_TERMINAL,
                "arriving_terminal_name": "Friday Harbor",
                "annotations": ["Reservations required for vehicles on this sailing."],
                "times": [
                    {
                        "departing_time": SAILING_ISO,
                        "arriving_time": ARRIVE_ISO,
                        "vessel_id": VESSEL_ID,
                        "vessel_name": "Yakima",
                        "annotation_indexes": [0],
                    }
                ],
            }
        ],
    }


def _sailing_space_stub(terminal_id=None):
    return [
        {
            "terminal_id": ANACORTES_TERMINAL,
            "departing_spaces": [
                {
                    "departure": SAILING_ISO,
                    "vessel_name": "Yakima",
                    "space_for_arrival_terminals": [
                        {
                            "terminal_id": ANACORTES_TERMINAL,
                            "drive_up_space_count": 55,
                            "reservable_space_count": 32,
                            "max_space_count": 139,
                            "arrival_terminal_ids": [FRIDAY_HARBOR_TERMINAL],
                        }
                    ],
                }
            ],
        }
    ]


def _vessel_locations_stub(vessel_id=None):
    return [
        {
            "vessel_id": VESSEL_ID,
            "vessel_name": "Yakima",
            "arriving_terminal_id": FRIDAY_HARBOR_TERMINAL,
            "eta": "2026-06-27T19:28:00-07:00",
            "eta_basis": "Estimated based on position.",
            "timestamp": "2026-06-27T21:54:30+00:00",
        }
    ]


def _clients(**overrides):
    base = dict(
        schedule=_schedule_stub,
        sailing_space=_sailing_space_stub,
        vessel_locations=_vessel_locations_stub,
        predict_eta=_corridor_adapter,
        skylink_board=lambda *a, **k: [],
        seaplane_schedule=lambda *a, **k: [],
    )
    base.update(overrides)
    return ConnectionClients(**base)


def _connection_intent():
    return {
        "mode": "ferry",
        "origin": {"label": "SeaTac"},
        "depart_dt": DEPART_ISO,
        "ferry": {
            "route_id": ROUTE_ID,
            "departing_terminal_id": ANACORTES_TERMINAL,
            "departing_terminal_name": "Anacortes",
            "arriving_terminal_id": FRIDAY_HARBOR_TERMINAL,
            "arriving_terminal_name": "Friday Harbor",
            "depart_clock": "18:30",
        },
    }


# --------------------------------------------------------------------------- #
# 1. The corridor <-> connections seam adapter (field + assembly reconciliation)
# --------------------------------------------------------------------------- #

def test_adapter_reconciles_field_names_and_sums_segments_plus_northern_leg():
    depart = datetime(2026, 6, 27, 15, 0, 0)
    out = aggregate_corridor_eta(
        depart, route_ids=SOUTHERN_ROUTE_IDS, predict_route_eta=_route_eta_stub
    )
    # Two southern segments at 55 min each + the 40 min modeled northern leg.
    assert out["eta"] == pytest.approx(55.0 + 55.0 + 40.0)
    # Interval dict -> summed [low, high] list, plus the northern band (35, 52).
    assert out["interval"] == [48.0 + 48.0 + 35.0, 64.0 + 64.0 + 52.0]
    # basis dict -> flat string the connections leg stores verbatim.
    assert out["basis"] == "modeled_history"


def test_adapter_unknown_when_no_southern_segment_resolves():
    depart = datetime(2026, 6, 27, 15, 0, 0)
    out = aggregate_corridor_eta(
        depart,
        route_ids=[],
        predict_route_eta=lambda *_a, **_k: {"eta_minutes": None},
    )
    # No southern data -> unknown drive, never "just the northern 40 minutes".
    assert out == {"eta": None, "interval": None, "basis": None}


def test_adapter_downgrades_basis_when_a_segment_uses_the_fallback():
    def mixed(route_id, depart_dt):
        if route_id == SOUTHERN_ROUTE_IDS[0]:
            return {
                "eta_minutes": 50.0,
                "interval": {"low_minutes": 45.0, "high_minutes": 58.0},
                "basis": {"method": "modeled_history"},
                "label": "MODELED",
            }
        return {
            "eta_minutes": 60.0,
            "interval": {"low_minutes": 52.0, "high_minutes": 70.0},
            "basis": {"method": "fallback_latest_measured"},
            "label": "MODELED",
        }

    out = aggregate_corridor_eta(
        datetime(2026, 6, 27, 15, 0, 0),
        route_ids=SOUTHERN_ROUTE_IDS,
        predict_route_eta=mixed,
    )
    assert out["basis"] == "modeled_fallback_latest_measured"
    assert out["eta"] is not None


# --------------------------------------------------------------------------- #
# 2. The visiting branch assembles a labeled connection plan into panel props
# --------------------------------------------------------------------------- #

def test_visiting_branch_attaches_a_labeled_connection_plan():
    agent = load_seed_agent("surface-planner-v1")
    focus = {"branch": "visiting", "connection": _connection_intent()}
    intent = draft_ui_intent(
        agent,
        "Plan a trip to the San Juans",
        focus=focus,
        connection_clients=_clients(),
    )

    assert intent["branch"] == "visiting"
    panel_ids = [p["id"] for p in intent["panels"]]
    assert "compare_places" in panel_ids
    assert "connections_plan" in panel_ids

    conn_panel = next(p for p in intent["panels"] if p["id"] == "connections_plan")
    plan = conn_panel["props"]["plan"]
    assert plan is not None

    # Composite is the weakest leg on the path: the modeled drive leg.
    assert plan["composite_label"] == cx.MODELED

    legs = {leg["leg"]: leg for leg in plan["legs"]}
    # The reconciled corridor field flowed through to a labeled, summed drive leg.
    assert legs["drive"]["label"] == cx.MODELED
    assert legs["drive"]["eta_minutes"] == pytest.approx(150.0)
    assert legs["drive"]["basis"] == "modeled_history"
    # Northern leg is always modeled, never measured.
    northern = next(
        seg for seg in legs["drive"]["segments"] if seg["name"] == "arlington_anacortes"
    )
    assert northern["label"] == cx.MODELED
    # Ferry leg: schedule published + space/vessel measured -> weakest published.
    assert legs["ferry"]["label"] == cx.PUBLISHED

    # Per-leg + composite labels and a freshness stamp are all present.
    assert plan["freshness"] is not None
    assert plan["feasibility"]["verdict"] == "likely"


def test_visiting_branch_intent_validates_on_public_route():
    agent = load_seed_agent("surface-planner-v1")
    focus = {"branch": "visiting", "connection": _connection_intent()}
    intent = draft_ui_intent(
        agent, "Plan a trip", focus=focus, connection_clients=_clients()
    )
    # All branch panels are registered + allow-listed, all skills are public T0/T1.
    validate_ui_intent(agent, intent, public_route=True)


def test_here_now_branch_also_carries_a_connection_plan():
    agent = load_seed_agent("surface-planner-v1")
    focus = {"branch": "here-now", "connection": _connection_intent()}
    intent = draft_ui_intent(
        agent, "What can I reach today", focus=focus, connection_clients=_clients()
    )
    panel_ids = [p["id"] for p in intent["panels"]]
    assert "local_area" in panel_ids
    assert "connections_plan" in panel_ids
    validate_ui_intent(agent, intent, public_route=True)


# --------------------------------------------------------------------------- #
# 3. Kayak + curious branches surface their typed panel props
# --------------------------------------------------------------------------- #

def test_kayak_branch_emits_modeled_window_props_and_no_connection_call():
    agent = load_seed_agent("surface-planner-v1")
    # No connection_clients injected: kayak must not touch the connections seam.
    intent = draft_ui_intent(agent, "I want to paddle", focus={"branch": "kayak"})
    kayak = next(p for p in intent["panels"] if p["id"] == "kayak_plan")
    # Empty windows render as unknown, never as safe water; safety framing is set.
    assert kayak["props"]["windows"] == []
    assert kayak["props"]["safety"]
    validate_ui_intent(agent, intent, public_route=True)


def test_kayak_branch_threads_server_side_tide_props():
    agent = load_seed_agent("surface-planner-v1")
    windows = [
        {"start": "2026-06-27T10:00:00-07:00", "end": "2026-06-27T11:00:00-07:00", "rating": "go"}
    ]
    focus = {"branch": "kayak", "kayak": {"windows": windows, "basis": {"station": "Rosario"}}}
    intent = draft_ui_intent(agent, "paddle", focus=focus)
    kayak = next(p for p in intent["panels"] if p["id"] == "kayak_plan")
    assert kayak["props"]["windows"] == windows
    assert kayak["props"]["basis"]["station"] == "Rosario"


def test_curious_branch_emits_sidequests_with_tier_and_confirm_chip():
    agent = load_seed_agent("surface-planner-v1")
    intent = draft_ui_intent(agent, "show me something interesting", focus={"branch": "curious"})
    sidequests = next(p for p in intent["panels"] if p["id"] == "sidequests")
    props = sidequests["props"]
    assert props["viewerTier"] == "anonymous-public"
    assert props["confirm"]["label"]
    assert len(props["items"]) >= 1
    validate_ui_intent(agent, intent, public_route=True)


# --------------------------------------------------------------------------- #
# 4. The branch seam is strictly additive (no branch -> today's keyword planner)
# --------------------------------------------------------------------------- #

def test_absent_branch_falls_back_to_keyword_planner():
    agent = load_seed_agent("surface-planner-v1")
    intent = draft_ui_intent(agent, "Explain the gates", focus=None)
    assert "branch" not in intent
    panel_ids = [p["id"] for p in intent["panels"]]
    assert "gates_summary" in panel_ids
