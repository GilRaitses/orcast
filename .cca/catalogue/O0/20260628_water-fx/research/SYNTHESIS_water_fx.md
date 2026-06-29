# WATER-FX research synthesis, ranked sequenced build plan

Author, the WATER-FX (WFX) sub-orchestrator. Reports to O0, not the human operator.
Repo state verified against the charter pin origin/main
`915e4cc77923de93ed5f7e9a75feab9eb2e12896` (branch main, 2026-06-28).
Honesty label holds. Every realism lever below changes how the water and sky look and
asserts no measured depth, color, or sea state. The seabed read stays the modeled CUDEM
topobathy. No code was changed in this wave. No dev server or build was run.

This document is the ranked, sequenced plan the twin's W3 and W4 waves, or a net-new
WFX-BUILD wave, consume. It is built from the 13 Wave 1 findings docs listed in section 1.
Every per-frame millisecond number in this synthesis is an estimate inherited from the
findings, labeled estimated, because the wave is read-only. The one number the whole budget
turns on, the cost of a single full opaque scene render of the streamed CUDEM tileset,
called U, is unmeasured and must be measured by the twin W-PERFUX load-perf research before
any third full render is approved.

---

## 1. The 13 findings docs

All under `.cca/catalogue/O0/20260628_water-fx/research/`.

| Role | Path | Core result |
| --- | --- | --- |
| WFX-R01 | `WFX-R01_surface_brdf.md` | The distracting sparkle is sub-pixel `pow(ndh,600)` glitter plus an unbounded additive white term. Replace with energy-conserving GGX and a real Schlick Fresnel at F0 0.02, plus a reflected-sky gradient. Pass-free, under 0.5 ms laptop. |
| WFX-R02 | `WFX-R02_wave_spectrum.md` | Scene scale is decisive, about 0.55 km per mesh quad against 25 m per vertical unit, so real waves are sub-quad. Keep Gerstner, drop sub-Nyquist waves, lower amplitude for a sheltered sea, push detail to a normal map. Reject FFT. |
| WFX-R03 | `WFX-R03_reflections.md` | The flat single-color sky reflection is the stark-horizon root cause. Default to a PMREM env sampled from the procedural sky, no extra per-frame render. Reserve planar Reflector for a high preset. Reject SSR. |
| WFX-R04 | `WFX-R04_sky_atmosphere.md` | The white sky is exposure, not a missing sky. The stark horizon is fog tuned for a far larger world than the 120-unit scene. Keep Preetham, drop exposure near 0.5, swap to FogExp2, share one horizon color. |
| WFX-R05 | `WFX-R05_lighting_tonemap.md` | ACES is already on by the r3f v8 default. The gap is `toneMappingExposure` left at 1.0. One renderer property near 0.5 fixes most of the white sky at zero per-frame cost. PMREM env helps future PBR materials, not the current custom shaders. |
| WFX-R06 | `WFX-R06_shoreline_foam.md` | Phase-couple foam run-up to the Gerstner long-wave phase, widening only the outer band so the land-never-washed invariant holds. Wet-sand belongs in `terrainStylist.ts`, not water2 or bathyTint. Pass-free. |
| WFX-R07 | `WFX-R07_caustics_godrays.md` | Caustics as a weak in-shader seabed term reusing the reconstructed `seabed.xz`, tuned faint for turbid water. Skip god-rays for the default top-down view. Defer shafts to a confirmed dive view behind a preset. |
| WFX-R08 | `WFX-R08_underwater_volumetrics.md` | Defines `web/lib/scene/underwater/` for W4. Swap `scene.fog` to a turbid-green FogExp2 with short visibility when submerged, reuse `rollInFog` for a no-pop crossing. Reject raymarch. Fog color from R09, visibility from R11. |
| WFX-R09 | `WFX-R09_rgb_absorption.md` | Adopt the per-channel Beer-Lambert form. The pending `{r:3.0,g:1.6,b:0.9}` is clear-ocean physics and is backward for the Salish green window. Keep `uDepthColorScale` as the green e-folding length, magnitude stays a modeled control. |
| WFX-R10 | `WFX-R10_seabed_interaction.md` | The depth pre-pass already renders and discards the opaque scene color, so seabed refraction is nearly free. Live `camera.far = fitRadius * 100` bands the shallow gradient, tighten it. Soft-shoreline feather reuses `column`. |
| WFX-R11 | `WFX-R11_salish_optics.md` | Cited Strait of Georgia optics, green at 530 nm penetrates deepest, blue dies first. Truthful sRGB targets, shallow `#4f8c79`, deep `#13302b`, underwater fog `#356f5d`. Extinction ratio green slowest, blue fastest. |
| WFX-R12 | `WFX-R12_surface_from_below.md` | Confirmed the surface is FrontSide so it vanishes from below, and a 40 m no-dunk clamp means nothing crosses the waterline today. Build a W4-owned underside material for the Snell window and TIR, dim and green for turbid water. |
| WFX-R13 | `WFX-R13_perf_adversarial.md` | The laptop is the binding tier and the baseline is already TWO full scene renders. Only the planar Reflector adds a third full render and can blow the laptop budget alone. Full budget table, ranking, and collision map. |

