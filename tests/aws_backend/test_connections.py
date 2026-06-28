"""Tests for the connections planner (src/aws_backend/casting/trips/connections.py).

PURE ASSEMBLY, no live calls. Every source callable is a stub injected through
:class:`ConnectionClients`, so the suite runs offline in CI. The headline case
answers the dispatch validation question:

    "Depart SeaTac 3 pm Friday, catch the 6:30 Anacortes sailing?"

and asserts a labeled feasibility + interval, a composite label of ``modeled``
when the plan uses a future corridor ETA, and that the northern Arlington ->
Anacortes leg is never labeled measured.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.aws_backend.casting.trips import connections as cx
from src.aws_backend.casting.trips.connections import (
    ConnectionClients,
    plan_connection,
    weakest_label,
)

# --------------------------------------------------------------------------- #
# Scenario fixtures (the SeaTac -> 6:30 Anacortes sailing question)
# --------------------------------------------------------------------------- #

# 3 pm Friday Pacific.
DEPART_ISO = "2026-06-27T15:00:00-07:00"
# The 6:30 pm Anacortes -> Friday Harbor sailing.
SAILING_ISO = "2026-06-27T18:30:00-07:00"
ARRIVE_ISO = "2026-06-27T19:30:00-07:00"

ROUTE_ID = 9
ANACORTES_TERMINAL = 1
FRIDAY_HARBOR_TERMINAL = 10
VESSEL_ID = 38

# Observation instant used as "now" so the test is deterministic.
NOW = datetime(2026, 6, 27, 21, 55, 0, tzinfo=timezone.utc)


def _schedule_stub(route_id, date):
    assert route_id == ROUTE_ID
    return {
        "schedule_id": 4321,
        "schedule_name": "Anacortes / San Juan Islands",
        "terminal_combos": [
            {
                "departing_terminal_id": ANACORTES_TERMINAL,
                "departing_terminal_name": "Anacortes",
                "arriving_terminal_id": FRIDAY_HARBOR_TERMINAL,
                "arriving_terminal_name": "Friday Harbor",
                "annotations": [
                    "Reservations required for vehicles on this sailing.",
                    "Subject to tidal cancellation.",
                ],
                "times": [
                    {
                        "departing_time": "2026-06-27T15:15:00-07:00",
                        "arriving_time": "2026-06-27T16:15:00-07:00",
                        "vessel_id": 2,
                        "vessel_name": "Chelan",
                        "annotation_indexes": [0],
                    },
                    {
                        "departing_time": SAILING_ISO,
                        "arriving_time": ARRIVE_ISO,
                        "vessel_id": VESSEL_ID,
                        "vessel_name": "Yakima",
                        "annotation_indexes": [0, 1],
                    },
                ],
            }
        ],
    }


def _sailing_space_stub(terminal_id=None):
    assert terminal_id == ANACORTES_TERMINAL
    return [
        {
            "terminal_id": ANACORTES_TERMINAL,
            "terminal_name": "Anacortes",
            "departing_spaces": [
                {
                    "departure": SAILING_ISO,
                    "vessel_name": "Yakima",
                    "space_for_arrival_terminals": [
                        {
                            "terminal_id": ANACORTES_TERMINAL,
                            "terminal_name": "Anacortes -> Friday Harbor",
                            "display_drive_up_space": True,
                            "drive_up_space_count": 55,
                            "display_reservable_space": True,
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


def _corridor_stub(depart_dt):
    """Future-departure corridor ETA: ~2 h 30 m typical, +/- interval.

    eta in minutes, interval [low_min, high_min], basis modeled_history.
    Depart 15:00 + 150 min = 17:30; worst case 175 min = 17:55, which still
    clears the 18:30 sailing with the 30 min buffer.
    """
    assert isinstance(depart_dt, datetime)
    return {"eta": 150.0, "interval": [135.0, 175.0], "basis": "modeled_history"}


def _ferry_intent():
    return {
        "mode": "ferry",
        "branch": "visiting",
        "question": "Depart SeaTac 3 pm Friday, catch the 6:30 Anacortes sailing?",
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


def _clients(**overrides):
    base = dict(
        schedule=_schedule_stub,
        sailing_space=_sailing_space_stub,
        vessel_locations=_vessel_locations_stub,
        predict_eta=_corridor_stub,
        skylink_board=lambda *a, **k: [],
        seaplane_schedule=lambda *a, **k: [],
    )
    base.update(overrides)
    return ConnectionClients(**base)


# --------------------------------------------------------------------------- #
# weakest_label helper
# --------------------------------------------------------------------------- #

def test_weakest_label_orders_measured_published_modeled_heuristic():
    assert weakest_label([cx.MEASURED, cx.PUBLISHED]) == cx.PUBLISHED
    assert weakest_label([cx.MEASURED, cx.MODELED]) == cx.MODELED
    assert weakest_label([cx.PUBLISHED, cx.MODELED, cx.HEURISTIC]) == cx.HEURISTIC
    assert weakest_label([cx.MEASURED]) == cx.MEASURED
    # Unknown / None labels are ignored, not treated as weakest.
    assert weakest_label([cx.MEASURED, None]) == cx.MEASURED
    assert weakest_label([None, None]) is None


# --------------------------------------------------------------------------- #
# The headline validation case
# --------------------------------------------------------------------------- #

def test_make_the_630_anacortes_sailing_is_feasible():
    plan = plan_connection(_ferry_intent(), clients=_clients(), now=NOW)

    feas = plan["feasibility"]
    assert feas["verdict"] == "likely"
    assert feas["feasible"] is True
    assert feas["sailing_departure"] == SAILING_ISO
    # Arrival interval is surfaced (modeled drive prediction interval).
    assert feas["arrival_interval"] == [
        "2026-06-27T17:15:00-07:00",
        "2026-06-27T17:55:00-07:00",
    ]
    # Worst-case still clears the 30 min terminal buffer (18:30 - 17:55 = 35).
    assert feas["worst_case_margin_minutes"] == pytest.approx(35.0)
    assert feas["buffer_minutes"] == 30


def test_composite_label_is_modeled_when_using_future_corridor_eta():
    plan = plan_connection(_ferry_intent(), clients=_clients(), now=NOW)
    # Drive leg is modeled and is the weakest leg on the path -> composite modeled.
    assert plan["composite_label"] == cx.MODELED


def test_per_leg_labels_are_attached():
    plan = plan_connection(_ferry_intent(), clients=_clients(), now=NOW)
    legs = {leg["leg"]: leg for leg in plan["legs"]}

    assert legs["drive"]["label"] == cx.MODELED
    # Ferry leg: schedule published + space/vessel measured -> weakest published.
    assert legs["ferry"]["label"] == cx.PUBLISHED
    assert legs["ferry"]["label_detail"]["schedule"] == cx.PUBLISHED
    assert legs["ferry"]["label_detail"]["space"] == cx.MEASURED
    assert legs["ferry"]["label_detail"]["vessel"] == cx.MEASURED


def test_northern_leg_is_always_modeled_never_measured():
    plan = plan_connection(_ferry_intent(), clients=_clients(), now=NOW)
    drive = next(leg for leg in plan["legs"] if leg["leg"] == "drive")
    northern = next(
        seg for seg in drive["segments"] if seg["name"] == "arlington_anacortes"
    )
    assert northern["label"] == cx.MODELED
    # No drive segment is ever labeled measured.
    assert all(seg["label"] == cx.MODELED for seg in drive["segments"])
    # corridor basis is surfaced as detail but never upgrades the leg label.
    assert drive["basis"] == "modeled_history"
    assert drive["label"] == cx.MODELED


def test_measured_space_count_and_freshness_are_surfaced():
    plan = plan_connection(_ferry_intent(), clients=_clients(), now=NOW)
    ferry = next(leg for leg in plan["legs"] if leg["leg"] == "ferry")
    assert ferry["space"]["drive_up_space_count"] == 55
    assert ferry["space"]["reservable_space_count"] == 32
    assert ferry["space"]["label"] == cx.MEASURED
    # Freshness = youngest measured source used. The vessel timestamp (21:54:30Z)
    # is older than the space observation instant (NOW, 21:55:00Z), so NOW wins.
    assert plan["freshness"] == NOW.isoformat()


def test_sailing_annotations_resolved_from_indexes():
    plan = plan_connection(_ferry_intent(), clients=_clients(), now=NOW)
    ferry = next(leg for leg in plan["legs"] if leg["leg"] == "ferry")
    assert ferry["sailing"]["vessel_name"] == "Yakima"
    assert ferry["sailing"]["departing_time"] == SAILING_ISO
    assert ferry["sailing"]["annotations"] == [
        "Reservations required for vehicles on this sailing.",
        "Subject to tidal cancellation.",
    ]


# --------------------------------------------------------------------------- #
# Unlikely + unknown paths (honesty: empty is unknown, never zero)
# --------------------------------------------------------------------------- #

def test_slow_corridor_makes_the_sailing_unlikely():
    slow = _clients(
        predict_eta=lambda d: {
            "eta": 240.0,
            "interval": [220.0, 270.0],
            "basis": "modeled_history",
        }
    )
    plan = plan_connection(_ferry_intent(), clients=slow, now=NOW)
    feas = plan["feasibility"]
    # 15:00 + 240 min = 19:00, after the 18:30 sailing.
    assert feas["verdict"] == "unlikely"
    assert feas["feasible"] is False
    # Still modeled overall (it used a future corridor ETA).
    assert plan["composite_label"] == cx.MODELED


def test_empty_adapters_yield_unknown_not_zero():
    empty = _clients(
        schedule=lambda *a, **k: {},
        sailing_space=lambda *a, **k: [],
        vessel_locations=lambda *a, **k: [],
        predict_eta=lambda d: {},
    )
    plan = plan_connection(_ferry_intent(), clients=empty, now=NOW)
    feas = plan["feasibility"]
    assert feas["verdict"] == "unknown"
    assert feas["feasible"] is None
    ferry = next(leg for leg in plan["legs"] if leg["leg"] == "ferry")
    # No fabricated counts; the space is simply unknown.
    assert ferry["space"] is None
    assert ferry["label"] is None
    # No measured source used -> no freshness stamp invented.
    assert plan["freshness"] is None


def test_suppressed_space_count_is_none_not_zero():
    suppressed = _clients(
        sailing_space=lambda terminal_id=None: [
            {
                "terminal_id": ANACORTES_TERMINAL,
                "departing_spaces": [
                    {
                        "departure": SAILING_ISO,
                        "space_for_arrival_terminals": [
                            {
                                "terminal_id": ANACORTES_TERMINAL,
                                "drive_up_space_count": None,
                                "reservable_space_count": None,
                                "arrival_terminal_ids": [FRIDAY_HARBOR_TERMINAL],
                            }
                        ],
                    }
                ],
            }
        ]
    )
    plan = plan_connection(_ferry_intent(), clients=suppressed, now=NOW)
    ferry = next(leg for leg in plan["legs"] if leg["leg"] == "ferry")
    assert ferry["space"]["drive_up_space_count"] is None
    assert ferry["space"]["reservable_space_count"] is None
    # The leg still counts as measured (the reading exists, the count is hidden).
    assert ferry["space"]["label"] == cx.MEASURED


# --------------------------------------------------------------------------- #
# Flight + seaplane legs (board + static table only, NO live OpenSky)
# --------------------------------------------------------------------------- #

def test_flight_board_leg_is_published_and_uses_no_opensky():
    board_rows = [
        {"flight_number": "AS123", "scheduled": "2026-06-27T20:00:00-07:00"}
    ]
    clients = _clients(skylink_board=lambda iata, direction="departures": board_rows)
    intent = {
        "mode": "flight",
        "flight": {"airport_iata": "SEA", "direction": "departures"},
    }
    plan = plan_connection(intent, clients=clients, now=NOW)
    flight = next(leg for leg in plan["legs"] if leg["leg"] == "flight")
    assert flight["label"] == cx.PUBLISHED
    assert flight["flights"] == board_rows
    assert plan["composite_label"] == cx.PUBLISHED
    # No measured live-position field is present (OpenSky is off this launch).
    assert "opensky" not in str(flight).lower()


def test_seaplane_leg_is_published_static():
    rows = [
        {
            "route": "Lake Union -> Friday Harbor",
            "departure_time": "17:15",
            "source_date": "2026-06-01",
        }
    ]
    clients = _clients(seaplane_schedule=lambda route=None, day=None: rows)
    intent = {"mode": "seaplane", "seaplane": {"route": "Lake Union -> Friday Harbor"}}
    plan = plan_connection(intent, clients=clients, now=NOW)
    seaplane = next(leg for leg in plan["legs"] if leg["leg"] == "seaplane")
    assert seaplane["label"] == cx.PUBLISHED
    assert seaplane["schedule"] == rows
    assert any("not a live status" in n for n in plan["honesty_notes"])


# --------------------------------------------------------------------------- #
# Default wiring stays importable even when sibling producers are absent
# --------------------------------------------------------------------------- #

def test_default_clients_degrade_gracefully_when_siblings_absent():
    # corridor / flights / seaplane may not have landed yet; default() must not
    # raise, and an empty intent must produce a coherent unknown plan.
    clients = ConnectionClients.default()
    plan = plan_connection({"mode": "ferry", "ferry": {}}, clients=clients, now=NOW)
    assert plan["feasibility"]["verdict"] == "unknown"
    assert plan["mode"] == "ferry"
