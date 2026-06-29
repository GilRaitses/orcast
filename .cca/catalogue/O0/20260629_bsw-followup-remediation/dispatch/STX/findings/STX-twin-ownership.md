# STX-R2 3D-TWIN ownership and the widening seam (findings)

Lane STX. Wave STX-R, member R2. Read-only. Reports to O0 via the STX
sub-orchestrator. repo_state_verified_against:
`61ba1d69ee36cf605f7ba741bdaa1defa8762834`.
Method: read `useTilesLayer.ts`, the SalishScene fit and framing constants, the
host bake contract, and the W2.6 datum rationale. No code edited.

## 1. How the extent is actually set (it is a baked artifact, not a constant)

The rendered extent is NOT a value the scene can widen by editing a number. It is
the geographic footprint of a baked tileset on S3 / CloudFront.

- `SalishScene.tsx:147` mounts `FULL_TILESET_URL =`
  `https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full/tileset.json`. That tileset
  is a quadtree of 85 glb tiles whose vertices only cover lat 48.40..48.70,
  lng -123.25..-122.75 (`WIRING-host.md`).
- `TILESET_BOUNDS` (`SalishScene.tsx:156`) is a DESCRIPTION of that footprint
  used for `projectToScene` / `worldPointToLatLng`, not a control. The comment is
  explicit: "Derived from the served tileset contract, NOT the stale
  pilot.bounds.json." Editing `TILESET_BOUNDS` without re-baking would only
  mis-register picks and placements against terrain that still ends at 48.40.

So "widen the extent" means: produce a new tileset (and substrate field) over a
wider bbox, then point `FULL_TILESET_URL` at it and update `TILESET_BOUNDS` to
match. The render-side edit is trivial. The artifact production is the work, and
it is 3D-TWIN-owned (see section 5).

## 2. How `useTilesLayer` sets framing (the fit math)

`useTilesLayer` does not know geography. It fits whatever tileset it is handed.

- It builds a `TilesRenderer(url)`, registers the meshopt glTF plugin, and each
  frame calls `setResolutionFromRenderer` + `update()` (`useTilesLayer.ts:94-181`).
- On first load it reads the runtime bounding sphere and, because the scene passes
  `fitScaleToWidth: SCENE_WIDTH` (= 120), scales the group so the sphere DIAMETER
  equals 120 scene units, then recenters X/Z to the origin and leaves Y at 0
  (`useTilesLayer.ts:191-219`). Vertical origin is left at NAVD88 0 m on purpose
  (the W2.6 datum fix, section 4).
- It then calls `onFit(worldSphere)`. The scene captures `sphere.radius` as
  `fitRadius` (`SalishScene.tsx:1564`), and EVERY downstream distance is sized off
  it: `worldUnitsPerMeter = fitRadius / geoRadiusMeters(TILESET_BOUNDS)`
  (`SalishScene.tsx:652`), the resting orbit radius `max(fitRadius*0.4, 24)`
  (`:668`), the resting altitude `RESTING_ORBIT_ALT_M = 6000` m converted through
  `worldUnitsPerMeter`, `camera.near/far` (`:654-659`), and OrbitControls
  `minDistance = fitRadius*0.5`, `maxDistance = fitRadius*2` (`:1595-1598`).

The consequence that matters for STX: the fit scales the WHOLE baked sphere to
120 units. A wider bbox is a bigger sphere, so a wider extent rescales the entire
frame and every camera distance derived from it (R4 quantifies the regression).

## 3. The W2.6 datum constraint a wider bake must preserve

W2.6 fixed "the land reads underwater" by keeping the tileset's glTF Y (= NAVD88
elevation in metres, the tileset has no root transform) mapped to scene Y through
the uniform fit scale with the vertical origin at 0, so NAVD88 0 m lands at scene
Y 0 (`useTilesLayer.ts:191-211`, `SalishScene.tsx:168-174`,
`W-PERFUX_RESEARCH_DISPATCH.md` standing clarification). The water plane, foam,
shoreline tint, bathy tint, and orca depth all key off `SEA_LEVEL_Y = 0` through
the same `worldUnitsPerMeter`.

A wider re-bake MUST preserve the same contract: no root transform, glTF Y =
NAVD88 m, true 1:1 vertical scale. Admiralty Inlet bathymetry runs to roughly
-100 m and the current extent already spans -376 to +734 m NAVD88, so the datum
mapping itself extends cleanly. The risk is not the datum, it is the fit scale:
the elevation range and the horizontal span both feed the bounding sphere, and a
much wider horizontal span dominates the sphere radius, which is what rescales
the frame.

## 4. The W-PERFUX framing the wider extent would fight

The resting framing is freshly tuned by W-PERFUX RP2 to STOP showing the view "so
far back". The landed values frame the San Juan core, not the whole extent:

