# WFX-R12 surface from below

Read-only research. WATER-FX Wave 1. Topic is the underside of the water surface when the camera dives, covering Snell's window, total internal reflection, ripple-from-below shading, the current underside handling, and the dive transition. Honesty label holds. The look is modeled, not measured. The Salish Sea is turbid and green, so from below the Snell window is a dim murky disc, not a crisp tropical mirror.

Verified against the same paths the charter cites. `three` is pinned at `^0.169.0` in `web/package.json` line 31, which matters for the TwoPassDoubleSide recommendation below.

## 1. Scope and current state

### The FrontSide gap is confirmed

`web/lib/scene/water2/depthWater.ts` builds the only live ocean surface through `makeWater2`. The `THREE.ShaderMaterial` is created with `side: THREE.FrontSide` at line 332, inside the material block at lines 327 to 356. `depthWrite: false` and `transparent: true` are set on the same block at lines 330 and 331. The mesh sets `renderOrder = 1` at line 362 and `frustumCulled = false` at line 366.

The consequence is exact. `THREE.FrontSide` renders only the triangles whose winding faces the camera. The plane is authored in XY then rotated by `mesh.rotation.x = -Math.PI / 2` at line 360 so its front face points up at the sky. When the eye sits above the plane the surface draws. When the eye drops below scene Y equal to the water level the front face points away from the camera, the back face is culled, and the surface fragment is never shaded. From below the water surface vanishes rather than showing a Snell window or a TIR mirror. There is no second material and no backface path. The fragment shader at lines 180 to 295 also assumes a downward look. It reads the opaque depth pre-pass, reconstructs the seabed world position through `uInverseViewProjection`, and computes `column = uWaterLevel - seabed.y` at line 242, which only has the intended meaning when the camera looks down through the column toward the seabed.

The vertex shader writes a single `vWorldNormal` at line 174 that always points up out of the plane, with no sign flip for an under-surface view. So even if the back face were drawn, the lighting math at lines 252 to 286 would shade it as if seen from above. This is the second half of the gap. Drawing the underside is necessary but not sufficient. The shading has to branch on which side faces the camera.

### The dive transition today is a fog-masked descent that never crosses the waterline

`web/lib/scene/atmosphere/transition.ts` is a pure tween factory library. It exposes `rollInFog` at lines 154 to 196, which pulls a `THREE.Fog` `far` inward or raises a `THREE.FogExp2` `density` to mask a camera cut, and `descentLighting` at lines 231 to 267, which dims and tints lights toward the realism sea-haze color `fogColorForSky(skyColor(elevationDeg))`. Both are frame-driven through `update(dtMs)` and own no realism internals. Neither tween touches the water material or the camera. There is no waterline-crossing event, no underside toggle, and no Snell or TIR code anywhere in this file.

The journey that consumes these tweens is `web/lib/journey/controller.ts`. Its beat order is documented at lines 8 to 12 and lines 225 to 226. It is flyTo an establishing altitude, roll fog out, then `descendTo(CRUISE_ALT_M, ...)` at line 275, then followPath, then orbit. `CRUISE_ALT_M = 230` at line 110, and the approach band ends at `APPROACH_ALT_END_M = 182` at line 113. These are metres above sea level. The descent stops well above the water and never goes under.

The reason the camera cannot dive today is a hard clamp in `web/lib/scene/camera/director.ts`. `MIN_ALT_ABOVE_SURFACE_METERS = 40` at line 52 and `MIN_WAVE_HEADROOM_UNITS = 0.5` at line 53 set a no-dunk floor. The clamp at lines 141 to 156 raises the eye to `surfaceY + max(metricClear, MIN_WAVE_HEADROOM_UNITS)` whenever a move or orbit would drop it below the surface. So in the shipped scene the eye is never below the waterline and the FrontSide gap is never visible in normal use. The underside problem is latent. It becomes real only when W4 introduces an actual dive that relaxes or replaces this clamp.

`SalishScene.tsx` wires the tweens through a `transitionsRef` drained each frame at lines 536 to 538 and imports the `TweenHandle` type at line 46. It does not implement any underwater state machine. There is no `web/lib/scene/underwater/` directory in the repo yet. The charter assigns that module to W4 and to WFX-R08. WFX-R12 defines the surface-from-below piece that the W4 dive will need the moment the no-dunk clamp is lifted.

