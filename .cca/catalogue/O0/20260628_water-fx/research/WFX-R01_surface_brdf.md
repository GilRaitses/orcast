# WFX-R01 surface-BRDF findings

Role WFX-R01, read-only research, WATER-FX Wave 1. Owner of this one file only.
Repo state verified against origin/main `915e4cc77923de93ed5f7e9a75feab9eb2e12896`.
Honesty label holds: modeled, not measured. Target water is the turbid green Salish
Sea (high CDOM and turbidity, Jerlov coastal type), not tropical blue.

Topic: physically based ocean surface BRDF. Diagnose why the current specular and
glitter read as distracting hard sparkle, and why the Fresnel reflection makes the
horizon stark. Propose an energy-conserving replacement that stays on `three`
(version `^0.169.0`, per `web/package.json` line 31), with GLSL-level guidance.

---

## 1. Scope and current state (file-cited)

The surface shading lives entirely in the fragment shader of
`web/lib/scene/water2/depthWater.ts`. The renderable factory `makeWater2` starts at
line 303. Defaults that matter to this topic:

- `DEFAULT_SKY = new THREE.Color("#9fc4e0")` at line 113. A single flat marine-haze
  color. This is the only thing the Fresnel term reflects.
- `uFresnelStrength` default `0.5`, set at line 345 and option-documented at line 74.
- `uSunDirection` default normalized `(0.4, 0.8, 0.4)` at line 353, overridden by
  `makeSun().direction` from `web/app/components/scene/realism/sun.ts` (see the
  `direction` field built at lines 135 to 139 of `sun.ts`).
- The water mesh is `transparent: true`, `depthWrite: false`, `FrontSide`, at lines
  330 to 332.

### 1.1 The exact specular and Fresnel code

The whole shading math is in the fragment `main()` from line 225 to 294. The lines
this topic must fix:

```272:286:web/lib/scene/water2/depthWater.ts
    // Fresnel sky reflection: grazing angles brighten toward the sky color.
    float fres = pow(1.0 - max(dot(n, viewDir), 0.0), 5.0);

    // Sun specular + sharper glitter, broken up by surface noise.
    vec3 sun = normalize(uSunDirection);
    vec3 halfVec = normalize(sun + viewDir);
    float ndh = max(dot(n, halfVec), 0.0);
    float spec = pow(ndh, 90.0);
    float glitter = pow(ndh, 600.0) *
      step(0.55, noise(vPlanePos * 7.0 + vec2(uTime * 0.9, -uTime * 0.7)));
    float diff = clamp(dot(n, sun), 0.0, 1.0);

    vec3 color = base * (0.6 + 0.4 * diff);
    color = mix(color, uSkyColor, fres * uFresnelStrength);
    color += vec3(1.0, 0.97, 0.9) * (spec * 0.8 + glitter * 1.4);
```

The normal `n` is the Gerstner analytic normal computed in the vertex shader
(`vWorldNormal`, accumulated at lines 144 to 146 and normalized at line 174) then
interpolated to each fragment and re-normalized at line 252. There is no normal map
and no roughness input anywhere in the material.

### 1.2 Renderer color pipeline (supporting fact)

A repository-wide search for `toneMapping`, `outputColorSpace`, `outputEncoding`,
and `ACESFilmic` across `web/**/*.{ts,tsx}` returns no matches. The renderer is left
at the `three` defaults, which for `0.169` is `NoToneMapping`. The water material is
a raw `ShaderMaterial` writing `gl_FragColor` directly (line 293), so it bypasses the
`three` `tonemapping_fragment` and `colorspace_fragment` chunks. Net effect: the
additive specular and glitter at line 286 have no highlight rolloff. Any value above
1.0 hard-clamps to white at the framebuffer. This is the renderer-side half of why
the sparkle reads as harsh, and it is owned by WFX-R05, not by this BRDF rewrite. The
BRDF fix below is necessary but not sufficient on its own without R05.

---

## 2. Diagnosis: why the current look is distracting and stark

Five concrete faults, each tied to a line.

