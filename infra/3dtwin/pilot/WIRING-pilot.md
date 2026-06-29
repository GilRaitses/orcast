# WIRING-pilot.md — how to mount the pilot tileset (for agent E sandbox + Wave 2 integrator)

## URL

```
https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/pilot/tileset.json
```

CORS is enabled (CloudFront managed CORS-with-preflight policy), so a browser on any origin
can `fetch` `tileset.json` and the relative `pilot.glb` it references. If the CloudFront
distribution still shows `Status: InProgress`, wait until `Deployed` (a few minutes).

## What it is

- OGC **3D Tiles 1.1**, one root tile, content `pilot.glb`.
- `pilot.glb` uses **`EXT_meshopt_compression`** + **`KHR_mesh_quantization`**.
- A **local engineering frame in meters** (NOT ECEF / not geographic). No root `transform`.
- glTF content is **Y-up**: `Y = elevation (m, true scale)`, `X = easting offset`,
  `Z = −(northing offset)`, both offsets relative to UTM-10N centroid `500026.174 E,
  5377480.675 N`. Horizontal extent ≈ 37.0 km × 33.4 km, elevation span −377.3…+717.5 m.

## Required loader setup (critical)

`3d-tiles-renderer` loads glb via three.js `GLTFLoader`. `KHR_mesh_quantization` is handled
natively, but **`EXT_meshopt_compression` needs the meshopt decoder registered** or the glb
will fail to load:

```ts
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
// after constructing the TilesRenderer:
tiles.manager.addHandler(/\.gltf$|\.glb$/, /* GLTFLoader configured with: */);
// or, on the GLTFLoader used by the tiles renderer:
gltfLoader.setMeshoptDecoder(MeshoptDecoder);
```

With `3d-tiles-renderer`'s `GLTFExtensionsPlugin` / loader plugin, pass the meshopt decoder to
the underlying `GLTFLoader`. Verify the glb actually loads (no "EXT_meshopt_compression" loader
error in the console) before judging orientation.

## Orientation (Y-up scene)

The tileset has no transform and a `box` bounding volume. 3D Tiles defines tile space as Z-up;
the glb content is Y-up and 3D Tiles applies the built-in glTF Y-up→Z-up rotation. In a Y-up
three.js scene the net result is usually that the terrain needs a **−90° rotation about X** so
elevation points along the scene's +Y:

```ts
tiles.group.rotation.x = -Math.PI / 2;   // map tiles Z-up -> three.js Y-up
scene.add(tiles.group);
```

Agent E should confirm visually (terrain ridges up, seafloor below the 0 m plane) and record
the exact rotation that looks correct; that value is the authoritative mount transform for
Wave 2. The model is centered on the origin, so no large-coordinate float-precision shift is
needed for the pilot.

## Minimal r3f mount sketch

```tsx
const tiles = new TilesRenderer('https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/pilot/tileset.json');
tiles.setCamera(camera);
tiles.setResolutionFromRenderer(camera, gl);
tiles.group.rotation.x = -Math.PI / 2;
scene.add(tiles.group);
// in the frame loop:
useFrame(() => { tiles.update(); });
// dispose:
() => { tiles.dispose(); scene.remove(tiles.group); };
```

## Scene-scale note for Wave 2 (`SalishScene.tsx`)

The current scene uses `SCENE_WIDTH = 120` and `HEIGHT_SCALE = 0.04` (`web/lib/sceneIntent.ts`)
for the placeholder heightfield. This pilot is in **real meters** (~37 km wide). The Wave-2
integrator must either scale the tiles group to the existing scene units (≈ `120 / 37000`) or
migrate the scene to meters. Do not bake exaggeration into the tileset — keep it true-scale and
scale at mount time.
