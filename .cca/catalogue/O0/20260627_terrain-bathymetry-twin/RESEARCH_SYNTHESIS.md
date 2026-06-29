# Research spike synthesis and corrected ground truth

Home: `.cca/catalogue/O0/20260627_terrain-bathymetry-twin/`
Date: 2026-06-27. Inputs: research/R1..R6 (six briefs) plus independent verification of the
live serving path by the orchestrator. Status: the W2 Phase-B integrator stays ON HOLD; this
synthesis sets the corrected plan it must follow.

## 0. Corrected ground truth (honesty correction)

Independent verification (curl of the live tileset plus `aws s3 ls`) contradicts the earlier
W1 gate-closure record (STEP_LOG S09/S10), which trusted a subagent self-report:

- S3 origin `s3://aimez-data/3dtwin/pilot/` DOES hold the CUDEM rebuild: `pilot.glb` 5.6 MiB and
  `tileset.json` 454 bytes, dated 04:08 local (08:08 UTC).
- CloudFront `https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/pilot/` is SERVING A STALE CACHED copy
  of the OLD GMRT pilot: `pilot.glb` 987048 bytes (last-modified 07:45 UTC, x-cache Hit) and a
  `tileset.json` with root `geometricError 25422.624`, child `geometricError 0.0`, box
  half-extents 18890.4 / 17013.6 / 558.36 m (about 37 km, GMRT extent).
- Therefore the earlier standalone-harness and in-app `/tiles3d` screenshots rendered the STALE
  GMRT pilot, not the CUDEM rebuild. The "datum-correct pilot is served" claim was not true at
  the CloudFront edge. The CUDEM objects exist in S3 but were never actually served because the
  distribution was not invalidated.

Two distinct defects fall out of this and are confirmed by the literature briefs:
1. Serving defect: CloudFront cache not invalidated, so the wrong (GMRT, approx MSL) artifact is
   live. A CloudFront invalidation of `/3dtwin/pilot/*` fixes which bytes are served.
2. Structural defect: BOTH the GMRT and the CUDEM pilots are a SINGLE root tile with child
   `geometricError 0.0` and no LoD children. R1 and R6 show this is the core reason a tile shows
   or vanishes on the frustum test alone, with `errorTarget`/`maxDepth` unable to help. The pilot
   must be re-baked as a real multi-LoD tileset.

## 1. Why the land vanishes (root causes, ranked)

R6 reframed the symptom against the ACTUAL live scene, and this is the key insight:

- The live `web/app/components/scene/SalishScene.tsx` does NOT use the tiles renderer, the pilot
  tileset, or the Gerstner water at all. It renders a hand-built `TerrainMesh` heightfield plus a
  plain `WaterPlane`. So what the operator saw is the PLACEHOLDER, and its bug is in that code.
- Most-likely cause: inverted triangle winding at `SalishScene.tsx:70`
  (`indices.push(a, d, b, b, d, e)`), so terrain front faces and normals point DOWN. With the
  default `FrontSide` material and `OrbitControls` clamped above the horizon
  (`maxPolarAngle = PI/2.05`), the terrain top is backface-culled, while the water plane front
  faces up and always renders. That asymmetry is exactly "water always present, land vanishes".
- Compounding: the transparent water (`transparent`, `depthWrite:false`, `renderOrder:1`,
  alpha 0.72) sorts by distance and washes a flat blue over low and shoreline terrain and any
  un-streamed geometry (R1, R4). Possible Y-datum misalignment presents identically (R4).
- Separately, when tiles ARE mounted (Wave 2), the single-tile, no-LoD tileset plus the camera
  far plane of 2000 versus a 25 km bounding sphere will clip and drop the terrain (R1, R6).

## 2. Decisions taken from the briefs

