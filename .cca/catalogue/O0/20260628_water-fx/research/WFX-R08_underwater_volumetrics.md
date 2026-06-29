# WFX-R08 underwater volumetrics

Role: WFX-R08, read-only research subagent, WATER-FX Wave 1.
Owns this one file. No code changed.
Repo state verified against the charter pin 915e4cc77923de93ed5f7e9a75feab9eb2e12896 (branch main, 2026-06-28).
Honesty label holds. Everything below is modeled, not measured. Salish Sea water is turbid and green with a short secchi depth, so underwater visibility is short by design.

Topic. Underwater volumetrics, meaning exponential depth fog, particulate in-scatter, and visibility falloff once the camera is below the water surface. This doc DEFINES the `web/lib/scene/underwater/` module that 3D-TWIN W4 will build. It does not write that module. It grounds it so W4 has a costed, file-cited spec.

---

## 1. Scope and current state, file-cited

### What exists today

The twin renders water and atmosphere with hand-written GLSL on `three`, no postprocessing library, no new dependency. The underwater module does not exist yet. `web/lib/scene/underwater/` returned zero files on glob, and the only consumer planned is W4.

Above-water fog is the only fog in the scene. `web/app/components/scene/realism/atmosphere.ts` line 22 `makeFog()` returns a linear `THREE.Fog` colored `#9fb8cc` with `near` 120 and `far` 520. `web/app/components/scene/realism/applyRealism.ts` line 99 sets `scene.fog = makeFog({ color: fogColorForSky(sky) })` and line 98 sets `scene.background` from `skyColor()`. `web/lib/scene/decor/fogTuning.ts` `tuneFog()` then retunes that fog color per sun elevation in place, mounted by `FogTuneRig` in `web/app/components/scene/SalishScene.tsx` line 673.

The water surface is `web/lib/scene/water2/depthWater.ts` `makeWater2()`. It samples an opaque-scene depth pre-pass, reconstructs the seabed world position through `uInverseViewProjection`, and computes a vertical water column. It then applies Beer-Lambert as `colorT = 1.0 - exp(-column / uDepthColorScale)` at line 256 and `depthAlpha = 1.0 - exp(-column / uDepthAlphaScale)` at line 257, mixing a two-stop `uColorShallow` to `uColorDeep` ramp. The plane sits at scene Y equal to `level`, default 0, with `depthWrite` false and `renderOrder` 1. This is the exact exponential form the underwater module mirrors, except the underwater module integrates extinction along the camera-to-fragment view ray rather than down a vertical column.

The camera cannot currently go underwater. `web/lib/scene/camera/director.ts` `enforceAltitudeClamp()` at line 146 lifts the eye to a no-dunk floor that is the higher of the water plane Y 0 and the probed tile surface plus a clearance, so today the eye is always held above the surface. W4 `camera-modes` adds `dive` and must relax that clamp for the underwater module to ever trigger.

### What `atmosphere/transition.ts` does today

This is the file the underwater transition must stay continuous with. It is `web/lib/scene/atmosphere/transition.ts`. It contains pure frame-driven tween factories. It owns no realism state and reaches into no realism internals. It operates only on the `THREE` objects passed in.

`makeTween()` at line 67 is the core. It captures start state lazily on the first `update()` call through an `onStart` hook, so a transition reads the live target value at the instant it actually begins, for example right after a camera cut. It eases progress through `onTick` and returns a `TweenHandle` with `update(dtMs)`, `cancel()`, `settled`, and a `done` promise that resolves on natural completion or cancel.

`rollInFog()` at line 154 is the relevant primitive. For a linear `THREE.Fog` it eases `far` inward, defaulting `farTo` to 40 percent of the live `far` at line 176, and optionally `near`. For a `THREE.FogExp2` it raises `density`, defaulting to 3 times the live density at line 179. It optionally cross-fades the fog color through `opts.color` at lines 181 and 191. The exported `FogTarget` type at line 54 is `THREE.Fog | THREE.FogExp2`, and `isLinearFog()` at line 56 branches on `fog.isFog`. So the file already understands both fog modes and already supports a color cross-fade. That is the seam the underwater transition reuses.

