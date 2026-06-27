"""Ocean Networks Canada (ONC) Oceans 3.0 hydrophone adapter.

Relays pre-generated spectrograms + station metadata for the `hydrophone_signal`
console panel. The ONC API token is read ONLY from the ONC_API_TOKEN env var and
is NEVER returned to the client or written to a tracked file
(HANDOFF_CHARTER B5). Spectrogram image bytes are streamed back through our own
backend so the token never leaves the server.

Discovery:   GET /api/locations?deviceCategoryCode=HYDROPHONE
Spectrogram: GET /api/archivefile/getByLocation (extension=png) then
             GET /api/archivefile/download?filename=...
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests

from ..config import settings

logger = logging.getLogger(__name__)

ONC_BASE = "https://data.oceannetworks.ca/api"
_TIMEOUT = 20.0


class OncDisabled(RuntimeError):
    """Raised when ONC integration is not configured (no token / flag off)."""


def onc_enabled() -> bool:
    return bool(settings.enable_onc and settings.onc_api_token)


def _token() -> str:
    token = settings.onc_api_token
    if not token:
        raise OncDisabled("ONC_API_TOKEN not configured")
    return token


def list_hydrophone_locations() -> List[Dict[str, Any]]:
    """Discover Salish Sea hydrophone locations and their location codes."""
    resp = requests.get(
        f"{ONC_BASE}/locations",
        params={"deviceCategoryCode": "HYDROPHONE", "token": _token()},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    return data if isinstance(data, list) else []


def _nearest_location(
    locations: List[Dict[str, Any]], lat: Optional[float], lng: Optional[float]
) -> Optional[Dict[str, Any]]:
    if not locations:
        return None
    if lat is None or lng is None:
        return locations[0]
    def dist(loc: Dict[str, Any]) -> float:
        llat = loc.get("lat")
        llng = loc.get("lon") if loc.get("lon") is not None else loc.get("lng")
        if llat is None or llng is None:
            return float("inf")
        return (float(llat) - lat) ** 2 + (float(llng) - lng) ** 2
    return min(locations, key=dist)


def recent_spectrogram_filename(location_code: str, *, days: int = 2) -> Optional[str]:
    """Return the most recent pre-generated spectrogram PNG filename, if any."""
    date_to = datetime.now(timezone.utc)
    date_from = date_to - timedelta(days=days)
    resp = requests.get(
        f"{ONC_BASE}/archivefile/location",
        params={
            "locationCode": location_code,
            "deviceCategoryCode": "HYDROPHONE",
            "dateFrom": date_from.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "dateTo": date_to.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "extension": "png",
            "token": _token(),
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    files = resp.json().get("files") or []
    # Prefer spectrogram products (dataProductCode HSD) when distinguishable.
    spectro = [f for f in files if "spect" in str(f).lower()] or files
    return spectro[-1] if spectro else None


def download_archivefile(filename: str) -> Tuple[bytes, str]:
    """Stream a single archive file's bytes (server-side; token never exposed)."""
    resp = requests.get(
        f"{ONC_BASE}/archivefile/download",
        params={"filename": filename, "token": _token()},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    content_type = resp.headers.get("Content-Type", "image/png")
    return resp.content, content_type


def hydrophone_signal(
    *, station: Optional[str], lat: Optional[float], lng: Optional[float]
) -> Dict[str, Any]:
    """Build the hydrophone_signal panel payload. Degrades gracefully when ONC is
    not configured: returns enabled=False with station metadata only."""
    if not onc_enabled():
        return {
            "status": "success",
            "enabled": False,
            "station": {"name": station, "lat": lat, "lng": lng},
            "spectrogram_url": None,
            "annotations_available": False,
            "message": (
                "Live ONC spectrogram requires ONC_API_TOKEN + ORCAST_ENABLE_ONC "
                "on the backend. Showing station metadata only."
            ),
        }
    try:
        locations = list_hydrophone_locations()
        loc = _nearest_location(locations, lat, lng)
        location_code = loc.get("locationCode") if loc else None
        filename = recent_spectrogram_filename(location_code) if location_code else None
        return {
            "status": "success",
            "enabled": True,
            "station": {
                "name": (loc.get("locationName") if loc else None) or station,
                "locationCode": location_code,
                "lat": loc.get("lat") if loc else lat,
                "lng": (loc.get("lon") if loc else None) or lng,
            },
            # Same-origin proxied path; the client never sees the ONC token.
            "spectrogram_url": (
                f"/api/be/api/onc/archivefile?filename={filename}" if filename else None
            ),
            "spectrogram_obtained_at": datetime.now(timezone.utc).isoformat(),
            "data_product": "ONC archivefile PNG (HSD spectrogram)",
            "annotations_available": True,
            "message": None if filename else "No recent spectrogram available for this station.",
        }
    except OncDisabled as exc:
        return {"status": "success", "enabled": False, "message": str(exc), "station": {"name": station}}
    except requests.RequestException as exc:
        logger.warning("ONC request failed: %s", exc)
        return {
            "status": "success",
            "enabled": False,
            "station": {"name": station, "lat": lat, "lng": lng},
            "message": "ONC service unreachable.",
        }
