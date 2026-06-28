# WIRING-bathy-style

Owner: WS-BATHY Water and Depth Stylist (producer A3). Scope:
`web/lib/scene/bathy/style/` only. Reads the public surface of `substrate/` and
`water2/`. Edits no water2 or substrate internals and no `SalishScene.tsx`. No
new dependency, `three` only.

## What this is

The styling surface for the submerged modeled seabed. It produces two things the
phase-B editor mounts.

1. A submerged-seabed depth tint, the cmocean `deep` perceptually-uniform ramp
   mapped over the scene depth extent, built on top of `buildSubstrateOverlay`
   and returned as an apply/dispose handle.
2. The proposed `Water2Options` tuning set for the depth-driven water, so shoals
   read light and translucent and channels read dark and opaque.

It also carries the request to the water2 owner for a per-channel RGB absorption
upgrade, in `WATER2_TUNING_REQUEST.md`.

MODELED, NOT MEASURED. The tint styles the modeled CUDEM topobathy that the tiles
already render. The water is physics and atmosphere over that modeled seabed.
Foam, Fresnel, and glitter are rendering, not soundings. Every produced object
carries the label `modeled, not measured` on `userData.label` and in `name`.

## Palette choice

cmocean `deep`, a sequential, perceptually-uniform, colorblind-safe colormap
built for bathymetry, light at the shallows darkening through teal and blue to a
dark blue and purple at depth. NOT jet or rainbow, which adds false gradients and
local-maxima bias and is not colorblind-safe. Source, Thyng et al. 2016,
Oceanography, and cmocean at https://matplotlib.org/cmocean/ . The ramp is
sampled at nine perceptually-spaced stops in `deepRamp.ts`.

## Exported API

```ts
import {
  // ramp
  DEEP_RAMP_STOPS,
  DEEP_RAMP_SHALLOW,
  DEEP_RAMP_DEEP,
  DEEP_RAMP_SHALLOW_HEX,
  DEEP_RAMP_DEEP_HEX,
  LAND_TINT_HEX,
  BATHY_TINT_LABEL,
  sampleDeepRamp,
  type RampStop,
  // seabed tint
  bathyOverlayOptions,
  buildBathyTint,
  type BathyTintOptions,
  type BathyTintHandle,
  // water tuning
  bathyWater2Options,
  PROPOSED_RGB_EXTINCTION,
  WATER_TUNED_SHALLOW,
  WATER_TUNED_DEEP,
  WATER_TUNED_FOAM,
  WATER_TUNED_SKY,
  type BathyWaterTuningOverrides,
} from "@/lib/scene/bathy/style";
```

### `sampleDeepRamp(t: number): [r, g, b]`

The cmocean `deep` ramp at `t` in [0,1], clamped. `t=0` is the shallow endpoint,
`t=1` the deep endpoint. Display-sRGB in [0,1]. Convert with
`THREE.Color.setRGB(r, g, b, THREE.SRGBColorSpace)` before writing to a buffer.

### `buildBathyTint(field, opts?): BathyTintHandle`

Builds the submerged-seabed tint over the modeled substrate field. Reuses
`buildSubstrateOverlay` for positions, projector seam, material, and base honesty
tags, then overwrites the per-vertex colors with the full perceptual ramp so the
green and teal midtones are preserved rather than collapsed to a linear two-stop
gray midtone.

Color mapping, `depth_m` negative below sea level and positive on land.

- submerged, `depth_m < 0`, the `deep` ramp over `[0, |minDepthM|]`, so 0 m maps
  to the shallow endpoint and the deepest seabed maps to the deep endpoint.
- above water, `depth_m > 0`, a fade from the shallow endpoint to the muted land
  tint over `[0, maxDepthM]`, set dressing for the optional point layer.

`BathyTintOptions`, `project?`, `pointSize?`, `opacity?`, `sizeAttenuation?`,
`minDepthM?`, `maxDepthM?`. Pass the WS-BATHY field projector from producer A2 as
`project` so the tint aligns with the rendered tile frame. The depth extent
defaults to the field's own `minDepthM` and `maxDepthM`.

`BathyTintHandle`, `object`, `apply(parent)`, `dispose()`. Pure until `apply`.

```ts
const tint = buildBathyTint(field, { project, opacity: 0.85 });
tint.apply(tilesGroup);
// on unmount
tint.dispose();
```

The returned object carries `userData.modeledNotMeasured = true`,
`userData.label = "modeled, not measured"`, `userData.bathyTint = true`, and
`userData.ramp = "cmocean deep (perceptually uniform)"`.

### `bathyWater2Options(overrides?): Water2Options`

The proposed water tuning the editor merges into its `makeWater2` construction.
Returns tuned `colorShallow`, `colorDeep`, `colorFoam`, `skyColor`,
`depthColorScale`, `depthAlphaScale`, `foamDepth`, `maxOpacity`,
`fresnelStrength`, `amplitude`, `speed`. The editor passes its own plane size,
level, and sun direction through `overrides`, so this set never overrides the
live frame.

```ts
const handle = makeWater2({
  width: SCENE_WIDTH * 1.6,
  depth: SCENE_DEPTH * 1.6,
  level: 0,
  ...bathyWater2Options({ sunDirection: sun.direction }),
});
```

## Relief blend

The depth tint is not a flat fill. The live scene's sun from the RealismRig
shades the tile mesh beneath these points, and the tint reads as the translucent
depth wash filling the lows over that shaded relief, the standard honest seafloor
treatment, Patterson, Mountains Unseen. No second light is added here.

## Seam discipline

- Reads `buildSubstrateOverlay`, `SUBSTRATE_LABEL`, and the substrate field
  types from the substrate public surface. Reads the `Water2Options` type from
  the water2 public surface. Edits neither internal.
- The per-channel RGB absorption upgrade is a request to the water2 owner, see
  `WATER2_TUNING_REQUEST.md`. It is not on the WS-BATHY critical path. If the
  owner defers, the two-stop tuning ships and the upgrade is a follow-up.
- Mounts nothing. The SalishScene phase-B editor owns the mount, after WS-INTENT
  and WS-SCENIC release the file per the convergence calendar.

## Validation

`cd web && npx tsc --noEmit` exits 0. The ramp endpoint and label fixture is
`bathyTint.fixture.ts`, type-checked by the same gate and runnable with a TS
runner. The real depth-read visual check, water2 `uDebug` thickness in normal and
debug frames, is deferred to the Director at phase-B acceptance, since styling
needs the live render.
