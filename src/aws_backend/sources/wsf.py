"""Washington State Ferries (WSF) REST API client for the Trips planner.

Source: WSDOT WSF REST API, base host ``https://www.wsdot.wa.gov/ferries/api``.
Open + free, JSON by default. The free WSDOT Traveler API access code is read
ONLY from the ``WSDOT_ACCESS_CODE`` env var and is passed as the query parameter
``apiaccesscode`` (lowercase — the WSF family differs from WSDOT Traffic, which
uses ``AccessCode``; see CONNECTIONS_RESEARCH section 0). The code is never
logged or returned to a caller.

All public functions degrade gracefully: when ``WSDOT_ACCESS_CODE`` is absent, or
the upstream is unreachable / returns a non-200, list endpoints return ``[]`` and
``schedule`` returns ``{}`` rather than raising.

WSF timestamps are WCF / ASP.NET JSON dates (``"/Date(1719500000000-0700)/"``):
epoch-millis (UTC) plus a display UTC offset. :func:`parse_wcf_date` parses these
to timezone-aware datetimes; record fields carry the ISO-8601 string so the
payload stays JSON-serializable for the planner.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import date as date_type
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

WSF_BASE = "https://www.wsdot.wa.gov/ferries/api"
_TIMEOUT = 20.0

# WCF/ASP.NET JSON date: /Date(<millis>[<+|-><HHMM>])/  (millis are UTC epoch ms).
_WCF_DATE_RE = re.compile(r"/Date\((-?\d+)(?:([+-])(\d{2})(\d{2}))?\)/")


class WsfDisabled(RuntimeError):
    """Raised internally when no WSDOT access code is configured."""


# --------------------------------------------------------------------------- #
# Access code + redaction
# --------------------------------------------------------------------------- #

def _access_code() -> str:
    code = os.getenv("WSDOT_ACCESS_CODE", "")
    if not code:
        raise WsfDisabled("WSDOT_ACCESS_CODE not configured")
    return code


def wsf_enabled() -> bool:
    """True when a WSDOT access code is present in the environment."""
    return bool(os.getenv("WSDOT_ACCESS_CODE"))


def _redact(text: str) -> str:
    """Strip the access code from any string before it reaches a log sink.

    ``requests`` exceptions embed the full request URL, which carries
    ``apiaccesscode=...``. Redact both the live value and the query parameter.
    """
    code = os.getenv("WSDOT_ACCESS_CODE")
    if code:
        text = text.replace(code, "***")
    return re.sub(r"(?i)(apiaccesscode=)[^&\s]+", r"\1***", text)


# --------------------------------------------------------------------------- #
# WCF date parsing
# --------------------------------------------------------------------------- #

def parse_wcf_date(value: Any) -> Optional[datetime]:
    """Parse a WCF/ASP.NET JSON date into a timezone-aware datetime.

    ``"/Date(1719500000000-0700)/"`` -> aware datetime at the embedded offset.
    The epoch is milliseconds since the Unix epoch in UTC; the trailing offset is
    the display timezone WSF intends. Returns ``None`` for missing/unparseable
    values (WSF uses ``null`` for, e.g., a not-yet-known ``ArrivingTime``).
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    match = _WCF_DATE_RE.search(value)
    if not match:
        return None
    millis = int(match.group(1))
    instant = datetime.fromtimestamp(millis / 1000.0, tz=timezone.utc)
    sign, hh, mm = match.group(2), match.group(3), match.group(4)
    if sign and hh is not None and mm is not None:
        delta = timedelta(hours=int(hh), minutes=int(mm))
        offset = -delta if sign == "-" else delta
        return instant.astimezone(timezone(offset))
    return instant


def _iso(value: Any) -> Optional[str]:
    """WCF date string -> ISO-8601 string (or None)."""
    parsed = parse_wcf_date(value)
    return parsed.isoformat() if parsed else None


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #

