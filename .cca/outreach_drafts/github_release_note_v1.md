# GitHub release note — draft v1

**Tag:** v0.1.0-hackathon  
**Status:** Draft. Review against CLAIM_BOUNDARIES.md before publishing.

---

## orcast v0.1.0 — AWS + Vercel hackathon submission

Gate-bounded encounter forecasting and community platform for field researchers.

### What it does

A gate-bounded encounter forecast for Southern Resident killer whales in the San Juan Islands. Every displayed confidence value is bounded by a statistical gate battery (phase-shuffled null test, held-out deviance skill, PIT calibration, human promotion decision). A 0% confidence value means the model fitted but the gates correctly suppress the display.

Every map cell links to the acoustic detections, kernel fits, and gate verdicts that produced it. Click any cell for the full provenance trace.

Community shore sightings enter a quarantine queue. A WorkOS-authenticated reviewer approves or rejects before any submission influences the model.

### Architecture

- **Vercel** — Next.js frontend with agent-automation demo path
- **App Runner** — FastAPI backend with Central Casting managed agents
- **DynamoDB** — 9 on-demand tables (system of record)
- **S3** — time-series + fitted kernel artifacts + evidence uploads
- **Step Functions** — fit / gate / promote pipeline
- **Amazon Bedrock** — sighting check narration (Claude Haiku)

### Grounding quality benchmark

The surface planner's interaction step-log, injected as RAG context to the Gemini Interactions API, reduces the unsupported scientific claim rate (R_uncited) from 60–100% (Maps-only geospatial grounding baseline, across query types) to 0%. Measured 2026-06-24 across 8 parallel scenarios. Tool: `tools/testing/grounding_parallel_rag.py`.

### Research

- Whitepaper 1: Evidence-bounded encounter forecasting (10 pp). Anchored on Olson et al. 2018 (opportunistic SRKW sightings) + Diggle et al. 2010 (preferential-sampling correction).
- Whitepaper 2: Grounding quality measurement for orchestrated AI reasoning chains, an evaluation primitive for human-in-the-loop agentic systems (5 pp). Anchored on Magentic-UI (Microsoft 2025) + Horvitz 1999 (mixed-initiative).
- 16 Emergent Mind search family summaries in `docs/whitepaper/research/`
- arXiv bundles built and validated; arXiv link pending (WP1, WP2)

### Live demo

https://orcast-h0.vercel.app

---

**Review notes before publishing:**
- Add arXiv links when papers are submitted
- Do not change the R_uncited framing
- The "0% means correct" explanation must stay in the release notes
