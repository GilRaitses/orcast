# WFX-R02 wave spectrum vs hand-tuned Gerstner

Agent WFX-R02, WATER-FX lane, Wave 1 research, read-only. One findings doc.
Topic. Whether to replace or augment the hand-tuned six-wave Gerstner sum in
`web/lib/scene/water2/depthWater.ts` with an oceanographic spectrum such as
Pierson-Moskowitz or JONSWAP, or with an FFT Tessendorf ocean, feasible on
`three`. The controlling fact is that the Salish Sea is a sheltered inland sea
with short fetch and small chop, not open tropical swell.

Honesty label. Modeled, not measured. Any wave model here changes how the
surface looks. It asserts no measured sea state.

---

## 1. Scope and current state, file-cited

The surface displacement lives in the vertex shader of
`web/lib/scene/water2/depthWater.ts`. It is a sum of six Gerstner waves with
hardcoded direction, wavelength, and steepness, declared at lines 126 to 131.

```126:131:web/lib/scene/water2/depthWater.ts
  const vec4 W0 = vec4( 1.0,  0.35, 18.0, 0.42);
  const vec4 W1 = vec4(-0.6,  1.0,  11.0, 0.34);
  const vec4 W2 = vec4( 0.8, -0.7,  6.5,  0.28);
  const vec4 W3 = vec4(-0.2, -1.0,  3.3,  0.20);
  const vec4 W4 = vec4( 0.5,  0.9,  2.1,  0.16);
  const vec4 W5 = vec4(-0.9,  0.2,  1.3,  0.12);
```

Each component uses deep-water dispersion. In the `gerstner` helper at lines 133
to 153 the wavenumber is `k = 2*pi / wavelength`, the phase speed is
`c = sqrt(9.8 / k)`, and the per-wave amplitude is `a = amp / k`. Analytic
normals are accumulated from the wave partials, so the fragment shader gets a
correct surface normal for free. The six waves are summed at lines 163 to 168
with a falling amplitude ladder from `uAmplitude` down to `uAmplitude * 0.18`.
The peak amplitude default is `0.32` scene units, set at line 335. The plane is
`PlaneGeometry(width, depth, segments, segments)` at line 309, with defaults
`width = 192`, `depth = 144`, `segments = 180` from lines 304 to 306. The mesh
is authored in XY then rotated to lie in XZ at line 360.

Prior in-repo art. `research/R4_ocean_water_rendering.md` already surveyed ocean
surface rendering for the twin and concluded that a four-wave Gerstner surface is
adequate for a tilted geospatial map and that a full FFT ocean is not justified
on WebGL2. That doc predates the water2 rewrite and described a four-wave v1 in
`web/app/components/scene/realism/water.ts`. This finding revisits the same
question against the current six-wave water2 surface and against the Salish Sea
fetch specifically.

Scene frame. `web/lib/sceneIntent.ts` sets `SCENE_WIDTH = 120` at line 57 and
`HEIGHT_SCALE = 0.04` metres per scene unit at line 65. The water plane width is
wired as `SCENE_WIDTH * 1.6 = 192` and depth `sceneDepth * 1.6` per
`web/app/components/scene/realism/WIRING-realism.md` lines 51 and 126. These two
scales are the heart of the recommendation below and are worked out in section 3.

---

## 2. Technique survey with URLs

### Gerstner sum, the current method

Gerstner or trochoidal waves move surface points in circular orbits, sharpen
crests, flatten troughs, and yield analytic normals. This is GPU Gems 1
Chapter 1, Mark Finch and Cyan Worlds, "Effective Water Simulation from
Physical Models",
https://developer.nvidia.com/gpugems/gpugems/part-i-natural-effects/chapter-1-effective-water-simulation-physical-models
. A small fixed sum is cheap, deterministic, stable at any zoom, and needs no
render targets. Its weakness is that a handful of fixed components reads
repetitive and synthetic up close and cannot carry a broadband sea state.

### Pierson-Moskowitz and JONSWAP spectra

Pierson-Moskowitz describes a fully developed open-ocean sea, parameterized by
wind speed alone. JONSWAP extends it with a fetch length and a peak-sharpness
factor gamma, so it represents a fetch-limited growing sea, which is exactly the
Salish Sea case. Frechot, "Realistic simulation of ocean surface using wave
spectra", gives the spectra and, more usefully, a method to sample a spectrum
into a finite set of wave amplitudes, frequencies, and directions that preserve
the spectral energy, suitable for both Gerstner sums and FFT,
https://hal.science/hal-00307938v1/file/frechot_realistic_simulation_of_ocean_surface_using_wave_spectra.pdf
. Frechot states plainly that for a fetch-limited sea JONSWAP is more
appropriate than Pierson-Moskowitz.

