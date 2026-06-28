"""Flight board adapters for the Trips planner — SeaTac departures/arrivals.

Launch scope (WS-TRIPS A2, phase A): a SeaTac schedule BOARD reader plus the
seaplane static table (``seaplane.py``). Live OpenSky aircraft positions are
DEFERRED — they require an off-AWS proxy + OAuth2 credentials (OpenSky may block
AWS IP ranges; CONNECTIONS_RESEARCH section 6). :func:`opensky_states` is shipped
as a STUB behind a flag and returns ``[]`` with a clear deferral note; no live
OpenSky fetching is implemented here.

Providers (CONNECTIONS_RESEARCH section 3):
- SkyLink (RapidAPI) ``/v3/schedules/{departures|arrivals}`` — primary SeaTac
  board (published/measured). Key from env ``SKYLINK_RAPIDAPI_KEY``.
- AviationStack ``/v1/flights`` — published fallback board. Key from env
  ``AVIATIONSTACK_KEY``.
- OpenSky ``states/all`` — DEFERRED stub (live positions; needs off-AWS proxy).

Honesty + safety contract, mirroring ``wsf.py`` / ``wsdot_traffic.py``:
- API keys are read ONLY from env, never hard-coded, never logged. :func:`_redact`
  strips the key (and the ``access_key`` query param) from any string before it
  reaches a log sink.
- Every read helper degrades gracefully: when the relevant key is absent, or the
  upstream is unreachable / returns non-200 / non-JSON, list readers return ``[]``
  and :func:`flight_status` returns ``{}`` — and NO network call is made when the
  key is absent. Board rows are labeled ``published`` (scheduled, not guaranteed).
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

_TIMEOUT = 20.0

# SkyLink (RapidAPI) ---------------------------------------------------------- #
SKYLINK_HOST = "skylink-api.p.rapidapi.com"
SKYLINK_BASE = f"https://{SKYLINK_HOST}"
SKYLINK_KEY_ENV = "SKYLINK_RAPIDAPI_KEY"

# AviationStack --------------------------------------------------------------- #
AVIATIONSTACK_BASE = "https://api.aviationstack.com/v1"
AVIATIONSTACK_KEY_ENV = "AVIATIONSTACK_KEY"

# OpenSky (DEFERRED) ---------------------------------------------------------- #
#: Live OpenSky positions are off until this flag is truthy AND a proxy is wired.
OPENSKY_ENABLE_ENV = "ORCAST_ENABLE_OPENSKY"
OPENSKY_PROXY_ENV = "OPENSKY_PROXY_URL"
#: Why OpenSky live fetching is not implemented at launch.
OPENSKY_DEFERRAL_NOTE = (
    "deferred: needs an off-AWS proxy (OPENSKY_PROXY_URL) + OAuth2 creds; OpenSky "
    "may block AWS IP ranges, so it must not be called directly from AWS. Live "
    "positional fetching is intentionally not implemented at launch."
)

_VALID_DIRECTIONS = ("departures", "arrivals")


# --------------------------------------------------------------------------- #
# Key access + redaction (env only; never logged)
# --------------------------------------------------------------------------- #

def skylink_enabled() -> bool:
    """True when a SkyLink RapidAPI key is present in the environment."""
    return bool(os.getenv(SKYLINK_KEY_ENV))


def aviationstack_enabled() -> bool:
    """True when an AviationStack key is present in the environment."""
    return bool(os.getenv(AVIATIONSTACK_KEY_ENV))


def opensky_enabled() -> bool:
    """OpenSky live positions are DEFERRED — always ``False`` at launch.

    Even when ``ORCAST_ENABLE_OPENSKY`` is set, live fetching is not implemented
    (it needs an off-AWS proxy); this guards the stub from ever hitting network.
    """
    return False


def _redact(text: str) -> str:
    """Strip any configured API key + the ``access_key`` query param from a string."""
    for env_name in (SKYLINK_KEY_ENV, AVIATIONSTACK_KEY_ENV):
        key = os.getenv(env_name)
        if key:
            text = text.replace(key, "***")
    return re.sub(r"(?i)(access_key=)[^&\s]+", r"\1***", text)


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #

def _get_json(
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    provider: str,
) -> Optional[Any]:
    """GET ``url`` and return decoded JSON, or ``None`` on any failure.

    Never raises to the caller (graceful degradation). The provider name is used
    only for log context; request URLs/exceptions are redacted before logging.
    """
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=_TIMEOUT)
    except requests.RequestException as exc:
        logger.warning("%s request failed: %s", provider, _redact(str(exc)))
        return None
    if resp.status_code != 200:
        logger.warning("%s -> HTTP %s", provider, resp.status_code)
        return None
    try:
        return resp.json()
    except ValueError as exc:
        logger.warning("%s non-JSON response: %s", provider, _redact(str(exc)))
        return None


# --------------------------------------------------------------------------- #
# Parsers
# --------------------------------------------------------------------------- #

def _endpoint(obj: Any) -> Dict[str, Any]:
    """Normalize a departure/arrival endpoint object (SkyLink + AviationStack
    share the same nested shape: airport / iata / icao / terminal / gate /
    scheduled / estimated / actual / delay)."""
    if not isinstance(obj, dict):
        return {}
    return {
        "airport": obj.get("airport"),
        "iata": obj.get("iata"),
        "icao": obj.get("icao"),
        "terminal": obj.get("terminal"),
        "gate": obj.get("gate"),
        "scheduled": obj.get("scheduled"),
        "estimated": obj.get("estimated"),
        "actual": obj.get("actual"),
        "delay": obj.get("delay"),
    }


def _parse_flight(item: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize one flight record (SkyLink schedule item / AviationStack data
    item / SkyLink single flight_status) into the planner's board shape.

    Both providers expose nested ``departure`` / ``arrival`` / ``airline`` /
    ``flight`` objects; flat top-level fields are tolerated as a fallback.
    """
    flight = item.get("flight") if isinstance(item.get("flight"), dict) else {}
    airline = item.get("airline") if isinstance(item.get("airline"), dict) else {}
    return {
        "flight_date": item.get("flight_date"),
        "status": item.get("flight_status") or item.get("status"),
        "flight_number": flight.get("iata") or flight.get("number") or item.get("flight_number"),
        "flight_icao": flight.get("icao"),
        "airline_name": airline.get("name") or item.get("airline_name"),
        "airline_iata": airline.get("iata"),
        "departure": _endpoint(item.get("departure")),
        "arrival": _endpoint(item.get("arrival")),
        # Boards are scheduled data — published, not a guarantee.
        "label": "published",
    }


