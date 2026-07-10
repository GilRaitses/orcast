# HUNT-BATHY findings

Discovery member BATHY. Read-only audit of bathymetry tileset mounting for the `orca-strike` sandbox route.

## Tileset URLs and bounds

### Two CloudFront tileset URLs

| Variant | Exact URL | Hook / scene |
|---------|-----------|--------------|
| **Full** (production) | `https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full/tileset.json` | `useTilesLayer` in `JourneyScene.tsx` (`56:57`), `WaterSandboxScene.tsx` (`33:34`), `SalishScene.tsx` (`163:164`) |
| **Pilot** (Wave 1 gate) | `https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/pilot/tileset.json` | `useTilesRenderer` in `TilesSandboxScene.tsx` (`25:26`, active at `30`) |

The `tiles3d` sandbox does **not** use `useTilesLayer`. It uses the lower-level `useTilesRenderer` hook with the **pilot** URL (`TilesSandboxScene.tsx` `44`, `111`). The existing `/orca` sandbox (`OrcaSandboxScene.tsx`) mounts **no tileset at all**; it uses a flat `planeGeometry` water surface at Y=0 (`206:218`).

**Correction for waveset wording:** the build wave should follow **journey / water / SalishScene**, not `tiles3d` or `/orca`, for `useTilesLayer` + `fitScaleToWidth` conventions.

### TILESET_BOUNDS (identical across full-tileset scenes)

`JourneyScene.tsx` `62:67`, `WaterSandboxScene.tsx` `36:41`, `SalishScene.tsx` `172:177`:

```ts
const TILESET_BOUNDS: HeightmapBounds = {
  min_lat: 48.4,
  max_lat: 48.7,
  min_lng: -123.25,
  max_lng: -122.75,
};
```

Journey and Water bounds are **identical** to each other and to SalishScene. `SCENE_DEPTH` is derived from these via `sceneDepth(TILESET_BOUNDS)` (`JourneyScene.tsx` `69`, `WaterSandboxScene.tsx` `43`, `SalishScene.tsx` `182`). `SCENE_WIDTH` is `120` (`web/lib/sceneIntent.ts` `57`).

### Journey vs Water `useTilesLayer` call comparison

| Argument | JourneyScene (`239:256`) | WaterSandboxScene (`426:432`) |
|----------|--------------------------|-------------------------------|
| `url` | `FULL_TILESET_URL` | `FULL_TILESET_URL` (same) |
| `groupRotationX` | `-Math.PI / 2` | `-Math.PI / 2` (same) |
| `fitScaleToWidth` | `SCENE_WIDTH` (120) | `SCENE_WIDTH` (120) (same) |
| `errorTarget` | `16` | `16` (same) |
| `enableShadows` | `false` | `false` (same) |
| `onFit` | **set** (see below) | **not set** |

Calls are identical except Journey supplies an `onFit` callback; Water omits it.

## useTilesLayer fit options (recommended call)

### Hook API (confirmed from source)

`web/lib/scene/tiles/useTilesLayer.ts` accepts:

- `url`, `errorTarget` (default `12`), `maxDepth` (default `Infinity`), `enabled` (default `true`), `enableShadows` (default `true`)
- `groupRotationX` (default `-Math.PI / 2`, `59`, `73`)
- `fitScaleToWidth` (default `null`, `74`)
- `onFit?: (sphere: THREE.Sphere) => void` (`56`, `75`)

### `fitScaleToWidth` semantics

From `useTilesLayer.ts` `38:49` and the per-frame fit block `191:212`:

1. On first root bounding-sphere availability, compute `scale = target / (sphere.radius * 2)` so the bounding-sphere **diameter** equals `target` scene units (`193:195`).
2. Apply uniform scale to `tiles.group` (`195`).
3. Recenter **horizontally only**: `group.position.set(-rotated.x, 0, -rotated.z)` (`211`). Vertical position stays at `0` so NAVD88 0 m maps to scene Y=0 (sea level for the water plane) (`199:205`).
4. Invoke `onFit` once with the **world-space** bounding sphere after fit (`217:219`).

With `fitScaleToWidth: SCENE_WIDTH` (120), the fitted sphere radius is deterministically `60` scene units (`SalishScene.tsx` `1653:1654`).

### Recommended call for `orca-strike`

Mirror journey/water/Salish:

