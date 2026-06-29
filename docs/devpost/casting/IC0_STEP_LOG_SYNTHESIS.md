# IC0 — step-log synthesis for skill catalog

**Date:** 2026-06-23  
**Family:** IC (Interactions Casting)  
**Baseline:** Wave Set M (Central Casting MVP)

## Purpose

Synthesize authoritative “step logs” from this workspace into a tiered skill catalog. There is no single runtime step-log file; inventories come from orchestrator ASL, H0 architecture, workflow truth table, and existing interaction trace columns.

## IC0-A — ASL orchestrator steps

Source: [`infra/aws/stepfunctions/forecast_orchestrator.asl.json`](../../../infra/aws/stepfunctions/forecast_orchestrator.asl.json)

| ASL state | Batch role | Proposed read skill (Wave J) | Write? |
|-----------|------------|------------------------------|--------|
| Ingest | Pull sources → sightings | `fetch_ingestion_status` | no |
| FreezeSnapshot | Pin `snap_id` | `fetch_snapshot_manifest` | no |
| FitAndGate | Fit + gate summary | `fetch_fit_summary` | no |
| DraftPromotion | Supervisor draft | `fetch_supervisor_recommendation` | no |
| AwaitHumanDecision | Human token wait | `fetch_pending_approval` | no |
| ApplyPromotion | Promote confidence | — | **write — excluded** |
| HoldLowConfidence | Pass-through | — | — |

Orchestrator steps inform **T3 batch cast roles** (`promotion-clerk-v1`, `dossier-explainer-v1`), not public explore concierge.

## IC0-B — H0 reasoning components

Source: [`H0_ARCHITECTURE.md`](../../H0_ARCHITECTURE.md) agent DAG

| Component | Concierge skill domain | Status |
|-----------|------------------------|--------|
| Source adapters | `fetch_realtime_events`, `fetch_verified_sightings` | live reads |
| Validation-gate referee | `fetch_gates` | live |
| Forecaster | `fetch_provenance`, `fetch_forecast_cell` | live |
| Promotion supervisor | `fetch_supervisor_recommendation` | partially live |
| Traceability | artifact citations (`repr_id`, `run_id`, `snap_id`) | partially live |

## IC0-C — Live GET API inventory

| GET route | Router | Proposed skill | Truth label |
|-----------|--------|----------------|-------------|
| `/api/gates` | kernel | (via `fetch_gates`) | live |
| `/api/provenance` | kernel | (via `fetch_provenance`) | live |
| `/api/hotspots` | read | (via `fetch_hotspots`) | live |
| `/api/environmental` | read | `fetch_environmental` | live |
| `/api/live-hydrophones` | read | `fetch_live_hydrophones` | live |
| `/api/realtime/events` | read | `fetch_realtime_events` | live |
| `/api/data-status` | timeseries | `fetch_data_status` | partially live |
| `/api/verified-sightings` | read | `fetch_verified_sightings` | live |
| `/api/review-dossier/latest` | review_dossier | `fetch_review_dossier_summary` | partially live (keyed) |
| `/api/decision-records` | kernel | `fetch_decision_records` | live (keyed) |

## IC0-D — Gap table (M catalog vs synthesis)

| Skill | In M `SKILL_CATALOG` | IC synthesis |
|-------|----------------------|--------------|
| `fetch_gates` | yes | keep T0 |
| `fetch_provenance` | yes | keep T1 |
| `fetch_hotspots` | yes | keep T0 |
| `fetch_forecast_cell` | yes | keep T1 |
| `fetch_environmental` | no | add T0 (IC2) |
| `fetch_live_hydrophones` | no | add T0 (IC2) |
| `fetch_realtime_events` | no | add T0 (IC2) |
| `fetch_data_status` | no | add T0 (IC2) |
| `fetch_verified_sightings` | no | add T0 (IC2) |
| T2/T3 reserved | no | document `enabled: false` |

## IC0-E — Recommended tiering

| Tier | Auth | Geo | Examples |
|------|------|-----|----------|
| **T0** | Public + rate limit | optional | `fetch_gates`, `fetch_hotspots`, `fetch_environmental`, … |
| **T1** | Public + rate limit | **required** | `fetch_provenance`, `fetch_forecast_cell` |
| **T2** | Keyed (`X-ORCAST-Key`) | optional | `fetch_review_dossier_summary`, `fetch_decision_records` |
| **T3** | Keyed / Step Functions | optional | `fetch_pending_approval`, `fetch_supervisor_recommendation` |

## Runtime trace gap (migration 003 → 004)

Migration `003` stores flat trace fields. IC1 adds `interaction_steps JSONB` for ordered steps matching [`INTERACTIONS_GROUNDING_PATTERN.md`](INTERACTIONS_GROUNDING_PATTERN.md).

## IC0 exit bar

- [x] ASL + H0 + API inventory documented
- [x] Tiering assigned
- [x] Reserved skills marked for Wave J
- [x] No Google/Gemini services
