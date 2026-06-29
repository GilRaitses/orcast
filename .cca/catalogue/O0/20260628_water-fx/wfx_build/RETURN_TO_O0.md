# WATER-FX build, return to O0

Sub-orchestrator return for the WFX sandbox build. Sandbox-only. No convergence
file edited. No commit, no push. The honesty label holds: every lever changes how
the water and sky look and asserts no measured depth, color, or sea state. The
seabed read stays the modeled CUDEM topobathy.

## Files I own and changed (water2 + the /water sandbox only)

- `web/lib/scene/water2/depthWater.ts` rewritten as the single merged
  R09 + R10 + R01 + R06 + R02 color-path edit (SYNTHESIS section 4 order).
- `web/app/(sandbox)/water/WaterSandboxScene.tsx` rebuilt into the verification
  rig (sky dome, exposure, fog modes, sun time-of-day, dive camera, deterministic
  freeze, perf harness).

I did NOT edit `web/app/components/scene/SalishScene.tsx` or `web/app/globals.css`.
Both show as modified in the working tree, but that is the CVP lane's BuoyMarker
beacon swap and its styles, not WFX. Confirmed by diff: the SalishScene change is
`<mesh>` cone/cylinder beacon to `<BuoyMarker>`, with no water, absorption,
exposure, fog, or uSky edit. No revert needed on my side.

## 1. Runtime error fixed (errorCount 0 on the render host)

The `/water` `Cannot read properties of undefined (reading 'value')` error was
mine. I had briefly routed the new water distance-fog through three.js
`material.fog`, whose `refreshFogUniforms` reads `fogColor.value` on a program
uniform SwiftShader did not expose, so it threw every frame. Fix: self-contained
fog uniforms (`uFogEnabled`, `uFogDensity`, `uFogColor`) plus a new
`handle.setFog(...)` the caller feeds from `scene.fog`. `material.fog` stays the
ShaderMaterial default false, so three never touches the fog uniform path.

Render host proof, errorCount 0:

```
{ "route": "/water", "canvas": true, "errorCount": 0, "errors": [] }
```

Frame Read and examined: `.cca/catalogue/O0/20260628_render-host/proof/water_022308.png`
One-line read: the water reads Salish dark green, not navy, translucent with the
modeled shallows and seabed showing through and soft shoreline foam. The sky is
white, which is the sandbox renderer default exposure 1.0, the SalishScene-level
fix below, not a sandbox change.

## 2. Merged depthWater.ts rewrite, what landed

In SYNTHESIS section 4 order, authored as one coherent edit under a single editor:

1. Per-channel Beer-Lambert body color (R09). `transmittance = exp(-(uAbsorption
   / uDepthColorScale) * column)`. With `uAbsorption = vec3(1.0)` and
   `uRefractStrength = 0` the body color reduces to the prior monochrome two-stop
   frame exactly, the clean A/B. Signed-off green-survives default is `{3,1,3}`.
2. Seabed refraction (R10 Rec A). The depth pre-pass render target now keeps a
   LINEAR-filtered color attachment, bound as `uSceneColor`, read at a normal
   offset screen UV with a depth guard, fed into the body so shallow water shows
   the refracted seabed and deep water fades to the deep tint. No new pass.
3. Energy-conserving GGX specular plus Schlick Fresnel at F0 0.02 (R01), mixing
   toward a reflected-sky gradient `uSkyHorizon..uSkyZenith` (the R03 PMREM seam).
   Roughness grows with screen-space normal variance (`fwidth`) to kill the old
   `pow(ndh,600)` sub-pixel glitter.
4. Soft shoreline feather (R10 Rec B) plus phase-coupled foam run-up (R06), both
   reusing `column` and the Gerstner long-wave phase, both zero at the waterline,
   so land is never washed.
5. Vertex (R02): the sub-Nyquist Gerstner waves are dropped (six down to three),
   amplitude and steepness lowered for a sheltered sea, fine ripple moved to a
   detail normal (a sampled KTX2 map when provided, else a procedural fallback).
6. Distance fog (R04) so the far water dissolves into the horizon haze, fed from
   `scene.fog` through `handle.setFog`.

New public `Water2Options` exposed, all optional with safe defaults so an
un-wired caller is a no-op: `absorption`, `refractStrength`, `roughness`,
`runup`, `contactSoftness`, `skyHorizon`, `skyZenith`, `detailNormalMap`,
`detailScale`, `detailStrength`, `side`. New handle method: `setFog`.

tsc clean. ReadLints clean.

## 3. Budget

Structural confirmation by code inspection: the WFX default stack adds NO third
full render. The seabed refraction reuses the EXISTING depth pre-pass color
attachment (`uSceneColor = depthTarget.texture`), allocates no new render target,
and every other lever is in-shader. So it folds into the two passes already
running, the depth pre-pass and the main render.