### Plain summary of the current state

The surface is `FrontSide` so it is invisible from below. The shader is hardwired for a top-down column read and an upward normal. The dive transition is a fog and lighting mask on a descent that stops above the water by a 40 m clamp. Nothing crosses the waterline today, so there is no pop yet, because there is no crossing yet. The work here is to make the crossing correct before W4 enables it.

## 2. Technique survey

### Snell's window physics

An underwater eye sees the entire 180 degree above-water hemisphere compressed into a cone. The half-angle of that cone equals the critical angle of the water-to-air interface. With the water index of refraction near 1.333 and air at 1.0, the critical angle is `theta_c = arcsin(1.0 / 1.333) = 48.6 degrees`, so the full cone is about 97.2 degrees. Outside that cone the surface shows total internal reflection of the underwater scene. The standard references confirm both the 97 degree window and the 48.6 degree critical angle. See Wikipedia "Snell's window" at https://en.wikipedia.org/wiki/Snell%27s_window and IOP Spark "Snell's window" at https://spark.iop.org/snells-window.

Three details from the sources matter for honest shading. First, the window is brightest at its center looking straight up and falls to near zero brightness at its rim, because at grazing incidence the Fresnel equations send most light into reflection rather than refraction. The Wikipedia article states this fall-off to nothing at the circumference explicitly. Second, refraction is very sensitive to surface flatness, so ripples distort or break up the disc, which is the ripple-from-below cue. Third, turbidity veils the image behind scattered light. For the Salish Sea this third point dominates. The disc reads as a dim green-grey glow with a soft edge, not a sharp porthole.

### Total internal reflection

For incidence from water to air at angles past 48.6 degrees from vertical, no light crosses the interface and the boundary acts as a near-perfect mirror reflecting the underwater scene back down. See Wikipedia "Total internal reflection" at https://en.wikipedia.org/wiki/Total_internal_reflection, which gives `theta_c approx 48.6 degrees` for water to air and notes the reflected image can be as bright as a direct view. The Grokipedia "Snell's window" page at https://grokipedia.com/page/Snell's_window adds that salinity near n equal to 1.340 shrinks the window to about 96 degrees, which is within tuning tolerance and does not change the approach.

### Rendering the surface from below in three

The three.js forum thread "Anyone gotten Water2 to work while looking upward from underneath the water surface" at https://discourse.threejs.org/t/anyone-gotten-water2-to-work-while-looking-upward-from-underneath-the-water-surface/85114 is the closest prior art. Its practical findings are direct. Plain `DoubleSide` alone does not give the expected refraction from underneath. A working pattern is a copy of the water plane flipped upside down, with the top set to `THREE.FrontSide` and the bottom to `THREE.BackSide`, or flipping the mesh when the camera Y crosses the plane Y. True refraction of the above-water scene needs a render-to-texture of the scene without water plus a depth read, which is a second pass.

Two three.js engine facts constrain the material choice. `gl_FrontFacing` does not behave as expected on a `DoubleSide` material that is also `transparent`, because the renderer splits it into two draw calls and reverses winding for the back pass. This is GitHub issue mrdoob/three.js#25149 at https://github.com/mrdoob/three.js/issues/25149. The fix is `THREE.TwoPassDoubleSide`, added in PR mrdoob/three.js#25165 at https://github.com/mrdoob/three.js/pull/25165, building on the two-call transparent rendering in PR mrdoob/three.js#21967 at https://github.com/mrdoob/three.js/pull/21967. After r148 plain `DoubleSide` renders transparent surfaces in a single pass again, and the two-pass behavior is opt-in through `TwoPassDoubleSide`. The repo is on `three` 0.169, which is past r148, so both modes are available. For a `ShaderMaterial` the recommended branch inside the shader uses the engine-supplied defines, for example `#ifdef FLIP_SIDED` for the back pass and `gl_FrontFacing` under `#ifdef DOUBLE_SIDED`, rather than reading `gl_FrontFacing` blindly.

A simpler reference underwater effect that uses post-processing is ywang170/three.js-glsl-simple-underwater-shader at https://github.com/ywang170/three.js-glsl-simple-underwater-shader, useful as a screen-space tint and ripple example but not a Snell-window solution.

## 3. Recommendations

