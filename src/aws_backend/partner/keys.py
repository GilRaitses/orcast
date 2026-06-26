"""Partner API key registry and tier limits."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from typing import Dict, Optional

from ..config import Settings, settings

TIERS: Dict[str, Dict[str, int | bool]] = {
    "free": {"daily_limit": 100, "sighting_assist": False},
    "builder": {"daily_limit": 1000, "sighting_assist": True},
    "pro": {"daily_limit": 10000, "sighting_assist": True},
}


@dataclass(frozen=True)
class PartnerKey:
    key_id: str
    tier: str
    owner: str
    active: bool = True


class PartnerKeyStore:
    def verify(self, raw_key: str) -> Optional[PartnerKey]:
        ...

    def record_use(self, key_id: str) -> None:
        ...


class MemoryPartnerKeyStore(PartnerKeyStore):
    def __init__(self, seed_key: str = "orcast_partner_dev_key", tier: str = "builder") -> None:
        self._hash = _hash_key(seed_key)
        self._meta = PartnerKey(key_id="partner_dev", tier=tier, owner="dev")
        self._usage: Dict[str, int] = {}

    def verify(self, raw_key: str) -> Optional[PartnerKey]:
        if secrets.compare_digest(_hash_key(raw_key), self._hash):
            return self._meta
        return None

    def record_use(self, key_id: str) -> None:
        self._usage[key_id] = self._usage.get(key_id, 0) + 1


class AwsPartnerKeyStore(PartnerKeyStore):
    def __init__(self, cfg: Settings = settings) -> None:
        import boto3

        self.table = boto3.resource("dynamodb", region_name=cfg.aws_region).Table(cfg.partner_keys_table)

    def verify(self, raw_key: str) -> Optional[PartnerKey]:
        key_hash = _hash_key(raw_key)
        response = self.table.get_item(Key={"pk": f"hash#{key_hash}"})
        item = response.get("Item")
        if not item or not item.get("active", True):
            return None
        return PartnerKey(
            key_id=str(item.get("key_id", "")),
            tier=str(item.get("tier", "free")),
            owner=str(item.get("owner", "")),
        )

    def record_use(self, key_id: str) -> None:
        from datetime import datetime, timezone

        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.table.update_item(
            Key={"pk": f"usage#{key_id}#{day}"},
            UpdateExpression="ADD request_count :one",
            ExpressionAttributeValues={":one": 1},
        )


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def build_partner_key_store(cfg: Settings = settings) -> PartnerKeyStore:
    if cfg.storage_backend.lower() == "aws":
        return AwsPartnerKeyStore(cfg)
    return MemoryPartnerKeyStore()


def tier_allows_sighting_assist(tier: str) -> bool:
    return bool(TIERS.get(tier, TIERS["free"]).get("sighting_assist"))


def tier_daily_limit(tier: str) -> int:
    return int(TIERS.get(tier, TIERS["free"])["daily_limit"])
