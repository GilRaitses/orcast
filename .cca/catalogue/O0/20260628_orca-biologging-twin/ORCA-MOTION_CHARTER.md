# ORCA-MOTION charter (OG) - H5 biologging -> rig driver

- Lane code: **OG** (under family ORCA). Type: research-first (H5 schema + mapping), then gated build.
- Depends on: **OR** (the `OrcaRig` named-DOF API). Can research in parallel with OM/OR.
- Owns (net-new): `infra/orca/biologging/`, `web/lib/scene/orca/motion/`. Touches no existing file in research.

## Intent
"Have it move driven by the data in the h5 from whale tagger" - parse the whale-tagger H5
biologging stream and drive the orca rig: orientation, dive depth, and fluke-stroke from the
real sensor channels, with the simulated in-repo dtag as the development fixture.

## Grounding
- **No `.h5` in repo**; the H5 is the operator's whale-tagger export. The standard tag toolchain
  is animaltags / tagtools: `Aw` (3-axis accelerometer), `Mw` (magnetometer), `p` (pressure ->
  depth), derived `pitch/roll/heading`, fluke stroke from the `Az` band. Sample rates differ per
  channel (sensor decimated; audio high-rate).
- **In-repo dtag is SIMULATED** (`data/dtag_analysis_results.json` = `cascadia_2010_k33_test`,
  `simulated: true`; aggregated dive analysis: `max_depth, descent_rate, ascent_rate, mean_dba,
  foraging_indicators`). Per-sample `depth/pitch/roll/heading/accel xyz` are produced by
  `scripts/ml_services/dtag_data_processor.py` and described in
  `scripts/database/create_dtag_tables.py`; served read-only by `src/aws_backend/routers/dtag.py`
  (honesty: `simulated: true`, `model_state: not_trained`).
- Twin datum: depth maps to Y on NAVD88 0 m == scene Y 0 (W2.6); `worldUnitsPerMeter (~0.003)`.

## Mapping (locked, physical)
| Sensor channel | Rig DOF |
|---|---|
| heading | `body_yaw` (world heading-follow) |
| pitch | `body_pitch` |
| roll | `body_roll` (bank into turns) |
| depth (from pressure) | world Y on the twin datum; drives the dive trajectory |
| accelerometer Az oscillation | fluke-beat `setFluke(phase, amplitude)` (stroke rate + power) |
| dive/foraging context | optional behavior tint / speed (honest, labeled) |

## Waves
- **OG-R (research, read-only):** `infra/orca/biologging/OG-R_h5_mapping.md` - the H5 schema
  (animaltags/tagtools layout), the **H5-parsing decision** (browser h5wasm vs a Python pre-bake
  to a compact JSON/typed-array the web loads - costed, returned to O0), the channel->DOF mapping
  with units/frames (NED vs scene axes, sample-rate alignment, fluke-stroke extraction from Az),
  and how the simulated fixture stands in until a real agreement-covered H5 is loaded.
- **OG-BUILD (gated on O0):** a loader/driver in `web/lib/scene/orca/motion/`:
  `loadBiologging(source)` -> a typed time-series; a per-frame `driveOrca(rig, t)` that sets the
  rig DOFs from the stream (interpolated, frame-rate independent); a clearly-labeled procedural
  fallback swim ONLY when no stream is loaded. Tuned in the `/orca` sandbox against the simulated
  fixture. Net-new; tsc clean.

## Acceptance
- OG-R: the schema + mapping + parsing decision are documented and cite real files; honesty
  framing explicit.
- OG-BUILD (gated): in the `/orca` sandbox the orca dives and orients **following the loaded
  stream** (verified against the simulated fixture: depth track matches, fluke beats with the Az
  oscillation, body banks with roll), frame-rate independent; the HUD labels it
  modeled/simulated; procedural fallback only when no stream. No commit without O0.

## Handoff
Mounting the driven orca into `SalishScene.tsx` underwater view is a later O0-gated step under
3D-TWIN `W4`, serialized vs W-CAM/W-LABELS/W3/WFX/LGC.

## Escalation
H5 parsing/dependency choice, partnership/data-access for a real deployment, mapping ambiguity,
or any gated step -> pause, return to O0.
