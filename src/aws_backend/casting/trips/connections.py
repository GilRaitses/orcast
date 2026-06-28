"""Connection feasibility planner — "make your sailing / flight".

``plan_connection(intent)`` is PURE ASSEMBLY. It owns no I/O of its own; it
reads from a small bundle of source callables (:class:`ConnectionClients`) and
stitches their output into one structured plan that the phase-B planner branch
attaches to the ``connections_plan`` panel props.

Inputs assembled (honesty map, ``DISCOVERY_MAP.md`` section 7):

- WSF schedule (``wsf.schedule``)            -> sailing times          | published
- WSF sailing space (``wsf.sailing_space``)  -> drive-up / reservable  | measured
- WSF vessel locations (``wsf.vessel_locations``) -> live ETA + basis  | measured
- Corridor model (``modeling/traffic/corridor.predict_eta``) -> drive  | modeled
- Flight board (``sources/flights.skylink_board``) -> SeaTac board     | published
- Seaplane table (``sources/seaplane.seaplane_schedule``) -> times     | published

Honesty rules enforced here:

- Empty adapter output is "unknown", never "zero". A missing count or sailing
  yields ``None`` / an unknown verdict, not a false negative.
- The drive leg is ALWAYS labeled ``modeled``. Even when the corridor model's
  basis is ``measured_current`` for the southern I-5 segments, the northern
  Arlington -> Anacortes leg has no WSDOT TravelTimes coverage and is modeled,
  so the leg as a whole can never be ``measured``.
- Per-leg label = the weakest signal actually used on that leg.
- Composite label = the weakest leg label on the path actually used, in the
  strength order measured > published > modeled > heuristic.
- Freshness stamp = the youngest (most recent) measured-source timestamp used.

This module does not call live OpenSky for this launch (board + seaplane only).
"""

from __future__ import annotations

import datetime as _dt
import importlib
import logging
from dataclasses import dataclass
from datetime import date as date_type
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Sequence

from src.aws_backend.casting.trips.fanout import fetch_legs_concurrently

logger = logging.getLogger(__name__)

# Sentinel distinguishing "not prefetched, fetch it here" from "prefetched but
# empty/failed". A prefetched ``None`` is coerced to the leg's empty sentinel,
# exactly like the sequential ``try/except`` path did.
_UNSET: Any = object()

# --------------------------------------------------------------------------- #
# Honesty labels + strength ordering
# --------------------------------------------------------------------------- #

MEASURED = "measured"
PUBLISHED = "published"
MODELED = "modeled"
HEURISTIC = "heuristic"

# Strength order: measured > published > modeled > heuristic. The composite
# label is the WEAKEST (lowest strength) label on the path actually used.
_LABEL_STRENGTH: Dict[str, int] = {
    MEASURED: 3,
    PUBLISHED: 2,
    MODELED: 1,
    HEURISTIC: 0,
}

LABEL_LEGEND: Dict[str, str] = {
    MEASURED: "Read live from a sensor or feed within seconds of now.",
    PUBLISHED: "A scheduled or curated value, accurate but not a live reading.",
    MODELED: "Estimated by a model, shown with a prediction interval.",
    HEURISTIC: "A best-effort hint, never a precise number.",
}

# Default minutes a vehicle should arrive at the terminal before departure.
_DEFAULT_TERMINAL_BUFFER_MIN = 30


def weakest_label(labels: Sequence[Optional[str]]) -> Optional[str]:
    """Return the weakest (lowest-strength) honesty label among ``labels``.

    Unknown / ``None`` labels are ignored. Returns ``None`` when nothing on the
    path carried a label (i.e. the path is entirely unknown).
    """
    present = [l for l in labels if l in _LABEL_STRENGTH]
    if not present:
        return None
    return min(present, key=lambda l: _LABEL_STRENGTH[l])


# --------------------------------------------------------------------------- #
# Source client bundle (the only seam to the outside world)
# --------------------------------------------------------------------------- #

def _noop_list(*_a: Any, **_k: Any) -> List[Any]:
    return []


def _noop_dict(*_a: Any, **_k: Any) -> Dict[str, Any]:
    return {}


