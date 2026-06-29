# WFX-R06 shoreline foam, wave run-up, wet-sand darkening

Lane WATER-FX (WFX), Wave 1 research, read-only. Owner WFX-R06. Reports to the
WFX sub-orchestrator, escalates to O0.

Repo state grounded against the charter `repo_state_verified_against`
915e4cc77923de93ed5f7e9a75feab9eb2e12896.

Honesty label: modeled, not measured. Foam, run-up, and wetness are interpretive
shading over the modeled CUDEM topobathy and the modeled water column. None of it
asserts a measured surf state. Salish Sea targets stay turbid and green, not
tropical-blue surf.

## 1. Scope and current state, file-cited

The current foam lives entirely in the water2 fragment shader and is driven by the
same water-column thickness the Beer-Lambert color and alpha use. The column is
reconstructed from the opaque-scene depth pre-pass and clamped at zero, so terrain
at or above the surface yields a zero column.

```236:244:web/lib/scene/water2/depthWater.ts
    } else {
      vec4 ndc = vec4(uv * 2.0 - 1.0, sceneDepth * 2.0 - 1.0, 1.0);
      vec4 worldH = uInverseViewProjection * ndc;
      vec3 seabed = worldH.xyz / worldH.w;
      // Vertical water column from the surface plane down to the seabed. Terrain
      // at/above the surface yields <= 0 -> the water clears and land shows.
      column = uWaterLevel - seabed.y;
    }
    column = max(column, 0.0);
```

The foam band itself is a thin column-keyed noise window, plus its contribution to
alpha.

```262:291:web/lib/scene/water2/depthWater.ts
    // Shoreline foam: a thin band just offshore. Zero exactly at the waterline
    // (so land never gets a foam wash) and zero again past the band.
    float fmid = uFoamDepth * 0.5;
    float foam =
      smoothstep(0.0, fmid, column) * (1.0 - smoothstep(fmid, uFoamDepth, column));
    float foamNoise =
      noise(vPlanePos * 1.6 + vec2(uTime * 0.6, uTime * 0.35)) * 0.6 +
      noise(vPlanePos * 4.0 - vec2(uTime * 0.4, uTime * 0.5)) * 0.4;
    foam *= 0.45 + 0.55 * foamNoise;

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
    color = mix(color, uColorFoam, clamp(foam, 0.0, 1.0));

    // Alpha: depth-driven core + a little Fresnel rim + the foam line. Clamped so
    // the thinnest water still approaches fully transparent and reveals land.
    float alpha = clamp(depthAlpha + fres * 0.18 + foam * 0.9, 0.0, 1.0);
```

The default band thickness is `uFoamDepth = 0.08` scene units, documented as "the
near-shore foam band."

```70:71:web/lib/scene/water2/depthWater.ts
  /** Column thickness (scene units) of the near-shore foam band. Default 0.08. */
  foamDepth?: number;
```

```343:343:web/lib/scene/water2/depthWater.ts
      uFoamDepth: { value: opts.foamDepth ?? 0.08 },
```

The math, read out exactly. `fmid = uFoamDepth * 0.5` is the band center.
`smoothstep(0.0, fmid, column)` ramps the foam up from zero column to the center.
`(1.0 - smoothstep(fmid, uFoamDepth, column))` ramps it back down to zero past the
band, so the band closes at `column = uFoamDepth`. Two octaves of value noise
scroll the foam, and the band is gated to never fall below `0.45` and never exceed
`1.0` of the noise envelope through `foam *= 0.45 + 0.55 * foamNoise`. Foam adds to
both the foam color mix and the alpha through `foam * 0.9`.

### The invariant to protect

At the exact waterline the column is zero, and `smoothstep(0.0, fmid, 0.0) = 0`, so
`foam = 0` there. Land, where `column = max(column, 0.0)` clamps to zero, also gets
`foam = 0`. This is the stated guarantee in the source comment "Zero exactly at the
waterline (so land never gets a foam wash) and zero again past the band." Any
run-up upgrade must keep the inner edge of the foam window anchored at a strictly
positive column so the land side stays at zero foam. The cheap way to guarantee
this is to only ever widen the OUTER edge of the window and never move the inner
`smoothstep(0.0, fmid, column)` factor off the zero origin.

### Where wet-sand actually lives (seam correction)

The dispatch points at `bathyTint.ts` for the shore band and wet-sand keying off Y
near zero. The verified seam is more precise than that. `bathyTint.ts` is a
submerged-seabed point overlay built on `buildSubstrateOverlay`. Its only
above-water handling is a flat land tint fade for `depth_m > 0`, and it writes a
per-vertex color buffer on a `THREE.Points` object, not a per-fragment land
material.

