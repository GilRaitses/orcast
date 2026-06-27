# LinkedIn post, draft v1

**Author:** Gil Raitses / aimez.ai  
**Status:** Draft. Review against CLAIM_BOUNDARIES.md before posting.

---

I've been building orcast, a gate-bounded encounter forecasting system for Southern Resident killer whales, as an aimez.ai research project submitted to the AWS + Vercel hackathon.

The core idea is that a forecast you can't audit isn't trustworthy. So every displayed confidence value in orcast is earned, not assumed.

**The gate battery:**
A fitted cyclic kernel (diel, lunar, seasonal) has to clear a phase-shuffled null test, a time-rescaling goodness-of-fit check, a held-out deviance skill gate, and PIT calibration before contributing to displayed confidence. If it fails any gate, the map shows the integrity condition, not a blank, the forecast, plus the exact reason confidence is withheld. The current effective confidence is 0%. That's the correct answer: the CV deviance skill is −0.018 (3 of 5 folds passing).

**The provenance panel:**
Click any map cell. You get a drilldown to the acoustic detections, fitted kernels, and gate verdicts that produced that cell's value. The provenance graph renders the interaction step-log as a typed node graph: Claim → Method → Experiment → Data → Research. Every annotation is bound to an artifact ID.

**The sighting check panel (/ask):**
Field observers can describe what they saw, upload a photo or audio clip, and get an encounter likelihood framing grounded in the live gate state, not a yes/no from a language model's parametric knowledge. Bedrock narrates from structured context; the step-log traces which skills ran and what artifacts they referenced.

**The exploration guide (/explore):**
A multi-turn guided tour of gates, provenance, and the surface planner. At `/explore?planner=1` a managed AI agent dispatches skill-dispatch panels in sequence, the routing is plan-then-execute, not open-ended generation.

**The grounding benchmark:**
This is the finding that surprised me. When the surface planner's interaction step-log is injected as RAG context to the Gemini Interactions API, the unsupported scientific claim rate drops from 60–100% (Maps-only geospatial grounding baseline across query types, 2026-06-24) to 0%. The difference is not better citation generation, the query type changed. Injecting a complete reasoning trace transforms an open-domain science question into a closed artifact-reference question. The model answers from the step-log.

That diagnostic, step-log injection achieves full grounding; narrowly structured context achieves none, is the basis of a companion paper on grounding quality measurement for orchestrator-in-the-loop agentic systems.

**Stack:** Amazon DynamoDB (9 tables, system of record), AWS App Runner, Vercel, AWS Step Functions, Amazon Bedrock, S3, WorkOS AuthKit.

Live: https://orcast-h0.vercel.app  
Whitepaper 1 (forecasting architecture): docs/whitepaper/Build/Raitses_orcast_2026_share.pdf  
Whitepaper 2 (grounding benchmark): docs/whitepaper2/Build/Raitses_orcast_grounding_2026_share.pdf

---

**Capture for post (to add before publishing):**
- Screen recording or GIF: forecast map → click cell → provenance drilldown (shows Claim/Method/Experiment graph)
- Screen recording or GIF: /explore routing demo (planner dispatching panels in sequence)
- Screen recording or GIF: /ask sighting check with evidence upload
- Screenshot: gates dashboard showing integrity conditions + 0% confidence with reason
- Screenshot: architecture.png from submission figures

**Review notes before posting:**
- "0% effective confidence is correct" framing must stay
- Do not add "predicts whale locations" or "identifies orca from photos"
- Grounding benchmark numbers require the date: 2026-06-24
- LeCun/AMI connection is future-work only, do not claim orcast fills that gap
