# J0 — Surface planner charter (Wave Set IC6 / J)

**Date:** 2026-06-23  
**Family:** IC (Interactions Casting) + J (keyed cast roles)  
**Baseline:** Wave Set IC5 (prepare-then-narrate + Gateway narration)

## Purpose

Add a **keyed-only surface planner** that emits a validated **UI intent schema** (`panels[]`, `skill_plan[]`, `deep_links[]`) so H0 clients can render an active surface without giving the chat model direct database or embedding access.

Public explore (`explore-guide-v1`) stays **prepare-then-narrate** with deterministic T0/T1 skills.

## Architecture boundary

| Layer | Role | Auth |
|-------|------|------|
| Chat surface | User message + map viewport | Public session |
| Public concierge | `explore-guide-v1` → fixed skills → narrate JSON | Rate-limited |
| **Keyed planner** | `surface-planner-v1` → `ui_intent` → execute `skill_plan` | `X-ORCAST-Key` |
| Step Functions | Fit / gate / promotion batch | Keyed automation |

The planner **does not** pick tools at runtime via LLM function calling. MVP planning is deterministic keyword rules; optional stretch is structured JSON from Haiku with schema validation.

## Relationship to Step Functions

[`forecast_orchestrator.asl.json`](../../../infra/aws/stepfunctions/forecast_orchestrator.asl.json) remains the **batch governance** orchestrator. Wave J seeds `promotion-clerk-v1` as the read-only cast face of DraftPromotion/AwaitHumanDecision—not a replacement for ASL.

## Auth matrix

| Route | Skills | Output |
|-------|--------|--------|
| `POST /api/interactions` | T0, T1 | `reply`, `steps`, `annotations` |
| `POST /api/interactions/prepare` | T0, T1 | grounded `context` |
| `POST /api/interactions/plan` | T0–T3 per agent | `ui_intent` + `prepare` |

## Out of scope (IC6/J)

- Embedding stores, vector search, RAG loops
- Public `/api/interactions/plan`
- LLM-chosen tools on any route
- Write skills / promotion apply
- Angular active surface (H0 Next.js only)

## Cross-links

- Schema: [UI_INTENT_SCHEMA.md](UI_INTENT_SCHEMA.md)
- Grounding: [INTERACTIONS_GROUNDING_PATTERN.md](INTERACTIONS_GROUNDING_PATTERN.md)
- Skills: [SKILL_CATALOG.md](SKILL_CATALOG.md)
- Panel registry: [`panel_registry.json`](../../../src/aws_backend/casting/panel_registry.json)

## Exit bar

- [x] `UI_INTENT_SCHEMA.md` published
- [x] `panel_registry.json` checked in
- [x] Keyed `/plan` route documented in `docs/API.md`
- [x] `ic6-doc-grep` PASS
