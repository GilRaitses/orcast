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
from .sources.ndbc import NdbcAdapter
from .sources.obis import LiveObisAdapter
from .sources.inaturalist import INaturalistAdapter
from .sources.orcahello_history import OrcaHelloHistoryAdapter
from .sources.orcasound import OrcasoundHydrophoneAdapter
from .sources.salmon import SalmonRunAdapter
from .sources.shoreline import ShorelineAdapter
from .spatial_enrichment import (
    DEFAULT_GRID_STATION,
    SPATIAL_GRID_STREAM,
    build_grid_cells,
)
from .timeseries import build_timeseries_store

# Module-level store; tests may override per-call via the ``store`` parameter.
store = build_timeseries_store(settings)

# Stream identifiers.
ACOUSTIC = "acoustic_detections"
ACOUSTIC_REVIEWED = "orcahello_reviewed_detector_outcomes"
WATER_LEVEL = "env_water_level"
CURRENTS = "env_currents"
SALMON = "salmon_run_index"
STATION_UPTIME = "station_uptime"
NDBC_MET = "noaa_ndbc_stdmet"
SHORELINE = "shoreline_distance"
SPATIAL_GRID = SPATIAL_GRID_STREAM
OBIS_VERIFIED = "obis_verified"
INATURALIST_VERIFIED = "inaturalist_verified"
AIS_VESSEL = "ais_vessel_traffic_erddap"
HABITAT_BC = "habitat_bc_shorezone"
PROTECTED_US = "protected_areas_us"
PROTECTED_CA = "protected_areas_ca"
FERRY_WA = "ferry_effort_wa"
FERRY_BC = "ferry_effort_bc"

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


def ingest_acoustic_reviewed_outcomes(
    adapter: Optional[Any] = None,
    in_region_only: bool = True,
    max_pages: int = 50,
    store: Optional[Any] = None,
) -> Dict[str, Any]:
    """Fetch reviewed OrcaHello labels for Level 0 detector QC."""
    ts = _resolve_store(store)
    adapter = adapter or OrcaHelloHistoryAdapter()
    if hasattr(adapter, "fetch_reviewed_outcomes"):
        records = adapter.fetch_reviewed_outcomes(
            max_pages=max_pages,
            in_region_only=in_region_only,
        )
    else:
        records = adapter.fetch_history(
            max_pages=max_pages,
            in_region_only=in_region_only,
            confirmed_only=False,
        )
        reviewed = []
        for record in records:
            if record.get("reviewed") is True:
                found = str(record.get("found") or "").lower()
                outcome = "confirmed" if record.get("confirmed") else (
                    "unknown" if "know" in found or "unknown" in found else "false_positive"
                )
                reviewed.append({**record, "outcome": outcome})
        records = reviewed
    return _put_grouped_by_station(ts, ACOUSTIC_REVIEWED, records)


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

    current_stations = list(getattr(noaa, "current_stations", [noaa.current_station]))
    for current_station in current_stations:
        currents = noaa.fetch_currents_history(begin, end, current_station)
        if currents:
            total += ts.put_series(CURRENTS, current_station, currents)
            stations.append(current_station)

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


def ingest_station_uptime(
    hydrophones_adapter: Optional[Any] = None,
    store: Optional[Any] = None,
) -> Dict[str, Any]:
    """Poll the hydrophone roster and append an uptime sample per station.

    Each call records a single point-in-time observation per in-region station
    so the ``STATION_UPTIME`` stream accumulates an availability time series.
    """
    ts = _resolve_store(store)
    adapter = hydrophones_adapter or OrcasoundHydrophoneAdapter()

    now_iso = datetime.now(timezone.utc).isoformat()
    stations: List[str] = []
    total = 0
    for hydrophone in adapter.hydrophones():
        station_id = hydrophone.get("id") or hydrophone.get("name") or "unknown"
        status = hydrophone.get("status") or "offline"
        record = {
            "t": now_iso,
            "id": station_id,
            "station": hydrophone.get("name"),
            "status": status,
            "up": 1 if status == "online" else 0,
        }
        count = ts.put_series(STATION_UPTIME, str(station_id), [record])
        if count:
            stations.append(str(station_id))
            total += count

    return {"stream": STATION_UPTIME, "stations": stations, "records": total}