### F1. The glitter lobe is far below pixel width and gated by a hard step (line 280 to 281)

`pow(ndh, 600.0)` is an extremely narrow specular lobe. For a Blinn-Phong exponent
`s`, the angular half-width of the highlight scales roughly as `1/sqrt(s)`, so
exponent 600 gives a lobe a handful of milliradians wide. The surface normal feeding
it is interpolated from a 180x180 plane spanning 192 by 144 scene units (geometry at
line 309), so a single screen pixel covers many wave slopes. A lobe that narrow
turns on and off between adjacent frames and adjacent pixels as the interpolated
normal crosses the lobe peak. That is textbook specular aliasing, the appearing and
disappearing sparkle described by the geometric-glint-AA literature (Chermain 2021,
section 5; Kaplanyan and Tokuyoshi). The `step(0.55, noise(...))` multiplier makes it
worse: it is a hard binary mask, so each glitter point is either full intensity or
zero with no transition, which adds its own flicker on top of the lobe flicker.

### F2. The specular and glitter are unphysical additive white, not energy conserving (line 286)

`color += vec3(1.0, 0.97, 0.9) * (spec * 0.8 + glitter * 1.4)` adds nearly white light
on top of the already-composited base and Fresnel color. It is not multiplied by a
Fresnel factor, not multiplied by the incident sun color or intensity, and not gated
by `N dot L`. The glitter is scaled by 1.4, so it deliberately overshoots 1.0. With no
tonemapping (section 1.2) this clamps to pure white. The result is bright hard dots
that have no relationship to how much light the surface could actually reflect. This
is the main source of the distracting read.

### F3. The Fresnel term has no F0 and is not used to drive the specular (line 273)

`pow(1.0 - max(dot(n, viewDir), 0.0), 5.0)` is the Schlick power-five shape with the
F0 and `(1 - F0)` factors dropped. Real Schlick for water is
`F = F0 + (1 - F0) * pow(1 - cosTheta, 5)` with `F0 ~= 0.02` at IOR 1.33
(Filament PBR theory, dielectric table: water 2 percent, IOR 1.33). The current code
gives `F = 0` at normal incidence instead of `0.02`, and at grazing it reaches `1.0`
which is then halved by `uFresnelStrength = 0.5`. More important, this Fresnel only
drives the flat-sky color mix at line 285. It does not modulate the sun specular at
line 286. Physically the specular highlight is the same reflection event as the sky
reflection and must be scaled by the same Fresnel factor.

### F4. The Fresnel reflects one flat color, which makes the horizon a hard band (line 285 and line 113)

`mix(color, uSkyColor, fres * uFresnelStrength)` blends every grazing fragment toward
the single constant `#9fc4e0`. A real sky is a gradient from a brighter, hazier
horizon to a darker zenith, and the reflected color depends on the reflected ray
direction, which varies fragment to fragment. Because the code uses one color, the
entire grazing region of the water collapses to a uniform band of `#9fc4e0`. That
uniform band against the rest of the scene is the stark, abrasive horizon line the
charter intent calls out (WAVESET_CHARTER.md lines 13 and 42 to 43). This is a
flat-input problem, not only a Fresnel-shape problem.

### F5. Diffuse-only base with no real reflection (line 284)

`base * (0.6 + 0.4 * diff)` lights the water body color by a Lambert-ish term. Water
is a low-albedo dielectric. Most of what the eye reads on real open water at distance
is reflected sky and reflected sun, not diffuse body color. The current model gives
almost all weight to the body color and only a thin flat sky mix, so the surface
reads as a tinted diffuse sheet with sparkles stuck on it rather than a reflective
interface.

---

## 3. Technique survey (web sources)

All URLs verified by fetch during this research.

