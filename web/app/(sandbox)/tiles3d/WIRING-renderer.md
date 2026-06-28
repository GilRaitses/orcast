# WIRING-renderer.md - mounting `3d-tiles-renderer` inside react-three-fiber

Wave 1, agent E (renderer sandbox) of the orcast terrain+bathymetry coastal twin
charter. This documents the **r3f + imperative `TilesRenderer` mount pattern** so
the Wave 2 integrator can lift it into `web/app/components/scene/SalishScene.tsx`
(the single convergence file) with no guesswork. Nothing here edits the live
scene; the proof lives entirely under `web/app/(sandbox)/tiles3d/`.

## What was added

- Dependency (sole manifest edit this wave): `3d-tiles-renderer@0.4.28` pinned
  exact in `web/package.json`. Its transitive deps (`pbf`, `pmtiles`,
  `@mapbox/vector-tile`) install automatically. Peers are already satisfied by
  the repo: `three ^0.169.0` (needs ≥0.167), `@react-three/fiber ^8.18.0`
  (needs ^8.17.9 || ^9), `react`/`react-dom` 18.3.1. **No other dependency was
  added.** Decoders (meshopt/draco/ktx2) ship inside `three/examples` (`three/addons/*`),
  so they need no extra npm package.

- Route files (all new, isolated):
  - `useTilesRenderer.ts` - the reusable lifecycle hook (the artifact Wave 2 reuses).
  - `TilesSandboxScene.tsx` - r3f `<Canvas>` proving coexistence with OrbitControls,
    shadows, and a raycast pick.
  - `TilesSandboxHost.tsx` - `dynamic(..., { ssr: false })` wrapper (mirrors `SceneHost`).
  - `page.tsx` - route at `/tiles3d` under the `(sandbox)` route group.

## The mount pattern (lifecycle)

`TilesRenderer` is **imperative**: it owns its own `.update()` per frame, its
camera registration, its LoD/error-target, and its disposal. r3f owns the render
loop. The integration is four hook bodies. See `useTilesRenderer.ts` for the
exact code; the shape is:

```ts
// 1. CONSTRUCT (useEffect, deps [url]): build once per url, dispose on unmount.
const tiles = new TilesRenderer(url);
tiles.registerPlugin(new ImplicitTilingPlugin());                 // implicit subtrees
tiles.registerPlugin(new GLTFExtensionsPlugin({ meshoptDecoder })); // glb + meshopt
// cleanup: tiles.removeEventListener(...); tiles.dispose();

// 2. CAMERA (useEffect, deps [tiles, camera]): register/unregister the active camera.
tiles.setCamera(camera);            // cleanup: tiles.deleteCamera(camera)

// 3. PER-FRAME (useFrame): the ONLY loop integration point.
camera.updateMatrixWorld();
tiles.setResolutionFromRenderer(camera, gl);  // gl = useThree(s => s.gl)
tiles.update();                                // advance one LoD/stream step

// 4. MOUNT into the scene graph (JSX): the tile meshes live under tiles.group.
<primitive object={tiles.group} />
```

`camera`, `gl`, and `invalidate` come from `useThree`. The hook also calls
`invalidate()` on the renderer's `needs-update` event so a `frameloop="demand"`
host still settles the LoD; with the default `frameloop="always"` it is a no-op
safety net.

This is exactly what the maintained `3d-tiles-renderer/r3f` `<TilesRenderer>`
component does internally - it was used as the reference. **Why hand-write it
instead of importing that component:** Wave 2 mounts into the
imperatively-authored `SalishScene` and needs the lifecycle inline and editable
(camera/error-target/shadows tied to existing scene state). The library's r3f
component is a valid alternative if a drop-in is preferred; the hook is the more
transferable form for this codebase.

## How OrbitControls coexists

`OrbitControls` (drei) operates on the same `useThree` camera. The per-frame
order is: OrbitControls mutates the camera (r3f runs control updates), then the
hook's `useFrame` reads `camera.updateMatrixWorld()` and calls
`tiles.setResolutionFromRenderer` + `tiles.update()`. No conflict: tiles only
read the camera, never move it. `makeDefault` registers the controls in
`state.controls` so other code (and the camera-fit effect) can reach
`controls.target`. The sandbox uses an `ElementRef<typeof OrbitControls>` ref to
re-target on first tileset load.

For Wave 2, `SalishScene` already mounts `<OrbitControls .../>`; keep it. The
tiles hook needs no change to controls.

## How shadows coexist

