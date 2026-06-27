"""Ocean Networks Canada (ONC) Oceans 3.0 hydrophone adapter.

Relays pre-generated spectrograms + station metadata for the `hydrophone_signal`
console panel. The ONC API token is read ONLY from the ONC_API_TOKEN env var and
is NEVER returned to the client or written to a tracked file
(HANDOFF_CHARTER B5). Spectrogram image bytes are streamed back through our own
backend so the token never leaves the server.

ONC Oceans 3.0 (v3 REST) endpoints used:
  Discovery:   GET /api/locations?deviceCategoryCode=HYDROPHONE
  Spectrogram: GET /api/archivefile/location  (extension=png) -> {"files": [...]}
               GET /api/archivefile/download?filename=...
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import requests

from ..config import settings

logger = logging.getLogger(__name__)

ONC_BASE = "https://data.oceannetworks.ca/api"
_TIMEOUT = 20.0

# --- Filename validation (SSRF / parameter-injection defense, AX-2) ----------
#
# ONC archive filenames look like:
#   ICLISTENHF1560_20181004T235903.000Z-spect.mat
#   AXISQ6044PTZACCC8E334C53_20161201T000001.000Z.jpg
#   ClayoquotSlope_Bullseye_ConductivityTemperatureDepth_..._-clean.png
#
# The download relay only serves spectrogram imagery, so we accept a deliberately
# narrow allowlist: ASCII letters/digits plus the punctuation that legitimately
# appears in ONC filenames ('.', '_', '-'), a required image extension, and a
# bounded length. This rejects URL schemes, hosts, '/', '..', '?', '&', '=',
# and whitespace, so the value cannot be coerced into fetching an arbitrary URL
# or injecting extra query parameters into the ONC request.
_ALLOWED_EXTENSIONS = ("png", "jpg", "jpeg")
_MAX_FILENAME_LEN = 256
# NOTE: anchor with \A...\Z (not ^...$). In Python, ``$`` also matches just
# before a trailing newline, which would let "file.png\n" pass validation.
_ARCHIVE_FILENAME_RE = re.compile(
    r"\A[A-Za-z0-9][A-Za-z0-9._-]*\.(?:" + "|".join(_ALLOWED_EXTENSIONS) + r")\Z"
)


class OncDisabled(RuntimeError):
    """Raised when ONC integration is not configured (no token / flag off)."""


class OncInvalidFilename(ValueError):
    """Raised when an archive filename fails allowlist validation."""


def is_valid_archive_filename(filename: Any) -> bool:
    """Return True only for plausible, safe ONC archive image filenames."""
    if not isinstance(filename, str):
        return False
    if not filename or len(filename) > _MAX_FILENAME_LEN:
        return False
    # `..` would pass the character class but is never legitimate.
    if ".." in filename:
        return False
    return bool(_ARCHIVE_FILENAME_RE.match(filename))


def validate_archive_filename(filename: Any) -> str:
    """Validate and return ``filename`` or raise :class:`OncInvalidFilename`."""
    if not is_valid_archive_filename(filename):
        # Do not echo the raw value back verbatim in a way that could be abused;
        # a short generic message is enough for the 400 response.
        raise OncInvalidFilename("Invalid ONC archive filename")
    return filename


def onc_enabled() -> bool:
    return bool(settings.enable_onc and settings.onc_api_token)


def _token() -> str:
    token = settings.onc_api_token
    if not token:
        raise OncDisabled("ONC_API_TOKEN not configured")
    return token


def _redact(text: str) -> str:
    """Strip the ONC token from any string before it reaches a log sink.

    ``requests`` exceptions (e.g. HTTPError/ConnectionError) embed the full
    request URL, which includes ``token=...``. Redact both the live token value
    and any ``token=`` query parameter as defense in depth.
    """
    token = settings.onc_api_token
    if token:
        text = text.replace(token, "***")
    return re.sub(r"(?i)(token=)[^&\s]+", r"\1***", text)


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


_TIMESTAMP_RE = re.compile(r"(\d{8}T\d{6})")


def _archive_sort_key(filename: str) -> str:
    """Sort key that orders ONC archive files chronologically.

    ONC filenames embed an ISO-ish timestamp (``YYYYMMDDTHHMMSS``); using that as
    the key is more reliable than raw lexical order across device prefixes. Files
    without a parseable timestamp sort first so real captures win the ``max``.
    """
    match = _TIMESTAMP_RE.search(filename)
    return match.group(1) if match else ""


def recent_spectrogram_filename(location_code: str, *, days: int = 2) -> Optional[str]:
    """Return the most recent pre-generated spectrogram PNG filename, if any.

    Note: the ONC ``/archivefile/location`` parameter is ``fileExtension`` (the
    python client maps its ``extension`` kwarg to this). A 400 here means the
    device had no deployment / no archived files in the requested window, which
    we treat as "no recent spectrogram" rather than an error.
    """
    date_to = datetime.now(timezone.utc)
    date_from = date_to - timedelta(days=days)
    resp = requests.get(
        f"{ONC_BASE}/archivefile/location",
        params={
            "locationCode": location_code,
            "deviceCategoryCode": "HYDROPHONE",
            "dateFrom": date_from.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "dateTo": date_to.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "fileExtension": "png",
            "token": _token(),
        },
        timeout=_TIMEOUT,
    )
    if resp.status_code == 400:
        # No deployment / no files in range (ONC errorCode 127), not a fault.
        logger.debug("ONC archivefile/location 400 for %s: %s", location_code, _redact(resp.text))
        return None
    resp.raise_for_status()
    payload = resp.json()
    files = (payload.get("files") if isinstance(payload, dict) else None) or []
    # `files` is a list of filename strings. Keep only safe image filenames so the
    # value we hand back can be replayed through the validated download route.
    candidates = [f for f in files if is_valid_archive_filename(f)]
    if not candidates:
        return None
    # Prefer full spectrogram products; ONC emits "...-spect.png" alongside
    # reduced "...-spect-small.png" / "...-spect-thumb.png" variants, so favor
    # the full-resolution image.
    spectro = [f for f in candidates if "spect" in f.lower()] or candidates
    full = [
        f for f in spectro if not ("small" in f.lower() or "thumb" in f.lower())
    ] or spectro
    # Ties on timestamp (full vs reduced share a capture time) break toward the
    # shortest name, which is the unsuffixed full image.
    return max(full, key=lambda f: (_archive_sort_key(f), -len(f)))


def download_archivefile(filename: str) -> Tuple[bytes, str]:
    """Stream a single archive file's bytes (server-side; token never exposed).

    ``filename`` is validated against a strict allowlist first to close the
    SSRF / parameter-injection vector (AX-2).
    """
    validate_archive_filename(filename)
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
        spectrogram_url = (
            f"/api/be/api/onc/archivefile?filename={quote(filename, safe='')}"
            if filename
            else None
        )
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
            "spectrogram_url": spectrogram_url,
            "spectrogram_obtained_at": datetime.now(timezone.utc).isoformat(),
            "data_product": "ONC archivefile PNG (HSD spectrogram)",
            "annotations_available": True,
            "message": None if filename else "No recent spectrogram available for this station.",
        }
    except OncDisabled as exc:
        return {"status": "success", "enabled": False, "message": str(exc), "station": {"name": station}}
    except requests.RequestException as exc:
        logger.warning("ONC request failed: %s", _redact(str(exc)))
        return {
            "status": "success",
            "enabled": False,
            "station": {"name": station, "lat": lat, "lng": lng},
            "message": "ONC service unreachable.",
        }
