"""Partner key verification (internal, for Vercel /api/v1 gateway)."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_api_key
from ..billing import billing_service
from ..partner import build_partner_key_store

router = APIRouter()
_store = build_partner_key_store()


@router.post("/api/partner/verify", dependencies=[Depends(require_api_key)])
def verify_partner_key(payload: Dict[str, Any]) -> Dict[str, Any]:
    raw = str(payload.get("key") or "")
    partner = _store.verify(raw)
    if partner is None:
        raise HTTPException(status_code=401, detail="Invalid partner key")
    return {"status": "success", "tier": partner.tier, "key_id": partner.key_id}


@router.get("/api/partner/tiers", dependencies=[Depends(require_api_key)])
def partner_tier_catalog() -> Dict[str, Any]:
    return {"status": "success", "tiers": billing_service.tier_catalog()}
