# orcast, H0 submission

H0: Hack the Zero Stack. Track: Open innovation. Primary AWS database: Amazon DynamoDB. Frontend: Next.js on Vercel.

## Tagline

A whale-encounter forecast that shows only the confidence its evidence has earned, every hot cell traces back to its data, and a human signs off before any confidence is promoted.

## Problem, for whom, and why

Wildlife and environmental forecasts present a smooth, confident surface that hides how thin or biased the underlying evidence is. A shore or kayak whale-watcher looking at a "hotspot" cannot tell whether it reflects real animal behavior or just where people happened to look. Researchers and data stewards have no audit trail from a displayed prediction back to the observations and statistical checks behind it.

**orcast** is built for three users:

- Shore and kayak whale-watchers (public forecast, sighting check, field journal),
- Field scientists and naturalists (fitness-gate dashboard, provenance drill-down, glossary),
- Data stewards (citizen-science moderation queue and human promotion approvals).

Why this problem: the Southern Resident killer whales are endangered, sightings are effort-biased, and acoustic detections are sparse. An auditable forecast with explicit integrity conditions is more useful than a falsely precise one. Every operational entity, sightings, moderation queue, decision audit log, field journal, hotspots, reports, ingestion runs, lives in **Amazon DynamoDB**.

See [WHITEPAPER_HYPOTHESIS.md](WHITEPAPER_HYPOTHESIS.md) for the formal gap-and-hypothesis framing.

## What it does

- **Always-on forecast** with inline confidence. The forecast is shown from day one; sharpness is governed by automated fitness gates plus a human promotion step.
- **Click-to-trace provenance.** Tap any map cell to see kernel contributions, gate verdicts, and a nearby evidence sample.
- **Fitness-gate dashboard** with **integrity conditions** (scope disclosures: single station, effort assumptions, excluded covariates, detector QC status) and Level 1 PSTH visuals + glossary tooltips.
- **Exploration guide (`/explore`).** Multi-turn navigation of gates and provenance, session history in PostgreSQL; operational truth stays in DynamoDB. Optional **surface planner** at `/explore?planner=1` (WorkOS): keyed `POST /api/interactions/plan` returns `ui_intent` panels (map, gates, decisions, provenance).
- **Central Casting.** Managed agents (`explore-guide-v1`, `surface-planner-v1`, keyed reviewers) with prepare-then-narrate skills; configs in DynamoDB `managed-agents` table.
- **Sighting check (`/ask`).** Drop a pin, describe what you saw; Bedrock Haiku narrates an evidence-backed read that separates encounter likelihood from sighting verification, grounded in the same gates and provenance.
- **Field journal (`/journal`).** Private observations and notes; publish sends a copy to the moderation queue when the user chooses.
- **Citizen-science moderation queue.** Shore sightings are quarantined until a signed-in reviewer approves; approval attaches attribution and low reliability weight.
- **Human-in-the-loop promotion.** Automated gates are necessary but not sufficient; promotion decisions are written to an immutable audit log.

## AWS Database(s) used: Amazon DynamoDB (primary) + PostgreSQL (exploration sessions)

S3 is object storage, not a database. DynamoDB is the system of record for every operational entity the app reads and writes. **PostgreSQL (RDS)** stores exploration guide session turns on `/explore` only, not sightings, gates, or audit records. S3 holds supporting time-series files and fit artifacts.

**Nine DynamoDB tables** (region us-west-2, on-demand):

| Table | Role |
|---|---|
| `orcast-aws-backend-sightings` | Normalized sightings with source provenance |
| `orcast-aws-backend-community-submissions` | Citizen-science moderation queue |
| `orcast-aws-backend-decision-records` | Immutable human promotion-decision audit log |
| `orcast-aws-backend-user-journal` | Per-user private field journal (WorkOS-scoped) |
| `orcast-aws-backend-hotspots` | Computed probability hotspots |
| `orcast-aws-backend-reports` | Probability reports |
| `orcast-aws-backend-ingestion-runs` | Per-run ingestion audit |
| `orcast-aws-backend-partner-api-keys` | Partner OpenAPI gateway keys |
| `orcast-aws-backend-managed-agents` | Central Casting managed agent configs |

See [DYNAMODB_PROOF.md](DYNAMODB_PROOF.md).

## Architecture

See [figures/architecture.png](figures/architecture.png). The Next.js app on Vercel calls a same-origin server-side proxy (`/api/be`) that injects the API key and WorkOS reviewer identity server-side. The proxy forwards to FastAPI on AWS App Runner, which reads/writes DynamoDB and S3, and writes exploration session turns to PostgreSQL. **Central Casting** routes (`/api/interactions/prepare`, `/plan`, `/narrate`) run managed agents with a skill manifest; narration may use Vercel AI Gateway on H0. Step Functions orchestrates ingest → fit → gate → human approval; kernel fit runs as a container-image Lambda (scipy/statsmodels). Sighting check and exploration guide use Amazon Bedrock (Claude Haiku) with deterministic template fallback.

## Tech stack

- Frontend: Next.js (App Router) + TypeScript on Vercel; Google Maps.
- Auth: WorkOS AuthKit for reviewer actions (moderation, journal, promotion, PII reads); public forecast/gates/ask stay open.
- LLM: Amazon Bedrock (Haiku) for sighting-check narration only; grounded in live API context.
- Backend: FastAPI on AWS App Runner (ECR).
- Data: DynamoDB (primary, 9 tables), S3 (time series + artifacts).
- Orchestration: Step Functions + Lambda + EventBridge.

## 3-minute demo script (keyed to the live UI)

1. **(0:00–0:20) Problem + home.** Open https://orcast-h0.vercel.app. "Wildlife forecasts hide how thin the evidence is. **orcast** shows the map anyway, but only the confidence the gates have earned."
2. **(0:20–0:45) Provenance.** Tap a water cell in the pilot region. Show kernels, gate verdicts, nearby evidence. "Nothing is asserted without a back-link."
3. **(0:45–1:15) Gates.** Open `/gates`. Walk integrity conditions and Level 1 PSTH. "When gates fail or data is partial, we say so on the surface, not in a footnote."
4. **(1:15–1:35) Explore planner (optional).** Sign in. Open `/explore?planner=1`, ask "show gates and provenance for this cell." Show `ui_intent` panels updating. "Central Casting plans the surface before narration."
5. **(1:35–2:00) Journal + moderation + DynamoDB.** Sign in (WorkOS). `/journal` → save → **Publish to community**. `/moderation` → approve. "Private notes stay private until publish; the queue is DynamoDB."
6. **(2:00–2:25) Database proof.** AWS Console → DynamoDB → nine `orcast-aws-backend-*` tables.
7. **(2:25–3:00) Architecture + close.** Show [architecture.png](figures/architecture.png). "Vercel → App Runner → DynamoDB + Central Casting. Built for audits, not black boxes."

Full beat sheet: [DEMO_STORYBOARD.md](DEMO_STORYBOARD.md).

## Submission checklist

- [x] Published Vercel project: https://orcast-h0.vercel.app
- [x] Description (this file + DEVPOST_DRAFT.md)
- [ ] ~3-minute demo video
- [x] AWS Database: DynamoDB (9 tables)
- [x] Vercel Team ID: `team_dQQph8zC78tTPHDnGnvawdKo`
- [x] Architecture diagram: [figures/architecture.png](figures/architecture.png)
- [ ] DynamoDB screenshot: console or [figures/dynamodb-proof.png](figures/dynamodb-proof.png)
