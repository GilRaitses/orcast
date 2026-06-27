# orcast forecast ML-ops lane (project home)

Home for the forecast ML-ops lane: MLM (covariate modeling) and MLO (production platform). This
directory holds two complementary things, which it is important not to confuse:

- The methodology gate ladder (the gate DEFINITION). `MLM_CHARTER.md`, `MLO_CHARTER.md`, and the
  `families:` block of `wave_shape.yml` define the leveled go/no-go gates M-L0..M-L3 from
  `docs/methodology/CALIBRATION_STUDIES.md`. This is what a level must satisfy to earn confidence.
- The frontier execution waveset (the EXECUTION plan). `WAVESET_CHARTER.md`, `DECISION_RECORD.md`,
  `WAVE1_DISPATCH.md`, and the `frontier_dispatch:` block of `wave_shape.yml` externalize the
  current L2/L3 frontier as parallel-subagent waves W1/W2/W3, mirroring the terrain-bathymetry
  project home (`.cca/catalogue/O0/20260627_terrain-bathymetry-twin/`). W1/W2/W3 are execution
  waves, not new levels. W1 (de-risk) and W2 (integrate) are done; W3 (L3) is in progress.
- The research waveset (investigation-first). `RESEARCH_CHARTER.md`, `RESEARCH_DISPATCH.md`, and the
  `research_dispatch:` block of `wave_shape.yml` charter six parallel research agents to find ways to
  push L2 and L3 off their honest blockers (counts vs binary presence, conditioning, temperature,
  burstiness/Hawkes timing fix, the data-volume dependency). Findings land under `research/` as
  decision aids; nothing promotes confidence. RAN 2026-06-27; graduated to W4.
- The forward-path campaign (ground + activate). `CAMPAIGN_CHARTER.md`, `CAMPAIGN_DISPATCH.md`, and the
  `forward_path_campaign:` block of `wave_shape.yml` structure the path off 0% after the W4 adoption:
  one parallel deploy (P0, the confidence-cliff fix, code-only) + a research/grounding wave (W5) that
  gates three downstream waves (W6 deploy the 3-node ingest, W7 promote multi-station, W8 L3 live feed +
  re-test). Grounding docs land under `research/forward/`. Nothing promotes; build/promotion are gated.

## Files

- `MLM_CHARTER.md`, `MLO_CHARTER.md`: the methodology charters (gate ladder).
- `WAVESET_CHARTER.md`: the parallel-dispatch canon (execution model, the three waves, the
  per-agent prompt skeleton, collision rules, gates, return contract; restates the locked B-items).
- `DECISION_RECORD.md`: the verified code surface + operator-confirmed decisions + risks.
- `WAVE1_DISPATCH.md`: the five ready-to-launch Wave 1 agent prompts (ran 2026-06-27).
- `RESEARCH_CHARTER.md` + `RESEARCH_DISPATCH.md`: the L2/L3 push research waveset (six agents, ran). Findings under `research/`.
- `W4_BUILD_CHARTER.md` + `W4_BUILD_DISPATCH.md`: the build wave graduating the research findings (consistency re-score, summer-conditioned L3, bin-level timing gate). RAN; the bin-level gate was then ADOPTED by recorded supervisor decision (DECISION_RECORD.md sec 4).
- `CAMPAIGN_CHARTER.md` + `CAMPAIGN_DISPATCH.md`: the forward-path campaign (P0 confidence-cliff fix + W5 grounding -> W6 deploy / W7 promote / W8 L3). Grounding docs under `research/forward/`.
- `WIRING-ingest.md`, `PATCH-salmon.md`, `WIRING-salmon-albion.md`: wiring/patch/provenance specs.
- `wave_shape.yml`: machine-readable shape (the `families:` level ladder, the `frontier_dispatch:`
  W1-W4 execution plan, the `research_dispatch:` research wave, and the `forward_path_campaign:`).
- `STEP_LOG.md`: the running synthesis trace (newest last).

## State (2026-06-27)

Effective confidence 0%. L0 PASS, L1 PASS, L2 FAIL, L3 WITHHELD. W1-W4 ran. The bin-level L2 timing
gate is ADOPTED (recorded supervisor decision) but does NOT promote: the served single-station fit has
held-out CV-skill -0.047, so the load-bearing CV-skill half fails and confidence stays 0.0. L3's real
Albion (Fraser) feed is wired all years; the pre-registered summer held-out result is FLAGGED-FOR-
DECISION (not promoted). The path off 0% is the deploy-gated 3-node ingest (flips served CV-skill
positive); the forward-path campaign grounds it. Next gate: launch W5 (research-grounding); P0
(confidence-cliff fix) is executing in parallel.

## Authority / lineage

- Locked decisions: `.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` section B.
- Operator intent / PIML strategy: `.cca/catalogue/O0/20260627_orcast-handoff/ORCHESTRATOR_NOTES.md`.
- Waveset execution-model template: `.cca/catalogue/O0/20260627_terrain-bathymetry-twin/`.
- Methodology canon: `docs/methodology/FORECAST_KERNELS.md`, `docs/methodology/CALIBRATION_STUDIES.md`.