def ingest_ndbc_realtime(
    adapter: Optional[Any] = None,
    store: Optional[Any] = None,
) -> Dict[str, Any]:
    """Persist NOAA NDBC realtime stdmet rows for detectability/noise covariates."""
    ts = _resolve_store(store)
    adapter = adapter or NdbcAdapter()
    total = 0
    stations: List[str] = []
    for station, records in adapter.fetch_all_realtime().items():
        if records:
            total += ts.put_series(NDBC_MET, station, records)
            stations.append(station)
    return {"stream": NDBC_MET, "stations": stations, "records": total}


def ingest_shoreline_snapshot(
    adapter: Optional[Any] = None,
    store: Optional[Any] = None,
) -> Dict[str, Any]:
    """Persist a bounded NOAA CUSP shoreline metadata snapshot."""
    ts = _resolve_store(store)
    adapter = adapter or ShorelineAdapter()
    # San Juan pilot bounding box: xmin, ymin, xmax, ymax.
    records = adapter.fetch_features(result_record_count=500, bbox=(-123.4, 48.3, -122.7, 49.1))
    if not records:
        records = adapter.fetch_features(result_record_count=100, bbox=None)
    count = ts.put_series(SHORELINE, "san_juan_pilot", records) if records else 0
    return {"stream": SHORELINE, "stations": ["san_juan_pilot"] if count else [], "records": count}


def ingest_spatial_grid(
    step_degrees: float = 0.05,
    store: Optional[Any] = None,
) -> Dict[str, Any]:
    """Persist per-cell bathymetry/shoreline covariates for the pilot grid."""
    ts = _resolve_store(store)
    records = build_grid_cells(step_degrees=step_degrees)
    count = ts.put_series(SPATIAL_GRID, DEFAULT_GRID_STATION, records) if records else 0
    return {
        "stream": SPATIAL_GRID,
        "stations": [DEFAULT_GRID_STATION] if count else [],
        "records": count,
    }


def ingest_obis_validation(
    adapter: Optional[Any] = None,
    start_date: str = "2020-01-01",
    end_date: str = "2025-12-31",
    store: Optional[Any] = None,
) -> Dict[str, Any]:
    """Persist bounded OBIS validation records with license/citation metadata."""
    ts = _resolve_store(store)
    adapter = adapter or LiveObisAdapter(size=200)
    records = adapter.fetch_validation_records(start_date=start_date, end_date=end_date)
    count = ts.put_series(OBIS_VERIFIED, "salish_sea", records) if records else 0
    return {"stream": OBIS_VERIFIED, "stations": ["salish_sea"] if count else [], "records": count}


def ingest_inaturalist_validation(
    adapter: Optional[Any] = None,
    store: Optional[Any] = None,
) -> Dict[str, Any]:
    """Persist bounded iNaturalist validation records with license/citation metadata."""
    ts = _resolve_store(store)
    adapter = adapter or INaturalistAdapter(days_back=365, per_page=100)
    records = adapter.fetch_validation_records()
    count = ts.put_series(INATURALIST_VERIFIED, "salish_sea", records) if records else 0
    return {
        "stream": INATURALIST_VERIFIED,
        "stations": ["salish_sea"] if count else [],
        "records": count,
    }