def _flight_list(payload: Any) -> List[Dict[str, Any]]:
    """Pull the flight array out of a provider payload.

    Handles a top-level list, or a dict wrapping the list under any of the
    common keys (``data`` / ``schedules`` / ``departures`` / ``arrivals`` /
    ``results`` / ``flights``).
    """
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        items = None
        for key in ("data", "schedules", "departures", "arrivals", "results", "flights"):
            value = payload.get(key)
            if isinstance(value, list):
                items = value
                break
        if items is None:
            return []
    else:
        return []
    return [_parse_flight(it) for it in items if isinstance(it, dict)]


# --------------------------------------------------------------------------- #
# Public adapter contract (CONNECTIONS_RESEARCH section 5)
# --------------------------------------------------------------------------- #

def skylink_board(
    airport_iata: str,
    direction: str = "departures",
) -> List[Dict[str, Any]]:
    """SeaTac departure/arrival board via SkyLink RapidAPI (published/measured).

    Args:
        airport_iata: IATA airport code (e.g. ``"SEA"``).
        direction: ``"departures"`` (default) or ``"arrivals"``.

    Returns ``[]`` when ``SKYLINK_RAPIDAPI_KEY`` is absent (NO network call), when
    ``direction`` is invalid, or when the upstream fails. Cache the result; do not
    poll per turn (free tier 1000 req/mo).
    """
    if direction not in _VALID_DIRECTIONS:
        logger.warning("skylink_board: invalid direction %r", direction)
        return []
    key = os.getenv(SKYLINK_KEY_ENV)
    if not key:
        logger.debug("%s not set; skipping SkyLink board", SKYLINK_KEY_ENV)
        return []
    payload = _get_json(
        f"{SKYLINK_BASE}/v3/schedules/{direction}",
        params={"iata": airport_iata},
        headers={"X-RapidAPI-Key": key, "X-RapidAPI-Host": SKYLINK_HOST},
        provider="SkyLink",
    )
    return _flight_list(payload)