### Recommendation A, preferred. A dedicated underside material on a flipped twin plane

Build the surface-from-below as a second material rather than overloading the existing top-down shader. Add a backface-oriented copy of the water plane at the same Y, sharing the same Gerstner vertex displacement so crests line up exactly with the top surface, and shade it with a from-below fragment shader. This keeps the existing `FrontSide` top shader at `depthWater.ts` untouched and gives W4 a clean module under `web/lib/scene/underwater/`.

The from-below fragment shader does this. Reconstruct the view direction from the fragment to the eye. Compute the angle between the upward surface normal and the view direction. Inside the 48.6 degree cone, sample the sky or above-water color and brighten toward the center of the disc, with a Fresnel-weighted fall-off to near zero at the 48.6 degree rim so the edge is soft. Outside the cone, show the TIR mirror by reflecting the underwater color, which in practice is the turbid in-scatter color from the WFX-R08 volumetrics rather than a real reflection probe. Modulate the whole result by the turbid attenuation so the disc stays dim and green. Add a ripple term by perturbing the cone test with the shared Gerstner normal so the window wobbles and the rim breaks up. Cite the honesty label in the WIRING doc. The Snell disc is a modeled cue, not a measured radiance.

Cost, estimated. One extra plane of the same `segments` as the main water, currently 180 by 180 at `depthWater.ts` line 38, is about 65k vertices in the vertex stage, only active while the eye is below the waterline. The fragment cost is a handful of extra ALU ops per covered pixel, with no new texture fetch if the TIR color reuses the volumetric in-scatter uniform. No extra full-scene pass if the Snell disc samples the existing sky color uniform rather than a live reflection. I estimate well under 0.3 ms on desktop at 1080p for the underside plane alone, since it only covers screen pixels when submerged and reuses existing buffers. This is an estimate, not a measured number. WFX-R13 should A/B it.

Three-only fallback. This recommendation is already three-only. It uses a second `THREE.Mesh` with `side: THREE.BackSide` and a hand-written `ShaderMaterial`. No new dependency.

### Recommendation B, lighter. Single plane switched to TwoPassDoubleSide with a side branch

Keep one plane and set the material to `THREE.TwoPassDoubleSide`, then branch the existing fragment shader on facing. The top branch keeps the current column read and surface shading. The bottom branch runs the Snell-and-TIR logic from Recommendation A. Use the engine define pattern from issue #25149, `#ifdef FLIP_SIDED` for the back pass, so the branch is reliable on a transparent material.

Cost, estimated. `TwoPassDoubleSide` doubles the draw calls for this one transparent mesh, back face first then front face, per PR #21967. That is one extra draw call for a single mesh, with the back pass only producing visible pixels when submerged. Vertex work is paid twice for the water plane, roughly the same 65k vertices again, so this is slightly cheaper than Recommendation A in memory and slightly more entangled in code. I estimate it within the same sub-0.3 ms band on desktop. Estimated, not measured.

Risk. Overloading one shader with both a top-down column read and a from-below cone makes the file harder to reason about and couples the W4 underwater work to the live `depthWater.ts` that other waves also depend on. Recommendation A keeps the underside in its own W4-owned module, which fits the charter's one-file-one-owner and avoids touching `depthWater.ts` in research-adjacent build work.

### Why not plain DoubleSide

Plain `DoubleSide` on a transparent material gives the documented `gl_FrontFacing` ambiguity from issue #25149 and the forum reports that it does not produce the expected from-below refraction on its own. It is the option to avoid.

## 4. Frame-budget impact

The depth pre-pass already costs one full scene render, set up at `depthWater.ts` lines 375 to 383 in `renderDepthPrepass`. The 60fps desktop budget is about 16.6 ms per frame and the 30fps laptop budget is about 33.3 ms. Neither recommendation here adds a second full-scene pass, which is the expensive thing. Both add at most a second draw of the water plane and a small amount of fragment ALU, and only while the eye is below the waterline.

DoubleSide versus a second material. A second material on a flipped twin plane, Recommendation A, costs one more mesh and one more draw call, and its vertex and fragment work is skippable by toggling `mesh.visible` based on camera Y so it is free above water. `TwoPassDoubleSide`, Recommendation B, costs one extra draw call on the existing mesh and pays the water vertex shader twice whenever the material is double-sided, which is harder to skip cleanly above water without flipping back to `FrontSide` on the crossing. For that reason Recommendation A is the cheaper steady-state choice above water and the easier one to gate.