def _resolve_callable(module_path: str, attr: str) -> Optional[Callable[..., Any]]:
    """Lazily resolve ``module_path.attr``; ``None`` when it cannot be imported.

    The corridor model and the flight/seaplane adapters are built by parallel
    phase-A producers and may not exist yet. Resolving lazily keeps this module
    importable and lets the planner degrade gracefully (treat absence as
    "unknown") rather than failing at import time.
    """
    try:
        module = importlib.import_module(module_path)
    except Exception as exc:  # pragma: no cover - exercised when sibling absent
        logger.debug("connections: %s not importable (%s)", module_path, exc)
        return None
    fn = getattr(module, attr, None)
    return fn if callable(fn) else None


@dataclass
class ConnectionClients:
    """Bundle of source callables the planner assembles over.

    Every field is a callable mirroring a finalized adapter signature. Tests
    inject stubs; production wires the real adapters via :meth:`default`. Any
    field that cannot be resolved (a sibling producer not landed yet) degrades
    to an empty / ``None`` result so the planner labels the leg unknown.
    """

    schedule: Callable[[int, date_type], Dict[str, Any]]
    sailing_space: Callable[..., List[Dict[str, Any]]]
    vessel_locations: Callable[..., List[Dict[str, Any]]]
    predict_eta: Callable[[datetime], Dict[str, Any]]
    skylink_board: Callable[..., List[Dict[str, Any]]]
    seaplane_schedule: Callable[..., List[Dict[str, Any]]]

    @classmethod
    def default(cls) -> "ConnectionClients":
        """Wire the real adapters, degrading any unresolved sibling to empty."""
        wsf_schedule = _resolve_callable("src.aws_backend.sources.wsf", "schedule")
        wsf_space = _resolve_callable("src.aws_backend.sources.wsf", "sailing_space")
        wsf_vessels = _resolve_callable(
            "src.aws_backend.sources.wsf", "vessel_locations"
        )
        corridor = _resolve_callable("modeling.traffic.corridor", "predict_eta")
        board = _resolve_callable("src.aws_backend.sources.flights", "skylink_board")
        seaplane = _resolve_callable(
            "src.aws_backend.sources.seaplane", "seaplane_schedule"
        )
        return cls(
            schedule=wsf_schedule or _noop_dict,
            sailing_space=wsf_space or _noop_list,
            vessel_locations=wsf_vessels or _noop_list,
            predict_eta=corridor or (lambda _dt: {}),
            skylink_board=board or _noop_list,
            seaplane_schedule=seaplane or _noop_list,
        )


# --------------------------------------------------------------------------- #
# Small parsing helpers
# --------------------------------------------------------------------------- #

