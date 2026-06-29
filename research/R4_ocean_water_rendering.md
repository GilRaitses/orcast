# R4 ocean and water rendering brief

Agent R4, terrain plus bathymetry 3D twin research spike.
Scope: real-time ocean surface rendering, reflection and refraction, and the rules that let a water plane and terrain coexist correctly in one scene. Read-only. No code edits.

Stack under study: Next.js, react-three-fiber, three@0.169, 3d-tiles-renderer@0.4.28. Current water is a sum-of-four Gerstner waves in `web/app/components/scene/realism/water.ts`, a `PlaneGeometry(192, 144, 160, 160)` `ShaderMaterial` at scene Y 0 with `transparent: true`, `depthWrite: false`, `renderOrder: 1`, opacity 0.72.

---

## 1. Ocean surface techniques

### Current orcast Gerstner approach

The existing shader sums four Gerstner waves with hardcoded direction, wavelength, and steepness, derives analytic normals from the wave partials, and shades with Fresnel plus Blinn-Phong sun specular. This is the classic GPU Gems 1 Chapter 1 method, "Effective Water Simulation from Physical Models" by Mark Finch and Cyan Worlds, NVIDIA GPU Gems 1, https://developer.nvidia.com/gpugems/gpugems/part-i-natural-effects/chapter-1-effective-water-simulation-physical-models . Gerstner waves move surface points in circular orbits, sharpen crests and flatten troughs, and give correct analytic normals for free, which is exactly what the current shader does.

Strengths of the current code. Cheap, no render targets, deterministic, analytic normals, stable at any zoom. Good enough for a calm protocol surface seen from a tilted map camera.

Limits of four Gerstner waves. A small fixed sum looks repetitive and synthetic up close, lacks high-frequency capillary detail, cannot represent a broadband sea state, and tends to read as "rolling hills of water" rather than ocean. The amplitude here is 0.35 scene units with steepness up to 0.42, so the visible motion is gentle. There is no surface microdetail, no foam, no reflection, and the color is driven only by wave height, not by the water depth beneath each point.

### FFT ocean, the Tessendorf statistical model

The industry-standard alternative is the FFT spectral ocean from Jerry Tessendorf, "Simulating Ocean Water", SIGGRAPH course notes 2001, widely mirrored, for example https://people.computing.clemson.edu/~jtessen/reports/papers_files/coursenotes2004.pdf . A height field is built in the frequency domain from a statistical wave spectrum, evolved over time with the deep-water dispersion relation, and converted to a spatial displacement map with an inverse FFT each frame. Choppy crests come from a horizontal displacement term, and foam comes from the Jacobian of that displacement going negative.

Spectra. Tessendorf used the Phillips spectrum, parameterized only by wind speed and direction. Modern implementations prefer JONSWAP, which adds fetch length and a peak-sharpness factor so the same code can render calm water through storm swell. See the DirectX 12 FFT writeup by Timethy Hyman, https://timethy.com/blog/fft-ocean-rendering/ , and George Bolba, "Oceans: Theory to Implementation", https://www.gikster.dev/posts/Ocean-Simulation/ . Both note the Phillips spectrum produces corner artifacts that JONSWAP avoids.

Cost and feasibility on this stack. FFT oceans are normally implemented with GPU compute shaders running the Cooley-Tukey butterfly on 256x256 or 512x512 RGBA16F textures for height, slope, and Jacobian. WebGL2 and three@0.169 have no compute shaders, so an FFT ocean on this stack would need either a fragment-shader ping-pong FFT, which is doable but heavy, or a move to WebGPU and three's TSL node path. The Tidewater engine demonstrates a production three.js FFT ocean that runs IFFT cascades in WebGPU with a WebGL2 TSL fallback, https://gettidewater.com/ , and a WebGPU-from-scratch walkthrough is at Barth Paleologue, https://barthpaleologue.github.io/Blog/posts/ocean-simulation-webgpu/ .

Tradeoff verdict for orcast. A full FFT ocean is more fidelity than a tilted geospatial twin needs, and it is a large lift on WebGL2. The cheaper and higher-value upgrade to the existing Gerstner surface is to add scrolling normal-map detail on top of the analytic Gerstner normals, the same pattern three's stock `Water` uses with a tiling `waterNormals` texture, https://threejs.org/docs/pages/Water.html . That buys broadband surface texture at near-zero cost without changing the geometry math.

---

## 2. Reflections and refraction

