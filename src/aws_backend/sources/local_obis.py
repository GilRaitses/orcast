from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from ..config import settings
from ..geo_region import filter_and_snap
from ..models import EnvironmentalSnapshot, NormalizedSighting, SourceEvidence
from .base import SourceAdapter, SourceFetchResult


class LocalObisAdapter(SourceAdapter):
    source_name = "obis_verified"
    reliability = 0.96

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings.local_obis_path

    def fetch(self) -> SourceFetchResult:
        if not self.path.exists():
            return SourceFetchResult(source=self.source_name, available=False, error=f"Missing {self.path}")
        with self.path.open("r", encoding="utf-8") as file:
            return SourceFetchResult(source=self.source_name, available=True, raw=json.load(file))

    def normalize(self, result: SourceFetchResult) -> List[NormalizedSighting]:
        if not result.available or not isinstance(result.raw, dict):
            return []

        sightings: List[NormalizedSighting] = []
        for item in result.raw.get("sightings", []):
            try:
                raw_lat = float(item["latitude"])
                raw_lng = float(item["longitude"])
            except (KeyError, TypeError, ValueError):
                result.skipped_count += 1
                continue
            snapped = filter_and_snap(raw_lat, raw_lng)
            if snapped is None:
                result.skipped_count += 1
                continue
            latitude, longitude = snapped

            timestamp = _parse_time(item.get("observation_timestamp"))
            confidence = float(item.get("data_quality_score", 0.9))
            evidence = SourceEvidence(
                source=self.source_name,
                source_id=str(item.get("sighting_id")),
                reliability=self.reliability,
                quality_grade="verified",
                notes="Local OBIS verified seed dataset",
            )
            env = item.get("environmental_context") or {}
            environmental = EnvironmentalSnapshot(
                timestamp=timestamp,
                latitude=latitude,
                longitude=longitude,
                tide_height_ft=_optional_float(env.get("tidal_height")),
                water_temp_c=_optional_float(env.get("water_temp_c")),
                data_sources={"historical": "OBIS verified local snapshot"},
                quality="historical_verified",
            )
            sightings.append(
                NormalizedSighting(
                    sighting_id=f"obis:{item.get('sighting_id')}",
                    source=self.source_name,
                    source_id=str(item.get("sighting_id")),
                    timestamp=timestamp,
                    latitude=latitude,
                    longitude=longitude,
                    location_name=item.get("location_name"),
                    behavior=_map_behavior(item.get("behavior_primary")),
                    count=item.get("pod_size"),
                    confidence=confidence,
                    source_reliability=self.reliability,
                    evidence=[evidence],
                    environmental=environmental,
                    raw=item,
                )
            )
        return sightings


def _parse_time(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _optional_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _map_behavior(value: str | None) -> str:
    if not value:
        return "unknown"
    normalized = value.lower().strip()
    if normalized == "foraging":
        return "feeding"
    return normalized

