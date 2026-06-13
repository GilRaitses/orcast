from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

import requests

from ..models import NormalizedSighting, SourceEvidence
from .base import SourceAdapter, SourceFetchResult


class OrcaHelloAdapter(SourceAdapter):
    source_name = "orcahello"
    reliability = 0.78

    def __init__(self, hours_back: int = 24) -> None:
        self.hours_back = hours_back
        self.base_url = "https://aifororcas.azurewebsites.net/api"

    def fetch(self) -> SourceFetchResult:
        end = datetime.now(timezone.utc)
        start = end - timedelta(hours=self.hours_back)
        params = {
            "fromDate": start.strftime("%m/%d/%Y"),
            "toDate": end.strftime("%m/%d/%Y"),
            "page": 1,
            "pageSize": 25,
        }
        try:
            response = requests.get(f"{self.base_url}/detections/bytag/whale", params=params, timeout=12)
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
                    error="OrcaHello returned non-JSON content; source skipped",
                )
            payload = response.json()
            if not isinstance(payload, dict) or "detections" not in payload:
                return SourceFetchResult(
                    source=self.source_name,
                    available=False,
                    status_code=response.status_code,
                    content_type=content_type,
                    error="OrcaHello JSON did not contain detections",
                )
            return SourceFetchResult(
                source=self.source_name,
                available=True,
                raw=payload,
                status_code=response.status_code,
                content_type=content_type,
            )
        except requests.RequestException as exc:
            return SourceFetchResult(source=self.source_name, available=False, error=str(exc))

    def normalize(self, result: SourceFetchResult) -> List[NormalizedSighting]:
        if not result.available or not isinstance(result.raw, dict):
            return []
        sightings: List[NormalizedSighting] = []
        for det in result.raw.get("detections", []):
            location = det.get("location") or {}
            latitude = location.get("latitude")
            longitude = location.get("longitude")
            timestamp = det.get("timestamp")
            if latitude is None or longitude is None or not timestamp:
                result.skipped_count += 1
                continue
            source_id = str(det.get("id"))
            confidence = _normalize_confidence(det.get("whaleFoundConfidence"))
            evidence = SourceEvidence(
                source=self.source_name,
                source_id=source_id,
                source_url=det.get("audioUri"),
                observed_at=datetime.fromisoformat(timestamp.replace("Z", "+00:00")),
                reliability=self.reliability,
                quality_grade=det.get("state"),
                evidence_urls=[url for url in [det.get("audioUri"), det.get("imageUri")] if url],
                notes="OrcaHello acoustic detection",
            )
            sightings.append(
                NormalizedSighting(
                    sighting_id=f"orcahello:{source_id}",
                    source=self.source_name,
                    source_id=source_id,
                    source_url=det.get("audioUri"),
                    timestamp=datetime.fromisoformat(timestamp.replace("Z", "+00:00")),
                    latitude=float(latitude),
                    longitude=float(longitude),
                    location_name=det.get("locationName"),
                    behavior="acoustic_detection",
                    confidence=confidence,
                    source_reliability=self.reliability,
                    evidence=[evidence],
                    raw=det,
                )
            )
        return sightings


def _normalize_confidence(value) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.5
    return confidence / 100.0 if confidence > 1 else confidence

