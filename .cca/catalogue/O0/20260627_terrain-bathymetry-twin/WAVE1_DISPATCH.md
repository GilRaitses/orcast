# Wave 1 dispatch, orcast terrain+bathymetry coastal twin

Status: READY. NOT launched. Launch is the next operator gate. Model: inherit (all six).
Six parallel agents, disjoint scopes, none edits `web/app/components/scene/SalishScene.tsx`,
type-check validation only, no dev server / full build. Large artifacts to S3, never git.
No commit/push by any agent without an explicit operator ask; each agent returns a wiring spec
and its results instead, and the orchestrator does one integration commit at wave end (also
operator-gated).

Shared context (every agent prompt embeds this):
- Charter: `.cca/catalogue/O0/20260627_terrain-bathymetry-twin/WAVESET_CHARTER.md`.
  Decision record: `.cca/catalogue/O0/20260627_terrain-bathymetry-twin/DECISION_RECORD.md`.
  Reference implementation: `~/.cursor/plans/realistic_nyc_3d_viewer_c0b6b2b4.plan.md`.
- GOAL: replace the coarse ETOPO1 placeholder geometry in the orcast Salish Sea scene with a
  higher-resolution integrated land+seafloor surface, served as OGC 3D Tiles 1.1 (glTF) and
  rendered via `3d-tiles-renderer` in the existing react-three-fiber scene, with the same
  geometry feeding the `s_space` depth/habitat science consumer. One geometry, no drift.
- Repo: `/Users/gilraitses/orcast` (git `main`). Web: Next.js under `web/` (`@react-three/fiber`
  8, `@react-three/drei` 9, `three` 0.169). Backend: FastAPI under `src/aws_backend/`.
- Study extent (`SAN_JUAN_BOUNDS`): min_lat 48.40, max_lat 48.70, min_lng -123.25, max_lng -122.75.
- Primary source: NOAA NCEI CUDEM 1/9 arc-second topobathy (`wash_pugetsound`), NAVD88 m
  vertical (EPSG:5703), NAD83 horizontal (EPSG:4269); tiles at
  `https://coast.noaa.gov/htdata/raster2/elevation/NCEI_ninth_Topobathy_2014_8483/wash_pugetsound/`.
  Target CRS EPSG:32610 (UTM 10N, m). Vertical reference NAVD88 m. Optional land refinement
  USGS 3DEP (public domain); GEBCO/CHS for any Canadian-side gap.
- Conversion host (GROUNDED 2026-06-27): the `aimez-services` EC2 instance
  (`i-04a649f91274e9fce`, c6i.xlarge), reachable as `ssh -i ~/.ssh/pax-ec2-key.pem
  ubuntu@44.197.243.177` (also SSM-managed in account 198456344617, us-east-1). It is
  **x86_64 / Ubuntu 22.04**, 4 vCPU, 7.6 GB RAM, ~20 GB free disk. It HAS `docker` and
  `python3`; it does NOT have gdal/ogr2ogr/pdal/gltfpack/node. Therefore run converters as
  official **linux/amd64** docker images natively on this x86_64 host (e.g. `osgeo/gdal`,
  `pdal/pdal`, a `3d-tiles-tools`/`gltfpack` image) — native arch, NO emulation (charter B.6).
  It already has `~/bakeoff` and `~/borough` dirs from the pax NYC tiler lineage; do not touch
  those. Use your own remote workdir `~/3dtwin/<your-role>/`. Stage large artifacts to S3
  (`s3://aimez-data/3dtwin/...`), not git.
- Convergence file (DO NOT EDIT this wave): `web/app/components/scene/SalishScene.tsx`.
- Manifest editor for the wave: ONLY agent E (renderer-sandbox) may edit `web/package.json`.
- Honesty: label all modeled outputs "modeled, not measured"; report measured results, not
  estimates; be explicit about what you verified vs assumed.

---

## Agent A — Realism module

You are agent A in Wave 1 of the orcast terrain+bathymetry coastal twin charter.
[Embed shared context above.]

YOUR TASK: own the NEW directory `web/app/components/scene/realism/`. Build a standalone,
self-contained scene-realism module for the Salish Sea twin, validated against a throwaway
scene (not the live scene). Deliver:
- a water surface treatment (animated normals or a simple Gerstner/again-flat shader is fine;
  it must read as ocean, not a flat plane),
