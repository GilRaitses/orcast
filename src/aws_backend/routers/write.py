from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends

from ..auth import require_api_key
from ..scoring import generate_hotspots
from ..state import run_ingestion, storage
from ..storage import model_to_dict

router = APIRouter()


@router.post("/api/sightings/ingest")
def ingest_sightings(include_live: bool = True, _: None = Depends(require_api_key)) -> Dict[str, Any]:
    run = run_ingestion(include_live=include_live)
    return model_to_dict(run)


@router.post("/api/hotspots/recompute")
def recompute_hotspots(_: None = Depends(require_api_key)) -> Dict[str, Any]:
    hotspots = generate_hotspots(storage.list_sightings(limit=10_000))
    storage.put_hotspots(hotspots)
    return {"status": "success", "total_count": len(hotspots), "hotspots": [model_to_dict(h) for h in hotspots]}
