from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter()

_DEPRECATED = {
    "/api/predictions": "/api/reports/probability",
    "/api/behavioral-analysis": "/api/reports/probability",
    "/api/dtag-data": "/api/sightings",
}


def _gone_response(replacement: str) -> Dict[str, Any]:
    return {"deprecated": True, "replacement": replacement, "status": "gone"}


@router.get("/api/predictions")
def deprecated_predictions() -> Dict[str, Any]:
    from fastapi import HTTPException

    raise HTTPException(status_code=410, detail=_gone_response(_DEPRECATED["/api/predictions"]))


@router.get("/api/behavioral-analysis")
def deprecated_behavioral_analysis() -> Dict[str, Any]:
    from fastapi import HTTPException

    raise HTTPException(status_code=410, detail=_gone_response(_DEPRECATED["/api/behavioral-analysis"]))


@router.get("/api/dtag-data")
def deprecated_dtag_data() -> Dict[str, Any]:
    from fastapi import HTTPException

    raise HTTPException(status_code=410, detail=_gone_response(_DEPRECATED["/api/dtag-data"]))
