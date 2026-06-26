"""Historical OrcaHello acoustic-detection archive adapter.

Unlike the live :class:`~src.aws_backend.sources.orcahello.OrcaHelloAdapter`
(which fetches a single recent window and emits ``NormalizedSighting`` objects),
this adapter pages through the full OrcaHello detections archive and returns
plain acoustic-detection record dicts. Persistence and modeling are handled by
callers; this module stays independent of state and storage.

The detections API returns a TOP-LEVEL JSON ARRAY of detections; total counts
live in response headers, not the body. See docs/ml/ORCA_ML_INTEGRATION.md.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

import requests

from ..geo_region import in_bounds

logger = logging.getLogger(__name__)

ORCAHELLO_API_HOST = "https://aifororcasdetections.azurewebsites.net"
ORCAHELLO_DETECTIONS_PATH = "/api/detections"

# Dedicated moderator-outcome endpoints (v1.2 Swagger).
REVIEWED_OUTCOME_PATHS = {
    "confirmed": "/api/detections/confirmed",
    "false_positive": "/api/detections/falsepositives",
    "unknown": "/api/detections/unknowns",
    "unreviewed": "/api/detections/unreviewed",
}

# OrcaHello marks a reviewed detection as a true orca when ``found`` is an
# affirmative yes. The archive is inconsistent about casing and occasionally
# uses a boolean, so we normalize against this set.
_AFFIRMATIVE_FOUND = {"yes", "true"}


class OrcaHelloHistoryAdapter:
    """Pages the OrcaHello detections archive into normalized record dicts."""

    source_name = "orcahello_history"

    def __init__(self, base_url: str = ORCAHELLO_API_HOST, timeout: float = 15.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @property
    def _endpoint(self) -> str:
        return f"{self.base_url}{ORCAHELLO_DETECTIONS_PATH}"

    def fetch_history(
        self,
        max_pages: int = 200,
        records_per_page: int = 100,
        timeframe: str = "all",
        confirmed_only: bool = False,
        in_region_only: bool = True,
    ) -> List[dict]:
        """Page through the archive and return normalized acoustic-detection dicts.

        Pages ``Page=1..N`` until an empty page or ``max_pages`` is reached. On a
        non-JSON body or any HTTP/transport error, paging stops and whatever has
        been collected so far is returned (this never raises).
        """
        records: List[dict] = []
        for page in range(1, max_pages + 1):
            detections = self._fetch_page(page, records_per_page, timeframe)
            if detections is None:
                # Transport/HTTP/parse failure: stop paging, keep what we have.
                break
            if not detections:
                # Empty page marks the end of the archive.
                break
            for det in detections:
                record = self._normalize(det)
                if record is None:
                    continue
                if in_region_only and not _record_in_region(record):
                    continue
                if confirmed_only and not record["confirmed"]:
                    continue
                records.append(record)
        return records

    def fetch_reviewed_outcomes(
        self,
        max_pages: int = 50,
        records_per_page: int = 100,
        timeframe: str = "all",
        in_region_only: bool = True,
    ) -> List[dict]:
        """Page the dedicated reviewed-outcome endpoints into normalized records."""
        records: List[dict] = []
        for outcome, path in REVIEWED_OUTCOME_PATHS.items():
            endpoint = f"{self.base_url}{path}"
            for page in range(1, max_pages + 1):
                detections = self._fetch_page(
                    page,
                    records_per_page,
                    timeframe,
                    endpoint=endpoint,
                )
                if detections is None:
                    break
                if not detections:
                    break
                for det in detections:
                    record = self._normalize(det)
                    if record is None:
                        continue
                    if in_region_only and not _record_in_region(record):
                        continue
                    record["outcome"] = outcome
                    record["reviewed"] = outcome != "unreviewed"
                    if outcome == "confirmed":
                        record["confirmed"] = True
                    elif outcome == "false_positive":
                        record["confirmed"] = False
                        record["found"] = record.get("found") or "no"
                    records.append(record)
        return records

    def _fetch_page(
        self,
        page: int,
        records_per_page: int,
        timeframe: str,
        endpoint: Optional[str] = None,
    ) -> Optional[List[dict]]:
        """Return the detections array for a page, or ``None`` to stop paging."""
        params = {
            "Page": page,
            "SortBy": "timestamp",
            "SortOrder": "asc",
            "Timeframe": timeframe,
            "RecordsPerPage": records_per_page,
        }
        url = endpoint or self._endpoint
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            logger.warning("OrcaHello history request failed on page %s: %s", page, exc)
            return None
        if response.status_code != 200:
            logger.warning(
                "OrcaHello history page %s returned HTTP %s; stopping",
                page,
                response.status_code,
            )
            return None
        try:
            payload = response.json()
        except ValueError as exc:
            logger.warning("OrcaHello history page %s was not JSON: %s; stopping", page, exc)
            return None
        # The API returns a top-level array; tolerate a wrapped object too.
        if isinstance(payload, dict):
            payload = payload.get("detections") or payload.get("items") or []
        if not isinstance(payload, list):
            logger.warning("OrcaHello history page %s JSON was not an array; stopping", page)
            return None
        return [det for det in payload if isinstance(det, dict)]

    def _normalize(self, det: dict) -> Optional[dict]:
        location = det.get("location") or {}
        latitude = _coerce_float(location.get("latitude"))
        longitude = _coerce_float(location.get("longitude"))
        timestamp = _parse_time(det.get("timestamp"))

        reviewed = bool(det.get("reviewed", False))
        found = det.get("found")
        confirmed = reviewed and _is_affirmative(found)

        return {
            "t": timestamp,
            "id": str(det.get("id")) if det.get("id") is not None else None,
            "station": location.get("name"),
            "latitude": latitude,
            "longitude": longitude,
            "confidence": _normalize_confidence(det.get("confidence")),
            "reviewed": reviewed,
            "found": found if isinstance(found, str) else _found_to_str(found),
            "confirmed": confirmed,
            "audio_uri": det.get("audioUri"),
            "spectrogram_uri": det.get("spectrogramUri"),
        }


def _record_in_region(record: dict) -> bool:
    lat = record.get("latitude")
    lng = record.get("longitude")
    if lat is None or lng is None:
        return False
    return in_bounds(lat, lng)


def _is_affirmative(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in _AFFIRMATIVE_FOUND
    return False


def _found_to_str(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def _coerce_float(value) -> Optional[float]:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result


def _parse_time(value) -> Optional[str]:
    """Return an ISO 8601 timestamp string, or ``None`` when unparseable."""
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.isoformat()


def _normalize_confidence(value) -> float:
    """Rescale OrcaHello's 0-100 confidence to a 0-1 float."""
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    if confidence > 1:
        confidence = confidence / 100.0
    return max(0.0, min(1.0, confidence))