`descentLighting()` at line 231 eases lights toward a descent look, dimming to 70 percent of current intensity at line 253 and tinting toward `fogColorForSky(skyColor(elevationDeg))` at line 244, default elevation 4 degrees.

The live consumer of these tweens is the journey controller, `web/lib/journey/controller.ts`. `runPlaceJourney` rolls the linear fog in as a soft mask over a camera cut, then clears it back out, reading a resting `far` at line 241 so the clear-out can restore it. That resting-far restore is linear-fog only. For a `FogExp2` it returns null at line 241 and the clear-out falls back to the `rollInFog` default. This matters for sequencing and is called out in section 5.

Net current state. There is no below-surface fog, no underwater tint, no in-scatter, no particulate, and no waterline crossing logic anywhere in `web/`. The pieces the module needs already exist in compatible form, namely a Beer-Lambert exponential convention in the water shader, a `scene.fog` slot that supports both `Fog` and `FogExp2`, and a tween library that can cross-fade either fog mode.

---

## 2. Technique survey with URLs

### A. Exponential distance fog as the volume

`THREE.FogExp2` applies `fogFactor = 1.0 - exp(-(density * fogDepth)^2)` per fragment inside every fogged material, where `fogDepth` is the camera-space distance. It is exponential squared fog, clear near the camera and densening faster than linear with distance, which reads as a believable short-visibility medium. It costs no extra render pass because it is compiled into the existing material fragment shaders. Only one fog object can be active on a scene at a time.
- https://threejs.org/docs/pages/FogExp2.html
- https://threejs.org/manual/en/fog.html
- https://github.com/mrdoob/three.js/pull/17273 documents the exact GLSL `1.0 - exp(-density*density*depth*depth)`.

Beer-Lambert transmittance is the physical basis. Transmittance is `exp(-sigma * distance)`, the same exponential the water column shader already uses at `depthWater.ts` lines 256 to 257. FogExp2 is the squared variant of that law applied to view distance.
- https://developer.download.nvidia.com/gameworks/events/GDC2016/Fast%20Flexible%20Physically-Based%20Volumetric%20Light%20Scattering%20-%20Notes.pdf

### B. Particulate in-scatter and the depth-dependent ambient add

In-scatter is the light scattered into the view ray by the medium and its particles, which is what makes water glow rather than just darken. The physically based real-time route separates single scattering, handled with froxel lighting through a frustum-aligned volume texture, from multiple scattering, approximated analytically from the oceanographic diffuse downwelling attenuation coefficient Kd as a function of depth and wavelength. That paper is explicit that the common cheap route in shipping games is a tinted exponential fog with a depth-dependent ambient term, controllable and inexpensive, which is exactly the baseline recommended here.
- https://onlinelibrary.wiley.com/doi/10.1111/cgf.15009 Real-Time Underwater Spectral Rendering, Monzon 2024.
- https://www.eurographics.es/wp-content/uploads/2023/05/TFM_underwater_rendering_CEIG2023.pdf CEIG 2023 companion.
- https://zaguan.unizar.es/record/135350/files/texto_completo.pdf full text.

The same paper makes the point that matters for R09. Atmosphere fog assumes monochromatic extinction, but water extinction is strongly wavelength dependent, so a single scalar fog density cannot reproduce per-channel absorption. This is why the FogExp2 color must be sourced from R09 rather than guessed.

A marine-snow particulate layer is a separate, cheaper cue. A `THREE.Points` cloud of additive sprites drifting near the camera reads as suspended particles catching light. It is one draw call and is preset-gated.

### C. Fullscreen post tint

A single `ShaderPass` over an `EffectComposer` chain can tint, desaturate, and vignette the whole frame, doing the saturation and edge falloff a uniform `scene.fog` cannot. Typical cost of a simple `ShaderPass` is about 0.1 ms at 1080p on a mid-range GPU. The catch is that adopting a composer routes the entire scene through ping-pong buffers and an extra fullscreen copy, and it changes the render path that the water depth pre-pass currently lives in. Each pass is a full-screen redraw, so cost scales with chain length.
- https://threejs.org/manual/en/how-to-use-post-processing.html
- https://threejs.org/docs/pages/EffectComposer.html
- https://masterallarts.com/learn/threejs-from-zero/07-post-processing/ gives the per-pass cost table, ShaderPass about 0.1 ms.