def _parse_dt(value: Any) -> Optional[datetime]:
    """Parse an ISO-8601 string or datetime into an aware datetime (or None)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _parse_date(value: Any, fallback: Optional[datetime]) -> Optional[date_type]:
    if isinstance(value, date_type) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str) and value.strip():
        try:
            return _dt.date.fromisoformat(value.strip()[:10])
        except ValueError:
            pass
    return fallback.date() if fallback else None


def _minutes(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _clock(dt: Optional[datetime]) -> Optional[str]:
    return dt.strftime("%H:%M") if dt else None


def _youngest(stamps: Sequence[Any]) -> Optional[str]:
    """Most recent timestamp among ``stamps`` (ISO strings / datetimes)."""
    parsed = [d for d in (_parse_dt(s) for s in stamps) if d is not None]
    if not parsed:
        return None
    return max(parsed).isoformat()


# --------------------------------------------------------------------------- #
# Drive leg (always modeled; northern leg never measured)
# --------------------------------------------------------------------------- #

def _build_drive_leg(
    clients: ConnectionClients,
    depart_dt: Optional[datetime],
    origin_label: str,
    destination_label: str,
    *,
    prediction: Any = _UNSET,
) -> Dict[str, Any]:
    """Drive leg from the corridor model. ALWAYS labeled ``modeled``.

    The corridor model returns ``{eta, interval, basis}`` where ``eta`` is the
    predicted travel time in minutes, ``interval`` is ``[low_min, high_min]``,
    and ``basis`` is one of ``measured_current`` / ``modeled_history`` /
    ``modeled_synthetic_bootstrap``. Whatever the basis, the leg total includes
    the unmeasured Arlington -> Anacortes segment, so the leg label is
    ``modeled`` and the northern segment is surfaced as a modeled segment.
    """
    leg: Dict[str, Any] = {
        "leg": "drive",
        "from": origin_label,
        "to": destination_label,
        "label": MODELED,
        "eta_minutes": None,
        "interval_minutes": None,
        "arrival": None,
        "arrival_interval": None,
        "basis": None,
        "segments": [
            {
                "name": "southern_i5",
                "label": MODELED,
                "note": "Southern I-5 segments, predicted for the departure time.",
            },
            {
                "name": "arlington_anacortes",
                "label": MODELED,
                "note": (
                    "WSDOT travel-time coverage on I-5 ends near Arlington "
                    "around milepost 208, so the final leg to Anacortes is "
                    "modeled, never measured."
                ),
            },
        ],
        "source": "modeling.traffic.corridor.predict_eta",
    }
    if depart_dt is None:
        leg["note"] = "No departure time supplied, drive estimate unknown."
        return leg

    if prediction is _UNSET:
        # Sequential path: fetch here (direct callers / no fan-out).
        try:
            prediction = clients.predict_eta(depart_dt) or {}
        except Exception as exc:  # defensive: a sibling producer may raise
            logger.warning("connections: corridor predict_eta failed: %s", exc)
            prediction = {}
    else:
        # Fan-out path: a prefetched ``None`` means the leg failed -> empty.
        prediction = prediction or {}

    eta_min = _minutes(prediction.get("eta"))
    interval = prediction.get("interval")
    basis = prediction.get("basis")
    leg["basis"] = basis if isinstance(basis, str) else None

    if eta_min is None:
        leg["note"] = "Corridor model returned no estimate, drive leg unknown."
        return leg

    leg["eta_minutes"] = eta_min
    leg["arrival"] = (depart_dt + timedelta(minutes=eta_min)).isoformat()

    low = high = None
    if isinstance(interval, (list, tuple)) and len(interval) == 2:
        low = _minutes(interval[0])
        high = _minutes(interval[1])
    if low is not None and high is not None:
        leg["interval_minutes"] = [low, high]
        leg["arrival_interval"] = [
            (depart_dt + timedelta(minutes=low)).isoformat(),
            (depart_dt + timedelta(minutes=high)).isoformat(),
        ]
    return leg


# --------------------------------------------------------------------------- #
# Ferry leg (schedule published, space + vessel measured)
# --------------------------------------------------------------------------- #

def _match_sailing_time(
    schedule: Dict[str, Any],
    departing_terminal_id: Optional[int],
    arriving_terminal_id: Optional[int],
    depart_clock: Optional[str],
    departing_time_iso: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Find the requested sailing inside a parsed ``wsf.schedule`` response."""
    combos = schedule.get("terminal_combos") or []
    target = _parse_dt(departing_time_iso)
    for combo in combos:
        if (
            departing_terminal_id is not None
            and combo.get("departing_terminal_id") != departing_terminal_id
        ):
            continue
        if (
            arriving_terminal_id is not None
            and combo.get("arriving_terminal_id") != arriving_terminal_id
        ):
            continue
        annotations = combo.get("annotations") or []
        for time_entry in combo.get("times") or []:
            dep = _parse_dt(time_entry.get("departing_time"))
            if dep is None:
                continue
            if target is not None and dep == target:
                return _sailing_record(combo, time_entry, dep, annotations)
            if depart_clock is not None and _clock(dep) == depart_clock:
                return _sailing_record(combo, time_entry, dep, annotations)
        # No clock/time filter -> first sailing on the combo is the candidate.
        if depart_clock is None and target is None:
            for time_entry in combo.get("times") or []:
                dep = _parse_dt(time_entry.get("departing_time"))
                if dep is not None:
                    return _sailing_record(combo, time_entry, dep, annotations)
    return None