The exact per-frame millisecond add and `U` (one full opaque scene render) are
NOT measured. The render host is CPU-only SwiftShader, which the RUNBOOK states is
invalid for client perf, and the local dev path is banned. A `?perf=1` harness is
built into the /water rig (measures U and a water-on vs water-off frame-time A/B,
gl.finish flushed) and is ready to run the instant a client-tier GPU box
(aimez-gpu-capture T4) is reachable. DECISION FOR O0: the binding-tier U
measurement is blocked on that GPU box. Until then the budget rests on the
structural no-third-render guarantee, not a measured number. The planar Reflector
stays gated per decision 8.

## 4. SalishScene.tsx integrate edit-list (for the gated W4 single editor)

Line numbers are the current working tree (post CVP BuoyMarker edit). Re-anchor
at W4, other lanes may shift them. THREE is already imported.

E1. Renderer exposure 0.5 plus ACES, fixes the white sky (R05). Line 1005.
- from: `onCreated={({ gl }) => gl.setClearColor("#08263d")}`
- to:
```
onCreated={({ gl }) => {
  gl.setClearColor("#08263d");
  gl.toneMapping = THREE.ACESFilmicToneMapping;
  gl.toneMappingExposure = 0.5;
}}
```
(ACESFilmic is already the r3f v8 default, the decisive change is exposure 0.5.)

E2. camera.far tighten (R10 Rec C1). Line 547. Coordinate with W-CAM, which owns
the far-plane sign-off.
- from: `camera.far = fitRadius * 100;`
- to:   `camera.far = fitRadius * 8;`

E3. FogExp2 retune to the 120-unit scene (R04). In `FogTuneRig`, lines 672 to 674.
- from:
```
if (scene.fog instanceof THREE.Fog) {
  tuneFog(scene.fog, { elevationDeg: sun.elevationDeg, azimuthDeg: sun.azimuthDeg });
}
```
- to:
```
scene.fog = new THREE.FogExp2(
  tunedFogColor({ elevationDeg: sun.elevationDeg, azimuthDeg: sun.azimuthDeg }),
  0.012,
);
```
`tunedFogColor` is already exported from `@/lib/scene/decor`. Density 0.012 is the
sandbox-proven value, W4 tunes it in the /world sandbox.
DEPENDENCY: line 481 reads `scene.fog instanceof THREE.Fog` for the journey fog
roll. Swapping to FogExp2 makes that branch null, so the journey fog animation
needs a FogExp2-aware update or the journey keeps a linear fog. Flag to the
journey owner through O0.

E4. Water uniform feeds, in the `makeWater2({ ... })` object, lines 295 to 305.
Add after `skyColor: skyColor(sun.elevationDeg),` (line 304):
```
absorption: new THREE.Vector3(3.0, 1.0, 3.0), // R11 green-survives (decision 2)
refractStrength: 0.035,
roughness: 0.12,
runup: 0.6,
contactSoftness: 0.06,
skyZenith: new THREE.Color("#5a86a8"),
```

E5. Per-frame fog feed to the water. In `Water2Rig` useFrame, after line 323
(`handle.update(state.clock.elapsedTime, camera);`) add:
```
const f = scene.fog;
if (f instanceof THREE.FogExp2) handle.setFog({ color: f.color, density: f.density });
else handle.setFog(null);
```

E6. Optional, R03 PMREM env. Next to the `background: false` seam (line 254),
build a PMREM from the sky dome and assign `scene.environment`, then rewire the
water `skyHorizon`/`skyZenith` feed to sample it. Not required for the default
stack, the gradient stops cover it. Defer to the W4 env build.

## 5. Decisions that need O0

1. Deep-tint retarget crosses WS-BATHY ownership. The green-survives look needs
   `bathyWater2Options` deep tint moved from navy `#0b2140` to turbid green
   `#13302b` and shallow from `#2f8fa6` to `#4f8c79`, in
   `web/lib/scene/bathy/style/waterTuning.ts`. SIGN_OFF decision 1 already ratifies
   green-survives, but the file is the WS-BATHY style owner's. Either WS-BATHY
   updates `WATER_TUNED_DEEP` / `WATER_TUNED_SHALLOW`, or W4 overrides them in the
   makeWater2 object. O0 to direct the owner coordination.
2. camera.far tighten needs W-CAM far-plane sign-off (E2).
3. The FogExp2 swap breaks the linear-fog journey roll at line 481 (E3 dependency).
4. U is unmeasured. The binding-tier measurement is blocked on the
   aimez-gpu-capture T4 box being reachable. O0 to decide whether to gate on it or
   accept the structural no-third-render guarantee for now.
