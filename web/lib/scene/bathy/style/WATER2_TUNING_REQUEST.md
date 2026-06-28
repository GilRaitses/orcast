# WATER2 tuning request, per-channel RGB absorption

From: WS-BATHY Water and Depth Stylist (`web/lib/scene/bathy/style/`).
To: the water2 owner (`web/lib/scene/water2/depthWater.ts`).
Date: 2026-06-27. Status: REQUEST. Not on the WS-BATHY critical path.

This is a request, not an edit. WS-BATHY owns only `web/lib/scene/bathy/style/`
and does not edit water2 internals. If the owner declines or defers, the WS-BATHY
seabed tint and the two-stop `Water2Options` tuning in `waterTuning.ts` ship as-is
and this becomes a follow-up.

## What works today

The water2 fragment shader drives both color and alpha from a single scalar
column thickness. Color is a two-stop lerp `mix(uColorShallow, uColorDeep,
colorT)` where `colorT = 1 - exp(-column / uDepthColorScale)`. Alpha is
`1 - exp(-column / uDepthAlphaScale)`. The depth pre-pass, the Beer-Lambert
attenuation, the foam band, the Fresnel term, and the sun glitter are correct and
stay as they are.

## What the request changes

Real water absorbs red fastest and blue slowest, so deep water shifts blue-green
toward navy and violet by physics. A two-stop lerp cannot reproduce that shift,
it only blends two fixed colors. The request is a per-channel RGB extinction so
the deep read follows physics rather than a chosen deep color.

Proposed shader change, owned by water2:

```glsl
// new uniform, inverse scene units per channel
uniform vec3 uAbsorption; // e.g. vec3(3.0, 1.6, 0.9), R fast .. B slow

// transmitted intrinsic water color, replacing the two-stop color lerp
vec3 transmittance = exp(-uAbsorption * column);
vec3 base = uColorShallow * transmittance + uColorDeep * (1.0 - transmittance);
```

`uColorShallow` stays the shallow tint. `uColorDeep` becomes the intrinsic deep
water color the transmittance fades toward. The single `uDepthColorScale` lever
can stay for backward compatibility, applied as an overall multiplier on
`uAbsorption`, or be retired in favor of the per-channel vector.

## Proposed starting coefficients

`web/lib/scene/bathy/style/waterTuning.ts` exports `PROPOSED_RGB_EXTINCTION`:

```ts
{ r: 3.0, g: 1.6, b: 0.9 } // inverse scene units of column thickness
```

Rationale, the deepest Haro Strait channel runs about 1.0 scene units below the
surface in the live tile frame. At `r = 3.0` the red channel reaches about 95
percent extinction over that column while blue at `b = 0.9` retains about 70
percent, which produces the deep navy and violet read. These are a starting
point for the owner to tune in the `/water` sandbox against the full-extent
tileset, read back through the `uDebug` thickness mode.

## Honesty note

This is physics over a MODELED seabed. The absorption upgrade changes how the
water looks, it asserts no measured depth. The seabed the water reads stays the
modeled CUDEM topobathy, labeled modeled, not measured.

## Acceptance for this request, if adopted

Type-check clean, then a real depth-read visual check in the `/water` sandbox and
in the live scene, normal and `uDebug` frames read and confirmed, shoals lighter
and bluer-green, channels darker and more violet, no regression in the foam line
at the waterline.
