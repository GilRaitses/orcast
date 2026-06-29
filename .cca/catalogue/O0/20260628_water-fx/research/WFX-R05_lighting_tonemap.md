# WFX-R05 lighting, exposure, tonemapping, PMREM environment

Role: WFX-R05, read-only research, Wave 1. Reports to the WFX sub-orchestrator, then O0.
Topic: sun disk, exposure, ACES tonemapping, and a PMREM environment built from the
procedural sky. Central question for this doc is whether the "white sky" is an
exposure/tonemap fault rather than a sky-color fault.

Honesty label: modeled, not measured. All perf numbers below are estimated from the
three.js docs, the canonical examples, and the forum threads cited, not measured on
this repo. No code was changed. No dev server was run.

## 1. Scope and current state, file-cited

### Headline finding (corrects a charter assumption)

The charter root cause 2 says the white sky comes from "no tonemapping-aware
exposure". That is half right. ACES tonemapping is already on, because the live scene
uses a `@react-three/fiber` v8 `<Canvas>`, and r3f v8 turns ACES on by default. The
real gap is that nobody lowered `toneMappingExposure` for the very bright Preetham sky,
so the sky and its sun disc clip toward white at the default exposure of 1.0. So the
white sky is mostly an exposure fault layered on top of a sky-tuning question, not a
"no ACES" fault and not purely a sky-color fault.

### Renderer settings actually in effect

The live scene `<Canvas>` sets no renderer color or tonemap props. The only renderer
mutation is the clear color.

```1007:1011:web/app/components/scene/SalishScene.tsx
      <Canvas
        camera={{ position: [0, 28, 30], fov: 45, near: 1, far: 800 }}
        style={{ width: "100%", height: "100%", background: "linear-gradient(#0b1f33,#08263d)" }}
        onCreated={({ gl }) => gl.setClearColor("#08263d")}
      >
```

A repository-wide search for `toneMapping`, `toneMappingExposure`, `outputColorSpace`,
`outputEncoding`, `ACESFilmic`, and `PMREMGenerator` across `web/**/*.{ts,tsx}` returns
no renderer configuration anywhere. The `flat` and `linear` `<Canvas>` props are also
unused. So every renderer color and tonemap setting is the r3f default.

The r3f version pins the defaults that are therefore in play.

```22:31:web/package.json
    "@react-three/drei": "^9.122.0",
    "@react-three/fiber": "^8.18.0",
```

Per the r3f v8 Canvas docs, `createRoot` builds the `WebGLRenderer` with
`antialias=true`, `alpha=true`, `powerPreference="high-performance"`, and then sets
`outputColorSpace = THREE.SRGBColorSpace` and `toneMapping = THREE.ACESFilmicToneMapping`.
`toneMappingExposure` is left at the three default of `1.0`. `THREE.ColorManagement` is
enabled. Source: https://github.com/pmndrs/react-three-fiber/blob/master/docs/API/canvas.mdx.

Net effective renderer state for the live twin:

- `toneMapping = ACESFilmicToneMapping` (r3f default, not set in repo)
- `toneMappingExposure = 1.0` (three default, never lowered)
- `outputColorSpace = SRGBColorSpace` (r3f default, correct already)
- `ColorManagement.enabled = true` (r3f default)
- clear color `#08263d`, but the sky dome paints over it (see below)

### What paints the sky today

The realism mount hands the background to the sky dome by passing `background: false`,
so the flat realism background does not fight the dome.

```245:255:web/app/components/scene/SalishScene.tsx
    const handle = applyRealism(scene, {
      date: SCENE_TIME,
      lat: 48.5,
      lng: -123,
      water: false,
      // WS-SCENIC: hand scene.background to the sky dome so realism's flat
      // background and the dome's horizon gradient do not fight.
      background: false,
```

`SkyRig` mounts the core three Preetham `Sky` addon and points it at the pinned sun.