def _sailing_record(
    combo: Dict[str, Any],
    time_entry: Dict[str, Any],
    dep: datetime,
    annotations: List[str],
) -> Dict[str, Any]:
    idxs = time_entry.get("annotation_indexes") or []
    resolved = [
        annotations[i]
        for i in idxs
        if isinstance(i, int) and 0 <= i < len(annotations)
    ]
    return {
        "departing_terminal_id": combo.get("departing_terminal_id"),
        "departing_terminal_name": combo.get("departing_terminal_name"),
        "arriving_terminal_id": combo.get("arriving_terminal_id"),
        "arriving_terminal_name": combo.get("arriving_terminal_name"),
        "departing_time": time_entry.get("departing_time"),
        "arriving_time": time_entry.get("arriving_time"),
        "departing_dt": dep,
        "vessel_id": time_entry.get("vessel_id"),
        "vessel_name": time_entry.get("vessel_name"),
        "annotations": resolved,
        "label": PUBLISHED,
    }


def _match_space(
    spaces: List[Dict[str, Any]],
    departing_terminal_id: Optional[int],
    arriving_terminal_id: Optional[int],
    sailing_dt: Optional[datetime],
) -> Optional[Dict[str, Any]]:
    """Find the drive-up / reservable counts for the matched sailing (measured).

    Returns ``None`` when no matching sailing space row exists. A returned row
    may still carry ``None`` counts when the WSF ``display_*`` flag suppressed
    them; that is "unknown for this sailing", never a misleading zero.
    """
    for terminal in spaces:
        if (
            departing_terminal_id is not None
            and terminal.get("terminal_id") != departing_terminal_id
        ):
            continue
        best: Optional[Dict[str, Any]] = None
        best_gap: Optional[float] = None
        for departing in terminal.get("departing_spaces") or []:
            dep = _parse_dt(departing.get("departure"))
            for arrival in departing.get("space_for_arrival_terminals") or []:
                if arriving_terminal_id is not None and not _arrival_matches(
                    arrival, arriving_terminal_id
                ):
                    continue
                gap = (
                    abs((dep - sailing_dt).total_seconds())
                    if dep is not None and sailing_dt is not None
                    else float("inf")
                )
                if best_gap is None or gap < best_gap:
                    best_gap = gap
                    best = {
                        "departure": departing.get("departure"),
                        "vessel_name": departing.get("vessel_name"),
                        "drive_up_space_count": arrival.get("drive_up_space_count"),
                        "reservable_space_count": arrival.get(
                            "reservable_space_count"
                        ),
                        "max_space_count": arrival.get("max_space_count"),
                        "label": MEASURED,
                    }
        # Accept only a reasonably close departure match (within ~20 min) when a
        # sailing time is known; otherwise accept the only candidate found.
        if best is not None and (
            sailing_dt is None or best_gap is None or best_gap <= 20 * 60
        ):
            return best
    return None


def _arrival_matches(arrival: Dict[str, Any], arriving_terminal_id: int) -> bool:
    if arrival.get("terminal_id") == arriving_terminal_id:
        return True
    ids = arrival.get("arrival_terminal_ids") or []
    return arriving_terminal_id in ids


def _match_vessel(
    vessels: List[Dict[str, Any]],
    vessel_id: Optional[int],
    arriving_terminal_id: Optional[int],
) -> Optional[Dict[str, Any]]:
    """Live vessel ETA for the sailing's vessel (measured), if it is underway."""
    for vessel in vessels:
        if vessel_id is not None and vessel.get("vessel_id") != vessel_id:
            continue
        if (
            arriving_terminal_id is not None
            and vessel.get("arriving_terminal_id") not in (None, arriving_terminal_id)
        ):
            continue
        if vessel.get("eta") is None:
            continue
        return {
            "vessel_id": vessel.get("vessel_id"),
            "vessel_name": vessel.get("vessel_name"),
            "eta": vessel.get("eta"),
            "eta_basis": vessel.get("eta_basis"),
            "timestamp": vessel.get("timestamp"),
            "label": MEASURED,
        }
    return None