def aviationstack_flights(
    dep_iata: Optional[str] = None,
    arr_iata: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """SeaTac board via AviationStack ``/v1/flights`` (published fallback).

    Pass ``dep_iata`` and/or ``arr_iata`` to filter the board. Returns ``[]`` when
    ``AVIATIONSTACK_KEY`` is absent (NO network call) or the upstream fails. Use
    as a fallback only (free tier ~100 req/mo).
    """
    key = os.getenv(AVIATIONSTACK_KEY_ENV)
    if not key:
        logger.debug("%s not set; skipping AviationStack", AVIATIONSTACK_KEY_ENV)
        return []
    params: Dict[str, Any] = {"access_key": key}
    if dep_iata:
        params["dep_iata"] = dep_iata
    if arr_iata:
        params["arr_iata"] = arr_iata
    payload = _get_json(
        f"{AVIATIONSTACK_BASE}/flights",
        params=params,
        provider="AviationStack",
    )
    return _flight_list(payload)


def flight_status(flight_number: str) -> Dict[str, Any]:
    """Single-flight status via SkyLink ``/v3/flight_status/{flight_number}``.

    Returns ``{}`` when ``SKYLINK_RAPIDAPI_KEY`` is absent (NO network call) or the
    upstream fails / returns no flight.
    """
    key = os.getenv(SKYLINK_KEY_ENV)
    if not key:
        logger.debug("%s not set; skipping SkyLink flight_status", SKYLINK_KEY_ENV)
        return {}
    payload = _get_json(
        f"{SKYLINK_BASE}/v3/flight_status/{flight_number}",
        headers={"X-RapidAPI-Key": key, "X-RapidAPI-Host": SKYLINK_HOST},
        provider="SkyLink",
    )
    if isinstance(payload, dict):
        # Some responses wrap the flight under a list; take the first.
        flights = _flight_list(payload)
        if flights:
            return flights[0]
        if any(k in payload for k in ("flight", "departure", "arrival", "status")):
            return _parse_flight(payload)
        return {}
    if isinstance(payload, list):
        flights = _flight_list(payload)
        return flights[0] if flights else {}
    return {}


def opensky_states(
    bbox: Tuple[float, float, float, float],
) -> List[Dict[str, Any]]:
    """STUB — live OpenSky positions are DEFERRED (returns ``[]``).

    Contract preserved for the connections planner: ``bbox`` is
    ``(lamin, lomin, lamax, lomax)``. Live fetching is intentionally NOT
    implemented at launch — see :data:`OPENSKY_DEFERRAL_NOTE`. OpenSky may block
    AWS IPs, so it must be routed through an off-AWS proxy
    (``OPENSKY_PROXY_URL``) with OAuth2 creds; that proxy is not wired yet.
    Always returns ``[]`` ("unknown"), never a fabricated position, and makes no
    network call.
    """
    if not opensky_enabled():
        logger.debug("opensky_states %s", OPENSKY_DEFERRAL_NOTE)
        return []
    # Reachable only if a future change wires the proxy; still a no-op stub now.
    logger.debug("opensky_states %s", OPENSKY_DEFERRAL_NOTE)
    return []