`ShaderPass`, `EffectComposer`, and `CopyShader` ship inside `three/addons`, so a composer-based tint is still three-only and adds no new runtime dependency. A dedicated library such as `pmndrs/postprocessing` is the costed-dependency option, not the default.

### D. Raymarched or froxel volume

True volumetric raymarching or froxel accumulation integrates in-scatter and shadowing along the ray and gives godrays and heterogeneous density. It is the expensive path. The spectral underwater pipeline above, which is froxel plus an analytic multiple-scattering term, measures over 30 fps on an NVIDIA GTX 1050 and over 60 fps on a GTX 1660 Super for the whole pipeline, not for a single added pass. The NVIDIA GDC 2016 volumetric scattering work builds light-volume meshes from shadow maps and accumulates the in-scatter integral, and assumes a deferred renderer or a depth pre-pass for a forward one.
- https://onlinelibrary.wiley.com/doi/10.1111/cgf.15009
- https://developer.download.nvidia.com/gameworks/events/GDC2016/Fast%20Flexible%20Physically-Based%20Volumetric%20Light%20Scattering%20-%20Notes.pdf

This is out of budget for the baseline and is not recommended. Volumetric light shafts as a feature belong to WFX-R07 caustics and godrays, not here.

---

## 3. Recommendation and cost, with three-only fallback

### Recommended baseline, cheapest credible approach

Swap `scene.fog`, do not raymarch. When the camera crosses below the water level, the underwater module saves the live above-water `scene.fog` and `scene.background`, then installs a `THREE.FogExp2` whose color comes from R09 and whose density comes from R11, and swaps `scene.background` to the same fog color so empty view directions read as turbid water rather than sky. On surfacing it restores the saved fog and background. This is the tinted-exponential-fog approach the literature names as the standard cheap route.

Density to visibility mapping. For FogExp2 the fog factor reaches roughly 0.95 at `distance` approximately `1.73 / density`. Treat that 0.95 distance as the visibility distance V from R11. Then `density` approximately `1.73 / V`. Because Salish visibility is short, V is small and density is high. The exact V is R11's number, modeled not measured. As a placeholder for sandbox bring-up only, a typical coastal secchi of a few meters maps, through the scene scale `worldUnitsPerMeter` used by the datum fix W2.6, to a small world-space V and therefore a large density. The integrator must tune V against R11, not against this placeholder.

Depth-graded tint. Darken and green-shift the fog color as the camera goes deeper, by lerping the R09-derived surface color toward a darker deep color over camera depth below Y 0, using the same `1 - exp(-depth/scale)` shape as `depthWater.ts`. This reproduces the loss of red first, then green surviving longest, without a per-channel volume.

In-scatter, baseline. Add a small depth-dependent ambient term to the fog color so the medium glows slightly toward the sun rather than only attenuating. This is a uniform add, not a froxel volume, matching the inexpensive depth-dependent ambient the literature describes.

Particulate, preset-gated. A `THREE.Points` marine-snow cloud of a few thousand additive sprites that drift and are recycled around the camera. One draw call, off by default, enabled in the quality preset W3 defined.

Per-channel honesty. FogExp2 carries one scalar density and one color, so it cannot apply per-channel extinction directly. Bake R09's per-channel absorption into the FogExp2 color by evaluating R09's `exp(-uAbsorption * representativeDistance)` at a representative view distance, so the green-dominant survival is in the color. If the look demands true per-channel underwater extinction later, the upgrade path is a `material.onBeforeCompile` injection that replaces the fog chunk with a per-channel `exp(-absorption * fogDepth)`, still three-only and still no extra pass. Recommend baking into FogExp2 color first and only upgrading if acceptance frames demand it.