1. Filament PBR theory and shading models, Google.
   https://google-filament.mintlify.app/concepts/pbr-theory and
   https://google-filament.mintlify.app/materials/shading-models and the full text at
   https://google.github.io/filament/Filament.md.html . Source for the Cook-Torrance
   microfacet form `f_r = D * G * F / (4 * NoV * NoL)`, the GGX (Trowbridge-Reitz)
   distribution `D_GGX`, the Smith correlated visibility term
   `V_SmithGGXCorrelated`, the Schlick Fresnel `F_Schlick(u, f0, f90)`, and the
   dielectric reflectance table giving water F0 = 0.02 at IOR 1.33. Also gives a
   half-precision GGX trick using `1 - NoH^2 = |cross(n,h)|^2` to keep highlights
   stable.

2. NVIDIA GPU Gems chapter 1, Effective Water Simulation from Physical Models.
   https://developer.nvidia.com/gpugems/gpugems/part-i-natural-effects/chapter-1-effective-water-simulation-physical-models
   Source for per-pixel Fresnel on water, separating water body color from reflection
   color, and modulating reflection by view angle. Confirms the house pattern of a
   per-pixel Fresnel driving a sky reflection, which the current shader only
   half-implements.

3. selfshadow, Specular Showdown in the Wild West (Stephen Hill).
   https://blog.selfshadow.com/2011/07/22/specular-showdown/ Survey of specular
   antialiasing: Toksvig factor `f_t = |Na| / (|Na| + s*(1 - |Na|))` that lowers the
   exponent and intensity where normals vary, plus LEAN and CLEAN. Source for the
   cheap in-shader exponent-widening approach.

4. NVIDIA, Mipmapping Normal Maps (Toksvig 2004 technical brief).
   https://developer.download.nvidia.com/whitepapers/2006/Mipmapping_Normal_Maps.pdf
   Original Toksvig factor derivation: the length of an averaged normal measures
   normal variance, and scaling the specular exponent by that factor removes
   strobing and sparkle.

5. Olano and Baker, LEAN Mapping (paper PDF).
   https://userpages.cs.umbc.edu/olano/papers/lean/lean.pdf and ACM record
   https://dl.acm.org/doi/10.1145/1730804.1730834 . Filters the distribution of bump
   normals so a Blinn-Phong exponent as high as 13,777 renders aliasing-free at
   distance, including on ocean. Relevant if a normal-map wave detail layer is added
   later (R02). Notes the `s/(2*pi)` normalization of Blinn-Phong toward a Beckmann
   lobe.

6. Chermain et al., Real-Time Geometric Glint Anti-Aliasing with Normal Map
   Filtering. https://xavierchermain.github.io/data/pdf/Chermain2021RealTime.pdf and
   https://doi.org/10.1145/3451257 . Confirms that geometric glint aliasing is driven
   by curvature across the pixel footprint, and that derivative-based footprint
   estimation with `dFdx`/`dFdy` of the (half-)slope is the real-time tool. States a
   measured overhead of 0.6 percent to 4.2 percent of frame time for the full glinty
   technique. Useful upper bound: even the heavy version is single-digit-percent.

7. Tokuyoshi and Kaplanyan, Improved Geometric Specular Antialiasing (JCGT).
   https://www.jcgt.org/published/0010/02/02/paper.pdf . The minimal in-shader
   method: estimate normal variance from screen-space derivatives of the normal and
   add it to the roughness as a clamped `kernelRoughness`. A few ALU per pixel, no
   textures, no extra pass. This is the directly adoptable fix for the present
   analytic-normal surface.

---

## 4. Recommendations (three-implementable)

All three are confined to the fragment shader of `web/lib/scene/water2/depthWater.ts`
plus, for REC-A roughness, one extra varying or a `dFdx` call. None adds a render
pass. None adds a dependency. Costs are estimated unless marked measured, because the
charter forbids running a dev server in this wave so no live frame capture was taken.

### REC-A (primary): energy-conserving microfacet specular with real Schlick Fresnel and slope-driven roughness

Replace lines 273 to 286 with a single normalized specular lobe driven by a roughness
that comes from wave slope and from screen-space normal variance. This kills F1, F2,
and F3 at once.

Proposed GLSL, drop-in for the block above. It reuses the existing `n`, `viewDir`,
`sun`, `diff`, `base`, `fres` names so the surrounding composite stays small:

