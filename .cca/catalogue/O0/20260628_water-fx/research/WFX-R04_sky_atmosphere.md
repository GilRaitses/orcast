# WFX-R04 sky + atmosphere (procedural sky, aerial perspective, horizon blend)

Role: WFX-R04, read-only research, Wave 1. Reports to the WFX sub-orchestrator, then O0.
Repo state: branch main, charter pins origin/main 915e4cc77923de93ed5f7e9a75feab9eb2e12896.
Honesty: every sky and fog effect here is modeled atmosphere, not measured sky or measured visibility.
Topic: diagnose why the sky reads white and the horizon reads stark, and recommend a procedural
sky bound to the sun plus aerial perspective that softens the horizon. This doc only writes
itself. It changes no code.

## 1. Scope and current state (file-cited)

The live scene already mounts a Preetham sky, a decorative DEM horizon ring, linear distance fog,
and a sun-warmed fog retune. The fault is not a missing sky. It is exposure, fog distance, and a
sky and fog that do not share a horizon color. Each claim below is cited.

### 1a. The sky dome is the three Preetham `Sky` addon, driven by the sun

`web/lib/scene/decor/sky.ts` wraps the vendored three addon and adds no npm dependency:

```21:23:web/lib/scene/decor/sky.ts
import * as THREE from "three";
import { Sky } from "three/addons/objects/Sky.js";
import { fogColorForSky, skyColor } from "@/app/components/scene/realism";
```

It defaults to Preetham and sets a mild marine haze, then points the Preetham `sunPosition`
uniform at the sun direction:

```95:104:web/lib/scene/decor/sky.ts
  const u = sky.material.uniforms;
  u.turbidity.value = opts.turbidity ?? DEFAULTS.turbidity;
  u.rayleigh.value = opts.rayleigh ?? DEFAULTS.rayleigh;
  u.mieCoefficient.value = opts.mieCoefficient ?? DEFAULTS.mieCoefficient;
  u.mieDirectionalG.value = opts.mieDirectionalG ?? DEFAULTS.mieDirectionalG;

  const setSun = (direction: THREE.Vector3) => {
    (u.sunPosition.value as THREE.Vector3).copy(direction).normalize();
  };
  setSun(opts.sunDirection ?? new THREE.Vector3(0, 1, 0));
```

`SalishScene.tsx` mounts that dome in `SkyRig` and feeds it the same pinned sun the lights and
water use, so the sky already agrees with `makeSun`:

```632:639:web/app/components/scene/SalishScene.tsx
function SkyRig() {
  const sun = useScenicSun();
  const handle = useMemo(() => makeSkyDome({ sunDirection: sun.direction }), [sun]);
  useEffect(() => {
    handle.setSun(sun.direction);
    return () => handle.dispose();
  }, [handle, sun]);
  return <primitive object={handle.object3D} />;
}
```

So the sky model and the sun are already coupled. The white look is not a coupling bug. It is a
tonemapping and exposure interaction, described in 1d.

### 1b. The horizon ring is an opaque DEM silhouette that relies on fog to dissolve

`web/lib/scene/decor/horizonRing.ts` builds a real-DEM ring from 28 km to 120 km, colored by
elevation, with a skirt dropped below sea level. Its material is opaque MeshStandard and it counts
on `scene.fog` to fade it:

```226:233:web/lib/scene/decor/horizonRing.ts
  const material = new THREE.MeshStandardMaterial({
    vertexColors: true,
    roughness: opts.roughness ?? DEFAULTS.roughness,
    metalness: 0,
    // Share the scene fog so the ring dissolves into the horizon haze.
    fog: true,
    side: THREE.FrontSide,
  });
```

The module header states the intent plainly: the mesh shares `scene.fog` so it dissolves into the
haze the way the served tiles do (`web/lib/scene/decor/horizonRing.ts` lines 22 to 23). The ring
is correct. The problem is that the fog never reaches most of it, shown in 1e.

### 1c. The sun model is already physical and high in the sky at the pinned time

`web/app/components/scene/realism/sun.ts` computes a real NOAA solar position. The scene pins one
instant:

```146:146:web/app/components/scene/SalishScene.tsx
const SCENE_TIME = new Date("2026-06-27T20:00:00Z");
```

