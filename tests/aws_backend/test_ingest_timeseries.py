import os
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.aws_backend import ingest_timeseries
from src.aws_backend.ingest_timeseries import (
    ACOUSTIC,
    ACOUSTIC_REVIEWED,
    CURRENTS,
    NDBC_MET,
    SALMON,
    SHORELINE,
    STATION_UPTIME,
    WATER_LEVEL,
    ingest_acoustic_reviewed_outcomes,
    ingest_acoustic_history,
    ingest_ndbc_realtime,
    ingest_noaa_history,
    ingest_salmon,
    ingest_shoreline_snapshot,
    ingest_station_uptime,
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
    current_stations = ["PUG1515", "PUG1702"]

    def __init__(self, water, currents):
        self._water = water
        self._currents = currents

    def fetch_water_level_history(self, begin, end, station=None):
        return list(self._water)

    def fetch_currents_history(self, begin, end, station):
        return [{**record, "station": station} for record in self._currents]


class FakeSalmon:
    def __init__(self, by_year):
        self._by_year = by_year

    def fetch_run_index(self, year):
        return list(self._by_year.get(year, []))


class FakeHydrophones:
    def __init__(self, records):
        self._records = records

    def hydrophones(self):
        return list(self._records)


class FakeNdbc:
    def fetch_all_realtime(self):
        return {
            "46088": [
                {"t": "2026-01-01T00:00:00+00:00", "id": "46088:1", "station": "46088", "wind_speed_m_s": 3.2}
            ]
        }


class FakeShoreline:
    def fetch_features(self, result_record_count=100, bbox=None):
        return [
            {
                "t": "2026-01-01T00:00:00+00:00",
                "id": "shore-1",
                "source": "noaa_cusp",
                "source_id": "GC1",
                "geometry": {"paths": []},
            }
        ]


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


def test_ingest_acoustic_reviewed_outcomes_only_writes_reviewed_labels():
    store = MemoryTimeSeriesStore()
    records = [
        {"t": "2026-01-01T00:00:00+00:00", "id": "a1", "station": "Lime Kiln", "reviewed": True, "found": "yes", "confirmed": True},
        {"t": "2026-01-02T00:00:00+00:00", "id": "a2", "station": "Lime Kiln", "reviewed": True, "found": "no", "confirmed": False},
        {"t": "2026-01-03T00:00:00+00:00", "id": "a3", "station": "Lime Kiln", "reviewed": False, "found": None, "confirmed": False},
    ]
    summary = ingest_acoustic_reviewed_outcomes(adapter=FakeOrcaHello(records), store=store)
    assert summary["stream"] == ACOUSTIC_REVIEWED
    assert summary["records"] == 2
    got = store.get_series(ACOUSTIC_REVIEWED, "Lime Kiln", _WIDE_START, _WIDE_END)
    assert [r["outcome"] for r in got] == ["confirmed", "false_positive"]


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

    assert summary["records"] == 3
    assert set(summary["stations"]) == {"9449880", "PUG1515", "PUG1702"}
    assert store.get_series(WATER_LEVEL, "9449880", _WIDE_START, _WIDE_END)
    assert store.get_series(CURRENTS, "PUG1515", _WIDE_START, _WIDE_END)
    assert store.get_series(CURRENTS, "PUG1702", _WIDE_START, _WIDE_END)


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


def test_ingest_station_uptime_writes_up_and_down_records():
    store = MemoryTimeSeriesStore()
    adapter = FakeHydrophones(
        [
            {"id": "rpi_orcasound_lab", "name": "Orcasound Lab", "status": "online"},
            {"id": "rpi_port_townsend", "name": "Port Townsend", "status": "offline"},
        ]
    )

    summary = ingest_station_uptime(hydrophones_adapter=adapter, store=store)

    assert summary["stream"] == STATION_UPTIME
    assert summary["records"] == 2
    assert set(summary["stations"]) == {"rpi_orcasound_lab", "rpi_port_townsend"}

    lab = store.get_series(STATION_UPTIME, "rpi_orcasound_lab", _WIDE_START, _WIDE_END)
    assert len(lab) == 1
    assert lab[0]["up"] == 1
    assert lab[0]["status"] == "online"

    pt = store.get_series(STATION_UPTIME, "rpi_port_townsend", _WIDE_START, _WIDE_END)
    assert len(pt) == 1
    assert pt[0]["up"] == 0
    assert pt[0]["status"] == "offline"

    status = timeseries_status(store=store)
    assert STATION_UPTIME in status
    assert status[STATION_UPTIME]["record_count"] == 2


def test_ingest_ndbc_realtime_writes_met_stream():
    store = MemoryTimeSeriesStore()
    summary = ingest_ndbc_realtime(adapter=FakeNdbc(), store=store)
    assert summary["stream"] == NDBC_MET
    assert summary["records"] == 1
    assert store.get_series(NDBC_MET, "46088", _WIDE_START, _WIDE_END)[0]["wind_speed_m_s"] == 3.2


def test_ingest_shoreline_snapshot_writes_static_stream():
    store = MemoryTimeSeriesStore()
    summary = ingest_shoreline_snapshot(adapter=FakeShoreline(), store=store)
    assert summary["stream"] == SHORELINE
    assert summary["records"] == 1
    got = store.get_series(SHORELINE, "san_juan_pilot", _WIDE_START, _WIDE_END)
    assert got[0]["source_id"] == "GC1"


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


def test_ingest_spatial_grid_writes_cells():
    store = MemoryTimeSeriesStore()
    summary = ingest_timeseries.ingest_spatial_grid(step_degrees=0.2, store=store)
    assert summary["records"] > 0
    got = store.get_series(
        ingest_timeseries.SPATIAL_GRID,
        "san_juan_pilot",
        _WIDE_START,
        _WIDE_END,
    )
    assert "cell_id" in got[0]


def test_ingest_obis_validation_writes_records():
    class FakeObis:
        def fetch_validation_records(self, start_date=None, end_date=None):
            return [
                {
                    "t": "2024-07-15T00:00:00+00:00",
                    "id": "obis:1",
                    "latitude": 48.55,
                    "longitude": -123.10,
                    "quality_grade": "verified",
                    "license": "CC-BY-4.0",
                    "citation": "OBIS test",
                    "source_url": "https://obis.org/occurrence/1",
                    "source": "obis_verified",
                }
            ]

    store = MemoryTimeSeriesStore()
    summary = ingest_timeseries.ingest_obis_validation(adapter=FakeObis(), store=store)
    assert summary["records"] == 1
