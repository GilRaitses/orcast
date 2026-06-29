# S0 — Submission materials sync charter

Date: 2026-06-26  
Wave set: **S** (Submission)  
Predecessor: Wave Set **IC** closed at **IC7** (surface planner deploy)  
Capstone: **H1** manual Devpost submit (depends on **S4**)

## Purpose

Bring judge-facing submission artifacts in line with production after Central Casting, surface planner (`/plan`, `ui_intent`), and managed-agents table shipped in IC6–IC7.

## Truth audit (stale vs prod)

| Claim in submission pack | Prod truth | Fix wave |
|--------------------------|------------|----------|
| "Seven DynamoDB tables" | **Nine** on-demand tables in CFN ([template.yaml](../../../infra/aws/template.yaml)): 7 operational + `partner-api-keys` + `managed-agents` | S3, DYNAMODB_PROOF |
| Architecture diagram | Missing Central Casting, `/api/interactions/*`, Vercel AI Gateway, H0 planner | S1 |
| ERD pages 1–5 | No `managed-agents` entity; PNGs may predate casting | S2 |
| Demo script | No `/explore?planner=1`, no casting narration path | S3 |
| [`WAVES_REGISTRY.md`](../WAVES_REGISTRY.md) | Stops at IC5 | S0 registry sync |
| Research **I7** diagram debt | Overlaps S2 ERD export | S2 closes I7 diagram portion |

### Nine DynamoDB tables (us-west-2)

| Table suffix | Role |
|--------------|------|
| `sightings` | Normalized sightings |
| `community-submissions` | Moderation queue |
| `decision-records` | Promotion audit log |
| `user-journal` | Private field journal |
| `hotspots` | Forecast hotspots |
| `reports` | Probability reports |
| `ingestion-runs` | Ingest audit |
| `partner-api-keys` | Partner gateway keys |
| `managed-agents` | Central Casting agent configs |

PostgreSQL (RDS) holds exploration session turns only — not counted as DynamoDB.

## Wave breakdown

### S1 — Architecture diagram

**Inputs:** [`figures/architecture.mmd`](../figures/architecture.mmd)  
**Deliverables:**

- Add subgraph or nodes: Central Casting (`/api/interactions/prepare`, `/plan`, `/narrate`), managed-agents DDB table, panel registry, Vercel AI Gateway path
- H0: `/explore?planner=1`, `ActiveSurfaceHost`, WorkOS + keyed proxy
- Re-export `figures/architecture.png` via mermaid-cli
- **Visual verify:** read PNG before marking done

**Acceptance:**

- PNG shows casting + 9th DDB table (managed-agents)
- Gateway path visible for narration
- No regression on Step Functions / existing tables

### S2 — ERD / workflow pages

**Inputs:** [`figures/orcast-erd-workflows.drawio`](../figures/orcast-erd-workflows.drawio), [`figures/_pages/STYLE_SPEC.md`](../figures/_pages/STYLE_SPEC.md)  
**Deliverables:**

- Page 1: add `managed-agents` entity + logical refs to casting routes
- Re-export pages 1–5 PNGs to `figures/orcast-erd-workflows-page*.png`
- **Visual verify:** read page1 + page5 PNGs

**Acceptance:**

- Page 1 legend still states DynamoDB logical refs (no enforced FK)
- Managed-agents visible on schema page
- Closes research I7 "drawio re-export pending" item

### S3 — Copy sync

**Files:**

- [`SUBMISSION.md`](../SUBMISSION.md)
- [`DEVPOST_DRAFT.md`](../DEVPOST_DRAFT.md)
- [`DEMO_STORYBOARD.md`](../DEMO_STORYBOARD.md)
- [`DYNAMODB_PROOF.md`](../DYNAMODB_PROOF.md)
- [`README.md`](../README.md)
- [`HACKATHON_SUBMIT_CHECKLIST.md`](../HACKATHON_SUBMIT_CHECKLIST.md)

**Acceptance:**

- Table count = nine everywhere (or explicit list)
- Demo beat: optional `/explore?planner=1` surface planner (30s)
- Central Casting + prepare-then-narrate mentioned in architecture section
- Architecture figure ref points to updated PNG

### S4 — Submission gate

**Deliverables:**

- `tools/waves/gates/s-doc-grep.sh`
- `./tools/waves/run-gate.sh s-gate` (doc grep + ic6-gate regression optional)

**Acceptance:**

- `s-doc-grep` PASS
- Registry entries S0–S4 present; `next_wave_set: S`

## Deferred (not in Wave Set S)

| Track | Notes |
|-------|-------|
| **IC8** | J3 ASL clerk, J4 LLM planner, J5 sighting-check — see [`IC8_NEXT_OBJECTIVES.md`](../casting/IC8_NEXT_OBJECTIVES.md) |
| **P1** | Adversarial probes — optional between S3 and S4 |
| **I2–I6** | Research rigor — post-hackathon |
| **D, U** | Data wiring, Angular map UX |

## Execution order

1. S0 (charter) — **done**
2. S1 + S3 — **done**
3. S2 (drawio export) — **done**
4. S4 gate — **done** (`./tools/waves/run-gate.sh s-gate` PASS)
5. Wave Set **A** — agent demo automation — [A0_AGENT_DEMO_CHARTER.md](A0_AGENT_DEMO_CHARTER.md) → `./tools/waves/run-gate.sh a-gate`
6. **H1** manual submit — [H1_MANUAL_SUBMIT.md](H1_MANUAL_SUBMIT.md)
7. IC8 / P1 — optional after H1

## pax orchestrator note

Cross-repo handoff: [`pax/.cca/catalogue/O0/20260626_wave-set-j-keyed-cast/ORCAST_ORCHESTRATOR_HANDOFF.md`](../../../../pax/.cca/catalogue/O0/20260626_wave-set-j-keyed-cast/ORCAST_ORCHESTRATOR_HANDOFF.md). Pax Wave Set J complete; ORCAST IC7 closed surface-planner gap. Pax does not run S waves unless demo copy references pax surfaces.
