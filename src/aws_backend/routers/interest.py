"""Interest / early-access signup with adaptive delivery.

POST /api/interest  {email, name?, interests?: [early_access|whitepapers|demo]}

Everything orcast offers is already live, so signup delivers immediately. The
response carries the real links for whatever the person asked for, and a delivery
email is composed and best-effort sent (skipped cleanly when no SES sender is
configured). The signup record is stored to S3 when available.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from ..config import settings
from ..state import storage

log = logging.getLogger(__name__)

router = APIRouter()

VALID_INTERESTS = {"early_access", "whitepapers", "demo"}


def _public_base() -> str:
    return os.getenv("ORCAST_PUBLIC_BASE", "https://orcast-h0.vercel.app").rstrip("/")


def _links_for(interests: List[str]) -> Dict[str, Any]:
    base = _public_base()
    out: Dict[str, Any] = {}
    if "early_access" in interests:
        out["early_access"] = base + "/"
    if "whitepapers" in interests:
        out["whitepapers"] = [
            {"title": "orcast: gate-bounded encounter forecasting", "url": base + "/papers/orcast_whitepaper.pdf"},
            {"title": "Output grounding for orchestrator-in-the-loop agents", "url": base + "/papers/orcast_grounding.pdf"},
        ]
    if "demo" in interests:
        out["demo"] = base + "/demo/orcast-demo.mp4"
    return out


def _confirmation(name: str, interests: List[str], links: Dict[str, Any]) -> str:
    """Adaptive, all-ready confirmation. No 'you'll hear when ready' language."""
    who = f"Thanks, {name}. " if name else "Thanks. "
    if not interests:
        return who + "orcast is live now. Explore the gate-bounded forecast at " + _public_base() + "/."
    lines: List[str] = [who + "It is all live now, here is what you asked for."]
    if "early_access" in interests:
        lines.append(f"Early access: open the live app at {links['early_access']} and start exploring.")
    if "whitepapers" in interests:
        wp = ", ".join(w["url"] for w in links["whitepapers"])
        lines.append(f"Whitepapers: read them now at {wp}.")
    if "demo" in interests:
        lines.append(f"Demo: watch the narrated walkthrough at {links['demo']}.")
    return " ".join(lines)


def _email_subject(interests: List[str]) -> str:
    if interests == ["demo"]:
        return "Your orcast demo walkthrough"
    if interests == ["whitepapers"]:
        return "The orcast whitepapers"
    if interests == ["early_access"]:
        return "Your orcast early access is live"
    return "orcast is live, here is your access"


def _email_body(name: str, interests: List[str], links: Dict[str, Any]) -> str:
    """Plain-text delivery email. All content is live; nothing is pending."""
    greeting = f"Hi {name}," if name else "Hi,"
    blocks: List[str] = [greeting, ""]
    blocks.append("Thanks for your interest in orcast. Everything is live, so here is what you asked for.")
    blocks.append("")
    if "early_access" in interests:
        blocks.append("Early access")
        blocks.append(f"  Open the live app and explore the gate-bounded forecast: {links['early_access']}")
        blocks.append("")
    if "whitepapers" in interests:
        blocks.append("Whitepapers")
        for w in links["whitepapers"]:
            blocks.append(f"  {w['title']}: {w['url']}")
        blocks.append("")
    if "demo" in interests:
        blocks.append("Demo")
        blocks.append(f"  Narrated walkthrough of the live system: {links['demo']}")
        blocks.append("")
    if not interests:
        blocks.append(f"Start here: {_public_base()}/")
        blocks.append("")
    blocks.append("Reply to this email with questions.")
    blocks.append("Gil Raitses, aimez.ai")
    return "\n".join(blocks)


def _send_email(to_addr: str, subject: str, body: str) -> bool:
    """Best-effort SES send. Returns True if sent. Skips cleanly when no verified
    sender is configured (SES sandbox / setup pending), so signup never fails."""
    sender = os.getenv("ORCAST_SES_SENDER", "").strip()
    if not sender:
        return False
    try:
        import boto3

        ses = boto3.client("ses", region_name=settings.region)
        ses.send_email(
            Source=sender,
            Destination={"ToAddresses": [to_addr]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": body}},
            },
        )
        return True
    except Exception as exc:  # noqa: BLE001 - delivery is best-effort
        log.warning("interest delivery email failed (non-fatal): %s", exc)
        return False


class InterestSignup(BaseModel):
    email: str
    name: str = ""
    interests: List[str] = []
    source: str = "orcast"

    @field_validator("email")
    @classmethod
    def email_ok(cls, v: str) -> str:
        v = v.strip().lower()
        if not v or "@" not in v:
            raise ValueError("valid email required")
        return v

    @field_validator("interests")
    @classmethod
    def interests_ok(cls, v: List[str]) -> List[str]:
        return [i for i in v if i in VALID_INTERESTS]


@router.post("/api/interest")
def register_interest(payload: InterestSignup) -> Dict[str, Any]:
    ts = datetime.now(timezone.utc)
    links = _links_for(payload.interests)
    message = _confirmation(payload.name.strip(), payload.interests, links)
    subject = _email_subject(payload.interests)
    body = _email_body(payload.name.strip(), payload.interests, links)
    delivered = _send_email(payload.email, subject, body)

    record = {
        "email": payload.email,
        "name": payload.name,
        "interests": payload.interests,
        "source": payload.source,
        "created_at": ts.isoformat(),
        "email_delivered": delivered,
    }
    try:
        bucket = settings.raw_payload_bucket
        if hasattr(storage, "s3") and storage.s3 is not None:
            date_prefix = ts.strftime("%Y-%m-%d")
            key = f"interest/{date_prefix}/{ts.strftime('%H%M%S')}_{hashlib.sha256(payload.email.encode()).hexdigest()[:12]}.json"
            storage.s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(record).encode(), ContentType="application/json")
            log.info("Interest signup stored: s3://%s/%s", bucket, key)
        else:
            log.info("Interest signup (local/memory): %s interests=%s", payload.email, payload.interests)
    except Exception as exc:  # noqa: BLE001 - storage is best-effort
        log.warning("Interest signup storage failed (non-fatal): %s", exc)

    return {"status": "ok", "message": message, "links": links, "email_delivered": delivered}
