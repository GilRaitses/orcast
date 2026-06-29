# ORCA biologging twin - program (mesh + skeleton + data-driven motion)

Curated 2026-06-28. An animated orca for the underwater view of the Salish Sea 3D twin: an
open-source mesh, an anatomical skeleton/rig, and movement **driven by whale-tagger biologging
telemetry** (the H5 sensor streams). Built as **three sequential charters** so each is a clean,
disjoint lane that a background agent can own.

- Family code: **ORCA**. Home: `.cca/catalogue/O0/20260628_orca-biologging-twin/`.
- `repo_state_verified_against`: origin/main `915e4cc77923de93ed5f7e9a75feab9eb2e12896`.
- Charter method: `~/.cursor/skills/waveset-orchestration/SKILL.md`.
- Render runtime: react-three-fiber / `three` (same as the twin). Lands in the twin's underwater
  view (3D-TWIN `W4`); developed in a net-new `/orca` sandbox first.

## Intent (operator)

"In the under water view I want to get an open source mesh of an orca and write up the skeleton
and have it move driven by the data in the h5 from whale tagger. Break that up into multiple
charters and dispatch background agents for all that."

## The charters (sequential where dependent; research can run in parallel)

Core pipeline (mesh -> rig -> motion):

| Code | Charter | Owns (net-new) | Produces |
|---|---|---|---|
| **OM** | `ORCA-MESH_CHARTER.md` | `web/public/orca/`, `infra/orca/mesh/` | a license-clean orca mesh, optimized glb (meshopt/KTX2), scaled to the twin metric frame, with a provenance/license manifest |
| **OR** | `ORCA-RIG_CHARTER.md` | `web/lib/scene/orca/rig/`, `docs/orca/SKELETON.md` | the anatomical skeleton write-up + an armature with skinning weights and named DOFs |
| **OG** | `ORCA-MOTION_CHARTER.md` | `web/lib/scene/orca/motion/`, `infra/orca/biologging/` | an H5 biologging -> rig driver (orientation, dive, fluke-stroke), with the simulated dtag as dev fixture |

Appearance + finer motion (added 2026-06-28; depend on OM/OR/OG):

| Code | Charter | Owns (net-new) | Produces |
|---|---|---|---|
| **OMAT** | `ORCA-MATERIALS_CHARTER.md` | `web/lib/scene/orca/materials/`, `web/public/orca/textures/` | skin PBR + countershading (eyepatch/saddle), wet BRDF + SSS, lit by the **WFX** environment (above + underwater) |
| **OEYE** | `ORCA-EYES_CHARTER.md` | `web/lib/scene/orca/eyes/` | eye mesh/material (cornea catch-light) + bounded gaze that layers on the OR head bone / OG orientation |
| **OMOU** | `ORCA-MOUTH_CHARTER.md` | `web/lib/scene/orca/mouth/` | mouth interior (teeth/tongue/cavity) + jaw articulation on the OR `jaw` DOF + labeled OG foraging-cued open |
| **OPHYS** | `ORCA-PHYSICS_CHARTER.md` | `web/lib/scene/orca/physics/` | bounded secondary dynamics (flex, follow-through, drag/banking, spine IK) **layered on** the OG telemetry pose, provably tracking the data within tolerance |

Convergence (mounting the orca in `web/app/components/scene/SalishScene.tsx`, lane `OINT`) is a
later, O0-gated step that serializes against W-CAM / W-LABELS / W3 / W4 / WFX / LGC.

### Cross-lane locks for the appearance/physics charters
- **OMAT consumes the WFX light/environment** (same sun/sky/PMREM above, same absorption/in-scatter
  below) so the orca is not lit disjoint from the water. New env APIs coordinate with WFX via O0.
- **OEYE/OMOU layer on OR DOFs** (head bone, `jaw`) and never override OG body orientation.
- **OPHYS never fabricates trajectory** - position/depth/heading/pitch/roll/fluke-rate stay OG's;
  OPHYS adds only bounded, clamped secondary motion that still tracks the telemetry within tolerance.

## Grounding (verified)

- **No orca mesh and no `.h5` exist in the repo** (Glob for `**/*.{glb,gltf,h5,hdf5,nc}` = 0).
  Both must be sourced. The H5 is the operator's whale-tagger export.
- **dtag schema** (from `scripts/database/create_dtag_tables.py`, `scripts/ml_services/
  dtag_data_processor.py`, `src/aws_backend/routers/dtag.py`): per-sample `depth, pitch, roll,
  heading, acceleration_x/y/z, behavior_type, acoustic_activity`; plus dive events
  (`max_depth, descent_rate, ascent_rate, mean_dba, foraging_indicators`).
- **In-repo dtag data is SIMULATED** (`data/dtag_analysis_results.json` =
  `cascadia_2010_k33_test`, `simulated: true`, TagTools-inspired, 36000 samples / 0.2h). It is
  the **development fixture**. Real Cascadia/NOAA DTAG is partnership-gated (see
  `docs/dtag_research_plan.md`). The standard tag toolchain is animaltags / tagtools
  (Aw accelerometer, Mw magnetometer, p pressure/depth, pitch/roll/heading, fluke stroke from Az).

## Locked decisions (do NOT reopen)

- **License first.** No mesh ships without a verified CC0 / CC-BY / permissive license recorded
  in `web/public/orca/LICENSE.md` (source URL, author, license, attribution text). No scraped or
  unclear-license asset. If only NC/ND or unclear assets are found, OM stops and returns to O0.
- **Honesty label (lock 4/5 analog).** The orca is a **modeled** animal whose motion is driven by
  **simulated or partnership-gated biologging telemetry**; it is NOT a measured swim of a named
  individual unless a real, agreement-covered deployment is loaded. The sandbox/HUD says so.
- **Anatomy, not cartoon.** The skeleton follows real odontocete anatomy: skull, cervical
  (fused-ish) -> thoracic -> lumbar -> caudal vertebral column, ribs, pectoral flippers (no hind
  limbs / no pelvic girdle), and a fluke driven by the caudal chain. Documented in
  `docs/orca/SKELETON.md` before rigging.
- **Motion mapping is physical.** heading -> world yaw; pitch/roll -> body orientation; depth ->
  Y on the twin's NAVD88-0m datum (W2.6); accelerometer Az oscillation -> fluke-stroke amplitude
  + phase. No hand-keyed "swim loop" pretending to be data when a stream is loaded.
- **Read-only research first.** Each charter's Wave 1 writes only findings docs; sourcing
  (downloads) and any mesh conversion run on a later gated wave. No `next dev/build` in a parallel
  wave; `tsc` clean; net-new files preferred; commit is an operator gate.
- **Built on `three`** (+ existing glb/meshopt path used by tiles); a new runtime dependency is a
  costed recommendation, not a default. H5 parsing in JS (h5wasm) vs a Python pre-bake step is an
  OG research decision returned to O0.

## Escalation (operator-protection catch)
The dispatched sub-orchestrator answers to **O0, not the human operator**. Any license ambiguity,
dependency choice, partnership/data-access question, locked-decision conflict, regression, or
gated step: **pause and return to O0**. No First AD solicits the human.

## Registry
Family ORCA (umbrella) + charters OM, OR, OG registered in `docs/devpost/waves.registry.yaml`.
Mesh-mount and commit are operator gates.
