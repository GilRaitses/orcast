# WIRING-substrate

Owner: `science-substrate` (Wave 2). Scope: `web/lib/scene/substrate/` plus the
one copied JSON asset. Does not edit `SalishScene.tsx`, `sceneIntent.ts`, or
`web/package.json`. No new dependency. `three` only.

## What this is

A live, sampleable view of agent F's modeled CUDEM depth field. The field is the
NOAA NCEI CUDEM 1/9 arc-second topobathy surface, rasterized to a regular
lat/lng grid. It is the same geometry that feeds the render tiles.

MODELED, NOT MEASURED. `depth_m` is NEGATIVE below sea level and POSITIVE on
land, identical to the Python `BathymetryAdapter`
(`src/aws_backend/sources/bathymetry.py`). Every exported object and any UI
string built from it carries the label `modeled, not measured` (exported as
`SUBSTRATE_LABEL`).

## Asset decision: fetch, not import

The field is copied verbatim to:

```
web/public/geo/sample_san_juan_bathymetry_cudem.json
```

served at runtime as `/geo/sample_san_juan_bathymetry_cudem.json`. Reasons:

- 288 KB of point data stays out of the JS bundle.
- The asset can be swapped (for example, when agent B's reprojected surface
  lands) without a web rebuild.
- It matches the existing pattern for `web/public/geo/salish_heightmap.json`.

The source of truth remains `infra/3dtwin/science/sample_san_juan_bathymetry_cudem.json`.
If that is regenerated, recopy it into `web/public/geo/`.

## Exported API

```ts
import {
  loadSubstrate,
  sampleSubstrate,
  buildSubstrateOverlay,
  SUBSTRATE_URL,
  SUBSTRATE_LABEL,
  type SubstrateField,
  type SubstratePoint,
  type SubstrateBounds,
  type SubstrateOverlayOptions,
} from "@/lib/scene/substrate";
```

### `loadSubstrate(url?: string): Promise<SubstrateField>`

Fetches and parses the field. Defaults to `SUBSTRATE_URL`. Computes
`minDepthM` / `maxDepthM` once. Rejects if the asset is missing or has no usable
points. Call this once and cache the result.

```ts
const field = await loadSubstrate();
```

`SubstrateField`:

```ts
interface SubstrateField {
  source: string;
  dataset: string;
  bounds: { min_lat; max_lat; min_lng; max_lng };
  resolution_deg: number;
  provenance: string;
  modeledNotMeasured: true;
  points: { lat: number; lng: number; depth_m: number }[];
  minDepthM: number;
  maxDepthM: number;
}
```

### `sampleSubstrate(field, lat, lng): number`

Nearest-neighbour depth in metres. Faithful mirror of
`BathymetryAdapter.depth_at`: nearest grid point by equirectangular distance
with longitude scaled by `cos(lat)`. Sign convention preserved (negative below
sea level). Returns `NaN` when the field is empty or the query is non-finite, so
a real 0 m sea-level reading is distinguishable from no data.

Use this on a pick to fill `SceneIntent.depth_m`:

```ts
const depth = sampleSubstrate(field, lat, lng);
emit({ type: "cell", lat, lng, depth_m: Number.isFinite(depth) ? depth : undefined });
```

### `buildSubstrateOverlay(field, opts?): THREE.Object3D`

Optional, toggleable data layer as a depth-tinted `THREE.Points` cloud. It owns
no per-frame state, so the integrator can `scene.add` and `scene.remove` it for
a toggle. Dispose `geometry` and `material` when retiring it.

The returned object is tagged for honesty labeling:

```ts
obj.name                          // "substrate-overlay (modeled, not measured)"
obj.userData.modeledNotMeasured   // true
obj.userData.label                // "modeled, not measured"
obj.userData.minDepthM / maxDepthM
```

Placement: by default the overlay uses the legacy `sceneIntent` frame
(`projectToScene` for X/Z, `depth_m * HEIGHT_SCALE` for Y, Y up). In the W2 tile
frame the integrator scales the tiles group to `SCENE_WIDTH` and rotates it
`rotation.x = -Math.PI/2`, so the default layout will not line up on its own.
Pass a `project` callback that maps a field point to the runtime tile frame so
the overlay aligns with the rendered terrain:

```ts
const overlay = buildSubstrateOverlay(field, {
  project: (lat, lng, depthM) => {
    // return scene-space [x, y, z] in the same frame as tiles.group
    return [/* x */, /* y */, /* z */];
  },
  pointSize: 0.6,
  opacity: 0.85,
});
scene.add(overlay);
```

`SubstrateOverlayOptions`: `project?`, `heightScale?`, `pointSize?`, `opacity?`,
`sizeAttenuation?`, `colorDeep?`, `colorShore?`, `colorHigh?`. The depth ramp
runs `colorDeep` at the most negative depth, through `colorShore` at sea level
when 0 m is in range, to `colorHigh` at the most positive depth.

## Validation

`cd web && npm run typecheck` passes (exit 0).
