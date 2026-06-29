# OCN-R3 finding. Read-only depth-clip seam for the double-diffusion plume

> Read-only research. OCN-R wave (measured-ocean-stratification). I edited no
> source. I propose no WFX edit. I staged nothing.
>
> Files read in full: `web/lib/scene/water2/depthWater.ts`,
> `web/lib/scene/water2/index.ts`, `web/lib/scene/wfx/realWfxEnv.ts`,
> `web/lib/scene/orca/materials/wfxEnv.ts`, `web/lib/scene/wfx/WIRING-slice-note.md`,
> `web/lib/scene/ocean/doubleDiffusion.ts`,
> `.cca/catalogue/O0/20260628_bside-acoustic-behavior-workbench/research/BSW-R09_ocean_process_layer.md`,
> `web/lib/scene/camera/director.ts`. I grepped
> `web/app/components/scene/SalishScene.tsx` for the mount points.
>
> Note on the dispatch path. The dispatch cited BSW-R09 under the `20260629`
> catalogue. The file actually lives under `20260628_bside-acoustic-behavior-workbench/research/`.
> I read it there. No content differs from the dispatch summary.

## 1. Task framing

The interpretive double-diffusion layer hangs a fixed vertical column of two
crossed additive planes. It must clip against the REAL water surface so no plume
renders above the surface and the column is depth-placed correctly. I define the
read-only seam by which the layer obtains the surface position, and I document
where that seam overlaps the ENV lane.

## 2. Two granularities of "clip against the surface", ranked

### Primary. Scalar surface-Y clip (cheap, no GPU coupling)

The layer needs one number, the world Y of the water surface, so the column top
maps to the surface and a shader top-clip discards or alpha-fades any fragment
above it. This number already exists read-only as the env handle field
`underwater.waterLevelY`, which the real producer sets from `SEA_LEVEL_Y`.

What already supports this:

- `createDoubleDiffusionLayer` already accepts `opts.surfaceY` and positions the
  group at `surfaceY - height/2`.

```48:60:web/lib/scene/ocean/doubleDiffusion.ts
  /** World Y of the surface (top of the column). Strata descend from here. */
  surfaceY?: number;
```

```205:206:web/lib/scene/ocean/doubleDiffusion.ts
  // Column hangs from the surface down by `height`.
  group.position.y = surfaceY - height / 2;
```

- The fragment shader already derives a normalized depth fraction from the plane
  V coordinate, so a top-clip is a one-line addition against the V that maps to
  `surfaceY`. The shader maps `depthFrac = 1.0 - vUv.y`, surface at `vUv.y == 1`.

```130:135:web/lib/scene/ocean/doubleDiffusion.ts
  void main() {
    float depthFrac = 1.0 - vUv.y;            // 0 surface, 1 deep
    vec4 strat = texture2D(uStrata, vec2(depthFrac, 0.5));
    float salinity = strat.r;                 // 0 fresh .. 1 salty
    float interface = strat.b;                // band sharpness at the halocline
```

I recommend this as the primary read-only seam. It needs NO WFX edit and NO
water2 edit. It consumes one existing read-only scalar and adds a top-clip inside
the layer's own shader. The ONLY external dependency is who owns publishing the
single live env handle, which is the ENV overlap in section 4.

### Secondary. Per-fragment depth-texture clip (precise, GPU-coupled)

The layer could read `Water2Handle.depthTarget.texture` read-only and clip the
plume per fragment behind the seabed and behind the surface, reconstructing the
seabed world position with the same inverse-view-projection math the water shader
uses. `depthTarget` is ALREADY exposed read-only on the handle, so OCN could
sample it WITHOUT a water2 edit.

```134:151:web/lib/scene/water2/depthWater.ts
export interface Water2Handle {
  /** The renderable water mesh; add it to the scene / r3f tree. */
  mesh: THREE.Mesh;
  /** The shader material (exposed for advanced tweaks / tuning). */
  material: THREE.ShaderMaterial;
  /** The opaque-scene render target the water samples (color + depth). */
  depthTarget: THREE.WebGLRenderTarget;
```

