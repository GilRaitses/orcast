# WFX-R09 per-channel RGB absorption, evaluate and extend

Lane WFX, Wave 1 research, read-only. Owner WFX-R09. Topic, evaluate and extend
the pending per-channel Beer-Lambert extinction request against real Jerlov
coastal and Salish Sea attenuation, decide the `uDepthColorScale` backward-compat
question, decide whether absorption drives alpha, and resolve the scene-unit to
meter conversion. This doc proposes math and coefficients. It changes no code.

Headline finding up front. The proposed coefficient vector `{r:3.0, g:1.6,
b:0.9}` encodes clear blue-ocean physics where red is absorbed fastest and blue
survives deepest. That is the wrong ordering for the Salish Sea. Measured Strait
of Georgia optics show blue and red are both attenuated fast and green survives
deepest, a green window. The extinction ordering for this scene should be blue
above red above green, not red above green above blue. The vector should be
re-balanced and the deep tint retargeted from navy toward turbid green. Details
and a backward-compatible shader form follow.

## 1. Scope and current state, file-cited

### The pending request, quoted

`web/lib/scene/bathy/style/WATER2_TUNING_REQUEST.md` asks the water2 owner to
replace the two-stop color lerp with a per-channel transmittance. The request
body, lines 30 to 42, states:

```glsl
// new uniform, inverse scene units per channel
uniform vec3 uAbsorption; // e.g. vec3(3.0, 1.6, 0.9), R fast .. B slow

// transmitted intrinsic water color, replacing the two-stop color lerp
vec3 transmittance = exp(-uAbsorption * column);
vec3 base = uColorShallow * transmittance + uColorDeep * (1.0 - transmittance);
```

The same file, lines 39 to 42, leaves the backward-compat lever open. Quote, the
single `uDepthColorScale` lever can stay for backward compatibility, applied as
an overall multiplier on `uAbsorption`, or be retired in favor of the per-channel
vector.

The starting coefficients live in `web/lib/scene/bathy/style/waterTuning.ts`
lines 55 to 59:

```ts
export const PROPOSED_RGB_EXTINCTION: { r: number; g: number; b: number } = {
  r: 3.0,
  g: 1.6,
  b: 0.9,
};
```

The stated rationale, `waterTuning.ts` lines 50 to 53 and the request lines 52 to
57, is that the deepest Haro Strait channel runs about 1.0 scene units below the
surface, so `r = 3.0` reaches about 95 percent extinction over that column while
`b = 0.9` retains about 70 percent, producing a deep navy and violet read.

### The current shader math, quoted

`web/lib/scene/water2/depthWater.ts` is the live fragment shader. The color and
alpha today, lines 255 to 260:

```glsl
// Beer-Lambert: color and alpha grow with column thickness.
float colorT = 1.0 - exp(-column / max(uDepthColorScale, 1e-4));
float depthAlpha = 1.0 - exp(-column / max(uDepthAlphaScale, 1e-4));
depthAlpha *= uMaxOpacity;

vec3 base = mix(uColorShallow, uColorDeep, colorT);
```

`column` is the vertical water-column thickness from the surface plane down to
the seabed, reconstructed from the opaque-scene depth pre-pass, lines 230 to 244.
Open water with no opaque geometry behind it is forced to `column = 50.0` so the
horizon reads solid, line 235. The final alpha blends the depth core with a
Fresnel rim and the foam line, line 291:

```glsl
float alpha = clamp(depthAlpha + fres * 0.18 + foam * 0.9, 0.0, 1.0);
```

Defaults that matter for tuning, `makeWater2` uniforms lines 341 to 345.
`uDepthColorScale` default `0.3`, `uDepthAlphaScale` default `0.3`,
`uMaxOpacity` default `0.96`. The WS-BATHY tuning in `waterTuning.ts`
`bathyWater2Options` overrides these to `depthColorScale 0.42`,
`depthAlphaScale 0.34`, `maxOpacity 0.95`, and sets `colorShallow #2f8fa6`,
`colorDeep #0b2140`, a navy. The current default deep is `#0a2540`, also navy,
`depthWater.ts` line 111.

### The datum and scale already wired

`web/app/components/scene/SalishScene.tsx` line 301 sets the water `level` to
`SEA_LEVEL_Y`, the W2.6 NAVD88 0 m datum mapped to scene Y 0. The live fit scale
is `worldUnitsPerMeter = fitRadius / geoRadiusMeters(TILESET_BOUNDS)`,
`SalishScene.tsx` line 549, reported at about `0.00242` units per meter in
`.cca/catalogue/O0/20260627_terrain-bathymetry-twin/research/RP2_view_scope.md`
line 46, and described as about `0.003` in the WATER-FX charter. One scene unit
is therefore about 333 to 413 meters of true depth. This is the crux of section
3 below.

