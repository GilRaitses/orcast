from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import requests

from ..geo_region import SAN_JUAN_BOUNDS, filter_and_snap
from ..models import NormalizedSighting, SourceEvidence
from .base import SourceAdapter, SourceFetchResult

OBIS_OCCURRENCE_URL = "https://api.obis.org/v3/occurrence"


def _region_wkt() -> str:
    """WKT POLYGON covering the San Juan archipelago bbox (lng lat order)."""
    min_lat = SAN_JUAN_BOUNDS.min_lat
    max_lat = SAN_JUAN_BOUNDS.max_lat
    min_lng = SAN_JUAN_BOUNDS.min_lng
    max_lng = SAN_JUAN_BOUNDS.max_lng
    return (
        "POLYGON(("
        f"{min_lng} {min_lat}, "
        f"{max_lng} {min_lat}, "
        f"{max_lng} {max_lat}, "
        f"{min_lng} {max_lat}, "
        f"{min_lng} {min_lat}"
        "))"
    )


class LiveObisAdapter(SourceAdapter):
    """Live OBIS occurrence backbone for Orcinus orca in the pilot region.

    Shares ``source_name`` with the local seed so records merge into the same
    canonical identity downstream.
    """

    source_name = "obis_verified"
    reliability = 0.96

    def __init__(self, size: int = 200, timeout: int = 45) -> None:
        self.size = size
        self.timeout = timeout

    def fetch(self, start_date: str | None = None, end_date: str | None = None) -> SourceFetchResult:
        params = {
            "scientificname": "Orcinus orca",
            "geometry": _region_wkt(),
            "size": self.size,
        }
        if start_date:
            params["startdate"] = start_date
        if end_date:
            params["enddate"] = end_date
        try:
            response = requests.get(OBIS_OCCURRENCE_URL, params=params, timeout=self.timeout)
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
                    error="OBIS returned non-JSON response",
                )
            return SourceFetchResult(
                source=self.source_name,
                available=True,
                raw=response.json(),
                status_code=response.status_code,
                content_type=content_type,
            )
        except (requests.RequestException, ValueError) as exc:
            return SourceFetchResult(source=self.source_name, available=False, error=str(exc))

    def normalize(self, result: SourceFetchResult) -> List[NormalizedSighting]:
        if not result.available or not isinstance(result.raw, dict):
            return []

        sightings: List[NormalizedSighting] = []
        for record in result.raw.get("results", []):
            try:
                raw_lat = float(record["decimalLatitude"])
                raw_lng = float(record["decimalLongitude"])
            except (KeyError, TypeError, ValueError):
                result.skipped_count += 1
                continue
            snapped = filter_and_snap(raw_lat, raw_lng)
            if snapped is None:
                result.skipped_count += 1
                continue
            latitude, longitude = snapped

            record_id = record.get("id") or record.get("occurrenceID")
            source_id = str(record_id)
            timestamp = _parse_time(record.get("eventDate"))
            source_url = record.get("occurrenceID") if _is_url(record.get("occurrenceID")) else None
            evidence = SourceEvidence(
                source=self.source_name,
                source_id=source_id,
                source_url=source_url,
                observed_at=timestamp,
                reliability=self.reliability,
                quality_grade="verified",
                notes=_obis_citation(record),
            )
            sightings.append(
                NormalizedSighting(
                    sighting_id=f"obis:{record_id}",
                    source=self.source_name,
                    source_id=source_id,
                    source_url=source_url,
                    timestamp=timestamp,
                    latitude=latitude,
                    longitude=longitude,
                    location_name=record.get("locality"),
                    behavior=_map_behavior(record.get("behavior")),
                    confidence=0.9,
                    source_reliability=self.reliability,
                    evidence=[evidence],
                    raw=record,
                )
            )
        return sightings

    def fetch_validation_records(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> List[dict]:
        """Return held-out validation records with license/citation metadata."""
        result = self.fetch(start_date=start_date, end_date=end_date)
        if not result.available or not isinstance(result.raw, dict):
            return []
        records: List[dict] = []
        for record in result.raw.get("results", []):
            try:
                raw_lat = float(record["decimalLatitude"])
                raw_lng = float(record["decimalLongitude"])
            except (KeyError, TypeError, ValueError):
                continue
            snapped = filter_and_snap(raw_lat, raw_lng)
            if snapped is None:
                continue
            latitude, longitude = snapped
            record_id = record.get("id") or record.get("occurrenceID")
            source_url = record.get("occurrenceID") if _is_url(record.get("occurrenceID")) else None
            records.append(
                {
                    "t": _parse_time(record.get("eventDate")).isoformat(),
                    "id": f"obis:{record_id}",
                    "latitude": latitude,
                    "longitude": longitude,
                    "quality_grade": "verified",
                    "license": record.get("license") or record.get("rights"),
                    "citation": _obis_citation(record),
                    "source_url": source_url,
                    "source": self.source_name,
                    "locality": record.get("locality"),
                }
            )
        return records


def _parse_time(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    text = str(value).strip()
    # OBIS eventDate can be a range ("2020-01-01/2020-01-02"); take the start.
    if "/" in text:
        text = text.split("/", 1)[0].strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
            try:
                parsed = datetime.strptime(text, fmt)
                break
            except ValueError:
                continue
        else:
            return datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _is_url(value) -> bool:
    return isinstance(value, str) and value.startswith(("http://", "https://"))


def _map_behavior(value: str | None) -> str:
    if not value:
        return "unknown"
    normalized = str(value).lower().strip()
    if normalized == "foraging":
        return "feeding"
    return normalized


def _obis_citation(record: dict) -> str:
    dataset = record.get("datasetName") or record.get("datasetID") or "OBIS occurrence"
    institution = record.get("institutionCode") or record.get("ownerInstitutionCode") or "unknown institution"
    event_date = record.get("eventDate") or "unknown date"
    return f"{dataset}; {institution}; eventDate={event_date}"
