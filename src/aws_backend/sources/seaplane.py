"""Kenmore Air seaplane schedule — curated PUBLISHED static table (no network).

Kenmore Air exposes no open API for its scheduled floatplane service
(CONNECTIONS_RESEARCH section 3: "Kenmore Air published timetable (no open API)
-> published static table"). The Trips planner still needs the Seattle Lake
Union <-> San Juan Islands seaplane legs, so this module ships a hand-curated
snapshot of the PUBLISHED seasonal timetable, labeled ``published`` (never live)
with the source date stamped on every row.

Honesty contract:
- Every row is labeled ``published`` with ``source`` + ``source_date``. The
  adapter NEVER claims realtime status for a seaplane (``realtime`` is always
  ``False``). The planner must present these as scheduled, not guaranteed.
- The times below are a curated snapshot of Kenmore Air's published seasonal
  timetable as transcribed on the stamped :data:`SOURCE_DATE`. Kenmore's actual
  departures shift seasonally and are tide-restricted; re-transcribe and bump
  ``SOURCE_DATE`` when the published timetable changes. Treat ``effective_start``
  / ``effective_end`` as the published seasonal window, not a guarantee.

There is NO network in this module. It mirrors the graceful contract of the
sibling clients (``wsf.py`` / ``wsdot_traffic.py``): callers always get a list,
and an over-specific filter simply yields ``[]`` (unknown), never an error.
"""

from __future__ import annotations

from datetime import date as date_type
from typing import Any, Dict, List, Optional

# --------------------------------------------------------------------------- #
# Provenance (stamped on every returned row)
# --------------------------------------------------------------------------- #

#: Honesty label carried by every row. Kenmore is a published timetable, not live.
SOURCE_LABEL = "published"

#: Human-readable provenance for the curated table.
SOURCE = "Kenmore Air published seaplane timetable (kenmoreair.com)"

#: Date the published timetable below was transcribed. Bump when re-transcribed.
SOURCE_DATE = "2026-06-27"

# Day-of-operation codes -> Python weekday() integers (Mon=0 .. Sun=6).
_DAY_CODE_TO_WEEKDAY = {
    "Mon": 0,
    "Tue": 1,
    "Wed": 2,
    "Thu": 3,
    "Fri": 4,
    "Sat": 5,
    "Sun": 6,
}
_DAILY = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Kenmore's Seattle seaplane base used by the scheduled San Juan service.
_LAKE_UNION = "Seattle Lake Union Seaplane Base"

# Published summer season window (seaplane service is seasonal + tide-restricted;
# CONNECTIONS_RESEARCH / kenmoreair.com note March-October seasonal operation).
_SUMMER_START = "2026-05-15"
_SUMMER_END = "2026-09-30"


def _row(
    *,
    route: str,
    origin: str,
    destination: str,
    departure_time: str,
    arrival_time: str,
    days_of_operation: List[str],
    dock: str,
    duration_min: int,
) -> Dict[str, Any]:
    """Build one published schedule row in the planner's normalized shape."""
    return {
        "route": route,
        "origin": origin,
        "destination": destination,
        "departure_time": departure_time,   # local (America/Los_Angeles), HH:MM
        "arrival_time": arrival_time,        # local, HH:MM
        "days_of_operation": list(days_of_operation),
        "season": "Summer 2026",
        "effective_start": _SUMMER_START,
        "effective_end": _SUMMER_END,
        "terminal": _LAKE_UNION,
        "dock": dock,
        "carrier": "Kenmore Air",
        "aircraft": "de Havilland Beaver / Otter (floatplane)",
        "duration_min": duration_min,
        # Honesty fields — published, never live.
        "label": SOURCE_LABEL,
        "realtime": False,
        "source": SOURCE,
        "source_date": SOURCE_DATE,
    }


# --------------------------------------------------------------------------- #
# Curated published timetable (Seattle Lake Union <-> San Juan Islands)
#
# Snapshot of the published seasonal floatplane schedule as of SOURCE_DATE.
# Times are local and approximate the published timetable; they are labeled
# published (scheduled, not guaranteed) and are seasonal + tide-restricted.
# --------------------------------------------------------------------------- #

