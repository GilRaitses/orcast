# Central Casting — skill catalog

Human index for [`skills_manifest.json`](../../../src/aws_backend/casting/skills_manifest.json). Synthesized from [`IC0_STEP_LOG_SYNTHESIS.md`](IC0_STEP_LOG_SYNTHESIS.md).

## Tiers

| Tier | Auth | Public `/api/interactions` |
|------|------|----------------------------|
| T0 | Public | allowed |
| T1 | Public (geo required) | allowed when viewport present |
| T2 | Keyed | **rejected** on public route |
| T3 | Keyed / batch | **rejected** on public route |

## Enabled skills — public (T0/T1, IC2)

| ID | Tier | Geo | Truth | Wraps |
|----|------|-----|-------|-------|
| `fetch_gates` | T0 | no | live | fit report + promotion gates |
| `fetch_provenance` | T1 | yes | live | cell kernel provenance |
| `fetch_hotspots` | T0 | no | live | top hotspot cells |
| `fetch_forecast_cell` | T1 | yes | live | cell intensity summary |
| `fetch_environmental` | T0 | no | live | NOAA environmental snapshot |
| `fetch_live_hydrophones` | T0 | no | live | hydrophone catalog in bounds |
| `fetch_realtime_events` | T0 | no | live | recent sightings as events |
| `fetch_data_status` | T0 | no | partially live | stream freshness / backfill status |
| `fetch_verified_sightings` | T0 | no | live | validated sightings subset |

## Enabled skills — keyed (T2/T3, Wave J1)

| ID | Tier | ASL / component |
|----|------|-----------------|
| `fetch_review_dossier_summary` | T2 | review dossier |
| `fetch_decision_records` | T2 | decision log |
| `fetch_supervisor_recommendation` | T3 | DraftPromotion |
| `fetch_pending_approval` | T3 | AwaitHumanDecision |
| `fetch_snapshot_manifest` | T3 | FreezeSnapshot |
| `fetch_ingestion_status` | T3 | Ingest |

Keyed skills run on `POST /api/interactions/plan` and keyed cast roles only.

## Cast roles (IC6/J)

| Agent id | Mode | Notes |
|----------|------|-------|
| `explore-guide-v1` | public explore | prepare-then-narrate |
| `surface-planner-v1` | keyed planner | emits `ui_intent` |
| `dossier-explainer-v1` | keyed | dossier + gates + decisions |
| `promotion-clerk-v1` | keyed | supervisor + pending approval |

Seeds: [`src/aws_backend/casting/seeds/`](../../../src/aws_backend/casting/seeds/).

## Annotation types

See [`INTERACTIONS_GROUNDING_PATTERN.md`](INTERACTIONS_GROUNDING_PATTERN.md).

## Validation

- Unknown skill id → HTTP 400
- Disabled skill in agent spec → HTTP 400
- T2/T3 on public interactions → HTTP 400 (`tier_blocked`)
- T1 without viewport → skill skipped (not run)
- Unknown panel id on plan route → HTTP 400 (`invalid_ui_intent`)
