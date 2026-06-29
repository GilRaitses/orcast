# WFX-R03 reflections

Role WFX-R03, read-only research, Wave 1, WATER-FX lane. Topic reflections. The
question is how to replace the flat single-color sky reflection that makes the
horizon stark, ranked by visual fidelity, by millisecond cost on a 60fps desktop
and 30fps laptop budget, and by feasibility on `three` with no new dependency.

Repo state read against the charter pin `915e4cc77923de93ed5f7e9a75feab9eb2e12896`.
All perf numbers below are estimated, not measured. I did not run the scene. The
estimates are derived from the render-pass structure I read in the code and from
the cited `three` documentation and examples.

## 1. Scope and current state, file-cited

The surface "reflection" today is a single flat color mixed in by a Fresnel term.

- `web/lib/scene/water2/depthWater.ts` line 113 defines `DEFAULT_SKY =
  new THREE.Color("#9fc4e0")`, one marine-haze color.
- Fragment shader line 203 declares `uniform vec3 uSkyColor`.
- Fragment shader lines 272 to 285 compute Fresnel and mix the surface color
  toward that one flat color. The operative lines are
  `float fres = pow(1.0 - max(dot(n, viewDir), 0.0), 5.0);` then
  `color = mix(color, uSkyColor, fres * uFresnelStrength);`. A grazing-angle
  surface, which is everything near the horizon, lerps to a single constant
  color. There is no sky gradient, no horizon brightening, no real environment.
  This is the stated root cause of the stark horizon.
- The open-water and horizon fragments take the deep branch. Lines 232 to 235
  set `column = 50.0` where no opaque geometry sits behind the fragment, so far
  water reads as a solid deep tint plus the same flat Fresnel color. The result
  at the waterline is a hard band between deep water and the dome.
- `web/app/components/scene/SalishScene.tsx` line 303 feeds that uniform from
  `skyColor(sun.elevationDeg)`, a single color from
  `web/app/components/scene/realism/atmosphere.ts` lines 34 to 47. So even when
  the sun moves the surface still reflects one flat color, not a sky image.

A real procedural sky already exists in the scene but the water does not sample
it.

- `web/lib/scene/decor/sky.ts` wraps the core `three` Preetham `Sky` addon from
  `three/addons/objects/Sky.js`, driven by the pinned sun. SalishScene mounts it
  through `SkyRig` at lines 632 to 640.
- A grep of `web/` for `Reflector`, `PMREM`, `CubeCamera`,
  `WebGLCubeRenderTarget`, `envMap`, and `.environment` returns no scene match.
  The renderer has no `scene.environment`, no reflector, and no cube probe. The
  rich sky the dome already renders never reaches the water shader.

The dependency baseline is `three` `^0.169.0` from `web/package.json` line 31.
Reflector, SSRPass, CubeCamera, WebGLCubeRenderTarget, and PMREMGenerator are all
shipped in that version, so none of the options below adds an npm dependency. The
only real cost is render passes against the frame budget.

Existing per-frame render cost, which every option is measured against. The
water rig already runs a depth pre-pass. `depthWater.ts` lines 375 to 383
`renderDepthPrepass` calls `renderer.render(scene, camera)` with the water mesh
hidden, and SalishScene line 321 runs it every frame before the main render. So
the opaque scene is rendered twice per frame today, once for the depth pre-pass
and once for the visible frame. The depth pre-pass is the one full extra scene
render the charter calls out. Any reflection technique is judged by how many more
full scene renders it adds on top of those two.

## 2. Technique survey with URLs

### Planar reflection, mirror camera plus render target

A mirror camera is reflected across the water plane, the scene is rendered from
it into a texture, and the surface samples that texture projected to screen. In
`three` this is the `Reflector` addon.

- Reflector docs, https://threejs.org/docs/pages/Reflector.html
- Mirror example, https://threejs.org/examples/#webgl_mirror

Fidelity is the highest of the three for a flat surface because it reflects the
actual scene, including the horizon ring land silhouettes and any boats or
beacons, with correct perspective. The cost is explicit. Reflector renders the
entire scene a second time from the mirrored camera, confirmed by the three
forum and docs. For this scene that is one more full scene render per frame, so
the water region would do three full scene renders per frame, the depth
pre-pass, the reflection, and the main pass. That is a 50 percent increase over
today's two-render cost. The reflection target can be shrunk below the drawing
buffer to claw cost back, and complex objects can be excluded by layers, but the
floor is still a full extra geometry pass.

### Screen-space reflection, SSR

SSR ray-marches the existing color and depth buffers in screen space to find
reflected pixels. In `three` this is `SSRPass` with `ReflectorForSSRPass`, run
through an `EffectComposer`.

- SSRPass example, https://threejs.org/examples/#webgl_postprocessing_ssr
- ReflectorForSSRPass docs, https://threejs.org/docs/pages/ReflectorForSSRPass.html