Cost of the baseline. The fog swap adds no render pass and is near zero added ALU per fragment, because fog is already part of every fogged material's fragment shader and FogExp2 is already a compiled path in `three`. Estimated added frame cost is effectively zero beyond the existing fog. The depth pre-pass that `depthWater.ts` already runs is unchanged. The depth-graded tint and the ambient add are uniform updates on the CPU per frame, negligible. The particulate `Points` layer is one transparent draw call of a few thousand points, estimated well under 0.5 ms on the target hardware and gated off by default. No measured number is claimed for the baseline because no code was run in this read-only wave.

### Optional addition, fullscreen tint, only if a composer already exists

If W4 or the wider stack stands up an `EffectComposer` for other reasons such as R05 tonemap or R07 godrays or the W5 post-fx wave, then add one underwater `ShaderPass` for saturation and vignette that FogExp2 cannot do, at an estimated 0.1 ms. Do not stand up a composer solely for the underwater tint, because the composer's fullscreen copy and the rewiring of the render path around the water depth pre-pass cost more than the tint buys. This is the dependency-style decision flagged to O0 in section 6.

### Three-only fallback

The entire baseline is already three-only with no new dependency. `THREE.FogExp2`, `THREE.Points`, and `material.onBeforeCompile` are core `three`. The optional fullscreen tint uses `ShaderPass` and `EffectComposer` from `three/addons`, which are still inside the `three` package, so even the optional path adds no new runtime dependency. The only true new-dependency option, a library such as `pmndrs/postprocessing`, is not recommended and is not needed for anything in this spec.

---

## 4. Frame-budget impact

Budget is 60 fps desktop and 30 fps laptop, which is 16.6 ms and 33.3 ms per frame. The depth pre-pass in `depthWater.ts` already spends one full scene render every frame, so every new pass is measured against what is left.

- FogExp2 swap and depth-graded tint and ambient add. Zero added render passes. Near-zero added per-fragment cost since fog is already compiled into materials. CPU side is a handful of uniform writes per frame. Estimated impact, negligible.
- Particulate `Points` layer. One additional transparent draw call. Estimated under 0.5 ms for a few thousand points on target hardware, preset-gated off by default. No measured number, read-only wave.
- Optional fullscreen tint `ShaderPass`. Estimated about 0.1 ms at 1080p from the cited per-pass table, but only viable if a composer already exists, because the composer itself adds a fullscreen copy and reorders the render path around the existing depth pre-pass.
- Raymarch or froxel volume. The cited spectral pipeline measures over 30 fps on a GTX 1050 and over 60 fps on a GTX 1660 Super for the whole pipeline. That is a measured number for the expensive option and confirms it is not a small add. Out of budget for the baseline, not recommended, godrays deferred to R07.

Conclusion. The recommended baseline fits the budget with effectively no measurable cost, because it reuses the already-paid fog path and adds at most one optional gated draw call. The expensive options are explicitly out of scope for the baseline.

---

## 5. Collision and sequencing

### This doc DEFINES `web/lib/scene/underwater/`, built by W4

3D-TWIN W4 `underwater` agent owns `web/lib/scene/underwater/` with deliverable below-surface exp fog and tint plus a smooth surface transition plus underside water plus optional particles and shafts, preset-gated. This is in `.cca/catalogue/O0/20260627_terrain-bathymetry-twin/wave_shape.yml` line 191. This research is the spec that agent consumes. No file collision in this wave because research writes only this doc.

Proposed module shape for W4, framework-free factory mirroring `makeWater2()`:
- An `installUnderwater(scene, opts)` factory that returns a handle with `update(camera, dtMs)`, `isSubmerged()`, and `dispose()`. It mutates `scene.fog` and `scene.background` only while submerged and restores both on dispose, exactly as `applyRealism` saves and restores `prevFog` and `prevBackground` at `applyRealism.ts` lines 93 to 94 and 130 to 131.
- A waterline crossing detector keyed on `camera.position.y` against the water level. The level must come from the W2.6 data-driven reference where NAVD88 0 m maps to scene Y 0, not a hardcoded 0, because W2.6 changes the level source in `depthWater.ts` and `SalishScene.tsx`.
- A fog color from R09 and a density from R11, with the depth-graded tint and ambient add from section 3.
- An optional `THREE.Points` particulate layer behind a preset flag.

### Continuity with `atmosphere/transition.ts`, no popping at the waterline

