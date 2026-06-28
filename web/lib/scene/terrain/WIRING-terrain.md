# WIRING-terrain.md, the Terrain Stylist module

WS-SCENIC, phase A, producer 1 (`Terrain Stylist`) of the orcast Salish scene. This
module owns only `web/lib/scene/terrain/` and never edits `SalishScene.tsx`,
`JourneyScene.tsx`, `web/lib/scene/tiles/`, or `web/app/components/scene/realism/`.
It reads the realism palette through the realism barrel and consumes the live
`TilesRenderer` through the public `3d-tiles-renderer` API only.

## Honesty statement

The biome tint is DERIVED from the rendered CUDEM height and slope. It is
interpretive color, not a vegetation survey and not draped land cover. The
geometry stays the real CUDEM tileset. The module only restyles tile materials, it
never changes tile geometry, transforms, or the tiles hook. Every restyled tile
mesh carries `mesh.userData.terrainTint = "derived tint, real CUDEM geometry"` so
any UI built from the scene graph can surface the label.

## Exports

```ts
import {
  applyTerrainStyle,
  type TerrainStyleOptions,
  type TerrainStyleHandle,
} from "@/lib/scene/terrain";
```

`web/lib/scene/terrain/index.ts` re-exports `applyTerrainStyle` and its option and
handle types.

## Function signature

```ts
function applyTerrainStyle(
  tiles: TilesRenderer,
  opts?: TerrainStyleOptions,
): TerrainStyleHandle;
```

`TilesRenderer` is imported from `3d-tiles-renderer` (no new dependency). The
caller passes the live instance returned by `useTilesLayer`. The function returns a
handle with a single `dispose()` method.

## What it does

1. Registers a `load-model` listener on `tiles`. On each newly streamed tile it
   traverses the loaded scene and, for every `THREE.Mesh`, clones the tile material,
   patches the clone with the biome tint by `material.onBeforeCompile`, sets
   `roughness` and optionally `normalScale`, and swaps the clone onto the mesh. The
   original material is stashed on `mesh.userData` so it can be restored.
2. Registers a `dispose-model` listener. When a tile unloads it restores the
   original material on each mesh and disposes the clone the module created.
3. Calls `forEachLoadedModel` once at mount so tiles already streamed in before the
   stylist mounted are restyled too.
4. `dispose()` removes both listeners, restores every styled mesh to its original
   material, and disposes every material the module created. It never disposes a
   material it did not create.

## How the tint maps elevation and slope

The tile group is fit so its bounding-sphere diameter equals `SCENE_WIDTH` (120)
with a uniform scale, so true relief is preserved with no vertical exaggeration and
sea level (0 m) maps to world Y == 0. In the fragment shader the module reads the
fragment world-space position and world-space normal (the world normal is
`mat3(modelMatrix) * objectNormal` normalized, valid because the fit scale is
uniform).

- Low flat ground reads forest-green near the realism `LAND_LOW` (#3f6b3a).
- A `smoothstep` over world Y from `midElevationM` to `highElevationM` (metres,
  converted to scene-Y with `worldUnitsPerMeter`) blends toward the drier grass-tan
  near the realism `LAND_HIGH` (#9aa886).
- A slope term `upDot = dot(worldNormal, up)` drives a `smoothstep` around
  `slopeThreshold` with `slopeSoftness`, so steep faces (low `upDot`) blend toward a
  rock gray.
- A narrow shoreline band just above Y == 0, of height `shoreBandM` metres and
  limited to flatter ground, blends toward a shoreline tint by `shoreStrength`.
- The whole biome color is blended over the tile's own resolved color by
  `tintStrength`, so geometry shading and any tile texture detail still read.

The shader injection points are `#include <common>`, `#include <beginnormal_vertex>`,
and `#include <begin_vertex>` in the vertex stage, and `#include <common>` and
`#include <color_fragment>` in the fragment stage, so the tint runs after the tile's
own map and vertex colors are resolved.

## The tile material hook used

The module hooks the public `3d-tiles-renderer` events `load-model` and
`dispose-model` on the passed `TilesRenderer`, and uses `forEachLoadedModel` to
restyle already-streamed tiles. This is the supported override pattern from the
NASA-AMMOS 3DTilesRenderer usage guide. The tiles hook in `web/lib/scene/tiles/`
also attaches its own `load-model` listener for shadow flags; both listeners coexist
because each only calls `addEventListener` on the same instance, so the tiles hook
stays a single owner and is never edited.

## Options

| Option | Type | Default | Meaning |
|---|---|---|---|
| `worldUnitsPerMeter` | `number` | `0.0024` | Scene units per metre of true elevation. Used to convert metre thresholds to scene-Y. |
| `lowColor` | `ColorRepresentation` | realism `LAND_LOW` (#3f6b3a) | Forest-green on low flat ground. |
| `midColor` | `ColorRepresentation` | realism `LAND_HIGH` (#9aa886) | Drier grass-tan at mid elevation. |
| `rockColor` | `ColorRepresentation` | `#6e6a63` | Rock gray on steep faces. |
| `shoreColor` | `ColorRepresentation` | `#9a8f73` | Shoreline band tint. |
| `midElevationM` | `number` | `120` | Metres above sea level where the low to mid blend begins. |
| `highElevationM` | `number` | `500` | Metres above sea level where the tint is fully mid/high. |
| `shoreBandM` | `number` | `35` | Height in metres above Y == 0 of the shoreline band. |
| `slopeThreshold` | `number` | `0.6` | `dot(worldNormal, up)` at/below which a face reads as steep rock (1 flat, 0 vertical). |
| `slopeSoftness` | `number` | `0.15` | Softness of the steep-rock transition. |
| `shoreStrength` | `number` | `0.7` | How strongly the shoreline band overrides the biome color, [0,1]. |
| `tintStrength` | `number` | `0.85` | Blend of the biome tint over the tile's own color, [0,1]. |
| `roughness` | `number` | `0.95` | `MeshStandardMaterial.roughness` on restyled materials. |
| `normalScale` | `number` | unset | When set and the tile material has a normal map, scales it via `material.normalScale`. |

## How the phase-B integrator mounts it

This is the phase-B SCENIC step that edits `SalishScene.tsx`, not part of phase A.
Inside `TwinScene`, once the live `tiles` instance exists:

```tsx
import { applyTerrainStyle } from "@/lib/scene/terrain";

useEffect(() => {
  if (!tiles) return;
  const handle = applyTerrainStyle(tiles, {
    // optional tuning, defaults are tuned for the SCENE_WIDTH = 120 fit
  });
  return () => handle.dispose();
}, [tiles]);
```

The same mount is repeated in `web/app/(sandbox)/journey/JourneyScene.tsx` so the
journey beats show the same vegetated land. Both mounts are owned by the single
phase-B SCENIC editor, not by this phase-A module.

## Validation

Phase A is type-check only, no dev server. `cd web && npx tsc --noEmit` exits 0. The
real rendered-frame check (low flat CUDEM ground reading as vegetated green, steep
faces as rock, a shoreline band at Y == 0) is deferred to the phase-B acceptance
gate and read by the Director.
