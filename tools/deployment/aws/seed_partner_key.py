#!/usr/bin/env python3
"""Seed a builder-tier partner API key in DynamoDB (hashed at rest)."""

from __future__ import annotations

import argparse
import hashlib
import os
import secrets
import sys

import boto3


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed orcast partner API key in DynamoDB")
    parser.add_argument("--table", default=os.getenv("ORCAST_PARTNER_KEYS_TABLE", "orcast-partner-api-keys"))
    parser.add_argument("--region", default=os.getenv("AWS_REGION", "us-west-2"))
    parser.add_argument("--tier", default="builder", choices=["free", "builder", "pro"])
    parser.add_argument("--owner", default="orcast-dev")
    parser.add_argument("--key", help="Raw key to store (generated if omitted)")
    args = parser.parse_args()

    raw_key = args.key or f"orcast_{args.tier}_{secrets.token_urlsafe(24)}"
    key_hash = _hash_key(raw_key)
    key_id = f"partner_{secrets.token_hex(6)}"

    table = boto3.resource("dynamodb", region_name=args.region).Table(args.table)
    table.put_item(
        Item={
            "pk": f"hash#{key_hash}",
            "key_id": key_id,
            "tier": args.tier,
            "owner": args.owner,
            "active": True,
        }
    )
    print(f"Seeded key_id={key_id} tier={args.tier}")
    print(f"ORCAST_PARTNER_DEV_KEY={raw_key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
