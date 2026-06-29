# STEP_LOG, orcast terrain+bathymetry coastal twin (newest last)

Two-to-four lines per step. Lineage: the 3d-twin template home
(`.cca/catalogue/O0/20260627_3d-twin/`) and its STEP_LOG.

S01. Hydrated the 3d-twin lane from files (handoff charter, hydration packet, waveset template,
wave_shape, NYC plan, SDR) and grounded the orcast worked example in the repo: convergence file
`web/app/components/scene/SalishScene.tsx`, science consumer `bathymetry.py` (`s_space`),
`SAN_JUAN_BOUNDS`. Returned the section H ack; surfaced the section 1 + section 7 decisions.

S02. Operator confirmed: (1) run all six Wave 1 agents incl. science spike; (2) conversion host =
aimez.ai EC2 (AWS); (3) inherit model; (4) data confirmed, ground it; (5) copy template to a new
home.

S03. Grounded the data sources (verified 2026-06-27): adopted NOAA NCEI CUDEM 1/9 arc-second
topobathy (`wash_pugetsound`) as the primary integrated source (NAVD88 m vertical, NAD83
horizontal, land+sea merged across the shoreline via VDatum at the source), with USGS 3DEP as
optional land refinement and GEBCO/CHS for any Canadian-side gap. Target CRS EPSG:32610; vertical
NAVD88 m. VDatum confirmed covering San Juan / Strait of Juan de Fuca for any non-NAVD88 blend.
This collapses the vertical-datum + coastline-seam footguns into the source.

S04. Instantiated this project home: copied `WAVESET_CHARTER.md` + `wave_shape.yml` from the
template; wrote `DECISION_RECORD.md` (confirmed + grounded), filled `wave_shape.yml`, wrote
`WAVE1_DISPATCH.md` (six self-contained agent prompts), this log, and the README.

S05. Operator confirmed CUDEM as primary source and a local-first launch (agents A realism +
E renderer-sandbox first). Launched A and E in background on the inherited model (own disjoint
web dirs; E sole manifest editor for `3d-tiles-renderer`; E mounts a stand-in public tileset
since D is gated; type-check only; no commit).

S06. Grounded the conversion host. `aimez.ai` apex is GitHub Pages; the real box is the
`aimez-services` EC2 (`i-04a649f91274e9fce`, c6i.xlarge), x86_64 Ubuntu 22.04, 4 vCPU, 7.6 GB
RAM, ~20 GB free, reachable `ssh -i ~/.ssh/pax-ec2-key.pem ubuntu@44.197.243.177` (also
SSM-managed, us-east-1). It has docker + python3 but NOT gdal/pdal/gltfpack/node, so converters
run as linux/amd64 docker images natively (x86_64, no emulation). It already has `~/bakeoff` and
`~/borough` from the pax NYC tiler lineage (left untouched). Operator said "confirmed go on", so
launched the four EC2 geo agents in background (B reproject+mesh, C tiler bake-off, D pilot
tileset, F science spike), each with its own remote workdir `~/3dtwin/<role>/` and S3 prefix
`s3://aimez-data/3dtwin/<role>/`. All six Wave 1 agents now running; no commits by agents.

S07. Mid-wave infra unblock. Grounded the conversion box (`aimez-services` EC2, x86_64). Found
the EC2 instance role `aimez-host-role` could not write to `s3://aimez-data` (its `aimez-host-s3`
policy only covers `pax-nyc-images`), which blocked artifact staging. CloudFront `EOMERK64CS5CE`
(`d8kxxpcnj3ub5.cloudfront.net`) was already provisioned to serve `aimez-data/3dtwin/pilot/*` to
browsers (OAC; bucket public-access blocked). Operator approved a minimal scoped IAM grant; added
inline policy `aimez-host-3dtwin` (s3:PutObject/GetObject on `aimez-data/3dtwin/*`, s3:ListBucket
prefix `3dtwin/*`; no delete) and round-trip verified from the instance role.

S08. Wave 1 complete (all six). Results:
- A realism: standalone realism module under `web/app/components/scene/realism/` (Gerstner water,
  self-contained NOAA sun, fog/sky, palette port) + WIRING-realism.md; scoped type-check clean.
- B reproject+mesh: corrected coverage to CUDEM `wash_bellingham` (4 tiles, 100% over the bbox
  incl. Canadian-side strip); reprojected to EPSG:32610 with NAVD88 m PROVEN preserved (means
  -19.639 -> -19.614, no ~22 m ellipsoid shift); 1.23M-vert continuous land+sea mesh, no seam.
  Outputs to s3://aimez-data/3dtwin/reproject/.