The water shader's own reconstruction shows the math OCN would mirror.

```328:336:web/lib/scene/water2/depthWater.ts
  // Column thickness (surface plane down to the seabed) from the depth buffer.
  float waterColumn(vec2 uv) {
    float sceneDepth = texture2D(uDepthTexture, uv).x;
    if (sceneDepth >= 0.9999) return 50.0; // open water / horizon: read as deep.
    vec4 ndc = vec4(uv * 2.0 - 1.0, sceneDepth * 2.0 - 1.0, 1.0);
    vec4 worldH = uInverseViewProjection * ndc;
    vec3 seabed = worldH.xyz / worldH.w;
    return uWaterLevel - seabed.y;
  }
```

I flag this as heavier and gate-worthy. It couples the layer to water2 internals,
the inverse-view-projection uniform and the camera matrices, and adds a texture
sample and reconstruction per fragment. The render-target also carries the water
mesh hidden, so its depth is the OPAQUE seabed, not the live wavy surface, which
means surface clipping via this path still leans on the scalar `waterLevelY`
plane. I recommend deferring this path until a dive POV exists and a perf gate
runs it.

### Ranking

| Rank | Seam | Edits WFX or water2 | GPU cost | Couples to water2 internals |
|---|---|---|---|---|
| 1 | Scalar `surfaceY` plus shader top-clip | none | ~0 | no |
| 2 | Per-fragment `depthTarget.texture` clip | none | adds sample plus reconstruction | yes |

## 3. What exists today vs what is missing

| Item | State | Location |
|---|---|---|
| `depthTarget` render target on the handle | EXISTS, read-only | `Water2Handle.depthTarget`, `depthWater.ts:140` |
| `depthTarget.texture` color attachment | EXISTS, read-only | `depthWater.ts:527` binds it as `uSceneColor` |
| `waterLevelY` scalar surface Y | EXISTS, read-only via env handle | `WfxEnvHandle.underwater.waterLevelY`, `wfxEnv.ts:37`, set in `realWfxEnv.ts:90` |
| `surfaceY` option on the layer | EXISTS | `doubleDiffusion.ts:50` |
| A surface-Y accessor ON `Water2Handle` itself | MISSING | no `getWaterLevelY` or `level` getter on the handle interface |
| A single live `WfxEnvHandle` published for shared consumption | MISSING | `OrcaRig` builds one, the slice bakes a second, ENV lane is consolidating |

The handle exposes `depthTarget` and `material` but no surface-Y getter, so the
scalar seam does not read the surface from `Water2Handle`. It reads the surface
from the env handle field `underwater.waterLevelY`, or, until the single env
handle is published, from an explicit `surfaceY` prop passed by `SalishScene`.

## 4. The exact read-only shape OCN consumes

OCN consumes a scalar and, only for the secondary path, a texture.

```ts
// Primary seam (recommended). The layer needs one number.
surfaceY: number; // scene units, the world Y of the water surface

// Secondary seam (deferred, gate-worthy). Read-only sample source.
depthTarget.texture: THREE.Texture; // already exposed on Water2Handle, read-only
```

OCN sets NO value. OCN mutates no WFX water uniform, no `Water2Handle` field,
`scene.environment`, `scene.fog`, or `scene.background`. The scalar feeds the
existing `surfaceY` layer option plus a shader top-clip. The texture, if ever
used, is sampled read-only with `texture2D`.

## 5. The ENV overlap, explicit

The ENV lane is consolidating the duplicate `makeRealWfxEnv` PMREM bake. Today
`SalishScene` bakes the env handle more than once. `OrcaRig` builds one as the
sole `scene.environment` writer, and `SliceRig` bakes a SECOND `makeRealWfxEnv`
only to light the reenactment pool, never assigning it to `scene.environment`.

```9:16:web/lib/scene/wfx/WIRING-slice-note.md
`SalishScene.tsx` `SliceRig` calls `makeRealWfxEnv` a SECOND time. This second
PMREM bake is used ONLY as the env map handed to `createOrcaPool`, so the
reenactment pool materials are lit by the same scene sky and the twin-unit
underwater optic. The slice never assigns this handle to `scene.environment`.
```