Options ranked by cost on WebGL2.

- Environment-map and IBL reflection. Sample a cubemap or the scene IBL through a Fresnel term. Cheapest, fully static or slowly updated, no extra scene passes. Good for sky color in the water. This is most of what sells a calm ocean and is what the current Fresnel-to-sky mix already approximates. Reference, the FidelityFX SSSR notes use an environment cubemap as the SSR fallback, https://interplayoflight.wordpress.com/2022/09/28/notes-on-screenspace-reflections-with-fidelityfx-sssr/ .
- Planar reflection. Render the scene a second time mirrored across the water plane into a render target, then sample it. This is what three's `Water` and `Water2` do through the `Reflector` and `Refractor` helpers, https://discourse.threejs.org/t/water2-scene-resolution/29578 . Quality is high for a flat plane, cost is one extra scene render per reflective plane at the render-target resolution, set by `textureWidth` and `textureHeight`, default 512. For a single sea-level plane this is affordable and is the standard three.js answer.
- Screen-space reflection, SSR. Ray-march the existing depth and color buffers to find reflected color, falling back to an environment map on a miss. High quality for in-screen geometry, but it needs a depth and normal prepass, it costs many texture samples per pixel, and it misses anything off-screen or behind the camera. Joost van Dongen reports roughly 37 samples per pixel over a short ray budget in Blightbound, http://joostdevblog.blogspot.com/2020/10/screen-space-reflections-in-blightbound.html , and 3D Game Shaders For Beginners documents the ray-march and its failure cases, https://lettier.github.io/3d-game-shaders-for-beginners/screen-space-reflection.html . SSR is the most expensive option and is poorly matched to a single flat plane where planar reflection is exact and cheaper.
- Depth-based refraction. Sample the scene color buffer with a UV offset driven by the surface normal and the water depth, so the seabed appears bent under the surface. Combined with a depth-difference read this also drives water transparency and color. This is the technique used in the SSR water writeup at Enigma Realm, https://blog.caiziii.com/blog/blog-screen-space-reflection-water/ , and is the standard "fake" refraction in most real-time water.

Verdict for orcast. Skip SSR. For a flat sea-level plane, planar reflection through three's `Water` is the highest quality-per-cost reflection, and an IBL or sky-cubemap Fresnel is the cheapest acceptable one. Refraction should be done as a depth-buffer offset, not as a re-rendered refractor, because the value here is depth-driven water color over the bathymetry, not glass-like bending.

---

## 3. Water and terrain interaction, the core failure mode

The spike trigger is that "water is always present but the land renders inconsistently and vanishes." The water shader is the prime suspect, and the mechanism is transparency depth handling.

### Why a transparent plane with depthWrite false can paint over terrain

In WebGL the depth buffer resolves opaque occlusion. Transparent objects do not write depth, so three.js renders them after opaque objects, sorted back-to-front by object center distance, and the result is order-dependent and approximate. The three.js forum and StackOverflow consensus is explicit that this is not a bug, it is how the z-buffer plus alpha blending works, and that intersecting geometry cannot be sorted robustly by center distance, https://stackoverflow.com/questions/11165345/three-js-webgl-transparent-planes-hiding-other-planes-behind-them and https://discourse.threejs.org/t/png-texture-not-rendering-correctly-with-meshbasicmaterial-depending-on-the-camera-position/71043 .

The current water mesh sets `transparent: true`, `depthWrite: false`, and `renderOrder: 1`. That combination produces several distinct failure modes that match "land vanishes" exactly.

1. Sort ambiguity at coincident depth. The water sits at Y 0 and the shoreline terrain also passes through Y 0. When the water plane center and a terrain tile are at similar camera distance, three's transparent sort order flips as the camera moves, so the same shoreline pixel is sometimes water-over-land and sometimes land-over-water. This reads as land flickering in and out, the classic symptom in the forum threads above.

2. renderOrder forcing water last. `renderOrder: 1` forces the water to draw after default-order geometry. If any terrain is itself transparent or shares the transparent queue, the forced order can make the water blend on top of terrain that should occlude it. Forcing the opposite, terrain at a low renderOrder and water higher, is the documented fix only for cleanly stacked planes, not for intersecting ones, https://discourse.threejs.org/t/transparency-not-working-right/34325 .