- C tiler bake-off: ran on B's REAL CUDEM mesh; recommends mesh->3D Tiles 1.1 (glTF) over
  quantized-mesh (~1 draw call vs ~532; native to 3d-tiles-renderer, no Cesium; stays in the
  shared UTM frame). Outputs to s3://aimez-data/3dtwin/bakeoff/.
- D pilot tileset: valid 3D Tiles 1.1 (validator 0 errors), gltfpack meshopt (9.4x), served
  CORS-correct at https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/pilot/tileset.json. CAVEAT: ran
  before B landed, so used GMRT (approx MSL, NOT NAVD88) substitute geometry. Pipeline-correct,
  datum-substitute; Wave 2 rebuilds the tileset from B's CUDEM/NAVD88 mesh via the recommended
  mesh->3DTiles path.
- E renderer sandbox: `/tiles3d` route mounts 3D Tiles via 3d-tiles-renderer@0.4.28 in r3f;
  reusable useTilesRenderer hook + WIRING-renderer.md; sole manifest editor; type-check clean;
  rendered a STAND-IN tileset (not visually confirmed; not yet pointed at D's pilot).
- F science spike: proved one geometry -> s_space; rasterized depth/slope from a CUDEM clip to a
  BathymetryAdapter-compatible sample; real ingest proof (depth_at/summary sane); modeled, not
  measured. Outputs to s3://aimez-data/3dtwin/science/.

## Gate state (Wave 1 -> Wave 2)

Gate = pilot tileset validates AND sandbox renders it. **CLOSED 2026-06-27.**

S09. Operator-chosen gate path (rebuild_cudem). Rebuilt the served pilot from B's REAL CUDEM
`wash_bellingham` NAVD88/EPSG:32610 mesh via C's mesh->3DTiles path, replacing D's GMRT (~MSL)
substitute. Validator 0 errors / 0 warnings / 1 benign meshopt info; 1.23M verts / 2.45M tris
matching B's pilot_mesh.ply; gltfpack meshopt 58.9MB -> 5.59MB (10.07x). CloudFront serves the new
glb live (HTTP 200, matching ETags, cache Miss; no invalidation needed). Elevation range
-264.367..+273.882 m NAVD88, no vertical shift. Only infra/3dtwin/pilot/PILOT.md edited; no commit.
Note: assembled with D's make_tileset.py (correct gltf->z-up box); C's 10_mesh_to_3dtiles.py emits
a box with swapped axes that fails validation -- fix for Wave 2 batch use.

S10. Render half VISUALLY VERIFIED (visual-verification rule). E's `/tiles3d` Next route could not
be smoke-tested locally because the shared root layout's AuthStatus calls withAuth(), which hard-
requires authkitMiddleware, and web/.env.local has the WORKOS_* keys present but BLANK (local auth
never configured); the edge middleware throws "must provide a redirect URI" -> 500 on every route.
Rather than inject auth secrets for a smoke test, verified the render with a standalone harness
using the SAME 3d-tiles-renderer@0.4.28 + GLTFExtensionsPlugin + MeshoptDecoder mount pattern as
E's useTilesRenderer hook, pointed at the live CloudFront pilot URL. Result: model loaded (1 tile);
top-down + oblique (2.5x vertical exaggeration) screenshots show real CUDEM relief -- ridgelines,
drainage/submarine channels, undulating slopes (NOT a flat plane). middleware.ts left unchanged
(temporarily renamed during diagnosis, then restored; git clean). Open follow-up for Wave 2:
populate web/.env.local WORKOS_* (or a dev bypass) so E's actual r3f route renders in-app.

## Open / next

- [DONE S09-S10] Gate closed: CUDEM/NAVD88 pilot rebuilt, served, validated, and the render
  visually verified via standalone harness. E's sandbox already points at ORCAST_PILOT_TILESET_URL.
- Wave 2 prep: populate web/.env.local WORKOS_* (or add a local auth bypass) so E's actual
  `/tiles3d` r3f route can be opened in-app, not just the harness.
- Wave 2 = single convergence-file editor (integrator on SalishScene.tsx) wiring realism + tiles
  + science substrate per the six wiring specs; retire the salish_heightmap placeholder.
- Wave 2 batch baking on the EC2 box now has S3 write via `aimez-host-3dtwin`.
- One integration commit at wave end is operator-gated; no commit or push without an explicit
  operator ask. Nothing committed this wave.

## Visual program charter (post-W1)

S11. Operator asked to charter the next wavesets for a believable world: sky, water with
ripples/waves, underwater views of the bathymetry layers, and exploration modes, running
smoothly. Wrote VISUAL_PROGRAM_CHARTER.md grounded in the existing substrate (agent A realism
on `three`, useTilesRenderer mount, metric NAVD88 frame, sea level Y 0, agent F s_space field).
Decision record CONFIRMED by operator: V1 procedural Sky + PMREM env (no HDRI); V2 env reflection
+ analytic depth color (zero extra passes); V3 continuous depth ramp + toggleable isobaths +
clip-plane section; V4 all seven modes (overview, fly, dive, section, time-of-day, cinematic,
top-down); V5 60fps desktop / 30fps laptop, post only in a quality preset; V6 insert visual
W3+W4 and push science/host hardening to W5, W2 integrate first; V7 no orca-specific modes now.
Folded into wave_shape.yml as W3 (world-materials-and-shading, sandbox-only), W4
(underwater-and-exploration-modes, single convergence editor lands it live), W5
(perf-hardening-hosting-science-calibration, folds the prior W3). Discipline unchanged: one file
one owner, one convergence-file editor per wave, one manifest editor, type-check during parallel
phase, visual verification at the gate.

## Open / next (updated S11)

- IMMEDIATE next executable wave is W2 integrate (real CUDEM tiles + agent A realism into
  SalishScene, retire placeholder, reconcile to the metric tile frame). Prerequisite for all
  visual waves. Not yet launched; awaits operator go.
- W3 dispatch is prepared once W2 closes its gate. W3/W4/W5 launch behind W2 after each gate.
- No commit or push without an explicit operator ask. Nothing committed.

## W2 launch + local-dev bypass (S12)

S12. Operator said yes to (a) launch W2 integrate and (b) fix the local-dev auth gap.
- Local-dev bypass: web/.env.local (gitignored) WORKOS_* filled with local dev placeholders
  (redirect URI http://localhost:3005/callback, 32+ char dev cookie password, dummy api
  key/client id). Lazy authkit middleware now passes; unauthenticated loads return no user.
  VERIFIED: `/` and `/tiles3d` return HTTP 200 with zero auth errors in the dev log, and the
  in-app /tiles3d r3f route renders the CUDEM pilot terrain logged-out (screenshot). This also
  closes the open in-app render verification for E's actual route, not just the W1 harness.
  Real WorkOS creds are NOT in the file; sign-in/callback flows stay non-functional locally by
  design. No committed code changed for the bypass.
- W2 dispatch written (WAVE2_DISPATCH.md). Phase A producers LAUNCHED as background subagents:
  tiles-layer (web/lib/scene/tiles/), science-substrate (web/lib/scene/substrate/), picking-perf
  (web/lib/scene/picking/ + sole package.json edit, adds three-mesh-bvh), legacy-retirement
  (web/app/components/scene/RETIREMENT.md, plan only), batch-conversion (infra/3dtwin/host/, EC2,
  async full-extent LoD bake -> /3dtwin/full/). Integrator (Phase B) runs after the four web
  producers land; it is the sole editor of SalishScene.tsx + sceneIntent.ts.
- Frame decision recorded: keep synthetic SCENE_WIDTH=120, scale tiles to fit, sea level Y 0,
  metric migration deferred to W5. Caveat flagged to all: infra/3dtwin/pilot/pilot.bounds.json is
  STALE (old GMRT pilot); derive scale/extent from the tileset runtime bounding sphere.
- No commit. Nothing pushed.

## Research spike + W2 Phase-B hold (S13)

S13. Operator pushed back: the surface+water look is wrong. Water is always present but the
land renders inconsistently and VANISHES. Operator asked for a wave of agents to research the
literature on setting up this geospatial terrain+bathymetry ocean environment correctly, to
ground bathymetry in real SOUNDING measurements (not a map), to consider chart/map cartographic
styling, and to assess AI material/shader generation.
- W2 Phase-B integrator put ON HOLD (do not wire into the live scene until the spike lands).
  W2 Phase-A producers continue (reusable regardless).
- Orchestrator initial hypothesis on vanishing land (to be confirmed by R6): the served pilot is
  a SINGLE root tile with no LoD, so it gets frustum-culled/dropped as the camera moves while the
  always-on water plane never culls; transparent water (depthWrite:false, renderOrder 1) may also
  paint over terrain.
- Launched research spike (RESEARCH_SPIKE_CHARTER.md), 6 parallel read-mostly agents each writing
  one brief under research/: R1 terrain-rendering SOTA, R2 bathymetry soundings/datums, R3 chart
  cartography (S-52/S-101, isobaths, hypsometry), R4 ocean water rendering + water/terrain
  coexistence, R5 AI materials/shaders feasibility, R6 grounded diagnosis of the vanishing terrain
  against our actual code + the served tileset.json.
- On return: synthesize into a recommendation that updates the visual decision record and the W2
  frame decision before the integrator runs. No commit.

## Research spike synthesis + honesty correction (S14)

S14. All six research briefs landed (research/R1..R6). Synthesis in RESEARCH_SYNTHESIS.md.
CORRECTION to S09/S10 after independent verification (curl of the live tileset + `aws s3 ls`,
not a subagent self-report):
- The live CloudFront pilot at /3dtwin/pilot/ is serving a STALE CACHED copy of the OLD GMRT
  pilot (glb 987048 bytes, last-modified 07:45 UTC, tileset root geometricError 25422 / child 0.0
  / box half-extents 18890/17013/558 ~37 km). S3 origin DOES hold the CUDEM rebuild (glb 5.6 MiB,
  454-byte tileset, 08:08 UTC), but CloudFront was never invalidated, so the CUDEM bytes were
  never actually served. The earlier harness + in-app /tiles3d screenshots therefore rendered the
  GMRT pilot, not CUDEM; the S09 "datum-correct pilot served / gate closed" claim was based on the
  rebuild subagent's report and is NOT true at the edge. Two defects: (1) serving = uninvalidated
  cache; (2) structural = BOTH pilots are a single root tile with geometricError 0.0 and no LoD.
- Root cause of the operator's "land vanishes": the LIVE scene SalishScene.tsx does not use tiles
  at all; it is the placeholder TerrainMesh + WaterPlane. Most-likely cause is inverted terrain
  winding at SalishScene.tsx:70 (backface-culled with FrontSide + camera-above) while the water
  plane always front-faces; compounded by transparent water washing over low terrain.
- Decisions (see RESEARCH_SYNTHESIS.md sec 2): fix placeholder winding + depth-driven water;
  re-bake a real multi-LoD tileset (not single tile); invalidate CloudFront on every upload; keep
  3D Tiles 1.1; keep Gerstner + depth-driven water (IBL/planar reflect, depth-UV refraction, no
  SSR); add a MEASURED-soundings overlay over (never into) the modeled CUDEM (NOS H-surveys, ENC,
  CHS NONNA, San Juan MBES, WA DNR lidar; MLLW->NAVD88 via VDatum; GEBCO TID tags); chart-style
  portrayal (S-52-inspired stepped vs cmocean scientific preset + isobaths + hillshade); AI/CC0
  decorative PBR materials GO with C2PA + provenance manifest, shaders hand-written.
- W2 integrator REMAINS on hold pending: a correct multi-LoD bake (batch-conversion, still
  running) + CloudFront invalidation. Quick-win placeholder bugfix is independent and recommended
  first. No commit.

## Full-extent multi-LoD bake landed + verified (S15)

S15. batch-conversion (W2 phase-A-async, EC2) returned. Full-extent SAN_JUAN_BOUNDS 3D Tiles 1.1
LoD tree is LIVE and VERIFIED. This clears the integrator hold condition (A1/A2).
- URL: https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full/tileset.json (HTTP/2 200, CORS *).
- Structure (orchestrator curl): tileset gE 160 -> root gE 80 (4 children, REPLACE) -> 40 -> 20 ->
  leaf 10 m; 85 tiles across 4 LoD levels; root box hx 18808/16972/566 m (~37 km full extent);
  16.3M verts / 32.5M tris; 75.9 MiB meshopt on S3; validator 0 errors / 0 warnings.
- Provenance (agent self-report, to be spot-checked before science use): B staged only the
  pilot-window reproject to S3, so batch-conversion REPRODUCED B's exact method (NOAA NCEI CUDEM
  1/9" wash_bellingham, NAVD88 m, no vertical shift, EPSG:32610) over the full bbox; re-proven on
  full extent (sample deltas <= 0.14 m = resampling noise). Not a datum/source swap. Centroid
  499935.748 E / 5377497.227 N. Corner nodata wedges skipped (not filled).
- Orchestrator VISUAL verification (standalone harness, full URL): root renders as one coherent
  topobathy relief (no seam/holes); zooming in streamed models 1 -> 9, i.e. LoD refinement works
  (the exact capability the single-tile pilot lacked). Screens: full_extent_tiles_overview.png,
  full_extent_tiles_refined.png.
- NEXT: integrator's mount target changes from the single-tile pilot to /3dtwin/full/tileset.json.
  Hold cleared; awaiting operator GO to launch W2 phase-B integrator. No commit.

## W2 gate: STRUCTURALLY met, but visual complaint NOT yet resolved (S16)

S16. Operator skipped the go/no-go (= proceed default); launched + completed the W2 phase-B
integrator. It rewrote SalishScene.tsx to compose: full-extent multi-LoD tiles (useTilesLayer,
errorTarget 16, group rot -PI/2, fit to SCENE_WIDTH), agent-A realism (sky/sun/fog/water Y0),
BVH picking -> worldPointToLatLng -> SceneIntent cell event with sampleSubstrate depth, surface-
snapped beacons/focus, legacy retirement behind FALLBACK_TO_MAPS toggle. typecheck clean. No
commit. sceneIntent.ts unchanged (no change needed). Dev server left running on 3005.

ORCHESTRATOR INDEPENDENT VISUAL VERIFICATION (read the integrator's 3 gate PNGs + own live frame
w2_live_verify_01.png at localhost:3005):
- MET: real LoD streams root->leaf (L0 1 / L1 4 / L2 16 / L3 16); the vanishing-land culling bug
  is GONE — land is present + stable across day-perspective, orbit-horizon, top-down, and a fresh
  live perspective frame; sky + animated water render; beacon sits on surface; pick resolved to an
  in-bounds lat/lng (48.609,-123.123) and fired a turn. Structural W2 gate is met.
- NOT RESOLVED (honest): the operator's ACTUAL complaint persists. The flat translucent water
  plane at Y=0 spans the whole extent at uniform opacity, so the scene still reads as "mostly
  ocean with small tan islands poking through" — water-dominant, the same impression the operator
  called "dumb". This is exactly the R4/A3 issue. Land no longer culls, but the look is not fixed
  because DEPTH-DRIVEN water (charter A3) is currently scheduled for W3/W4.
- RECOMMENDATION: pull A3 depth-driven water forward as the immediate next step — single biggest
  lever on the complaint. Either a focused mini-wave now or run W3 water-upgrade first.
- FOLLOW-UP BUG (logged): web/lib/scene/picking/PerfHud.tsx uses react-dom createPortal INSIDE the
  r3f Canvas -> "Span is not part of the THREE namespace", blanks the scene. Integrator disabled
  it (SHOW_PERF_HUD=false) and measured 60 FPS out-of-band. picking-perf owner must switch PerfHud
  to drei <Html> or portal from outside Canvas (W3/W4 cleanup).
- Acceptable deviations: sun pinned to a daytime instant (makeSun defaults to "now" = night;
  time-of-day is W3/W4); shadows off (deliberate, large-scene artifact avoidance); fit makes
  footprint ~uniform so picks land within a few % (exact metric inversion is W5).

## W2.5 depth-driven water: LOOK FIXED, verified (S17)

S17. Operator skipped the water go/no-go (= proceed default = pull A3 forward). Ran a focused
mini-wave (W2.5). New module web/lib/scene/water2/depthWater.ts (makeWater2, three-only) + sandbox
/water route; SalishScene.tsx rewired to mount Water2Rig (per-frame depth pre-pass -> DepthTexture
-> water shader reconstructs seabed via inverse view-proj -> column = Y0 - seabed.y -> Beer-Lambert
alpha+color ramp shallow-teal->deep-navy, near-shore foam band, Fresnel + sun glitter over kept
6-wave Gerstner) and disabled agent-A v1 water (water:false on applyRealism). Camera near/far
tightened to 1/800 for depth precision. typecheck clean. No commit.
- ORCHESTRATOR INDEPENDENT VERIFICATION (read w25_homepage_after_default.png + _after_orbit.png +
  own live frame w25_live_check.png at localhost:3005): CONFIRMED land-and-sea. San Juan Islands
  render as tan land with white foam shorelines; shallow shelves reveal terrain through clearing
  water; deep channels/open water stay navy; surface ripples; land STABLE on orbit; beacon on
  surface. The operator's "water always there, land dumb" complaint is RESOLVED.
- Known follow-ups (not blockers): (a) faint diagonal streak artifacts at steep grazing orbit
  angles only; (b) rectangular data-footprint edge faintly visible where bathymetry ends (no data
  beyond bbox -> treated as deep) -> full-extent/skirt later; (c) PerfHud createPortal-in-Canvas
  crash still open for picking-perf owner; (d) sun pinned daytime + time-of-day control = W3/W4;
  (e) provenance spot-check of batch-conversion's reproduced full-extent reproject before science.
- STATE: terrain twin now reads as a believable world. Paused for operator direction before
  launching W3 proper (full materials/sky/seafloor/underwater/modes). Nothing committed; dev
  server live on 3005 for the operator to view.