Synthesis (this doc), `SYNTHESIS_water_fx.md`.

---

## 2. The four faults, and what the research converged on

The operator reported four things, distracting water shading, a white sky, a stark abrasive
horizon, and no fog or sun light. The research resolved each to a concrete, file-cited root
cause, and on three of the four the findings converged independently.

1. Distracting water. The `pow(ndh,600.0)` glitter gated by a hard `step(0.55,noise)` and an
   unbounded additive white term at `depthWater.ts` lines 279 to 286 produce sub-pixel
   specular aliasing and an overshoot that ACES compresses to desaturated white. R01 and R13
   agree. The fix is an energy-conserving GGX lobe whose roughness grows with screen-space
   normal variance, plus a real Schlick Fresnel. R02 adds that the sub-Nyquist Gerstner waves
   W4 and W5 also shimmer and contribute to the distracting read.

2. White sky. Not a missing sky and not missing ACES. The r3f v8 Canvas already enables
   ACESFilmicToneMapping, but `toneMappingExposure` is left at 1.0 over a bright Preetham dome
   whose sun term is 19000.0, at a pinned 64.61 degree summer-noon sun. R04 and R05 agree, and
   R13 explicitly corrects R01's contrary premise that the renderer is at NoToneMapping. The
   fix is one renderer property near 0.5.

3. Stark horizon. Two stacked causes. The flat-sky Fresnel mixes one constant `#9fc4e0` so
   every grazing fragment collapses to a uniform band, and the linear fog at near 120 far 520
   is tuned for a far larger world than the 120-unit scene, so the opaque DEM horizon ring
   never dissolves. R01, R03, R04, R13 agree. The fixes are a view-dependent reflected-sky
   color, later a PMREM env sample, and a FogExp2 retune to the real scene scale.

4. No fog or sun light. The fog distance problem above, plus there is no visible sun disc
   tied to `makeSun` and no aerial perspective. R04 and R05 own this. Fog retune plus an
   optional sun disc plus the shared horizon color address it.

A fifth finding the operator did not ask for but the research surfaced. The water is too
blue and physically backward for the Salish Sea. The pending WS-BATHY extinction vector
`{r:3.0,g:1.6,b:0.9}` and the navy deep tints encode clear-blue-ocean physics where blue
survives deepest. R09 and R11 independently show, from measured Strait of Georgia optics,
that green penetrates deepest here and blue dies first. This is a correctness item, detailed
in section 5.

---

## 3. Ranked sequenced build plan, realism-gain-per-ms

Cheapest and highest impact first. Each lever states its estimated cost, its owning findings
doc, and its dependency. The first five levers are near-free and remove all four reported
faults. The expensive structural levers are below the line and are gated or cut.

