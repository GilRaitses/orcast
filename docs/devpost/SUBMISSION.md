# orcast, H0 submission

H0: Hack the Zero Stack. Track: Open innovation. Primary AWS database: Amazon DynamoDB. Frontend: Next.js on Vercel.

## Tagline

orcast is a two-sided loop around Salish Sea killer whales. Encounter forecasting is the grounding layer that both a public visitor console and a behavior-analysis research workbench stand on, and an AI orchestration layer is set up for shared benefit across three parties, the tourists who visit, the researchers who study whale behavior, and the whales themselves.

## The two-sided loop

Encounter forecasting is the grounding layer, not the end product. Both sides of the loop stand on the same forecast, and each side improves it.

The A side is the visitor console. A visitor states intent and the console transduces that intent into planning objects, the map, gates, decision, and provenance panels the visitor acts on. Trip use cases such as a shore watch, a kayak outing, or a ferry crossing share one grounding forecast, so the forecast is the substrate the planning objects are built on rather than a separate feature.

The B side is a behavior-analysis research workbench. It carries collaborative review of community reports today, and the build is extending toward dtag modeling replay and a terrain and bathymetry 3D twin of the San Juan Islands. The workbench exists to close a gap that advances both sides. Sharper behavior analysis sharpens the forecast that grounds the visitor trips, and the visitor activity and the twin give the research side more to work with.

The bridge is an AI managed-orchestration layer that runs the routines across both sides. It is the orchestration direction set out by the pax Friend console, the liquid-glass research console tracked in the LGC lane. That console is chartered and not yet shipped, so it is the direction the orchestration is built toward rather than a delivered surface. It is set up for the best shared benefit across conservation, enjoyment, and rigor, for the tourists visiting the Salish Sea, the researchers studying whale behavior, and the whales themselves.

## Problem, for whom, and why

Wildlife and environmental forecasts present a smooth, confident surface that hides how thin or biased the underlying evidence is. A shore or kayak whale-watcher looking at a "hotspot" cannot tell whether it reflects real animal behavior or just where people happened to look. Researchers and data stewards have no audit trail from a displayed prediction back to the observations and statistical checks behind it.

orcast serves three parties at once. Shore and kayak whale-watchers act on the public forecast, the sighting check, and the field journal. Field scientists and naturalists work the fitness-gate dashboard, the provenance drill-down, the glossary, and the research workbench. Data stewards run the citizen-science moderation queue and the human promotion approvals. The whales themselves are the third party the loop is set up to benefit, because a forecast that does not oversell and a research side that sharpens it together steer attention and effort more honestly.

Why this problem. The Southern Resident killer whales are endangered, sightings are effort-biased, and acoustic detections are sparse. An auditable forecast with explicit integrity conditions is more useful than a falsely precise one. Every operational entity, sightings, moderation queue, decision audit log, field journal, hotspots, reports, and ingestion runs, lives in **Amazon DynamoDB**.

See [WHITEPAPER_HYPOTHESIS.md](WHITEPAPER_HYPOTHESIS.md) for the formal gap-and-hypothesis framing.

## What it does

The forecast is the grounding layer under everything below. The visitor console reads it to build planning objects, and the research and stewardship tools read and improve it. The capabilities that ship today are the A side of the loop plus the stewardship seam.

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

1. **(0:00–0:20) Problem + home.** Open https://orcast-h0.vercel.app. "Wildlife forecasts hide how thin the evidence is. **orcast** shows the map anyway, but only the confidence the gates have earned. This forecast is the grounding layer that a visitor console and a research workbench both stand on."
2. **(0:20–0:45) Provenance.** Tap a water cell in the pilot region. Show kernels, gate verdicts, nearby evidence. "Nothing is asserted without a back-link."
3. **(0:45–1:15) Gates.** Open `/gates`. Walk integrity conditions and Level 1 PSTH. "When gates fail or data is partial, we say so on the surface, not in a footnote."
4. **(1:15–1:35) Explore planner (optional).** Sign in. Open `/explore?planner=1`, ask "show gates and provenance for this cell." Show `ui_intent` panels updating. "Central Casting plans the surface before narration."
5. **(1:35–2:00) Journal + moderation + DynamoDB.** Sign in (WorkOS). `/journal` → save → **Publish to community**. `/moderation` → approve. "Private notes stay private until publish; the queue is DynamoDB."
6. **(2:00–2:25) Database proof.** AWS Console → DynamoDB → nine `orcast-aws-backend-*` tables.
7. **(2:25–3:00) Architecture + close.** Show [architecture.png](figures/architecture.png). "Vercel frontend, App Runner API, DynamoDB system of record, and Central Casting interactions. The forecast grounds a visitor console and a research workbench, and the orchestration direction serves tourists, researchers, and the whales themselves. Built for audits, not black boxes."

Full beat sheet: [DEMO_STORYBOARD.md](DEMO_STORYBOARD.md).

## Submission checklist

- [x] Published Vercel project: https://orcast-h0.vercel.app
- [x] Description (this file + DEVPOST_DRAFT.md)
- [ ] ~3-minute demo video
- [x] AWS Database: DynamoDB (9 tables)
- [x] Vercel Team ID: `team_dQQph8zC78tTPHDnGnvawdKo`
- [x] Architecture diagram: [figures/architecture.png](figures/architecture.png)
- [ ] DynamoDB screenshot: console or [figures/dynamodb-proof.png](figures/dynamodb-proof.png)
