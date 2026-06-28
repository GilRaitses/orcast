# Devpost draft — copy/paste field by field

Update bracketed items after you record the video / capture the console shot.

---

**Project name**

orcast

**Subtitle / full title**

Physical world model fusion for orca encounter forecasting and community platform for field researchers

**Elevator pitch / tagline** (one line)

orcast is a two-sided loop around Salish Sea killer whales. Encounter forecasting is the grounding layer that a public visitor console and a behavior-analysis research workbench both stand on, and an AI orchestration layer is set up for shared benefit across the tourists who visit, the researchers who study whale behavior, and the whales themselves.

**Track**

Open innovation

---

**What it does / Description** (main text field)

Wildlife forecasts usually show a smooth, confident map that hides how thin or biased the evidence is. For an endangered population like the Southern Resident killer whales, watched from shore and kayak, with effort-biased sightings and sparse acoustic detections, that false precision is actively misleading.

**orcast** treats the forecast as a grounding layer rather than the end product. A visitor states intent and the visitor console transduces that intent into planning objects on top of the forecast, the map, gates, decision, and provenance panels the visitor acts on. A behavior-analysis research workbench stands on the same forecast and improves it, carrying collaborative review of community reports today and extending toward dtag modeling replay and a terrain and bathymetry 3D twin. An AI managed-orchestration layer runs the routines across both sides and is set up for shared benefit across three parties, the tourists, the researchers, and the whales themselves. That orchestration follows the pax Friend console direction tracked in the LGC lane, which is chartered and not yet shipped. Every operational entity, sightings, moderation queue, decision audit log, private field journal, hotspots, reports, and ingestion runs, is stored in **Amazon DynamoDB**.

The forecast is a modeled probability not an observed sighting. Detection is a confidence score not ground truth. Probability zones are predictions not guarantees. The 3D twin is modeled not measured.

**Features**

The capabilities that ship today are the A side visitor console plus the stewardship seam. The B side research workbench and the AI orchestration bridge are the direction the build is heading.

- Always-on forecast with inline confidence governed by fitness gates + human promotion (not hidden until "ready").
- Click-to-trace provenance: kernels, gate verdicts, nearby evidence per map cell.
- Gates dashboard with **integrity conditions** and Level 1 PSTH visuals + glossary.
- **Sighting check** (`/ask`): Bedrock-grounded chat that separates encounter likelihood from whether your observation was an orca.
- **Field journal** (`/journal`): private notes; publish sends a copy to the community moderation queue.
- **Citizen-science moderation:** quarantined in DynamoDB until a WorkOS-signed reviewer approves.
- **Exploration guide** (`/explore`): multi-turn gates/provenance tour; optional **surface planner** at `/explore?planner=1` (signed in) plans `ui_intent` panels via Central Casting.
- **Central Casting:** managed agents with prepare-then-narrate skills; agent configs in DynamoDB `managed-agents`.
- **Grounding quality benchmark:** The surface planner step-log reduces unsupported scientific claim rate ($R_\text{uncited}$) from 91% (Maps-only baseline) to **0%** — measured live against the Gemini Interactions API with Google Maps grounding. Eight parallel scenarios benchmarked, 2026-06-24. ([benchmark tool](tools/testing/grounding_parallel_rag.py)) This metric provides the evaluation primitive that LeCun's world model architecture (AMI, V-JEPA) requires for evidence-bound intermediate representations — and which no existing physical-world AI benchmark currently measures.
- Immutable promotion audit log in DynamoDB when a reviewer promotes, holds, or rejects confidence.

**For:** shore/kayak whale-watchers, field scientists, data stewards.

**Hypothesis (whitepaper):** [WHITEPAPER_HYPOTHESIS.md](WHITEPAPER_HYPOTHESIS.md) — we bridge the gap between a forecast you can use in the field and one you can defend in public.

**Built with**

Next.js, TypeScript, Vercel, AWS DynamoDB, AWS App Runner, AWS Lambda, AWS Step Functions, Amazon Bedrock, AWS S3, FastAPI, Python, WorkOS AuthKit, Google Maps, Gemini Interactions API (grounding benchmark).

---

**Which AWS Database(s) did you use?**

Amazon DynamoDB (primary). S3 is supporting object storage only.

Nine on-demand tables in us-west-2: `sightings`, `community-submissions` (moderation queue), `decision-records` (human audit log), `user-journal` (private field notes, WorkOS-scoped), `hotspots`, `reports`, `ingestion-runs`, `partner-api-keys`, `managed-agents` (Central Casting configs).

**Why DynamoDB**

Single-digit-millisecond, on-demand access fits per-entity reads/writes, append-only audit logs, and a spiky citizen-science workload — zero capacity planning for a hackathon-scale demo that still needs transactional integrity.

**Vercel Team ID**

team_dQQph8zC78tTPHDnGnvawdKo

**Live URL**

https://orcast-h0.vercel.app

**Architecture diagram**

Attach `docs/devpost/figures/architecture.png`

**Screenshot proving AWS Database usage**

AWS Console → DynamoDB → Tables (us-west-2) showing nine `orcast-aws-backend-*` tables. Fallback: `docs/devpost/figures/dynamodb-proof.png`.

**Demo video (~3 min)**

[paste link after recording — script in DEMO_STORYBOARD.md]

---

## Devpost checklist

- [x] Live URL: https://orcast-h0.vercel.app
- [x] Description (above)
- [ ] Demo video (~3 min)
- [x] AWS Database: DynamoDB
- [x] Vercel Team ID: team_dQQph8zC78tTPHDnGnvawdKo
- [x] Architecture diagram
- [ ] DynamoDB screenshot
