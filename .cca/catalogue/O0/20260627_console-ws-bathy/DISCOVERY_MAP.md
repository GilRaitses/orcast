# WS-BATHY discovery map

Home: `.cca/catalogue/O0/20260627_console-ws-bathy/`
Date: 2026-06-27. Wave: Discovery. Status: COMPLETE, read-only, doc-producing.
Grounds the research in this codebase, names every file to create or edit, its owner, the seam, and the honesty label.

## 1. Key fact, resolved from the data

The served CUDEM tileset IS topobathy. The seafloor is already baked into the render geometry. A separate measured seabed source is NOT required for the water to read depth. See `RESEARCH_SYNTHESIS.md` sections 1 and 2. Proof, `infra/3dtwin/host/WIRING-host.md` elevation range -376.431 to +733.885 m NAVD88, and NOAA NCEI metadata that only the 1/9 arc-second CUDEM integrates bathymetry and topography.

Therefore the WS-BATHY build is a styling and provenance build on an existing seabed, not a new seabed mesh. The teams produce a depth field reader, a bathymetric seabed tint, water tuning, and a measured-versus-modeled honesty layer.

## 2. What already exists and is reusable, with its public surface

### 2.1 water2 (`web/lib/scene/water2/`), owner the existing water2 module

Public surface, reuse only, do not edit internals.

- `makeWater2(opts: Water2Options): Water2Handle`.
- `Water2Options`, the tuning levers, `colorShallow`, `colorDeep`, `colorFoam`, `skyColor`, `sunDirection`, `amplitude`, `speed`, `depthColorScale`, `depthAlphaScale`, `foamDepth`, `maxOpacity`, `fresnelStrength`, `width`, `depth`, `segments`, `level`.
- `Water2Handle`, `mesh`, `material`, `depthTarget`, `renderDepthPrepass(renderer, scene, camera)`, `update(seconds, camera, sunDirection?)`, `setSize(w, h, dpr)`, `setSunDirection(dir)`, `dispose()`.
- The fragment shader debug uniform `uDebug` plus `uDebugScale` renders the water-column thickness as grayscale, the acceptance instrument for a real depth read.

What WS-BATHY may change THROUGH the water2 owner, the per-channel absorption upgrade and any default palette change. These touch `depthWater.ts` internals, so they are requested from the water2 owner, not edited here.

### 2.2 substrate (`web/lib/scene/substrate/`), owner `science-substrate`

Public surface, reuse only, do not edit internals.

- `loadSubstrate(url?): Promise<SubstrateField>`, fetched from `/geo/sample_san_juan_bathymetry_cudem.json`.
- `sampleSubstrate(field, lat, lng): number`, nearest-neighbour modeled depth, negative below sea level, `NaN` for no data.
- `buildSubstrateOverlay(field, opts?): THREE.Object3D`, a toggleable depth-tinted `THREE.Points` cloud, already honesty-tagged. Accepts a `project` callback so the integrator can place it in the live tile frame, and `colorDeep`, `colorShore`, `colorHigh`, `pointSize`, `opacity`.
- `SubstrateField`, `source`, `dataset`, `bounds`, `resolution_deg`, `provenance`, `modeledNotMeasured: true`, `points`, `minDepthM`, `maxDepthM`.
- `SUBSTRATE_URL`, `SUBSTRATE_LABEL = "modeled, not measured"`.

`buildSubstrateOverlay` is built but NOT currently mounted in `SalishScene.tsx`. It is the cleanest existing hook for the seabed bathymetric tint, retuned to a perceptually uniform `deep` palette, and for a substrate-driven coverage overlay.

### 2.3 SalishScene (`web/app/components/scene/SalishScene.tsx`), CONVERGENCE FILE, single editor per the calendar

What it already does, `RealismRig`, `Water2Rig`, the tiles primitive, `SurfaceBeacons`, `FocusMarker`, `OrbitControls`, and the pick handler that fills `depth_m` from `sampleSubstrate`. `TILESET_BOUNDS` and `SCENE_DEPTH` define the live frame.

WS-BATHY edits this file ONLY in its phase B, and ONLY after WS-INTENT then WS-SCENIC have taken their turns, per the convergence calendar in `PROGRAM_WAVESETS_CHARTER.md` section 4. Until then WS-BATHY stages its scene changes as pure modules the phase-B editor mounts.

### 2.4 Supporting surfaces

- `web/lib/sceneIntent.ts`, `projectToScene`, `sceneDepth`, `SCENE_WIDTH`, `HEIGHT_SCALE`, the projection the overlay `project` callback must match.
- `src/aws_backend/sources/bathymetry.py`, the Python `BathymetryAdapter`, the depth sign convention authority. Read-only reference, not edited by this waveset.
- `infra/3dtwin/science/WIRING-science.md`, the documented later-wave path to swap the committed asset. Out of scope here.

## 3. Where the new bathy modules slot

All new modules are pure, framework-free where possible, mirroring the water2 and substrate factory style. They build in phase A in parallel. They are mounted by the single phase-B editor of `SalishScene.tsx`.

Proposed new module paths.

