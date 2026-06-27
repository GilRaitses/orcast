# STEP_LOG, CAND forecast candidate-preparation waveset

All times America/New_York.

## 2026-06-27

- Chartered family CAND from the data-source inventory (three read-only mining agents:
  sighting sources, covariate/modeling features, hydrophones/annotation platforms).
- Recorded the honest grounding: confirmed equals cross_validation verified/likely; four
  in-region hydrophones; OrcaHello annotation records (334 reviewed labels, 761 acoustic
  detections at haro_strait); covariates and their fitted status (only diel and lunar fitted).
- Feasibility checked at charter time: committed static sighting files hold 8-10 records
  each (4 of 8 verified-seed within 5 km of a hydrophone). Reaching 40 requires the live
  OBIS/iNaturalist pull plus the OrcaHello acoustic history. Live ingest is operator-gated.
- Wrote `CANDIDATE_CHARTER.md`, `wave_shape.yml`, `candidate_targets.schema.yml`, the
  `candidates.targets.json` skeleton, and `DISPATCH_PROMPTS.md`.
- Registered family CAND in `docs/devpost/waves.registry.yaml` and `WAVES_REGISTRY.md`.

## 2026-06-27 (execution)

- Built the harness `tools/forecast_candidates/build_candidates.py` (ingest + hydrophone +
  covariate + OrcaHello-overlap joins + scoring/tiers + cache).
- C-GAP (live): 93 in-region, 91 confirmed visual, 1359 OrcaHello records, 257 pool, 166 tier-A.
  Feasibility for 40/20 comfortably met. See GAP_COVERAGE.md.
- C-BUILD (live, --max 200): wrote candidates.targets.json with 200 candidates, 166 tier-A,
  184 within 5 km of a hydrophone, across all four hydrophones. OrcaHello index cached.
- C-VERIFY: validation block + adversarial checks PASS. See CAND_VERIFY.md.
- External note: OrcaHello history API intermittently 403s; successful fetch cached for
  reproducibility (orcahello_index.cache.json).

## Open / awaiting operator

- Approve live ingest (OBIS, iNaturalist, OrcaHello) so C-BUILD can assemble the 40.
- C-GAP is read-only and can run without live network if it uses the cached snapshot; live
  feeds make the coverage count real.
- Commit/push only on explicit request.
