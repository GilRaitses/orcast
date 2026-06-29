# orcast terrain+bathymetry coastal twin (project home)

Instantiated 2026-06-27 from the reusable 3d-twin template
(`.cca/catalogue/O0/20260627_3d-twin/`). This is the live project home for the orcast worked
example: a San Juan / Salish Sea coastal twin where one integrated land+seafloor surface renders
in the existing react-three-fiber scene and the same geometry feeds the `s_space` depth/habitat
science consumer.

## Files

- `WAVESET_CHARTER.md`: the lane canon (copied from the template; execution model verbatim,
  the three waves, the per-agent prompt skeleton, the collision rules, the gates).
- `DECISION_RECORD.md`: operator-confirmed decision record (2026-06-27) + grounded data sources.
- `wave_shape.yml`: machine-readable shape, filled with the confirmed values.
- `WAVE1_DISPATCH.md`: the six ready-to-launch Wave 1 agent prompts (NOT yet launched).
- `STEP_LOG.md`: synthesis trace for this lane (newest last).

## State (2026-06-27)

Decision record CONFIRMED by the operator. Wave 1 dispatch is written and READY. No agents
launched, no commit, no push. The next gate is the operator's go to launch Wave 1.

Confirmed decisions: run all six Wave 1 agents (science spike included); conversion host =
aimez.ai EC2 (AWS); inherit the orchestrator model; primary source NOAA NCEI CUDEM 1/9
topobathy (NAVD88 m, one integrated land+sea surface), target CRS EPSG:32610, vertical reference
NAVD88 m; science consumer = `s_space` via `BathymetryAdapter`.

## Lineage

- Template: `.cca/catalogue/O0/20260627_3d-twin/`
- pax plan: `~/.cursor/plans/realistic_nyc_3d_viewer_c0b6b2b4.plan.md`