- `web/lib/scene/bathy/` is the new sibling family for this waveset, parallel to `water2/` and `substrate/`, no edits to either.
  - `web/lib/scene/bathy/provenance/` (Bathy Data Engineer). A typed loader and a coverage model for the measured reference, BlueTopo `bathy_coverage` on the US side and CHS NONNA presence on the BC side, plus the carried provenance and licence strings. Produces a measured-versus-modeled signal queryable by lat or lng, defaulting to modeled where no measured coverage exists. Fetched asset under `web/public/geo/`, not bundled, mirroring substrate.
  - `web/lib/scene/bathy/field/` (Bathy Terrain Builder). A seabed depth-field reader that wraps the existing substrate field and exposes a normalized depth for tinting, reconciled to the live tile frame and the NAVD88 Y = 0 datum. It reads `SubstrateField` and the live seabed, it does not author a second seabed mesh.
  - `web/lib/scene/bathy/style/` (Water and Depth Stylist). The bathymetric seabed tint, a perceptually uniform `deep` ramp plus relief, built as a buildable object or as a tuned `SubstrateOverlayOptions` set passed to `buildSubstrateOverlay`, plus the proposed `Water2Options` tuning set (palette and the requested per-channel absorption). Pure, returns objects and option sets, mounts nothing.
  - `web/lib/scene/bathy/honesty/` (Honesty Labeler). The label model that stamps `modeledNotMeasured` and the measured-coverage label onto every bathy surface and any UI string, reusing `SUBSTRATE_LABEL` and adding a measured-coverage label. Pure helpers.
- `web/public/geo/` new fetched assets for the measured reference, for example a BlueTopo-derived coverage raster or point set and a NONNA-derived coverage set, copied verbatim like the substrate JSON, swappable without a rebuild, source of truth under `infra/3dtwin/`.

The exact internal file split inside each team folder is the producer's choice under one-file-one-owner, the dispatch fixes the folder boundaries and the public surface.

## 4. The scene-mount seam, phase B, serialized after SCENIC

- Convergence file, `web/app/components/scene/SalishScene.tsx`.
- Order, INTENT then SCENIC then BATHY, each a single phase-B editor. WS-BATHY mounts last.
- What the phase-B editor does, add a `BathyRig` that mounts the seabed tint overlay through `buildSubstrateOverlay` with the bathy `style` options and the bathy `field` projector, applies the stylist `Water2Options` tuning to the `Water2Rig` construction, mounts the honesty coverage layer, and keeps the pick `depth_m` modeled-labeled. No new render loop, the water2 pre-pass stays the only per-frame depth pass.
- Seam discipline, the BathyRig is a pure module set mounted by the editor. WS-BATHY does not add a second depth pre-pass and does not edit the water2 or substrate internals in the convergence file.

## 5. One-file-one-owner table

| File or folder | Action | Owner team | Seam, what it reads or mounts | Honesty label it must carry |
| --- | --- | --- | --- | --- |
| `web/lib/scene/bathy/provenance/` | create | Bathy Data Engineer | reads fetched BlueTopo and NONNA coverage assets, exposes measured-versus-modeled per lat or lng | measured where coverage true, else modeled, per area, never blanket measured |
| `web/public/geo/` measured coverage asset(s) | create | Bathy Data Engineer | fetched at runtime like substrate, source of truth under `infra/3dtwin/` | provenance and licence strings, BlueTopo public domain, NONNA Open Government Licence Canada with attribution |
| `web/lib/scene/bathy/field/` | create | Bathy Terrain Builder | reads `SubstrateField` and the live seabed, normalizes depth for tinting, NAVD88 Y = 0 datum | modeled, not measured, mirrors `SUBSTRATE_LABEL` |
| `web/lib/scene/bathy/style/` | create | Water and Depth Stylist | builds the `deep` ramp tint object or `SubstrateOverlayOptions`, and the proposed `Water2Options` tuning set | modeled tint over modeled seabed, foam and water labeled atmosphere-and-physics, not survey |
| `web/lib/scene/bathy/honesty/` | create | Honesty Labeler | stamps labels on every bathy object and UI string, reuses `SUBSTRATE_LABEL`, adds a measured-coverage label | the canonical measured-versus-modeled label source for the waveset |
| `web/lib/scene/water2/depthWater.ts` | request only | water2 owner, NOT WS-BATHY | per-channel absorption upgrade and palette change requested through the owner | n/a, internal |
| `web/lib/scene/substrate/*` | request only | `science-substrate`, NOT WS-BATHY | any internal change requested through the owner | n/a, internal |
| `web/app/components/scene/SalishScene.tsx` | edit, phase B only | WS-BATHY phase-B editor, after SCENIC | mounts BathyRig, applies stylist `Water2Options`, keeps pick `depth_m` modeled | scene honesty note updated, modeled seabed, measured coverage where labeled |

## 6. Honesty ledger, the label each served surface must carry

- The seabed geometry, the modeled CUDEM topobathy already in the tiles. Label modeled, not measured.
- The seabed bathymetric tint, a styling of the modeled seabed. Label modeled.
- The depth-driven water color and alpha, physics over the modeled seabed. Not a measurement. Foam and Fresnel are physics and atmosphere, not a survey track.
- The pick `depth_m`, modeled CUDEM substrate via `sampleSubstrate`. Keep modeled, not measured.
- The measured coverage overlay, where BlueTopo `bathy_coverage` is true or NONNA is present. This is the ONLY surface allowed to read measured, and only where the source flag asserts it, never inferred.
- NONNA reference, if surfaced, must be datum-noted, chart datum not NAVD88, and must not be rendered as competing seabed geometry.

## 7. Discovery gate check

Every file to create or edit is listed with its owner and its integration seam. The only convergence-file edit proposed is `SalishScene.tsx` in phase B, owned by the single WS-BATHY phase-B editor and serialized after SCENIC per the calendar, no unowned convergence-file edit. water2 and substrate internals are request-only through their owners. Discovery gate PASSED.
