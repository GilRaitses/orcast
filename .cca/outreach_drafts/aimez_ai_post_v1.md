# aimez.ai post, orcast research release

**Surface:** aimez.ai (website / project page)  
**Author:** Gil Raitses, aimez.ai  
**Status:** Draft. Review against CLAIM_BOUNDARIES.md before publishing.

---

## orcast: gate-bounded encounter forecasting for Southern Resident killer whales

**aimez.ai research project · AWS + Vercel hackathon submission · June 2026**

Wildlife forecasting products display smooth probability maps with no record of the evidence that produced them. A displayed hotspot could reflect animal behavior, observer bias, acoustic detector false positives, or model overfitting, the map gives you no way to tell. This is the epistemic gap that orcast addresses.

---

### What orcast does

**Gate-bounded confidence.** Every confidence value displayed on the forecast map has passed a statistical gate battery: a phase-shuffled null test on each cyclic kernel, a time-rescaling goodness-of-fit test, held-out deviance skill, and PIT calibration. A gate failure surfaces an integrity condition, not a hidden blank, alongside the forecast. The current effective confidence is 0% because the deviance skill is −0.018. That is the correct answer.

**Per-cell provenance drilldown.** Clicking any map cell opens a provenance panel tracing the cell's value to its generating acoustic detections, fitted kernels, and gate verdicts. The provenance graph renders the interaction step-log as a typed node structure: Claim (C), Method (M), Experiment (X), Data (D), Research (R). Every annotation is bound to an artifact identifier.

**Interactive panels across the platform:**

- **Forecast map**, heatmap of encounter likelihood with live gate-bounded confidence, cell-level provenance on click
- **Gates panel**, full integrity condition dashboard, Level 1 PSTH kernel visualization, equations, and glossary
- **Sighting check** (`/ask`), field observers describe or upload evidence (image, audio); Bedrock narrates encounter likelihood from structured skill context, not from parametric LLM knowledge; the step-log traces every skill invocation and artifact reference
- **Field journal** (`/journal`), private field notes; publishing sends to the community moderation queue
- **Moderation queue**, citizen shore sightings stay quarantined until a WorkOS-authenticated reviewer signs off; the decision record is immutable in DynamoDB
- **Exploration guide** (`/explore`), multi-turn guided routing through gates, provenance, and surface planner panels; at `/explore?planner=1` the managed surface planner dispatches a `ui_intent` panel sequence via Central Casting

**Routing architecture.** The surface planner is a plan-then-execute agent: it emits a `skill_plan` before dispatch, executes only the skills in the cast role's allow-list, and narrates after all skills complete. The step-log records every intermediate state: which skills ran, what artifacts they returned, what the model annotated. This is the audit substrate.

---

### The grounding quality benchmark

The surface planner's step-log, injected as RAG context to the Gemini Interactions API (gemini-3.5-flash, 2026-06-24), reduces the unsupported scientific claim rate from 60–100% (Maps-only geospatial grounding baseline, across query types) to 0% in the surface-planner step-log scenario, the strongest of eight parallel benchmark scenarios. The mechanism is query transformation: injecting a complete reasoning trace converts an open-domain marine science question into a closed artifact-reference question. The language model answers from the step-log, not from world knowledge.

This finding is the basis of a companion paper: *Grounding quality measurement for orchestrated AI reasoning chains: evidence-binding rate as an evaluation primitive for orchestrator-in-the-loop agentic systems* (aimez.ai, 2026).

The `R_uncited` metric, the fraction of scientific sentences in a system's output with no bound citation, is the evaluation primitive. It is architecture-diagnostic: two systems with identical surface accuracy can have very different `R_uncited` values depending on whether their reasoning traces are passed as context. The benchmark tool is reproducible at `tools/testing/grounding_parallel_rag.py`.

---

### System of record

Nine Amazon DynamoDB tables in us-west-2: `sightings`, `community-submissions`, `decision-records`, `user-journal`, `hotspots`, `reports`, `ingestion-runs`, `partner-api-keys`, `managed-agents`. DynamoDB is the system of record; every confidence-bearing surface is auditable to a specific table entry.

Stack: Next.js · Vercel · FastAPI · AWS App Runner · Amazon Bedrock · AWS Step Functions · AWS S3 · WorkOS AuthKit · Google Maps.

---

### Research outputs

**Whitepaper 1**, *Evidence-bounded encounter forecasting: an honest-model architecture for effort-biased wildlife observation data*  
Gil Raitses, aimez.ai (2026) · 7 pp (share PDF) · arXiv link pending

**Whitepaper 2**, *Grounding quality measurement for orchestrated AI reasoning chains: evidence-binding rate as an evaluation primitive for orchestrator-in-the-loop agentic systems*  
Gil Raitses, aimez.ai (2026) · 4 pp (share PDF) · arXiv link pending

---

### Live demo

https://orcast-h0.vercel.app

---

**Capture needed before publishing:**
- GIF: forecast map → cell click → provenance panel drilldown (C/M/X node graph)
- GIF: /explore routing demo, surface planner dispatching panel sequence
- GIF: /ask sighting check with evidence upload → Bedrock narration
- Screenshot: gates dashboard (integrity conditions + 0% confidence display)
- Screenshot or GIF: moderation queue approve/reject flow
- PNG: architecture diagram (available at docs/devpost/figures/architecture.png)
- PNG: DynamoDB ERD (docs/figures/fig-01-erd-dynamodb/figure.png)

**Review notes:**
- Do not claim "predicts whale locations" or "identifies orca from images"
- 0% confidence must be framed as correct, not as a limitation
- LeCun AMI connection is future-work only; do not claim orcast fills that gap
- All quantitative claims must use exact numbers from CLAIM_BOUNDARIES.md
