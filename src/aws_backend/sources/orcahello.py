from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

import requests

from ..geo_region import in_bounds
from ..models import NormalizedSighting, SourceEvidence
from .base import SourceAdapter, SourceFetchResult


# OrcaHello / "AI For Orcas" detections REST API (v1.2). The detections API is a
# separate host from the Blazor moderator/public portal (aifororcas.azurewebsites.net,
# which serves HTML). The API returns a TOP-LEVEL JSON ARRAY of detections; total
# counts live in response headers, not the body. See docs/ml/ORCA_ML_INTEGRATION.md.
ORCAHELLO_API_HOST = "https://aifororcasdetections.azurewebsites.net"

# Map OrcaHello's Timeframe enum from an hours window. The API accepts discrete
# buckets: 30m, 3h, 6h, 24h, 1w, 1m, range, all.
_TIMEFRAME_BUCKETS = [
    (0.5, "30m"),
    (3, "3h"),
    (6, "6h"),
    (24, "24h"),
    (24 * 7, "1w"),
    (24 * 31, "1m"),
]


def _timeframe_for_hours(hours_back: float) -> str:
    for threshold, label in _TIMEFRAME_BUCKETS:
        if hours_back <= threshold:
            return label
    return "all"


class OrcaHelloAdapter(SourceAdapter):
    source_name = "orcahello"
    reliability = 0.78

    def __init__(self, hours_back: int = 24, confirmed_only: bool = False) -> None:
        self.hours_back = hours_back
        # OrcaHello's unreviewed stream is dominated by false positives. Prefer
        # the confirmed endpoint when a "detected" claim is needed; otherwise we
        # label records as unreviewed acoustic candidates.
        self.confirmed_only = confirmed_only
        self.base_url = ORCAHELLO_API_HOST

    @property
    def _endpoint(self) -> str:
        return "/api/detections/confirmed" if self.confirmed_only else "/api/detections"

    def fetch(self) -> SourceFetchResult:
        params = {
            "Page": 1,
            "SortBy": "timestamp",
            "SortOrder": "desc",
            "Timeframe": _timeframe_for_hours(self.hours_back),
            "RecordsPerPage": 50,
        }
        try:
            response = requests.get(f"{self.base_url}{self._endpoint}", params=params, timeout=12)
            content_type = response.headers.get("content-type", "")
            if response.status_code != 200:
                return SourceFetchResult(
                    source=self.source_name,
                    available=False,
                    status_code=response.status_code,
                    content_type=content_type,
                    error=response.text[:300],
                )
            # Fallback guard: the live API serves JSON, but if we somehow hit the
            # HTML portal again, skip cleanly rather than raising on .json().
            if "json" not in content_type.lower():
                return SourceFetchResult(
                    source=self.source_name,
                    available=False,
                    status_code=response.status_code,
                    content_type=content_type,
                    error="OrcaHello returned non-JSON content; source skipped",
                )
            payload = response.json()
            # The detections API returns a top-level array. Be tolerant of a
            # wrapped object too, in case a future version nests the list.
            if isinstance(payload, dict):
                payload = payload.get("detections") or payload.get("results") or []
            if not isinstance(payload, list):
                return SourceFetchResult(
                    source=self.source_name,
                    available=False,
                    status_code=response.status_code,
                    content_type=content_type,
                    error="OrcaHello JSON was not a detections array",
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
        if not result.available or not isinstance(result.raw, list):
            return []
        sightings: List[NormalizedSighting] = []
        for det in result.raw:
            if not isinstance(det, dict):
                result.skipped_count += 1
                continue
            location = det.get("location") or {}
            latitude = location.get("latitude")
            longitude = location.get("longitude")
            timestamp = _parse_time(det.get("timestamp"))
            if latitude is None or longitude is None or timestamp is None:
                result.skipped_count += 1
                continue

            # Region filter on the hydrophone position. These are fixed
            # instrument locations, so we do not snap them to water; out-of-region
            # stations (e.g. Port Townsend) are dropped server-side.
            if not in_bounds(float(latitude), float(longitude)):
                result.skipped_count += 1
                continue

            source_id = str(det.get("id"))
            # Top-level confidence is on a 0-100 scale; _normalize_confidence
            # rescales to 0..1.
            confidence = _normalize_confidence(det.get("confidence"))
            reviewed = bool(det.get("reviewed", False))
            found = det.get("found")
            confirmed = reviewed and isinstance(found, str) and found.strip().lower() == "yes"
            # Honesty: these are acoustic candidate detections at a hydrophone,
            # not confirmed orca positions. Only confirmed records earn the
            # "confirmed" grade; everything else stays an unreviewed candidate.
            quality_grade = "confirmed_acoustic_detection" if confirmed else "unreviewed_acoustic_candidate"
            location_name = location.get("name")
            audio_uri = det.get("audioUri")
            spectrogram_uri = det.get("spectrogramUri")
            evidence_urls = [url for url in [audio_uri, spectrogram_uri] if url]

            note = (
                f"OrcaHello acoustic candidate at hydrophone {location_name or 'unknown'} "
                "(coordinates are the hydrophone position, not the orca)"
            )

            evidence = SourceEvidence(
                source=self.source_name,
                source_id=source_id,
                source_url=audio_uri,
                observed_at=timestamp,
                reliability=self.reliability,
                quality_grade=quality_grade,
                evidence_urls=evidence_urls,
                notes=note,
            )
            sightings.append(
                NormalizedSighting(
                    sighting_id=f"orcahello:{source_id}",
                    source=self.source_name,
                    source_id=source_id,
                    source_url=audio_uri,
                    timestamp=timestamp,
                    latitude=float(latitude),
                    longitude=float(longitude),
                    location_name=location_name,
                    behavior="acoustic_detection",
                    confidence=confidence,
                    source_reliability=self.reliability,
                    evidence=[evidence],
                    raw=det,
                )
            )
        return sightings


def _parse_time(value) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _normalize_confidence(value) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.5
    if confidence > 1:
        confidence = confidence / 100.0
    return max(0.0, min(1.0, confidence))