def ingest_p1_sources(
    ais: Optional[Any] = None,
    habitat: Optional[Any] = None,
    ferries: Optional[Any] = None,
    protected: Optional[Any] = None,
    store: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Ingest bounded P1 spatial/prey/effort sources."""
    from .sources.ais import AisTrafficAdapter
    from .sources.ferries import FerryEffortAdapter
    from .sources.habitat import HabitatAdapter
    from .sources.protected_areas import ProtectedAreasAdapter

    ts = _resolve_store(store)
    ais = ais or AisTrafficAdapter()
    habitat = habitat or HabitatAdapter()
    ferries = ferries or FerryEffortAdapter()
    protected = protected or ProtectedAreasAdapter()

    summaries = []
    ais_records = ais.fetch_aggregated_bins()
    summaries.append(
        {
            "stream": AIS_VESSEL,
            "stations": ["salish_sea"] if ais_records else [],
            "records": ts.put_series(AIS_VESSEL, "salish_sea", ais_records) if ais_records else 0,
        }
    )

    habitat_records = habitat.fetch_features(result_record_count=100)
    summaries.append(
        {
            "stream": HABITAT_BC,
            "stations": ["salish_sea"] if habitat_records else [],
            "records": ts.put_series(HABITAT_BC, "salish_sea", habitat_records) if habitat_records else 0,
        }
    )

    ferry_wa = ferries.fetch_wa_routes()
    summaries.append(
        {
            "stream": FERRY_WA,
            "stations": ["washington"] if ferry_wa else [],
            "records": ts.put_series(FERRY_WA, "washington", ferry_wa) if ferry_wa else 0,
        }
    )
    ferry_bc = ferries.fetch_bc_routes()
    summaries.append(
        {
            "stream": FERRY_BC,
            "stations": ["british_columbia"] if ferry_bc else [],
            "records": ts.put_series(FERRY_BC, "british_columbia", ferry_bc) if ferry_bc else 0,
        }
    )

    protected_us = protected.fetch_us_mpa(result_record_count=100)
    summaries.append(
        {
            "stream": PROTECTED_US,
            "stations": ["salish_sea"] if protected_us else [],
            "records": ts.put_series(PROTECTED_US, "salish_sea", protected_us) if protected_us else 0,
        }
    )
    protected_ca = protected.fetch_ca_protected()
    summaries.append(
        {
            "stream": PROTECTED_CA,
            "stations": ["canada"] if protected_ca else [],
            "records": ts.put_series(PROTECTED_CA, "canada", protected_ca) if protected_ca else 0,
        }
    )
    return summaries


def backfill_all(
    years_back: int = 3,
    acoustic: Optional[Any] = None,
    noaa: Optional[Any] = None,
    salmon: Optional[Any] = None,
    hydrophones: Optional[Any] = None,
    ndbc: Optional[Any] = None,
    shoreline: Optional[Any] = None,
    store: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Backfill every stream: all acoustic history plus the last N years."""
    now = datetime.now(timezone.utc)
    begin = now - timedelta(days=365 * years_back)
    current_year = now.year
    years = list(range(current_year - years_back + 1, current_year + 1))

    return [
        ingest_acoustic_history(adapter=acoustic, store=store),
        ingest_acoustic_reviewed_outcomes(adapter=acoustic, store=store),
        ingest_noaa_history(begin, now, noaa=noaa, store=store),
        ingest_salmon(years, salmon=salmon, store=store),
        ingest_station_uptime(hydrophones_adapter=hydrophones, store=store),
        ingest_ndbc_realtime(adapter=ndbc, store=store),
        ingest_shoreline_snapshot(adapter=shoreline, store=store),
    ]


def refresh_recent(
    days: int = 7,
    acoustic: Optional[Any] = None,
    noaa: Optional[Any] = None,
    salmon: Optional[Any] = None,
    hydrophones: Optional[Any] = None,
    ndbc: Optional[Any] = None,
    shoreline: Optional[Any] = None,
    store: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Refresh the trailing window: recent acoustic, NOAA, current-year salmon."""
    ts = _resolve_store(store)
    now = datetime.now(timezone.utc)
    begin = now - timedelta(days=days)

    acoustic_summary = _ingest_acoustic_recent(ts, days=days, adapter=acoustic)
    reviewed_summary = ingest_acoustic_reviewed_outcomes(adapter=acoustic, max_pages=20, store=ts)
    noaa_summary = ingest_noaa_history(begin, now, noaa=noaa, store=ts)
    salmon_summary = ingest_salmon([now.year], salmon=salmon, store=ts)
    uptime_summary = ingest_station_uptime(hydrophones_adapter=hydrophones, store=ts)
    ndbc_summary = ingest_ndbc_realtime(adapter=ndbc, store=ts)
    shoreline_summary = ingest_shoreline_snapshot(adapter=shoreline, store=ts)
    spatial_summary = ingest_spatial_grid(store=ts)
    obis_summary = ingest_obis_validation(store=ts)
    inat_summary = ingest_inaturalist_validation(store=ts)

    return [
        acoustic_summary,
        reviewed_summary,
        noaa_summary,
        salmon_summary,
        uptime_summary,
        ndbc_summary,
        shoreline_summary,
        spatial_summary,
        obis_summary,
        inat_summary,
    ]


def timeseries_status(store: Optional[Any] = None) -> Dict[str, Any]:
    """Summarize each stream: stations, record count, and first/last timestamp."""
    ts = _resolve_store(store)
    status: Dict[str, Any] = {}
    for stream in (
        ACOUSTIC,
        ACOUSTIC_REVIEWED,
        WATER_LEVEL,
        CURRENTS,
        SALMON,
        STATION_UPTIME,
        NDBC_MET,
        SHORELINE,
        SPATIAL_GRID,
        OBIS_VERIFIED,
        INATURALIST_VERIFIED,
    ):
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
