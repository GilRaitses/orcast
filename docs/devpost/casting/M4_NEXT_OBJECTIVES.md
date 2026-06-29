# Wave Set M4 — reprobe dossier and Wave I charter

**Date:** 2026-06-23  
**User-facing label:** Wave Set H (Central Casting)  
**Baseline:** [M0_TERRAIN_DOSSIER.md](M0_TERRAIN_DOSSIER.md)  
**Production:** https://orcast-h0.vercel.app · https://pjrftm3bkv.us-west-2.awsapprunner.com

## Wave Set M verdict

**Central Casting MVP shipped.** Registry CRUD keyed; public `POST /api/interactions` with `agent_id` only; `explore-guide-v1` seeded; interaction trace persisted on Postgres turns. No Gemini / Google services.

## M4 reprobe panels

| Panel | Question | Verdict |
|-------|----------|---------|
| M4-A | Public CRUD or skill injection? | **PASS** — `/api/managed-agents` requires X-ORCAST-Key; skills validated against `SKILL_CATALOG` |
| M4-B | Version pin + spec hash reproducibility? | **PASS** — `resolved_spec_hash` on each interaction; optional `agent_version` pin |
| M4-C | Rate limits on `/api/interactions`? | **PASS** — same explore turn bucket (10/min) on Vercel proxy |
| M4-D | Trace sufficient without embeddings? | **PASS** — `skills_invoked`, `gate_ids`, `provenance_refs` on turns |
| M4-E | CONTRACT matches prod paths? | **PASS** — `/api/managed-agents`, `/api/interactions`, `/api/interactions/status` |

## Delivered in M

| ID | Deliverable |
|----|-------------|
| M1-A | `ManagedAgentsTable` in CFN + `ORCAST_MANAGED_AGENTS_TABLE` |
| M1-B | Registry store + CRUD + seed `explore-guide-v1.json` |
| M1-C | `POST /api/interactions`, concierge runtime, migration `003_interaction_trace.sql` |
| M1-D | `SKILL_CATALOG`, policy enforcement, guide optional instructions/skills |
| M1-E | Gates `m`, `m-gate` |
| M2 | `main.py` routers, proxy public POST for interactions |
| M3 | `seed_managed_agent.py` deploy hook |

## Open items → Wave I

1. **I1 — Inline hydration** — `POST /api/interactions` with inline `agent: { instructions, skills, … }`
2. **I2 — Vercel Gateway route** — `web/app/api/interactions/route.ts` mirroring explore Gateway path
3. **I3 — Concierge trace UI** — Explore panel shows cast role + expandable steps
4. **I4 — G5 remediation** — gates UI honesty (G3-D-01), docs truth in `docs/API.md`
5. **I5 — Optional `AI_GATEWAY_API_KEY`** on Vercel for live Gateway narration

## Wave J preview (not started)

- `sighting-check-v1`, `dossier-explainer-v1`
- Step Functions invokes `promotion-clerk-v1` by ID

## Gate commands

```bash
./tools/waves/run-gate.sh m
./tools/waves/run-gate.sh m-gate
./tools/waves/run-gate.sh e-gate
./tools/waves/run-gate.sh g-gate
./tools/waves/run-gate.sh H0
```

## Registry patch

Set `next_wave_set: I`; mark M0–M4 `done`.