SSR adds no full scene render, but it has two disqualifying problems for this
exact fault. First it can only reflect what is already on screen. The stark
horizon is caused by the sky and the far horizon, which sit at or beyond the top
of the frame and are not in the color buffer for a grazing water ray, so SSR
falls back to a flat color or a cubemap anyway and does not fix the horizon by
itself. Second the scene has no `EffectComposer` today, it renders straight
through react-three-fiber, so adopting SSR means standing up a full postprocess
pipeline plus a normal buffer, which is a large change that collides with
WFX-R05 tonemapping ownership. SSR also needs careful thickness and step tuning
to avoid streaking. It is the wrong tool for a horizon problem.

### Environment cube probe, CubeCamera plus WebGLCubeRenderTarget

A `CubeCamera` renders the surroundings into the six faces of a cube render
target once, and the surface samples that cube by its reflected ray.

- CubeCamera docs, https://threejs.org/docs/#api/en/cameras/CubeCamera
- WebGLCubeRenderTarget docs, https://threejs.org/docs/#api/en/renderers/WebGLCubeRenderTarget

Fidelity for a sky reflection is good because the cube captures the full Preetham
dome in every direction, which is exactly what the horizon needs. The raw cube
has no roughness mips, so reflections are mirror-sharp and read wrong for a rough
sea surface unless prefiltered, which is what PMREM adds below. Cost is a one-
time six-face render of the sky when the sky changes, then a per-frame cube
sample that is effectively free. Because the sun is pinned, see section 4, the
six-face render is paid once at load.

### PMREM environment from the procedural sky

PMREMGenerator turns a cube or a scene into a Prefiltered Mipmapped Radiance
Environment Map, a CubeUV texture with roughness-indexed blur levels.
`fromScene` renders a scene, here just the sky, into that map.

- PMREMGenerator docs, https://threejs.org/docs/pages/PMREMGenerator.html
- The ocean example shows the exact pattern, sky into `pmremGenerator.fromScene`,
  assigned to `scene.environment`, rebuilt only when the sun moves,
  https://github.com/mrdoob/three.js/blob/master/examples/webgl_shaders_ocean.html

This is the cube probe plus the roughness prefilter the sea surface wants, and it
is the standard `three` way to drive water reflections from a procedural sky. The
water shader samples the PMREM by its reflected ray instead of a flat color. Cost
is the one-time `fromScene` build plus a per-frame env sample that replaces the
existing flat mix at no measurable extra cost.

## 3. Recommendation with cost and three-only fallback

Recommended default. Build a PMREM environment from the procedural sky that
WFX-R04 owns, and sample it in the `depthWater.ts` Fresnel term in place of the
flat `uSkyColor`. Concretely the line
`color = mix(color, uSkyColor, fres * uFresnelStrength);` becomes a mix toward
`textureCube` or `textureCubeUV` of the PMREM sampled by `reflect(-viewDir, n)`,
with the existing Fresnel weight. This removes the stark horizon at the source
because grazing fragments then reflect the real bright horizon band of the sky
rather than one constant color, and it costs no extra full scene render.

Cost, estimated. The PMREM build with `fromScene` at the default 256 texture
renders only the single-draw sky dome to six faces and prefilters it. Estimated
2 to 6 ms one-time on a desktop GPU and roughly 10 to 25 ms one-time on a weak
laptop, paid once at load and again only on a sun retarget, not per frame. The
per-frame addition in the water shader is one prefiltered env lookup replacing
one flat mix, estimated under 0.1 ms at the water's screen coverage and within
noise of the current shader. Memory is one 256 by 256 CubeUV render target, on
the order of a few hundred kilobytes. Net per-frame full scene renders stay at
two, the depth pre-pass and the main pass. This is the cheapest option that
actually removes the stark horizon.

Reserved quality preset. Keep planar `Reflector` as an opt-in high preset for
machines with budget headroom, because it is the only option that reflects the
horizon-ring land and scene objects, not just the sky. Cost is the explicit
third full scene render per frame from section 2, gated by the device-tier and
budget call WFX-R13 owns. Do not make it the default.

Rejected for this fault. SSR, for the two reasons in section 2, it cannot reflect
the off-screen horizon and it forces an EffectComposer pipeline the scene does
not have.

Three-only fallback, and note the entire recommendation is already three-only
with zero new dependency. If the PMREM build proves too heavy on the lowest
device tier, the fallback is to replace the single flat `uSkyColor` with a cheap
analytic two-color or three-color sky gradient evaluated in the fragment shader
from the reflected ray's Y component, mixing a horizon-haze color into a zenith
color. That is between the current flat color and the PMREM in fidelity, removes
the single-color stark band, and adds no pass and no texture. The gradient dome
math already in `web/lib/scene/decor/sky.ts` lines 139 to 149 is a ready
reference for the colors and the exponent.

## 4. Frame-budget impact, counting full renders

Budget. 60fps desktop is a 16.7 ms frame, 30fps laptop is a 33.3 ms frame.

Baseline today is two full scene renders per frame, the depth pre-pass at
`depthWater.ts` lines 375 to 383 and SalishScene line 321, plus the main render.