_SCHEDULE: List[Dict[str, Any]] = [
    # Lake Union <-> Friday Harbor (San Juan Island)
    _row(
        route="Lake Union <-> Friday Harbor",
        origin=_LAKE_UNION,
        destination="Friday Harbor Seaplane Base",
        departure_time="09:00",
        arrival_time="09:45",
        days_of_operation=_DAILY,
        dock="Friday Harbor marina pier",
        duration_min=45,
    ),
    _row(
        route="Lake Union <-> Friday Harbor",
        origin=_LAKE_UNION,
        destination="Friday Harbor Seaplane Base",
        departure_time="17:15",
        arrival_time="18:00",
        days_of_operation=_DAILY,
        dock="Friday Harbor marina pier",
        duration_min=45,
    ),
    _row(
        route="Friday Harbor <-> Lake Union",
        origin="Friday Harbor Seaplane Base",
        destination=_LAKE_UNION,
        departure_time="10:00",
        arrival_time="10:45",
        days_of_operation=_DAILY,
        dock="Lake Union seaplane terminal",
        duration_min=45,
    ),
    _row(
        route="Friday Harbor <-> Lake Union",
        origin="Friday Harbor Seaplane Base",
        destination=_LAKE_UNION,
        departure_time="18:15",
        arrival_time="19:00",
        days_of_operation=_DAILY,
        dock="Lake Union seaplane terminal",
        duration_min=45,
    ),
    # Lake Union <-> Roche Harbor (San Juan Island, north)
    _row(
        route="Lake Union <-> Roche Harbor",
        origin=_LAKE_UNION,
        destination="Roche Harbor Seaplane Base",
        departure_time="09:00",
        arrival_time="09:50",
        days_of_operation=_DAILY,
        dock="Roche Harbor resort dock",
        duration_min=50,
    ),
    _row(
        route="Roche Harbor <-> Lake Union",
        origin="Roche Harbor Seaplane Base",
        destination=_LAKE_UNION,
        departure_time="10:05",
        arrival_time="10:55",
        days_of_operation=_DAILY,
        dock="Lake Union seaplane terminal",
        duration_min=50,
    ),
    # Lake Union <-> West Sound (Orcas Island) — tide-restricted seasonal
    _row(
        route="Lake Union <-> West Sound (Orcas)",
        origin=_LAKE_UNION,
        destination="West Sound Seaplane Base (Orcas Island)",
        departure_time="09:00",
        arrival_time="09:55",
        days_of_operation=["Thu", "Fri", "Sat", "Sun"],
        dock="West Sound dock",
        duration_min=55,
    ),
    _row(
        route="West Sound (Orcas) <-> Lake Union",
        origin="West Sound Seaplane Base (Orcas Island)",
        destination=_LAKE_UNION,
        departure_time="10:10",
        arrival_time="11:05",
        days_of_operation=["Thu", "Fri", "Sat", "Sun"],
        dock="Lake Union seaplane terminal",
        duration_min=55,
    ),
    # Lake Union <-> Rosario (Orcas Island)
    _row(
        route="Lake Union <-> Rosario (Orcas)",
        origin=_LAKE_UNION,
        destination="Rosario Resort Seaplane Base (Orcas Island)",
        departure_time="16:45",
        arrival_time="17:40",
        days_of_operation=["Fri", "Sat", "Sun"],
        dock="Rosario Resort dock",
        duration_min=55,
    ),
    # Lake Union <-> Lopez Island
    _row(
        route="Lake Union <-> Lopez Island",
        origin=_LAKE_UNION,
        destination="Lopez Island Seaplane Base",
        departure_time="09:00",
        arrival_time="09:50",
        days_of_operation=["Fri", "Sat", "Sun"],
        dock="Fisherman Bay dock",
        duration_min=50,
    ),
]


# --------------------------------------------------------------------------- #
# Filtering helpers
# --------------------------------------------------------------------------- #

def _matches_route(row: Dict[str, Any], route: str) -> bool:
    """Case-insensitive substring match on route / origin / destination."""
    needle = route.strip().lower()
    if not needle:
        return True
    haystack = " ".join(
        str(row.get(key, "")) for key in ("route", "origin", "destination")
    ).lower()
    return needle in haystack


def _operates_on(row: Dict[str, Any], day: date_type) -> bool:
    """True when ``row`` runs on ``day`` (weekday in days_of_operation AND the
    day falls within the published seasonal window)."""
    weekday = day.weekday()
    operating_weekdays = {
        _DAY_CODE_TO_WEEKDAY[code]
        for code in row.get("days_of_operation", [])
        if code in _DAY_CODE_TO_WEEKDAY
    }
    if weekday not in operating_weekdays:
        return False
    iso = day.isoformat()
    start = row.get("effective_start")
    end = row.get("effective_end")
    if start and iso < start:
        return False
    if end and iso > end:
        return False
    return True


# --------------------------------------------------------------------------- #
# Public adapter contract (CONNECTIONS_RESEARCH section 5)
# --------------------------------------------------------------------------- #

def seaplane_schedule(
    route: Optional[str] = None,
    day: Optional[date_type] = None,
) -> List[Dict[str, Any]]:
    """Return the curated PUBLISHED Kenmore Air seaplane schedule (no network).

    Args:
        route: optional case-insensitive substring filter matched against the
            route name, origin, or destination (e.g. ``"Friday Harbor"`` or
            ``"Orcas"``). ``None`` returns every route.
        day: optional :class:`datetime.date`. When given, only rows that operate
            on that weekday AND fall within the published seasonal window are
            returned. An out-of-season or non-operating day yields ``[]``
            ("unknown"), never a fabricated departure.

    Returns:
        A list of published schedule rows (copies, safe to mutate), each stamped
        ``label="published"``, ``realtime=False``, ``source``, ``source_date``.
        Always a list; an over-specific filter simply returns ``[]``.
    """
    rows = [dict(row) for row in _SCHEDULE]
    if route is not None:
        rows = [r for r in rows if _matches_route(r, route)]
    if day is not None:
        rows = [r for r in rows if _operates_on(r, day)]
    return rows


def source_stamp() -> Dict[str, str]:
    """Provenance stamp for the curated table (label + source + source_date)."""
    return {
        "label": SOURCE_LABEL,
        "source": SOURCE,
        "source_date": SOURCE_DATE,
    }