3. A big plane occluding tiles in the transparent pass. The water plane is 192 by 144 scene units, larger than the study area. With `depthWrite: false` it does not occlude opaque terrain through the depth buffer, but it does cover the whole frame with a 0.72-to-near-1.0 alpha. Where the seabed or island is below or near Y 0, the opaque terrain is drawn first and correct, then the full-frame translucent water is blended over all of it including land that rises only slightly above sea level, so low terrain is washed out toward the water color and reads as "gone". Island tiles that have not finished streaming, the 3d-tiles-renderer LoD concern owned by R1, leave only the water visible in that region, which is the literal "water present, land absent" report.

4. Plane above terrain due to datum or Y offset. If the baked tiles are not yet at the 0 m NAVD88 contour, per the charter the Y 0 alignment lands only after Wave 2, then the flat water plane can sit above terrain that should be dry land, and the translucent plane covers it. This is a scene-graph alignment bug, not a shader bug, but it presents identically.

There is also a known three.js interaction worth flagging. `THREE.Water` reflections break when any object with `depthWrite: false` is in the frustum, mrdoob/three.js issue 13287, https://github.com/mrdoob/three.js/issues/13287 . If orcast later adopts `Water`, the current `depthWrite: false` water plane itself would corrupt those reflections.

### Depth-based water color from terrain depth

The correct way to color water over real bathymetry is not wave height, which the current shader uses, but the water column depth. Read the opaque-only depth buffer, compute the distance from the water surface to the seabed below each pixel, and use that to drive both alpha and a shallow-to-deep color ramp. Shallow water near shore becomes transparent and reveals the seabed, deep water becomes opaque and dark. The Enigma Realm writeup describes exactly this, reading an opaque-only depth texture to compute water-to-seabed distance and using it for a depth-based alpha and a Beer-Lambert color falloff, https://blog.caiziii.com/blog/blog-screen-space-reflection-water/ . This single change also fixes the "land washed out" problem, because near the coast the water goes transparent and the shoreline shows through instead of being painted over by a flat 0.72 alpha.

### Shoreline, wading, foam, and intersection

The same depth difference yields a shoreline mask. Where the water-to-seabed distance is near zero, the surface is meeting land, so blend in a foam texture and reduce alpha. This is the standard depth-driven foam line, documented in the depth-based water sources above. Crucially, depth-driven alpha is also implicit culling of thin shoreline water. Zero-depth water becomes nearly transparent and foam masks the seam, so no explicit CPU clipping of water against the coastline is required, per Enigma Realm. That directly addresses the wading and intersection cases where a flat plane otherwise clips hard through sloping terrain.

### Summary of the fix for coexistence

The land-vanishing report is best explained by transparent-plane sorting plus a flat full-frame alpha plus possible Y-datum misalignment. The robust fixes are, in order of value: drive water alpha and color from the depth-buffer water-column depth so shallow and dry areas stop being painted over, confirm the water plane Y matches the 0 m contour of the tiles, set `renderOrder` and depth state deliberately with terrain drawn opaque-first, and keep the plane no larger than the wet area or fade it out where depth is non-positive.

---

## 4. Underwater rendering

If the camera ever drops below the surface, or to sell shallow water from above, the standard real-time toolkit is:

- Exponential depth fog. Beer-Lambert color attenuation with distance, tinting toward deep blue-green and losing red first. Strata's underwater shader exposes exactly this as `uFogColor`, `uFogDensity`, `uAbsorptionColor`, and `uAbsorptionRate`, https://strata.game/shaders/volumetrics/ , and Tidewater frames it as directional Beer-Lambert absorption, https://gettidewater.com/ .
- Caustics. The aesthetics-driven GPU Gems 1 Chapter 2 method, "Rendering Water Caustics" by Juan Guardado and Daniel Sanchez-Crespo, NVIDIA, https://developer.nvidia.com/gpugems/gpugems/part-i-natural-effects/chapter-2-rendering-water-caustics , projects a caustic pattern onto the seabed. A more physical real-time WebGL and three.js approach that refracts light rays at the surface and accumulates convergence is Martin Renou, "Real-time rendering of water caustics", https://medium.com/@martinRenou/real-time-rendering-of-water-caustics-59cda1d74aa , building on Evan Wallace's WebGL water. A cheap version is just two scrolling samples of a caustics texture, minned together, masked by shallow depth.
- God rays, crepuscular shafts. Volumetric light scattering, either as a screen-space radial blur from the sun or as raymarched shafts with additive blending. Noted as the natural companion to caustics in GPU Gems 1 Chapter 2 and shipped as screen-space god rays in Tidewater.
- Surface from below. Snell's window and total internal reflection past the critical angle near 49 degrees, called out as a feature in Tidewater. This only matters if orcast ever goes fully submerged, which is not the current map use case.