`<Canvas shadows>` is already set in `SalishScene`. The catch: tile meshes are
added to `tiles.group` **at runtime**, after the JSX renders, so they are not
configured as shadow casters by r3f. Fix in the hook on the `load-model` event:
traverse `e.scene` and set `mesh.castShadow = mesh.receiveShadow = true`
(`enableShadows` option, default true). The sandbox adds a `shadowMaterial`
ground plane to confirm the tiles cast into the shadow map. `SalishScene`'s
existing `directionalLight castShadow` then lights the tiles for free.

## How a raycast pick maps to a cell

r3f raycasts a `<primitive>` recursively, so an `onClick` on
`<primitive object={tiles.group}>` resolves hits on the dynamically streamed tile
meshes. The handler gets `e.point` = the **world-space** hit (a `THREE.Vector3`).
Two cases for turning that into a `SceneIntent` (`web/lib/sceneIntent.ts`):

- **Local-frame tiles (the orcast pilot path).** The decision record bakes the
  orcast tileset in a local EPSG:32610 (UTM 10N, meters) engineering frame. Map
  the world hit to lat/lng with the existing
  `unprojectFromScene(x, z, bounds, depth)` (same helper `SalishScene` already
  uses for its terrain pick), then emit
  `onIntent({ type: "cell", lat, lng, depth_m })`. Depth comes from the hit `y`
  (un-applying `HEIGHT_SCALE`) or from `sampleDepth`. **Confirm the pilot's local
  origin/axis convention against `projectToScene` before trusting the numbers.**
- **ECEF / georeferenced tiles (globe path, not the orcast plan).** Use
  `tiles.ellipsoid.getPositionToCartographic(point, result)` to recover
  lat/lng/height. Not needed for the local-frame orcast pilot; listed for completeness.

The sandbox HUD only prints the raw world point because the stand-in tileset is
not georeferenced to the Salish bbox - the lat/lng mapping is a Wave 2 step once
the real pilot frame is known.

## Stand-in tileset (MUST be swapped in Wave 2)

```
https://raw.githubusercontent.com/CesiumGS/3d-tiles-samples/main/1.1/SparseImplicitQuadtree/tileset.json
```

A public OGC **3D Tiles 1.1** sample (asset.version "1.1", implicit QUADTREE
subtrees, `.glb` content), served with `Access-Control-Allow-Origin: *`. Defined
as the exported constant `STANDIN_TILESET_URL` in `TilesSandboxScene.tsx`.
**Wave 2 replaces this single constant** with agent D's baked orcast pilot
tileset URL (S3/CDN). The mount code does not change - only the URL. This is a
stand-in chosen because agent D (pilot bake on EC2) is deferred; it exercises the
mount pattern, not the orcast geometry.

## LoD / error-target knobs

`tiles.errorTarget` (px screen-space error; lower = more detail/more tiles, the
sandbox uses 8) and `tiles.maxDepth` are set in a separate effect so they can be
tuned at runtime without rebuilding the tileset. For the orcast pilot, tune
`errorTarget` against frame time in the Wave 2 perf harness.

## Adding DRACO / KTX2 for the pilot (if the bake uses them)

`GLTFExtensionsPlugin` already takes the loaders; meshopt is wired. To add the
others (no new npm dep - both come from `three/addons`):

```ts
import { DRACOLoader } from "three/addons/loaders/DRACOLoader.js";
import { KTX2Loader } from "three/addons/loaders/KTX2Loader.js";
// const dracoLoader = new DRACOLoader().setDecoderPath("/draco/");      // host the wasm
// const ktxLoader = new KTX2Loader().setTranscoderPath("/basis/").detectSupport(renderer);
new GLTFExtensionsPlugin({ meshoptDecoder: MeshoptDecoder, dracoLoader, ktxLoader });
```

The decoder/transcoder wasm/js assets must be served from the app's `public/`
(or a CDN). Only needed if the pilot glTF is draco/ktx2-compressed.

## Validation done this wave

- `npx tsc --noEmit` (web type-check) - result reported in the agent return.
- **Not done (parallel-wave rule):** no `next dev`, no `next build`. The mount
  therefore is **type-correct and API-correct against `3d-tiles-renderer@0.4.28`
  but not visually confirmed to render**; visual confirmation is the explicit
  Wave 2 gate (`the sandbox renders it`).

## Risks / honesty notes

- Rendering is **assumed, not verified** (no dev server this wave). The pattern
  matches the library's own r3f component 1:1, which reduces but does not
  eliminate runtime risk.
- The stand-in tileset is a synthetic sample, not georeferenced to the Salish
  bbox; the lat/lng pick mapping is therefore documented, not exercised end to end.
- `raw.githubusercontent.com` is fine for a sandbox but is not a production
  origin; Wave 2 must point at the hosted orcast pilot.
- Implicit tiling needs `ImplicitTilingPlugin` (registered). The orcast pilot, if
  explicit, does not require it but the plugin is harmless to leave registered.