- `RESTING_ORBIT_ALT_M = 6000` m and orbit radius `max(fitRadius*0.4, 24)` give a
  pitch of about 31 deg onto a roughly 10 to 14 km core patch
  (`SalishScene.tsx:206, 668`, `RP2_view_scope.md`).
- Startup LoD caps `RESTING_ERROR_TARGET = 32` and `RESTING_MAX_DEPTH = 2` hold
  the tree at L0..L2 (about 21 tiles, about 19 MiB) and lift to leaves only when
  the user grabs the map or a focus journey fires (`SalishScene.tsx:215-218,
  1604-1618`).

A wider extent works directly against this tuning: the same `fitRadius*0.4`
orbit factor now frames a fraction of a much larger sphere, so either the core
shrinks on screen or, if re-tightened to the core, the two new Admiralty nodes
sit about 45 to 55 km south-east, off-frame at rest and reachable only by a
journey. R4 details this regression.

## 5. Ownership and the convergence seam

The extent and framing are 3D-TWIN-owned and serialized. The STX charter and
`wave_shape.yml` lock it: any tileset-extent or framing change is 3D-TWIN-owned
and serialized on `SalishScene.tsx` and `useTilesLayer.ts` across 3D-TWIN, WFX,
ORCA, OCN, and ENV. `SalishScene.tsx` is the shared convergence file
(`PROGRAM.md` locked decision 6), edited only by a single serialized editor in an
INT wave after `git pull --rebase`. STX does not edit it unilaterally.

The full re-bake pipeline is host-side and human-gated for compute
(`PROGRAM.md` gate ledger: box compute / GPU host time = human gate):

1. `infra/3dtwin/host/01_fetch_reproject.sh`, fetch and reproject the CUDEM
   source over the wider bbox (NAD83 to EPSG:32610, NAVD88 preserved).
2. `infra/3dtwin/host/02_bake.sh` plus `bake_tree.py`, bake the LoD quadtree over
   the wider bbox. This is where tile count grows, see R3.
3. `infra/3dtwin/host/03_compress.sh`, meshopt plus quantization.
4. `infra/3dtwin/host/04_validate.sh`, `3d-tiles-validator` must report 0 errors.
5. `infra/3dtwin/host/05_upload.sh`, upload to `s3://aimez-data/3dtwin/...` and
   serve via CloudFront.
6. Re-bake or extend the substrate field
   (`infra/3dtwin/science/build_sample_json.py`) over the same wider bbox so
   `sampleSubstrate` and the bathy tint have data under the new nodes.

Source caveat: the current bake uses the CUDEM `wash_bellingham` collection.
Admiralty Inlet (lat 48.0 to 48.2) is at or beyond the southern edge of that
collection, so a wider bake may require an additional CUDEM tile (for example a
Puget Sound collection) at step 1, which is more fetch and reproject work, not a
free clip of the existing source.

## 6. The cleanest widening seam, IF O0 ever proceeds

Two shapes, both 3D-TWIN-owned. R3 and R4 cost them and recommend deferral.

- Seam A, one union tileset. Re-bake a single quadtree over the union bbox
  (about lat 48.00..48.70, lng -123.25..-122.55). Render-side change is small
  (swap `FULL_TILESET_URL`, update `TILESET_BOUNDS`, re-tune the resting orbit).
  Cost: the union bbox is about 3.3x the current area and mostly empty water and
  unrelated land between the core and Admiralty, so it is the worst load and
  framing trade (R3, R4).
- Seam B, a separate small Admiralty tileset, two-box. Bake only the Admiralty
  box (about 491 km2, the TB1 `ADMIRALTY_INLET_BOUNDS`) and mount it as a second
  tileset. This keeps the core bake untouched but breaks the scene's single-bbox
  assumption: `projectToScene`, `TILESET_BOUNDS`, the single fit, and
  `SCENE_CENTER` all assume one contiguous footprint. Two disjoint footprints 45+
  km apart in one `SCENE_WIDTH = 120` frame either reintroduce the wide-frame
  blowup or need a second projection frame and a second view, which is a larger
  architectural change than "an extent edit". This is closer to a new Admiralty
  view than a player widen.

## 7. R2 conclusions for the decision

- The extent is a baked artifact. Widening is a host re-bake plus a substrate
  re-bake, not a `TILESET_BOUNDS` edit. The render-side edit is small and
  3D-TWIN-owned on the `SalishScene.tsx` / `useTilesLayer.ts` convergence files.
- The fit scales the whole baked sphere to 120 units, so a wider bbox rescales the
  entire frame and every camera distance derived from `fitRadius`.
- A wider extent fights the just-landed W-PERFUX RP2 tightening that fixed the
  operator's "so far back" complaint.
- The cleanest seam is a 3D-TWIN-coordinated re-bake plus a single-editor INT
  edit, gated on box compute and on a GPU ACCEPT capture. Neither seam shape is
  cheap, and the source DEM may need an extra CUDEM tile.