ENV will expose ORCA's single live `WfxEnvHandle`. OCN's scalar surface-Y read
should consume THAT single handle once ENV publishes it, reading
`handle.underwater.waterLevelY`, rather than baking or reading a second copy.
Reading a second copy would risk divergence if the surface Y ever moves off
`SEA_LEVEL_Y`.

Until ENV publishes the single handle, OCN takes `surfaceY` as an explicit prop
from `SalishScene`. That path is already wired. `SalishScene` mounts the rig with
the scene constant.

```174:174:web/app/components/scene/SalishScene.tsx
const SEA_LEVEL_Y = 0;
```

```1666:1666:web/app/components/scene/SalishScene.tsx
      {oceanOn && <OceanProcessRig surfaceY={SEA_LEVEL_Y} />}
```

The explicit-prop path is the new-param case. Adding a top-clip uniform fed from
this prop is a layer-internal edit OCN owns, but threading any NEW shared value
through `SalishScene` is the single-editor OCN-INT slot, and consuming the single
ENV handle instead of a second bake is the dependency on the ENV lane.

### Coordination return to O0

The scalar seam works today with the explicit `surfaceY` prop and needs no
cross-lane action. The clean form, OCN reading `underwater.waterLevelY` off the
single live `WfxEnvHandle`, depends on the ENV lane publishing that single handle
first. That handle does not exist yet. I return this dependency to O0 as the ENV
overlap. The depth seam OCN needs does exist read-only already, so this is a
coordination ordering item, not a WFX edit request.

## 6. Camera-dive caveat from BSW-R09

`director.ts` has NO dive or underwater mode. It enforces a hard no-dunk clamp
that only ever lifts the camera eye above the higher of the water plane and the
probed tile surface plus a clearance floor. The floor combines a metric clearance
and a wave-headroom minimum.

```46:53:web/lib/scene/camera/director.ts
// Hard no-dunk safety clamp. The camera eye may never sit closer to the surface
// than this. Two floors, whichever is higher: a metric clearance (metres above
// the higher of the water plane Y=0 and the probed tile surface) and a minimum
// world-unit headroom that always clears the displaced water crests (water2's
// wave amplitude is ~0.18-0.32 scene units), so a low fly-by can never plunge
// below a wave even where the metric clearance maps to a tiny world distance.
const MIN_ALT_ABOVE_SURFACE_METERS = 40;
const MIN_WAVE_HEADROOM_UNITS = 0.5;
```

```146:157:web/lib/scene/camera/director.ts
  function enforceAltitudeClamp(): void {
    const cam = handle.camera;
    if (!cam) return;
    let surfaceY = 0; // water surface plane
    if (handle.getSurfaceY) {
      const s = handle.getSurfaceY(cam.position.x, cam.position.z);
      if (typeof s === "number" && Number.isFinite(s) && s > surfaceY) surfaceY = s;
    }
    const metricClear = MIN_ALT_ABOVE_SURFACE_METERS * worldUnitsPerMeter();
    const minY = surfaceY + Math.max(metricClear, MIN_WAVE_HEADROOM_UNITS);
    if (cam.position.y < minY) cam.position.y = minY;
  }
```

Because the camera stays above the surface, a top-clip changes nothing visible
today. The plume column below the surface is what the above-water camera sees,
and the surface plane already occludes the part of the column at and above it
once placement is correct. A top-clip matters visually only once an underwater
POV exists and a viewer can look up at the surface from below. BSW-R09 records
the same gate, that the dive POV must relax the clamp first or the layer stays
dormant.

The layer ships VISIBLE in the current mount, since `OceanProcessRig` calls
`setEnabled(true)` and is gated by the `oceanOn` toggle, default off. So the
column is visible only when the operator enables the ocean toggle, and the
surface top-clip enhancement is dormant in effect until a dive POV lands. I
recommend implementing the scalar top-clip now since it is free and correct, and
deferring the per-fragment depth-texture clip until the dive POV and a perf gate
exist.
