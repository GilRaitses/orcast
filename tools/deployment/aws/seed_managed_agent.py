#!/usr/bin/env python3
"""Seed Central Casting managed agents in DynamoDB."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import boto3

REPO_ROOT = Path(__file__).resolve().parents[3]
SEEDS_DIR = REPO_ROOT / "src/aws_backend/casting/seeds"
DEFAULT_SEEDS = (
    "explore-guide-v1.json",
    "surface-planner-v1.json",
    "dossier-explainer-v1.json",
    "promotion-clerk-v1.json",
)


def seed_agent(table, agent, *, region: str) -> None:
    table.put_item(
        Item={
            "agent_id": agent.id,
            "version": agent.version,
            "instructions": agent.instructions,
            "skills": agent.skills,
            "data_bindings": agent.data_bindings,
            "model": agent.model,
            "policy": {
                "write_tools": agent.policy.write_tools,
                "allowed_deep_links": agent.policy.allowed_deep_links,
                "allowed_panels": agent.policy.allowed_panels,
                "planner_mode": agent.policy.planner_mode,
            },
            "active": agent.active,
            "spec_hash": agent.spec_hash(),
        }
    )
    print(f"Seeded managed agent id={agent.id} version={agent.version} spec_hash={agent.spec_hash()}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed managed agents in DynamoDB")
    parser.add_argument(
        "--table",
        default=os.getenv("ORCAST_MANAGED_AGENTS_TABLE", "orcast-aws-backend-managed-agents"),
    )
    parser.add_argument("--region", default=os.getenv("AWS_REGION", "us-west-2"))
    parser.add_argument("--seed", action="append", help="Path to agent JSON seed (repeatable)")
    parser.add_argument("--all", action="store_true", help="Seed all default cast roles")
    args = parser.parse_args()

    sys.path.insert(0, str(REPO_ROOT))
    from src.aws_backend.casting.models import ManagedAgent

    seeds: list[Path] = []
    if args.seed:
        seeds = [Path(s) for s in args.seed]
    elif args.all:
        seeds = [SEEDS_DIR / name for name in DEFAULT_SEEDS]
    else:
        seeds = [SEEDS_DIR / "explore-guide-v1.json"]

    table = boto3.resource("dynamodb", region_name=args.region).Table(args.table)
    for path in seeds:
        data = json.loads(path.read_text(encoding="utf-8"))
        seed_agent(table, ManagedAgent.from_dict(data), region=args.region)
    return 0


if __name__ == "__main__":
    sys.exit(main())