I evaluated `makeSun` for that instant at lat 48.5, lng -123. Solar elevation is 64.61 degrees, a
high summer-noon sun. This matters because the Preetham radiance is brightest at high sun, so the
pinned time maximizes the wash described next, and it also kills the warm sun-side horizon the
operator expects, because `fogTuning.ts` only warms the haze when the sun is below about 12
degrees (`web/lib/scene/decor/fogTuning.ts` lines 60 to 64), which never fires at 64.61 degrees.

### 1d. Why the sky reads white: ACES at exposure 1.0 over Preetham radiance

The renderer is the react-three-fiber default. The Canvas sets no `gl` tonemapping or exposure
override:

```1007:1011:web/app/components/scene/SalishScene.tsx
      <Canvas
        camera={{ position: [0, 28, 30], fov: 45, near: 1, far: 800 }}
        style={{ width: "100%", height: "100%", background: "linear-gradient(#0b1f33,#08263d)" }}
        onCreated={({ gl }) => gl.setClearColor("#08263d")}
      >
```

react-three-fiber 8.18 defaults the renderer to ACES filmic tonemapping unless the Canvas is set
`flat`. I confirmed this in the installed package: `events-776716bd.esm.js` creates the renderer
with `toneMapping: flat ? THREE.NoToneMapping : THREE.ACESFilmicToneMapping`. The Canvas here is
not `flat`, so ACES is active, and `toneMappingExposure` is left at the default 1.0.

The vendored `three/examples/jsm/objects/Sky.js` (three 0.169) ends its fragment shader with
`#include <tonemapping_fragment>` and `#include <colorspace_fragment>` (Sky.js lines 212 to 213),
so the renderer ACES curve and exposure apply on top of the shader's own brightening curve
`pow(texColor, 1.0 / (1.2 + 1.2 * vSunfade))` (Sky.js line 208). The canonical three sky example
runs this shader at `renderer.toneMappingExposure = 0.5`. The live scene runs it at 1.0, roughly
twice the reference exposure, with a 64.61 degree sun that already pushes the Preetham output high.
ACES then compresses those high values toward desaturated near-white across most of the dome. That
is the white sky. It is an exposure and tonemapping problem far more than a sky-model problem. The
renderer exposure and the ACES decision are WFX-R05's surface, so I flag the coupling and defer the
global lever to R05, but the sky cannot read correctly while exposure stays at 1.0.

The gradient fallback dome would not read white. Its colors are pale blue-grey
(`topColor #9fc4e0`, `bottomColor #9fb8cc`, `web/lib/scene/decor/sky.ts` lines 122 to 125), which
confirms the white-out is specific to the Preetham path under ACES at exposure 1.0.

### 1e. Why the horizon reads stark: fog does not reach the rendered scene

The scene is small. `SCENE_WIDTH` is 120 (`web/lib/sceneIntent.ts` line 57), the tileset fits to
radius 60, and the camera sits at distance about 41 with a zoom-out cap near 120. The horizon ring
at 28 km to 120 km maps through the fit scale of about 0.00242 units per metre to roughly 68 to 290
scene units from the origin.

The realism fog is linear with near 120 and far 520:

```22:25:web/app/components/scene/realism/atmosphere.ts
export function makeFog(opts: FogOptions = {}): THREE.Fog {
  const color = new THREE.Color(opts.color ?? "#9fb8cc");
  return new THREE.Fog(color, opts.near ?? 120, opts.far ?? 520);
}
```

With near 120, fog contributes nothing until 120 units. The served terrain and the inner half of
the horizon ring (about 68 to 120 units) get zero fog. The far ring edge at about 290 units sits at
linear fog factor (290 - 120) / (520 - 120), about 0.42, so even the farthest land only half
dissolves. The result is a hard, opaque DEM silhouette standing against a bright sky. That is the
stark, abrasive horizon. The ring material is doing exactly what it promised. The fog distances are
tuned for a much larger world than the 120-unit scene actually renders.

Three more seams stack on top.

- The Preetham sky does not read `scene.fog`. Sky.js has no fog chunk, so where the ring's top edge
  meets the dome there is a hard material boundary between half-fogged land and unfogged sky, with
  no aerial perspective bridging them.
- The fog color is derived independently of the actual Preetham horizon color. `fogColorForSky`
  pulls the sky color toward a fixed sea blue: `sky.clone().lerp(new THREE.Color("#1b4a6b"), 0.35)`
  (`web/app/components/scene/realism/atmosphere.ts` lines 53 to 55). It is not sampled from the
  Preetham horizon, so terrain fading into fog does not match the sky immediately behind it.
