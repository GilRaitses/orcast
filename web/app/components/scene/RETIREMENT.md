# RETIREMENT.md - removing the placeholder terrain path from SalishScene.tsx

Wave 2, agent `legacy-retirement`. This is a plan the **integrator** applies.
Agent `legacy-retirement` did **not** edit `SalishScene.tsx`, `sceneIntent.ts`,
or any other code file. The integrator is the sole editor of
`web/app/components/scene/SalishScene.tsx` and `web/lib/sceneIntent.ts`.

All line numbers below quote the **current** `SalishScene.tsx` (282 lines as
read at the start of Wave 2). Apply the removals in the order given so the line
numbers above each step stay valid as you work upward, or apply top-down and
re-read after each edit. The safest order is bottom-up by line number, so the
ordered checklist at the end is sequenced to minimize line drift.

---

## What is being retired and what replaces it

| Retired thing | Current lines | Replaced by |
|---|---|---|
| `salish_heightmap.json` fetch + `Heightmap` state + loading view | 154, 160-168, 187, 193-199 | `useTilesLayer` mount from `web/lib/scene/tiles` |
| `TerrainMesh` placeholder geometry + vertex-color build | 40-93, 220-224 | tile geometry from the served 3D Tiles tileset |
| `WaterPlane` component + its mount | 95-108, 225 | realism animated water at Y 0 from `web/app/components/scene/realism` |
| `depthColor` + `WATER_*` / `LAND_*` constants | 26-38 | already reproduced in `realism/palette.ts` (single palette source) |
| hard-coded light block | 217-219 | realism `RealismLayer` / `RealismRig` lights (see `WIRING-realism.md`) |

## What stays (do NOT remove)

- `HydrophoneBeacon` (lines 110-151) - keep the component. Its **placement**
  changes from `sampleDepth` against the heightmap to a tile-surface Y. See
  step 7.
- `FocusMarker` (lines 262-281) - keep the component, same placement change.
- `OrbitControls` (lines 250-257) - keep. The integrator sets `minDistance` /
  `maxDistance` from the `onFit` bounding sphere instead of the hard-coded
  20 / 400.
- The `onIntent` plumbing: `onIntentRef` (lines 157-158), the `cell` emit, and
  the `hydrophone` emit (lines 234-243). Keep all of it.
- The hydrophone fetch (lines 170-177) and `ORCASOUND_FALLBACK`. Keep.
- The `assetError` state and the `salish-scene-error` dispatch (lines 156,
  180-185, 189-191). Keep and re-wire to the tiles load-error (see Fallback
  toggle below).
- The `assetError` -> `"salish-scene-error"` to-Maps fallback in
  `SceneHost.tsx` (lines 52-70). Do NOT touch `SceneHost.tsx`; it already
  listens for the event and swaps to `MapHero`.

---

## Step 1. Remove the palette constants and `depthColor` (lines 26-38)

These now live in `realism/palette.ts` (`WATER_SHALLOW`, `WATER_DEEP`,
`LAND_LOW`, `LAND_HIGH`, `depthColor`, plus `oceanDepthColor`,
`landElevationColor`). Delete the in-file copies.

Remove:

```tsx
const WATER_SHALLOW = new THREE.Color("#2e6f9e");
const WATER_DEEP = new THREE.Color("#0a2540");
const LAND_LOW = new THREE.Color("#3f6b3a");
const LAND_HIGH = new THREE.Color("#9aa886");

function depthColor(depth: number, minDepth: number, maxDepth: number): THREE.Color {
  if (depth < 0) {
    const t = Math.min(1, depth / minDepth); // minDepth is negative; t in [0,1] for deep
    return WATER_SHALLOW.clone().lerp(WATER_DEEP, t);
  }
  const t = maxDepth > 0 ? Math.min(1, depth / maxDepth) : 0;
  return LAND_LOW.clone().lerp(LAND_HIGH, t);
}
```

If the integrator wants to color anything in `SalishScene.tsx` (for example a
substrate overlay), import from the palette instead of redefining:

```tsx
import { oceanDepthColor, landElevationColor } from "./realism";
```

Note: the served 3D Tiles already carry baked vertex color from the conversion
pipeline, so the live tiles do not need runtime coloring. Only import palette
helpers if you add a data overlay.

## Step 2. Remove `TerrainMesh` (lines 40-93)