Extra pass. Neither recommendation requires a new render target if the Snell disc samples the existing sky color uniform and the TIR mirror reuses the WFX-R08 in-scatter color. A physically refracted above-water image inside the disc would need a render-to-texture of the scene without water, per the forum thread, which is a second pass and a real cost. I recommend deferring true refraction inside the disc to a later option and shipping the modeled disc first, because in turbid Salish water the disc is dim and soft and a crude sky-colored disc reads correctly.

All numbers in this section are estimates derived from the structure of the code. WFX-R13 owns the measured frame-time A/B.

## 5. Collision and sequencing

W4 underwater module. The charter assigns `web/lib/scene/underwater/` to W4 and the volumetrics definition to WFX-R08. The surface-from-below underside material must live in that W4 module and consume the WFX-R08 in-scatter color and attenuation as uniforms, so the Snell disc and the TIR mirror share one turbid-green palette with the surrounding volume. There must be no separate color story for the surface versus the volume, or the waterline will read as a seam. WFX-R12 defines the surface piece. WFX-R08 defines the volume piece. They share uniforms.

water2 collision. Recommendation A adds a sibling mesh and does not edit `depthWater.ts`, which is the lighter collision footprint. Recommendation B edits the `depthWater.ts` material side and fragment shader directly, which collides with any other wave touching that file, including WFX-R09 RGB absorption and WFX-R10 seabed interaction that both rewrite the same fragment shader. O0 should prefer Recommendation A if more than one wave needs `depthWater.ts` in the same build window.

transition.ts continuity, no pop at the crossing. The no-pop requirement is a continuity contract between four things at the instant the eye crosses scene Y equal to the water level. First, the underside material turns visible exactly as the topside stops being front-facing, so there is never a frame with no surface. With Recommendation A this is a `mesh.visible` toggle keyed on camera Y against `uWaterLevel`. With Recommendation B the single double-sided mesh handles both sides automatically, which is its one continuity advantage. Second, the fog must be continuous. `rollInFog` in `transition.ts` should be driven to its submerged target as the crossing completes so the above-water haze eases into the underwater turbidity fog without a step. Third, the lighting must be continuous. `descentLighting` already eases lights toward the sea-haze tint and dimmer intensity, which is the right direction for going under, so the W4 dive should continue that same tween past the surface rather than starting a new one at the crossing. Fourth, the underwater volumetric tint from WFX-R08 must start from the same color the surface Fresnel and fog were approaching, so the boundary value matches on both sides. The practical rule for W4 is to make the crossing a single continuous parameter from above to below, not two states with a switch, and to drive the existing `transition.ts` tweens through the crossing rather than around it.

Sequencing. WFX-R12 is research only and edits no code. The build of the underside material is W4 work gated on O0, and it depends on WFX-R08 fixing the in-scatter color and on the camera no-dunk clamp at `director.ts` line 52 being relaxed or replaced by a dive mode. Until that clamp changes, the underside material is never reached, so the underside build and the clamp change must land together or the feature is dead code.

## 6. Open questions for O0

1. Does O0 want an actual dive in this program, given the hard no-dunk clamp at `director.ts` line 52. The whole surface-from-below topic is latent until that clamp is relaxed or a dedicated dive mode replaces it. If diving stays out of scope, this work is deferred, not built.

2. Recommendation A second material versus Recommendation B TwoPassDoubleSide. A is the cleaner W4-owned module and the cheaper above-water steady state, B is the simplest continuity at the crossing. O0 should pick one before W4 starts so the underwater module owner does not build both.

3. How real should the Snell disc be. The cheap modeled disc samples a sky color uniform and needs no extra pass. A physically refracted above-water image inside the disc needs a scene-without-water render target, which is a second pass and a measured cost WFX-R13 must sign off. My recommendation is to ship the modeled disc first given turbid Salish water hides the detail.

4. Who owns the crossing continuity. The no-pop contract spans `transition.ts`, the camera dive in `director.ts`, the WFX-R08 volume, and the WFX-R12 surface. This crosses several wave owners and the `SalishScene.tsx` convergence file. O0 should name one integrator for the crossing so the four pieces are tuned against one another rather than separately.
