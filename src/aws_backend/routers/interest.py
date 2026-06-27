"""Interest / early-access signup with audience-aware, adaptive delivery.

POST /api/interest  {email, name?, audience?, interests?}

Two funnels, keyed off `audience`:
- research_partner: try the live tool + read the whitepapers; lead is captured so
  a pilot on their data/region can follow.
- visitor: early access to orcast Trips (San Juan Islands trip planning on an
  honest forecast) plus the live forecast.
- curious (default): the live forecast, whitepapers on request.

Everything offered is already live, so signup delivers the real links immediately
and a delivery email is composed and best-effort sent via SES.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel, field_validator

from ..config import settings
from ..state import storage

log = logging.getLogger(__name__)

router = APIRouter()

VALID_INTERESTS = {"early_access", "whitepapers", "demo"}
VALID_AUDIENCES = {"research_partner", "visitor", "curious"}


def _base() -> str:
    return os.getenv("ORCAST_PUBLIC_BASE", "https://orcast-h0.vercel.app").rstrip("/")


def _whitepapers() -> List[Dict[str, str]]:
    b = _base()
    return [
        {"title": "orcast: gate-bounded encounter forecasting", "url": b + "/papers/orcast_whitepaper.pdf"},
        {"title": "Output grounding for orchestrator-in-the-loop agents", "url": b + "/papers/orcast_grounding.pdf"},
    ]


def _links(audience: str, interests: List[str]) -> Dict[str, Any]:
    b = _base()
    out: Dict[str, Any] = {"app": b + "/"}
    want = set(interests)
    if audience == "research_partner" or "whitepapers" in want or audience == "curious":
        out["whitepapers"] = _whitepapers()
    if audience == "research_partner" or "demo" in want:
        out["demo"] = b + "/demo/orcast-demo.mp4"
    return out


def _confirmation(name: str, audience: str, links: Dict[str, Any]) -> str:
    who = f"Thanks, {name}. " if name else "Thanks. "
    app = links["app"]
    if audience == "research_partner":
        msg = who + (
            f"orcast is live and yours to try right now at {app}. I will follow up about "
            f"standing it up on your data or region. It shows only the confidence its evidence "
            f"earns, so every cell is auditable."
        )
        if links.get("whitepapers"):
            msg += " The two whitepapers: " + ", ".join(w["url"] for w in links["whitepapers"]) + "."
        return msg
    if audience == "visitor":
        return who + (
            f"You are on the early-access list for orcast Trips, San Juan Islands trip planning "
            f"built on an honest encounter forecast. Explore the live Salish Sea forecast now at {app}."
        )
    msg = who + f"orcast is live. Explore the gate-bounded Salish Sea forecast at {app}."
    if links.get("whitepapers"):
        msg += " Whitepapers: " + ", ".join(w["url"] for w in links["whitepapers"]) + "."
    return msg


def _email_subject(audience: str) -> str:
    if audience == "research_partner":
        return "Try orcast on your data"
    if audience == "visitor":
        return "Your orcast Trips early access"
    return "orcast is live"


def _email_body(name: str, audience: str, links: Dict[str, Any]) -> str:
    greeting = f"Hi {name}," if name else "Hi,"
    app = links["app"]
    lines: List[str] = [greeting, ""]
    if audience == "research_partner":
        lines += [
            "Thanks for the interest in orcast. It is live and you can use it now.",
            "",
            f"Try the live tool: {app}",
            "",
            "If you study Southern Resident killer whales or run a hydrophone network, I can",
            "stand up a gate-bounded forecast on your region or data. Reply and we will scope it.",
        ]
        if links.get("whitepapers"):
            lines += ["", "Whitepapers"]
            for w in links["whitepapers"]:
                lines.append(f"  {w['title']}: {w['url']}")
    elif audience == "visitor":
        lines += [
            "Thanks for joining the orcast Trips early-access list.",
            "",
            "orcast Trips is San Juan Islands trip planning built on an honest encounter forecast,",
            "one that shows what the evidence supports and where it is uncertain.",
            "",
            f"Explore the live forecast now: {app}",
            "You will hear from me as trip planning rolls out.",
        ]
    else:
        lines += [f"orcast is live. Explore the forecast: {app}"]
        if links.get("whitepapers"):
            lines += ["", "Whitepapers"]
            for w in links["whitepapers"]:
                lines.append(f"  {w['title']}: {w['url']}")
    lines += ["", "Reply with questions.", "Gil Raitses, aimez.ai"]
    return "\n".join(lines)


def _send_email(to_addr: str, subject: str, body: str) -> bool:
    sender = os.getenv("ORCAST_SES_SENDER", "").strip()
    if not sender:
        return False
    try:
        import boto3

        ses = boto3.client("ses", region_name=settings.aws_region)
        ses.send_email(
            Source=sender,
            Destination={"ToAddresses": [to_addr]},
            Message={"Subject": {"Data": subject}, "Body": {"Text": {"Data": body}}},
        )
        return True
    except Exception as exc:  # noqa: BLE001 - delivery is best-effort
        log.warning("interest delivery email failed (non-fatal): %s", exc)
        return False


class InterestSignup(BaseModel):
    email: str
    name: str = ""
    audience: str = "curious"
    interests: List[str] = []
    source: str = "orcast"

    @field_validator("email")
    @classmethod
    def email_ok(cls, v: str) -> str:
        v = v.strip().lower()
        if not v or "@" not in v:
            raise ValueError("valid email required")
        return v

    @field_validator("audience")
    @classmethod
    def audience_ok(cls, v: str) -> str:
        return v if v in VALID_AUDIENCES else "curious"

    @field_validator("interests")
    @classmethod
    def interests_ok(cls, v: List[str]) -> List[str]:
        return [i for i in v if i in VALID_INTERESTS]


@router.post("/api/interest")
def register_interest(payload: InterestSignup) -> Dict[str, Any]:
    ts = datetime.now(timezone.utc)
    links = _links(payload.audience, payload.interests)
    message = _confirmation(payload.name.strip(), payload.audience, links)
    subject = _email_subject(payload.audience)
    body = _email_body(payload.name.strip(), payload.audience, links)
    delivered = _send_email(payload.email, subject, body)

    record = {
        "email": payload.email,
        "name": payload.name,
        "audience": payload.audience,
        "interests": payload.interests,
        "source": payload.source,
        "created_at": ts.isoformat(),
        "email_delivered": delivered,
    }
    try:
        bucket = settings.raw_payload_bucket
        if hasattr(storage, "s3") and storage.s3 is not None:
            key = f"interest/{ts.strftime('%Y-%m-%d')}/{ts.strftime('%H%M%S')}_{hashlib.sha256(payload.email.encode()).hexdigest()[:12]}.json"
            storage.s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(record).encode(), ContentType="application/json")
            log.info("Interest signup stored: s3://%s/%s (audience=%s)", bucket, key, payload.audience)
        else:
            log.info("Interest signup (local/memory): %s audience=%s", payload.email, payload.audience)
    except Exception as exc:  # noqa: BLE001 - storage is best-effort
        log.warning("Interest signup storage failed (non-fatal): %s", exc)

    return {"status": "ok", "message": message, "links": links, "email_delivered": delivered}