## 2. Technique survey with sources

### Beer-Lambert and spectral transmittance

Beer-Lambert states transmittance falls exponentially with path length,
`T(lambda) = exp(-k(lambda) * d)`, where `k` is the wavelength-dependent
attenuation coefficient and `d` is path length. Per-channel RGB extinction is
the three-sample discretization of that law at representative red, green, and
blue wavelengths. The proposed `exp(-uAbsorption * column)` is exactly this form.
The physics is sound. What is wrong is the coefficient vector, not the equation.

### Pure water absorption, the clear-ocean baseline

Pure water absorption coefficients in inverse meters, Pope and Fry 1997
integrating-cavity data, mirrored at the Oregon Medical Laser Center, give the
canonical clear-water spectrum:

- 450 nm blue, 0.00922 m^-1
- 550 nm green, 0.0565 m^-1
- 650 nm red, 0.340 m^-1

Source https://omlc.org/spectra/water/abs/pope97.html and the data table
https://omlc.org/spectra/water/data/pope97.txt. Smith and Baker 1981 give a
close set, 0.0145, 0.0638, 0.349 m^-1 at the same wavelengths,
https://omlc.org/spectra/water/data/smith81.txt. The ratio red to green to blue
in pure water is roughly 37 to 6 to 1. Red is absorbed fastest and blue slowest.
This is why clear tropical open water reads deep blue, and this is the regime the
proposed `{3.0, 1.6, 0.9}` vector models, just gentler. That regime is correct
for clear water and wrong for the Salish Sea.

### Jerlov water types, the coastal classification

Jerlov 1968 and 1976 classify water by the spectral diffuse attenuation
coefficient `Kd`, five open-ocean types I, IA, IB, II, III and nine coastal types
1 to 9, with turbidity rising by class number. Ocean Optics Web Book,
https://oceanopticsbook.info/view/inherent-and-apparent-optical-properties/classification-schemes.
The key qualitative result for coastal types, from the same source, is that
turbidity from dissolved organic matter and particles raises short-wavelength
attenuation so the transmission peak shifts from blue toward green and yellow,
500 to 575 nm. Self-consistent inherent optical property tables for the Jerlov
types are given by Solonenko and Mobley 2015,
https://opg.optica.org/ao/abstract.cfm?uri=ao-54-17-5392, and measured
absorption and scattering for Jerlov IB to 5C by the World-wide Ocean Optics
Database study, https://doi.org/10.1364/ao.470464. The original tables are at 25
nm increments and require interpolation for exact RGB wavelengths, which is why
the measured regional data below is the better anchor.

### Salish Sea optics, the regional truth

Strait of Georgia underwater light field, McKee and others, FACETS 2018,
https://www.facetsjournal.com/doi/10.1139/facets-2017-0074. The decisive
sentence, quote, throughout the Strait, blue and red wavelengths are attenuated
most rapidly resulting in a green peak of reflectance, the portion of the
electromagnetic spectrum that penetrates the most deeply. Measured downwelling
attenuation `KEd` in the turbid Fraser-plume optical water mass OM1, Table 2 of
that paper, shows blue at 411 and 443 nm near `2.0` to `2.3` m^-1, green near 531
nm at the minimum near `0.68` m^-1, and red rising back to about `0.85` to `1.0`
m^-1. Reflectance is lowest at 400 to 450 nm purple-blue and peaks at 520 to 640
nm yellow-green. The plume meets or exceeds Jerlov coastal type 9 in the short
wavelengths. Blue and red 1 percent penetration is never deeper than about 9 m,
and below roughly 15 m only green light remains. The cause is high CDOM and
inorganic-particle scattering from the Fraser River.

The ordering this forces for the scene is unambiguous. Extinction is highest in
blue, next in red, lowest in green. Transmittance survives in green. The deep
read of Salish water is turbid green-grey going to dark olive-green, not navy and
not violet. WFX-R11 owns the canonical color targets and the final coefficient
numbers. This section supplies the ratio and the citation R11 can confirm or
refine.

## 3. Recommendations, exact shader and uniform extension

### 3a. Adopt the per-channel form, with a unit-normalized ratio and a scalar