| Area | Decision | Source |
|---|---|---|
| Placeholder bug | Fix terrain winding (or DoubleSide as a quick check); keep water opaque-sorted or move to depth-driven alpha; bias water just below Y 0. This is a small, contained fix to the live scene. | R6, R4 |
| Tileset structure | Re-bake the terrain as a real multi-LoD implicit quadtree (root-largest, monotonically halving geometricError, leaves near 0), NOT a single tile. The full-extent `batch-conversion` agent must produce this; the pilot path should be retired or rebuilt the same way. | R1 |
| Serving | Invalidate CloudFront `/3dtwin/pilot/*` so the CUDEM bytes actually serve, and add invalidation as a required step in every bake-and-upload. | ground truth |
| Format | OGC 3D Tiles 1.1 (glTF) stays correct for `3d-tiles-renderer`. quantized-mesh is Cesium-internal. The format was never the problem. | R1 |
| Water | Keep 4-wave Gerstner plus a scrolling detail normal. Switch alpha and color to DEPTH-DRIVEN from the opaque depth buffer (Beer-Lambert), so shallow and dry areas go transparent and reveal land. Foam from the depth difference. IBL or three planar Reflector for reflection, depth-buffer UV refraction, no SSR. | R4 |
| Bathymetry data | Add a MEASURED-soundings overlay over the modeled CUDEM surface, never blended into it. Datasets covering the bbox: NOS H-surveys (H08085, H10766, H11631, H11632), NOAA ENC `SOUNDG`/`DEPARE`, CHS NONNA for the Canadian strip, the San Juan MBES compilation, 2019 WA DNR lidar (NAVD88). Reconcile MLLW to NAVD88 only via NOAA VDatum. Tag per source with GEBCO TID. Keep "modeled, not measured" verifiable. | R2 |
| Cartography | Procedural depth-plus-elevation tint with a swappable "chart" preset (S-52 stepped depth shades, emphasised safety contour) and a "scientific" preset (cmocean), plus NW hillshade and two-tier isobaths, optional billboard sounding labels, optional chart-raster drape. S-52-inspired, not certified ECDIS. Reconcile LAT/MLLW vs NAVD88 in the legend. | R3 |
| AI materials | GO for AI-generated tileable PBR sets for DECORATIVE surfaces (sediment, rock, kelp, shore, a cosmetic water detail-normal), with a CC0 path (Poly Haven, ambientCG) preferred or parallel. Keep shaders hand-written. Label every AI asset via C2PA plus a provenance manifest as decorative, not measured. Materials must never alter elevation or depth. | R5 |

## 3. Effect on the wave plan

- New W2 prerequisite: a CORRECT multi-LoD bake (R1) before the integrator runs, and a CloudFront
  invalidation step. The `batch-conversion` full-extent agent already targets a real LoD tree; its
  output, not the single-tile pilot, becomes the integration target.
- Quick-win track (independent of W2): fix the placeholder `SalishScene` winding and water so the
  CURRENT live scene renders land correctly. Small, contained, directly answers the operator.
- W3 materials and shading (visual program) gains: depth-driven water, the chart vs scientific
  portrayal presets and isobaths from R3, and AI or CC0 decorative PBR sets from R5.
- W4 gains a measured-soundings overlay layer (R2) alongside the modeled substrate, both clearly
  labeled.
- The "modeled, not measured" constraint is strengthened: GEBCO TID tagging for data, C2PA plus a
  manifest for decorative materials.

## 4. Immediate recommended actions (operator to confirm priority)

1. Fix the live placeholder vanishing-land bug (winding plus water depth sort). Smallest change,
   biggest visible payoff.
2. Invalidate CloudFront so the CUDEM (datum-correct) bytes serve, and confirm by re-fetch.
3. Let `batch-conversion` finish the full-extent multi-LoD bake, then validate and visually verify
   it actually streams and refines, before the integrator wires it in.
4. Schedule the soundings overlay, chart portrayal, and AI or CC0 materials into W3 and W4 as
   above.
