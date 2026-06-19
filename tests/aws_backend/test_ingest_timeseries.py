import os
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.aws_backend import ingest_timeseries
from src.aws_backend.ingest_timeseries import (
    ACOUSTIC,
    CURRENTS,
    SALMON,
    WATER_LEVEL,
    ingest_acoustic_history,
    ingest_noaa_history,
    ingest_salmon,
    timeseries_status,
)
from src.aws_backend.main import app
from src.aws_backend.timeseries import MemoryTimeSeriesStore

_WIDE_START = datetime(1970, 1, 1, tzinfo=timezone.utc)
_WIDE_END = datetime(2100, 1, 1, tzinfo=timezone.utc)


class FakeOrcaHello:
    def __init__(self, records):
        self._records = records
        self.calls = []

    def fetch_history(self, **kwargs):
        self.calls.append(kwargs)
        return list(self._records)


class FakeNoaa:
    station = "9449880"
    current_station = "PUG1515"

    def __init__(self, water, currents):
        self._water = water
        self._currents = currents

    def fetch_water_level_history(self, begin, end, station=None):
        return list(self._water)

    def fetch_currents_history(self, begin, end, station):
        return list(self._currents)


class FakeSalmon:
    def __init__(self, by_year):
        self._by_year = by_year

    def fetch_run_index(self, year):
        return list(self._by_year.get(year, []))


def _acoustic_records():
    return [
        {"t": "2026-01-01T00:00:00+00:00", "id": "a1", "station": "Lime Kiln"},
        {"t": "2026-01-02T00:00:00+00:00", "id": "a2", "station": "Lime Kiln"},
        {"t": "2026-01-03T00:00:00+00:00", "id": "b1", "station": "Orcasound Lab"},
    ]


def test_ingest_acoustic_groups_by_station():
    store = MemoryTimeSeriesStore()
    adapter = FakeOrcaHello(_acoustic_records())

    summary = ingest_acoustic_history(adapter=adapter, store=store)

    assert summary["stream"] == ACOUSTIC
    assert summary["records"] == 3
    assert set(summary["stations"]) == {"Lime Kiln", "Orcasound Lab"}

    lime = store.get_series(ACOUSTIC, "Lime Kiln", _WIDE_START, _WIDE_END)
    assert [r["id"] for r in lime] == ["a1", "a2"]
    lab = store.get_series(ACOUSTIC, "Orcasound Lab", _WIDE_START, _WIDE_END)
    assert [r["id"] for r in lab] == ["b1"]


def test_ingest_noaa_writes_water_level_and_currents():
    store = MemoryTimeSeriesStore()
    water = [{"t": "2026-01-01T00:00:00+00:00", "value": 1.0, "product": "water_level", "station": "9449880"}]
    currents = [{"t": "2026-01-01T00:00:00+00:00", "value": 0.5, "product": "currents", "station": "PUG1515"}]
    noaa = FakeNoaa(water, currents)

    summary = ingest_noaa_history(
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        datetime(2026, 1, 2, tzinfo=timezone.utc),
        noaa=noaa,
        store=store,
    )

    assert summary["records"] == 2
    assert set(summary["stations"]) == {"9449880", "PUG1515"}
    assert store.get_series(WATER_LEVEL, "9449880", _WIDE_START, _WIDE_END)
    assert store.get_series(CURRENTS, "PUG1515", _WIDE_START, _WIDE_END)


def test_ingest_salmon_writes_series():
    store = MemoryTimeSeriesStore()
    salmon = FakeSalmon(
        {
            2026: [
                {"t": "2026-07-20", "fraser_index": 1.0, "columbia_index": None, "run_index": 1.0, "source": "x"},
            ]
        }
    )

    summary = ingest_salmon([2026], salmon=salmon, store=store)

    assert summary["stream"] == SALMON
    assert summary["records"] == 1
    assert summary["stations"] == ["salish_sea"]
    # Salmon timestamps are date-only (naive), so query with a naive window.
    naive_start = datetime(1970, 1, 1)
    naive_end = datetime(2100, 1, 1)
    assert store.get_series(SALMON, "salish_sea", naive_start, naive_end)


def test_timeseries_status_reports_counts_and_bounds():
    store = MemoryTimeSeriesStore()
    ingest_acoustic_history(adapter=FakeOrcaHello(_acoustic_records()), store=store)
    ingest_salmon(
        [2026],
        salmon=FakeSalmon({2026: [{"t": "2026-07-20", "run_index": 1.0, "source": "x"}]}),
        store=store,
    )

    status = timeseries_status(store=store)

    acoustic = status[ACOUSTIC]
    assert acoustic["record_count"] == 3
    assert set(acoustic["stations"]) == {"lime_kiln", "orcasound_lab"}
    assert acoustic["first_t"] == "2026-01-01T00:00:00+00:00"
    assert acoustic["last_t"] == "2026-01-03T00:00:00+00:00"

    # Salmon stores naive date-only timestamps; status falls back gracefully.
    assert status[SALMON]["record_count"] == 1
    assert status[SALMON]["first_t"] == "2026-07-20"

    assert status[WATER_LEVEL]["record_count"] == 0
    assert status[WATER_LEVEL]["first_t"] is None


def test_data_status_endpoint_returns_200():
    client = TestClient(app)
    response = client.get("/api/data-status")
    assert response.status_code == 200
    body = response.json()
    assert ACOUSTIC in body
    assert WATER_LEVEL in body


def test_backfill_endpoint_requires_key_when_configured(monkeypatch):
    monkeypatch.setattr(ingest_timeseries, "backfill_all", lambda years_back=3: [{"stream": "fake", "stations": [], "records": 0}])

    with patch.dict(os.environ, {"ORCAST_API_KEY": "test-secret-key"}, clear=False):
        client = TestClient(app)

        denied = client.post("/api/timeseries/backfill")
        assert denied.status_code == 401

        allowed = client.post(
            "/api/timeseries/backfill",
            headers={"X-ORCAST-Key": "test-secret-key"},
        )
        assert allowed.status_code == 202
        assert allowed.json()["status"] == "accepted"


def test_refresh_endpoint_requires_key_when_configured(monkeypatch):
    monkeypatch.setattr(ingest_timeseries, "refresh_recent", lambda days=7: [{"stream": "fake", "stations": [], "records": 0}])

    with patch.dict(os.environ, {"ORCAST_API_KEY": "test-secret-key"}, clear=False):
        client = TestClient(app)

        denied = client.post("/api/timeseries/refresh")
        assert denied.status_code == 401

        allowed = client.post(
            "/api/timeseries/refresh",
            headers={"X-ORCAST-Key": "test-secret-key"},
        )
        assert allowed.status_code == 202
