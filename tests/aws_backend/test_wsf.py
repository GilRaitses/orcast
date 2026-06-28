"""Tests for the WSF (Washington State Ferries) REST client.

All tests run against recorded / hand-authored fixtures with ``requests.get``
monkeypatched out — there are NO live network calls in this path. The single
optional live smoke that recorded ``fixtures/wsf/sailing_space.json`` is run
manually and is NOT part of this suite.

Covers:
- WCF/ASP.NET ``/Date(...)/`` epoch+offset parsing.
- Field mapping for every public function.
- ``terminalsailingspace`` nested DepartingSpaces[] -> SpaceForArrivalTerminals[]
  with DriveUp/Reservable counts AND the Display* suppression flags
  (suppressed -> None, never a misleading 0).
- The lowercase ``apiaccesscode`` query parameter (WSF, not ``AccessCode``).
- Graceful degradation when WSDOT_ACCESS_CODE is absent / upstream fails.
- The access code never leaking into logs.
"""

from __future__ import annotations

import datetime
import json
from datetime import timedelta
from pathlib import Path

import pytest
import requests

from src.aws_backend.sources import wsf

FIXTURES = Path(__file__).parent / "fixtures" / "wsf"
_CODE = "TEST-ACCESS-CODE-1234"


def _load(name: str):
    return json.loads((FIXTURES / f"{name}.json").read_text())


class _FakeResp:
    def __init__(self, payload, status_code=200, content_type="application/json"):
        self._payload = payload
        self.status_code = status_code
        self.headers = {"Content-Type": content_type}
        self.url = "https://www.wsdot.wa.gov/ferries/api/..."

    def json(self):
        if self._payload is _NO_JSON:
            raise ValueError("No JSON object could be decoded")
        return self._payload


_NO_JSON = object()


def _router(capture):
    """Return a fake ``requests.get`` that serves fixtures by URL and records the
    last url + params for assertions."""

    def fake_get(url, params=None, timeout=None):
        capture["url"] = url
        capture["params"] = params
        capture["timeout"] = timeout
        if "/vessels/rest/vessellocations" in url:
            data = _load("vessel_locations")
            # /{VesselID} variant -> single object
            tail = url.rsplit("/", 1)[-1]
            if tail.isdigit():
                want = int(tail)
                data = next((v for v in data if v["VesselID"] == want), {})
            return _FakeResp(data)
        if "/schedule/rest/schedule/" in url:
            return _FakeResp(_load("schedule"))
        if "/terminalsailingspace" in url:
            return _FakeResp(_load("sailing_space"))
        if "/terminalwaittimes" in url:
            return _FakeResp(_load("wait_times"))
        if "/schedule/rest/routes/" in url:
            return _FakeResp(_load("routes"))
        if "/schedule/rest/terminals/" in url:
            return _FakeResp(_load("terminals"))
        raise AssertionError(f"unexpected url {url}")

    return fake_get


@pytest.fixture
def enabled(monkeypatch):
    """Access code present + requests.get serving fixtures."""
    monkeypatch.setenv("WSDOT_ACCESS_CODE", _CODE)
    capture: dict = {}
    monkeypatch.setattr(wsf.requests, "get", _router(capture))
    return capture


# --------------------------------------------------------------------------- #
# WCF date parsing
# --------------------------------------------------------------------------- #

def test_parse_wcf_date_epoch_and_offset():
    dt = wsf.parse_wcf_date("/Date(1782612300000-0700)/")
    assert dt is not None
    # Instant is the UTC epoch carried by the millis.
    assert round(dt.timestamp() * 1000) == 1782612300000
    # Trailing offset becomes the datetime's display tz.
    assert dt.utcoffset() == timedelta(hours=-7)


def test_parse_wcf_date_no_offset_is_utc():
    dt = wsf.parse_wcf_date("/Date(1782612300000)/")
    assert dt is not None
    assert dt.utcoffset() == timedelta(0)


def test_parse_wcf_date_none_and_garbage():
    assert wsf.parse_wcf_date(None) is None
    assert wsf.parse_wcf_date("not a date") is None
    assert wsf.parse_wcf_date(12345) is None


# --------------------------------------------------------------------------- #
# vessel_locations
# --------------------------------------------------------------------------- #

