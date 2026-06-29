# IC8 — Casting follow-on objectives (planned)

Status: **planned** — Wave Set **S4** PASS; charter after H1 unless demo video needs J3 ASL clerk.  
Predecessor: **IC7** (surface planner deploy complete).

## J3 / IC8a — Step Functions promotion clerk

**Goal:** On human-wait in [`forecast_orchestrator.asl.json`](../../../infra/aws/stepfunctions/forecast_orchestrator.asl.json), invoke `promotion-clerk-v1` via `/api/interactions/prepare` (keyed).

**Acceptance:**

- ASL task calls App Runner with cast key
- Clerk skill `fetch_pending_approval` + `fetch_supervisor_recommendation` in step log
- Local test + prod smoke extension

## J4 / IC8b — LLM surface planner

**Goal:** Replace keyword rules in [`planner.py`](../../../src/aws_backend/casting/planner.py) with schema-validated Bedrock/Haiku JSON when `ManagedAgentPolicy.planner_mode == "llm"`.

**Acceptance:**

- JSON schema matches [`UI_INTENT_SCHEMA.md`](UI_INTENT_SCHEMA.md)
- Feature flag per agent; default remains deterministic
- `ic6-local` + `ic6-gate` regression PASS

## J5 / IC8c — sighting-check-v1 skill

**Goal:** Ship keyed skill + seed per [`M4_NEXT_OBJECTIVES.md`](M4_NEXT_OBJECTIVES.md).

**Acceptance:**

- Skill in manifest T2/T3 as scoped
- Seed agent or attach to explore-guide policy
- Tests in `test_interactions_plan.py` or skill suite

## IC8d — Deploy hygiene

**Goal:** Avoid CFN rollback on image-only deploy (IC7 lesson).

**Deliverables:**

- Script: merge App Runner env on image update
- Align CFN `ContainerImage` param with live tag in manifest
- Document in [`tools/deployment/aws/deploy.sh`](../../../tools/deployment/aws/deploy.sh) header

## Gates (to add when chartered)

- `ic8-local.sh` — ASL unit + clerk prepare mock
- `ic8-gate` — prod human-wait smoke (optional)

Registry: add IC8/J3–J5 entries when work starts; set `next_wave_set: IC8` only after S set closes.
