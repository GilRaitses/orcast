# ORCA biologging twin (family ORCA)

An animated orca for the underwater view of the Salish Sea 3D twin: an open-source mesh, an
anatomical skeleton/rig, and movement driven by whale-tagger biologging telemetry (the H5 sensor
streams). Split into three disjoint charters so each is a clean background lane.

Files:
- `PROGRAM.md` - umbrella, intent, grounding, locked decisions, the three charters.
- `ORCA-MESH_CHARTER.md` (OM) - source + import a license-clean orca mesh.
- `ORCA-RIG_CHARTER.md` (OR) - skeleton write-up + armature/skinning + named DOFs.
- `ORCA-MOTION_CHARTER.md` (OG) - H5 biologging -> rig driver (orientation, dive, fluke-stroke).
- `wave_shape.yml` - machine-readable shape (charters, waves, mapping, gates).
- `ORCHESTRATOR_DISPATCH_PROMPT.md` - the paste block for the background sub-orchestrator.
- `findings/` - OM-R/OR-R/OG-R findings + `SYNTHESIS_orca.md` (created by the wave).

How to start: dispatch the sub-orchestrator with `ORCHESTRATOR_DISPATCH_PROMPT.md`. It runs the
three read-only research waves in parallel and returns to O0. All *-BUILD waves, the mount into
the live scene (OINT), downloads, dependency adoption, and commits are O0/operator gates.

Key facts: no orca mesh and no `.h5` exist in the repo yet (both sourced). The in-repo dtag is
SIMULATED (the dev fixture); real DTAG is partnership-gated. Honesty label: modeled animal,
simulated/partnership-gated motion, not a measured swim of a named individual.

Lands in the 3D-TWIN family's `W4` (underwater). Status: chartered + research dispatched 2026-06-28.