The module must reuse `rollInFog` from `transition.ts`, not duplicate tweening. The continuous crossing is three steps.
1. Approaching the surface from above, ease the existing linear `scene.fog` `far` inward and cross-fade its color toward the turbid green using `rollInFog(durationMs, fog, { far, color })`, which already supports both at `transition.ts` lines 176 and 191.
2. At the crossing, swap to a `THREE.FogExp2` pre-seeded so its fog factor at a representative distance matches the linear fog factor at that same distance at the moment of the swap, so there is no visual pop. Matching condition. Linear factor is `(d - near) / (far - near)` clamped. FogExp2 factor is `1 - exp(-(density * d)^2)`. Choose the seed density so these are equal at a chosen d, then ease density from that seed up to the R11 target with `rollInFog` on the FogExp2 path, which animates density at line 179.
3. Surfacing reverses this, swapping back to the saved linear fog and easing it back out.

Because `rollInFog` captures its start state lazily on first `update()`, the swap-then-ease sequence reads live values and will not snap. This is the same lazy-capture behavior the journey controller relies on.

### Collision with the journey controller over `scene.fog`

`web/lib/journey/controller.ts` drives `scene.fog` for camera-cut masks and assumes a linear `THREE.Fog`, reading a resting `far` at line 241 that returns null for a `FogExp2`. If a journey runs while submerged, its clear-out logic will mis-restore the underwater fog. The module must own a clear above-and-below state and the integrator must not run place journeys while submerged, or the module must expose its own restore that the integrator calls. This is a sequencing rule for W4's integrator and an O0 question in section 6.

### Camera clamp dependency

The underwater module cannot trigger until W4 `camera-modes` relaxes `enforceAltitudeClamp()` at `director.ts` line 146 for dive mode. The crossing detector and the clamp relaxation must be wired together by W4 so the eye can pass Y 0 and the fog swaps at the same instant.

### Depends on R09 and R11, defers to R12 and R07

- R09 rgb-absorption supplies the fog color, evaluating and extending the per-channel extinction in `WATER2_TUNING_REQUEST.md`. This module bakes that into the FogExp2 color and keeps the per-channel upgrade path open through `onBeforeCompile`.
- R11 salish-optics supplies the visibility distance V and the turbid-green target, which sets density through `density` approximately `1.73 / V`. Visibility is short by R11's truthful numbers, modeled not measured.
- R12 surface-from-below owns the underside of the surface, Snell window, and total internal reflection. This module does not render the underside, it only fogs and tints the volume, and it hands off to R12 at the surface plane.
- R07 caustics-godrays owns volumetric light shafts. The particulate layer here is the cheap suspended-particle cue, not the shaft volume.

---

## 6. Open questions for O0

1. Composer in the target architecture. Is W4, or R05 or R07 or the W5 post-fx wave, going to introduce an `EffectComposer` anyway. If yes, the underwater fullscreen tint can ride it for an estimated 0.1 ms. If no, the recommendation is FogExp2-only with no composer, because standing one up solely for the underwater tint costs more than it returns. This is the new-dependency-style decision the charter routes to O0.

2. Water-level accessor. W2.6 makes the water level data-driven so NAVD88 0 m maps to scene Y 0. The crossing detector must read that same reference. Confirm the shared accessor the module reads rather than hardcoding 0, since `depthWater.ts` and `SalishScene.tsx` are W2.6's to change.

3. Ownership of `scene.fog` while submerged. The journey controller assumes linear fog and will mis-restore a `FogExp2`. Confirm the rule. Either the integrator suppresses journeys while submerged, or the underwater module owns an explicit save-and-restore that the integrator calls on every crossing.

4. Per-channel versus scalar underwater extinction. Accept the FogExp2 monochromatic color baked from R09 as the baseline, or commit up front to the `onBeforeCompile` per-channel fog injection. Recommendation is to ship the baked baseline and only upgrade if acceptance frames demand it.

5. Preset gating. Which quality preset enables the particulate layer and, later, R07 shafts. The W3 frame-budget decision says post only in the quality preset, so confirm the particulate `Points` layer defaults off and turns on with that preset.