```ts
const FULL_TILESET_URL =
  "https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full/tileset.json";

const TILESET_BOUNDS: HeightmapBounds = {
  min_lat: 48.4,
  max_lat: 48.7,
  min_lng: -123.25,
  max_lng: -122.75,
};

const tiles = useTilesLayer({
  url: FULL_TILESET_URL,
  groupRotationX: -Math.PI / 2,
  fitScaleToWidth: SCENE_WIDTH, // 120
  errorTarget: 16,
  enableShadows: false,
  onFit: (sphere) => {
    // Required for worldUnitsPerMeter + camera near/far (see below).
    setFitRadius(sphere.radius);
    // worldUnitsPerMeter = sphere.radius / geoRadiusMeters(TILESET_BOUNDS);
  },
});

// Mount:
{tiles && <primitive object={tiles.group} />}
```

### `onFit` downstream usage

| Scene | `onFit` body | Purpose |
|-------|--------------|---------|
| `JourneyScene.tsx` `245:255` | `setFitRadius(sphere.radius)`; `handle.fitRadius = sphere.radius`; `handle.worldUnitsPerMeter = sphere.radius / geoRadiusMeters(TILESET_BOUNDS)`; camera `near`/`far` from `sphere.radius` | Gates choreography start (`277:278`); feeds Camera Director altitude scaling |
| `SalishScene.tsx` `1624` | `setFitRadius(sphere.radius)` | Drives `scenicWorldUnitsPerMeter` (`1608:1609`), camera `minDistance`/`maxDistance` (`1655:1658`), and all rigs that need live fit scale (OrcaRig, BathyRig, TerrainStylistRig, etc.) |
| `WaterSandboxScene.tsx` | *(none)* | Fit still runs inside the hook; no consumer reads the sphere |

For orca-strike dead-reckoning, **`onFit` is required** to derive `worldUnitsPerMeter` the same way Journey and Salish do.

## getSurfaceY seabed probe pattern

Both implementations are a self-contained downward `THREE.Raycaster` against `tiles.group` with **no external dependency** beyond three.js. Reusable as an inline ~10-line helper.

### JourneyScene (`makeSurfaceProbe`)

`JourneyScene.tsx` `118:134`:

```ts
function makeSurfaceProbe(group: THREE.Object3D | null) {
  const ray = new THREE.Raycaster();
  const origin = new THREE.Vector3();
  const down = new THREE.Vector3(0, -1, 0);
  return (x: number, z: number): number | null => {
    if (!group) return null;
    origin.set(x, 1e5, z);
    ray.set(origin, down);
    ray.near = 0;
    ray.far = 2e5;
    const hits = ray.intersectObject(group, true);
    return hits.length ? hits[0].point.y : null;
  };
}
```

Wired per frame: `handle.getSurfaceY = makeSurfaceProbe(tiles?.group ?? null)` (`266`).

### SalishScene (`surfaceYAt`)

`SalishScene.tsx` `254:265`:

```ts
function surfaceYAt(group: THREE.Object3D, x: number, z: number): number | null {
  const ray = new THREE.Raycaster(
    new THREE.Vector3(x, 1e5, z),
    new THREE.Vector3(0, -1, 0),
    0,
    2e5,
  );
  const hits = ray.intersectObject(group, true);
  return hits.length ? hits[0].point.y : null;
}
```

Used for beacon placement (`506`), focus marker (`536`), and Camera Director no-dunk clamp via `handle.getSurfaceY` (`653`).

### orca-strike usage notes

- **Seabed collision floor:** probe `(orcaX, orcaZ)` each frame; clamp orca Y so `orcaY >= surfaceY + clearance`. Returns `null` when tiles have not streamed at that XZ yet; handle with a safe default or skip clamp until hits exist.
- **Boat placement at water surface:** place boats at **Y = 0** (sea level / `SEA_LEVEL_Y`), **not** at the raycast-probed seabed. Salish maps NAVD88 0 m to scene Y=0 via the tiles fit (`SalishScene.tsx` `184:190`, `useTilesLayer.ts` `199:205`).
- **BVH acceleration (optional):** Salish installs `accelerateTilesPicking(tiles)` for faster raycasts (`1630:1633`). Worth mirroring if the pilot does frequent seabed probes.

## worldUnitsPerMeter derivation

### `geoRadiusMeters`

Identical in `JourneyScene.tsx` `112:116` and `SalishScene.tsx` `272:276`:

```ts
function geoRadiusMeters(b: HeightmapBounds): number {
  const latSpanM = (b.max_lat - b.min_lat) * 111_000;
  const lngSpanM = (b.max_lng - b.min_lng) * 73_600;
  return 0.5 * Math.hypot(latSpanM, lngSpanM);
}
```

