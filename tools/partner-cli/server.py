#!/usr/bin/env python3
"""Minimal partner CLI for orcast external endpoints.

Usage:
  export ORCAST_WEB_BASE=https://orcast-h0.vercel.app
  export ORCAST_PARTNER_KEY=orcast_builder_dev
  python3 tools/mcp-orcast/server.py get_gates
  python3 tools/mcp-orcast/server.py check_sighting --place "Lime Kiln" --observed_at 2026-06-19T12:00:00Z
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def _base() -> str:
    return os.environ.get("ORCAST_WEB_BASE", "https://orcast-h0.vercel.app").rstrip("/")


def _key() -> str:
    key = os.environ.get("ORCAST_PARTNER_KEY") or os.environ.get("ORCAST_PARTNER_DEV_KEY", "")
    if not key:
        raise SystemExit("Set ORCAST_PARTNER_KEY")
    return key


def _request(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{_base()}/api/v1/{path.lstrip('/')}"
    data = None
    headers = {"X-ORCAST-Partner-Key": _key(), "Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        raise SystemExit(f"{exc.code} {detail}") from exc


def cmd_get_gates(_: argparse.Namespace) -> None:
    print(json.dumps(_request("GET", "api/gates"), indent=2))


def cmd_get_provenance(_: argparse.Namespace) -> None:
    print(json.dumps(_request("GET", "api/provenance"), indent=2))


def cmd_check_sighting(args: argparse.Namespace) -> None:
    payload = {
        "place": args.place,
        "observed_at": args.observed_at,
        "behavior": args.behavior or "",
    }
    print(json.dumps(_request("POST", "api/sighting-assist", payload), indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="orcast partner CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("get_gates").set_defaults(func=cmd_get_gates)
    sub.add_parser("get_provenance").set_defaults(func=cmd_get_provenance)

    sighting = sub.add_parser("check_sighting")
    sighting.add_argument("--place", required=True)
    sighting.add_argument("--observed_at", required=True)
    sighting.add_argument("--behavior", default="")
    sighting.set_defaults(func=cmd_check_sighting)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