### Spectrum-seeded Gerstner

The spectrum is not exclusive to FFT. The standard middle path is to
importance-sample a JONSWAP spectrum into N discrete Gerstner components, so the
wave directions, wavelengths, and amplitudes are physically grounded by a chosen
wind and fetch while the renderer still just sums Gerstner waves. An Unreal
developer thread documents exactly this, JONSWAP feeding Gerstner parameters
from wind speed and fetch, with the author summing 170 waves and noting the
count can drop a lot while still looking good,
https://forums.unrealengine.com/t/physical-ocean-surface-developing-a-realistic-water-shader/29314
. Frechot above is the academic basis for the sampling step.

### FFT Tessendorf ocean

The industry-standard high-fidelity model is the FFT spectral ocean from Jerry
Tessendorf, "Simulating Ocean Water", SIGGRAPH 2001 course notes,
https://people.computing.clemson.edu/~jtessen/reports/papers_files/coursenotes2004.pdf
. A height field is built in the frequency domain from a statistical spectrum,
evolved with the dispersion relation, and inverse-transformed to a spatial
displacement map each frame. Choppy crests come from a horizontal displacement
term, foam from the Jacobian of that displacement going negative. A current,
clear walkthrough is Robert Ryan, "Ocean Rendering, Part 1, Simulation", 2025,
https://rtryan98.github.io/2025/10/04/ocean-rendering-part-1.html
, which states the key point for this decision. The result of an FFT ocean is
the same as summing more Gerstner waves than a GPU can sum in one frame. FFT
buys breadth of the spectrum, not a different look at low component counts.

### FFT on this stack

Production FFT oceans run the Cooley-Tukey butterfly in compute shaders on
256x256 or 512x512 float textures. WebGL2 and `three` r0.169 have no compute
shaders. A reference WebGPU implementation that seeds h0 from a JONSWAP
directional model and runs a 2D IFFT via the butterfly in 16x16 workgroups is
Majkejl/fft_water_sim, https://github.com/Majkejl/fft_water_sim , which confirms
the normal home for this technique is WebGPU compute, not WebGL2. The
three-side production path is the Tidewater engine, which runs IFFT cascades in
WebGPU with a WebGL2 TSL fallback, https://gettidewater.com/ . On the current
WebGL2 renderer an FFT would have to be a fragment-shader ping-pong, which is
doable and heavy, costed in section 4.

### Choppiness

Gerstner already produces choppy crests through its horizontal orbit term,
controlled here by the steepness field of each `Wn`. The same crest-pinching in
FFT comes from the separate horizontal displacement term. Choppiness is not a
reason to move to FFT. The current shader already has the lever, it is the
fourth component of each `Wn` vec4.

---

## 3. Salish Sea scale, the controlling argument

The Salish Sea is a sheltered inland sea, not open ocean. The Strait of Georgia
is a roughly 250 km by 25 to 50 km enclosed strait whose sea state is dominated
by locally generated wind-sea, fetch-limited by islands and mountainous terrain,
not by Pacific swell. Gemmrich and Dewey, EGU 2017, report a median significant
wave height Hs of 0.3 m, with strong mountain outflows able to push Hs above
2.5 m,
https://meetingorganizer.copernicus.org/EGU2017/EGU2017-3802.pdf
. Yang et al 2019 model the whole Salish Sea and find the Strait of Juan de
Fuca largest and swell-dominated, the Strait of Georgia wind-sea dominated, and
Puget Sound small, with the modeled maximum Hs in the Strait of Georgia rising
from about 2.68 m in the south to 4.08 m in the far north,
https://www.sciencedirect.com/science/article/abs/pii/S0272771419301556
. A historical DFO record put significant wave heights never above about 2.1 to
2.7 m at exposed Strait of Georgia banks over multi-month observation, and below
0.3 m most of the time in protected inlets,
https://waves-vagues.dfo-mpo.gc.ca/Library/487-14.pdf
. The honest target for the twin is a calm sea most of the time, Hs near 0.3 m,
with wavelengths and periods of a short fetch-limited wind-sea, not long ocean
swell.

Now the scene scale, which is decisive. Vertical is exact from the code.
`HEIGHT_SCALE = 0.04` means 1 scene unit equals 25 m of real height. Horizontal
is estimated. `SCENE_WIDTH = 120` units spans the modeled longitude extent. Using
the repo's own constant of 73.6 km per degree of longitude at 48.5 N from
`sceneDepth` in `web/lib/sceneIntent.ts` and the Orcasound modeled footprint of
about 0.84 degrees of longitude, 120 units spans roughly 62 km, so one scene
unit is about 0.52 km horizontally. This is labeled estimated because the true
heightmap bounds may differ from the Orcasound node footprint. See open question 4.

