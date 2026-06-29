# M0 — Central Casting terrain dossier

**Date:** 2026-06-23  
**Wave Set H** (registry family **M**)  
**Baseline:** Wave Set G complete; explore guide live on App Runner + optional Vercel AI Gateway

## M0-A — Current explore flow

| Step | Component | Path |
|------|-----------|------|
| 1 | Browser `/explore` | [`web/app/explore/page.tsx`](../../../web/app/explore/page.tsx) |
| 2 | Gateway narration (optional) | [`web/app/api/explore/route.ts`](../../../web/app/api/explore/route.ts) — `prepare` then `generateText` |
| 3 | App Runner prepare | `POST /api/explore/prepare` — [`routers/explore.py`](../../../src/aws_backend/routers/explore.py) → `build_exploration_context` |
| 4 | App Runner turn persist | `POST /api/explore/turn` → `compose_guide_reply` → `SessionStore.save_exchange` |
| 5 | Hard-coded agent | [`guide.py`](../../../src/aws_backend/exploration/guide.py) `SYSTEM_PROMPT` lines 13–22 |
| 6 | Tools | [`tools.py`](../../../src/aws_backend/exploration/tools.py) `fetch_gates`, `fetch_provenance`, `fetch_hotspots`, `fetch_forecast_cell` |
| 7 | Postgres | `exploration_sessions`, `exploration_turns` — migrations `001`, `002` |

**Gap:** No versioned agent config, no `agent_id` resolution, no interaction trace columns.

## M0-B — Auth surface

| Path | Auth |
|------|------|
| `GET /api/explore/status` | Public (proxy allow-list) |
| `POST /api/explore/sessions`, `/turn`, `/prepare` | Public + explore rate limits |
| `POST /api/interactions` | Public + same rate limits (M2 proxy) |
| `GET/POST /api/managed-agents` | `require_api_key` (X-ORCAST-Key) |
| Governance writes | `require_trusted_reviewer` via WorkOS proxy |

Registry CRUD must never be on the public allow-list.

## M0-C — Storage split

| Store | Role |
|-------|------|
| DynamoDB `ManagedAgentsTable` | Versioned cast configs (`agent_id` + `version`) |
| Postgres `exploration_turns` | Interaction history + trace fields (migration `003_interaction_trace.sql`) |

Local dev: `MemoryManagedAgentStore` seeds `explore-guide-v1`; Postgres via `ORCAST_DATABASE_URL`.

## M0-D — Skill inventory

| Skill | Function | Default in explore-guide-v1 |
|-------|----------|----------------------------|
| `fetch_gates` | `tools.fetch_gates` | always |
| `fetch_provenance` | `tools.fetch_provenance` | when viewport/focus has lat/lng |
| `fetch_forecast_cell` | `tools.fetch_forecast_cell` | when viewport/focus has lat/lng |
| `fetch_hotspots` | `tools.fetch_hotspots` | when no pin |

Seed agent lists all four; runtime selects subset by viewport (same logic as today).

## M0-E — G5 backlog + prod gaps

| G5 item | Disposition |
|---------|-------------|
| Deploy auth reprobe | M3 preflight — verify `ORCAST_API_KEY` on App Runner |
| `AI_GATEWAY_API_KEY` on Vercel | M3 ops note — Bedrock fallback OK for M exit |
| Gates UI honesty, docs truth, D3/D4 | Deferred to Wave I / R-Delta |

**Prod URLs:** https://orcast-h0.vercel.app · https://pjrftm3bkv.us-west-2.awsapprunner.com

## M0 exit bar

- [x] Contract drafted — [`MANAGED_AGENTS_CONTRACT.md`](MANAGED_AGENTS_CONTRACT.md)
- [x] Zero open P1 blocking M1 parallel lanes
- [x] No Gemini / Google services in M scope