| # | Lever | Est cost | Owner doc | Depends on |
| --- | --- | --- | --- | --- |
| 1 | Renderer exposure to about 0.5 | zero ms | R05 | none, fixes white sky at the source |
| 2 | Fog retune to FogExp2 at the 120-unit scene, soft ring top-edge feather | about zero ms | R04 | none, fixes stark horizon |
| 3 | Reflected-sky gradient Fresnel with the F0 0.02 floor | under 0.02 ms | R01 REC-B | the seam R03 env sample later swaps into |
| 4 | Energy-conserving GGX specular, variance-driven roughness | about 0.05 ms desktop, 0.1 to 0.4 ms laptop | R01 REC-A | must land with or after lever 1, or it still washes under ACES |
| 5 | Green recolor plus per-channel absorption, corrected green-window ratio | under 0.05 ms | R11, R09 | resolve the red coefficient conflict first, section 5 |
| 6 | `camera.far` tighten toward `fitRadius * 4` to `8` | free | R10 Rec C1 | edits the convergence file, fold into the W-CAM edit |
| 7 | Seabed refraction reusing the already-discarded color buffer | 0.1 to 0.3 ms | R10 Rec A | merge with lever 5 in one color-path rewrite |
| 8 | Soft shoreline contact feather | under 0.05 ms | R10 Rec B | reuses `column` |
| 9 | PMREM env sample replacing the flat sky in the Fresnel | under 0.1 ms per frame, one-time build | R03, R05 R05-3 | depends on lever 1 and on R05 owning the single PMREM build |
| 10 | Detail normal map for fine ripple, drop sub-Nyquist Gerstner waves | under 0.1 ms, vertex cost drops | R02 | a new texture asset, or the procedural-noise fallback |
| 11 | Phase-coupled foam run-up plus terrain wet-sand band | under 0.05 ms each | R06 | wet-sand lands in `terrainStylist.ts`, a different owner |
| 12 | Underwater FogExp2 swap and depth-graded tint, submerged only | about zero ms | R08 | a dive mode, fog color from R09, visibility from R11 |
| 13 | Weak seabed-local caustics | under 0.5 ms | R07 R07-A | low payoff in the default far view, ship weak or defer |
| 14 | Surface-from-below underside material | under 0.3 ms, submerged only | R12 | latent until a dive mode relaxes the no-dunk clamp |

Below the line, gated or cut.

- Planar Reflector. Adds a third full scene render, an estimated U on top of the 2U baseline.
  On the laptop tier this alone can exceed the 33.3 ms budget. High preset opt-in only, never
  the default. R03 and R13 agree.
- God-rays for the default top-down view. The sun is off-screen and there is no on-screen
  medium, so realism-per-ms is near zero, and it forces an EffectComposer the scene lacks.
  Cut for the demo unless a dive view is confirmed. R07 and R13 agree.
- FFT ocean. An estimated 40 to 80 fullscreen passes per frame on WebGL2 for fidelity the
  0.55 km mesh quad cannot display. The clearest cut in the lane. R02 and R13 agree.

The budget headline. The recommended default stack is the fold-in levers 1 through 13. R13
estimates the added per-frame cost at roughly 0.5 to 1.2 ms desktop and 0.6 to 1.8 ms
laptop, all folding into the two passes that already run. The binding constraint is not the
realism levers, it is U, the cost of one full scene render, and the laptop baseline of 2U.
No third full render should land until U is measured.

---

## 4. The merged depthWater.ts color-path rewrite

Four findings rewrite the same fragment block at `depthWater.ts` lines 272 to 291, and three
findings rewrite the same color path. They must be authored as ONE coherent water2 rewrite
under a single editor, not four separate patches to the same lines. R01, R03, R09, R10, and
R06 all say this independently.

The single merged edit composes, in order.

1. Per-channel Beer-Lambert body color, R09. `transmittance = exp(-(uAbsorption /
   uDepthColorScale) * column)`, `base = uColorShallow * transmittance + uColorDeep * (1 -
   transmittance)`. `uAbsorption = vec3(1.0)` reproduces the current monochrome frame exactly
   for a clean A/B. Coefficients and deep tint from R11.
2. Seabed refraction, R10 Rec A. Bind the existing discarded `depthTarget.texture` as
   `uSceneColor`, offset the screen UV by the surface normal with a depth guard, and feed the
   refracted seabed color into the body term so `seabedColor * transmittance` is the
   physically meaningful read. Flip the color attachment filter to linear.
3. Energy-conserving specular and reflected-sky Fresnel, R01 REC-A and REC-B. Replace the
   glitter and additive white with a GGX lobe and a Schlick Fresnel at F0 0.02, mixing toward
   a reflected-sky gradient that R03 later swaps for the PMREM env sample behind the same seam.