```137:144:web/lib/scene/bathy/style/bathyTint.ts
      } else if (d > 0 && maxD > 0) {
        const tl = Math.max(0, Math.min(1, d / maxD));
        c.copy(landShallow).lerp(landHigh, tl);
      } else {
        c.copy(landShallow);
      }
      colorAttr.setXYZ(i, c.r, c.g, c.b);
    }
```

The real per-fragment shoreline band near Y equals zero is in the terrain stylist,
which already injects a world-Y-keyed shore mask into the streamed CUDEM tile
material.

```293:298:web/lib/scene/terrain/terrainStylist.ts
  // Narrow shoreline band just above sea level (Y == 0), only on flatter ground.
  float shoreMask = ( 1.0 - smoothstep( 0.0, uShoreBandY, abs( terrainY ) ) ) * upDot;
  biome = mix( biome, uShore, shoreMask * uShoreStrength );
```

So wet-sand darkening belongs in `terrainStylist.ts` on the land material, layered
into that existing `shoreMask`, not in `bathyTint.ts` and not in the water shader.
The water shader cannot darken sand correctly because past the waterline the water
is transparent and writes no land color. This is the cross-seam flagged in section
5.

## 2. Technique survey with URLs

### Depth-intersection foam (what water2 already does)

The water2 foam is the standard depth-intersection shoreline foam pattern, just
keyed on a reconstructed vertical column instead of a raw depth-buffer difference.
The canonical writeups:

- Roystan, Unity toon water, depth-difference foam with a noise cutoff and a
  normal-modulated foam distance so steep contacts foam deeper than flat shore.
  https://roystan.net/articles/toon-water/
- Cyanilux, Shoreline shader breakdown, the most complete reference for this topic.
  Covers depth-based shore gradients, scrolling-line dissolve, swash run-up, and
  wet sand. https://www.cyanilux.com/tutorials/shoreline-shader-breakdown/
- Daniel Ilett, Shader Graph scene intersections, reconstructs position from depth
  and thresholds the difference for edge foam.
  https://danielilett.com/2024-05-28-tut7-13-intro-to-shader-graph-part-9/
- tuxalin water-shader, a hand-GLSL ocean with `waterDepth`, `shoreFade`, and a
  `FoamValue` that mixes a shore texture and a foam texture by wave amplitude.
  https://github.com/tuxalin/water-shader/blob/master/shaders/unity/water.shader

The key transferable idea from Roystan and tuxalin is widening the foam threshold
on steep contacts and tying foam strength to wave amplitude, both of which water2
can do without a new pass.

### Wave-phase run-up (swash)

Run-up, or swash, is the foam edge advancing up the beach and retreating with each
wave. The two practical patterns:

- Cyanilux swash motion. A cosine drives a back-and-forth offset that pushes the
  foam mask up the beach then retreats it, remapped to 0..1 and used to both move
  and fade the foam band. The author notes the up-run can be made shorter in
  duration than the retreat for a more natural asymmetry, and that the swash sine
  and the approaching-wave scroll share a period but are manually phase-offset.
  https://www.cyanilux.com/tutorials/shoreline-shader-breakdown/
- GPU Gems 1, chapter 1, effective water with Gerstner waves. The Gerstner phase
  `f = k(dot(dir, pos) - c t)` already encodes where each long wave is in its
  cycle. Coupling the swash to that real phase, rather than a free cosine, ties the
  foam pulse to the same waves the surface already shows.
  https://developer.nvidia.com/gpugems/gpugems/part-i-natural-effects/chapter-1-effective-water-simulation-physical-models

water2 is better placed than the Cyanilux setup here because it already computes
the Gerstner phases in the vertex shader, so the swash can ride the dominant
long-wave phase for free instead of inventing a second oscillator.

### Wet-sand darkening and wetness

Wet sand is a land-material effect, not a water effect. The consistent recipe
across sources is darken and slightly saturate the albedo, drop roughness, and
optionally nudge metalness, inside a mask that the swash leaves behind.

- Cyanilux wet sand. Darkens the material under the retreated swash with a low-alpha
  black and a smoothstep-masked gradient, and notes the same mask can feed
  smoothness for a shinier wet look. https://www.cyanilux.com/tutorials/shoreline-shader-breakdown/
- Galidar Oceanology shoreline wetness, concrete parameter targets that match the
  recipe. MoistureRoughness about 0.05, MoistureMetalness about 0.25, a wetness
  radius and a vertical wetness origin relative to the water surface.
  https://galidar.com/oceanology-nextgen/NextGenShorelineWetness
- Unity production-ready wetness decal, "darkening color and increasing smoothness,
  very simple math and no texture samples, very performance efficient," which is the
  cost profile to aim for. https://docs.unity3d.com/Packages/com.unity.shadergraph@17.6/manual/Shader-Graph-Sample-Production-Ready-Detail.html

