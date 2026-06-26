"""NOAA Marine Cadastre / PMEL AIS vessel-traffic proxy adapter.

Aggregates vessel presence into grid/time bins for detectability and effort
offsets. Raw AIS tracks are not modeled directly.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

import requests

from ..geo_region import SAN_JUAN_BOUNDS

# PMEL ERDDAP tabledap endpoint for AIS annual summaries (dataset IDs vary by year).
_ERDDAP_TABLE = "https://coastwatch.pfeg.noaa.gov/erddap/tabledap/AIS2023_WestCoast.csv"


class AisTrafficAdapter:
    source_name = "noaa_ais"
    reliability = 0.75

    def __init__(self, timeout: float = 30.0, max_rows: int = 500) -> None:
        self.timeout = timeout
        self.max_rows = max_rows

    def fetch_aggregated_bins(self) -> List[Dict[str, object]]:
        """Return bounded vessel-traffic proxy bins for the pilot region."""
        params = {
            "latitude,longitude,time,vessel_type,mmsi": "",
            "latitude>=": SAN_JUAN_BOUNDS.min_lat,
            "latitude<=": SAN_JUAN_BOUNDS.max_lat,
            "longitude>=": SAN_JUAN_BOUNDS.min_lng,
            "longitude<=": SAN_JUAN_BOUNDS.max_lng,
            "orderBy": "time",
            "limit": self.max_rows,
        }
        try:
            response = requests.get(_ERDDAP_TABLE, params=params, timeout=self.timeout)
        except requests.RequestException:
            return []
        if response.status_code != 200 or "latitude" not in response.text.splitlines()[0].lower():
            return []
        return self._parse_csv(response.text)

    def _parse_csv(self, text: str) -> List[Dict[str, object]]:
        lines = [line for line in text.splitlines() if line and not line.startswith("Row")]
        if len(lines) < 2:
            return []
        headers = [part.strip() for part in lines[0].split(",")]
        records: List[Dict[str, object]] = []
        for row in lines[1:]:
            values = [part.strip() for part in row.split(",")]
            if len(values) != len(headers):
                continue
            payload = dict(zip(headers, values))
            try:
                lat = float(payload.get("latitude", ""))
                lng = float(payload.get("longitude", ""))
            except ValueError:
                continue
            cell_id = f"{lat:.3f}:{lng:.3f}"
            records.append(
                {
                    "t": payload.get("time") or datetime.now(timezone.utc).isoformat(),
                    "grid_cell_id": cell_id,
                    "latitude": lat,
                    "longitude": lng,
                    "vessel_count": 1,
                    "vessel_minutes": 60.0,
                    "large_vessel_presence": 1.0 if _is_large(payload.get("vessel_type")) else 0.0,
                    "speed_weighted_presence": 1.0,
                    "source": self.source_name,
                    "source_url": _ERDDAP_TABLE,
                }
            )
        return records


def _is_large(vessel_type: object) -> bool:
    text = str(vessel_type or "").lower()
    return any(token in text for token in ("cargo", "tanker", "passenger", "towing"))