- PMREM env, recommended. Per-frame full scene renders stay at two. The only
  per-frame cost is one env sample in the water shader, estimated under 0.1 ms.
  The six-face build and prefilter is one-time because the sun is pinned, see
  below. This fits the budget with no change to the per-frame render count.
- Planar Reflector, quality preset. Per-frame full scene renders rise to three,
  the depth pre-pass, the reflection, and the main pass, a 50 percent increase
  over baseline geometry work. On a frame that is already near budget this is the
  difference between hitting and missing 60fps, which is why it is gated to a
  quality tier and to a reduced reflection-target size.
- SSR. No extra full scene render, but it needs a normal buffer and an
  EffectComposer the scene lacks, and the ray-march is fragment-bound and scales
  with resolution and step count. Cost is real and unbounded without tuning, and
  it still does not fix the horizon, so it is not budgeted here.

The pinned-sun fact that makes PMREM nearly free per frame. `makeSun(SCENE_TIME,
48.5, -123)` is created once in `useMemo` at SalishScene lines 282 and 603 and
the sky is driven from it, so the sky is static for the session. PMREM therefore
builds once at load and only rebuilds if a future time-of-day control retargets
the sun. If the sun ever animates per frame, the PMREM rebuild cost would move
on-budget and the cheap-gradient fallback or a throttled rebuild would become the
right default. This is an open question for O0 in section 6.

## 5. Collision and sequencing

Feeds. This finding feeds the twin's W3 world-materials-and-shading wave,
specifically the sky-env and water-upgrade agents, and the WFX build wave. The
concrete deliverable for build is a new cube or PMREM uniform on the water
material plus the Fresnel-mix change at `depthWater.ts` lines 272 to 285, and a
`scene.environment` assignment in the integrator.

Depends on WFX-R04, sky. The reflection is only as good as the sky it samples.
R04 defines the procedural sky. The existing Preetham `Sky` addon from
`decor/sky.ts` is already a valid PMREM source, so if R04 keeps it the env can be
baked now. If R04 swaps the sky model, the PMREM source follows it with no change
to R03's water-side sampling.

Depends on WFX-R05, PMREM and tonemap. R05 owns PMREM generation, exposure, and
ACES. R03 consumes R05's env texture, it should not bake its own. There is a
clear ownership seam, recommend R05 owns the single `fromScene` build and the
`scene.environment` assignment, since R05 also wants that env for image-based
lighting on the terrain and other MeshStandard materials, and R03's water simply
samples it. This avoids two agents double-baking the same map. The env must be
sampled in linear space and tonemapped consistently with R05's pipeline.

Collision with WFX-R01, surface BRDF. R01 and R03 edit the same fragment block,
`depthWater.ts` lines 272 to 285. R01 owns the Fresnel and specular response,
R03 owns what the surface reflects toward, the env radiance. To stop two agents
rewriting the same lines in the build wave, R01 and R03 should hand the build a
single combined surface-reflection spec, R01's Schlick Fresnel weighting R03's
env sample.

Convergence file. Adding `scene.environment` and any reflector mount touches
`web/app/components/scene/SalishScene.tsx`, the locked convergence file. Per the
charter this serializes through O0 against W-CAM, W-LABELS, W3, W4, and LGC.
Research changes none of it. Note SalishScene already manages background
ownership, `RealismRig` runs with background false so `SkyRig` owns
`scene.background`, so the env assignment slots next to that existing seam.

## 6. Open questions for O0

1. PMREM build ownership. Confirm R05 owns the single `fromScene` build and the
   `scene.environment` assignment, with R03's water and R01's surface as
   consumers, so the map is baked once. My recommendation is yes.
2. Sun lifetime. The sun is pinned via `makeSun(SCENE_TIME)` in `useMemo`. Is a
   time-of-day control planned that would retarget the sun at runtime? If the sun
   stays static the PMREM is a one-time load cost. If it animates per frame the
   rebuild moves on-budget and the cheap-gradient fallback or a throttled rebuild
   becomes the default. This decides how aggressively to favor PMREM.
3. Reflection content for the default. Is a sky-only reflection acceptable for
   the default surface, or must the default also reflect the horizon-ring land
   silhouettes and scene objects? Sky-only is what PMREM gives cheaply. Reflecting
   land and objects needs the planar Reflector and its third full scene render. My
   recommendation keeps sky-only as the default and reserves planar for a quality
   preset, but the realism call is O0's.
4. Quality-tier matrix. Is there an existing low, medium, high device tiering the
   env-versus-planar choice plugs into, and which tier carries the planar preset?
   WFX-R13 owns the budget, this needs the device tiers to land the gate.
5. Pipeline and color space. The scene renders straight through
   react-three-fiber with no EffectComposer. Confirm R05's tonemapping stays in
   that direct pipeline so the env sample is combined in linear and tonemapped
   once, rather than introducing a postprocess chain, which would also be the
   only path that could make SSR viable later.
