#!/usr/bin/env python3
"""8-scenario parallel grounding benchmark: Maps-only vs RAG-augmented with orcast context.

Fetches live orcast skill outputs (gates, provenance, hotspots, surface planner),
injects them as grounding context into 8 Gemini queries run concurrently via asyncio,
and measures the unsupported scientific claim rate for each scenario.

Hypothesis: orcast's evidence-bound skill outputs, when injected as RAG context into
a Gemini Maps-grounded query, reduce the uncited evidence rate below the Maps-only
85% baseline.

Usage:
    source .agent-credentials.env
    python3 tools/testing/grounding_parallel_rag.py
    python3 tools/testing/grounding_parallel_rag.py --json
    python3 tools/testing/grounding_parallel_rag.py --scenario 4  # single scenario
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
CREDS_FILE = REPO_ROOT / ".agent-credentials.env"
ENDPOINT   = "https://generativelanguage.googleapis.com/v1beta/interactions"
API_REVISION = "2026-05-20"
MODEL      = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
SAN_JUAN   = {"latitude": 48.5465, "longitude": -123.03}

SCIENCE_MARKERS = re.compile(
    r"\b(NOAA|DFO|census|population|salmon|Chinook|hydrophone|bathymetr|"
    r"decline|study|studies|research|data|fisheries|pod|pods|p\s*=|"
    r"\d{4}|\d+\s*(?:%|percent|feet|ft|miles|mph|years?))\b",
    re.IGNORECASE,
)

# ── 8 test scenarios ─────────────────────────────────────────────────────────

SCENARIOS = [
    {
        "id": 1,
        "label": "Maps-only: orca evidence (baseline)",
        "query": (
            "Where along the west side of San Juan Island are southern resident "
            "killer whales most likely to be seen from shore, and what is the evidence?"
        ),
        "rag_skill": None,
        "rag_label": "none",
    },
    {
        "id": 2,
        "label": "Maps + orcast gates context (RAG)",
        "query": (
            "Where along the west side of San Juan Island are southern resident "
            "killer whales most likely to be seen from shore, and what does the "
            "evidence from the acoustic monitoring data show?"
        ),
        "rag_skill": "gates",
        "rag_label": "orcast_gates",
    },
    {
        "id": 3,
        "label": "Maps + orcast provenance context (RAG)",
        "query": (
            "What is the modeled encounter intensity for orcas at Haro Strait, "
            "and what kernels and data sources contributed to this prediction?"
        ),
        "rag_skill": "provenance",
        "rag_label": "orcast_provenance",
    },
    {
        "id": 4,
        "label": "Maps + orcast surface planner output (RAG)",
        "query": (
            "Which fitness gates currently block promotion of the orca encounter "
            "forecast, and what integrity conditions are active?"
        ),
        "rag_skill": "planner",
        "rag_label": "orcast_planner",
    },
    {
        "id": 5,
        "label": "Maps-only: sighting check (baseline)",
        "query": (
            "I saw a black dorsal fin from shore at Lime Kiln Point — "
            "what is the encounter likelihood for orcas today and could it be one?"
        ),
        "rag_skill": None,
        "rag_label": "none",
    },
    {
        "id": 6,
        "label": "Maps + orcast sighting-assist context (RAG)",
        "query": (
            "I saw a black dorsal fin from shore at Lime Kiln Point — "
            "what does the orcast sighting check say about encounter likelihood "
            "and what data is it grounded in?"
        ),
        "rag_skill": "sighting",
        "rag_label": "orcast_sighting",
    },
    {
        "id": 7,
        "label": "Maps-only: trip planning (baseline)",
        "query": (
            "Plan a shore-based whale watching afternoon near Lime Kiln Point. "
            "Include viewpoints, parking, and when orcas are most likely."
        ),
        "rag_skill": None,
        "rag_label": "none",
    },
    {
        "id": 8,
        "label": "Maps + orcast hotspots + dossier (RAG)",
        "query": (
            "Plan a shore-based orca watching afternoon using the orcast forecast "
            "hotspots near Lime Kiln Point. What does the confidence gate say about "
            "the reliability of the forecast today?"
        ),
        "rag_skill": "hotspots",
        "rag_label": "orcast_hotspots",
    },
]


# ── credential loading ────────────────────────────────────────────────────────

def load_creds() -> dict[str, str]:
    out: dict[str, str] = {}
    for src in [CREDS_FILE]:
        if src.exists():
            for line in src.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip()
    for k in ["GEMINI_API_KEY", "ORCAST_AGENT_KEY", "ORCAST_WEB_BASE"]:
        if k in os.environ:
            out[k] = os.environ[k]
    return out


# ── orcast context fetchers ───────────────────────────────────────────────────

def _agent_headers(key: str) -> dict[str, str]:
    return {"X-ORCAST-Agent-Key": key, "Content-Type": "application/json"}


def fetch_orcast_context(skill: str | None, agent_key: str, web_base: str) -> str:
    """Fetch live orcast skill output and format as RAG context block."""
    if skill is None:
        return ""
    base = web_base.rstrip("/")
    h = _agent_headers(agent_key)
    ctx_lines = [f"\n\n--- ORCAST LIVE CONTEXT ({skill.upper()}) ---"]
    try:
        if skill == "gates":
            r = requests.get(f"{base}/api/be/api/gates", headers=h, timeout=20)
            if r.ok:
                d = r.json()
                ctx_lines += [
                    f"Effective confidence: {d.get('effective_confidence', 'n/a')}",
                    f"Status: {d.get('status', 'n/a')}",
                    f"Promoted: {d.get('promoted', False)}",
                    "Integrity conditions: " + "; ".join(d.get("caveats", [])),
                ]
        elif skill == "provenance":
            r = requests.get(
                f"{base}/api/be/api/provenance?lat=48.5465&lng=-123.03",
                headers=h, timeout=20,
            )
            if r.ok:
                d = r.json()
                ctx_lines.append(
                    f"Intensity: {d.get('intensity', 'n/a')} "
                    f"confidence: {d.get('effective_confidence', d.get('confidence', 'n/a'))}"
                )
                for k in d.get("kernel_contributions", []):
                    ctx_lines.append(
                        f"Kernel {k.get('kernel')}: phase={k.get('phase','?'):.3f} "
                        f"log_rate={k.get('log_rate_contribution','?')} "
                        f"beats_null={k.get('beats_null','?')}"
                    )
                note = d.get("trace_note", "")
                if note:
                    ctx_lines.append(f"Trace note: {note}")
        elif skill == "planner":
            sess_r = requests.post(
                f"{base}/api/be/api/explore/sessions",
                json={"title": "rag_test"},
                headers=h, timeout=15,
            )
            if sess_r.ok:
                sid = sess_r.json().get("session_id", str(uuid.uuid4()))
                plan_r = requests.post(
                    f"{base}/api/interactions/plan",
                    json={
                        "session_id": sid,
                        "message": "Which gates block promotion right now?",
                        "agent_id": "surface-planner-v1",
                        "viewport": {"lat": 48.5465, "lng": -123.03, "zoom": 10},
                    },
                    headers=h, timeout=60,
                )
                if plan_r.ok:
                    d = plan_r.json()
                    ui = d.get("ui_intent", {})
                    ctx_lines.append(f"Surface planner panels: {[p['id'] for p in ui.get('panels', [])]}")
                    ctx_lines.append(f"Skill plan: {ui.get('skill_plan', [])}")
                    for step in (d.get("prepare") or {}).get("steps", []):
                        ctx_lines.append(
                            f"Step {step.get('type')}: {step.get('skill', '')} "
                            f"{step.get('output_status', '')}"
                        )
                    for ann in (d.get("prepare") or {}).get("annotations", []):
                        ctx_lines.append(f"Annotation [{ann.get('type')}]: {ann.get('label')} {ann.get('href','')}")
        elif skill == "sighting":
            r = requests.post(
                f"{base}/api/be/api/sighting-assist",
                json={"message": "I saw a black dorsal fin", "lat": 48.5465, "lng": -123.03},
                headers=h, timeout=30,
            )
            if r.ok:
                d = r.json()
                ctx_lines.append(f"Encounter likelihood reply: {d.get('reply', '')[:600]}")
                ctx_lines.append(f"Source: {d.get('source', 'n/a')}")
        elif skill == "hotspots":
            r = requests.get(
                f"{base}/api/be/api/hotspots",
                headers=h, timeout=20,
            )
            if r.ok:
                d = r.json()
                hotspots = d.get("hotspots") or d.get("results") or []
                for hs in hotspots[:3]:
                    ctx_lines.append(
                        f"Hotspot: {hs.get('name', hs.get('hotspot_id', '?'))} "
                        f"prob={hs.get('probability', '?'):.3f} "
                        f"confidence={hs.get('confidence', '?')}"
                    )
    except Exception as exc:
        ctx_lines.append(f"[fetch error: {exc}]")
    ctx_lines.append("--- END ORCAST CONTEXT ---\n")
    return "\n".join(ctx_lines)


# ── grounding metrics ─────────────────────────────────────────────────────────

def measure_grounding(body: dict) -> dict[str, Any]:
    text_blocks, place_citations, step_types = [], [], []
    for step in body.get("steps", []) or []:
        step_types.append(step.get("type"))
        for block in step.get("content", []) or []:
            if block.get("type") == "text" and block.get("text"):
                text_blocks.append(block["text"])
            for ann in block.get("annotations", []) or []:
                if ann.get("type") in ("place_citation", "maps_citation"):
                    place_citations.append({"name": ann.get("name") or ann.get("title"), "url": ann.get("url")})

    full_text = "\n".join(text_blocks)
    place = sum(1 for c in place_citations if "maps.google" in (c.get("url") or "") or "cid=" in (c.get("url") or ""))
    scientific = len(place_citations) - place
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", full_text) if s.strip()]
    sci_sents = [s for s in sentences if SCIENCE_MARKERS.search(s)]
    cited_names = {(c.get("name") or "").lower() for c in place_citations if c.get("name")}
    unsupported = [s for s in sci_sents if not any(n and n in s.lower() for n in cited_names)]
    rate = len(unsupported) / len(sci_sents) * 100 if sci_sents else 0.0
    words = sum(len(t.split()) for t in text_blocks) or 1

    return {
        "text": full_text[:800],
        "total_citations": len(place_citations),
        "place_citations": place,
        "scientific_citations": scientific,
        "density": round(len(place_citations) / words * 1000, 1),
        "sci_claims": len(sci_sents),
        "unsupported": len(unsupported),
        "uncited_rate": round(rate, 1),
        "step_types": step_types,
    }


# ── Gemini call (sync, runs in thread pool for parallel) ─────────────────────

def run_scenario_sync(scenario: dict, gemini_key: str, orcast_context: str) -> dict[str, Any]:
    query = scenario["query"]
    if orcast_context:
        full_query = (
            f"{query}\n{orcast_context}\n"
            "(Use the orcast data above to ground your answer where relevant.)"
        )
    else:
        full_query = query

    body = {
        "model": MODEL,
        "input": full_query,
        "tools": [{"type": "google_maps", **SAN_JUAN}],
    }
    t0 = time.time()
    resp = requests.post(
        ENDPOINT,
        headers={"x-goog-api-key": gemini_key, "Content-Type": "application/json", "Api-Revision": API_REVISION},
        json=body,
        timeout=90,
    )
    elapsed = round(time.time() - t0, 1)
    if not resp.ok:
        return {"id": scenario["id"], "label": scenario["label"], "error": f"HTTP {resp.status_code}", "elapsed": elapsed}

    data = resp.json()
    if isinstance(data, list):
        data = data[0] if data else {}
    if "error" in data:
        return {"id": scenario["id"], "label": scenario["label"], "error": data["error"].get("message"), "elapsed": elapsed}

    metrics = measure_grounding(data)
    return {
        "id": scenario["id"],
        "label": scenario["label"],
        "rag_label": scenario["rag_label"],
        "elapsed": elapsed,
        **metrics,
    }


# ── async orchestrator ────────────────────────────────────────────────────────

async def run_all_parallel(
    scenarios: list[dict],
    gemini_key: str,
    agent_key: str,
    web_base: str,
) -> list[dict[str, Any]]:
    loop = asyncio.get_event_loop()

    async def run_one(s: dict) -> dict[str, Any]:
        # Fetch orcast context in thread pool (blocking HTTP)
        ctx = await loop.run_in_executor(
            None, fetch_orcast_context, s["rag_skill"], agent_key, web_base
        )
        # Run Gemini query in thread pool (blocking HTTP)
        result = await loop.run_in_executor(
            None, run_scenario_sync, s, gemini_key, ctx
        )
        label = result.get("label", "?")
        uncited = result.get("uncited_rate", "?")
        print(f"  [{result.get('id')}] {label[:50]:<50} uncited={uncited}%  {result.get('elapsed','?')}s")
        return result

    tasks = [asyncio.create_task(run_one(s)) for s in scenarios]
    return await asyncio.gather(*tasks)


# ── reporting ─────────────────────────────────────────────────────────────────

def print_report(results: list[dict[str, Any]]) -> None:
    results = sorted(results, key=lambda r: r.get("id", 99))
    print("\n" + "=" * 78)
    print(f"{'#':<3} {'Label':<42} {'RAG':<18} {'Uncited%':>8} {'Citations':>10} {'Words':>6}")
    print("-" * 78)
    for r in results:
        if "error" in r:
            print(f"{r['id']:<3} {r['label'][:42]:<42} ERROR: {r['error']}")
            continue
        words = round(r['total_citations'] / (r['density'] / 1000)) if r['density'] else 0
        print(
            f"{r['id']:<3} {r['label'][:42]:<42} "
            f"{r['rag_label']:<18} {r['uncited_rate']:>7.0f}% "
            f"{r['total_citations']:>5}cites  {r['sci_claims']:>4}sci"
        )

    # Pair comparison
    baseline_ids = {1: 2, 5: 6, 7: 8}
    print("\n── RAG lift (reduction in uncited rate) ──")
    for base_id, rag_id in baseline_ids.items():
        bline = next((r for r in results if r.get("id") == base_id), None)
        rag   = next((r for r in results if r.get("id") == rag_id), None)
        if bline and rag and "uncited_rate" in bline and "uncited_rate" in rag:
            lift = bline["uncited_rate"] - rag["uncited_rate"]
            direction = "↓" if lift > 0 else "↑"
            print(
                f"  Scenario {base_id}→{rag_id}: "
                f"{bline['uncited_rate']:.0f}% → {rag['uncited_rate']:.0f}%  "
                f"{direction}{abs(lift):.0f}pp  ({rag['rag_label']})"
            )
    print("=" * 78)


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="8-scenario parallel grounding RAG benchmark")
    parser.add_argument("--scenario", type=int, help="Run a single scenario ID (1-8)")
    parser.add_argument("--json", action="store_true", help="Print JSON results")
    parser.add_argument("--out", help="Write JSON results to this path")
    args = parser.parse_args()

    creds = load_creds()
    gemini_key = creds.get("GEMINI_API_KEY", "")
    agent_key  = creds.get("ORCAST_AGENT_KEY", "")
    web_base   = creds.get("ORCAST_WEB_BASE", "https://orcast-h0.vercel.app")

    if not gemini_key:
        print("ERROR: GEMINI_API_KEY not set. Run: bash tools/testing/set_gemini_key.sh", file=sys.stderr)
        return 1
    if not agent_key:
        print("ERROR: ORCAST_AGENT_KEY not set. Run: bash tools/testing/setup_agent_user.sh", file=sys.stderr)
        return 1

    scenarios = SCENARIOS
    if args.scenario:
        scenarios = [s for s in SCENARIOS if s["id"] == args.scenario]
        if not scenarios:
            print(f"ERROR: Unknown scenario {args.scenario}. Valid: 1-8", file=sys.stderr)
            return 1

    print(f"Running {len(scenarios)} grounding scenarios in parallel")
    print(f"  Gemini model: {MODEL}  |  orcast: {web_base}")
    print(f"  RAG scenarios: {sum(1 for s in scenarios if s['rag_skill'])} with live orcast context")
    print()

    results = asyncio.run(run_all_parallel(scenarios, gemini_key, agent_key, web_base))

    if args.json or args.out:
        out = json.dumps(results, indent=2)
        if args.out:
            Path(args.out).write_text(out)
            print(f"\nJSON → {args.out}")
        else:
            print("\n" + out)
    else:
        print_report(results)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