The tiles supply geometry, so the whole placeholder mesh and its vertex-color
construction go away. Delete the entire `TerrainMesh` function (lines 40-93).
Its click handler (lines 81-86) is replaced by picking against `tiles.group`
using the `picking` module (`worldPointToLatLng`), wired by the integrator.

Remove the block beginning:

```tsx
function TerrainMesh({
  map,
  depth,
  onPick,
}: {
  ...
}) {
  ...
}
```

through its closing brace at line 93.

## Step 3. Remove `WaterPlane` (lines 95-108)

Superseded by the realism animated water surface, which sits at Y 0 (sea level,
elevation 0 m, per the reconciliation decision in `WAVE2_DISPATCH.md`). Delete
the entire `WaterPlane` function:

```tsx
function WaterPlane({ depth }: { depth: number }) {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
      <planeGeometry args={[SCENE_WIDTH * 1.6, depth * 1.6]} />
      <meshStandardMaterial
        color="#1b4a6b"
        transparent
        opacity={0.45}
        roughness={0.2}
        metalness={0.4}
      />
    </mesh>
  );
}
```

The realism water authored width and depth (`SCENE_WIDTH * 1.6`,
`depth * 1.6`) carry over into the `RealismLayer` / `RealismRig` water options
per `WIRING-realism.md`. The flat tint `#1b4a6b` is preserved in the palette as
`WATER_SURFACE_TINT`.

## Step 4. Remove the heightmap state and fetch (lines 154, 160-168)

Remove the state:

```tsx
const [map, setMap] = useState<Heightmap | null>(null);
```

Remove the fetch effect:

```tsx
useEffect(() => {
  fetch("/geo/salish_heightmap.json", { cache: "force-cache" })
    .then((r) => {
      if (!r.ok) throw new Error(`heightmap ${r.status}`);
      return r.json();
    })
    .then((m: Heightmap) => setMap(m))
    .catch(() => setAssetError(true));
}, []);
```

In its place the integrator mounts the tiles. The tiles hook owns its own
lifecycle and is constructed via `useTilesLayer` from `web/lib/scene/tiles`,
not via this fetch. The hook's load-error path replaces the `.catch(() =>
setAssetError(true))` (see Fallback toggle).

After/replacement shape the integrator wires (illustrative, integrator owns the
exact composition):

```tsx
const PILOT_TILESET_URL =
  "https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/pilot/tileset.json";

const tiles = useTilesLayer({
  url: PILOT_TILESET_URL,
  groupRotationX: -Math.PI / 2,
  fitScaleToWidth: SCENE_WIDTH,
  enableShadows: true,
  onFit: (sphere) => {
    // set camera framing + OrbitControls min/max distance from sphere.radius
  },
  onError: () => setAssetError(true),
});
```

## Step 5. Remove the `depth`-from-bounds memo and the loading view (lines 187, 189-199)

`depth` was derived from `map.bounds` via `sceneDepth`. With the heightmap gone,
remove:

```tsx
const depth = useMemo(() => (map ? sceneDepth(map.bounds) : 90), [map]);
```

The integrator still needs a Z extent for `projectToScene` / `unprojectFromScene`
when placing beacons and converting picks. Derive it from the tileset bounds at
runtime (the `onFit` sphere or the tileset geographic bounds), not from the
retired heightmap. Document the chosen bounds, as the dispatch requires.

Remove the `!map` loading view (lines 193-199):

```tsx
if (!map) {
  return (
    <div className="scene-loading">
      <p className="muted">Loading 3D Salish Sea…</p>
    </div>
  );
}
```

The lazy-load spinner in `SceneHost.tsx` (the `dynamic(...)` `loading`) already
covers the import wait, and the tiles stream in progressively, so a blocking
"Loading" gate is no longer needed. Keep the `assetError` early return (lines
189-191), now driven by the tiles load-error.

## Step 6. Replace the light block, `TerrainMesh` mount, and `WaterPlane` mount in the Canvas (lines 217-225)

Per `WIRING-realism.md` Option 1, remove the hard-coded lights:

```tsx
<ambientLight intensity={0.6} />
<directionalLight position={[60, 90, 40]} intensity={1.1} castShadow />
<hemisphereLight args={["#8fc7ff", "#0a2540", 0.4]} />
```

Remove the `TerrainMesh` mount:

```tsx
<TerrainMesh
  map={map}
  depth={depth}
  onPick={(lat, lng, depthM) => onIntentRef.current?.({ type: "cell", lat, lng, depth_m: depthM })}