4. Soft shoreline feather, R10 Rec B, and phase-coupled foam run-up, R06 R06-A, both reusing
   the existing `column` and Gerstner phase, both preserving the land-never-washed invariant.
5. Vertex change, R02. Drop the sub-Nyquist waves, lower amplitude and steepness for a
   sheltered sea, sample a detail normal map for the fine ripple the mesh cannot carry.

This merged rewrite is sandbox-only build work in `web/lib/scene/water2/depthWater.ts`. It
edits no convergence file. The new uniforms it exposes, `uAbsorption`, `uSceneColor`,
`uRefractStrength`, `uContactSoftness`, `uRunup`, `uRoughness`, and the sky-gradient stops,
are public `Water2Options`, but the option object is constructed in `SalishScene.tsx`, so
wiring the feeds is a later convergence-file edit, section 6.

---

## 5. Dependency decisions needing O0 sign-off

These are the locked-decision conflicts, new-dependency choices, and scope calls the
sub-orchestrator is escalating rather than deciding. Per the charter, gated waves and any
of these decisions are O0's.

1. The absorption coefficient ordering, a locked-decision conflict. The pending WS-BATHY
   `WATER2_TUNING_REQUEST.md` and `PROPOSED_RGB_EXTINCTION = {r:3.0,g:1.6,b:0.9}` encode
   clear-blue-ocean physics. R09 and R11 both show, from measured Strait of Georgia optics,
   that the Salish ordering is inverted, green slowest, blue fastest. Adopting the pending
   request verbatim ships water that is too blue and physically backward, against the locked
   Salish-green constraint. Recommended decision, reverse the ordering toward green-survives,
   retarget the deep tint from navy toward turbid green near `#13302b`. This crosses the
   WS-BATHY style owner intent and needs an O0 call.

2. The red coefficient, a sub-conflict inside the same uniform. R09 recommends red 1.4, R11
   recommends red 3.0, for the same `uAbsorption`. Both agree green 1.0 lowest and blue 3.0
   highest. O0 picks one, it cannot be averaged silently. Recommendation, adopt R11's OM3
   deep-channel vector `{r:3.0, g:1.0, b:3.0}` for the deep channels the shader cares about,
   since R11 is the optics owner and grounds it in the clearer Pacific-fed OM3 water mass.

3. A detail normal-map texture asset, a new-asset choice. R02's primary path adds one small
   tiling water normal map to the bundle, on the order of tens to a few hundred KB as KTX2.
   The three-only fallback generates the detail normal procedurally from the existing
   value-noise with no asset. Recommendation, allow the texture asset for quality, accept the
   procedural fallback on the lowest tier.

4. The dive view, the single largest realism-per-ms scope call. R07 god-rays, R08 particulate
   and the underwater volume, and R12 surface-from-below are all latent until a dive mode
   relaxes the 40 m no-dunk camera clamp in `director.ts`. If the demo stays top-down and
   orbit, recommended cut is god-rays entirely, caustics to a weak deferred term, and
   surface-from-below deferred not built. If a dive is in scope, R08 defines the underwater
   module and R12 the underside material, both three-only.

5. The planar Reflector, a budget gate. It is the only lever that adds a third full scene
   render. Recommendation, default to the near-free PMREM env sample, gate the Reflector to a
   high quality preset that does not exist yet, and do not approve it until U is measured.

6. The EffectComposer, a structural and dependency decision. The scene renders
   direct-to-screen today. God-rays and an optional underwater fullscreen tint need a
   composer. Recommendation, stay direct-to-screen, introduce a composer at most once costed
   at the W5 post-fx layer, never charged to a single WATER-FX effect. The pmndrs
   `postprocessing` library is a new runtime dependency and is not recommended.

7. Measure U. No third full render should be approved until the twin W-PERFUX load-perf
   research replaces the estimated U of 2 to 5 ms desktop and 8 to 18 ms laptop with a
   measured number, because at the high end the laptop is already over budget from the 2U
   baseline alone.

8. The R01 premise correction. R01 section 1.2 states the renderer is NoToneMapping. ACES is
   on by the r3f default at exposure 1.0, verified by R04, R05, and R13. The energy-conserving
   specular recommendation stands, but the build must pair it with the exposure fix and not
   ship R01's stated cause.

---

## 6. Full collision map, SalishScene.tsx and globals.css vs the twin and LGC