Keep the request equation and keep `uDepthColorScale`. Make `uAbsorption` a
unit-normalized ratio vector where green equals 1, and let `uDepthColorScale`
remain the green-channel e-folding column length in scene units. This recovers
the exact current monochrome behavior when the vector is `vec3(1.0)`, so the
change is strictly backward compatible.

Proposed extended fragment-shader block, replacing `depthWater.ts` lines 256 and
260:

```glsl
// Per-channel Beer-Lambert. uAbsorption is a unit-normalized ratio (green = 1),
// uDepthColorScale is the green-channel e-folding column length in scene units.
// uAbsorption = vec3(1.0) reproduces the legacy monochrome colorT exactly.
vec3 k = uAbsorption / max(uDepthColorScale, 1e-4);
vec3 transmittance = exp(-k * column);
vec3 base = uColorShallow * transmittance + uColorDeep * (1.0 - transmittance);
```

New uniform, added beside the existing color uniforms in `makeWater2`:

```ts
uAbsorption: { value: new THREE.Vector3(2.6, 1.0, 3.0) }, // R, G, B ratio, green = 1
```

Cost. Two extra scalar `exp` per fragment over the current single `exp`, plus a
vec3 divide and a multiply-add. No new texture sample, no new uniform texture, no
new pass. Negligible, see section 4. Three-only note, this is a plain GLSL edit
to the existing `ShaderMaterial`, no dependency, and it is the native path. No
fallback is needed because the cost is already at the floor. A LUT-texture
alternative would be slower because it adds a sample.

### 3b. Recommended coefficients, with the scene-unit caveat

Anchor the ratio on the measured OM1 Strait of Georgia values, blue 2.0 to 2.3,
red 0.85 to 1.0, green 0.68 m^-1. Normalizing to green equals 1 gives roughly
blue 3.0 to 3.4, red 1.3 to 1.5, green 1.0. A defensible starting vector is

```ts
uAbsorption = vec3(/* R */ 1.4, /* G */ 1.0, /* B */ 3.0)
```

This makes green the long-survivor, blue fade fastest, red fade next, which is
the green-window the regional data shows. WFX-R11 should confirm or replace these
numbers. This is the opposite ordering from the pending `{r:3.0, g:1.6, b:0.9}`,
which keeps blue the survivor and is correct only for clear blue ocean.

The scene-unit caveat is not optional. The coefficient is per scene unit, but the
real `Kd` is per meter, and one scene unit is about 333 to 413 meters here. A
literal conversion, `k_scene = Kd_per_meter / worldUnitsPerMeter`, turns the
green `Kd` of `0.68` m^-1 into about `281` per scene unit. At that magnitude the
water reaches full body color within roughly one percent of a scene unit, a few
meters of real depth, which matches the physics that all light but green is gone
by 15 m, but which would render the entire visible column as flat opaque body
color with no gradient. The scene compresses hundreds of meters into one unit, so
literal per-meter extinction is unusable for the look. The honest resolution is
to keep the physically-grounded RATIO between channels, which carries the
truthful chromatic behavior, and treat the overall MAGNITUDE as a modeled look
control through `uDepthColorScale`. The ratio is physics. The magnitude is a
modeled choice. This sits exactly under the locked honesty label, modeled not
measured.

### 3c. Retarget the deep tint, coordinate with WS-BATHY

The transmittance form fades toward `uColorDeep` as the body color. With the
green-window ratio, `uColorDeep` should be a turbid dark green-grey to olive, not
the current navy `#0b2140` from `waterTuning.ts` line 35 or the default
`#0a2540` from `depthWater.ts` line 111. WS-BATHY owns those style constants and
the `PROPOSED_RGB_EXTINCTION` export, so the deep-tint retarget and the
coefficient re-balance must be agreed with the WS-BATHY style owner because they
reverse the stated navy and violet intent of the original request. WFX-R11
supplies the exact green target. Cost, none, it is a constant change.

### 3d. Backward-compat decision, keep uDepthColorScale

Keep it, do not retire it. Repurpose it as the green-channel e-folding length and
make `uAbsorption` the unit-normalized ratio, as in 3a. Reasons. It preserves one
intuitive depth knob the sandbox already tunes. It makes `vec3(1.0)` reproduce
the current frame exactly for a clean A/B. It cleanly separates the modeled
magnitude from the physical ratio, which is precisely the honesty split section
3b needs. Retiring it would fold the magnitude into the vector and lose the clean
fallback and the single-knob tuning surface.

### 3e. Should absorption drive alpha, recommend no, keep alpha achromatic

