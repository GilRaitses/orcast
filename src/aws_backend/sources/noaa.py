from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Union

import requests

from ..models import EnvironmentalSnapshot
from .base import SourceAdapter, SourceFetchResult

# CO-OPS datagetter caps a single request at 31 days for 6-minute interval
# products, so longer ranges must be split into chunks at or below this size.
_MAX_RANGE_DAYS = 31

# Water-level stations and current stations use different identifier spaces.
# 9449880 (Friday Harbor) reports water level/temperature; currents require a
# dedicated current-station id. The prior default ("PUG1515") returns no data.
# PUG1702 is "Rosario Strait" (48.4581, -122.7501), a NOAA CO-OPS current
# station inside the San Juan Islands archipelago that publishes harmonic
# current predictions. It is verified to return data via the datagetter
# (product=currents_predictions, interval=60). It remains configurable per call.
_DEFAULT_CURRENT_STATION = "PUG1702"
DEFAULT_CURRENT_STATIONS = ("PUG1701", "PUG1702", "PUG1703")

_DATAGETTER_URL = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"


class NoaaAdapter(SourceAdapter):
    source_name = "noaa_coops"
    reliability = 0.9

    station = "9449880"
    station_name = "Friday Harbor"
    latitude = 48.5453
    longitude = -123.0125

    current_station = _DEFAULT_CURRENT_STATION
    current_stations = DEFAULT_CURRENT_STATIONS

    def fetch(self) -> SourceFetchResult:
        raw: Dict[str, object] = {}
        errors = []
        for product in ["water_level", "water_temperature"]:
            params = {
                "station": self.station,
                "product": product,
                "date": "latest",
                "datum": "MLLW",
                "format": "json",
                "units": "english",
                "time_zone": "gmt",
                "application": "ORCAST",
            }
            try:
                response = requests.get("https://api.tidesandcurrents.noaa.gov/api/prod/datagetter", params=params, timeout=10)
                content_type = response.headers.get("content-type", "")
                if response.status_code == 200 and "json" in content_type.lower():
                    raw[product] = response.json()
                else:
                    errors.append(f"{product}: HTTP {response.status_code} {content_type}")
            except requests.RequestException as exc:
                errors.append(f"{product}: {exc}")

        return SourceFetchResult(
            source=self.source_name,
            available=bool(raw),
            raw=raw,
            error="; ".join(errors) if errors else None,
        )

    def normalize(self, result: SourceFetchResult):
        return []

    def current_environment(self) -> EnvironmentalSnapshot:
        result = self.fetch()
        tide_height = None
        water_temp = None
        if result.available and isinstance(result.raw, dict):
            water_level = _latest_value(result.raw.get("water_level"))
            if water_level is not None:
                tide_height = water_level
            water_temp_f = _latest_value(result.raw.get("water_temperature"))
            if water_temp_f is not None:
                water_temp = (water_temp_f - 32) * 5 / 9

        return EnvironmentalSnapshot(
            timestamp=datetime.now(timezone.utc),
            latitude=self.latitude,
            longitude=self.longitude,
            tide_height_ft=tide_height if tide_height is not None else 0.0,
            water_temp_c=water_temp if water_temp is not None else 12.0,
            salinity_ppt=30.5,
            current_speed=0.5,
            visibility_km=15.0,
            data_sources={"tide": "NOAA CO-OPS", "temperature": "NOAA CO-OPS"},
            quality="live" if result.available else "fallback",
        )

    def fetch_water_level_history(
        self,
        begin: Union[date, datetime],
        end: Union[date, datetime],
        station: Optional[str] = None,
    ) -> List[Dict[str, object]]:
        """Return a normalized water-level time series for ``[begin, end]``.

        Long ranges are split into <=31-day chunks to satisfy the CO-OPS
        datagetter limit; a failing chunk is skipped so the remaining chunks
        still contribute data.
        """
        return self._fetch_history(
            product="water_level",
            begin=begin,
            end=end,
            station=station or self.station,
        )

    def fetch_currents_history(
        self,
        begin: Union[date, datetime],
        end: Union[date, datetime],
        station: str,
    ) -> List[Dict[str, object]]:
        """Return a normalized currents (speed) time series for ``[begin, end]``.

        Currents require a current-station id distinct from water-level
        stations. Real-time survey currents are tried first (``product=currents``);
        if that yields nothing (most San Juan stations are prediction-only), the
        harmonic current predictions are used instead
        (``product=currents_predictions``). Any failure (unknown station,
        unsupported product) yields an empty list rather than raising.
        """
        observed = self._fetch_history(
            product="currents",
            begin=begin,
            end=end,
            station=station,
        )
        if observed:
            return observed
        return self._fetch_current_predictions(begin, end, station)

    def _fetch_current_predictions(
        self,
        begin: Union[date, datetime],
        end: Union[date, datetime],
        station: str,
    ) -> List[Dict[str, object]]:
        """Fetch hourly harmonic current predictions and normalize them.

        The ``currents_predictions`` product uses a different payload shape than
        the observation products: results live under ``current_predictions.cp``
        with ``Time`` and ``Velocity_Major`` (knots) fields rather than the
        ``data``/``v`` rows of observation products.
        """
        series: List[Dict[str, object]] = []
        for chunk_begin, chunk_end in _chunk_ranges(begin, end, _MAX_RANGE_DAYS):
            params = {
                "station": station,
                "product": "currents_predictions",
                "begin_date": chunk_begin.strftime("%Y%m%d"),
                "end_date": chunk_end.strftime("%Y%m%d"),
                "interval": "60",
                "format": "json",
                "units": "english",
                "time_zone": "gmt",
                "application": "ORCAST",
            }
            try:
                response = requests.get(_DATAGETTER_URL, params=params, timeout=30)
                content_type = response.headers.get("content-type", "")
                if response.status_code != 200 or "json" not in content_type.lower():
                    continue
                payload = response.json()
            except (requests.RequestException, ValueError):
                continue

            series.extend(_normalize_current_predictions(payload, station=station))
        return series

    def _fetch_history(
        self,
        product: str,
        begin: Union[date, datetime],
        end: Union[date, datetime],
        station: str,
    ) -> List[Dict[str, object]]:
        series: List[Dict[str, object]] = []
        for chunk_begin, chunk_end in _chunk_ranges(begin, end, _MAX_RANGE_DAYS):
            params = {
                "station": station,
                "product": product,
                "begin_date": chunk_begin.strftime("%Y%m%d"),
                "end_date": chunk_end.strftime("%Y%m%d"),
                "datum": "MLLW",
                "format": "json",
                "units": "english",
                "time_zone": "gmt",
                "application": "ORCAST",
            }
            try:
                response = requests.get(_DATAGETTER_URL, params=params, timeout=30)
                content_type = response.headers.get("content-type", "")
                if response.status_code != 200 or "json" not in content_type.lower():
                    continue
                payload = response.json()
            except (requests.RequestException, ValueError):
                continue

            series.extend(_normalize_series(payload, product=product, station=station))
        return series


