from __future__ import annotations

from fastapi import Header, HTTPException

from .config import settings


def require_api_key(x_orcast_key: str | None = Header(default=None, alias="X-ORCAST-Key")) -> None:
    """Require X-ORCAST-Key when ORCAST_API_KEY is configured (production)."""
    if not settings.api_key:
        return
    if x_orcast_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing X-ORCAST-Key header")