```glsl
    // --- REC-A: PBR specular for a water dielectric ---
    const float F0 = 0.02;              // water at IOR 1.33 (Filament)
    vec3 sun = normalize(uSunDirection);
    vec3 h   = normalize(sun + viewDir);
    float NoV = clamp(dot(n, viewDir), 1e-4, 1.0);
    float NoL = clamp(dot(n, sun),     0.0,  1.0);
    float NoH = clamp(dot(n, h),       0.0,  1.0);
    float VoH = clamp(dot(viewDir, h), 0.0,  1.0);

    // Roughness from wave slope plus geometric AA (Tokuyoshi/Kaplanyan).
    // dNdx/dNdy measure how fast the normal turns across this pixel; large
    // variance -> wider, dimmer lobe -> no sub-pixel sparkle.
    vec3 dNx = dFdx(n);
    vec3 dNy = dFdy(n);
    float variance = 0.5 * (dot(dNx, dNx) + dot(dNy, dNy));
    float baseRough = uRoughness;                 // new uniform, ~0.06 calm .. 0.20 chop
    float rough = clamp(sqrt(baseRough*baseRough + variance), 0.02, 0.6);
    float a  = rough * rough;

    // GGX distribution.
    float d  = (NoH * NoH) * (a*a - 1.0) + 1.0;
    float D  = (a*a) / max(3.14159265 * d * d, 1e-6);
    // Smith correlated visibility (Filament fast form).
    float gv = NoL * (NoV * (1.0 - a) + a);
    float gl = NoV * (NoL * (1.0 - a) + a);
    float Vis = 0.5 / max(gv + gl, 1e-5);
    // Schlick Fresnel with real F0, evaluated at V dot H for the highlight.
    float F  = F0 + (1.0 - F0) * pow(1.0 - VoH, 5.0);

    float specular = D * Vis * F * NoL;           // energy-conserving scalar
    vec3 sunColor  = vec3(1.0, 0.97, 0.9);        // tie to makeSun().color later
```

Then the composite at line 284 to 287 becomes:

```glsl
    vec3 color = base * (0.6 + 0.4 * diff);
    color = mix(color, reflectedSky, fresEnv);    // REC-B supplies these two
    color += sunColor * specular;                 // bounded, Fresnel-weighted
    color = mix(color, uColorFoam, clamp(foam, 0.0, 1.0));
```

Why this fixes the faults. F1: the lobe width now comes from `rough`, and `rough`
grows with both authored chop and per-pixel normal variance, so the lobe can never be
narrower than the pixel footprint. The flickering binary `step` glitter is deleted.
F2: `specular = D * Vis * F * NoL` is the normalized Cook-Torrance scalar, it is
bounded by the Fresnel and geometry terms instead of an arbitrary 1.4 gain. F3: F0 is
present and the same Fresnel scales the highlight.

Cost: estimated. The added math is roughly 30 to 45 ALU ops over the current ~15,
plus two `dFdx`/`dFdy` on a vec3 (cheap, hardware quad differencing). At 1080p with
dpr 1 the water plane covers on the order of 2.1 million fragments. 2.1e6 fragments
times ~40 extra ops is ~8.4e7 ops per frame. On a desktop GPU in the multi-TFLOP
range this is well under 0.1 ms. On a low-end laptop iGPU near 0.5 to 1 TFLOP it is
an estimated 0.1 to 0.4 ms. Both are small next to the existing depth pre-pass, which
is a full extra scene render of the streamed CUDEM tileset (see section 5). Marked
estimated; a measured number needs a gated A/B in the `/water` sandbox.

Three-only fallback: if `dFdx`/`dFdy` on the normal proves noisy at grazing angles
(the JCGT paper flags grazing instability), drop the `variance` term and drive
`rough` from wave slope alone, computed as `1 - n.y` of the geometric normal, which is
already available with no derivatives. This still widens the lobe on steep wave faces
and removes the worst sparkle, just less precisely. Both paths are pure `three`, no
new uniform beyond `uRoughness`.

### REC-B (primary): replace the flat-sky Fresnel with a view-dependent reflected-sky color

