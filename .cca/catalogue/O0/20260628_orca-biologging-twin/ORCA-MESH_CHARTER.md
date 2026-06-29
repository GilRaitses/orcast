# ORCA-MESH charter (OM) - source + import a license-clean orca mesh

- Lane code: **OM** (under family ORCA). Type: research-first, then gated sourcing/conversion.
- `repo_state_verified_against`: origin/main `915e4cc`.
- Owns (net-new): `web/public/orca/`, `infra/orca/mesh/`. Touches no existing file in research.

## Intent
"Get an open source mesh of an orca" for the twin's underwater view - anatomically credible,
license-clean, optimized for the web renderer, scaled to the twin's metric frame.

## Grounding
- No mesh exists in repo (Glob `**/*.{glb,gltf}` = 0). The twin already streams glb tiles via
  meshopt (`web/lib/scene/tiles/useTilesLayer.ts`), so a glb + meshopt path is proven.
- Twin frame: synthetic `SCENE_WIDTH=120` with a live fit scale `worldUnitsPerMeter (~0.003)`;
  NAVD88 0 m maps to scene Y 0 (W2.6). An adult orca is ~6-8 m -> ~0.018-0.024 scene units.

## Waves
- **OM-R (research, read-only):** survey open-source orca/killer-whale meshes with VERIFIED
  permissive licenses (CC0/CC-BY/public-domain). Candidate sources to vet: Sketchfab CC0/CC-BY,
  NOAA/Smithsonian 3D, Poly Haven-style libraries, Wikimedia, scientific morphology repos. For
  each candidate record: source URL, author, license + attribution text, poly count, topology
  quality (is it cleanly riggable - quad-ish body, separable flippers/fluke), UVs/textures.
  Output `infra/orca/mesh/OM-R_candidates.md` with a ranked recommendation. If only NC/ND/unclear
  assets exist, STOP and return to O0 (do not download).
- **OM-BUILD (gated on O0):** download the chosen mesh; record `web/public/orca/LICENSE.md`
  (source/author/license/attribution); convert + optimize to `web/public/orca/orca.glb`
  (gltfpack/meshopt, optional KTX2 textures); scale/orient to the twin frame (heading +X, up +Y);
  a loader stub `web/lib/scene/orca/loadOrcaMesh.ts`. tsc clean.

## Acceptance
- OM-R: a ranked candidate list, every entry with a verified license; a clear recommendation.
- OM-BUILD (gated): `orca.glb` loads in the `/orca` sandbox at correct scale/orientation;
  `LICENSE.md` complete; sizes recorded; honesty label present. No commit without O0.

## Handoff
The chosen mesh's topology + named submeshes (body / pectoral flippers / fluke / jaw) feed
**ORCA-RIG (OR)**: OR needs a clean, separable body to place the skeleton and weight the skin.

## Escalation
License ambiguity, dependency choice, or any download/conversion (gated) -> pause, return to O0.