- The water meets the sky with a flat reflected color and no distance fade. The water2 shader is
  hand-written GLSL, so `scene.fog` does not auto-apply, and at the far horizon it reads as solid
  deep water tinted by a single flat sky color: `color = mix(color, uSkyColor, fres *
  uFresnelStrength)` (`web/lib/scene/water2/depthWater.ts` line 285), with open-water fragments
  forced to a deep column (`web/lib/scene/water2/depthWater.ts` lines 232 to 235). There is no soft
  water-to-sky blend at the horizon line.

`fogTuning.ts` is the existing, non-realism lever that can already retune this fog in place. It
sets the haze color from the sky and warms it toward the sun only at low sun, and `tuneFog` already
handles both `THREE.Fog` and `THREE.FogExp2` (`web/lib/scene/decor/fogTuning.ts` lines 72 to 79).
It does not currently change near or far in `FogTuneRig`, which only passes elevation and azimuth
(`web/app/components/scene/SalishScene.tsx` lines 676 to 679), so the too-far fog distances survive.

## 2. Technique survey

### 2a. Preetham analytic daylight (the model already in the tree)

A Practical Analytic Model for Daylight, Preetham, Shirley, Smits, SIGGRAPH 1999. Closed-form sky
luminance and chromaticity from sun position and a single turbidity parameter. Cheap, one shader,
no datasets. Weak at low sun and overstates horizon brightness, which is part of the milky horizon
under high exposure. Paper: https://www.cs.utah.edu/~shirley/papers/sunsky/sunsky.pdf . three
addon source: https://github.com/mrdoob/three.js/blob/master/examples/jsm/objects/Sky.js . Live
example: https://threejs.org/examples/#webgl_shaders_sky .

### 2b. Hosek-Wilkie analytic sky-dome radiance (higher fidelity)

An Analytic Model for Full Spectral Sky-Dome Radiance, Hosek and Wilkie, SIGGRAPH 2012, with a 2013
solar-radiance extension. More accurate horizon and twilight than Preetham, ground-albedo aware.
Cost is a coefficient dataset (radiance lookup tables) that must ship with the build and a port to
GLSL, because three has no bundled Hosek-Wilkie object. Project and data:
https://cgg.mff.cuni.cz/projects/SkylightModelling/ .

### 2c. three `Sky` object (the concrete integration of 2a)

`three/addons/objects/Sky.js`. One BackSide box at the far plane, one draw call, four atmosphere
uniforms plus `sunPosition`. Already vendored with `three` 0.169 and already wrapped by
`decor/sky.ts`. Zero new dependency. Docs context: https://threejs.org/docs/#examples/en/objects/Sky
(manual entry) and the example above.

### 2d. Aerial perspective and distance fog

Aerial perspective is the desaturation and tinting of distant objects toward the sky color as the
air column between viewer and object scatters and absorbs light. The cheap, real-time stand-in is
distance fog whose color equals the sky behind the object. three offers two fog models.

- `THREE.Fog`, linear between near and far. Easy to reason about, but the look depends entirely on
  matching near and far to the scene scale, which is the present failure.
- `THREE.FogExp2`, exponential by density, `factor = 1 - exp(-(density * dist)^2)`. This is closer
  to physical extinction and to the Beer-Lambert law the water already uses, needs only one density
  number rather than a near and a far tuned to scene size, and fades gracefully at any distance.
  Docs: https://threejs.org/docs/#api/en/scenes/FogExp2 and https://threejs.org/docs/#api/en/scenes/Fog .

For a full physically based treatment that couples sky and aerial perspective in one framework, see
Hillaire, A Scalable and Production Ready Sky and Atmosphere Rendering Technique, EGSR 2020,
https://sebh.github.io/publications/egsr2020.pdf , and the classic O'Neil GPU Gems 2 chapter,
https://developer.nvidia.com/gpugems/gpugems2/part-ii-shading-lighting-and-shadows/chapter-16-accurate-atmospheric-scattering
. Both are heavier than this scene needs. They are listed as the upgrade ceiling, not the
recommendation.

### 2e. Horizon and water-to-sky blend

The standard fix for a hard water-to-sky seam is to fade the far water toward the same horizon color
the sky and fog use, either by giving the water shader a fog term that reads the shared fog color or
by reflecting the real sky environment so the grazing-angle Fresnel returns the sky that is actually
there. The reflection route is WFX-R03's surface and the environment map is WFX-R05's. This doc
specifies the shared horizon color they should both consume.

## 3. Recommendation

