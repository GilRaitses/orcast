"""Tests for the flight board adapters (src/aws_backend/sources/flights.py).

No live calls: SkyLink / AviationStack reads are served from recorded, sanitized
fixtures under ``fixtures/flights/`` with ``requests.get`` monkeypatched out.
Covers:
- SkyLink + AviationStack board parsing (nested departure/arrival/airline/flight).
- API keys read from env; header / param wiring; keys never logged.
- Graceful degradation: absent key -> [] / {} with NO network call.
- The OpenSky stub: always [] (deferred), never a network call, deferral note.
"""

import json
from pathlib import Path

import pytest
import requests

from src.aws_backend.sources import flights

FIXTURES = Path(__file__).parent / "fixtures" / "flights"
_SKYLINK_KEY = "TEST-SKYLINK-KEY-9999"
_AVIATIONSTACK_KEY = "TEST-AVSTACK-KEY-8888"


def _load(name: str):
    return json.loads((FIXTURES / f"{name}.json").read_text())


class _FakeResp:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        if self._payload is _NO_JSON:
            raise ValueError("No JSON object could be decoded")
        return self._payload


_NO_JSON = object()


# --------------------------------------------------------------------------- #
# SkyLink board
# --------------------------------------------------------------------------- #

def test_skylink_board_parses_departures(monkeypatch):
    monkeypatch.setenv(flights.SKYLINK_KEY_ENV, _SKYLINK_KEY)
    capture = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        capture["url"] = url
        capture["params"] = params
        capture["headers"] = headers
        return _FakeResp(_load("skylink_departures_sea"))

    monkeypatch.setattr(flights.requests, "get", fake_get)

    board = flights.skylink_board("SEA", direction="departures")
    assert len(board) == 2
    first = board[0]
    assert first["flight_number"] == "AS412"
    assert first["airline_name"] == "Alaska Airlines"
    assert first["status"] == "scheduled"
    assert first["departure"]["iata"] == "SEA"
    assert first["departure"]["gate"] == "N12"
    assert first["departure"]["delay"] == 13
    assert first["arrival"]["iata"] == "SFO"
    # Boards are published (scheduled), not guaranteed.
    assert first["label"] == "published"
    # SkyLink endpoint + auth header wiring.
    assert capture["url"].endswith("/v3/schedules/departures")
    assert capture["params"] == {"iata": "SEA"}
    assert capture["headers"]["X-RapidAPI-Key"] == _SKYLINK_KEY
    assert capture["headers"]["X-RapidAPI-Host"] == flights.SKYLINK_HOST


def test_skylink_board_invalid_direction_returns_empty(monkeypatch):
    monkeypatch.setenv(flights.SKYLINK_KEY_ENV, _SKYLINK_KEY)

    def boom(*_a, **_k):
        raise AssertionError("invalid direction must not hit network")

    monkeypatch.setattr(flights.requests, "get", boom)
    assert flights.skylink_board("SEA", direction="sideways") == []


def test_skylink_board_absent_key_no_network(monkeypatch):
    monkeypatch.delenv(flights.SKYLINK_KEY_ENV, raising=False)

    def boom(*_a, **_k):
        raise AssertionError("no network call without a SkyLink key")

    monkeypatch.setattr(flights.requests, "get", boom)
    assert flights.skylink_enabled() is False
    assert flights.skylink_board("SEA") == []


def test_skylink_board_http_error_degrades(monkeypatch):
    monkeypatch.setenv(flights.SKYLINK_KEY_ENV, _SKYLINK_KEY)
    monkeypatch.setattr(
        flights.requests, "get", lambda *a, **k: _FakeResp([], status_code=503)
    )
    assert flights.skylink_board("SEA") == []


# --------------------------------------------------------------------------- #
# AviationStack board
# --------------------------------------------------------------------------- #