For the Salish Sea, the wet darkening should be modest. Turbid green shallows and
gray-tan glacial-till beaches do not flash a bright specular sheet the way tropical
white sand does, so a strong metalness or near-mirror roughness would read as
unreal. A darken-and-slightly-smooth pass is the honest target.

## 3. Recommendations with cost and three-only fallback

### R06-A. Phase-coupled run-up foam in water2 (primary)

Keep the existing column-keyed foam window and add a swash term driven by the
dominant long-wave Gerstner phase, modulating only the OUTER edge of the window and
the foam intensity. This preserves the zero-at-waterline invariant by construction.

Vertex shader, add one varying derived from the longest wave W0, which already has
its phase computed in `gerstner`. Expose the phase cheaply by recomputing the W0
scalar phase in `main` after the displacement sum.

```glsl
// vertex, after the existing disp += gerstner(...) sum:
vec2 d0 = normalize(W0.xy);
float k0 = 6.2831853 / W0.z;
float c0 = sqrt(9.8 / k0);
float phase0 = k0 * (dot(d0, p) - c0 * uTime * uSpeed);
// 0 at trough, 1 at crest; this is the swash drive.
vSwash = 0.5 + 0.5 * sin(phase0);
```

Fragment shader, replace the fixed band edges with swash-widened edges. The inner
factor stays anchored at zero column, so land foam stays exactly zero.

```glsl
// fragment, replacing the foam window:
// uRunup in [0,1], default ~0.6, how far the swash widens the band.
float runup = 1.0 + uRunup * vSwash;          // 1.0 at trough, up to 1+uRunup at crest
float foamDepth = uFoamDepth * runup;          // outer edge breathes landward
float fmid = foamDepth * 0.5;
float foam =
  smoothstep(0.0, fmid, column) * (1.0 - smoothstep(fmid, foamDepth, column));
// existing two-octave noise, unchanged:
float foamNoise =
  noise(vPlanePos * 1.6 + vec2(uTime * 0.6, uTime * 0.35)) * 0.6 +
  noise(vPlanePos * 4.0 - vec2(uTime * 0.4, uTime * 0.5)) * 0.4;
foam *= 0.45 + 0.55 * foamNoise;
// pulse the brightness with the swash so the line surges and fades:
foam *= mix(0.65, 1.0, vSwash);
```

Optional, the Roystan steep-contact widening. Where the seabed under the fragment
is steep, foam can reach deeper. water2 does not currently carry the seabed normal,
but a cheap proxy is the screen-space gradient of the reconstructed column, which
needs no new pass. This is a nice-to-have for WFX-BUILD, not required for the core
run-up.

Why this is honest and safe. The inner `smoothstep(0.0, fmid, column)` is identical
in form to the current code and still evaluates to zero at `column = 0`, so the
land-never-washed guarantee holds for every swash value. The swash only ever scales
`foamDepth` by a factor at or above 1.0, which moves the OUTER edge offshore and
back, never the inner edge onto land.

Cost, estimated. Vertex, one extra `normalize`, one `dot`, one `sin`, and a few
mul/add per vertex on a 180x180 plane, roughly 33k verts. This is a handful of ALU
ops on a vertex shader that already evaluates six Gerstner waves, so the added
vertex cost is in the low single-digit percent of the existing vertex work and far
below the depth pre-pass cost. Fragment, two extra `mul` and one `mix` per water
fragment, with no new texture sample. On the order of single-digit ALU instructions
added to a shader that already does multiple `noise` calls and two `pow` specular
terms. Not separately measurable against the existing fragment load. No new pass,
no new uniform texture, two new scalar uniforms `uRunup` and the `vSwash` varying.

Three-only fallback. None needed. This is hand-GLSL on the existing water2
material, no dependency. The heavier alternative, a foam flipbook texture atlas
sampled along the swash, would add one texture bind and one sample per fragment plus
authored art, for crisper foam filaments. The procedural two-octave noise already in
the file is the three-only path and is the recommendation.

### R06-B. Wet-sand darkening on the terrain material (cross-seam, secondary)

Implement wet sand in `terrainStylist.ts`, not in water2 and not in `bathyTint.ts`,
layered into the existing `shoreMask` near Y equals zero. Darken and slightly
desaturate the resolved biome color inside a thin band just above the waterline, and
drop roughness modestly so the wet zone reads damp rather than mirror-like.