def _get(path: str) -> Any:
    """GET ``{WSF_BASE}/{path}`` with the lowercase ``apiaccesscode`` param.

    Returns the parsed JSON, or ``None`` on any failure (missing code,
    transport error, non-200, or non-JSON body). Never raises to the caller.
    """
    try:
        code = _access_code()
    except WsfDisabled as exc:
        logger.debug("WSF skipped: %s", exc)
        return None
    url = f"{WSF_BASE}/{path.lstrip('/')}"
    try:
        resp = requests.get(url, params={"apiaccesscode": code}, timeout=_TIMEOUT)
    except requests.RequestException as exc:
        logger.warning("WSF request failed: %s", _redact(str(exc)))
        return None
    if resp.status_code != 200:
        logger.warning("WSF %s -> HTTP %s", _redact(url), resp.status_code)
        return None
    try:
        return resp.json()
    except ValueError as exc:
        logger.warning("WSF non-JSON response: %s", _redact(str(exc)))
        return None


# --------------------------------------------------------------------------- #
# Parsers
# --------------------------------------------------------------------------- #

def _parse_vessel(v: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "vessel_id": v.get("VesselID"),
        "vessel_name": v.get("VesselName"),
        "mmsi": v.get("Mmsi"),
        "departing_terminal_id": v.get("DepartingTerminalID"),
        "departing_terminal_name": v.get("DepartingTerminalName"),
        "departing_terminal_abbrev": v.get("DepartingTerminalAbbrev"),
        "arriving_terminal_id": v.get("ArrivingTerminalID"),
        "arriving_terminal_name": v.get("ArrivingTerminalName"),
        "arriving_terminal_abbrev": v.get("ArrivingTerminalAbbrev"),
        "latitude": v.get("Latitude"),
        "longitude": v.get("Longitude"),
        "speed": v.get("Speed"),
        "heading": v.get("Heading"),
        "in_service": v.get("InService"),
        "at_dock": v.get("AtDock"),
        "left_dock": _iso(v.get("LeftDock")),
        "eta": _iso(v.get("Eta")),
        # The honesty source for the ETA (position-based vs scheduled).
        "eta_basis": v.get("EtaBasis"),
        "scheduled_departure": _iso(v.get("ScheduledDeparture")),
        "op_route_abbrev": v.get("OpRouteAbbrev"),
        "vessel_position_num": v.get("VesselPositionNum"),
        "sort_seq": v.get("SortSeq"),
        "managed_by": v.get("ManagedBy"),
        "timestamp": _iso(v.get("TimeStamp")),
        "vessel_watch_status": v.get("VesselWatchStatus"),
        "vessel_watch_msg": v.get("VesselWatchMsg"),
    }


def _parse_arrival_space(a: Dict[str, Any]) -> Dict[str, Any]:
    """One ``SailingSpaceArrival``: drive-up / reservable counts per arrival
    terminal, honoring the ``Display*`` suppression flags.

    When ``DisplayDriveUpSpace`` / ``DisplayReservableSpace`` is False the count
    is not meaningful for this sailing, so the numeric field is suppressed to
    ``None`` (never shown as a misleading 0). The raw counts + display flags are
    preserved so the planner can decide presentation.
    """
    display_drive_up = a.get("DisplayDriveUpSpace")
    display_reservable = a.get("DisplayReservableSpace")
    drive_up_raw = a.get("DriveUpSpaceCount")
    reservable_raw = a.get("ReservableSpaceCount")
    return {
        "terminal_id": a.get("TerminalID"),
        "terminal_name": a.get("TerminalName"),
        "vessel_id": a.get("VesselID"),
        "vessel_name": a.get("VesselName"),
        "display_drive_up_space": display_drive_up,
        "drive_up_space_count": drive_up_raw if display_drive_up else None,
        "drive_up_space_count_raw": drive_up_raw,
        "drive_up_space_hex_color": a.get("DriveUpSpaceHexColor"),
        "display_reservable_space": display_reservable,
        "reservable_space_count": reservable_raw if display_reservable else None,
        "reservable_space_count_raw": reservable_raw,
        "reservable_space_hex_color": a.get("ReservableSpaceHexColor"),
        "max_space_count": a.get("MaxSpaceCount"),
        "arrival_terminal_ids": a.get("ArrivalTerminalIDs"),
    }


