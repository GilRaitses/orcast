"""WSDOT Traveler API — road traffic client for the SeaTac <-> Anacortes corridor.

Backs the Trips planner's road leg with WSDOT realtime travel times + traffic
flow. Two honesty-critical facts from the W2 recon
(``.cca/.../console-journey-trips/CONNECTIONS_RESEARCH.md`` sections 0 + 2) are
pinned in code:

1. The query parameter is ``AccessCode`` (PascalCase) for the Traffic REST.svc
   endpoints. This DIFFERS from WSF (``apiaccesscode``, lowercase). Both read the
   same secret from env ``WSDOT_ACCESS_CODE``.
2. Measured TravelTimes coverage on I-5 ENDS near Arlington (~MP 208). There is
   NO TravelTimes route for Arlington -> Mount Vernon -> Burlington -> SR 20 ->
   Anacortes. ``corridor_route_ids()`` therefore surfaces ONLY the southern
   I-5 routes the feed actually returns; the northern leg is left for the W3
   corridor model to label as modeled (never measured).

The access code is read ONLY from the env var, never hard-coded, never logged,
never written to a tracked file. Missing code degrades gracefully: the read
helpers return ``[]`` instead of raising.

Endpoints (REST .svc JSON):
  Travel times:  /Traffic/api/TravelTimes/TravelTimesREST.svc/GetTravelTimesAsJson
  Traffic flow:  /Traffic/api/TrafficFlow/TrafficFlowREST.svc/GetTrafficFlowsAsJson

WCF/ASP.NET dates (``/Date(1719500000000-0700)/``) are parsed to aware UTC
datetimes.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

WSDOT_BASE = "https://www.wsdot.wa.gov"
_TRAVEL_TIMES_PATH = "/Traffic/api/TravelTimes/TravelTimesREST.svc/GetTravelTimesAsJson"
_TRAFFIC_FLOW_PATH = "/Traffic/api/TrafficFlow/TrafficFlowREST.svc/GetTrafficFlowsAsJson"
_TIMEOUT = 20.0

# FlowReadingValue enum (recon section 2). 0/5 are non-readings; 1-4 are live
# congestion levels used to color the corridor where no travel-time route exists.
FLOW_READING_LABELS = {
    0: "Unknown",
    1: "WideOpen",
    2: "Moderate",
    3: "Heavy",
    4: "StopAndGo",
    5: "NoData",
}

# SeaTac -> Anacortes northbound I-5 chain, by friendly ``Name`` (recon section 2).
# TravelTimeID integers are NOT static across the feed, so the corridor is
# resolved at runtime by matching on these names (+ I-5 / Northbound when the
# feed provides RoadwayLocation detail). Ordered south -> north.
#
# The express-lane / HOV variants ("Seattle-Everett HOV", "... EL") are excluded:
# the corridor model wants the general-purpose mainline, not the reversible
# express lanes.
CORRIDOR_ROUTE_NAMES: List[str] = [
    "SeaTac-Seattle",       # leg 1: airport area north into Seattle (~13.0 mi)
    "Seattle-Lynnwood",     # leg 2a: optional finer-grained sub-leg (~15.7 mi)
    "Seattle-Everett",      # leg 2: Seattle -> Everett (~26.9 mi)
    "Everett-Marysville",   # leg 3: through Everett/Marysville (~7.9 mi)
    "Everett-Arlington",    # leg 4: north to Arlington ~MP 208 (~13.1 mi)
]

# Tokens that mark express-lane / HOV / reverse variants we do not want in the
# mainline corridor chain.
_EXCLUDED_NAME_TOKENS = ("hov", " el", "-el", "express", "reverse", "exp lane")

# Default appendable history log. data/external/ is already gitignored
# (license-gated external data), so this jsonl is never committed.
_DEFAULT_HISTORY_PATH = (
    Path(os.getenv("ORCAST_REPO_ROOT", Path(__file__).resolve().parents[3]))
    / "data"
    / "external"
    / "traffic_corridor"
    / "seatac_anacortes.jsonl"
)

# WCF/ASP.NET JSON date: "/Date(1719500000000-0700)/" or "/Date(1719500000000)/".
_WCF_DATE_RE = re.compile(r"/Date\((-?\d+)([+-]\d{4})?\)/")


# --------------------------------------------------------------------------- #
# Access code (env only; never logged / committed)
# --------------------------------------------------------------------------- #

def access_code() -> str:
    """Return the WSDOT Traveler API access code from env, or "" when unset."""
    return os.getenv("WSDOT_ACCESS_CODE", "")


def is_configured() -> bool:
    """True when an access code is present so live calls can be attempted."""
    return bool(access_code())


# --------------------------------------------------------------------------- #
# WCF date parsing
# --------------------------------------------------------------------------- #

def parse_wcf_date(value: Any) -> Optional[datetime]:
    """Parse a WCF/ASP.NET ``/Date(ms[+/-hhmm])/`` string to an aware UTC datetime.

    The epoch milliseconds are UTC; the trailing offset is the provider's display
    offset and does not change the instant, so we always return UTC. Returns
    ``None`` for null / unparseable values rather than raising.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str):
        return None
    match = _WCF_DATE_RE.search(value)
    if not match:
        return None
    try:
        millis = int(match.group(1))
    except ValueError:
        return None
    return datetime.fromtimestamp(millis / 1000.0, tz=timezone.utc)


