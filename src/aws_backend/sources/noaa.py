from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

import requests

from ..models import EnvironmentalSnapshot
from .base import SourceAdapter, SourceFetchResult


class NoaaAdapter(SourceAdapter):
    source_name = "noaa_coops"
    reliability = 0.9

    station = "9449880"
    station_name = "Friday Harbor"
    latitude = 48.5453
    longitude = -123.0125

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

