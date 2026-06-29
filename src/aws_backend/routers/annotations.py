"""DTAG annotation write API (studio-live-persistence, STU-B).

Net-new authenticated persistence for the annotation studio. The client store
``HttpAnnotationStore`` already POSTs the ``AnnotationSubmissionRequest`` shape
to ``/api/dtag/annotations`` and reads back the full ``Annotation`` on list and
get. This router conforms to that wire schema. It does not edit the read-only
``dtag.py`` surface; it reuses ``dtag._load_deployments`` read-only to validate
the target deployment and read its simulated flag.

Authorization (locked, not public):
- Router-level ``require_api_key`` closes the direct-backend bypass, the same
  pattern ``journal.py`` uses. A keyless direct caller is rejected before any
  reviewer logic runs.
- Writes also require ``require_trusted_reviewer``; reads require
  ``require_signed_in``.

Security posture (P0 and P1 built in from the start):
- Identity is server-stamped. ``annotator_id`` is the verified WorkOS reviewer
  id (never the email), ``annotator_role`` is the verified role, and ``source``
  is pinned to ``community``. The request body's identity fields are ignored.
- ``dataset``, ``license_status``, ``tool``, and ``h5_refs`` are pinned from the
  deployment record or server constants, so the client cannot spoof provenance.
- Unknown ``deployment_id`` is rejected; ``simulated`` is stamped from the
  deployment record so an annotation stays labeled simulated end to end.
- Inputs are enum- and length-validated; reads return an explicit field
  allow-list that never exposes a reviewer email; writes are rate-limited per
  reviewer id.
"""

from __future__ import annotations

import hashlib
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ..annotations import build_annotation_store
from ..annotations.store import StoredAnnotation
from ..auth import (
    ReviewerIdentity,
    require_api_key,
    require_signed_in,
    require_trusted_reviewer,
)
from ..models import utc_now
from .dtag import _load_deployments

router = APIRouter(dependencies=[Depends(require_api_key)])
_store = build_annotation_store()

# Pinned server constants. The annotation tool id matches the client constant in
# web/lib/annotation/provenance.ts so the round-trip provenance is consistent.
ANNOTATION_TOOL = "bss-annotation-studio-v1"
_DIVE_H5_REFS = [
    "depth/values",
    "dives/dive_indices",
    "analysis/animal_frame_metrics/odba",
]

_ALLOWED_TARGET_KINDS = {"dive", "time_range"}
_ALLOWED_METHODS = {"manual", "derived"}

# Recognized expert/researcher role tiers. source is derived server-side from the
# verified ReviewerIdentity.reviewer_role, never from the request body, and is
# never "model" for a human annotation. The trusted proxy currently stamps only
# the constant role "reviewer" (see web/lib/agentAuth.ts reviewerProxyHeaders), so
# in practice source pins to "community" today. This set is the expert-mapping
# hook for when a real role tier lands.
_EXPERT_ROLES = {"expert", "researcher", "scientist", "biologist"}


def _derive_source(identity: ReviewerIdentity) -> str:
    role = (identity.reviewer_role or "").strip().lower()
    return "expert" if role in _EXPERT_ROLES else "community"


# Lowercase slug: a leading alphanumeric then up to 63 of [a-z0-9_-]. Blocks
# whitespace, control chars, markup, and expression syntax in label fields.
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")

_LIST_LIMIT_DEFAULT = 100
_LIST_LIMIT_MAX = 500

# In-process write rate limit keyed on reviewer id (best-effort, per backend
# process). Authenticated annotation writes are not covered by the proxy's
# public-path limiter, so the write surface caps itself.
_WRITE_RATE_LIMIT = 30
_WRITE_RATE_WINDOW_S = 60.0
_write_buckets: Dict[str, Tuple[int, float]] = {}


def _rate_limited(reviewer_id: str) -> bool:
    now = time.monotonic()
    bucket = _write_buckets.get(reviewer_id)
    if bucket is None or now >= bucket[1]:
        _write_buckets[reviewer_id] = (1, now + _WRITE_RATE_WINDOW_S)
        return False
    count = bucket[0] + 1
    _write_buckets[reviewer_id] = (count, bucket[1])
    return count > _WRITE_RATE_LIMIT


def _dedup_key(reviewer_id: str, deployment_id: str, start: int, end: int, behavior: str) -> str:
    raw = f"{reviewer_id}|{deployment_id}|{start}|{end}|{behavior}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


class TargetModel(BaseModel):
    kind: str = Field(max_length=32)
    dive_id: Optional[int] = Field(default=None, ge=0)
    start_sample: int = Field(ge=0)
    end_sample: int = Field(ge=0)


class ProvenanceInput(BaseModel):
    # The client sends these. Identity, authority, and license fields are ignored
    # and re-derived server-side. Length caps bound the parsed request body. Only
    # ``method`` is read from the body.
    source: Optional[str] = Field(default=None, max_length=32)
    annotator_id: Optional[str] = Field(default=None, max_length=128)
    annotator_role: Optional[str] = Field(default=None, max_length=64)
    method: Optional[str] = Field(default=None, max_length=32)
    dataset: Optional[str] = Field(default=None, max_length=128)
    h5_refs: List[str] = Field(default_factory=list, max_length=64)
    license_status: Optional[str] = Field(default=None, max_length=64)
    tool: Optional[str] = Field(default=None, max_length=64)


class AnnotationCreateRequest(BaseModel):
    deployment_id: str = Field(min_length=1, max_length=128)
    target: TargetModel
    behavior: str = Field(min_length=1, max_length=64)
    state: Optional[str] = Field(default=None, max_length=64)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    notes: Optional[str] = Field(default=None, max_length=2000)
    provenance: ProvenanceInput = Field(default_factory=ProvenanceInput)


