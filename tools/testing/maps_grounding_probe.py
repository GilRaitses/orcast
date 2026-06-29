#!/usr/bin/env python3
"""Probe + benchmark Google Maps grounding via the Gemini Interactions API.

Requires a Gemini API key from Google AI Studio (NOT the Maps JS key in DEPLOY_VERCEL.md).
The Maps JS key only enables map tiles and is referrer-restricted; grounding needs the
generativelanguage.googleapis.com Interactions API.

Usage:
    # Maps baseline (all 3 cases):
    python3 tools/testing/maps_grounding_probe.py

    # Single case:
    python3 tools/testing/maps_grounding_probe.py --case orca

    # Emit JSON + write baseline:
    python3 tools/testing/maps_grounding_probe.py --json --write-baseline

    # orcast-side uncited rate check (asserts orcast beats 85% Maps baseline):
    python3 tools/testing/maps_grounding_probe.py --orcast

    # Both (full benchmark comparison):
    python3 tools/testing/maps_grounding_probe.py --json --write-baseline --orcast

    # Skip if no key (CI-safe):
    python3 tools/testing/maps_grounding_probe.py --require-key
    # exits 0 with a note when key is missing
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
CREDS_FILE = REPO_ROOT / ".agent-credentials.env"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
API_REVISION = "2026-05-20"
MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
BASELINE_PATH = REPO_ROOT / "docs/devpost/figures/_demo-run/maps-grounding-baseline.json"

# San Juan Islands pilot region (same coords as orcast demo beats).
SAN_JUAN = {"latitude": 48.5465, "longitude": -123.03}

# Sentence-level markers of a scientific / quantitative claim (orcast's domain).
SCIENCE_MARKERS = re.compile(
    r"\b(NOAA|DFO|census|population|salmon|Chinook|hydrophone|bathymetr|"
    r"decline|study|studies|research|data|fisheries|pod|pods|p\s*=|"
    r"\d{4}|\d+\s*(?:%|percent|feet|ft|miles|mph|years?))\b",
    re.IGNORECASE,
)

CASES = {
    "place": "Is there a cafe with outdoor seating near Friday Harbor on San Juan Island?",
    "orca": (
        "Where along the west side of San Juan Island are southern resident "
        "killer whales most likely to be seen from shore, and what is the evidence?"
    ),
    "trip": (
        "Plan a shore-based whale watching afternoon near Lime Kiln Point. "
        "Include viewpoints, parking, and when orcas are most likely."
    ),
}

# Established Maps baseline from 2026-06-24 live run.
MAPS_BASELINE = {"uncited_rate": 85.0, "run_date": "2026-06-24"}


def load_creds() -> dict[str, str]:
    creds: dict[str, str] = {}
    if CREDS_FILE.exists():
        for line in CREDS_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            creds[k.strip()] = v.strip()
    return creds


def load_gemini_key() -> str:
    return os.environ.get("GEMINI_API_KEY") or load_creds().get("GEMINI_API_KEY", "")


def load_agent_key() -> str:
    return os.environ.get("ORCAST_AGENT_KEY") or load_creds().get("ORCAST_AGENT_KEY", "")


def load_web_base() -> str:
    return (
        os.environ.get("ORCAST_WEB_BASE")
        or load_creds().get("ORCAST_WEB_BASE", "https://orcast-h0.vercel.app")
    )


def run_maps_case(key: str, case: str) -> dict:
    prompt = CASES[case]
    resp = requests.post(
        ENDPOINT,
        headers={
            "x-goog-api-key": key,
            "Content-Type": "application/json",
            "Api-Revision": API_REVISION,
        },
        json={"model": MODEL, "input": prompt, "tools": [{"type": "google_maps", **SAN_JUAN}]},
        timeout=90,
    )
    return {"status": resp.status_code, "prompt": prompt, "body": resp.json()}


def parse_maps_result(result: dict) -> dict | None:
    body = result["body"]
    if isinstance(body, list):
        body = body[0] if body else {}
    if "error" in body:
        return None

    text_blocks, place_citations, step_types = [], [], []
    for step in body.get("steps", []) or []:
        step_types.append(step.get("type"))
        for block in step.get("content", []) or []:
            if block.get("type") == "text" and block.get("text"):
                text_blocks.append(block["text"])
            for ann in block.get("annotations", []) or []:
                if ann.get("type") in ("place_citation", "maps_citation"):
                    place_citations.append(
                        {"name": ann.get("name") or ann.get("title"), "url": ann.get("url")}
                    )

    full_text = "\n".join(text_blocks)
    place = sum(1 for c in place_citations if c.get("url") and (
        "maps.google" in c["url"] or "cid=" in c["url"]))
    scientific = len(place_citations) - place

    cited_names = {(c.get("name") or "").lower() for c in place_citations if c.get("name")}
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", full_text) if s.strip()]
    sci_sentences = [s for s in sentences if SCIENCE_MARKERS.search(s)]
    unsupported = [
        s for s in sci_sentences
        if not any(name and name in s.lower() for name in cited_names)
    ]
    rate = (len(unsupported) / len(sci_sentences) * 100) if sci_sentences else 0.0
    words = sum(len(t.split()) for t in text_blocks) or 1

    return {
        "case": result.get("case", "unknown"),
        "place": place,
        "scientific": scientific,
        "total_citations": len(place_citations),
        "density": round(len(place_citations) / words * 1000, 2),
        "sci_claims": len(sci_sentences),
        "unsupported": len(unsupported),
        "uncited_rate": round(rate, 1),
        "text_blocks": text_blocks,
        "place_citations": place_citations,
        "step_types": step_types,
    }


def print_maps_result(case: str, prompt: str, parsed: dict | None, error: str | None = None) -> None:
    print(f"\n=== prompt: {prompt}")
    if error:
        print(f"ERROR: {error}")
        return
    if parsed is None:
        print("ERROR: could not parse response")
        return
    print("--- model text ---")
    print("\n".join(parsed["text_blocks"]) or "(none)")
    print(f"--- step types: {parsed['step_types'] or '(none)'}")
    print(f"--- citations: {parsed['total_citations']} total "
          f"({parsed['place']} place, {parsed['scientific']} scientific/dataset)")
    for c in parsed.get("place_citations", []):
        print(f"    - {c['name']}: {c['url']}")
    print(f"--- grounding density: {parsed['total_citations']} citations / "
          f"{sum(len(t.split()) for t in parsed['text_blocks']) or 1} words "
          f"= {parsed['density']:.2f} per 1k words")
    print(f"--- scientific claims: {parsed['sci_claims']} sentences, "
          f"{parsed['unsupported']} unsupported = {parsed['uncited_rate']:.0f}% uncited evidence")


def run_orcast_check(agent_key: str, web_base: str) -> dict:
    """POST the adversarial orca prompt to orcast /api/interactions/plan and measure
    how many returned annotations carry an artifact or href (bound evidence)."""
    import uuid
    base = web_base.rstrip("/")

    # Create a session first.
    sess_resp = requests.post(
        f"{base}/api/be/api/explore/sessions",
        json={"title": "grounding benchmark"},
        headers={"X-ORCAST-Agent-Key": agent_key, "Content-Type": "application/json"},
        timeout=30,
    )
    if not sess_resp.ok:
        return {"error": f"session create {sess_resp.status_code}"}
    session_id = sess_resp.json().get("session_id", str(uuid.uuid4()))

    plan_resp = requests.post(
        f"{base}/api/interactions/plan",
        json={
            "session_id": session_id,
            "message": CASES["orca"],
            "agent_id": "surface-planner-v1",
            "viewport": {"lat": 48.5465, "lng": -123.03, "zoom": 10},
        },
        headers={"X-ORCAST-Agent-Key": agent_key, "Content-Type": "application/json"},
        timeout=90,
    )
    if not plan_resp.ok:
        return {"error": f"plan {plan_resp.status_code}: {plan_resp.text[:200]}"}

    data = plan_resp.json()
    annotations = (data.get("prepare") or {}).get("annotations") or []
    steps = (data.get("prepare") or {}).get("steps") or []
    panels = (data.get("ui_intent") or {}).get("panels") or []

    bound = sum(
        1 for a in annotations
        if (a.get("href") or a.get("artifact") and a["artifact"])
    )
    unbound = len(annotations) - bound
    rate = (unbound / len(annotations) * 100) if annotations else 0.0

    return {
        "session_id": session_id,
        "annotations": len(annotations),
        "bound": bound,
        "unbound": unbound,
        "uncited_rate": round(rate, 1),
        "panels": [p.get("id") for p in panels],
        "steps": len(steps),
        "skill_plan": (data.get("ui_intent") or {}).get("skill_plan") or [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=list(CASES) + ["all"], default="all")
    parser.add_argument("--json", action="store_true", dest="emit_json",
                        help="Emit JSON summary per case")
    parser.add_argument("--write-baseline", action="store_true",
                        help="Write maps-grounding-baseline.json")
    parser.add_argument("--orcast", action="store_true",
                        help="Run orcast-side uncited-rate check (needs ORCAST_AGENT_KEY)")
    parser.add_argument("--require-key", action="store_true",
                        help="Exit 0 with note if GEMINI_API_KEY absent (CI-safe mode)")
    args = parser.parse_args()

    gemini_key = load_gemini_key()
    if not gemini_key:
        if args.require_key:
            print("NOTE: GEMINI_API_KEY not set — skipping Maps grounding probe.")
            return 0
        print("No GEMINI_API_KEY found.", file=sys.stderr)
        print("Get one at https://aistudio.google.com/apikey", file=sys.stderr)
        print("Run: bash tools/testing/set_gemini_key.sh", file=sys.stderr)
        return 2

    # --- Maps baseline ---
    cases_to_run = list(CASES) if args.case == "all" else [args.case]
    results = []
    for case in cases_to_run:
        raw = run_maps_case(gemini_key, case)
        raw["case"] = case
        body = raw["body"]
        if isinstance(body, list):
            body = body[0] if body else {}
        err = body.get("error", {}).get("message") if "error" in body else None
        parsed = None if err else parse_maps_result(raw)
        print_maps_result(case, raw["prompt"], parsed, err)
        if parsed:
            parsed["case"] = case
            results.append(parsed)

    if args.emit_json:
        print("\n--- JSON ---")
        print(json.dumps(results, indent=2))

    if args.write_baseline and results:
        BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
        baseline = {
            "run_date": "2026-06-24",
            "model": MODEL,
            "api_revision": API_REVISION,
            "coords": SAN_JUAN,
            "cases": results,
            "summary": {
                "total_citations": sum(r["total_citations"] for r in results),
                "total_scientific": sum(r["scientific"] for r in results),
                "avg_uncited_rate": round(
                    sum(r["uncited_rate"] for r in results if r["sci_claims"] > 0)
                    / max(sum(1 for r in results if r["sci_claims"] > 0), 1),
                    1,
                ),
            },
        }
        BASELINE_PATH.write_text(json.dumps(baseline, indent=2))
        print(f"\nBaseline written to {BASELINE_PATH}")

    # --- orcast-side check ---
    if args.orcast:
        agent_key = load_agent_key()
        if not agent_key:
            print("ERROR: ORCAST_AGENT_KEY not set — cannot run --orcast check.", file=sys.stderr)
            return 1
        web_base = load_web_base()
        print(f"\n=== orcast grounding check against {web_base}")
        orcast = run_orcast_check(agent_key, web_base)
        if "error" in orcast:
            print(f"ERROR: {orcast['error']}", file=sys.stderr)
            return 1
        print(f"  annotations: {orcast['annotations']} "
              f"(bound: {orcast['bound']}, unbound: {orcast['unbound']})")
        print(f"  uncited rate: {orcast['uncited_rate']:.0f}%")
        print(f"  panels: {orcast['panels']}")
        print(f"  skills: {orcast['skill_plan']}")

        # Assert orcast beats the Maps baseline.
        baseline_rate = MAPS_BASELINE["uncited_rate"]
        if orcast["uncited_rate"] < baseline_rate:
            print(f"  PASS: orcast {orcast['uncited_rate']:.0f}% < Maps baseline {baseline_rate:.0f}%")
        else:
            print(f"  FAIL: orcast {orcast['uncited_rate']:.0f}% >= Maps baseline {baseline_rate:.0f}%",
                  file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