def _chunk_ranges(
    begin: Union[date, datetime],
    end: Union[date, datetime],
    max_days: int,
) -> List[tuple]:
    start = _as_date(begin)
    stop = _as_date(end)
    if stop < start:
        start, stop = stop, start

    span = timedelta(days=max_days - 1)
    chunks: List[tuple] = []
    cursor = start
    while cursor <= stop:
        chunk_end = min(cursor + span, stop)
        chunks.append((cursor, chunk_end))
        cursor = chunk_end + timedelta(days=1)
    return chunks


def _as_date(value: Union[date, datetime]) -> date:
    if isinstance(value, datetime):
        return value.date()
    return value


def _normalize_series(payload, product: str, station: str) -> List[Dict[str, object]]:
    if not isinstance(payload, dict):
        return []
    rows = payload.get("data") or []
    normalized: List[Dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        raw_value = row.get("v")
        if raw_value in (None, ""):
            continue
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        normalized.append(
            {
                "t": _to_iso(row.get("t")),
                "value": value,
                "product": product,
                "station": station,
            }
        )
    return normalized


def _normalize_current_predictions(payload, station: str) -> List[Dict[str, object]]:
    """Normalize a ``currents_predictions`` payload into series rows.

    Each row mirrors the observation-product schema (``t``/``value``/``product``/
    ``station``) so downstream storage treats both shapes identically.
    """
    if not isinstance(payload, dict):
        return []
    container = payload.get("current_predictions")
    if not isinstance(container, dict):
        return []
    rows = container.get("cp") or []
    normalized: List[Dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        raw_value = row.get("Velocity_Major")
        if raw_value in (None, ""):
            continue
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        normalized.append(
            {
                "t": _to_iso(row.get("Time")),
                "value": value,
                "velocity_major_knots": value,
                "speed_knots": abs(value),
                "product": "currents_predictions",
                "station": station,
                "bin": row.get("Bin"),
                "depth_ft": _coerce_float(row.get("Depth")),
                "mean_flood_dir_deg": _coerce_float(row.get("meanFloodDir")),
                "mean_ebb_dir_deg": _coerce_float(row.get("meanEbbDir")),
            }
        )
    return normalized


def _to_iso(timestamp) -> Optional[str]:
    if not isinstance(timestamp, str) or not timestamp:
        return timestamp if isinstance(timestamp, str) else None
    try:
        parsed = datetime.strptime(timestamp, "%Y-%m-%d %H:%M")
    except ValueError:
        return timestamp
    return parsed.replace(tzinfo=timezone.utc).isoformat()


def _latest_value(payload) -> float | None:
    if not isinstance(payload, dict):
        return None
    rows = payload.get("data") or []
    if not rows:
        return None
    try:
        return float(rows[-1]["v"])
    except (KeyError, TypeError, ValueError):
        return None


def _coerce_float(value) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

