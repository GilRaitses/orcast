from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests


_REALTIME_URL = "https://www.ndbc.noaa.gov/data/realtime2/{station}.txt"


class NdbcAdapter:
    """NOAA NDBC standard meteorological rows for detectability/noise covariates."""

    source_name = "noaa_ndbc"
    reliability = 0.9

    def __init__(self, station_ids: Optional[List[str]] = None, timeout: float = 15.0) -> None:
        self.station_ids = station_ids or ["46088"]
        self.timeout = timeout

    def fetch_stdmet_realtime(self, station_id: str) -> List[Dict[str, object]]:
        response = requests.get(_REALTIME_URL.format(station=station_id), timeout=self.timeout)
        if response.status_code != 200:
            return []
        return _parse_stdmet(response.text, station_id=station_id, source_url=response.url)

    def fetch_all_realtime(self) -> Dict[str, List[Dict[str, object]]]:
        return {station: self.fetch_stdmet_realtime(station) for station in self.station_ids}


def _parse_stdmet(text: str, station_id: str, source_url: str) -> List[Dict[str, object]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 3:
        return []
    header = lines[0].lstrip("#").split()
    units = lines[1].lstrip("#").split() if lines[1].startswith("#") else []
    records: List[Dict[str, object]] = []
    for line in lines[2:]:
        parts = line.split()
        if len(parts) < len(header):
            continue
        row = dict(zip(header, parts))
        parsed = _row_to_record(row, station_id=station_id, source_url=source_url)
        if parsed:
            parsed["units"] = dict(zip(header, units)) if units else {}
            records.append(parsed)
    return records


def _row_to_record(row: Dict[str, str], station_id: str, source_url: str) -> Optional[Dict[str, object]]:
    try:
        dt = datetime(
            int(row["YY"]),
            int(row["MM"]),
            int(row["DD"]),
            int(row["hh"]),
            int(row["mm"]),
            tzinfo=timezone.utc,
        )
    except (KeyError, TypeError, ValueError):
        return None
    return {
        "t": dt.isoformat(),
        "id": f"{station_id}:{dt.isoformat()}",
        "station": station_id,
        "source": "noaa_ndbc",
        "source_url": source_url,
        "wind_dir_deg_true": _num(row.get("WDIR")),
        "wind_speed_m_s": _num(row.get("WSPD")),
        "wind_gust_m_s": _num(row.get("GST")),
        "wave_height_m": _num(row.get("WVHT")),
        "dominant_wave_period_s": _num(row.get("DPD")),
        "average_wave_period_s": _num(row.get("APD")),
        "mean_wave_dir_deg_true": _num(row.get("MWD")),
        "pressure_hpa": _num(row.get("PRES")),
        "air_temp_c": _num(row.get("ATMP")),
        "water_temp_c": _num(row.get("WTMP")),
        "dewpoint_c": _num(row.get("DEWP")),
        "visibility_nmi": _num(row.get("VIS")),
    }


def _num(value: Optional[str]) -> Optional[float]:
    if value in (None, "MM", ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