def test_vessel_locations_parsed(enabled):
    out = wsf.vessel_locations()
    assert len(out) == 2
    chelan = out[0]
    assert chelan["vessel_id"] == 2
    assert chelan["vessel_name"] == "Chelan"
    assert chelan["latitude"] == 48.508 and chelan["longitude"] == -122.679
    assert chelan["speed"] == 14.6 and chelan["heading"] == 271
    assert chelan["in_service"] is True and chelan["at_dock"] is False
    # ETA basis is the honesty source for the ETA.
    assert "Estimated" in chelan["eta_basis"]
    # WCF dates become ISO strings.
    assert chelan["eta"].startswith("20")
    # A docked vessel with null Eta degrades to None, not a crash.
    yakima = out[1]
    assert yakima["at_dock"] is True
    assert yakima["eta"] is None and yakima["eta_basis"] is None
    assert yakima["left_dock"] is None


def test_vessel_locations_single_id_path(enabled):
    out = wsf.vessel_locations(vessel_id=38)
    assert len(out) == 1 and out[0]["vessel_id"] == 38
    assert enabled["url"].endswith("/vessellocations/38")


# --------------------------------------------------------------------------- #
# sailing_space — the trip-critical nested parse
# --------------------------------------------------------------------------- #

def test_sailing_space_drive_up_and_reservable(enabled):
    out = wsf.sailing_space()
    ana = next(t for t in out if t["terminal_id"] == 1)
    assert ana["terminal_abbrev"] == "ANA"
    # Friday Harbor departure carries both counts displayed.
    fh = next(
        a
        for d in ana["departing_spaces"]
        for a in d["space_for_arrival_terminals"]
        if a["terminal_name"] == "Anacortes -> Friday Harbor"
    )
    assert fh["drive_up_space_count"] == 55
    assert fh["reservable_space_count"] == 32
    assert fh["display_drive_up_space"] is True
    # Departure WCF date parsed to ISO on the parent departing space.
    dep = ana["departing_spaces"][0]
    assert dep["departure"].startswith("20")
    assert dep["vessel_name"] == "Chelan"


def test_sailing_space_suppresses_when_display_false(enabled):
    out = wsf.sailing_space()
    bain = next(t for t in out if t["terminal_id"] == 3)
    seattle = bain["departing_spaces"][0]["space_for_arrival_terminals"][0]
    # DisplayReservableSpace is False -> suppress the count (do not show 0/None as real)
    assert seattle["display_reservable_space"] is False
    assert seattle["reservable_space_count"] is None
    # DriveUp is displayed and meaningful.
    assert seattle["display_drive_up_space"] is True
    assert seattle["drive_up_space_count"] == 84


def test_sailing_space_driveup_suppressed_not_zero(monkeypatch):
    """A full lane with DisplayDriveUpSpace=False must suppress to None, never 0."""
    monkeypatch.setenv("WSDOT_ACCESS_CODE", _CODE)
    suppressed = [
        {
            "TerminalID": 1,
            "TerminalName": "Anacortes",
            "DepartingSpaces": [
                {
                    "Departure": "/Date(1782612300000-0700)/",
                    "IsCancelled": False,
                    "VesselID": 2,
                    "VesselName": "Chelan",
                    "MaxSpaceCount": 120,
                    "SpaceForArrivalTerminals": [
                        {
                            "TerminalID": 10,
                            "TerminalName": "Friday Harbor",
                            "DisplayDriveUpSpace": False,
                            "DriveUpSpaceCount": 0,
                            "DisplayReservableSpace": False,
                            "ReservableSpaceCount": 0,
                        }
                    ],
                }
            ],
        }
    ]
    monkeypatch.setattr(wsf, "_get", lambda path: suppressed)
    arr = wsf.sailing_space()[0]["departing_spaces"][0]["space_for_arrival_terminals"][0]
    assert arr["drive_up_space_count"] is None
    assert arr["reservable_space_count"] is None
    # Raw values are preserved for callers that need them.
    assert arr["drive_up_space_count_raw"] == 0
    assert arr["reservable_space_count_raw"] == 0


def test_sailing_space_single_terminal_path(enabled):
    wsf.sailing_space(terminal_id=1)
    assert enabled["url"].endswith("/terminalsailingspace/1")


# --------------------------------------------------------------------------- #
# schedule / wait_times / routes / terminals
# --------------------------------------------------------------------------- #

