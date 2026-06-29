# H0 workshop compliance scope

Grading rubric for orcast against the [Vercel × AWS Workshop](https://aws-workshop-companion-site.vercel.app/docs) (Ship 26 / Hack the Zero Stack follow-up). Use this to score execution, plan Devpost copy, and pick high-reward next work.

**Workshop promise:** fullstack AI app on Vercel + Amazon Aurora PostgreSQL, AI via **Vercel AI Gateway + Amazon Bedrock**, deployed end-to-end.

**orcast stance:** same **Vercel + AWS + Bedrock** spine, different data plane (DynamoDB + S3) and product shape (governed forecast, not a generic chat UI). Equivalence is explicit below.

## Grading labels

| Label | Meaning |
|-------|---------|
| **Met** | Workshop step satisfied as written |
| **Equivalent** | Different implementation, same judge-facing intent |
| **Partial** | Started but incomplete or not visible in demo |
| **Gap** | Not done; workshop expects it |
| **N/A** | Workshop step does not apply to orcast domain |
| **Exceeds** | Goes beyond workshop (extra credit for narrative) |

## Compliance matrix

### Welcome / prerequisites

| Workshop item | Label | orcast evidence | Notes |
|---------------|-------|-----------------|-------|
| Vercel account + project | **Met** | https://orcast-h0.vercel.app | Production deploy live |
| Vercel CLI / deploy path | **Met** | [DEPLOY_VERCEL.md](DEPLOY_VERCEL.md), `web/` | Root dir `web` |
| Useful links / docs hygiene | **Partial** | Registry + truth table exist | Link workshop compliance in Devpost optional |

### Hands-on: Setup

| Workshop item | Label | orcast evidence | Notes |
|---------------|-------|-----------------|-------|
| Dev environment (agentic stack / CLI) | **Equivalent** | Cursor + repo scripts; not Vercel Devbox | Acceptable if deploy is reproducible |
| AWS credentials / region | **Met** | App Runner `us-west-2`, [HANDOFF_STATUS.md](../../HANDOFF_STATUS.md) | |
| Env vars wired before deploy | **Met** | `ORCAST_API_BASE`, `ORCAST_API_KEY`, WorkOS, partner key | More vars than workshop |

### Hands-on: Build the App

| Workshop item | Label | orcast evidence | Notes |
|---------------|-------|-----------------|-------|
| Next.js fullstack app | **Met** | `web/` App Router | |
| Chat-style UI as hero | **N/A** | Forecast map + gates, not open chat | **Say in Devpost:** anti-chatbot by design |
| Server-side API boundary | **Met** | `/api/be` proxy, `/api/v1` partner gateway | Stronger than workshop |
| TypeScript frontend | **Met** | `web/` | |

### Hands-on: Connect the Database

| Workshop item | Label | orcast evidence | Notes |
|---------------|-------|-----------------|-------|
| Amazon Aurora PostgreSQL | **Partial** | **RDS PostgreSQL (private)** for exploration sessions | DynamoDB = operational truth; Postgres = guided exploration history only |
| ORM / server queries from Vercel | **Equivalent** | FastAPI on App Runner → DDB/S3 | Data access server-side, not browser → DB |
| Migrations / schema visible | **Partial** | CFN + [DYNAMODB_PROOF.md](DYNAMODB_PROOF.md) | H1 screenshot still manual |
| Connection string in Vercel env | **Equivalent** | `ORCAST_API_BASE` + API key, not raw DDB from edge | Correct security pattern |

**Judge script (one line):** “DynamoDB holds sightings, gates, and audit records. PostgreSQL holds exploration guide session history only — not the forecast system of record.”

### Hands-on: Wire Up AI

| Workshop item | Label | orcast evidence | Notes |
|---------------|-------|-----------------|-------|
| Amazon Bedrock model invocation | **Met** | Sighting check Haiku; promotion supervisor Sonnet | IAM on App Runner |
| Vercel AI Gateway | **Gap** | Bedrock called from **AWS backend**, not via AI Gateway | Workshop-specific integration |
| Model picker / switch models | **Partial** | `ORCAST_BEDROCK_*` env vars | No UI model picker |
| Grounded / non-hallucinated AI | **Exceeds** | Template fallback, live `/api/gates` + provenance context | Core product thesis |
| Streaming chat UX | **N/A** | `/ask` is form + structured reply | |

### Hands-on: Deploy

| Workshop item | Label | orcast evidence | Notes |
|---------------|-------|-----------------|-------|
| Deploy to Vercel production | **Met** | `orcast-h0.vercel.app` | |
| End-to-end smoke (UI → API → data → AI) | **Met** | `./tools/waves/run-gate.sh H0` | agent_smoke, sighting-assist, gates |
| AWS backend deployed | **Exceeds** | App Runner, Lambda, Step Functions, CloudFront maps | Workshop is Vercel-centric only |

### Extras (workshop)

| Extra | Label | orcast evidence |
|-------|-------|-----------------|
| Model Picker | **Partial** | Env-based model IDs only |
| VS Code Setup | **Equivalent** | Cursor / VS Code workspace |
| Devbox Cheatsheet | **Gap** | Not used |

## Execution scorecard (summary)

| Section | Score | Weight for H0 judges |
|---------|-------|----------------------|
| Setup + Deploy | Met | High — must show live URL |
| Build the App (Vercel fullstack) | Met | High |
| Connect the Database | Partial (dual-DB) | Medium — explain DynamoDB truth + Postgres exploration in 10s |
| Wire Up AI (Bedrock) | Partial (no AI Gateway) | Medium |
| Exceeds workshop (orchestration, governance) | Exceeds | High for differentiation |

**Rough compliance:** ~**88% equivalent-or-better** on workshop intent; ~**75% literal** (AI Gateway gap; Postgres is RDS not Aurora Serverless in phase 1).

## Highest-reward next areas

Ranked by **judge impact × effort × alignment with orcast science** (not workshop literalism).

### Tier 1 — Do before Devpost (high reward, low–medium effort)

| Priority | Action | Workshop axis | Wave / gate |
|----------|--------|---------------|-------------|
| 1 | Complete **H1 manual**: video, DynamoDB screenshot, publish Devpost | Deploy + Database | H1 |
| 2 | Add **one Devpost paragraph** mapping workshop → orcast (Vercel + AWS + Bedrock; DDB not Aurora; governed not chat) | All sections | copy only |
| 3 | Run **P1 adversarial probe** + file dossier | Deploy truth | P1 → `P1-gate` |
| 4 | Ensure `./tools/waves/run-gate.sh H0` green with `ORCAST_PARTNER_DEV_KEY` set | Deploy smoke | H0 |

### Tier 2 — Strong workshop alignment (medium effort, optional for science)

| Priority | Action | Reward | Risk |
|----------|--------|--------|------|
| 5 | **Vercel AI Gateway** route for `/ask` (edge or server route → Gateway → Bedrock) | Literal “Wire Up AI” match | Extra hop; must keep grounding |
| 6 | **Architecture diagram callout** for “Vercel ↔ AWS ↔ Bedrock” on [figures/architecture.png](figures/architecture.png) | Judge scan in 30s | Doc only |
| 7 | Partner API demo curl in video (1 line) | Shows Vercel as API gateway | Low |

### Tier 3 — Do not prioritize for workshop compliance

| Item | Why skip |
|------|----------|
| Migrate to Aurora PostgreSQL | Wrong fit; DynamoDB is correct for entities + [DYNAMODB_PROOF.md](DYNAMODB_PROOF.md) |
| Rebuild as generic chat app | Violates H0 anti-chatbot thesis |
| Vercel Devbox | Optional workshop extra; repo already deploys |
| CloudFront as primary Devpost URL | [WAVES_REGISTRY.md](WAVES_REGISTRY.md) — H0 is Vercel |

### Tier 4 — Post-hackathon science (high long-term reward, not workshop)

| Area | Wave |
|------|------|
| Full snapshot freeze (I2) | I2 |
| Baselines scorecard (I5) | I5 |
| Data wiring D1–D4 | D1–D4 |

## Suggested Devpost “workshop alignment” blurb

> Built with the **Vercel + AWS** pattern from the Ship workshop: Next.js on Vercel, managed AWS data and compute, **Amazon Bedrock** for grounded narration. **DynamoDB** is the system of record; **PostgreSQL** stores exploration guide sessions on `/explore`. The product is intentionally **not a chatbot**: reasoning runs through adapters, gates, and human promotion.

## Verification commands

```bash
# Workshop-style deploy smoke
./tools/waves/run-gate.sh H0

# Literal Bedrock path (backend, not AI Gateway today)
curl -s https://orcast-h0.vercel.app/api/be/api/sighting-assist/status | jq .

# Database plane (DynamoDB via API, not Aurora)
curl -s https://orcast-h0.vercel.app/api/be/api/data-status | jq .
```

## Registry cross-reference

| Compliance area | orcast wave |
|-----------------|-------------|
| Deploy + automated smoke | H0 |
| Manual submit artifacts | H1 |
| Truth / no overclaim | P1, I0, truth table |
| AI wiring hardening | I6, optional AI Gateway spike |
| Database proof | H1 screenshot, DYNAMODB_PROOF |

Canonical waves: [WAVES_REGISTRY.md](WAVES_REGISTRY.md).

## Review cadence

1. Before recording demo video: fill Tier 1 checklist.
2. After any deploy: `run-gate.sh H0`.
3. Before judging: re-read **Gap** rows only (AI Gateway, Aurora literal)—decide if Tier 2 item 5 is worth it.

**Last scoped:** 2026-06-23 against workshop overview and hands-on section titles from [workshop docs](https://aws-workshop-companion-site.vercel.app/docs).