def _parse_departing_space(d: Dict[str, Any]) -> Dict[str, Any]:
    arrivals = d.get("SpaceForArrivalTerminals") or []
    return {
        "departure": _iso(d.get("Departure")),
        "is_cancelled": d.get("IsCancelled"),
        "vessel_id": d.get("VesselID"),
        "vessel_name": d.get("VesselName"),
        "max_space_count": d.get("MaxSpaceCount"),
        "space_for_arrival_terminals": [_parse_arrival_space(a) for a in arrivals],
    }


def _parse_sailing_space(t: Dict[str, Any]) -> Dict[str, Any]:
    departing = t.get("DepartingSpaces") or []
    return {
        "terminal_id": t.get("TerminalID"),
        "terminal_subject_id": t.get("TerminalSubjectID"),
        "region_id": t.get("RegionID"),
        "terminal_name": t.get("TerminalName"),
        "terminal_abbrev": t.get("TerminalAbbrev"),
        "sort_seq": t.get("SortSeq"),
        "is_no_fare_collected": t.get("IsNoFareCollected"),
        "no_fare_collected_msg": t.get("NoFareCollectedMsg"),
        "departing_spaces": [_parse_departing_space(d) for d in departing],
    }


def _parse_sched_time(s: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "departing_time": _iso(s.get("DepartingTime")),
        "arriving_time": _iso(s.get("ArrivingTime")),
        "loading_rule": s.get("LoadingRule"),
        "vessel_id": s.get("VesselID"),
        "vessel_name": s.get("VesselName"),
        "vessel_handicap_accessible": s.get("VesselHandicapAccessible"),
        "vessel_position_num": s.get("VesselPositionNum"),
        "routes": s.get("Routes"),
        "annotation_indexes": s.get("AnnotationIndexes"),
    }


def _parse_terminal_combo(c: Dict[str, Any]) -> Dict[str, Any]:
    times = c.get("Times") or []
    return {
        "departing_terminal_id": c.get("DepartingTerminalID"),
        "departing_terminal_name": c.get("DepartingTerminalName"),
        "arriving_terminal_id": c.get("ArrivingTerminalID"),
        "arriving_terminal_name": c.get("ArrivingTerminalName"),
        "sailing_notes": c.get("SailingNotes"),
        "annotations": c.get("Annotations"),
        "annotations_ivr": c.get("AnnotationsIVR"),
        "times": [_parse_sched_time(s) for s in times],
    }


def _parse_schedule(s: Dict[str, Any]) -> Dict[str, Any]:
    combos = s.get("TerminalCombos") or []
    return {
        "schedule_id": s.get("ScheduleID"),
        "schedule_name": s.get("ScheduleName"),
        "schedule_season": s.get("ScheduleSeason"),
        "schedule_pdf_url": s.get("SchedulePDFUrl"),
        "schedule_start": _iso(s.get("ScheduleStart")),
        "schedule_end": _iso(s.get("ScheduleEnd")),
        "all_routes": s.get("AllRoutes"),
        "terminal_combos": [_parse_terminal_combo(c) for c in combos],
    }


def _parse_wait_time(w: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "route_id": w.get("RouteID"),
        "route_name": w.get("RouteName"),
        # Human-authored free text -> advisory only, never parse into a number.
        "wait_time_notes": w.get("WaitTimeNotes"),
        "wait_time_last_updated": _iso(w.get("WaitTimeLastUpdated")),
        "wait_time_ivr_notes": w.get("WaitTimeIVRNotes"),
    }


def _parse_terminal_wait(t: Dict[str, Any]) -> Dict[str, Any]:
    waits = t.get("WaitTimes") or []
    return {
        "terminal_id": t.get("TerminalID"),
        "terminal_subject_id": t.get("TerminalSubjectID"),
        "region_id": t.get("RegionID"),
        "terminal_name": t.get("TerminalName"),
        "terminal_abbrev": t.get("TerminalAbbrev"),
        "sort_seq": t.get("SortSeq"),
        "wait_times": [_parse_wait_time(w) for w in waits],
    }


