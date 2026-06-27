"""ONC hydrophone signal relay (public read-only).

Serves station metadata + recent spectrogram for the `hydrophone_signal` console
panel. The ONC token stays server-side; spectrogram bytes are streamed through
`/api/onc/archivefile` so the client never receives the token.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, Response

from ..sources import onc

router = APIRouter()


@router.get("/api/onc/hydrophone-signal")
def onc_hydrophone_signal(
    station: Optional[str] = Query(default=None, max_length=120),
    lat: Optional[float] = Query(default=None),
    lng: Optional[float] = Query(default=None),
) -> Dict[str, Any]:
    return onc.hydrophone_signal(station=station, lat=lat, lng=lng)


@router.get("/api/onc/archivefile")
def onc_archivefile(filename: str = Query(..., max_length=256)) -> Response:
    # Reject malformed filenames before any upstream call (SSRF / injection, AX-2).
    if not onc.is_valid_archive_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid ONC archive filename")
    if not onc.onc_enabled():
        raise HTTPException(status_code=503, detail="ONC integration not configured")
    try:
        content, content_type = onc.download_archivefile(filename)
    except onc.OncInvalidFilename as exc:
        raise HTTPException(status_code=400, detail="Invalid ONC archive filename") from exc
    except onc.OncDisabled as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - upstream failures map to 502
        raise HTTPException(status_code=502, detail="ONC archivefile fetch failed") from exc
    return Response(content=content, media_type=content_type)
