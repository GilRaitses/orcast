from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

import requests

from ..models import NormalizedSighting, SourceEvidence
from .base import SourceAdapter, SourceFetchResult


class INaturalistAdapter(SourceAdapter):
    source_name = "inaturalist"
    reliability = 0.72

    def __init__(self, days_back: int = 30, per_page: int = 50) -> None:
        self.days_back = days_back
        self.per_page = per_page

    def fetch(self) -> SourceFetchResult:
        start = (datetime.now(timezone.utc) - timedelta(days=self.days_back)).strftime("%Y-%m-%d")
        params = {
            "taxon_name": "Orcinus orca",
            "per_page": self.per_page,
            "order": "desc",
            "order_by": "observed_on",
            "geo": "true",
            "d1": start,
        }
        try:
            response = requests.get("https://api.inaturalist.org/v1/observations", params=params, timeout=15)
            content_type = response.headers.get("content-type", "")
            if response.status_code != 200:
                return SourceFetchResult(
                    source=self.source_name,
                    available=False,
                    status_code=response.status_code,
                    content_type=content_type,
                    error=response.text[:300],
                )
            if "json" not in content_type.lower():
                return SourceFetchResult(
                    source=self.source_name,
                    available=False,
                    status_code=response.status_code,
                    content_type=content_type,
                    error="iNaturalist returned non-JSON response",
                )
            return SourceFetchResult(
                source=self.source_name,
                available=True,
                raw=response.json(),
                status_code=response.status_code,
                content_type=content_type,
            )
        except requests.RequestException as exc:
            return SourceFetchResult(source=self.source_name, available=False, error=str(exc))

    def normalize(self, result: SourceFetchResult) -> List[NormalizedSighting]:
        if not result.available or not isinstance(result.raw, dict):
            return []
        sightings: List[NormalizedSighting] = []
        for obs in result.raw.get("results", []):
            location = obs.get("location")
            observed_at = obs.get("time_observed_at") or obs.get("observed_on")
            if not location or not observed_at:
                result.skipped_count += 1
                continue
            try:
                lat_text, lng_text = location.split(",", 1)
                latitude = float(lat_text)
                longitude = float(lng_text)
            except (TypeError, ValueError):
                result.skipped_count += 1
                continue

            quality_grade = obs.get("quality_grade", "unknown")
            reliability = _quality_reliability(quality_grade)
            photos = [photo.get("url") for photo in obs.get("photos", []) if photo.get("url")]
            source_id = str(obs.get("id"))
            evidence = SourceEvidence(
                source=self.source_name,
                source_id=source_id,
                source_url=obs.get("uri"),
                observed_at=_parse_time(observed_at),
                reliability=reliability,
                quality_grade=quality_grade,
                evidence_urls=photos,
                notes=f"iNaturalist observation by {obs.get('user', {}).get('login', 'unknown')}",
            )
            sightings.append(
                NormalizedSighting(
                    sighting_id=f"inat:{source_id}",
                    source=self.source_name,
                    source_id=source_id,
                    source_url=obs.get("uri"),
                    timestamp=_parse_time(observed_at),
                    latitude=latitude,
                    longitude=longitude,
                    common_name=obs.get("species_guess") or "Killer Whale",
                    behavior="unknown",
                    confidence=reliability,
                    source_reliability=reliability,
                    evidence=[evidence],
                    raw=obs,
                )
            )
        return sightings


def _parse_time(value: str) -> datetime:
    if "T" in value:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def _quality_reliability(quality_grade: str) -> float:
    if quality_grade == "research":
        return 0.82
    if quality_grade == "needs_id":
        return 0.62
    return 0.48

