"""Private field journal — per-user observations, notes, and trip plans."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import ReviewerIdentity, require_api_key, require_signed_in
from ..journal import build_journal_store
from ..models import CommunitySubmission, CommunitySubmissionStatus, JournalEntry, JournalEntryKind, utc_now
from ..state import storage
from ..storage import model_to_dict

# require_api_key at the router level closes the public-tunnel bypass: the backend
# is directly reachable, and require_signed_in only checks a spoofable
# X-ORCAST-Reviewer-Id header. The Vercel proxy injects X-ORCAST-Key on every
# forwarded request, so the signed-in path is unaffected; direct callers without
# the server-side key get 401 before reviewer logic runs.
router = APIRouter(dependencies=[Depends(require_api_key)])
_journal = build_journal_store()

_ALLOWED_BEHAVIORS = {"feeding", "traveling", "socializing", "resting", "unknown"}


class JournalEntryRequest(BaseModel):
    kind: JournalEntryKind = JournalEntryKind.OBSERVATION
    title: str = Field(min_length=1, max_length=200)
    place: Optional[str] = Field(default=None, max_length=200)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    observed_at: Optional[datetime] = None
    body: Optional[str] = Field(default=None, max_length=4000)
    behavior: str = "unknown"
    count: Optional[int] = None
    evidence_assets: list = Field(default_factory=list)  # list of EvidenceAsset dicts


@router.get("/api/journal/entries")
def list_journal_entries(
    identity: ReviewerIdentity = Depends(require_signed_in),
) -> Dict[str, Any]:
    user_id = identity.reviewer_id or ""
    entries = _journal.list_entries(user_id)
    return {
        "status": "success",
        "total_count": len(entries),
        "entries": [model_to_dict(e) for e in entries],
    }


@router.post("/api/journal/entries")
def create_journal_entry(
    payload: JournalEntryRequest,
    identity: ReviewerIdentity = Depends(require_signed_in),
) -> Dict[str, Any]:
    user_id = identity.reviewer_id or ""
    behavior = payload.behavior if payload.behavior in _ALLOWED_BEHAVIORS else "unknown"
    entry = JournalEntry(
        id=uuid4().hex,
        user_id=user_id,
        user_email=identity.reviewer_email,
        kind=payload.kind,
        title=payload.title.strip(),
        place=payload.place,
        latitude=payload.latitude,
        longitude=payload.longitude,
        observed_at=payload.observed_at,
        body=payload.body,
        behavior=behavior,
        count=payload.count,
        evidence_assets=payload.evidence_assets or [],
    )
    _journal.put_entry(entry)
    return {"status": "success", "entry": model_to_dict(entry)}


@router.post("/api/journal/entries/{entry_id}/publish")
def publish_journal_entry(
    entry_id: str,
    identity: ReviewerIdentity = Depends(require_signed_in),
) -> Dict[str, Any]:
    """Copy a private journal entry into the public moderation queue."""
    user_id = identity.reviewer_id or ""
    entry = _journal.get_entry(user_id, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    if entry.community_submission_id:
        return {
            "status": "success",
            "already_published": True,
            "community_submission_id": entry.community_submission_id,
        }

    if not entry.place and not (entry.latitude and entry.longitude):
        raise HTTPException(
            status_code=422,
            detail="Add a place name or map coordinates before publishing to community.",
        )
    observed_at = entry.observed_at or entry.created_at
    submission = CommunitySubmission(
        id=uuid4().hex,
        place=entry.place or f"{entry.latitude:.4f}, {entry.longitude:.4f}",
        latitude=entry.latitude,
        longitude=entry.longitude,
        observed_at=observed_at,
        behavior=entry.behavior,
        count=entry.count,
        notes=(entry.body or entry.title)[:2000],
        observer_name=identity.reviewer_email or identity.display_name,
        status=CommunitySubmissionStatus.PENDING,
        evidence_assets=list(entry.evidence_assets),
    )
    storage.put_community_submission(submission)
    entry.community_submission_id = submission.id
    entry.updated_at = utc_now()
    _journal.update_entry(entry)
    return {
        "status": "success",
        "entry": model_to_dict(entry),
        "community_submission": model_to_dict(submission),
    }