Fixes F4 and F5. Compute the reflected ray and shade it with a vertical sky gradient
so grazing fragments no longer collapse to one color, and weight the body-vs-sky mix
by the real Fresnel at `N dot V`.

```glsl
    // --- REC-B: reflected-sky color instead of one flat uSkyColor ---
    vec3 r = reflect(-viewDir, n);                // reflected view ray
    float up = clamp(r.y * 0.5 + 0.5, 0.0, 1.0);  // 0 at horizon, 1 at zenith
    vec3 reflectedSky = mix(uSkyHorizon, uSkyZenith, up);
    float fresEnv = F0 + (1.0 - F0) * pow(1.0 - NoV, 5.0);  // real Schlick at N.V
```

`uSkyHorizon` and `uSkyZenith` are two new color uniforms. They can be fed from the
existing `skyColor(elevationDeg)` helper in
`web/app/components/scene/realism/atmosphere.ts` (lines 34 to 47): pass the current
sky color as the horizon stop and a darker, bluer stop as the zenith. The single
`uSkyColor` uniform at line 351 and `uFresnelStrength` at line 345 are retired in
favor of `fresEnv` carrying the correct normal-incidence floor.

Why it fixes the horizon: `reflectedSky` now varies with `r.y`, so the grazing band
shows a gradient that matches the sky above it instead of a hard uniform line. The mix
weight `fresEnv` rises smoothly from 0.02 at normal incidence to near 1.0 at grazing,
which is the physically correct ramp.

Cost: estimated, negligible. One `reflect`, one `mix`, one extra `pow`. A handful of
ALU. No pass, no texture, no dependency.

Three-only fallback: this is already the three-only fallback. The higher-fidelity
version, a real reflected environment, is a sampled sky cube or PMREM and a planar or
screen-space reflection. That belongs to WFX-R03 (reflections) and WFX-R04 (sky), and
each of those is a costed extra pass that this BRDF doc does not own. REC-B is the
zero-pass bridge that already removes the stark band, and it is the consumer of
whatever env R03/R04 later provide: swap `reflectedSky` from the gradient to a
`textureCube(envMap, r)` sample with no other change to the BRDF.

### REC-C (optional, defer): Toksvig or LEAN exponent filtering if a normal-map detail layer is added

Only relevant if R02 adds a tiled normal-map for fine ripple detail on top of the
Gerstner geometry. In that case the geometric-derivative AA in REC-A does not see the
texture-space variance, and a Toksvig factor baked into the normal-map mips (source 3
and 4) or LEAN moments (source 5) is the correct filter. Until a normal map exists
there is nothing to filter, so this is a defer, not a now.

Cost: estimated. Toksvig is one texture channel and two ALU per pixel at runtime plus
an offline mip bake. LEAN is two RG textures and linear filtering. No extra pass.
Three-only fallback: Toksvig, since it needs only a stored normal length and no second
moment textures.

---

## 5. Frame-budget impact (ms and passes vs the 60/30 budget and the depth pre-pass)

Budget: 60 fps desktop is a 16.7 ms frame, 30 fps laptop is a 33.3 ms frame.

The existing cost this topic must respect is the depth pre-pass. In
`renderDepthPrepass` (lines 375 to 383 of `depthWater.ts`) the code hides the water
mesh, sets the depth render target, and calls `renderer.render(scene, camera)`. That
is one full additional render of the entire opaque scene, which for the streamed CUDEM
tileset is the dominant per-frame cost of the water feature. No measured number is
available in this read-only wave, but structurally it is on the order of a second full
scene draw, so plausibly several ms on a laptop. Mark estimated.

Against that baseline, the recommendations in section 4 add zero passes and zero
render targets. They are all extra fragment ALU on the water plane that already draws.
Estimated added cost:

- REC-A: ~0.05 ms desktop, ~0.1 to 0.4 ms laptop (derived in section 4).
- REC-B: below ~0.02 ms either tier, a few ALU.
- REC-C: not adopted now.