### SalishScene.tsx, the contested convergence file

WATER-FX needs these edits landed in `web/app/components/scene/SalishScene.tsx`, all in a
later gated integrate wave.

- Renderer exposure near 0.5 and an optional sun disc, in the `onCreated` callback and the
  `<Canvas>` at lines 1007 to 1011. R05.
- Fog mode swap to FogExp2 or corrected near and far, where the realism fog is owned and
  retuned by `FogTuneRig`. R04.
- `scene.environment` assignment for the PMREM env, next to the existing `background: false`
  sky-dome seam at lines 245 to 255. R03, R05.
- Rewire the water `uSkyColor` feed at line 303 from the flat `skyColor(...)` to the env
  sample or the R01 gradient. R03.
- `camera.far` tighten at lines 550 to 554. R10 Rec C1.
- The new water uniform feeds in the `Water2Rig` option object at lines 275 to 326, for the
  merged rewrite uniforms in section 4.

Who else edits SalishScene.tsx, from the twin `wave_shape.yml` and the LGC lane.

| Lane or role | Edits SalishScene.tsx | Note |
| --- | --- | --- |
| W2.6 datum-integrator | Yes, plus depthWater.ts and useTilesLayer.ts | Changes the water level source. Gated and uncommitted as of 2026-06-28. Must land first. |
| W-CAM camera-rig | Yes, camera rig only | Must coordinate edit order with W4 and W-LABELS. Owns far-plane sign-off. |
| W-LABELS scene-mount | Yes, label mount, plus globals.css `.scene-label` | Sequenced after the LGC token drop and RP2 framing. |
| W4 integrator | Yes, sole convergence-file editor of its wave | Wires sky, materials, water2, underwater, modes. |
| W3 | No, sandbox-only this wave | Collides only on depthWater.ts and materials, not the convergence file. |
| LGC | globals.css `:root` tokens, not SalishScene.tsx | Shares the same serialization queue indirectly. |
| WFX integrate | Yes, the edits above | Recommend merging into the W4 integrator role. |

### globals.css, the LGC and labels seam

WATER-FX needs no `globals.css` edit. The collision there is between LGC, which owns the Part
A design tokens in `:root` and the glass classes, and W-LABELS, which owns the `.scene-label`
family and is sequenced after the LGC token drop. WATER-FX is relevant here only because its
integrate edit to SalishScene.tsx shares the same serialization queue as W-LABELS.

### depthWater.ts and waterTuning.ts, the shared shader seam

Not the convergence file, but the second contested seam.

- `depthWater.ts` is wanted by W2.6 datum-integrator, by W3 water-upgrade in the sandbox, and
  by the merged WFX color path of R01, R03, R09, and R10 Rec A. These must collapse to one
  editor per build window.
- `waterTuning.ts` is the WS-BATHY style owner's file. The R09 and R11 coefficient re-balance
  and deep-tint retarget reverse its original navy intent and need that owner's agreement
  through O0.
- `terrainStylist.ts` is W3 terrain-material and W2.6 tint-scale-fix territory. The R06
  wet-sand band lands there, not in water2.

### Recommended serialization order

1. W2.6 datum-integrator first, gated and committed. It changes the water level source and
   edits SalishScene.tsx, depthWater.ts, and useTilesLayer.ts together. Every WATER-FX water
   edit assumes the corrected NAVD88 0 m datum.
2. LGC Part A tokens into `globals.css :root`. Independent of WFX.
3. W-PERFUX RP2 resting framing and W-CAM camera rig. Fold the R10 Rec C1 `camera.far`
   tighten into the W-CAM edit, since W-CAM signs off on any far-plane change anyway.
4. W3 water-upgrade and the WFX-BUILD net-new water work, both sandbox-only and parallel, no
   SalishScene.tsx edit. Author the merged R01 plus R03 plus R09 plus R10 Rec A plus R06
   color-path rewrite of depthWater.ts here under a single editor, and resolve the R09 and
   R11 coefficient conflict against the WS-BATHY owner.
5. W-LABELS after the LGC tokens and RP2 framing.
6. WFX-INTEGRATE last, as a single serialized editor of SalishScene.tsx, landing exposure,
   fog, env assignment, the uSkyColor rewire, the water uniform feeds, and the camera.far
   change. Recommended, merge the WFX-INTEGRATE editor into the W4 integrator so SalishScene.tsx
   has exactly one owner across W4 and WATER-FX.