def _parse_roadway_location(loc: Any) -> Optional[Dict[str, Any]]:
    """Normalize a WSDOT ``RoadwayLocation`` object."""
    if not isinstance(loc, dict):
        return None
    return {
        "description": loc.get("Description"),
        "road_name": loc.get("RoadName"),
        "direction": loc.get("Direction"),
        "milepost": loc.get("MilePost"),
        "latitude": loc.get("Latitude"),
        "longitude": loc.get("Longitude"),
    }


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #

def _get_json(path: str, extra_params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
    """GET a Traffic REST.svc JSON endpoint with the PascalCase ``AccessCode``.

    Returns the decoded JSON, or ``None`` when the code is absent or the request
    fails (graceful degradation; the caller maps ``None`` to an empty list).
    """
    code = access_code()
    if not code:
        logger.debug("WSDOT_ACCESS_CODE not set; skipping %s", path)
        return None
    params: Dict[str, Any] = {"AccessCode": code}
    if extra_params:
        params.update(extra_params)
    try:
        resp = requests.get(f"{WSDOT_BASE}{path}", params=params, timeout=_TIMEOUT)
    except requests.RequestException as exc:
        logger.warning("WSDOT request failed for %s: %s", path, _redact(str(exc), code))
        return None
    if resp.status_code != 200:
        logger.warning("WSDOT %s returned HTTP %s", path, resp.status_code)
        return None
    try:
        return resp.json()
    except ValueError:
        logger.warning("WSDOT %s returned non-JSON content", path)
        return None


def _redact(text: str, code: str) -> str:
    """Strip the access code from any string before it reaches a log sink."""
    if code:
        text = text.replace(code, "***")
    return re.sub(r"(?i)(accesscode=)[^&\s]+", r"\1***", text)


# --------------------------------------------------------------------------- #
# Public read API
# --------------------------------------------------------------------------- #

def parse_travel_time(route: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize one ``TravelTimeRoute`` object into the planner's shape."""
    return {
        "travel_time_id": route.get("TravelTimeID"),
        "name": route.get("Name"),
        "description": route.get("Description"),
        "distance": route.get("Distance"),       # decimal miles
        "average_time": route.get("AverageTime"),  # typical minutes
        "current_time": route.get("CurrentTime"),  # live minutes
        "time_updated": parse_wcf_date(route.get("TimeUpdated")),
        "start_point": _parse_roadway_location(route.get("StartPoint")),
        "end_point": _parse_roadway_location(route.get("EndPoint")),
        "raw": route,
    }


def parse_flow(flow: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize one ``FlowData`` object into the planner's shape."""
    reading = flow.get("FlowReadingValue")
    return {
        "flow_data_id": flow.get("FlowDataID"),
        "time": parse_wcf_date(flow.get("Time")),
        "station_name": flow.get("StationName"),
        "region": flow.get("Region"),
        "reading_value": reading,
        "reading_label": FLOW_READING_LABELS.get(reading, "Unknown"),
        "location": _parse_roadway_location(flow.get("FlowStationLocation")),
        "raw": flow,
    }


def travel_times() -> List[Dict[str, Any]]:
    """All current ``TravelTimeRoute`` readings (measured). Empty when unconfigured."""
    payload = _get_json(_TRAVEL_TIMES_PATH)
    if not isinstance(payload, list):
        return []
    return [parse_travel_time(r) for r in payload if isinstance(r, dict)]


def traffic_flows() -> List[Dict[str, Any]]:
    """All current ``FlowData`` station readings (measured). Empty when unconfigured."""
    payload = _get_json(_TRAFFIC_FLOW_PATH)
    if not isinstance(payload, list):
        return []
    return [parse_flow(f) for f in payload if isinstance(f, dict)]


# --------------------------------------------------------------------------- #
# Corridor resolution
# --------------------------------------------------------------------------- #

def _norm_name(name: Any) -> str:
    return re.sub(r"\s+", " ", str(name or "").strip()).lower()


def _is_excluded_variant(name: Any) -> bool:
    low = _norm_name(name)
    return any(tok in low for tok in _EXCLUDED_NAME_TOKENS)


def corridor_routes(routes: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """Resolve the SeaTac -> Anacortes northbound I-5 travel-time routes.

    Matches the live feed against :data:`CORRIDOR_ROUTE_NAMES` (case/space
    insensitive), dropping HOV / express-lane variants. Returns the parsed route
    dicts ordered south -> north (the order of ``CORRIDOR_ROUTE_NAMES``). Pass
    ``routes`` (already-parsed :func:`travel_times` output) to resolve without a
    network call; otherwise it fetches.

    HONEST COVERAGE: only routes the feed actually returns are included. The
    Arlington -> Anacortes leg has no TravelTimes product, so it never appears
    here; that leg's ETA is modeled downstream, not measured.
    """
    if routes is None:
        routes = travel_times()
    by_name: Dict[str, Dict[str, Any]] = {}
    for route in routes:
        name = route.get("name")
        if _is_excluded_variant(name):
            continue
        key = _norm_name(name)
        # First match per name wins; keep mainline general-purpose routes.
        by_name.setdefault(key, route)
    resolved: List[Dict[str, Any]] = []
    for candidate in CORRIDOR_ROUTE_NAMES:
        match = by_name.get(_norm_name(candidate))
        if match is not None:
            resolved.append(match)
    return resolved


def corridor_route_ids() -> List[int]:
    """Resolve the corridor's ``TravelTimeID`` integers (south -> north).

    Only ids the live feed currently exposes are returned; missing legs are
    silently skipped (e.g. the unmeasured Arlington -> Anacortes leg).
    """
    ids: List[int] = []
    for route in corridor_routes():
        tid = route.get("travel_time_id")
        if isinstance(tid, int):
            ids.append(tid)
    return ids


# --------------------------------------------------------------------------- #
# Self-collected history (W3 corridor model fits on this)
# --------------------------------------------------------------------------- #

def history_path() -> Path:
    """Path of the appendable corridor history log (under gitignored data/external)."""
    return _DEFAULT_HISTORY_PATH


def append_history(record: Dict[str, Any], path: Optional[Path] = None) -> None:
    """Append one corridor travel-time reading to the history log.

    The Traffic API has no historical endpoint, so the W3 corridor model trains
    on a self-collected log. Each call writes ONE JSON object per line with a
    UTC ``logged_at`` stamp (added if absent), so rows are time-ordered and the
    file is safe to append to forever. ``datetime`` values (e.g. parsed
    ``time_updated``) are serialized via ``default=str``.

    ``path`` defaults to ``data/external/traffic_corridor/seatac_anacortes.jsonl``
    (gitignored). Pass an explicit path in tests.
    """
    target = Path(path) if path is not None else history_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    row = dict(record)
    row.setdefault("logged_at", datetime.now(timezone.utc).isoformat())
    line = json.dumps(row, default=str, ensure_ascii=False)
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")