This is half the geographic diagonal of the served bbox in metres (~27.8 km for the San Juan extent).

### `worldUnitsPerMeter` assignment (in `onFit`)

`JourneyScene.tsx` `249`:

```ts
handle.worldUnitsPerMeter = sphere.radius / geoRadiusMeters(TILESET_BOUNDS);
```

`SalishScene.tsx` `668` (same formula, applied when `fitRadius` is set from `onFit`):

```ts
handle.worldUnitsPerMeter = fitRadius / geoRadiusMeters(TILESET_BOUNDS);
```

With `fitScaleToWidth: SCENE_WIDTH`, `sphere.radius` is `60`, so `worldUnitsPerMeter ≈ 60 / geoRadiusMeters(TILESET_BOUNDS) ≈ 0.00216` scene units per metre.

### Dead-reckoning conversion

To convert real swim speed (m/s) to scene units per frame:

```ts
const sceneDelta = speedMps * worldUnitsPerMeter * deltaSeconds;
```

Gate on `worldUnitsPerMeter != null` (fit complete) before integrating, same as `OrcaRig` (`SalishScene.tsx` `952`, `984`) and `OrcaSandboxScene`'s hardcoded `worldUnitsPerMeter: 1` (`124`) which is sandbox-only and **not** geographically scaled.

## Go/no-go recommendation

### **GO** — mount the real **full** tileset via `useTilesLayer` on first attempt

**Rationale:**

1. **Proven path.** Journey, Water, and SalishScene all mount `FULL_TILESET_URL` with `fitScaleToWidth: SCENE_WIDTH`, `groupRotationX: -Math.PI / 2`, `errorTarget: 16` (`JourneyScene.tsx` `239:244`, `WaterSandboxScene.tsx` `426:431`, `SalishScene.tsx` `1617:1623`). This is production-validated, not experimental.
2. **Fit semantics are documented and deterministic.** `useTilesLayer.ts` `38:49`, `191:212` guarantee sea level at Y=0 and a 120-unit-wide frame. No manual bbox math needed.
3. **Seabed probe is trivial to inline.** `makeSurfaceProbe` / `surfaceYAt` are ~10 lines, no imports beyond three.js (`JourneyScene.tsx` `121:134`, `SalishScene.tsx` `256:265`).
4. **`worldUnitsPerMeter` derivation is one line in `onFit`.** Copy from Journey (`249`) or Salish (`668`).
5. **CORS is already solved.** Pilot tileset comment notes CloudFront OAC with CORS (`TilesSandboxScene.tsx` `22:24`). Full tileset is served from the same distribution and loads in live Salish.

### Risks (justify documented flat-plane fallback only if these block the time budget)

| Risk | Evidence | Mitigation |
|------|----------|------------|
| **Load time / tile count** | Full tileset is 85 tiles, 4 LoD levels, ~75.75 MiB (`SalishScene.tsx` `160:162`, `228:230`). First paint streams coarse L0..L2 when `maxDepth: 2` (Salish resting caps). | Start with `errorTarget: 16` like journey/water; optionally cap `maxDepth` initially. Seabed raycast returns `null` until tiles stream at the orca's XZ. |
| **Network / availability** | Salish listens for `load-error` and falls back (`1638:1643`, `1983:1986`). | Wire `tiles.addEventListener("load-error", ...)` or show `OrcaSandboxScene`-style flat plane (`206:218`) as **documented** fallback per `waveset.md` `143:148`. |
| **Raycast misses outside footprint** | `surfaceYAt` returns `null` when ray misses (`264`). | Collision floor should tolerate `null` (no clamp) or use substrate depth as secondary bound. |
| **Wrong tileset variant** | Pilot URL is a different, smaller bake (`TilesSandboxScene.tsx` `22:26`). | Use **full** URL only; do not copy `tiles3d` pilot URL. |

### Flat-plane fallback reference

If tileset mount fails within the time budget, `OrcaSandboxScene.tsx` `206:218` provides the accepted fallback: a `200×200` `planeGeometry` at Y=0 with `meshPhysicalMaterial`, plus `worldUnitsPerMeter: 1` (`124`). Document explicitly; never substitute silently (`waveset.md` `146:148`).

**Bottom line:** Low-risk for HUNT-W2 to mount the full tileset with the journey/water call signature on the first attempt. Reserve the flat-plane fallback for load failures or acceptance-time budget overruns, not as the default plan.