For orcast the realistic near-term subset is exponential depth tint plus an optional cheap caustics texture on the seabed in shallow zones. Full god rays and Snell's window are out of scope for a tilted map view.

---

## 5. WebGL and three.js specifics

- `three/addons/objects/Water.js`, `THREE.Water`. Flat reflective plane using a planar `Reflector`, takes a tiling `waterNormals` texture, sun direction, sun color, water color, and `distortionScale`. WebGLRenderer only. WebGPU uses `WaterMesh`. https://threejs.org/docs/pages/Water.html . This is the closest drop-in upgrade to the current hand-written shader and gives planar sky and scene reflection plus normal-map detail with little code.
- `three/addons/objects/Water2.js`, flowing water using both `Reflector` and `Refractor`, controlled by `textureWidth`, `textureHeight`, `flowDirection`, `scale`, `color`. Intended for flat surfaces only, and its refractor produces edge artifacts on non-trivial or curved geometry, per the three.js forum, https://discourse.threejs.org/t/the-refraction-effect-of-water2-is-not-ideal-enough/28845 and https://stackoverflow.com/questions/49945509/threejs-water2-changing-reflection-state .
- Known shader patterns. Depth-buffer reads for refraction, depth-difference for transparency and foam, normal-map scroll for microdetail, Fresnel-to-environment for reflection. All are WebGL2-friendly and need at most a depth prepass, not compute.
- react-three-fiber and drei. drei does not ship a first-class water helper, so projects typically wrap `THREE.Water` in an r3f component or hand-write a shader, which is what orcast already does. The depth-buffer reads need r3f to expose the scene depth texture, available via a render target or `gl.depthTexture` patterns.
- References. GPU Gems 1 Chapter 1 Gerstner water (the current method) and Chapter 2 caustics, both linked above. Tessendorf 2001 for FFT ocean. Eric Bruneton's water and atmosphere work is the deeper physical reference for ocean BRDF and aerial perspective if higher fidelity is ever needed. Recent practical real-time references are the FFT writeups by Hyman and Bolba, the WebGPU implementation by Paleologue, and the Tidewater three.js engine for a production WebGPU plus WebGL2 path.

---

## Implications for orcast

Is the Gerstner approach adequate? For a tilted geospatial map twin, yes, the four-wave Gerstner surface is adequate as the surface motion model and should be kept. It is cheap, stable, and analytic. It is not the cause of the land-vanishing bug. A full FFT ocean is not justified on WebGL2 and would be a large rewrite for fidelity this view does not need.

What to fix about water and terrain coexistence, in priority order.

1. Color and alpha by water-column depth, not wave height. Read the opaque depth buffer, compute surface-to-seabed distance, and drive alpha and a shallow-to-deep ramp from it. Shallow and dry areas then go transparent instead of being painted over by the flat 0.72 alpha. This is the single change that most directly stops "water present, land absent".
2. Fix scene-graph alignment. Confirm the water plane Y equals the 0 m NAVD88 contour of the baked tiles, and fade or clip the plane where computed depth is non-positive so it never covers land. Coordinate with R1 on tile streaming and LoD, since missing tiles also leave only water visible.
3. Make depth and draw order deliberate. Keep terrain opaque and drawn first. Reconsider `renderOrder: 1` and `depthWrite: false` together. With depth-based alpha the plane can stop covering dry terrain regardless of sort order, which removes the camera-angle flicker.
4. Add a shoreline foam line from the same depth difference, which doubles as implicit culling of thin coastal water.

Recommended reflection and refraction within a 60fps budget. Use an environment or sky-cubemap Fresnel reflection as the default, cheap path. If a real mirror is wanted, adopt three's `Water` planar `Reflector` at a modest `textureWidth` near 512, since a single flat sea-level plane is the exact case it is built for, at the cost of one extra scene pass. Do refraction as a depth-buffer UV offset, reusing the same depth read as the color and foam, rather than a second refractor pass. Explicitly avoid SSR here, it is the most expensive option, it fails off-screen, and planar reflection is both cheaper and exact for a flat plane. Note that if `Water` is adopted, the current `depthWrite: false` plane must change, because depthWrite-false objects in frustum corrupt `Water` reflections, three.js issue 13287.