- atmosphere/fog + a sun/directional-light helper appropriate to ~48.5 N,
- an ocean depth color ramp (shallow -> deep) and a land elevation ramp consistent with the
  current `depthColor` intent in `SalishScene.tsx` (read it for palette continuity; do not edit it).
Export a small API the integrator can call (e.g. `applyRealism(scene, opts)` /
`makeWater(opts)` / `makeSun(date, lat, lng)`), pure where possible.

DELIVERABLES: the module files + `WIRING-realism.md` telling the integrator exactly how to mount
it into `SalishScene.tsx` (what to import, where, what it replaces).

VALIDATION: `tsc --noEmit` (or the web type-check) on your files only. No dev server / build.

COLLISION-AVOIDANCE: do NOT edit `SalishScene.tsx` or `web/package.json`. Add no dependencies
(use what is already in `web/package.json`). Commit nothing; return the wiring spec + results.

RETURN: exported API signatures, decisions, type-check result, risks. No commit.

---

## Agent B — Reproject + mesh recipe (OWNS THE TWO FOOTGUNS)

You are agent B in Wave 1 of the orcast terrain+bathymetry coastal twin charter.
[Embed shared context above.]

YOUR TASK: own the NEW directory `infra/3dtwin/reproject/`. On aimez.ai EC2 (confirm reachability
and `uname -m`, install arch-native GDAL/PDAL first), produce a reproducible recipe + scripts that:
1. fetch/clip NOAA NCEI CUDEM 1/9 topobathy to the study bbox (one coastal pilot chunk is enough
   this wave),
2. reproject from NAD83 geographic to EPSG:32610 (UTM 10N, meters) WITHOUT any implicit vertical
   shift (preserve NAVD88 m exactly),
3. mesh the single integrated surface into a clean triangulated mesh (decimate sensibly),
4. mark the 0 m NAVD88 contour as the modeled shoreline; since CUDEM is already a continuous
   topobathy surface, NO two-dataset weld is required on the primary path. Document the weld
   procedure that WOULD apply if 3DEP land is later blended (VDatum MLLW->NAVD88 m first, weld at
   the 0 m line against `data/geo/san_juan_land.geojson`, no gap/overlap).
Confirm CUDEM tile coverage over the full bbox; flag any Canadian-side (west of ~-123.1) gap for
GEBCO/CHS fill.

DELIVERABLES: scripts + `RECIPE.md` (exact commands, CRS/datum proof, coverage notes) +
`WIRING-geometry.md` describing the output mesh format/CRS/units for the tiler agent. Large mesh
outputs to S3 (record the URIs); only scripts + small proofs to the repo dir.

VALIDATION: run the recipe on the pilot chunk; report the real CRS, vertical datum, vertex/tri
counts, and bbox coverage. State explicitly that NAVD88 m is preserved (show a sample elevation
before/after reprojection).

COLLISION-AVOIDANCE: do NOT edit `SalishScene.tsx` or `web/package.json`. Native arch only, no
emulation. Commit nothing.

RETURN: recipe summary, output S3 URIs, CRS/datum/units proof, coverage + risks. No commit.

---

## Agent C — Tiler bake-off

You are agent C in Wave 1 of the orcast terrain+bathymetry coastal twin charter.
[Embed shared context above.]