def test_aviationstack_parses_and_sends_access_key(monkeypatch):
    monkeypatch.setenv(flights.AVIATIONSTACK_KEY_ENV, _AVIATIONSTACK_KEY)
    capture = {}

    def fake_get(url, params=None, headers=None, timeout=None):
        capture["url"] = url
        capture["params"] = params
        return _FakeResp(_load("aviationstack_flights_sea"))

    monkeypatch.setattr(flights.requests, "get", fake_get)

    board = flights.aviationstack_flights(dep_iata="SEA")
    assert len(board) == 2
    first = board[0]
    assert first["flight_number"] == "AS1185"
    assert first["status"] == "scheduled"
    assert first["departure"]["iata"] == "SEA"
    assert first["arrival"]["iata"] == "LAX"
    assert first["label"] == "published"
    # access_key + dep_iata in the query string.
    assert capture["params"]["access_key"] == _AVIATIONSTACK_KEY
    assert capture["params"]["dep_iata"] == "SEA"


def test_aviationstack_absent_key_no_network(monkeypatch):
    monkeypatch.delenv(flights.AVIATIONSTACK_KEY_ENV, raising=False)

    def boom(*_a, **_k):
        raise AssertionError("no network call without an AviationStack key")

    monkeypatch.setattr(flights.requests, "get", boom)
    assert flights.aviationstack_enabled() is False
    assert flights.aviationstack_flights(dep_iata="SEA") == []


# --------------------------------------------------------------------------- #
# flight_status (SkyLink single flight)
# --------------------------------------------------------------------------- #

def test_flight_status_parsed(monkeypatch):
    monkeypatch.setenv(flights.SKYLINK_KEY_ENV, _SKYLINK_KEY)
    monkeypatch.setattr(
        flights.requests,
        "get",
        lambda *a, **k: _FakeResp(_load("skylink_flight_status")),
    )
    status = flights.flight_status("AS412")
    assert status["flight_number"] == "AS412"
    assert status["status"] == "active"
    assert status["departure"]["actual"] is not None


def test_flight_status_absent_key_no_network(monkeypatch):
    monkeypatch.delenv(flights.SKYLINK_KEY_ENV, raising=False)

    def boom(*_a, **_k):
        raise AssertionError("no network call without a SkyLink key")

    monkeypatch.setattr(flights.requests, "get", boom)
    assert flights.flight_status("AS412") == {}


# --------------------------------------------------------------------------- #
# OpenSky stub — DEFERRED
# --------------------------------------------------------------------------- #

def test_opensky_states_is_deferred_stub(monkeypatch):
    # Even with the flag set, the stub never fetches and returns [].
    monkeypatch.setenv(flights.OPENSKY_ENABLE_ENV, "1")
    monkeypatch.setenv(flights.OPENSKY_PROXY_ENV, "https://proxy.example/opensky")

    def boom(*_a, **_k):
        raise AssertionError("opensky_states is a deferred stub; no network allowed")

    monkeypatch.setattr(flights.requests, "get", boom)
    assert flights.opensky_enabled() is False
    assert flights.opensky_states((47.0, -123.0, 49.0, -122.0)) == []
    assert "off-AWS proxy" in flights.OPENSKY_DEFERRAL_NOTE
    assert "deferred" in flights.OPENSKY_DEFERRAL_NOTE.lower()


# --------------------------------------------------------------------------- #
# Keys never leak into logs
# --------------------------------------------------------------------------- #

def test_redact_strips_keys(monkeypatch):
    monkeypatch.setenv(flights.SKYLINK_KEY_ENV, _SKYLINK_KEY)
    monkeypatch.setenv(flights.AVIATIONSTACK_KEY_ENV, _AVIATIONSTACK_KEY)
    msg = (
        f"GET https://api.aviationstack.com/v1/flights?access_key={_AVIATIONSTACK_KEY} "
        f"with X-RapidAPI-Key {_SKYLINK_KEY} failed"
    )
    redacted = flights._redact(msg)
    assert _SKYLINK_KEY not in redacted
    assert _AVIATIONSTACK_KEY not in redacted
    assert "access_key=***" in redacted


def test_request_failure_does_not_log_key(monkeypatch, caplog):
    monkeypatch.setenv(flights.SKYLINK_KEY_ENV, _SKYLINK_KEY)

    def boom(*_a, **_k):
        raise requests.RequestException(
            f"failed url with X-RapidAPI-Key {_SKYLINK_KEY}"
        )

    monkeypatch.setattr(flights.requests, "get", boom)
    with caplog.at_level("WARNING"):
        flights.skylink_board("SEA")
    assert _SKYLINK_KEY not in caplog.text
