"""Time-series ingest orchestration.

Pulls history from the source adapters (OrcaHello acoustic detections, NOAA
water level / currents, salmon run index) and persists it into the
:class:`~src.aws_backend.timeseries.TimeSeriesStore` keyed by stream + station.

Adapters and the store are injectable so tests can pass fakes; production code
relies on the module-level ``store`` and the default adapters.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .config import settings
from .sources.noaa import NoaaAdapter
from .sources.orcahello_history import OrcaHelloHistoryAdapter
from .sources.salmon import SalmonRunAdapter
from .timeseries import build_timeseries_store

# Module-level store; tests may override per-call via the ``store`` parameter.
store = build_timeseries_store(settings)

# Stream identifiers.
ACOUSTIC = "acoustic_detections"
WATER_LEVEL = "env_water_level"
CURRENTS = "env_currents"
SALMON = "salmon_run_index"

# Wide windows used when summarizing what has been stored. Some streams store
# tz-aware timestamps (acoustic, NOAA) while others store naive date-only
# timestamps (salmon), so the store cannot compare them against a single window;
# we try the aware window first and fall back to the naive one per station.
_WINDOW_START = datetime(1970, 1, 1, tzinfo=timezone.utc)
_WINDOW_END = datetime(2100, 1, 1, tzinfo=timezone.utc)
_WINDOW_START_NAIVE = datetime(1970, 1, 1)
_WINDOW_END_NAIVE = datetime(2100, 1, 1)


def _resolve_store(store: Optional[Any]):
    return store if store is not None else globals()["store"]


def _parse_t(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        text = value.replace("Z", "+00:00") if isinstance(value, str) else value
        dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def ingest_acoustic_history(
    adapter: Optional[Any] = None,
    in_region_only: bool = True,
    max_pages: int = 200,
    store: Optional[Any] = None,
) -> Dict[str, Any]:
    """Fetch the OrcaHello archive and persist it grouped by station."""
    ts = _resolve_store(store)
    adapter = adapter or OrcaHelloHistoryAdapter()

    records = adapter.fetch_history(max_pages=max_pages, in_region_only=in_region_only)
    return _put_grouped_by_station(ts, ACOUSTIC, records)


def ingest_noaa_history(
    begin: datetime,
    end: datetime,
    noaa: Optional[Any] = None,
    store: Optional[Any] = None,
) -> Dict[str, Any]:
    """Persist NOAA water-level and currents history for ``[begin, end]``."""
    ts = _resolve_store(store)
    noaa = noaa or NoaaAdapter()

    stations: List[str] = []
    total = 0

    water = noaa.fetch_water_level_history(begin, end, station=noaa.station)
    if water:
        total += ts.put_series(WATER_LEVEL, noaa.station, water)
        stations.append(noaa.station)

    currents = noaa.fetch_currents_history(begin, end, noaa.current_station)
    if currents:
        total += ts.put_series(CURRENTS, noaa.current_station, currents)
        stations.append(noaa.current_station)

    return {"stream": "noaa", "stations": stations, "records": total}


def ingest_salmon(
    years: List[int],
    salmon: Optional[Any] = None,
    store: Optional[Any] = None,
) -> Dict[str, Any]:
    """Persist the salmon run index for each requested year."""
    ts = _resolve_store(store)
    salmon = salmon or SalmonRunAdapter()

    total = 0
    for year in years:
        records = salmon.fetch_run_index(year)
        total += ts.put_series(SALMON, "salish_sea", records)

    stations = ["salish_sea"] if total else []
    return {"stream": SALMON, "stations": stations, "records": total}


def backfill_all(
    years_back: int = 3,
    acoustic: Optional[Any] = None,
    noaa: Optional[Any] = None,
    salmon: Optional[Any] = None,
    store: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Backfill every stream: all acoustic history plus the last N years."""
    now = datetime.now(timezone.utc)
    begin = now - timedelta(days=365 * years_back)
    current_year = now.year
    years = list(range(current_year - years_back + 1, current_year + 1))

    return [
        ingest_acoustic_history(adapter=acoustic, store=store),
        ingest_noaa_history(begin, now, noaa=noaa, store=store),
        ingest_salmon(years, salmon=salmon, store=store),
    ]


def refresh_recent(
    days: int = 7,
    acoustic: Optional[Any] = None,
    noaa: Optional[Any] = None,
    salmon: Optional[Any] = None,
    store: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Refresh the trailing window: recent acoustic, NOAA, current-year salmon."""
    ts = _resolve_store(store)
    now = datetime.now(timezone.utc)
    begin = now - timedelta(days=days)

    acoustic_summary = _ingest_acoustic_recent(ts, days=days, adapter=acoustic)
    noaa_summary = ingest_noaa_history(begin, now, noaa=noaa, store=ts)
    salmon_summary = ingest_salmon([now.year], salmon=salmon, store=ts)

    return [acoustic_summary, noaa_summary, salmon_summary]


def timeseries_status(store: Optional[Any] = None) -> Dict[str, Any]:
    """Summarize each stream: stations, record count, and first/last timestamp."""
    ts = _resolve_store(store)
    status: Dict[str, Any] = {}
    for stream in (ACOUSTIC, WATER_LEVEL, CURRENTS, SALMON):
        status[stream] = _stream_status(ts, stream)
    return status


# -- internals ----------------------------------------------------------------
def _put_grouped_by_station(ts: Any, stream: str, records: List[dict]) -> Dict[str, Any]:
    groups: Dict[str, List[dict]] = {}
    for record in records:
        station = record.get("station") or "unknown"
        groups.setdefault(station, []).append(record)

    written_stations: List[str] = []
    total = 0
    for station, recs in groups.items():
        count = ts.put_series(stream, station, recs)
        if count:
            written_stations.append(station)
            total += count

    return {"stream": stream, "stations": written_stations, "records": total}


def _ingest_acoustic_recent(
    ts: Any, days: int, adapter: Optional[Any]
) -> Dict[str, Any]:
    adapter = adapter or OrcaHelloHistoryAdapter()
    records = adapter.fetch_history(timeframe="all")
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    recent = [r for r in records if _within_cutoff(r, cutoff)]
    return _put_grouped_by_station(ts, ACOUSTIC, recent)


def _within_cutoff(record: dict, cutoff: datetime) -> bool:
    raw = record.get("t")
    if not raw:
        return False
    try:
        return _parse_t(raw) >= cutoff
    except (ValueError, TypeError):
        return False


def _get_all(ts: Any, stream: str, station: str) -> List[dict]:
    """Read a station's full series, tolerating naive or tz-aware timestamps."""
    try:
        return ts.get_series(stream, station, _WINDOW_START, _WINDOW_END)
    except TypeError:
        return ts.get_series(stream, station, _WINDOW_START_NAIVE, _WINDOW_END_NAIVE)


def _stream_status(ts: Any, stream: str) -> Dict[str, Any]:
    try:
        stations = ts.list_stations(stream)
        records: List[dict] = []
        for station in stations:
            records.extend(_get_all(ts, stream, station))

        first_t = None
        last_t = None
        if records:
            ordered = sorted(records, key=lambda r: _parse_t(r["t"]))
            first_t = ordered[0]["t"]
            last_t = ordered[-1]["t"]

        return {
            "stations": stations,
            "record_count": len(records),
            "first_t": first_t,
            "last_t": last_t,
        }
    except Exception as exc:  # noqa: BLE001 - status must stay resilient per-stream.
        return {
            "stations": [],
            "record_count": 0,
            "first_t": None,
            "last_t": None,
            "error": str(exc),
        }
