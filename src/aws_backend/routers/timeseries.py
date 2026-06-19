from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends

from .. import ingest_timeseries
from ..auth import require_api_key

router = APIRouter()


@router.get("/api/data-status")
def data_status() -> Dict[str, Any]:
    return ingest_timeseries.timeseries_status()


@router.post("/api/timeseries/backfill", status_code=202)
def backfill(
    background: BackgroundTasks, years_back: int = 3, _: None = Depends(require_api_key)
) -> Dict[str, Any]:
    """Run the full backfill in the background; paging the OrcaHello archive and
    multi-year NOAA exceeds the request timeout, so return 202 and let it run."""
    background.add_task(ingest_timeseries.backfill_all, years_back)
    return {"status": "accepted", "job": "backfill", "years_back": years_back}


@router.post("/api/timeseries/refresh", status_code=202)
def refresh(
    background: BackgroundTasks, days: int = 7, _: None = Depends(require_api_key)
) -> Dict[str, Any]:
    background.add_task(ingest_timeseries.refresh_recent, days)
    return {"status": "accepted", "job": "refresh", "days": days}
