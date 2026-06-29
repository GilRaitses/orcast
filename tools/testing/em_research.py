#!/usr/bin/env python3
"""Run Emergent Mind searches for orcast whitepaper search families and write
research summaries to docs/whitepaper/research/.

Uses the Emergent Mind Paper Search API:
  POST https://api.emergentmind.com/v1/papers/search
  Header: x-api-key: <key>

Key storage: EMERGENT_MIND_API_KEY in gitignored .agent-credentials.env.
Set it with: bash tools/testing/set_em_key.sh

Usage:
    python3 tools/testing/em_research.py               # run all families
    python3 tools/testing/em_research.py --family SF-1 # one family
    python3 tools/testing/em_research.py --list        # list families + queries
    python3 tools/testing/em_research.py --dry-run     # show what would run, no API calls
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import time
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
CREDS_FILE = REPO_ROOT / ".agent-credentials.env"
RESEARCH_DIR = REPO_ROOT / "docs/whitepaper/research"
EM_ENDPOINT = "https://api.emergentmind.com/v1/papers/search"
NUM_RESULTS = 5       # papers per query (1–50)
SLEEP_BETWEEN = 2.0   # seconds between API calls (rate limiting)


# ---------------------------------------------------------------------------
# Search family definitions.  Each family maps to one section in the
# whitepaper and carries the queries from SEARCH_FAMILY_GRID.md.
# ---------------------------------------------------------------------------
FAMILIES: dict[str, dict] = {
    "SF-1": {
        "slug": "SF-01-effort-bias",
        "section": 1,
        "claim": (
            "Effort bias, epistemic opacity, and governance failure are documented "
            "failure modes in wildlife encounter products"
        ),
        "queries": [
            "effort bias wildlife encounter forecasting detection probability",
            "observer effort confounding orca sighting density hotspot",
            "occupancy model detection correction acoustic monitoring bias",
            "passive acoustic monitoring false positive rate presence absence detection",
            "cetacean encounter rate spatial bias survey effort",
        ],
        "verification_target": (
            "At least one paper demonstrating that naive hotspot aggregation "
            "overstates animal presence relative to effort-corrected estimates."
        ),
    },
    "SF-2": {
        "slug": "SF-02-acoustic-qc",
        "section": 3,
        "claim": (
            "Passive acoustic detection systems have non-trivial false-positive rates "
            "requiring explicit quarantine before influencing a probabilistic model."
        ),
        "queries": [
            "OrcaHello killer whale acoustic classifier false positive rate",
            "Orcasound passive acoustic monitoring uncertainty marine mammal",
            "deep learning bioacoustics detection precision recall field deployment",
            "PSTH peristimulus time histogram acoustic event spike train fit",
            "Level 0 QC acoustic candidate review workflow marine mammal detector",
        ],
        "verification_target": (
            "Paper or report quantifying the false-positive rate of an acoustic ML "
            "classifier in field deployment, ideally >= 10%."
        ),
    },
    "SF-3": {
        "slug": "SF-03-negative-binomial",
        "section": 2,
        "claim": (
            "Negative-binomial regression or Poisson point-process intensity models "
            "are the appropriate distributional family for sparse, overdispersed "
            "encounter count data."
        ),
        "queries": [
            "negative binomial regression wildlife count data overdispersion zero inflation",
            "inhomogeneous Poisson process intensity ecological encounter rate",
            "cyclic covariate diel lunar kernel encounter rate temporal model",
            "sparse count data distribution family ecological forecasting selection",
            "log-rate decomposition covariate contribution encounter intensity",
        ],
        "verification_target": (
            "Paper using NB or point-process intensity for wildlife encounter data, "
            "reporting superiority over Gaussian or Poisson for overdispersed counts."
        ),
    },
    "SF-4": {
        "slug": "SF-04-null-gating",
        "section": 2,
        "claim": (
            "Phase-shuffled null tests and time-rescaling goodness-of-fit are valid, "
            "conservative statistical gates for cyclic temporal covariates in "
            "count/point-process models."
        ),
        "queries": [
            "phase shuffled surrogate null test cyclic temporal covariate significance",
            "time rescaling theorem Kolmogorov-Smirnov goodness of fit point process",
            "diel lunar covariate null hypothesis test spike train temporal model",
            "permutation null distribution temporal covariate ecological model gate",
            "model selection gate criterion temporal ecological forecasting confidence bound",
        ],
        "verification_target": (
            "Paper using phase-shuffle or time-rescaling tests specifically, or a "
            "methodological review establishing these as valid null tests."
        ),
    },
    "SF-5": {
        "slug": "SF-05-cv-skill",
        "section": 2,
        "claim": (
            "Negative mean held-out deviance skill and failed PIT calibration are "
            "grounds for withholding displayed confidence."
        ),
        "queries": [
            "probability integral transform PIT calibration ecological species distribution model",
            "mean deviance skill cross-validation ecological forecasting out-of-sample",
            "calibration ecological forecast confidence interval coverage skill score",
            "Brier skill score deviance null model ecological forecast evaluation",
            "negative skill score model worse than climatology null ecological prediction",
        ],
        "verification_target": (
            "Paper establishing PIT or deviance skill as a calibration diagnostic "
            "for distributional ecological forecasts, with interpretation for negative skill."
        ),
    },
    "SF-6": {
        "slug": "SF-06-uncertainty-communication",
        "section": 1,
        "claim": (
            "Users of confidence-smoothed spatial forecasts systematically overtrust "
            "displayed certainty when maps do not expose statistical basis or model limits."
        ),
        "queries": [
            "uncertainty visualization map user trust ecological forecast",
            "confidence display spatial forecast decision making overtrust cognitive bias",
            "forecast communication uncertainty public wildlife management",
            "species distribution model confidence map user interpretation",
            "honesty information interface design ecological uncertainty",
        ],
        "verification_target": (
            "Paper demonstrating user overtrust or miscalibrated decision-making "
            "when spatial forecasts omit uncertainty bounds or caveats."
        ),
    },
    "SF-7": {
        "slug": "SF-07-llm-grounding",
        "section": 4,
        "claim": (
            "Structured citation architectures reduce the rate of unsupported scientific "
            "claims relative to unstructured LLM generation or place-grounded tool calls."
        ),
        "queries": [
            "retrieval augmented generation factual accuracy citation hallucination reduction",
            "groundingSupports span citation binding LLM attribution architecture",
            "prepare then narrate tool grounding LLM deterministic skill dispatch",
            "structured step log LLM interaction provenance scientific claim",
            "citation architecture place grounding vs dataset grounding evidence quality",
        ],
        "verification_target": (
            "Paper showing structured grounding (tool dispatch + span citation) reduces "
            "unsupported-claim or hallucination rate versus ungrounded or place-only generation."
        ),
    },
    "SF-8": {
        "slug": "SF-08-agent-orchestration",
        "section": 5,
        "claim": (
            "Plan-then-execute architectures with deterministic allow-listed tool dispatch "
            "reduce tool hallucination and improve output verifiability."
        ),
        "queries": [
            "plan execute LLM agent tool selection hallucination deterministic",
            "orchestrator managed subagent parallel lane verification skill dispatch",
            "tool use allow-list manifest safety agent LLM",
            "ReAct plan act verify agent workflow grounding",
            "agent orchestration step log audit trail reproducibility verification",
        ],
        "verification_target": (
            "Paper demonstrating reduced error or hallucination when tool invocation is "
            "constrained to an explicit manifest versus free LLM tool-calling."
        ),
    },
    "SF-9": {
        "slug": "SF-09-data-provenance",
        "section": 4,
        "claim": (
            "Persisting an ordered step log per interaction as JSONB is sufficient to "
            "reconstruct the provenance chain from a displayed metric to its source data."
        ),
        "queries": [
            "data provenance lineage reproducibility scientific workflow audit trail",
            "interaction step log machine readable provenance claim tracing",
            "knowledge graph provenance scientific data artifact origin",
            "FAIR data principles provenance metadata reproducibility",
            "claim method experiment data graph scientific provenance visualization",
        ],
        "verification_target": (
            "Paper establishing step-log or trace-based provenance as sufficient "
            "for scientific reproducibility in a computational or AI workflow."
        ),
    },
    "SF-10": {
        "slug": "SF-10-hitl-moderation",
        "section": 6,
        "claim": (
            "Citizen-science data without quarantine and human review authority produces "
            "systematic confidence overestimates; a signed promotion step is necessary."
        ),
        "queries": [
            "citizen science data quality control machine learning integration governance",
            "human in the loop moderation approval crowdsourced label quality",
            "wildlife observation citizen science bias verification expert review",
            "community science data quarantine moderation queue attribution reliability",
            "human authority AI decision promotion immutable audit record",
        ],
        "verification_target": (
            "Paper quantifying data quality degradation or model error when unmoderated "
            "crowdsourced data enters a probabilistic model without review."
        ),
    },
    "SF-11": {
        "slug": "SF-11-geospatial-grounding-limits",
        "section": 7,
        "claim": (
            "Google Maps grounding resolves place citations (POI) but leaves 85% of "
            "scientific evidence claims uncited; domain-specific provenance systems are required."
        ),
        "queries": [
            "LLM geospatial grounding scientific evidence accuracy citation quality",
            "Google Maps grounding Gemini API place citation scientific claim limitation",
            "knowledge grounding domain specific vs general purpose tool LLM",
            "citation type evaluation LLM grounding place vs scientific dataset",
            "grounding with maps vs RAG scientific evidence coverage accuracy",
        ],
        "verification_target": (
            "Supplemental only (pre-verified by live benchmark 2026-06-24). "
            "EM search to find academic critiques of geospatial tool grounding limits."
        ),
        "pre_verified": True,
    },
    "SF-12": {
        "slug": "SF-12-cmx-graphs",
        "section": 4,
        "claim": (
            "Claim/method/experiment graph architectures over step logs enable inline "
            "span-bound citation markers equivalent to GraphiMind / MindSearch approaches."
        ),
        "queries": [
            "GraphiMind scientific paper knowledge graph claim method experiment novelty",
            "MindSearch multi-agent query decomposition knowledge graph construction",
            "knowledge graph claim citation binding interactive grounding interface",
            "claim method experiment directed graph scientific provenance visualization",
            "supporting contrasting background citation edge scientific knowledge graph",
        ],
        "verification_target": (
            "Paper describing a C/M/X or equivalent graph schema for scientific provenance, "
            "or a system binding text-span citations to structured knowledge nodes."
        ),
    },
    "SF-13": {
        "slug": "SF-13-rag-quality-measurement",
        "section": 4,
        "claim": (
            "Not all RAG context reduces the unsupported scientific claim rate; structured "
            "step-log reasoning traces achieve 0% uncited rate where unstructured data "
            "injection does not."
        ),
        "queries": [
            "RAG context quality measurement grounding evaluation metric",
            "structured vs unstructured retrieval augmented generation citation accuracy",
            "step log trace injection LLM grounding factual accuracy",
            "reasoning chain injection evidence binding claim accuracy measurement",
            "retrieval quality diagnostic hierarchy grounding architecture evaluation",
        ],
        "verification_target": (
            "Paper measuring the differential effect of RAG context type on unsupported "
            "scientific claim rate, or proposing a formal metric for grounding quality."
        ),
    },
    "SF-14": {
        "slug": "SF-14-steplog-world-model-eval",
        "section": 5,
        "claim": (
            "A world model planning step-log functions as a structured evidence trace; "
            "injecting it as grounding context eliminates uncited claims in planning-type "
            "queries, and R_uncited applied to intermediate planning outputs measures whether "
            "the model's stated beliefs are evidence-bound."
        ),
        "queries": [
            "world model evaluation intermediate representation grounding evidence binding",
            "JEPA joint embedding predictive architecture evaluation framework 2025 2026",
            "planning step log intermediate output verification grounding quality",
            "LeCun world model evaluation benchmark physical world reasoning 2026",
            "AI agent reasoning chain traceability evidence citation intermediate steps",
        ],
        "verification_target": (
            "Paper proposing or applying evaluation frameworks for world model intermediate "
            "outputs, or measuring whether AI planning traces are grounded in sensor evidence."
        ),
    },
    "SF-15": {
        "slug": "SF-15-lecun-ami-primary",
        "section": 6,
        "claim": (
            "LeCun's world model architecture (AMI, 2022) requires that intermediate "
            "representations be grounded in their generating sensor observations as a design "
            "property; no formal evaluation metric for this evidence-binding property is "
            "proposed in the AMI position paper or in subsequent JEPA architecture papers."
        ),
        "queries": [
            "LeCun autonomous machine intelligence world model architecture evaluation 2022",
            "path towards autonomous machine intelligence world model grounding sensor observation",
            "V-JEPA video JEPA evaluation framework grounding 2024 2025",
            "AMI world model evidence binding belief grounding sensor observation evaluation",
            "JEPA world model intermediate representation evaluation metric grounding",
        ],
        "verification_target": (
            "LeCun's 2022 position paper or V-JEPA paper confirming that evidence grounding "
            "is named as a design requirement but that no claim-level metric is proposed, "
            "confirming the gap that R_uncited fills."
        ),
    },
    "SF-16": {
        "slug": "SF-16-physical-world-eval",
        "section": 7,
        "claim": (
            "Existing benchmarks for physical-world AI reasoning (embodied AI, robotics planning, "
            "situated reasoning) measure task completion or prediction accuracy but do not measure "
            "whether intermediate reasoning claims are bound to their generating sensor observations."
        ),
        "queries": [
            "physical world reasoning AI benchmark evaluation intermediate steps 2024 2025",
            "world model evaluation situated reasoning grounding sensor observation benchmark",
            "AI planning benchmark evidence traceability intermediate claims physical world",
            "robotics planning benchmark claim verification sensor observation grounding 2025",
            "embodied AI benchmark evaluation world model intermediate representation 2025",
        ],
        "verification_target": (
            "Survey or benchmark paper evaluating embodied AI or planning AI on task completion "
            "or accuracy without a claim-level evidence binding metric — confirming the gap."
        ),
    },
}


def load_key() -> str:
    key = os.environ.get("EMERGENT_MIND_API_KEY", "")
    if not key and CREDS_FILE.exists():
        for line in CREDS_FILE.read_text().splitlines():
            line = line.strip()
            if line.startswith("EMERGENT_MIND_API_KEY="):
                key = line.split("=", 1)[1].strip()
                break
    return key


def search(key: str, query: str, n: int = NUM_RESULTS) -> list[dict]:
    resp = requests.post(
        EM_ENDPOINT,
        headers={"x-api-key": key, "Content-Type": "application/json"},
        json={"query": query, "num_results": n},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    # API returns list or {"results": [...]}
    if isinstance(data, list):
        return data
    return data.get("results") or data.get("papers") or []


def format_paper(p: dict) -> str:
    title = p.get("title") or p.get("name") or "(no title)"
    arxiv_id = p.get("arxiv_id") or p.get("id") or ""
    authors = p.get("authors") or []
    if isinstance(authors, list):
        authors = ", ".join(a.get("name") or str(a) for a in authors[:3])
    summary = p.get("abstract") or p.get("summary") or p.get("description") or ""
    summary = textwrap.fill(summary[:600] + ("…" if len(summary) > 600 else ""), 80)
    return f"**{title}**\n{arxiv_id}  {authors}\n{summary}"


def run_family(key: str, fid: str, dry_run: bool = False) -> Path:
    f = FAMILIES[fid]
    slug = f["slug"]
    out = RESEARCH_DIR / f"{slug}.md"
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# {fid} — {slug.replace('-', ' ').title()}",
        "",
        f"**Section:** {f['section']}",
        "",
        f"**Claim:** {f['claim']}",
        "",
        f"**Verification target:** {f['verification_target']}",
        "",
    ]

    if f.get("pre_verified"):
        lines += [
            "## Status",
            "",
            "Pre-verified by live benchmark (2026-06-24, Gemini 3.5 Flash).",
            "See `PROVENANCE_GRAPH_CONTRACT.md` for numbers.",
            "EM searches below are supplemental.",
            "",
        ]

    for q in f["queries"]:
        lines += [f"## Query: {q}", ""]
        if dry_run:
            lines += ["*(dry run — no API call)*", ""]
            continue
        try:
            papers = search(key, q)
            if not papers:
                lines += ["*(no results)*", ""]
            else:
                for p in papers:
                    lines += [format_paper(p), ""]
        except requests.HTTPError as e:
            lines += [f"ERROR: {e}", ""]
        time.sleep(SLEEP_BETWEEN)

    lines += [
        "---",
        "",
        "## Family summary",
        "",
        "*(fill after reading papers — 4–6 sentences, one verification verdict: "
        "Supported / Partial / Not found)*",
        "",
        "**Status:** Not yet run" if not dry_run else "**Status:** Dry run",
    ]

    out.write_text("\n".join(lines))
    print(f"  -> wrote {out.relative_to(REPO_ROOT)}")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Emergent Mind research for orcast whitepaper")
    parser.add_argument("--family", help="Run a single family (e.g. SF-1)")
    parser.add_argument("--list", action="store_true", help="List families and their queries")
    parser.add_argument("--dry-run", action="store_true", help="Show structure, skip API calls")
    args = parser.parse_args()

    if args.list:
        for fid, f in FAMILIES.items():
            print(f"\n{fid} ({f['slug']}) — section {f['section']}")
            for q in f["queries"]:
                print(f"  - {q}")
        return 0

    key = "" if args.dry_run else load_key()
    if not key and not args.dry_run:
        print("No EMERGENT_MIND_API_KEY found.", file=sys.stderr)
        print("Run: cd /Users/gilraitses/orcast && bash tools/testing/set_em_key.sh", file=sys.stderr)
        return 2

    target = {}
    if args.family:
        fid = args.family.upper()
        if fid not in FAMILIES:
            print(f"Unknown family '{fid}'. Known: {', '.join(FAMILIES)}", file=sys.stderr)
            return 1
        target = {fid: FAMILIES[fid]}
    else:
        target = FAMILIES

    print(f"Running {len(target)} search families → {RESEARCH_DIR.relative_to(REPO_ROOT)}/")
    for fid in target:
        print(f"\n[{fid}] {FAMILIES[fid]['slug']}")
        run_family(key, fid, dry_run=args.dry_run)

    print(f"\nDone. Open docs/whitepaper/research/ and fill in Family summary sections.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