Keep alpha on the existing scalar `uDepthAlphaScale`, `depthWater.ts` line 257,
and do not make `uAbsorption` drive it. Reason, the framebuffer carries a single
alpha channel and standard blending cannot express per-channel opacity, so a
chromatic alpha is not representable without premultiplied or dual-source
blending. The chromatic story belongs entirely in the color term. Alpha stays the
achromatic is-the-seabed-hidden scalar. Keeping color and alpha decoupled also
preserves the current foam and Fresnel-rim alpha composition at line 291 with no
regression. Cost, none.

A physically-correct chromatic-transmission path does exist and is worth noting
for later, but it is out of R09 scope and steps on WFX-R10. It would sample the
opaque scene COLOR, not only its depth, and composite per-channel transmittance
against the real seabed color with the water drawn opaque. The existing depth
pre-pass already renders the opaque scene, so capturing its color is about one
extra render-target attachment and zero extra passes, but it changes the seam
between water2 and the seabed and belongs to R10 and the W3 build. Flagging it,
not recommending it for R09.

## 4. Frame-budget impact

Zero extra passes. Confirmed. The change is fragment-shader arithmetic inside the
existing single water draw. The depth pre-pass at `depthWater.ts` lines 375 to
383 is untouched and still costs its one full opaque scene render, unchanged by
this work.

Per-fragment delta, the current path computes one scalar `exp` for `colorT`. The
extended path computes a vec3 `exp`, which is three scalar `exp`, so plus two
`exp` per fragment, plus a vec3 divide and a multiply-add, minus the `mix`. On a
water surface covering on the order of one to two million fragments at desktop
resolution, two added transcendental ops per fragment is on the order of a few
million extra ALU ops per frame, which is well under 0.05 ms on any GPU that
holds the 60 fps and 30 fps targets in the charter. This is an estimate from op
count, not a measured A/B, because the research wave runs no dev server. WFX-R13
should fold it into the full-stack accounting, where it rounds to zero against
the pre-pass and the proposed reflection and volumetric passes. No new texture
fetch, no bandwidth change, no new uniform texture.

## 5. Collision and sequencing

- Adoption lands in `web/lib/scene/water2/depthWater.ts`, owned by the twin W3
  water-upgrade agent and the WFX-BUILD wave. R09 is research only and edits
  nothing here. The build wave makes the shader edit.
- Coefficients depend on WFX-R11 Salish optics for the canonical color targets
  and final numbers. The ratio and citations here are the input R11 confirms.
- The scene-unit magnitude depends on the twin W2.6 datum and scale fix. The
  `worldUnitsPerMeter` of about 0.00242, RP2 line 46, sets the meter-to-unit
  conversion that section 3b reasons over, and the `level = SEA_LEVEL_Y` datum is
  already wired at `SalishScene.tsx` line 301.
- The deep-tint and coefficient constants live in
  `web/lib/scene/bathy/style/waterTuning.ts`, owned by WS-BATHY. The re-balance
  in 3b and the retarget in 3c reverse the original request intent and must be
  agreed with that owner through O0.
- No `SalishScene.tsx` or `globals.css` edit is implied by R09, so no convergence
  collision with W-CAM, W-LABELS, W3, W4, or LGC arises from this finding. Any
  later build edit stays inside `depthWater.ts` and `waterTuning.ts`.

## 6. Open questions for O0

1. Coefficient ordering. The pending `{r:3.0, g:1.6, b:0.9}` models clear blue
   ocean and contradicts the locked Salish-green constraint and the measured
   Strait of Georgia green window. Approve re-balancing to the green-window ratio
   near `vec3(R 1.4, G 1.0, B 3.0)`, green as the survivor, and retargeting the
   deep tint from navy to turbid green. This crosses the WS-BATHY style request
   intent and needs an O0 call.
2. Retire versus keep `uDepthColorScale`. Recommendation is keep, repurposed as
   the green-channel e-folding length with a unit-normalized ratio vector, fully
   backward compatible. Confirm.
3. Per-meter versus per-scene-unit. Recommendation is to keep the physical
   channel ratio and treat the overall magnitude as a modeled look control,
   because literal per-meter `Kd` over the compressed scene scale renders a flat
   opaque column with no gradient. Confirm this honesty framing.
4. Chromatic seabed transmission. There is a physically-correct path that samples
   the opaque color buffer for true per-channel transmission of the seabed color,
   at about one extra render-target attachment and zero extra passes. It changes
   the water2-to-seabed seam and overlaps WFX-R10 and W3. Decide whether to scope
   it into the build or leave R09 at the color-math change only.