Two consequences fall straight out of those two scales.

Vertical exaggeration is about twentyfold. Horizontal is about 520 m per unit
and vertical is 25 m per unit, a ratio near 20.8. The frame is a vertically
exaggerated relief map, not a metric box.

Real waves are far smaller than one mesh quad. The mesh quad edge is
`192 / 180 = 1.067` units east-west and `144 / 180 = 0.80` units north-south, so
about 0.55 km per quad. A real Salish wind wave has a wavelength on the order of
3 to 30 m, which is 0.006 to 0.06 scene units, one to two orders of magnitude
smaller than a single quad. Real wave geometry cannot be carried by this mesh at
all. It can only ever be a surface-normal detail in the fragment shader.

The current Gerstner constants confirm the geometry is decorative, not metric.
The wavelengths run from `W0` at 18 units, about 9.4 km, down to `W5` at 1.3
units, about 0.68 km. The per-wave vertical amplitude is `a = amp / k`. For `W0`
that is `0.32 / (2*pi/18) = 0.92` units, about 23 m of vertical-equivalent
height, and the summed crest of all six can reach about 1.67 units, about 42 m.
Against a real median Hs of 0.3 m this geometry is one to two orders of
magnitude too tall in metric terms. It only reads calm because the wavelengths
are kilometers, so the visible slope of `W0` is only about 5 percent. The
surface looks like long gentle hills, which is what `R4_ocean_water_rendering.md`
already called "rolling hills of water".

A second, separable defect is aliasing. Faithful sampling needs at least two
quads per wavelength, about 2.13 units here. `W5` at 1.3 units and `W4` at 2.1
units sit below or at that Nyquist limit and `W3` at 3.3 units is marginal.
These short components shimmer and crawl as the camera moves, which is a likely
contributor to the "distracting" read alongside the specular and glitter that
WFX-R01 owns. The fix is to stop trying to represent sub-quad waves as geometry.

---

## 4. Recommendation, cost, and three-only fallback

### Primary recommendation, keep Gerstner, retune for short fetch, push detail to a normal map

Do not adopt FFT. Keep the Gerstner sum and change it in three ways.

1. Drop the sub-Nyquist components `W4` and `W5` from the geometry and move that
energy into a fragment-shader detail normal. Keep three to four long components
for a gentle large-scale heave that the mesh can actually represent.

2. Lower amplitude and steepness to a sheltered sea. Reduce the `uAmplitude`
default from `0.32` toward `0.10` to `0.15`, and cap the per-wave steepness from
`0.42` toward `0.15` to `0.20`. This matches small fetch-limited chop rather than
storm swell, and it removes the crest-pinching that high steepness summed across
six waves can push into self-intersection.

3. Seed the surviving wave constants from a JONSWAP table for a chosen wind and
fetch, per Frechot and the Unreal thread in section 2, so the directions,
wavelengths, and amplitudes are physically grounded rather than hand-picked,
even though the renderer still sums a small Gerstner set. This is a one-time
offline computation that emits the same `vec4 Wn` constants the shader already
uses, so it costs nothing at runtime.

For the fine wind texture that the mesh cannot carry, add a tiling detail normal
map sampled with two scrolling UV layers in the fragment shader and blended into
`vWorldNormal` before the Fresnel and specular terms. This is the same pattern
three's stock `Water` uses with its `waterNormals` texture,
https://threejs.org/docs/pages/Water.html .

Cost of the primary recommendation. Zero added render passes. The vertex stage
gets cheaper because there are fewer Gerstner components. The fragment stage adds
two texture samples per pixel for the normal map plus a normal blend, a handful
of ALU and two texture fetches, which is negligible against the existing depth
pre-pass that re-renders the whole terrain scene. Estimated, not measured. The
only new artifact is one small tiling normal-map texture in the bundle, on the
order of tens to a few hundred KB depending on resolution and KTX2 compression.

### Three-only fallback, no texture asset

If O0 does not want to add a texture asset to the bundle, the detail normal can
be generated procedurally in the fragment shader from the value-noise function
that already exists in `depthWater.ts` at lines 211 to 223. Perturb the normal by
the gradient of two scrolling octaves of that noise. This trades a few extra ALU
per pixel for zero asset bytes and stays purely on `three` with no new
dependency. It is slightly noisier in appearance than a hand-authored normal map
but is fully self-contained. Both the primary path and this fallback are
`three`-only. The only path that adds a dependency is FFT, addressed next.

