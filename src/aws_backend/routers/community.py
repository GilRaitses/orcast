from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from ..auth import require_api_key
from ..models import CommunitySubmission, CommunitySubmissionStatus
from ..state import storage
from ..storage import model_to_dict

router = APIRouter()

_ALLOWED_BEHAVIORS = {"feeding", "traveling", "socializing", "resting", "unknown"}


class CommunitySightingRequest(BaseModel):
    place: str = Field(max_length=200)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    observed_at: datetime
    behavior: str = "unknown"
    count: Optional[int] = None
    notes: Optional[str] = Field(default=None, max_length=2000)
    observer_name: Optional[str] = Field(default=None, max_length=120)
    website: Optional[str] = None


class CommunityReviewRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@router.post("/api/community/sightings", status_code=status.HTTP_201_CREATED)
def submit_community_sighting(payload: CommunitySightingRequest, response: Response) -> Dict[str, Any]:
    if payload.website:
        response.status_code = status.HTTP_200_OK
        return {"status": "ok"}

    behavior = payload.behavior if payload.behavior in _ALLOWED_BEHAVIORS else "unknown"
    submission = CommunitySubmission(
        id=uuid4().hex,
        place=payload.place,
        latitude=payload.latitude,
        longitude=payload.longitude,
        observed_at=payload.observed_at,
        behavior=behavior,
        count=payload.count,
        notes=payload.notes,
        observer_name=payload.observer_name,
        status=CommunitySubmissionStatus.PENDING,
    )
    storage.put_community_submission(submission)
    return {"id": submission.id, "status": submission.status.value}


@router.get("/api/community/submissions")
def list_community_submissions(
    status: Optional[str] = Query(default=None),
    _: None = Depends(require_api_key),
) -> Dict[str, Any]:
    submissions = storage.list_community_submissions(status=status)
    return {
        "status": "success",
        "total_count": len(submissions),
        "submissions": [model_to_dict(s) for s in submissions],
    }


@router.post("/api/community/submissions/{submission_id}/approve")
def approve_community_submission(
    submission_id: str,
    payload: Optional[CommunityReviewRequest] = None,
    _: None = Depends(require_api_key),
) -> Dict[str, Any]:
    latitude = payload.latitude if payload else None
    longitude = payload.longitude if payload else None
    updated = storage.update_community_submission_status(
        submission_id,
        CommunitySubmissionStatus.APPROVED.value,
        latitude=latitude,
        longitude=longitude,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    return model_to_dict(updated)


@router.post("/api/community/submissions/{submission_id}/reject")
def reject_community_submission(
    submission_id: str,
    _: None = Depends(require_api_key),
) -> Dict[str, Any]:
    updated = storage.update_community_submission_status(
        submission_id,
        CommunitySubmissionStatus.REJECTED.value,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    return model_to_dict(updated)