So the full REC-A plus REC-B BRDF rewrite is an estimated sub-0.5 ms cost on the worst
target, which is a small fraction of the 33.3 ms laptop budget and is dwarfed by the
existing depth pre-pass. The expensive realism levers, a reflected environment cube or
planar reflection, a procedural sky pass, and underwater volumetrics, are each a
separate pass owned by R03, R04, and R08, and must be costed there against the same
pre-pass baseline. This topic stays pass-free on purpose.

---

## 6. Collision and sequencing notes

This doc feeds 3D-TWIN W3 water-upgrade, owner `web/lib/scene/water2/`. All proposed
edits are inside `depthWater.ts` (fragment shader and a small set of new uniforms),
which is the W3 water-upgrade owner file, so there is no convergence-file collision.
The integration that lands the chosen stack into
`web/app/components/scene/SalishScene.tsx` is a later gated wave and serializes via O0
against W-CAM, W-LABELS, W3, W4, and LGC, per WAVESET_CHARTER.md lines 69 to 71. This
research touches none of those.

Sequencing dependencies:

- REC-A roughness reads the surface normal. If WFX-R02 replaces the 6-wave Gerstner
  sum with a spectrum or FFT, the normal source at `vWorldNormal` changes. Land REC-A
  after the wave-normal source is stable, or keep the geometric-derivative variance
  path which is agnostic to how the normal was produced.
- REC-B `reflectedSky` is the seam for WFX-R03 (reflections) and WFX-R04 (sky). Ship
  REC-B with the two-stop gradient first, then swap the gradient for the R03/R04 env
  sample with no other BRDF change.
- The renderer color pipeline (section 1.2) is owned by WFX-R05. The energy-conserving
  specular will still clip to white until R05 enables tonemapping or routes the water
  through the `three` output chunks. REC-A and R05 should land together or R05 first.
- WFX-R09 (rgb-absorption) edits the `base` body color, not the specular. REC-A and
  REC-C compose with it cleanly because they only add reflected light on top of
  whatever `base` becomes.
- WFX-R13 (perf-adversarial) should fold the section 5 estimates into the full-stack
  budget and replace them with measured numbers once a gated sandbox A/B is allowed.

---

## 7. Open questions for O0

1. Is a sampled environment reflection (sky cube or PMREM, or planar/SSR) in scope for
   W3, or should R01 ship REC-B with the analytic two-stop gradient first and treat the
   env sample as a later swap? This decides whether the stark horizon is fully fixed in
   one wave or two.
2. The renderer has no tonemapping set (section 1.2). Energy-conserving specular needs
   a tonemap or an output rolloff to not clip to white. Confirm R05 owns this and that
   REC-A is gated to land with or after R05, not before.
3. Should `uRoughness` be a single authored scalar, or should chop drive it from the
   R02 wave state (for example wind speed mapped to slope variance)? This couples R01
   to R02's chosen wave model.
4. Sun color and intensity for the highlight should come from `makeSun().color` and
   `.intensity` rather than the hard-coded `vec3(1.0, 0.97, 0.9)`. Confirm that wiring
   the sun color into the water material is in scope for the BRDF build, or owned by
   R05's lighting work.

---

## Appendix: verified paths cited

- `web/lib/scene/water2/depthWater.ts` (fragment shader lines 180 to 295; specular
  block 272 to 286; pre-pass 375 to 383; geometry 309; material 327 to 356).
- `web/app/components/scene/realism/sun.ts` (direction 135 to 139; color 149 to 151).
- `web/app/components/scene/realism/palette.ts` (water color stops 16 to 23).
- `web/app/components/scene/realism/atmosphere.ts` (`skyColor` 34 to 47).
- `web/app/(sandbox)/water/WaterSandboxScene.tsx` (rig and sliders 57 to 256).
- `web/package.json` line 31 (`three` `^0.169.0`).
- `web/lib/scene/bathy/style/WATER2_TUNING_REQUEST.md` (the pending per-channel
  absorption request, owned by WFX-R09, body-color only, not this topic).
- `.cca/catalogue/O0/20260628_water-fx/WAVESET_CHARTER.md` and `wave_shape.yml`.
