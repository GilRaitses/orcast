#!/usr/bin/env python3
"""End-to-end smoke test for protected orcast layers via the Vercel proxy agent key."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
CREDS_FILE = REPO_ROOT / ".agent-credentials.env"


def load_creds() -> dict[str, str]:
    if CREDS_FILE.exists():
        creds: dict[str, str] = {}
        for line in CREDS_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            creds[k.strip()] = v.strip()
        return creds
    return {
        "ORCAST_AGENT_KEY": os.environ.get("ORCAST_AGENT_KEY", ""),
        "ORCAST_WEB_BASE": os.environ.get("ORCAST_WEB_BASE", "https://orcast-h0.vercel.app"),
        "ORCAST_AGENT_REVIEWER_ID": os.environ.get("ORCAST_AGENT_REVIEWER_ID", "agent_orcast_automation"),
        "ORCAST_AGENT_REVIEWER_EMAIL": os.environ.get("ORCAST_AGENT_REVIEWER_EMAIL", "agent@orcast.dev"),
    }


def agent_headers(key: str) -> dict[str, str]:
    return {"Content-Type": "application/json", "X-ORCAST-Agent-Key": key}


def proxy(base: str, path: str) -> str:
    return f"{base.rstrip('/')}/api/be/{path.lstrip('/')}"


def main() -> int:
    parser = argparse.ArgumentParser(description="orcast agent smoke test")
    parser.add_argument("--dry-run", action="store_true", help="Read-only checks; skip journal publish mutations")
    args = parser.parse_args()

    creds = load_creds()
    key = creds.get("ORCAST_AGENT_KEY", "")
    base = creds.get("ORCAST_WEB_BASE", "https://orcast-h0.vercel.app")
    if not key:
        print("Missing ORCAST_AGENT_KEY. Run: bash tools/testing/setup_agent_user.sh", file=sys.stderr)
        return 1

    h = agent_headers(key)
    failures: list[str] = []

    def check(name: str, resp: requests.Response, expect: int = 200) -> dict[str, Any] | None:
        if resp.status_code != expect:
            failures.append(f"{name}: HTTP {resp.status_code} {resp.text[:200]}")
            return None
        try:
            return resp.json()
        except json.JSONDecodeError:
            failures.append(f"{name}: invalid JSON")
            return None

    print(f"Agent smoke against {base}")

    # Protected reads
    journal = check("journal list", requests.get(proxy(base, "api/journal/entries"), headers=h, timeout=30))
    if journal is not None:
        print(f"  journal entries: {journal.get('total_count', 0)}")

    moderation = check(
        "moderation queue",
        requests.get(proxy(base, "api/community/submissions?status=pending"), headers=h, timeout=30),
    )
    if moderation is not None:
        print(f"  pending submissions: {moderation.get('total_count', 0)}")

    dossier = check("review dossier", requests.get(proxy(base, "api/review-dossier/latest"), headers=h, timeout=30))
    if dossier is not None:
        print(f"  dossier stage: {dossier.get('dossier', {}).get('workflow_stage')}")

    decisions = check("decision records", requests.get(proxy(base, "api/decision-records"), headers=h, timeout=30))
    if decisions is not None:
        print(f"  decision records: {decisions.get('total_count', 0)}")

    # Journal write + publish
    create = check(
        "journal create",
        requests.post(
            proxy(base, "api/journal/entries"),
            headers=h,
            json={
                "title": "Agent probe sighting",
                "place": "Lime Kiln Point",
                "body": "Automated agent smoke test entry.",
                "behavior": "traveling",
                "kind": "observation",
            },
            timeout=30,
        ),
    )
    entry_id = create.get("entry", {}).get("id") if create else None
    if entry_id and not args.dry_run:
        print(f"  created journal entry: {entry_id[:8]}…")
        pub = check(
            "journal publish",
            requests.post(proxy(base, f"api/journal/entries/{entry_id}/publish"), headers=h, timeout=30),
        )
        if pub:
            sub_id = pub.get("community_submission", {}).get("id", "")
            print(f"  published to moderation: {sub_id[:8]}…")
    elif entry_id and args.dry_run:
        print(f"  dry-run: skipped publish for entry {entry_id[:8]}…")

    # Public layer still works
    sighting = check(
        "sighting assist",
        requests.post(
            proxy(base, "api/sighting-assist"),
            json={"message": "agent probe", "lat": 48.5, "lng": -123.0},
            timeout=60,
        ),
    )
    if sighting is not None:
        print(f"  sighting source: {sighting.get('source')}")

    sess = check(
        "explore session",
        requests.post(proxy(base, "api/explore/sessions"), json={"title": "agent plan smoke"}, timeout=30),
    )
    session_id = sess.get("session_id") if sess else None
    if session_id:
        plan = check(
            "surface planner (agent key)",
            requests.post(
                f"{base.rstrip('/')}/api/interactions/plan",
                headers=h,
                json={
                    "message": "Show gates and provenance for this region",
                    "agent_id": "surface-planner-v1",
                    "session_id": session_id,
                    "viewport": {"lat": 48.5465, "lng": -123.03, "zoom": 10},
                },
                timeout=90,
            ),
        )
        if plan is not None:
            panels = (plan.get("ui_intent") or {}).get("panels") or []
            print(f"  plan panels: {[p.get('id') for p in panels]}")

    if failures:
        print("\nFAILURES:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print("\nAgent smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