### When FFT would be justified, and its cost

FFT is justified only if a future camera flies down to sea level for a close-up
broadband ocean look, which the current tilted-map twin does not do. See open
question 1. Even then, prefer migrating to `WebGPURenderer` and the TSL node
path over a WebGL2 ping-pong, because the technique's natural home is compute,
per Majkejl and Tidewater in section 2. A WebGPU migration is a hard
architecture change to the whole renderer, not a local water edit, and is an O0
decision.

A WebGL2 fragment ping-pong FFT, if forced, is costed in section 5. It is not
recommended.

---

## 5. Frame-budget impact

Current vertex and segment cost at the 180 by 180 plane.

- Vertices `181 * 181 = 32,761`. Triangles `180 * 180 * 2 = 64,800`. Indices
  194,400. From `PlaneGeometry(192, 144, 180, 180)` at line 309 of
  `depthWater.ts`.
- Per vertex the shader runs six `gerstner` calls, each with one `sin`, one
  `cos`, a `normalize`, a `sqrt`, and a few multiplies. That is on the order of
  196,000 transcendental evaluations per frame for the water vertex stage, about
  11.8 million per second at 60 fps. This is negligible on a desktop GPU and
  small on a weak laptop integrated GPU. Estimated, not measured. The dominant
  water cost is not the vertices, it is the depth pre-pass that re-renders the
  opaque scene, set up in `renderDepthPrepass` at lines 375 to 383.

Primary recommendation impact. Fewer Gerstner components lowers the vertex cost
below the current figure. The fragment adds two normal-map texture samples per
pixel. No extra passes. Net change is within the 60 fps desktop and 30 fps
laptop budget with margin. Estimated.

FFT impact, for the record. A WebGL2 fragment ping-pong IFFT at N equal to 256
needs a spectrum-update pass, `2 * log2(256) = 16` butterfly passes for the 2D
transform, a transpose or permutation, and a normal and Jacobian assembly pass,
roughly 18 to 22 full-screen passes at 256 by 256 per frame for a single
cascade. A convincing sea wants two to four cascades to span swell and chop,
which multiplies to roughly 40 to 80 passes per frame, each a render-target bind
and draw with RGBA16F bandwidth. Set against a budget where the depth pre-pass
already spends one full terrain render, this is a large addition for fidelity
this tilted-map view cannot even display at 0.55 km quads. Estimated, not
measured. This is the adversarial cross-check WFX-R13 should confirm in the
full-stack accounting.

---

## 6. Collision and sequencing

This finding feeds the twin's W3 water-upgrade and any WFX-BUILD water module.
All proposed changes are local to the vertex and fragment shaders and the
`makeWater2` options in `web/lib/scene/water2/depthWater.ts`. No edit to
`web/app/components/scene/SalishScene.tsx` in research, and none required by the
primary recommendation beyond passing a tuned `amplitude` and a normal-map
option through the existing `Water2Options` interface at lines 34 to 76.

Ordering against sibling research.

- WFX-R01 surface BRDF consumes the surface normal that this shader produces.
  Retuning the wave set changes that normal, so the R02 wave retune and the R01
  specular and Fresnel rework must be sequenced and tuned together in the
  `/water` sandbox, not landed independently.
- WFX-R03 reflections also read the same normal for the Fresnel sky and scene
  reflection. The detail normal map proposed here improves the input to both R01
  and R03 at once.
- WFX-R09 RGB absorption is column-driven and independent of surface geometry,
  so it does not collide with this change.

Build-wave note. The detail normal map, if adopted as an asset, is a new file
under the water module, not a `SalishScene.tsx` edit, so it does not enter the
convergence-file serialization. The spectrum-seeding step is an offline script
that emits shader constants and does not run at runtime.

---

## 7. Open questions for O0

1. Is any sea-level free-fly or low close-up camera planned, or does the camera
   stay tilted-map-high? This is the single switch between the Gerstner plus
   normal-map recommendation and any future FFT case.
2. Approve adding one small tiling water normal-map texture to the bundle, or
   require the procedural-noise fallback that adds no asset?
3. Should wave parameters be exposed as wind and fetch inputs through a
   spectrum-seed, or stay as fixed constants retuned once for a calm Salish sea?
4. Confirm the true heightmap bounds so the horizontal scale per scene unit is
   exact rather than estimated from the Orcasound footprint. The 0.55 km quad and
   20x exaggeration figures depend on it, though the qualitative conclusion that
   real waves are sub-quad holds across any plausible bounds.
