"""Interest / mailing list signup endpoint.

POST /api/interest  {email, name?}
Stores a JSON record to S3 under interest/{iso_date}/{timestamp}_{email_hash}.json
and returns 200. Works in local/memory mode (no-op write) and in production.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from ..config import settings
from ..state import storage

log = logging.getLogger(__name__)

router = APIRouter()


class InterestSignup(BaseModel):
    email: str
    name: str = ""
    source: str = "orcast"

    @field_validator("email")
    @classmethod
    def email_not_empty(cls, v: str) -> str:
        v = v.strip().lower()
        if not v or "@" not in v:
            raise ValueError("valid email required")
        return v


@router.post("/interest")
def register_interest(payload: InterestSignup):
    """Store an interest signup. Gracefully degrades if S3 is unavailable."""
    ts = datetime.now(timezone.utc)
    date_prefix = ts.strftime("%Y-%m-%d")
    stamp = ts.strftime("%H%M%S")
    email_hash = hashlib.sha256(payload.email.encode()).hexdigest()[:12]
    key = f"interest/{date_prefix}/{stamp}_{email_hash}.json"

    record = {
        "email": payload.email,
        "name": payload.name,
        "source": payload.source,
        "created_at": ts.isoformat(),
    }

    try:
        bucket = storage.raw_payload_bucket  # reuse existing bucket
        if hasattr(storage, "s3") and storage.s3 is not None:
            storage.s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=json.dumps(record).encode(),
                ContentType="application/json",
            )
            log.info("Interest signup stored: s3://%s/%s", bucket, key)
        else:
            log.info("Interest signup (local/memory, not persisted): %s", payload.email)
    except Exception as exc:
        log.warning("Interest signup storage failed (non-fatal): %s", exc)

    return {"status": "ok", "message": "Thanks — you'll hear from us when the papers are ready."}