def _build_ferry_leg(
    clients: ConnectionClients,
    ferry: Dict[str, Any],
    depart_dt: Optional[datetime],
    *,
    schedule: Any = _UNSET,
    spaces: Any = _UNSET,
    vessels: Any = _UNSET,
) -> Dict[str, Any]:
    route_id = ferry.get("route_id")
    dep_term = ferry.get("departing_terminal_id")
    arr_term = ferry.get("arriving_terminal_id")
    trip_date = _parse_date(ferry.get("trip_date"), depart_dt)

    leg: Dict[str, Any] = {
        "leg": "ferry",
        "from": ferry.get("departing_terminal_name") or dep_term,
        "to": ferry.get("arriving_terminal_name") or arr_term,
        "label": None,
        "sailing": None,
        "space": None,
        "vessel": None,
        "label_detail": {},
        "source": "wsf.schedule + wsf.sailing_space + wsf.vessel_locations",
    }

    sailing = None
    if route_id is not None and trip_date is not None:
        if schedule is _UNSET:
            try:
                schedule_data = clients.schedule(int(route_id), trip_date) or {}
            except Exception as exc:
                logger.warning("connections: wsf.schedule failed: %s", exc)
                schedule_data = {}
        else:
            schedule_data = schedule or {}
        sailing = _match_sailing_time(
            schedule_data,
            dep_term,
            arr_term,
            ferry.get("depart_clock"),
            ferry.get("departing_time"),
        )

    sailing_dt: Optional[datetime] = None
    if sailing is not None:
        sailing_dt = sailing.pop("departing_dt", None)
        leg["sailing"] = sailing
        leg["label_detail"]["schedule"] = PUBLISHED
    else:
        leg["sailing_note"] = (
            "No matching sailing found in the schedule, sailing unknown."
        )

    if spaces is _UNSET:
        try:
            spaces_data = clients.sailing_space(dep_term) or []
        except Exception as exc:
            logger.warning("connections: wsf.sailing_space failed: %s", exc)
            spaces_data = []
    else:
        spaces_data = spaces or []
    space = _match_space(spaces_data, dep_term, arr_term, sailing_dt)
    if space is not None:
        leg["space"] = space
        leg["label_detail"]["space"] = MEASURED

    if vessels is _UNSET:
        try:
            vessels_data = clients.vessel_locations() or []
        except Exception as exc:
            logger.warning("connections: wsf.vessel_locations failed: %s", exc)
            vessels_data = []
    else:
        vessels_data = vessels or []
    vessel = _match_vessel(
        vessels_data, sailing.get("vessel_id") if sailing else None, arr_term
    )
    if vessel is not None:
        leg["vessel"] = vessel
        leg["label_detail"]["vessel"] = MEASURED

    leg["label"] = weakest_label(list(leg["label_detail"].values()))
    leg["sailing_dt"] = sailing_dt
    return leg


# --------------------------------------------------------------------------- #
# Flight + seaplane legs (board + static table only; NO live OpenSky)
# --------------------------------------------------------------------------- #

def _build_flight_leg(
    clients: ConnectionClients, flight: Dict[str, Any]
) -> Dict[str, Any]:
    """SeaTac board leg (published). No live OpenSky position for this launch."""
    iata = flight.get("airport_iata") or "SEA"
    direction = flight.get("direction", "departures")
    try:
        board = clients.skylink_board(iata, direction) or []
    except Exception as exc:
        logger.warning("connections: skylink_board failed: %s", exc)
        board = []
    number = flight.get("flight_number")
    if number:
        board = [
            f
            for f in board
            if str(f.get("flight_number") or f.get("flight") or "").upper()
            == str(number).upper()
        ]
    leg: Dict[str, Any] = {
        "leg": "flight",
        "airport_iata": iata,
        "direction": direction,
        "label": PUBLISHED if board else None,
        "flights": board[: flight.get("limit", 10)],
        "source": "sources.flights.skylink_board",
        "note": "Scheduled board. Live aircraft positions are not used here.",
    }
    if not board:
        leg["flight_note"] = "No board entries returned, flight board unknown."
    return leg


def _build_seaplane_leg(
    clients: ConnectionClients, seaplane: Dict[str, Any], depart_dt: Optional[datetime]
) -> Dict[str, Any]:
    """Seaplane leg from the curated published static table."""
    route = seaplane.get("route")
    day = _parse_date(seaplane.get("day"), depart_dt)
    try:
        rows = clients.seaplane_schedule(route, day) or []
    except Exception as exc:
        logger.warning("connections: seaplane_schedule failed: %s", exc)
        rows = []
    leg: Dict[str, Any] = {
        "leg": "seaplane",
        "route": route,
        "label": PUBLISHED if rows else None,
        "schedule": rows,
        "source": "sources.seaplane.seaplane_schedule",
        "note": "Published static timetable, not a live status.",
    }
    if not rows:
        leg["seaplane_note"] = "No seaplane times returned, seaplane unknown."
    return leg