def _to_wire(record: StoredAnnotation) -> Dict[str, Any]:
    """Explicit read DTO allow-list. Never leaks a reviewer email or the
    server-only dedup key, and returns the full client ``Annotation`` shape."""
    target: Dict[str, Any] = {
        "kind": record.target["kind"],
        "start_sample": record.target["start_sample"],
        "end_sample": record.target["end_sample"],
    }
    if record.target.get("dive_id") is not None:
        target["dive_id"] = record.target["dive_id"]

    wire: Dict[str, Any] = {
        "id": record.id,
        "target": target,
        "behavior": record.behavior,
        "provenance": {
            "dataset": record.provenance["dataset"],
            "deployment_id": record.provenance["deployment_id"],
            "source": record.provenance["source"],
            "annotator_id": record.provenance["annotator_id"],
            "annotator_role": record.provenance["annotator_role"],
            "method": record.provenance["method"],
            "h5_refs": list(record.provenance["h5_refs"]),
            "license_status": record.provenance["license_status"],
            "tool": record.provenance["tool"],
            "created_at": record.provenance["created_at"],
        },
        "simulated": record.simulated,
    }
    if record.state is not None:
        wire["state"] = record.state
    if record.confidence is not None:
        wire["confidence"] = record.confidence
    if record.notes is not None:
        wire["notes"] = record.notes
    return wire


@router.post("/api/dtag/annotations")
def create_annotation(
    payload: AnnotationCreateRequest,
    identity: ReviewerIdentity = Depends(require_trusted_reviewer),
) -> Dict[str, Any]:
    # The target deployment must exist. Reject unknown ids so an annotation can
    # never orphan or attach to a fabricated deployment.
    entry = _load_deployments().get(payload.deployment_id)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail="Unknown deployment_id. DTAG data is partnership-gated.",
        )

    if payload.target.kind not in _ALLOWED_TARGET_KINDS:
        raise HTTPException(status_code=422, detail="invalid target.kind")
    if payload.target.end_sample < payload.target.start_sample:
        raise HTTPException(status_code=422, detail="end_sample before start_sample")
    if not _SLUG_RE.match(payload.behavior):
        raise HTTPException(status_code=422, detail="invalid behavior")
    if payload.state is not None and not _SLUG_RE.match(payload.state):
        raise HTTPException(status_code=422, detail="invalid state")
    method = (payload.provenance.method or "manual").lower()
    if method not in _ALLOWED_METHODS:
        raise HTTPException(status_code=422, detail="invalid method")

    reviewer_id = identity.reviewer_id or ""
    if _rate_limited(reviewer_id):
        raise HTTPException(status_code=429, detail="annotation write rate limit exceeded")

    simulated = bool(entry["simulated"])
    # P0: identity is the verified reviewer, never the request body. The opaque
    # WorkOS id is stored; the email is never persisted.
    annotator_id = reviewer_id
    annotator_role = identity.reviewer_role or "community"
    source = _derive_source(identity)
    # P1: provenance authority fields pinned from the record / server constants.
    dataset = payload.deployment_id
    # "simulated-example" is the honest label for the simulated bundled deployment.
    # When real partnership-gated deployments land, each must carry its actual
    # data-sharing-agreement license string here (future, out of scope now).
    license_status = "simulated-example" if simulated else "partner-supplied"
    h5_refs = list(_DIVE_H5_REFS) if payload.target.kind == "dive" else []
    created_at = utc_now().isoformat()

    dedup_key = _dedup_key(
        annotator_id,
        payload.deployment_id,
        payload.target.start_sample,
        payload.target.end_sample,
        payload.behavior,
    )

    record = StoredAnnotation(
        id=uuid4().hex,
        deployment_id=payload.deployment_id,
        dedup_key=dedup_key,
        simulated=simulated,
        target={
            "kind": payload.target.kind,
            "dive_id": payload.target.dive_id,
            "start_sample": payload.target.start_sample,
            "end_sample": payload.target.end_sample,
        },
        behavior=payload.behavior,
        state=payload.state,
        confidence=payload.confidence,
        notes=payload.notes,
        provenance={
            "dataset": dataset,
            "deployment_id": payload.deployment_id,
            "source": source,
            "annotator_id": annotator_id,
            "annotator_role": annotator_role,
            "method": method,
            "h5_refs": h5_refs,
            "license_status": license_status,
            "tool": ANNOTATION_TOOL,
            "created_at": created_at,
        },
        created_at=created_at,
    )

    stored, created = _store.create(record)
    return {
        "id": stored.id,
        "status": "created" if created else "duplicate",
        "simulated": stored.simulated,
    }


@router.get("/api/dtag/annotations")
def list_annotations(
    deployment_id: str = Query(..., min_length=1, max_length=128),
    limit: int = Query(default=_LIST_LIMIT_DEFAULT, ge=1, le=_LIST_LIMIT_MAX),
    identity: ReviewerIdentity = Depends(require_signed_in),
) -> List[Dict[str, Any]]:
    rows = _store.list_for_deployment(deployment_id, limit=limit)
    return [_to_wire(r) for r in rows]


@router.get("/api/dtag/annotations/{annotation_id}")
def get_annotation(
    annotation_id: str,
    identity: ReviewerIdentity = Depends(require_signed_in),
) -> Dict[str, Any]:
    record = _store.get(annotation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="annotation not found")
    return _to_wire(record)
