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
  waves, not new levels.

## Files

- `MLM_CHARTER.md`, `MLO_CHARTER.md`: the methodology charters (gate ladder).
- `WAVESET_CHARTER.md`: the parallel-dispatch canon (execution model, the three waves, the
  per-agent prompt skeleton, collision rules, gates, return contract; restates the locked B-items).
- `DECISION_RECORD.md`: the verified code surface + operator-confirmed decisions + risks.
- `WAVE1_DISPATCH.md`: the five ready-to-launch Wave 1 agent prompts (NOT yet launched).
- `wave_shape.yml`: machine-readable shape (the `families:` level ladder AND the
  `frontier_dispatch:` W1/W2/W3 execution plan).
- `STEP_LOG.md`: the running synthesis trace (newest last).

## State (2026-06-27)

Effective confidence 0%. L0 PASS, L1 PASS, L2 FAIL (multi-station skill +0.078 but time-rescaling
KS p=0.0 and cross-station PSTH corr 0.14-0.34), L3 WITHHELD (climatology salmon placeholder). The
frontier waveset is written and READY. No agents launched, no commit, no push. The next gate is the
operator's go to launch Wave 1.

## Authority / lineage

- Locked decisions: `.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` section B.
- Operator intent / PIML strategy: `.cca/catalogue/O0/20260627_orcast-handoff/ORCHESTRATOR_NOTES.md`.
- Waveset execution-model template: `.cca/catalogue/O0/20260627_terrain-bathymetry-twin/`.
- Methodology canon: `docs/methodology/FORECAST_KERNELS.md`, `docs/methodology/CALIBRATION_STUDIES.md`.
