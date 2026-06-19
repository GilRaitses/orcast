from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from .. import ingest_timeseries
from ..auth import require_api_key

router = APIRouter()


@router.get("/api/data-status")
def data_status() -> Dict[str, Any]:
    return ingest_timeseries.timeseries_status()


@router.post("/api/timeseries/backfill")
def backfill(years_back: int = 3, _: None = Depends(require_api_key)) -> List[Dict[str, Any]]:
    return ingest_timeseries.backfill_all(years_back)


@router.post("/api/timeseries/refresh")
def refresh(days: int = 7, _: None = Depends(require_api_key)) -> List[Dict[str, Any]]:
    return ingest_timeseries.refresh_recent(days)