Keep the model. Fix the exposure, the fog distance, and the shared horizon color. Add a soft edge
where land, water, and sky meet. No new dependency is required.

### R1. Keep three `Sky` Preetham, do not add a sky library

The Preetham `Sky` is already vendored, already wrapped, and already sun-coupled. It is the right
model for this scene. Hosek-Wilkie is higher fidelity but costs a shipped coefficient dataset and a
GLSL port, which is not justified for a stylized turbid-Salish look. Recommendation: stay on
Preetham. Three-only fallback: the existing `gradient` mode dome in `decor/sky.ts` for low-end
devices, already implemented. Cost: zero, the model is in place. New dependency: none.

### R2. Bring the sky into exposure range (coordinate with WFX-R05)

The white sky is an exposure problem. The renderer-level lever, setting
`gl.toneMappingExposure` to about 0.4 to 0.6 on the Canvas, or deciding the ACES policy, belongs to
WFX-R05 (lighting and tonemap). I recommend R05 own the global exposure and I flag that the sky
needs it near 0.5 to match the reference. If R05 wants the sky tuned without touching global
exposure, the sky-local fallback is to lower the dome's `rayleigh` and `turbidity` and to set the
Sky material `toneMapped = false` so ACES does not double-process it, then hand-balance the dome
brightness against the rest of the scene. The global exposure route is cleaner and is preferred.
Cost: a single renderer property, no per-frame cost. New dependency: none.

### R3. Make the fog do aerial perspective at this scene scale

Replace the linear near 120, far 520 fog with a `THREE.FogExp2` density tuned to the 120-unit world,
estimated density 0.004 to 0.008, so distant terrain and the horizon ring fade smoothly across the
rendered depth instead of staying sharp until 120 units. `fogTuning.ts` already supports `FogExp2`
in `tuneFog`, so the retune path exists. The actual swap of `scene.fog` happens in `SalishScene.tsx`
where the fog object is owned, which is the convergence file and must serialize per the charter
lock. Three-only fallback if a fog-mode swap is unwanted: keep `THREE.Fog` but pull near to about 30
to 60 and far to about 250 to 350 so the same 120-unit scene actually fogs. Cost: fog is a
per-fragment term inside existing passes, no new pass, no measurable frame cost. New dependency:
none.

### R4. Share one horizon color between sky, fog, and water

The fog color and the water's reflected sky color must equal the Preetham sky color at the horizon
direction, so terrain dissolving into fog and water grazing into sky both match the dome behind
them. Best route: WFX-R05 builds a PMREM environment from this same Preetham sky, and the horizon
color is sampled from it so all three consumers agree by construction. Three-only fallback without a
PMREM: retune `fogColorForSky` (or set the fog color through `fogTuning.tunedFogColor`) to the
measured Preetham horizon tint at the pinned sun, and pass the same color into water2's `uSkyColor`,
which is already a public option (`web/lib/scene/water2/depthWater.ts` lines 49 to 50). Cost:
color derivation only, negligible. New dependency: none.

### R5. Drive the horizon ring, do not replace it

The DEM ring is real data and worth keeping. It should be driven by the corrected aerial-perspective
fog from R3, which already fades it once the fog reaches it, plus a soft alpha feather at the ring's
top edge so the silhouette does not cut a hard line against the sky. The ring stays in
`web/lib/scene/decor/`. The feather is a small material change inside the ring builder, owned by the
decor owner, not the convergence file. Recommendation: drive, not replace. Cost: the feather is a
shader or vertex-alpha tweak with no new pass. New dependency: none.

### R6. Give the water a horizon fade (hand off to water2 owner and WFX-R03)

The water2 shader needs a distance term that fades the far surface toward the shared horizon color
from R4, removing the hard water-to-sky seam. Because water2 is hand-written GLSL, `scene.fog` does
not auto-apply, so this is an explicit in-shader fog or horizon-blend term, not a material flag. I
specify the shared horizon color and the seam to remove. The shader edit belongs to the water2
owner, and the reflection-versus-fog decision overlaps WFX-R03. Cost: one extra term in an existing
shader, negligible. New dependency: none.

### Recommended stack, in order

three Preetham `Sky`, sun-coupled, already mounted. Renderer exposure near 0.5 from WFX-R05.
`FogExp2` aerial perspective tuned to the 120-unit scene. One shared horizon color from a PMREM env
(WFX-R05) consumed by fog and by water2's `uSkyColor`. A soft top-edge feather on the horizon ring.
A horizon fade term in the water2 shader (water2 owner and WFX-R03). Every item is three-only with a
stated fallback and adds no dependency.