YOUR TASK: own the NEW directory `infra/3dtwin/bakeoff/`. On aimez.ai EC2 (arch-native tools),
take one reprojected pilot chunk (coordinate with agent B's output format via `WIRING-geometry.md`;
if B's output is not ready, generate a stand-in chunk and state that) and convert it TWO ways:
(1) meshed-surface to OGC 3D Tiles 1.1 (glTF), and (2) a quantized-mesh / terrain-tile path.
Compare output size, draw calls, and visual fidelity; recommend ONE for Wave 2.

DELIVERABLES: scripts + `BAKEOFF.md` with the measured comparison table and a clear recommendation
+ `WIRING-tiler.md` (the chosen pipeline's exact steps). Tile outputs to S3 (URIs recorded).

VALIDATION: produce both candidates on the one chunk; report real measured sizes/draw counts
(not estimates).

COLLISION-AVOIDANCE: do NOT edit `SalishScene.tsx` or `web/package.json`. Native arch only.
Commit nothing.

RETURN: comparison table, recommendation, output S3 URIs, risks. No commit.

---

## Agent D — Optimize + assemble pilot tileset

You are agent D in Wave 1 of the orcast terrain+bathymetry coastal twin charter.
[Embed shared context above.]

YOUR TASK: own the NEW directory `infra/3dtwin/pilot/`. On aimez.ai EC2 (arch-native gltfpack +
CesiumGS 3d-tiles-tools), take the pilot tiles/mesh and produce ONE valid, optimized 3D Tiles 1.1
pilot tileset (meshopt compression + quantization), validated with a 3D Tiles validator. Report
real on-disk sizes and tile counts.

DELIVERABLES: scripts + `PILOT.md` (validator output, real sizes, the public/S3 tileset URL for
the sandbox agent to mount) + `WIRING-pilot.md`. The tileset artifact goes to S3, NOT git.

VALIDATION: run the 3D Tiles validator on the assembled tileset; paste the pass/fail result and
the real sizes.

COLLISION-AVOIDANCE: do NOT edit `SalishScene.tsx` or `web/package.json`. Native arch only.
Commit nothing.

RETURN: validator result, real sizes, tileset S3 URL, risks. No commit.

---

## Agent E — Renderer sandbox (SOLE MANIFEST EDITOR)

You are agent E in Wave 1 of the orcast terrain+bathymetry coastal twin charter.
[Embed shared context above.]

YOUR TASK: own a NEW isolated Next.js route `web/app/(sandbox)/tiles3d/` that mounts a 3D Tiles
1.1 pilot tileset via NASA-AMMOS `3d-tiles-renderer` INSIDE react-three-fiber (the existing
stack), proving the imperative `TilesRenderer` (its own `update()`, camera sync, LoD) integrates
with r3f's render loop, `OrbitControls`, shadows, and a basic raycast pick — WITHOUT touching
`SalishScene.tsx`. Use agent D's pilot tileset URL if ready; otherwise mount a public sample
tileset and clearly note the substitution. This route is the de-risking proof for the Wave 2
live-scene integration.

YOU ARE THE ONLY AGENT THIS WAVE PERMITTED TO EDIT `web/package.json`: add `3d-tiles-renderer`
(and its required peer/loader deps) at a pinned version. Add nothing else.

DELIVERABLES: the route files + the `web/package.json` change + `WIRING-renderer.md` documenting
the r3f + `TilesRenderer` mount pattern (lifecycle, camera/update wiring, dispose) for the Wave 2
integrator.

VALIDATION: `tsc --noEmit` on the web app. Do NOT run a dev server or full build (parallel-wave
rule). If you can type-check only, do that and report it.

COLLISION-AVOIDANCE: do NOT edit `SalishScene.tsx`. Commit nothing; return the diff + wiring spec.

RETURN: route API, the exact `package.json` diff, the r3f mount pattern, type-check result,
risks. No commit.

---

## Agent F — Science feasibility spike

You are agent F in Wave 1 of the orcast terrain+bathymetry coastal twin charter.
[Embed shared context above.]

YOUR TASK: own the NEW directory `infra/3dtwin/science/`. On aimez.ai EC2 (arch-native GDAL),
rasterize a depth (and optionally slope/aspect) field from the SAME pilot mesh/surface used for
the render (agent B's output; or a CUDEM clip directly, stating which), at a resolution suitable
for the `s_space` covariate. Confirm the existing `BathymetryAdapter`
(`src/aws_backend/sources/bathymetry.py`, JSON grid/point form) can ingest the derived field, and
prototype a derived depth/habitat layer. This proves one geometry feeds both render and science.

DELIVERABLES: scripts + a sample derived field + `SCIENCE-SPIKE.md` (how it was produced, the
exact `BathymetryAdapter`-compatible format, and the provenance line) + `WIRING-science.md`. The
output replaces the ETOPO1 `data/geo/san_juan_bathymetry.json` provenance in a later wave; do NOT
overwrite that file this wave. Large rasters to S3.

VALIDATION: load the derived field through `BathymetryAdapter` (or a faithful local harness) and
show `depth_at()` returns sane values inside the bbox. Label everything "modeled, not measured".

COLLISION-AVOIDANCE: do NOT edit `SalishScene.tsx`, `web/package.json`, or the committed
`san_juan_bathymetry.json`. Native arch only. Commit nothing.

RETURN: derived-field format, ingest proof, provenance line, risks. No commit.

---

## Wave 1 exit (orchestrator, operator-gated)

Gate to Wave 2: agent D's pilot tileset validates AND agent E's sandbox renders it. On gate pass,
the orchestrator collects the six wiring specs, does ONE integration commit + push (only on
explicit operator ask), and prepares the Wave 2 dispatch (single convergence-file editor =
integrator on `SalishScene.tsx`).