```632:640:web/app/components/scene/SalishScene.tsx
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

The dome defaults are turbidity 6, rayleigh 2.5, mieCoefficient 0.005, mieDirectionalG
0.8 (`web/lib/scene/decor/sky.ts` lines 96 to 99). The sun is pinned to a single
instant, a June midday, so the sky never animates today.

```146:146:web/app/components/scene/SalishScene.tsx
const SCENE_TIME = new Date("2026-06-27T20:00:00Z");
```

### Why the Preetham dome blows out at exposure 1.0

The vendored Sky shader writes a sun disc with very high radiance and then runs the
renderer tonemapping on its own output.

```203:212:web/node_modules/three/examples/jsm/objects/Sky.js
			float sundisk = smoothstep( sunAngularDiameterCos, sunAngularDiameterCos + 0.00002, cosTheta );
			L0 += ( vSunE * 19000.0 * Fex ) * sundisk;
			...
			#include <tonemapping_fragment>
```

The `19000.0` sun term and the bright sky luminance are designed to be compressed by a
reduced exposure. The canonical three example does exactly that, pairing the Sky addon
with `toneMapping = ACESFilmicToneMapping` and `toneMappingExposure = 0.5`. Source:
https://github.com/mrdoob/three.js/blob/master/examples/webgl_shaders_sky.html. At the
repo default exposure of 1.0 the same sky reads near white, especially around the sun
and at the zenith. That matches the operator report of a white sky.

### Sun light and the missing visible sun

`makeSun` already returns a sun direction, a warm-to-neutral color, a directional
intensity, and an ambient intensity (`web/app/components/scene/realism/sun.ts` lines 143
to 161). `applyRealism` feeds those into a `DirectionalLight`, an `AmbientLight`, and a
`HemisphereLight` (`applyRealism.ts` lines 73 to 85). So the scene has directional and
fill light. What it does not have is a visible sun disc tied to `makeSun`. The only sun
disc present is the one baked into the Preetham shader, whose brightness is governed by
exposure. The throwaway `RealismSandbox.tsx` does add a small `meshBasicMaterial` sphere
at the sun direction (lines 85 to 88), but that harness is not wired into the live scene.

### No image-based lighting today

A search for `.environment` and `PMREMGenerator` across `web` finds no
`scene.environment` assignment and no PMREM use. So no material in the scene receives
image-based lighting. Any `MeshStandardMaterial` or `MeshPhysicalMaterial` decor is lit
only by the three discrete lights, which is part of why surfaces read flat.

## 2. Technique survey with URLs

- ACES filmic tonemapping. A filmic curve that compresses high dynamic range toward a
  filmic roll-off so bright values do not hard-clip to white. It is the r3f v8 default
  and the standard pairing for the Preetham sky. r3f Canvas defaults:
  https://github.com/pmndrs/react-three-fiber/blob/master/docs/API/canvas.mdx. The known
  r3f gotcha that `toneMapping` may be ignored if passed only through `gl` in older v8
  builds, with `flat` and `onCreated` as the reliable levers, is documented in
  https://github.com/pmndrs/react-three-fiber/issues/1547.

- `toneMappingExposure`. A scalar multiply on scene luminance before the tonemap curve.
  Lowering it darkens and de-clips the image. The canonical Sky example sets it to 0.5:
  https://github.com/mrdoob/three.js/blob/master/examples/webgl_shaders_sky.html. Forum
  confirmation that 0.5 is the practical value for the Sky addon:
  https://discourse.threejs.org/t/get-changing-light-color-of-sun-in-sky-js-shader/25815.

- Output color space. sRGB output with ColorManagement enabled is the modern correct
  setup and is already the r3f default here, so no change is needed. Background on why
  this matters: https://www.donmccurdy.com/2020/06/17/color-management-in-threejs.

- `PMREMGenerator`. Prefilters an environment, an HDRI, a cubemap, or a rendered scene,
  into a mip chain where each mip matches a roughness level, so PBR materials get correct
  image-based lighting and roughness-aware reflections. `fromScene` can prefilter a live
  scene such as the sky dome. Docs and usage:
  https://threejs.org/docs/#api/en/extras/PMREMGenerator and
  https://www.ramijames.com/learn-threejs/lighting/environment-maps. The standard
  guidance is to run it once at load, reuse one generator instance, and dispose the
  source. Running `fromScene` every frame is called out as extremely expensive:
  https://discourse.threejs.org/t/bad-performances-when-animating-a-pmremgenerator-environment/48043
  and https://discourse.threejs.org/t/practical-way-to-animate-scene-environment/84319.

- Dynamic environment alternative. For an animated sky a `CubeCamera` plus
  `WebGLCubeRenderTarget` at 128 to 256 px, updated every few frames, is the cheaper
  real-time path, though it still needs a PMREM pass for proper roughness:
  https://dev.to/peter3riding/real-time-dynamic-environment-maps-in-threejs-the-holy-donut-technique-explained-2796.

## 3. Recommendations with cost and three-only fallback

Everything below is core three plus the already-present r3f. No new dependency is
required, so there is no costed new-dependency recommendation and no separate fallback
to state. The fallback is the recommendation. Ordered by realism gain per millisecond.

### R05-1, lower exposure for the bright sky (cheapest, do first)

Set `toneMappingExposure` to about 0.5, matching the canonical Sky example, with a tune
range of 0.4 to 0.6. ACES is already on and sRGB output is already correct, so this is
the single line that fixes most of the white sky. Because the existing code already uses
`onCreated` to set the clear color, the safe place is the same callback, which also
sidesteps the historical r3f `gl`-prop tonemapping gotcha.

```tsx
onCreated={({ gl }) => {
  gl.setClearColor("#08263d");
  gl.toneMapping = THREE.ACESFilmicToneMapping; // already the r3f default, set for clarity
  gl.toneMappingExposure = 0.5;                  // tune 0.4 to 0.6
}}
```

Cost: zero per-frame cost. It is a renderer property, not a pass. Estimated effort one
line. This is a `SalishScene.tsx` edit, so it serializes through O0 in a build wave.

### R05-2, a visible sun disc tied to makeSun (cheap, optional)

The Preetham shader already draws a sun disc, so a separate disc is optional. If a
crisper sun is wanted, add a single `meshBasicMaterial` sphere or a camera-facing sprite
placed along `makeSun().direction` and colored from `makeSun().color`, the same pattern
the sandbox already uses. Keep it small and additive so it reads as glare, not a hard
ball. Cost: one extra draw call, negligible. Three-only, no dependency.

### R05-3, PMREM environment from the sky for image-based lighting (one-time cost)

Build a PMREM from the Preetham dome once and assign it to `scene.environment` so every
PBR material gets sky-driven ambient and roughness-aware reflection. The robust recipe
is to make one `PMREMGenerator`, hide everything except the sky, call `fromScene`, then
restore visibility and assign the texture. Pseudocode, three-only:

```ts
const pmrem = new THREE.PMREMGenerator(gl);
pmrem.compileEquirectangularShader(); // warm the shader to spread the cost
const envTex = pmrem.fromScene(scene /* sky-only via a layer or temporary hide */).texture;
scene.environment = envTex;
// regenerate only when the sun/date changes; dispose the old texture and the generator on unmount
```

Two honest caveats for this repo. First, the custom water `ShaderMaterial` in
`web/lib/scene/water2/depthWater.ts` and the Preetham sky material do not auto-consume
`scene.environment`, so the IBL benefit lands on `MeshStandardMaterial` and
`MeshPhysicalMaterial` decor and on any future PBR terrain or seafloor material that W3
builds, not on the existing hand-written water or sky shaders. Second, the streamed
3D-tiles materials are textured and will not gain much from IBL. So R05-3 is most
valuable once W3 introduces real PBR materials. It is a strong enabler, not an instant
win on the current shader set. Three-only, no dependency.

## 4. Frame-budget impact

The frame budget is 60 fps desktop and 30 fps laptop, and the depth pre-pass already
spends one full scene render. Against that:

- R05-1 exposure and R05-2 sun disc add no per-frame render passes. Exposure is a
  property read inside the existing tonemap step. The sun disc is one tiny draw. Both fit
  the budget with no measurable cost.

- R05-3 PMREM is a one-time cost, not per-frame, as long as the sun stays pinned. With
  `SCENE_TIME` static today, the env map is generated once at mount and never again, so
  there is zero steady-state frame cost. Estimated one-time generation, not measured
  here, is on the order of a few milliseconds on desktop and a brief stutter that can
  reach tens of milliseconds on a weak laptop GPU, consistent with the forum reports
  cited in section 2. Calling `compileEquirectangularShader` early spreads that cost.

- The cost only becomes per-event when W3 or W4 adds time-of-day animation. Regenerating
  the PMREM on every sun change would be expensive, because `fromScene` re-renders and
  re-prefilters the sky. The mitigation is to regenerate at most on discrete date
  changes, or to switch to a low-res `CubeCamera` env updated every few frames with
  keyframe crossfade, per the dynamic-environment references in section 2. This is a W3
  or W4 design choice, not a Wave 1 build.

Summary of one-time versus per-frame:

- One-line renderer settings, exposure, tonemap, color space: per-frame cost zero.
- PMREM with a pinned sun: one-time at mount, per-frame cost zero.
- PMREM with an animated sun: per-event cost on each regen, must be throttled.

## 5. Collision and sequencing

- The renderer config lives in `web/app/components/scene/SalishScene.tsx`, the locked
  convergence file. R05-1 and R05-2 edit it, so they must serialize through O0 in a
  build or integrate wave against W-CAM, W-LABELS, W3, W4, and LGC, per the charter
  convergence lock. The exact touch point is the `onCreated` callback at line 1010 and
  the `<Canvas>` element around lines 1007 to 1011.

- R05-3 PMREM should tie to the sky environment work. The dome already owns the
  background via `SkyRig` and `background: false`. The PMREM env and the dome must read
  the same sun, so this depends on WFX-R04 sky-atmosphere and should land with the W3
  sky-env agent so one owner controls the sky, the env map, and the background together.
  Sequence R05-3 after R04 and after R05-1, since the env map should be prefiltered from
  a correctly exposed sky.

- R05-1 exposure interacts with R04 sky tuning and with WFX-R03 reflections and WFX-R01
  surface BRDF, because lowering global exposure darkens the whole frame, including the
  water specular and the terrain. The exposure value should be chosen jointly with R04
  and R01 so the sky stops clipping without crushing the water and land. The water2
  shader feeds on a flat `skyColor(...)` today (`SalishScene.tsx` line 303), so its
  Fresnel sky reflection will not follow the dome or the env map until R03 rewires it.

- Color space needs no change and creates no collision, since sRGB output is already the
  r3f default.

## 6. Open questions for O0

1. Confirm the white-sky correction is acceptable to record. ACES is already on by the
   r3f default, so the fix is `toneMappingExposure` plus R04 sky tuning, not adding ACES.
   This refines charter root cause 2. Approve the corrected framing.

2. Target exposure value. Recommend 0.5 with a 0.4 to 0.6 tune range, chosen jointly
   with R04 and R01. Who owns the final number, the integrator or a sandbox tune.

3. Should the live scene add a visible sun disc tied to `makeSun`, R05-2, or rely on the
   Preetham shader's own disc. This is a look decision.

4. PMREM scope. Given the existing water and sky are custom `ShaderMaterial`s that do not
   consume `scene.environment`, confirm that R05-3 is sequenced into W3 alongside real
   PBR materials rather than landed early for little gain.

5. Time-of-day. `SCENE_TIME` is pinned, so PMREM is one-time today. If W3 or W4 animates
   the sun, O0 should pick the env strategy, discrete-date regen versus a throttled
   `CubeCamera`, before that build wave starts.

6. Owner for the `SalishScene.tsx` renderer edit. R05-1 and R05-2 touch the convergence
   file, so O0 should assign the single serialized editor and the collision order against
   W-CAM, W-LABELS, W3, W4, and LGC.