The single rule that prevents the worst collision, one editor of SalishScene.tsx per wave and
one editor of depthWater.ts per build window. Today five roles want SalishScene.tsx and three
want depthWater.ts. Collapsing each to one serialized editor is what the charter collision
lock already demands.

---

## 7. Recommended sequencing onto W3 and W4, or a new WFX-BUILD

The research maps cleanly onto the twin's existing visual program, so a separate WFX-BUILD
wave is not required. The recommendation is to land WATER-FX through the twin waves with
ownership coordinated by O0, rather than spawning a parallel build that would double-own
depthWater.ts and SalishScene.tsx.

- W3 world-materials-and-shading consumes levers 1 through 11 and 13. The sky-env agent owns
  the procedural sky, the PMREM env, and the renderer exposure decision with R04 and R05. The
  water-upgrade agent owns the merged depthWater.ts rewrite from section 4. The seabed-material
  agent owns the R07 caustic term. The terrain-material agent owns the R06 wet-sand band. The
  perf-harness agent owns the U measurement and the frame-time A/B in the `/world` sandbox.
- W4 underwater-and-exploration-modes consumes levers 12 and 14, only if a dive view is in
  scope. The underwater agent builds `web/lib/scene/underwater/` from R08. The water2 or
  underwater owner builds the R12 underside material. The camera-modes agent relaxes the
  no-dunk clamp. The W4 integrator is the sole SalishScene.tsx editor and should absorb the
  WFX-INTEGRATE edits.
- If O0 prefers WATER-FX to move ahead of the W3 and W4 gates, a net-new WFX-BUILD wave can
  author the same merged depthWater.ts rewrite and the sky and fog modules in the sandboxes,
  provided it is the single owner of depthWater.ts for that window and hands the SalishScene.tsx
  integrate to the same serialized editor the twin uses. This is an O0 promotion decision.

---

## 8. Open questions for O0, consolidated

1. Approve reversing the absorption ordering to green-survives and retargeting the deep tint
   from navy to turbid green, against the pending WS-BATHY request intent. Section 5 item 1.
2. Pick the red coefficient, R09's 1.4 or R11's 3.0, for `uAbsorption`. Recommendation, R11's
   `{r:3.0,g:1.0,b:3.0}`. Section 5 item 2.
3. Allow a detail normal-map texture asset, or require the procedural fallback. Section 5 item 3.
4. Confirm whether a dive view is in scope, which gates god-rays, the underwater volume, and
   surface-from-below. Section 5 item 4.
5. Confirm the planar Reflector is a high-preset opt-in, never the default. Section 5 item 5.
6. Confirm the renderer stays direct-to-screen with no EffectComposer outside a single W5 post
   layer. Section 5 item 6.
7. Direct W-PERFUX to measure U before any third full render is approved. Section 5 item 7.
8. Confirm the single-editor collapse, merging WFX-INTEGRATE into the W4 integrator and naming
   one editor for the merged depthWater.ts rewrite sequenced after W2.6. Section 6.
9. Confirm whether WATER-FX lands through W3 and W4 or through a net-new WFX-BUILD wave.
   Section 7.

---

## 9. Acceptance criteria for the later gated waves

From the charter, restated so the build and accept waves inherit them.

- The merged depthWater.ts rewrite type-checks clean, is tuned in the `/water` and `/world`
  sandboxes, and `uAbsorption = vec3(1.0)` reproduces the current frame for a clean A/B.
- Before and after frames are Read-examined at open-water surface, shoreline, dive or
  underwater if in scope, and the horizon at sunrise, noon, and sunset.
- The water reads physical and not distracting, the sky and horizon are soft with sun and fog,
  the underwater is turbid-green Salish optics, and there is no white-sky or stark-horizon
  regression.
- The frame-time A/B replaces every estimated millisecond in R13 section 2 with a measured
  number, and the full stack stays within 60 fps desktop and 30 fps laptop.
- The honesty label is intact. Every lever changes how the water looks and asserts no measured
  depth, color, or sea state. The seabed read stays the modeled CUDEM topobathy.