# --------------------------------------------------------------------------- #
# Feasibility (drive arrival vs sailing departure)
# --------------------------------------------------------------------------- #

def _assess_feasibility(
    depart_dt: Optional[datetime],
    drive_leg: Dict[str, Any],
    ferry_leg: Dict[str, Any],
    buffer_min: int,
) -> Dict[str, Any]:
    sailing_dt = ferry_leg.get("sailing_dt")
    arrival = _parse_dt(drive_leg.get("arrival"))
    interval = drive_leg.get("arrival_interval")
    arrival_high = None
    if isinstance(interval, list) and len(interval) == 2:
        arrival_high = _parse_dt(interval[1])

    result: Dict[str, Any] = {
        "verdict": "unknown",
        "feasible": None,
        "buffer_minutes": buffer_min,
        "sailing_departure": sailing_dt.isoformat() if sailing_dt else None,
        "arrival_estimate": drive_leg.get("arrival"),
        "arrival_interval": interval,
        "margin_minutes": None,
        "worst_case_margin_minutes": None,
    }
    if depart_dt is None or sailing_dt is None or arrival is None:
        result["reason"] = "Not enough information to judge the connection."
        return result

    margin_mid = (sailing_dt - arrival).total_seconds() / 60.0
    margin_worst = (
        (sailing_dt - arrival_high).total_seconds() / 60.0
        if arrival_high is not None
        else margin_mid
    )
    result["margin_minutes"] = round(margin_mid, 1)
    result["worst_case_margin_minutes"] = round(margin_worst, 1)

    if margin_worst >= buffer_min:
        result["verdict"] = "likely"
        result["feasible"] = True
        result["reason"] = (
            "Even the slow end of the drive estimate reaches the terminal "
            "with the recommended buffer to spare."
        )
    elif margin_mid >= buffer_min:
        result["verdict"] = "tight"
        result["feasible"] = True
        result["reason"] = (
            "The typical drive makes the sailing with the buffer, but the slow "
            "end of the estimate cuts it close."
        )
    elif margin_mid >= 0:
        result["verdict"] = "tight"
        result["feasible"] = True
        result["reason"] = (
            "The typical drive reaches the terminal before departure but "
            "inside the recommended buffer."
        )
    else:
        result["verdict"] = "unlikely"
        result["feasible"] = False
        result["reason"] = (
            "The drive estimate arrives after the sailing departs."
        )
    return result


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #

