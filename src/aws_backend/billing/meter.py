"""Usage metering hooks for partner API billing (Stripe integration stub)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from ..partner.keys import PartnerKey, tier_daily_limit


@dataclass
class UsageMeter:
    key_id: str
    day: str
    count: int = 0


class BillingService:
    def check_quota(self, partner: PartnerKey, current_count: int) -> bool:
        return current_count < tier_daily_limit(partner.tier)

    def record_event(self, partner: PartnerKey, endpoint: str, units: int = 1) -> None:
        """Stripe meter hook — no-op until ORCAST_STRIPE_SECRET_KEY is configured."""
        _ = (partner, endpoint, units)

    def tier_catalog(self) -> Dict[str, Dict[str, object]]:
        from ..partner.keys import TIERS

        return {
            "free": {**TIERS["free"], "price_usd": 0},
            "builder": {**TIERS["builder"], "price_usd": 29},
            "pro": {**TIERS["pro"], "price_usd": None},
        }


billing_service = BillingService()