/>
```

Remove the `WaterPlane` mount:

```tsx
<WaterPlane depth={depth} />
```

Add in their place the realism layer and the tiles group. Illustrative
(integrator owns exact wiring):

```tsx
<RealismLayer depth={depth} />
<primitive object={tiles.group} />
```

The `cell` intent that `TerrainMesh.onPick` used to emit now comes from picking
`tiles.group` via the `picking` module, so the `onIntentRef.current?.({ type:
"cell", ... })` call moves to the pick handler the integrator wires on the tiles
mesh.

## Step 7. Re-place beacons and the focus marker onto the tile surface (lines 201-208, 226-249, 262-281)

`beacons` and `FocusMarker` currently read `map.bounds` and call `sampleDepth`
for Y. With `map` removed both must derive position from the tile frame.

The `inBoundsNodes` filter (lines 201-208) used `map.bounds`. Replace the bounds
source with the runtime tileset bounds the integrator derived in step 5.

In the beacons map (lines 226-246), this pair changes:

```tsx
const [x, z] = projectToScene(node.latitude, node.longitude, map.bounds, depth);
const y = sampleDepth(map, node.latitude, node.longitude) * HEIGHT_SCALE;
```

to use the runtime bounds for XZ and a tile-surface Y (raycast `tiles.group`
downward at that XZ, or sample `science-substrate` `sampleSubstrate` for depth
and convert). Keep the `Math.max(y, 0)` floor so beacons never sink below sea
level. Keep the `HydrophoneBeacon` JSX and its `onSelect` hydrophone emit
unchanged.

In `FocusMarker` (lines 262-281) the same two lines change the same way. Keep
the component; change only its position source from `map` + `sampleDepth` to
runtime bounds + tile-surface Y. The `+ 4` hover offset stays.

## Step 8. Clean up imports (lines 7-19)

After the removals these imports are no longer referenced and must be dropped to
keep `npm run typecheck` clean:

- `sampleDepth` - removed with the heightmap path.
- `sceneDepth` - removed with the `depth`-from-bounds memo.
- `type Heightmap` - no `Heightmap` state remains.
- `HEIGHT_SCALE` - removed once beacon/focus Y comes from the tile surface; if
  the integrator keeps a vertical-exaggeration knob on the tiles group instead,
  remove it here regardless since the per-vertex height scaling is gone.

These imports stay:

- `getJSON` (hydrophone fetch), `projectToScene`, `unprojectFromScene` (still
  used for XZ placement and pick conversion), `ORCASOUND_FALLBACK`, `SCENE_WIDTH`,
  `type HydrophoneNode`, `type SceneIntent`.

Before:

```tsx
import { getJSON } from "@/lib/api";
import {
  HEIGHT_SCALE,
  ORCASOUND_FALLBACK,
  SCENE_WIDTH,
  projectToScene,
  sampleDepth,
  sceneDepth,
  unprojectFromScene,
  type Heightmap,
  type HydrophoneNode,
  type SceneIntent,
} from "@/lib/sceneIntent";
```

After:

```tsx
import { getJSON } from "@/lib/api";
import {
  ORCASOUND_FALLBACK,
  SCENE_WIDTH,
  projectToScene,
  unprojectFromScene,
  type HydrophoneNode,
  type SceneIntent,
} from "@/lib/sceneIntent";
```

Do NOT delete the unused exports from `web/lib/sceneIntent.ts` in this wave.
`sampleDepth`, `sceneDepth`, `HEIGHT_SCALE`, and the `Heightmap` type may still
be referenced by other modules and the metric migration is deferred to W5. Leave
`sceneIntent.ts` exports intact; only stop importing them here.

---

## Fallback toggle (do not show an empty canvas)

Today the only failure path is the heightmap fetch `.catch(() =>
setAssetError(true))`, which dispatches `salish-scene-error`, which `SceneHost`
catches and swaps to the Google Maps baseline. With the heightmap gone, the new
failure source is the tileset failing to load. Re-wire the same mechanism to the
tiles load-error so a bad tileset never leaves an empty canvas.

Add one module-level flag near the top of `SalishScene.tsx`:

```tsx
// When the tileset fails to load: true => fall back to Google Maps via
// SceneHost; false => show the minimal in-scene placeholder below.
const FALLBACK_TO_MAPS = true;
```

Keep the existing `assetError` state (line 156) and keep the existing dispatch
effect (lines 180-185) exactly as is:

```tsx
useEffect(() => {
  if (assetError) {
    const evt = new CustomEvent("salish-scene-error");
    window.dispatchEvent(evt);
  }
}, [assetError]);
```

Wire the tiles hook error to `setAssetError`. `useTilesLayer` exposes an
`errorTarget` / `onError` per the tiles dispatch; on a `TilesRenderer`
`load-error` (the root `tileset.json` 404s, CORS fails, or meshopt decode
fails), set the flag:

```tsx
const tiles = useTilesLayer({
  url: PILOT_TILESET_URL,
  // ...framing options...
  onError: () => {
    if (FALLBACK_TO_MAPS) setAssetError(true);
    else setTilesFailed(true);
  },
});
```

If the integrator prefers the in-scene placeholder over Maps, add a second
state and render a minimal stand-in inside the Canvas so the realism water and
lights still show and the canvas is never blank:

```tsx
const [tilesFailed, setTilesFailed] = useState(false);