```glsl
// terrainStylist injectFragment, after the existing shoreMask block:
// wet band hugs the waterline from above; reuse shoreMask shape but tighter.
float wetMask = (1.0 - smoothstep(0.0, uWetBandY, max(terrainY, 0.0))) * upDot;
// darken + slightly desaturate toward a damp tone:
float lum = dot(biome, vec3(0.299, 0.587, 0.114));
vec3 wet = mix(biome, vec3(lum), 0.15) * uWetDarken;   // uWetDarken ~ 0.72
biome = mix(biome, wet, wetMask * uWetStrength);
```

The roughness drop is a material assignment, not a per-fragment shader edit, and
fits the existing `clone.roughness = roughness` path. A second, swash-synced band is
possible later if water2 publishes the swash phase to the terrain material, but that
couples two modules and should be a deliberate O0 decision, not a default.

Cost, estimated. A few ALU ops per land fragment in the shore band, no new pass, no
texture. Indistinguishable from the existing biome tint cost. The Unity wetness
decal reference confirms this class of effect is "very simple math and no texture
samples."

Three-only fallback. None needed. This is an `onBeforeCompile` injection on the
already-patched `MeshStandardMaterial`, same mechanism the stylist already uses.

### Salish honesty tuning

Default the wet darkening toward the lower end, `uWetDarken` near 0.75, and keep
foam color the existing near-white `#dfeef5`, not pure white, so the shoreline reads
as turbid Salish foam rather than tropical surf. Tune in the `/water` and `/world`
sandboxes during WFX-BUILD.

## 4. Frame-budget impact

Confirmed in-shader, zero extra passes. The charter records that the depth pre-pass
already costs one full scene render, and both recommendations add only ALU to
shaders that already run, with no second target, no reflection pass, and no new
texture bind.

- R06-A adds a small constant to the water vertex shader and the water fragment
  shader. No change to the depth pre-pass, which runs with the water hidden anyway,
  so foam math never executes during the pre-pass.
- R06-B adds a small constant to the terrain tile fragment shader inside the
  existing shore band, plus a roughness value set at material clone time.

Net added passes, zero. Net added texture samples per fragment, zero. Net added
uniforms, two scalars on water2 and two scalars plus a roughness value on the
terrain material. Against a 60fps desktop budget of about 16.6 ms and the existing
two full scene renders, the added per-fragment ALU is below measurement noise and
should be confirmed with an A/B frame-time capture in WFX-ACCEPT rather than
asserted as a measured number now.

## 5. Collision and sequencing

- Foam and run-up, R06-A, are owned by the water-upgrade seam
  `web/lib/scene/water2/depthWater.ts`. In the twin wave map this is W3
  water-upgrade, and in WFX it lands through WFX-BUILD then WFX-INTEGRATE. No
  convergence-file edit in research.
- Wet-sand darkening, R06-B, is a cross-seam into the terrain material owner
  `web/lib/scene/terrain/terrainStylist.ts`, which is W3 terrain-material territory,
  a different owner than water2. This must be coordinated through O0 so WFX-R06 does
  not duplicate or collide with the terrain-material agent. The dispatch named
  `bathyTint.ts`, but the verified shore band is in `terrainStylist.ts`, so the
  ownership flag points there.
- Both effects feed the same later `SalishScene.tsx` integration that serializes
  against W-CAM, W-LABELS, W3, W4, and LGC per the charter collision lock. Research
  touches none of those files.
- Adjacent WFX research overlaps to deconflict in synthesis. WFX-R01 surface BRDF
  and WFX-R10 seabed interaction both touch the same fragment shader and the same
  depth reconstruction, so the foam edits and any BRDF or soft-shoreline edits must
  be merged as one coherent water2 rewrite in WFX-BUILD, not as three separate
  patches to the same lines.

## 6. Open questions for O0

1. Ownership of R06-B. Wet-sand darkening is terrain-material territory in
   `terrainStylist.ts`, not water2 and not `bathyTint.ts`. Should WFX-R06 hand the
   wet-sand spec to the W3 terrain-material agent, or does WFX own a thin wet-band
   addition to the existing `shoreMask`. Requesting a single owner.
2. Swash phase sharing. R06-A keeps the swash internal to water2. A more coherent
   shoreline would let the terrain wet band breathe with the same swash, which
   requires water2 to publish a swash phase the terrain material reads. That couples
   two modules and one convergence point. Adopt now or defer to a later wave.
3. Run-up amplitude honesty. The Salish Sea inshore is low-energy compared to open
   surf. Should the default `uRunup` be conservative so the foam band breathes only
   slightly, matching a sheltered inland sea rather than an exposed beach. Proposing
   a small default, confirmed visually in the sandbox.
4. Steep-contact foam widening. The Roystan normal-modulated foam distance needs a
   seabed normal or a column gradient that water2 does not carry today. Worth the
   extra ALU for foam around terrain that pokes through the surface, or out of scope
   for this lane. Defer to WFX-R10 seabed-interaction to decide jointly.
