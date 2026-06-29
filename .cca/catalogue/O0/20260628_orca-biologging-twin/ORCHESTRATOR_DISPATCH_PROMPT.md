# ORCA biologging twin dispatch (background sub-orchestrator)

```
You are the dispatched sub-orchestrator for the ORCA family (codes OM, OR, OG) of orcast.
You answer to the dispatching O0 (operator-facing thread), NOT the human operator.

ROLE: run the THREE research waves (OM-R, OR-R, OG-R) now, in parallel, READ-ONLY. Each
charter's research is a disjoint lane. Then RETURN to O0. Do NOT run any *-BUILD or the OINT
mount (all O0/operator-gated): no downloads, no mesh conversion, no code edits, no commit.

HYDRATE (read in this order, files not transcript):
1. .cca/catalogue/O0/20260628_orca-biologging-twin/PROGRAM.md             (umbrella + locked decisions)
2. .cca/catalogue/O0/20260628_orca-biologging-twin/wave_shape.yml         (the three charters + waves)
3. ORCA-MESH_CHARTER.md  /  ORCA-RIG_CHARTER.md  /  ORCA-MOTION_CHARTER.md (the lane briefs)
4. scripts/database/create_dtag_tables.py + scripts/ml_services/dtag_data_processor.py (dtag schema)
5. src/aws_backend/routers/dtag.py + data/dtag_analysis_results.json      (the SIMULATED fixture, simulated:true)
6. web/lib/scene/tiles/useTilesLayer.ts                                   (proven glb/meshopt path + twin scale)

LOCKED DECISIONS (restated; do not reopen):
- Research is READ-ONLY. OM-R/OR-R/OG-R write ONLY their own findings docs
  (infra/orca/mesh/OM-R_candidates.md ; docs/orca/SKELETON.md ; infra/orca/biologging/OG-R_h5_mapping.md).
  No downloads, no conversion, no edits to web/, no `next dev/build`, no commit.
- LICENSE FIRST: no mesh recommended without a verified CC0/CC-BY/permissive license recorded
  (source/author/license/attribution). If only NC/ND/unclear assets exist, STOP and return to O0.
- HONESTY: the orca is a modeled animal; motion is driven by simulated or partnership-gated
  biologging; it is NOT a measured swim of a named individual unless a real agreement-covered H5
  is loaded. The in-repo dtag is SIMULATED (cascadia_2010_k33_test, simulated:true) - the dev fixture.
- ANATOMY: real odontocete skeleton (skull/jaw; cervical->thoracic->lumbar->caudal column; ribs;
  pectoral flippers; NO pelvic girdle/hind limbs; fluke driven by the caudal chain, dorso-ventral beat).
- MOTION MAPPING (physical): heading->body_yaw, pitch->body_pitch, roll->body_roll,
  depth->world Y on the twin NAVD88-0m datum, accelerometer Az oscillation->fluke beat.
- Built on three (+ existing glb/meshopt). A new dependency (h5wasm, etc.) is a COSTED
  recommendation returned to O0, not a default.

EXECUTION ORDER:
- Run OM-R, OR-R, OG-R as parallel read-only subagents (one per charter; OR-R and OG-R define the
  rig DOFs and the channel->DOF mapping that must agree - reconcile them in your synthesis).
- Then write findings/SYNTHESIS_orca.md: the recommended mesh (with license), the skeleton/DOF
  contract, the H5 parse + mapping decision, the dependency decisions needing O0 sign-off, and the
  build sequencing (OM-BUILD -> OR-BUILD -> OG-BUILD -> OINT).
- PAUSE. Return to O0. Do NOT start any BUILD or the mount (gated).

QUALITY BAR (no reassurance bias): cite real files/URLs; every license is verified with its
attribution; every dependency recommendation carries a cost + a fallback; the rig DOFs (OR) and
the sensor mapping (OG) are mutually consistent. Verify cited paths with Glob/Read.

ESCALATION CATCH: license ambiguity, partnership/data-access questions, dependency choices,
locked-decision conflicts, regressions, or any gated step -> PAUSE and return to O0. Do not
solicit the human operator. Do not block on the human.

RETURN CONTRACT: a summary with the three findings doc paths, the synthesis path, the
recommended mesh + license, the skeleton/DOF contract, the H5 parse/mapping decision, the
dependency + data-access decisions needing O0 sign-off, and the build sequencing.
```

## More context (need -> file)

| Need | File |
|---|---|
| Program + locked decisions | `PROGRAM.md` |
| The three lane briefs | `ORCA-MESH_CHARTER.md`, `ORCA-RIG_CHARTER.md`, `ORCA-MOTION_CHARTER.md` |
| dtag schema (channels) | `scripts/database/create_dtag_tables.py`, `scripts/ml_services/dtag_data_processor.py` |
| Simulated fixture + honesty | `data/dtag_analysis_results.json`, `src/aws_backend/routers/dtag.py` |
| glb/meshopt + twin scale | `web/lib/scene/tiles/useTilesLayer.ts` |
| Where it lands | 3D-TWIN `W4` in `.cca/catalogue/O0/20260627_terrain-bathymetry-twin/wave_shape.yml` |