def _parse_route(r: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "route_id": r.get("RouteID"),
        "route_abbrev": r.get("RouteAbbrev"),
        "description": r.get("Description"),
        "region_id": r.get("RegionID"),
        "service_disruptions": r.get("ServiceDisruptions"),
    }


def _parse_terminal(t: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "terminal_id": t.get("TerminalID"),
        "description": t.get("Description"),
    }


def _trip_date(value: date_type) -> str:
    """WSF TripDate path segment is ``YYYY-MM-DD``."""
    return value.strftime("%Y-%m-%d")


# --------------------------------------------------------------------------- #
# Public adapter contract (CONNECTIONS_RESEARCH section 5)
# --------------------------------------------------------------------------- #

def vessel_locations(vessel_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Real-time vessel positions + ETA (measured, ~5 s; do not cache long).

    Optionally narrow to a single ``vessel_id``. Returns ``[]`` when the access
    code is absent or the upstream is unreachable.
    """
    path = (
        f"/vessels/rest/vessellocations/{int(vessel_id)}"
        if vessel_id is not None
        else "/vessels/rest/vessellocations"
    )
    data = _get(path)
    if data is None:
        return []
    # The /{VesselID} variant returns a single object; the list variant an array.
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return []
    return [_parse_vessel(v) for v in data if isinstance(v, dict)]


def schedule(route_id: int, date: date_type) -> Dict[str, Any]:
    """Schedule for ``route_id`` on ``date`` (``SchedResponse``).

    Returns ``{}`` when the access code is absent or the upstream is unreachable.
    """
    path = f"/schedule/rest/schedule/{_trip_date(date)}/{int(route_id)}"
    data = _get(path)
    if not isinstance(data, dict):
        return {}
    return _parse_schedule(data)


def sailing_space(terminal_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Terminal sailing space — drive-up vs reservable left per departure
    (measured, ~5 s; do not cache long).

    Each terminal carries ``departing_spaces[]`` -> ``space_for_arrival_terminals[]``
    with ``drive_up_space_count`` / ``reservable_space_count``. Counts are
    suppressed to ``None`` when the corresponding ``display_*`` flag is False
    (raw values are kept under ``*_raw``). Returns ``[]`` on absent code / error.
    """
    path = (
        f"/terminals/rest/terminalsailingspace/{int(terminal_id)}"
        if terminal_id is not None
        else "/terminals/rest/terminalsailingspace"
    )
    data = _get(path)
    if data is None:
        return []
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return []
    return [_parse_sailing_space(t) for t in data if isinstance(t, dict)]


def wait_times(terminal_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Terminal wait times. ``wait_time_notes`` is human free text — surface as
    advisory/heuristic, never parse to a number. Returns ``[]`` on absent
    code / error.
    """
    path = (
        f"/terminals/rest/terminalwaittimes/{int(terminal_id)}"
        if terminal_id is not None
        else "/terminals/rest/terminalwaittimes"
    )
    data = _get(path)
    if data is None:
        return []
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return []
    return [_parse_terminal_wait(t) for t in data if isinstance(t, dict)]


def routes(trip_date: date_type) -> List[Dict[str, Any]]:
    """Routes valid on ``trip_date`` for RouteID resolution (published; cache via
    ``/cacheflushdate``). Returns ``[]`` on absent code / error.
    """
    data = _get(f"/schedule/rest/routes/{_trip_date(trip_date)}")
    if not isinstance(data, list):
        return []
    return [_parse_route(r) for r in data if isinstance(r, dict)]


def terminals(trip_date: date_type) -> List[Dict[str, Any]]:
    """Terminals valid on ``trip_date`` for TerminalID resolution (published;
    cache via ``/cacheflushdate``). Returns ``[]`` on absent code / error.
    """
    data = _get(f"/schedule/rest/terminals/{_trip_date(trip_date)}")
    if not isinstance(data, list):
        return []
    return [_parse_terminal(t) for t in data if isinstance(t, dict)]