// ...inside the Canvas, when FALLBACK_TO_MAPS is false:
{tilesFailed && (
  <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
    <planeGeometry args={[SCENE_WIDTH, SCENE_WIDTH]} />
    <meshStandardMaterial color={"#0a2540"} roughness={0.9} />
  </mesh>
)}
```

Behavior summary:

- `FALLBACK_TO_MAPS = true` (default): tileset load-error sets `assetError`, the
  existing effect dispatches `salish-scene-error`, `SceneHost` swaps to
  `MapHero`. This reuses the proven path and is the recommended default for the
  gate.
- `FALLBACK_TO_MAPS = false`: tileset load-error sets `tilesFailed`, the scene
  keeps realism water and lights and draws a flat dark sea-level plane so the
  canvas is never empty. No Maps swap.

Either way, the canvas is never left blank on a tileset failure.

---

## Ordered checklist for the integrator

Apply bottom-up by line number so earlier line references stay valid.

1. Re-place `FocusMarker` (lines 262-281): swap `map.bounds` + `sampleDepth` for
   runtime tileset bounds + tile-surface Y. Keep the component and `+ 4` offset.
2. In the Canvas body, re-place beacons (lines 226-246) and the focus mount
   (lines 247-249): runtime bounds for XZ, tile-surface Y, keep `Math.max(y, 0)`
   and the `onSelect` hydrophone emit.
3. Replace the light block + `TerrainMesh` mount + `WaterPlane` mount (lines
   217-225) with `RealismLayer` + the tiles group, and move the `cell` emit into
   the tiles pick handler.
4. Replace `inBoundsNodes` (lines 201-208) bounds source with runtime tileset
   bounds.
5. Remove the `!map` loading view (lines 193-199); keep the `assetError` early
   return (lines 189-191).
6. Remove the `depth`-from-bounds memo (line 187); derive Z extent from the
   tileset at runtime.
7. Add the `FALLBACK_TO_MAPS` flag and wire `useTilesLayer({ onError })` to
   `setAssetError` (or `setTilesFailed`). Keep the existing `salish-scene-error`
   dispatch effect (lines 180-185).
8. Remove the heightmap fetch effect (lines 160-168) and mount `useTilesLayer`.
9. Remove the `Heightmap` `map` state (line 154).
10. Remove the `WaterPlane` function (lines 95-108).
11. Remove the `TerrainMesh` function (lines 40-93).
12. Remove the `depthColor` function and the `WATER_*` / `LAND_*` constants
    (lines 26-38).
13. Clean up imports (lines 7-19) per step 8. Leave `sceneIntent.ts` exports
    intact.
14. Run `npm run typecheck` and resolve any remaining unused-symbol errors.

## Acceptance for this retirement (matches the W2 gate)

- No reference to `salish_heightmap.json`, `Heightmap` state, `TerrainMesh`,
  `WaterPlane`, the in-file `depthColor`, or the `WATER_*` / `LAND_*` constants
  remains in `SalishScene.tsx`.
- `HydrophoneBeacon`, `FocusMarker`, `OrbitControls`, the `onIntent` plumbing,
  and the `assetError` -> `salish-scene-error` to-Maps path in `SceneHost.tsx`
  all still work.
- A forced tileset load-error degrades to Maps (default) or the minimal
  placeholder, never an empty canvas.
- `npm run typecheck` is clean.