def plan_connection(
    intent: Dict[str, Any],
    *,
    clients: Optional[ConnectionClients] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Assemble a labeled connection feasibility plan from ``intent``.

    ``intent`` shape (all keys optional unless noted):

    - ``mode``: ``"ferry"`` (default) / ``"flight"`` / ``"seaplane"``.
    - ``branch``: the journey branch string, echoed into the plan.
    - ``question``: free-text question, echoed for display.
    - ``origin``: ``{"label": "SeaTac"}`` for the drive origin.
    - ``depart_dt``: ISO-8601 departure datetime (drives the corridor model).
    - ``ferry``: ``{route_id, departing_terminal_id, arriving_terminal_id,
      trip_date?, depart_clock?, departing_time?, terminal_buffer_minutes?}``.
    - ``flight``: ``{airport_iata?, direction?, flight_number?, limit?}``.
    - ``seaplane``: ``{route?, day?}``.

    Returns a structured plan dict with per-leg honesty labels, a composite
    label (the weakest leg on the path used), and a freshness stamp from the
    youngest measured source. Inject ``clients`` in tests; production uses
    :meth:`ConnectionClients.default`.
    """
    clients = clients or ConnectionClients.default()
    now = now or datetime.now(timezone.utc)

    intent = intent or {}
    mode = (intent.get("mode") or "ferry").lower()
    origin = intent.get("origin") or {}
    origin_label = origin.get("label") or "origin"
    depart_dt = _parse_dt(intent.get("depart_dt"))

    plan: Dict[str, Any] = {
        "version": "1.0.0",
        "mode": mode,
        "branch": intent.get("branch"),
        "question": intent.get("question"),
        "depart_dt": depart_dt.isoformat() if depart_dt else None,
        "legs": [],
        "feasibility": None,
        "composite_label": None,
        "freshness": None,
        "honesty_notes": [],
        "labels_legend": dict(LABEL_LEGEND),
        "generated_at": now.isoformat(),
    }

    legs: List[Dict[str, Any]] = []
    measured_stamps: List[Any] = []
    notes: List[str] = []

    ferry = intent.get("ferry")
    flight = intent.get("flight")
    seaplane = intent.get("seaplane")

    # Drive leg precedes a ferry / seaplane departure that has a road approach.
    ferry_leg: Optional[Dict[str, Any]] = None
    if mode == "ferry" or ferry:
        ferry = ferry or {}
        destination = ferry.get("departing_terminal_name") or "the terminal"

        # The four ferry-branch legs (corridor ETA + WSF schedule / sailing
        # space / vessel locations) are independent blocking calls. Fan them out
        # so wall time approaches the slowest leg instead of their sum. Matching,
        # feasibility, labels, and freshness all stay sequential below; only the
        # I/O fetches run concurrently. Each result is None on failure and the
        # builders coerce it to their empty sentinel, so behavior is unchanged.
        route_id = ferry.get("route_id")
        dep_term = ferry.get("departing_terminal_id")
        trip_date = _parse_date(ferry.get("trip_date"), depart_dt)

        fetch_tasks: Dict[str, Callable[[], Any]] = {}
        if depart_dt is not None:
            fetch_tasks["drive_prediction"] = lambda: clients.predict_eta(depart_dt)
        if route_id is not None and trip_date is not None:
            fetch_tasks["ferry_schedule"] = (
                lambda: clients.schedule(int(route_id), trip_date)
            )
        fetch_tasks["ferry_spaces"] = lambda: clients.sailing_space(dep_term)
        fetch_tasks["ferry_vessels"] = lambda: clients.vessel_locations()

        fetched = fetch_legs_concurrently(fetch_tasks)

        drive_leg = _build_drive_leg(
            clients,
            depart_dt,
            origin_label,
            destination,
            prediction=fetched.get("drive_prediction"),
        )
        legs.append(drive_leg)
        notes.append(drive_leg["segments"][1]["note"])

        ferry_leg = _build_ferry_leg(
            clients,
            ferry,
            depart_dt,
            schedule=(
                fetched["ferry_schedule"] if "ferry_schedule" in fetched else _UNSET
            ),
            spaces=fetched.get("ferry_spaces"),
            vessels=fetched.get("ferry_vessels"),
        )
        # Stamp measured freshness from the live ferry signals actually used.
        if ferry_leg.get("space") is not None:
            measured_stamps.append(now)
        if ferry_leg.get("vessel") is not None:
            measured_stamps.append(ferry_leg["vessel"].get("timestamp"))
        ferry_for_plan = {k: v for k, v in ferry_leg.items() if k != "sailing_dt"}
        legs.append(ferry_for_plan)

        buffer_min = int(
            (ferry or {}).get("terminal_buffer_minutes", _DEFAULT_TERMINAL_BUFFER_MIN)
        )
        plan["feasibility"] = _assess_feasibility(
            depart_dt, drive_leg, ferry_leg, buffer_min
        )

    if mode == "flight" or flight:
        legs.append(_build_flight_leg(clients, flight or {}))

    if mode == "seaplane" or seaplane:
        legs.append(_build_seaplane_leg(clients, seaplane or {}, depart_dt))

    plan["legs"] = legs

    # Composite label = weakest label across legs ON THE PATH USED (legs that
    # actually resolved a label). Unknown legs do not strengthen the composite.
    leg_labels = [leg.get("label") for leg in legs]
    plan["composite_label"] = weakest_label(leg_labels)

    plan["freshness"] = _youngest(measured_stamps)

    if mode == "seaplane" or seaplane:
        notes.append("Seaplane times are a published timetable, not a live status.")
    if mode == "flight" or flight:
        notes.append(
            "The flight board is the scheduled board. Live aircraft positions "
            "are not used for this plan."
        )
    plan["honesty_notes"] = notes
    return plan