## 4. Frame-budget impact

Budget is 60fps desktop and 30fps laptop, and the water2 depth pre-pass already costs one full scene
render every frame (`web/app/components/scene/SalishScene.tsx` lines 318 to 323), so it dominates.
Against that baseline:

- Sky dome: already present. One BackSide box drawn at the far plane, one draw call, a full-screen
  fragment fill of the analytic shader. Setting `sunPosition` is a uniform write on sun change, not
  per frame. Estimated cost on a mid desktop GPU at 1080p is a fraction of a millisecond and it is
  already being paid today. No new pass.
- Exposure change (R2): a renderer property. Zero frame cost.
- Fog, linear or FogExp2 (R3): a per-fragment term folded into passes that already run. No new pass,
  no measurable cost.
- Shared horizon color (R4): a color computed on sun change. Negligible. The PMREM that produces it
  is WFX-R05's cost, and PMREM regeneration runs only when the sun moves, not per frame.
- Ring feather (R5) and water horizon fade (R6): added shader terms inside existing draws. No new
  pass.

Net: the sky-and-atmosphere fix adds no render pass and no measurable per-frame cost beyond the sky
fill already in the scene. The only real new GPU work in the wider stack is WFX-R05's PMREM, which
is amortized to sun changes. All numbers here are estimated from draw-call and pass accounting, not
measured, because Wave 1 is read-only and runs no dev server. WFX-R13 should confirm with a profiler.

## 5. Collision and sequencing

- Sky-env module home is `web/lib/scene/sky/`, owned by the twin W3 sky-env agent. The PMREM env
  (WFX-R05) and any new sky helpers should land there, not in `decor/`. WFX-R04 only researches.
- The horizon ring stays in `web/lib/scene/decor/horizonRing.ts`. The R5 top-edge feather is a decor
  owner change.
- The fog mode swap, the fog near and far, and the renderer exposure all touch
  `web/app/components/scene/SalishScene.tsx`, the convergence file. Per the charter lock, any later
  build or integration that edits `SalishScene.tsx` or `globals.css` serializes through O0 against
  W-CAM, W-LABELS, W3, W4, and the LGC lane. Research touches none of these.
- WFX-R05 (lighting-tonemap) owns renderer exposure, ACES policy, and the PMREM env built from this
  sky. R04's white-sky fix depends on R05's exposure decision. Sequence R05's exposure before or
  with the sky landing.
- WFX-R03 (reflections) samples this sky for the water's grazing reflection. The shared horizon
  color from R4 is the contract R03 should consume.
- The water2 horizon fade (R6) is the water2 owner's shader edit, overlapping WFX-R01 (surface BRDF)
  and WFX-R03 (reflections). Coordinate ownership through O0 so the sky-reflection term is authored
  once.
- `fogTuning.ts` and `atmosphere/transition.ts` already support both fog modes, so a swap to
  `FogExp2` keeps the existing retune and roll-in tweens working (`rollInFog` handles a `FogExp2`
  density target, `web/lib/scene/atmosphere/transition.ts` lines 177 to 180).

## 6. Open questions for O0

- Exposure ownership. R04's white-sky fix needs renderer exposure near 0.5, which is WFX-R05's
  surface. Confirm R05 owns the global `toneMappingExposure` and the ACES policy, or direct R04's
  build to use the sky-local `toneMapped = false` fallback instead.
- Pinned sun. `SCENE_TIME` is 2026-06-27T20:00:00Z, a 64.61 degree summer-noon sun, which maximizes
  the white-out and gives no warm sun-side horizon, while the operator asked for light from the sun.
  Confirm whether to keep noon or pin a lower sun for a warmer marine horizon. This decision changes
  the target look that R04, R03, and R05 all tune toward.
- Fog mode. Switching `scene.fog` from `THREE.Fog` to `THREE.FogExp2` affects every fogged material
  and the existing transition tweens. Confirm the swap is allowed, or keep linear fog with corrected
  near and far.
- Shared horizon color source. Should the horizon color be sampled from WFX-R05's PMREM env, the
  robust route, or hand-tuned to match the Preetham horizon as a three-only fallback. This sets the
  dependency between R04, R05, and R03.
- Convergence-file scheduling. The exposure, fog, and any sky-env wiring land in `SalishScene.tsx`.
  Confirm the serialization slot against W-CAM, W-LABELS, W3, W4, and LGC for the later gated build
  and integrate waves.
