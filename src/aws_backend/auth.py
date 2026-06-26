from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException

from .config import settings


def _production_mode() -> bool:
    return settings.env not in ("local", "test", "development")


def require_api_key(x_orcast_key: str | None = Header(default=None, alias="X-ORCAST-Key")) -> None:
    """Require X-ORCAST-Key on keyed routes (always in production)."""
    if _production_mode():
        if not settings.api_key:
            raise HTTPException(status_code=503, detail="ORCAST_API_KEY is not configured")
        if x_orcast_key != settings.api_key:
            raise HTTPException(status_code=401, detail="Invalid or missing X-ORCAST-Key header")
        return
    if not settings.api_key:
        return
    if x_orcast_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing X-ORCAST-Key header")


@dataclass(frozen=True)
class ReviewerIdentity:
    reviewer_id: str | None = None
    reviewer_email: str | None = None
    reviewer_role: str | None = None

    @property
    def display_name(self) -> str:
        return self.reviewer_email or self.reviewer_id or "unknown"


def reviewer_identity(
    reviewer_id: str | None = Header(default=None, alias="X-ORCAST-Reviewer-Id"),
    reviewer_email: str | None = Header(default=None, alias="X-ORCAST-Reviewer-Email"),
    reviewer_role: str | None = Header(default=None, alias="X-ORCAST-Reviewer-Role"),
) -> ReviewerIdentity:
    """Identity stamped by the trusted Vercel proxy after WorkOS auth."""
    return ReviewerIdentity(
        reviewer_id=reviewer_id,
        reviewer_email=reviewer_email,
        reviewer_role=reviewer_role,
    )


def require_signed_in(
    identity: ReviewerIdentity = Depends(reviewer_identity),
) -> ReviewerIdentity:
    """Require a WorkOS user id forwarded by the trusted proxy."""
    if not identity.reviewer_id:
        raise HTTPException(status_code=401, detail="Sign in required")
    return identity


def require_trusted_reviewer(
    identity: ReviewerIdentity = Depends(reviewer_identity),
    trusted_proxy: str | None = Header(default=None, alias="X-ORCAST-Trusted-Proxy"),
) -> ReviewerIdentity:
    """Governance writes must come through the Vercel proxy with a stamped reviewer."""
    if _production_mode() or settings.api_key:
        if trusted_proxy != "vercel":
            raise HTTPException(status_code=401, detail="Reviewer actions require trusted proxy")
    if not identity.reviewer_id:
        raise HTTPException(status_code=401, detail="Sign in required")
    return identity
