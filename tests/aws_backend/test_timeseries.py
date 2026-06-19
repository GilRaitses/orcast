from datetime import datetime

from src.aws_backend.timeseries import (
    MemoryTimeSeriesStore,
    build_timeseries_store,
)
from src.aws_backend.config import Settings


def _records():
    return [
        {"t": "2026-01-02T00:00:00+00:00", "id": "a", "value": 2},
        {"t": "2026-01-01T00:00:00+00:00", "id": "b", "value": 1},
        {"t": "2026-01-03T00:00:00+00:00", "id": "c", "value": 3},
    ]


def test_put_then_get_in_range_sorted():
    store = MemoryTimeSeriesStore()
    written = store.put_series("noaa", "station-1", _records())
    assert written == 3

    result = store.get_series(
        "noaa",
        "station-1",
        datetime.fromisoformat("2026-01-01T00:00:00+00:00"),
        datetime.fromisoformat("2026-01-03T00:00:00+00:00"),
    )
    assert [r["id"] for r in result] == ["b", "a", "c"]


def test_out_of_range_excluded():
    store = MemoryTimeSeriesStore()
    store.put_series("noaa", "station-1", _records())

    result = store.get_series(
        "noaa",
        "station-1",
        datetime.fromisoformat("2026-01-02T00:00:00+00:00"),
        datetime.fromisoformat("2026-01-02T12:00:00+00:00"),
    )
    assert [r["id"] for r in result] == ["a"]


def test_dedupe_on_repeated_put():
    store = MemoryTimeSeriesStore()
    store.put_series("noaa", "station-1", _records())
    store.put_series("noaa", "station-1", _records())

    result = store.get_series(
        "noaa",
        "station-1",
        datetime.fromisoformat("2026-01-01T00:00:00+00:00"),
        datetime.fromisoformat("2026-01-31T00:00:00+00:00"),
    )
    assert len(result) == 3
    assert [r["id"] for r in result] == ["b", "a", "c"]


def test_list_stations():
    store = MemoryTimeSeriesStore()
    store.put_series("noaa", "Station One", [{"t": "2026-01-01T00:00:00+00:00", "id": "a"}])
    store.put_series("noaa", "Station Two", [{"t": "2026-01-01T00:00:00+00:00", "id": "b"}])
    store.put_series("orcahello", "Other", [{"t": "2026-01-01T00:00:00+00:00", "id": "c"}])

    assert store.list_stations("noaa") == ["station_one", "station_two"]
    assert store.list_stations("orcahello") == ["other"]


def test_station_name_sanitization():
    store = MemoryTimeSeriesStore()
    record = {"t": "2026-01-01T00:00:00+00:00", "id": "a"}
    store.put_series("noaa", "Lime Kiln #2 / Buoy!", [record])

    assert store.list_stations("noaa") == ["lime_kiln_2_buoy"]
    result = store.get_series(
        "noaa",
        "LIME KILN #2 / BUOY!",
        datetime.fromisoformat("2026-01-01T00:00:00+00:00"),
        datetime.fromisoformat("2026-01-02T00:00:00+00:00"),
    )
    assert [r["id"] for r in result] == ["a"]


def test_factory_selects_memory_backend():
    store = build_timeseries_store(Settings(storage_backend="memory"))
    assert isinstance(store, MemoryTimeSeriesStore)