def test_schedule_parsed(enabled):
    out = wsf.schedule(9, datetime.date(2026, 6, 27))
    assert out["schedule_id"] == 4321
    combo = out["terminal_combos"][0]
    assert combo["departing_terminal_id"] == 1
    assert combo["arriving_terminal_name"] == "Friday Harbor"
    first = combo["times"][0]
    assert first["departing_time"].startswith("20")
    assert first["annotation_indexes"] == [0]
    # AnnotationIndexes resolve against Annotations.
    assert combo["annotations"][first["annotation_indexes"][0]].startswith("Reservations")
    # A null ArrivingTime degrades to None.
    assert combo["times"][1]["arriving_time"] is None
    # TripDate path segment is YYYY-MM-DD.
    assert "/schedule/rest/schedule/2026-06-27/9" in enabled["url"]


def test_wait_times_freetext_preserved(enabled):
    out = wsf.wait_times()
    ana = next(t for t in out if t["terminal_id"] == 1)
    note = ana["wait_times"][0]["wait_time_notes"]
    assert isinstance(note, str) and "60-90 minutes" in note
    assert ana["wait_times"][0]["wait_time_last_updated"].startswith("20")


def test_routes_and_terminals_parsed(enabled):
    routes = wsf.routes(datetime.date(2026, 6, 27))
    assert any(r["route_id"] == 9 and r["route_abbrev"] == "ana-sj" for r in routes)
    terminals = wsf.terminals(datetime.date(2026, 6, 27))
    assert any(t["terminal_id"] == 1 and t["description"] == "Anacortes" for t in terminals)


# --------------------------------------------------------------------------- #
# Lowercase apiaccesscode param (the #1 WSF integration bug)
# --------------------------------------------------------------------------- #

def test_uses_lowercase_apiaccesscode(enabled):
    wsf.vessel_locations()
    params = enabled["params"]
    assert "apiaccesscode" in params
    assert "AccessCode" not in params  # that is the WSDOT Traffic casing
    assert params["apiaccesscode"] == _CODE


# --------------------------------------------------------------------------- #
# Graceful degradation
# --------------------------------------------------------------------------- #

def test_absent_code_returns_empty_without_network(monkeypatch):
    monkeypatch.delenv("WSDOT_ACCESS_CODE", raising=False)

    def boom(*_a, **_k):
        raise AssertionError("no network call may happen without an access code")

    monkeypatch.setattr(wsf.requests, "get", boom)
    assert wsf.wsf_enabled() is False
    assert wsf.vessel_locations() == []
    assert wsf.sailing_space() == []
    assert wsf.wait_times() == []
    assert wsf.routes(datetime.date(2026, 6, 27)) == []
    assert wsf.terminals(datetime.date(2026, 6, 27)) == []
    assert wsf.schedule(9, datetime.date(2026, 6, 27)) == {}


def test_http_error_degrades(monkeypatch):
    monkeypatch.setenv("WSDOT_ACCESS_CODE", _CODE)
    monkeypatch.setattr(wsf.requests, "get", lambda *a, **k: _FakeResp([], status_code=503))
    assert wsf.vessel_locations() == []
    assert wsf.schedule(9, datetime.date(2026, 6, 27)) == {}


def test_request_exception_degrades(monkeypatch):
    monkeypatch.setenv("WSDOT_ACCESS_CODE", _CODE)

    def boom(*_a, **_k):
        raise requests.RequestException("connection refused")

    monkeypatch.setattr(wsf.requests, "get", boom)
    assert wsf.sailing_space() == []


def test_non_json_degrades(monkeypatch):
    monkeypatch.setenv("WSDOT_ACCESS_CODE", _CODE)
    monkeypatch.setattr(wsf.requests, "get", lambda *a, **k: _FakeResp(_NO_JSON))
    assert wsf.wait_times() == []


# --------------------------------------------------------------------------- #
# The access code never leaks into logs
# --------------------------------------------------------------------------- #

def test_redact_strips_code(monkeypatch):
    monkeypatch.setenv("WSDOT_ACCESS_CODE", "LEAKYCODE999")
    msg = "Max retries: url=...vessellocations?apiaccesscode=LEAKYCODE999"
    redacted = wsf._redact(msg)
    assert "LEAKYCODE999" not in redacted
    assert "apiaccesscode=***" in redacted


def test_request_failure_does_not_log_code(monkeypatch, caplog):
    monkeypatch.setenv("WSDOT_ACCESS_CODE", "LEAKYCODE999")

    def boom(*_a, **_k):
        raise requests.RequestException(
            "url=https://www.wsdot.wa.gov/ferries/api/vessels/rest/vessellocations?apiaccesscode=LEAKYCODE999"
        )

    monkeypatch.setattr(wsf.requests, "get", boom)
    with caplog.at_level("WARNING"):
        wsf.vessel_locations()
    assert "LEAKYCODE999" not in caplog.text
