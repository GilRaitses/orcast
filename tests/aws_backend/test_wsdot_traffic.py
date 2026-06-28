"""Tests for the WSDOT Traffic client (src/aws_backend/sources/wsdot_traffic.py).

No live calls: every HTTP read is served from recorded, sanitized fixtures under
``fixtures/wsdot_traffic/`` (captured from the live data.wsdot.wa.gov NW feed on
2026-06-27; the response bodies contain only public road data, never the access
code). Covers:

- WCF ``/Date(...)/`` epoch parsing (with/without offset, null, passthrough).
- travel_times() / traffic_flows() field parsing + the 0-5 congestion enum.
- corridor_route_ids() resolving the SeaTac<->Anacortes northbound I-5 chain by
  Name, EXCLUDING the HOV/express-lane variants, and surfacing only measured
  legs (the Arlington->Anacortes gap is never implied).
- append_history() writing + round-tripping a row into a tmp dir (timestamped,
  appendable, datetime-serializing).
- graceful behavior when WSDOT_ACCESS_CODE is unset (no request, empty results).
- the access code never leaking into a log string.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.aws_backend.sources import wsdot_traffic as wt


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "wsdot_traffic"


def _load(name):
    return json.loads((FIXTURE_DIR / name).read_text())


TRAVEL_TIMES_RAW = _load("travel_times.json")
TRAFFIC_FLOWS_RAW = _load("traffic_flows.json")


class _JsonResp:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


@pytest.fixture
def configured(monkeypatch):
    """Set a fake access code so the read helpers attempt a (mocked) request."""
    monkeypatch.setenv("WSDOT_ACCESS_CODE", "FAKE-TEST-CODE")
    return "FAKE-TEST-CODE"


def _mock_feed(monkeypatch):
    """Route GetTravelTimes -> travel-time fixture, GetTrafficFlows -> flow fixture."""
    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured["last_params"] = params
        if "TravelTimes" in url:
            return _JsonResp(TRAVEL_TIMES_RAW)
        if "TrafficFlow" in url:
            return _JsonResp(TRAFFIC_FLOWS_RAW)
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr(wt.requests, "get", fake_get)
    return captured


# --------------------------------------------------------------------------- #
# WCF date parsing
# --------------------------------------------------------------------------- #

def test_parse_wcf_date_with_offset():
    dt = wt.parse_wcf_date("/Date(1782608400000-0700)/")
    assert dt is not None
    assert dt.tzinfo is not None
    # The offset is display-only; the instant is the UTC epoch-millis.
    assert dt == datetime.fromtimestamp(1782608400000 / 1000.0, tz=timezone.utc)


def test_parse_wcf_date_without_offset():
    dt = wt.parse_wcf_date("/Date(1719500000000)/")
    assert dt == datetime.fromtimestamp(1719500000000 / 1000.0, tz=timezone.utc)


def test_parse_wcf_date_handles_null_and_junk():
    assert wt.parse_wcf_date(None) is None
    assert wt.parse_wcf_date("not a date") is None
    assert wt.parse_wcf_date(12345) is None


def test_parse_wcf_date_passthrough_datetime():
    naive = datetime(2026, 6, 27, 12, 0, 0)
    aware = wt.parse_wcf_date(naive)
    assert aware.tzinfo == timezone.utc


# --------------------------------------------------------------------------- #
# travel_times() parsing
# --------------------------------------------------------------------------- #

def test_travel_times_parses_fields(configured, monkeypatch):
    _mock_feed(monkeypatch)
    routes = wt.travel_times()
    assert routes, "expected parsed travel-time routes"
    seatac = next(r for r in routes if r["name"] == "SeaTac-Seattle")
    assert seatac["travel_time_id"] == 43
    assert seatac["current_time"] == 12
    assert seatac["average_time"] == 16
    assert seatac["distance"] == pytest.approx(13.03)
    assert isinstance(seatac["time_updated"], datetime)
    assert seatac["time_updated"].tzinfo is not None
    # RoadwayLocation normalized (note the live feed uses RoadName "005" / "N").
    assert seatac["start_point"]["milepost"] == pytest.approx(152.8)
    assert seatac["end_point"]["road_name"] == "005"


def test_travel_times_sends_pascalcase_accesscode(configured, monkeypatch):
    captured = _mock_feed(monkeypatch)
    wt.travel_times()
    params = captured["last_params"]
    # PascalCase AccessCode for the Traffic REST.svc endpoints (NOT apiaccesscode).
    assert "AccessCode" in params
    assert "apiaccesscode" not in params
    assert params["AccessCode"] == "FAKE-TEST-CODE"


# --------------------------------------------------------------------------- #
# traffic_flows() parsing + congestion enum
# --------------------------------------------------------------------------- #

def test_traffic_flows_parses_fields(configured, monkeypatch):
    _mock_feed(monkeypatch)
    flows = wt.traffic_flows()
    assert flows
    first = flows[0]
    assert first["flow_data_id"] is not None
    assert isinstance(first["time"], datetime)
    assert first["location"]["road_name"] == "005"
    assert first["reading_value"] in wt.FLOW_READING_LABELS
    assert first["reading_label"] == wt.FLOW_READING_LABELS[first["reading_value"]]


def test_flow_reading_enum_mapping():
    # 0=Unknown,1=WideOpen,2=Moderate,3=Heavy,4=StopAndGo,5=NoData (recon section 2).
    cases = {0: "Unknown", 1: "WideOpen", 2: "Moderate", 3: "Heavy", 4: "StopAndGo", 5: "NoData"}
    for value, label in cases.items():
        parsed = wt.parse_flow({"FlowDataID": 1, "FlowReadingValue": value})
        assert parsed["reading_label"] == label
    # Out-of-range / missing degrades to Unknown, never crashes.
    assert wt.parse_flow({"FlowReadingValue": 99})["reading_label"] == "Unknown"
    assert wt.parse_flow({})["reading_label"] == "Unknown"


# --------------------------------------------------------------------------- #
# Corridor resolution (the headline deliverable)
# --------------------------------------------------------------------------- #

EXPECTED_CORRIDOR = [
    ("SeaTac-Seattle", 43),
    ("Seattle-Lynnwood", 27),
    ("Seattle-Everett", 4),
    ("Everett-Marysville", 268),
    ("Everett-Arlington", 267),
]


def test_corridor_routes_resolve_by_name(configured, monkeypatch):
    _mock_feed(monkeypatch)
    routes = wt.corridor_routes()
    names = [r["name"] for r in routes]
    assert names == [n for n, _ in EXPECTED_CORRIDOR]


def test_corridor_route_ids_resolved(configured, monkeypatch):
    _mock_feed(monkeypatch)
    ids = wt.corridor_route_ids()
    assert ids == [i for _, i in EXPECTED_CORRIDOR]
    assert all(isinstance(i, int) for i in ids)


def test_corridor_excludes_hov_and_express_variants(configured, monkeypatch):
    _mock_feed(monkeypatch)
    routes = wt.corridor_routes()
    # The fixture contains "Seattle-Everett HOV" / "Everett-Seattle HOV"; the
    # mainline corridor must not pick the express-lane variants.
    for r in routes:
        assert "hov" not in r["name"].lower()
    assert wt._is_excluded_variant("Seattle-Everett HOV") is True
    assert wt._is_excluded_variant("Seattle-Everett EL") is True
    assert wt._is_excluded_variant("Seattle-Everett") is False


def test_corridor_does_not_imply_arlington_to_anacortes(configured, monkeypatch):
    """HONEST COVERAGE GAP: TravelTimes end ~Arlington (MP ~208). No corridor
    route may claim Mount Vernon / Burlington / Anacortes coverage."""
    _mock_feed(monkeypatch)
    routes = wt.corridor_routes()
    blob = json.dumps([r["raw"] for r in routes]).lower()
    for absent in ("mount vernon", "burlington", "anacortes", "sr 20", "sr20"):
        assert absent not in blob
    # Northernmost measured endpoint stays at/below Arlington (~MP 208).
    end_mps = [r["end_point"]["milepost"] for r in routes if r["end_point"]]
    assert max(end_mps) <= 210


def test_corridor_resolution_offline_via_passed_routes():
    """corridor_routes() resolves from already-parsed travel_times without a call."""
    parsed = [wt.parse_travel_time(r) for r in TRAVEL_TIMES_RAW]
    routes = wt.corridor_routes(parsed)
    assert [r["name"] for r in routes] == [n for n, _ in EXPECTED_CORRIDOR]


# --------------------------------------------------------------------------- #
# append_history()
# --------------------------------------------------------------------------- #

def test_append_history_writes_and_roundtrips(tmp_path):
    log = tmp_path / "corridor" / "seatac_anacortes.jsonl"
    record = {
        "travel_time_id": 43,
        "name": "SeaTac-Seattle",
        "current_time": 12,
        "average_time": 16,
        "time_updated": wt.parse_wcf_date("/Date(1782608400000-0700)/"),
    }
    wt.append_history(record, path=log)

    assert log.exists()
    lines = log.read_text().strip().splitlines()
    assert len(lines) == 1
    row = json.loads(lines[0])
    assert row["travel_time_id"] == 43
    assert row["name"] == "SeaTac-Seattle"
    # A UTC timestamp is added so rows are time-ordered for the W3 model.
    assert "logged_at" in row
    # datetime fields serialize (default=str), not crash.
    assert isinstance(row["time_updated"], str)


def test_append_history_appends_multiple_rows(tmp_path):
    log = tmp_path / "seatac_anacortes.jsonl"
    wt.append_history({"travel_time_id": 1}, path=log)
    wt.append_history({"travel_time_id": 2}, path=log)
    lines = log.read_text().strip().splitlines()
    assert len(lines) == 2
    assert [json.loads(l)["travel_time_id"] for l in lines] == [1, 2]


def test_append_history_preserves_supplied_logged_at(tmp_path):
    log = tmp_path / "seatac_anacortes.jsonl"
    wt.append_history({"travel_time_id": 1, "logged_at": "2026-06-27T00:00:00+00:00"}, path=log)
    row = json.loads(log.read_text().strip())
    assert row["logged_at"] == "2026-06-27T00:00:00+00:00"


def test_history_path_is_under_gitignored_external_dir():
    p = wt.history_path()
    assert "data/external/traffic_corridor" in p.as_posix()
    assert p.name == "seatac_anacortes.jsonl"


# --------------------------------------------------------------------------- #
# Graceful absence of the access code
# --------------------------------------------------------------------------- #

def test_unconfigured_returns_empty_without_request(monkeypatch):
    monkeypatch.delenv("WSDOT_ACCESS_CODE", raising=False)

    def boom(*_a, **_k):
        raise AssertionError("no request must be made when the code is absent")

    monkeypatch.setattr(wt.requests, "get", boom)
    assert wt.is_configured() is False
    assert wt.travel_times() == []
    assert wt.traffic_flows() == []
    assert wt.corridor_route_ids() == []


def test_request_failure_degrades_to_empty(configured, monkeypatch):
    import requests as _requests

    def boom(*_a, **_k):
        raise _requests.RequestException("connection refused")

    monkeypatch.setattr(wt.requests, "get", boom)
    assert wt.travel_times() == []
    assert wt.traffic_flows() == []


# --------------------------------------------------------------------------- #
# Access code never leaks
# --------------------------------------------------------------------------- #

def test_redact_strips_access_code():
    code = "SECRET-CODE-XYZ"
    msg = f"GET https://www.wsdot.wa.gov/Traffic/...?AccessCode={code} failed"
    redacted = wt._redact(msg, code)
    assert code not in redacted
    assert "AccessCode=***" in redacted
