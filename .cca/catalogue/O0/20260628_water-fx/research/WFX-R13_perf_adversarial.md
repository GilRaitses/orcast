# WFX-R13 perf-adversarial

Role WFX-R13, the adversarial read-only cross-cutting member of the WATER-FX Wave 1
research lane. Owns this one file only. No code changed. Reports to the WFX
sub-orchestrator, then O0.

Repo state verified against the charter pin origin/main
`915e4cc77923de93ed5f7e9a75feab9eb2e12896` (branch main, 2026-06-28).

Honesty label holds. Everything in the budget table is modeled, not measured. No dev
server was run, no frame was captured, per the locked read-only constraint. Every
millisecond number is an estimate derived from render-pass and ALU accounting, and each
carries its assumption inline. The single number most in need of real measurement is the
cost of one full opaque scene render of the streamed CUDEM tileset, which is the unit the
whole budget turns on. I flag it as estimated everywhere it appears.

My job is to be the skeptic. Where a sibling doc is optimistic, I say so. Where two
siblings contradict each other on a number the build will adopt, I surface it as a
correctness risk rather than averaging it away.

---

## 1. Budget baseline and current state, file-cited

Frame budget. 60 fps desktop is a 16.7 ms frame. 30 fps laptop is a 33.3 ms frame. This
is the charter constraint at `WAVESET_CHARTER.md` lines 72 to 74.

The live per-frame baseline is TWO full opaque scene renders, not one. The water depth
pre-pass renders the entire opaque scene every frame with the water hidden, then the main
pass renders it again. The pre-pass is here.

```375:383:web/lib/scene/water2/depthWater.ts
    renderDepthPrepass(renderer, scene, camera) {
      const prevTarget = renderer.getRenderTarget();
      const wasVisible = mesh.visible;
      mesh.visible = false;
      renderer.setRenderTarget(depthTarget);
      renderer.render(scene, camera);
      renderer.setRenderTarget(prevTarget);
      mesh.visible = wasVisible;
    },
```

It is driven unconditionally every frame from the convergence file.

```319:323:web/app/components/scene/SalishScene.tsx
    const handle = handleRef.current;
    if (!handle) return;
    handle.renderDepthPrepass(gl, scene, camera as THREE.PerspectiveCamera);
    handle.update(state.clock.elapsedTime, camera);
```

So the accounting unit for the rest of this doc is one full opaque scene render. Call it
U. The baseline is 2U per frame before any WATER-FX effect is added. WFX-R03 and WFX-R10
both confirm this two-render baseline from the same code, at `WFX-R03_reflections.md`
section 4 and `WFX-R10_seabed_interaction.md` section 4.

Estimated value of U, labeled estimated, no measurement taken. On a desktop discrete GPU
rendering the streamed multi-LoD CUDEM tileset I estimate U at 2 to 5 ms. On a weak laptop
integrated GPU I estimate U at 8 to 18 ms. The wide band is honest. The tile count, the
LoD error target, and the texture sizes that set U are exactly what the twin W-PERFUX
load-perf research is measuring at `RP1_load_perf.md`, and that number must replace this
estimate before any third full render is approved. The consequence of this estimate is the
headline of section 2. At 2U the laptop baseline is already 16 to 36 ms, which means the
laptop can already be at or over its 33.3 ms budget from the pre-pass alone, before a single
realism lever lands.

Renderer color state, corrected against a sibling claim. WFX-R01 section 1.2 asserts the
renderer is left at `NoToneMapping` and that specular above 1.0 hard-clamps to white at the
framebuffer. That premise is wrong. WFX-R04 section 1d and WFX-R05 section 1 both verified
that the react-three-fiber v8 `<Canvas>` defaults the renderer to `ACESFilmicToneMapping`
with `toneMappingExposure` left at 1.0, confirmed in the installed package. The wash is ACES
compression of a too-bright input at exposure 1.0, not a hard framebuffer clamp. The fix is
the exposure value, not adding ACES. R01's recommended energy-conserving specular is still
correct, but its stated cause is not. I flag this so the build does not ship R01's premise
as written. The `<Canvas>` and its only renderer mutation are here.

```1007:1011:web/app/components/scene/SalishScene.tsx
      <Canvas
        camera={{ position: [0, 28, 30], fov: 45, near: 1, far: 800 }}
        style={{ width: "100%", height: "100%", background: "linear-gradient(#0b1f33,#08263d)" }}
        onCreated={({ gl }) => gl.setClearColor("#08263d")}
      >
```

The water surface shading I am judging is the fragment block at
`web/lib/scene/water2/depthWater.ts` lines 272 to 291, read in full and quoted in section 3.

---

## 2. Full-stack frame-budget table

All ms numbers estimated, assumptions inline. U is one full opaque scene render, estimated
2 to 5 ms desktop and 8 to 18 ms laptop, per section 1. "Folds in" means the effect adds
only ALU or texture samples to a pass that already runs and adds zero new scene renders.
The cumulative column tracks the recommended default stack, not every row, and excludes the
two rows explicitly gated or cut.

| Effect, owner doc | Adds a full scene render? | Est ms desktop | Est ms laptop | Assumption |
| --- | --- | --- | --- | --- |
| Existing depth pre-pass | Yes, 1U, already in baseline | 2 to 5 | 8 to 18 | the dominant cost, estimated U, the number to measure first |
| Main render | Yes, 1U, already in baseline | 2 to 5 | 8 to 18 | the visible frame |
| R05 exposure set to 0.5 | No | 0 | 0 | a renderer property read inside the existing tonemap step |
| R04 procedural sky | No, already paid | ~0 added | ~0 added | one BackSide box, one draw call, already in the live scene |
| R04 FogExp2 or near/far retune | No | ~0 | ~0 | fog is a per-fragment term already compiled into materials |
| R01 in-shader BRDF, REC-A plus REC-B | No, folds in | ~0.05 | 0.1 to 0.4 | 30 to 45 extra ALU plus two dFdx on the water fragments only |
| R02 detail normal map | No, folds in | <0.1 | <0.1 | two texture samples, and vertex cost drops from fewer Gerstner terms |
| R09 per-channel absorption | No, folds in | <0.05 | <0.05 | two extra exp per water fragment over the current one |
| R11 green recolor | No | 0 | 0 | constant changes only, no per-frame cost |
| R10 Rec A seabed refraction | No, reuses discarded color buffer | 0.1 to 0.3 | 0.1 to 0.3 | one or two texture samples on water fragments, color buffer already rendered |
| R10 Rec B soft shoreline | No, folds in | <0.05 | <0.05 | reuses the existing column value |
| R10 Rec C1 camera.far tighten | No | free | free | changes the projection only, removes depth banding |
| R06 foam run-up plus wet sand | No, folds in | <0.05 | <0.05 | a few ALU on water and terrain fragments |
| R03 PMREM env sample | No per frame, one-time build | <0.1 per frame | <0.1 per frame | replaces the flat mix with one prefiltered env lookup, sun pinned |
| R05 PMREM regen, sun pinned | No per frame | 0 steady, one-time few ms | 0 steady, one-time tens of ms | fromScene runs once at load, not per frame |
| R07 caustics term | No, folds in | <0.2 | 0.3 to 0.5 | two texture fetches on the seabed or water fragments |
| R03 planar Reflector | YES, adds 1U, third full render | +2 to 5 | +8 to 18 | renders the whole scene a second time from the mirror camera |
| R05 PMREM regen if sun animates | No new render, but per-event | per-event few ms | per-event tens of ms | fromScene re-renders and re-prefilters the sky on every sun change |
| R07 god-rays, deferred | Composer plus fullscreen passes | +1 to 3 at half res | more, plus composer copy | needs an EffectComposer the scene lacks, reorders the render path |
| R08 underwater FogExp2 | No, folds in, submerged only | ~0 | ~0 | fog swap, active only below the waterline |
| R08 particulate Points | No, one draw call, gated off | <0.5 | <0.5 | a few thousand additive sprites, preset-gated |
| R12 surface-from-below | No new scene pass, one extra draw | <0.3 | <0.3 | second plane drawn only while submerged |

Cumulative for the recommended default stack, on top of the 2U baseline and excluding the
planar Reflector, god-rays, and submerged-only items, the added per-frame cost is the sum of
the fold-in rows. Desktop adds roughly 0.5 to 1.2 ms. Laptop adds roughly 0.6 to 1.8 ms.
Against a desktop frame of 16.7 ms minus 2U of 4 to 10 ms, the default stack fits with
clear headroom. Against a laptop frame of 33.3 ms minus 2U of 16 to 36 ms, the default
stack fits only if U is at the low end of its estimated band, and does not fit if U is at
the high end. The binding constraint is the laptop, and the binding cost is U, not the
realism levers.

How many add a full extra scene render, the expensive unit. Of every proposed effect,
exactly one adds a third full scene render per frame, the R03 planar Reflector. The R07
god-rays path does not add a full scene render but it stands up an EffectComposer and stacks
fullscreen passes plus a fullscreen copy onto a pipeline that is currently direct-to-screen,
which is the second most expensive structural change. R05 PMREM is one-time while the sun is
pinned and only becomes a per-event cost if a time-of-day control animates the sun. Every
other effect folds into a pass that already runs.

Which combination blows budget. On the laptop tier, the depth pre-pass plus the planar
Reflector is three full scene renders, an estimated 24 to 54 ms before any shading, which
exceeds the 33.3 ms budget across most of the estimated U band on its own. Adding the
god-rays composer on top is unrecoverable on the laptop. The default stack of fold-in
effects does not blow budget on either tier. The risk is entirely in the two expensive
structural levers, the planar Reflector as a default and a god-rays composer, not in the
shader-math levers.

---

## 3. Adversarial findings

### 3a. What reads distracting and unreal, cited to the exact lines

The distracting sparkle is two hand-picked exponents and an unbounded additive white term.

```279:286:web/lib/scene/water2/depthWater.ts
    float spec = pow(ndh, 90.0);
    float glitter = pow(ndh, 600.0) *
      step(0.55, noise(vPlanePos * 7.0 + vec2(uTime * 0.9, -uTime * 0.7)));
    float diff = clamp(dot(n, sun), 0.0, 1.0);

    vec3 color = base * (0.6 + 0.4 * diff);
    color = mix(color, uSkyColor, fres * uFresnelStrength);
    color += vec3(1.0, 0.97, 0.9) * (spec * 0.8 + glitter * 1.4);
```

The `pow(ndh, 600.0)` glitter lobe is a few milliradians wide, far below the pixel footprint
of a normal interpolated across a 180 by 180 plane that spans 192 by 144 scene units, so the
lobe turns on and off between adjacent frames and pixels. That is specular aliasing, and
WFX-R01 fault F1 derives it correctly. The `step(0.55, noise(...))` is a hard binary mask
that adds its own flicker on top. The additive term `vec3(1.0, 0.97, 0.9) * (spec * 0.8 +
glitter * 1.4)` is not Fresnel-weighted, not gated by N dot L, and the glitter is scaled by
1.4 so it deliberately overshoots 1.0. Under ACES at exposure 1.0 that overshoot compresses
toward desaturated white rather than reading as a bounded highlight. This is the main source
of the distracting read, and the fix is WFX-R01 REC-A, an energy-conserving GGX lobe whose
width is driven by a roughness that grows with screen-space normal variance so it can never
be narrower than the pixel.

The stark flat-sky Fresnel is one line reflecting one constant color.

```272:285:web/lib/scene/water2/depthWater.ts
    float fres = pow(1.0 - max(dot(n, viewDir), 0.0), 5.0);
```
```285:285:web/lib/scene/water2/depthWater.ts
    color = mix(color, uSkyColor, fres * uFresnelStrength);
```

`uSkyColor` defaults to the single flat `DEFAULT_SKY = "#9fc4e0"` at `depthWater.ts` line
113, and the live scene feeds it one flat color from `skyColor(sun.elevationDeg)` at
`SalishScene.tsx` line 303. Every grazing fragment near the horizon lerps to that one color,
so the entire grazing band collapses to a uniform line. The Schlick shape also drops the F0
floor, so it reads 0 at normal incidence instead of the physical 0.02 for water at IOR 1.33.
WFX-R01 faults F3 and F4 own this, and the fix is REC-B, a view-dependent reflected-sky
color, with R03's PMREM env sample as the higher-fidelity swap behind the same seam.

### 3b. The white-sky and stark-horizon regression, root cause

White sky. Verified to be an exposure interaction, not a missing sky and not a missing ACES.
The Preetham `Sky` addon writes a sun term of 19000.0 and a bright dome and then runs the
renderer tonemap on its own output, at `web/node_modules/three/examples/jsm/objects/Sky.js`
lines 203 to 212, cited by WFX-R05 section 1. The canonical three sky example pairs that
shader with `toneMappingExposure = 0.5`. The live scene leaves exposure at 1.0, roughly twice
the reference, with a 64.61 degree summer-noon sun at the pinned `SCENE_TIME` of
2026-06-27T20:00:00Z, `SalishScene.tsx` line 146, which maximizes the Preetham radiance. ACES
then compresses the high values toward near-white. The fix is the single renderer property
WFX-R05 R05-1 names, exposure near 0.5. This is the cheapest realism win in the lane and it
costs zero ms.

Stark horizon. Two stacked causes, both verified. First, the DEM horizon ring is an opaque
`MeshStandardMaterial` that relies on `scene.fog` to dissolve.

```226:233:web/lib/scene/decor/horizonRing.ts
  const material = new THREE.MeshStandardMaterial({
    vertexColors: true,
    roughness: opts.roughness ?? DEFAULTS.roughness,
    metalness: 0,
    // Share the scene fog so the ring dissolves into the horizon haze.
    fog: true,
    side: THREE.FrontSide,
  });
```

Second, the fog never reaches it. The realism fog is linear with near 120 and far 520
(`atmosphere.ts` lines 22 to 25, cited by WFX-R04 section 1e), but the rendered scene is only
about 120 units wide, so the served terrain and the inner horizon ring get zero fog and the
far ring only half dissolves. The ring is doing exactly what it promised, the fog distances
are tuned for a far larger world than the scene renders. The Preetham sky also does not read
`scene.fog`, so there is a hard material boundary where the half-fogged ring meets the
unfogged dome. The fix is WFX-R04 R3, swap to `THREE.FogExp2` at a density tuned to the
120-unit scene, or pull the linear near and far in, plus a soft top-edge feather on the ring.
Both fixes cost about zero ms because fog is already a per-fragment term in the existing
passes. The gradient fallback dome reads pale blue-grey at `sky.ts` lines 121 to 122, which
confirms the white-out is specific to the Preetham path under exposure 1.0, not a sky-color
choice.

The adversarial point for O0. The white sky and stark horizon are not solved by adding
passes. They are solved by one exposure property and one fog retune, both near-zero ms, both
landing in the convergence file. The expensive levers do not touch this regression at all.

### 3c. The coefficient-ordering conflict, a correctness risk

The pending WS-BATHY request encodes the wrong physics for this water, and two sibling docs
independently caught it. The pending vector is here.

```55:59:web/lib/scene/bathy/style/waterTuning.ts
export const PROPOSED_RGB_EXTINCTION: { r: number; g: number; b: number } = {
  r: 3.0,
  g: 1.6,
  b: 0.9,
};
```

This puts blue at the lowest extinction, so blue survives deepest and the deep read goes
navy and violet, which is clear blue-ocean physics. WFX-R11 section 3.1 and WFX-R09 headline
both show the Salish Sea inverts this. Measured Strait of Georgia optics in Loos, Costa and
Johannessen 2017 show blue and red attenuated fastest and green surviving deepest, a green
window. The correct ordering is green slowest, then red, with blue fastest, and the deep
tint must retarget from the navy `#0b2140` at `waterTuning.ts` line 35 and `#0a2540` at
`depthWater.ts` line 111 toward a turbid green-grey near `#13302b`. If the build adopts the
pending request verbatim it ships water that is both too blue and physically backward for
the Salish Sea, against the locked charter constraint at `WAVESET_CHARTER.md` lines 65 to 66.

The sub-conflict the build must resolve. The two siblings that feed the same `uAbsorption`
uniform agree green equals 1.0 lowest and blue near 3.0 highest, but they disagree on red.
WFX-R09 section 3b recommends `vec3(R 1.4, G 1.0, B 3.0)`. WFX-R11 section 3.2 recommends the
OM3 deep-channel vector `{r: 3.0, g: 1.0, b: 3.0}`. That is a red coefficient of 1.4 versus
3.0 for the same shader uniform. The build cannot adopt both. This is a correctness item for
O0, not a number to average. The ratio is physics, the magnitude is a modeled look control
through `uDepthColorScale`, and R09 section 3b is explicit that a literal per-meter Kd over
the compressed scene scale would render a flat opaque column with no gradient, so the
magnitude stays modeled. The deep-tint retarget also reverses the stated navy and violet
intent of the original WS-BATHY request, so it crosses the style owner and needs an O0 call.

### 3d. Levers with poor realism-per-ms, candidates to cut

Three levers cost real budget or structure for little visible return in the default
top-down orbit view, and I name them as cuts.

The R03 planar Reflector as a default. It is the only effect that adds a third full scene
render, an estimated U on top of the baseline 2U, and on the laptop tier that alone can
exceed the 33.3 ms budget. Its only advantage over the PMREM env sample is that it reflects
the horizon-ring land and scene objects, not just the sky. In a turbid green sea viewed from
a high orbit camera, a sky-only reflection from the near-free PMREM env sample carries the
horizon fix at under 0.1 ms per frame. Reserve planar for an opt-in high preset, never the
default. WFX-R03 section 3 reaches the same conclusion.

The R07 god-rays for the default view. The sun is not in frame in a top-down orbit view and
there is no on-screen medium above the water, so screen-space god-rays have nothing to
scatter through and nothing to radiate from. Realism-per-ms is effectively zero, and the
technique forces an EffectComposer the scene does not have. WFX-R07 section 3b recommends
skip for the default view and defer to a future dive view behind a preset. I agree and call
it a cut for the demo unless an underwater dive is confirmed in scope.

The R07 caustics in the default far view. Caustics on the seabed seen through a thin turbid
column from a far orbit camera are sub-pixel and low-contrast by the optics WFX-R07 section 6
documents, secchi depth a few meters so caustic contrast collapses within roughly one
secchi. The term is cheap at under 0.5 ms but its visible payoff in the default view is near
zero. Ship it weak and seabed-local only, or defer it to a dive view. It is not a budget
risk, it is a low-priority lever that should not be sequenced ahead of the exposure, fog,
BRDF, and recolor work.

WFX-R02 already rejects FFT ocean for this tilted-map view at section 4, and I concur. A
WebGL2 ping-pong FFT is 40 to 80 fullscreen passes per frame for fidelity the 0.55 km mesh
quad cannot even display. It is the clearest cut in the lane.

---

## 4. Ranked levers by realism-gain-per-ms

Cheap and high-impact first. Each row states the cost and the owning doc. All ms estimated
per section 2.

1. R05 exposure to 0.5. Zero ms. Fixes the white sky at the source. Highest realism per ms
   in the lane. `WFX-R05` R05-1.
2. R04 fog retune to FogExp2 or corrected near and far. About zero ms. Fixes the stark
   horizon by letting the ring and far terrain dissolve. `WFX-R04` R3.
3. R01 REC-B reflected-sky gradient plus real Schlick Fresnel with the F0 floor. Under
   0.02 ms. Removes the flat-sky stark band and is the seam the env sample later swaps into.
   `WFX-R01` REC-B.
4. R01 REC-A energy-conserving GGX specular with variance-driven roughness. About 0.05 ms
   desktop, 0.1 to 0.4 ms laptop. Kills the distracting sub-pixel glitter and the unbounded
   white. Must land with or after R05 exposure or it still washes under ACES. `WFX-R01`
   REC-A.
5. R11 green recolor plus R09 per-channel absorption with the corrected green-window ratio.
   Under 0.05 ms. Fixes the too-blue unreal water and the wrong deep tint. Resolve the red
   coefficient conflict from section 3c first. `WFX-R11`, `WFX-R09`.
6. R10 Rec C1 camera.far tighten. Free. Removes the shallow-gradient depth banding the live
   far over near ratio of 200000 causes. Edits the convergence file, needs W-CAM sign-off.
   `WFX-R10` Rec C, C1.
7. R10 Rec A seabed refraction reusing the already-discarded color attachment. 0.1 to 0.3
   ms. High realism for no new pass, because the pre-pass already renders and throws away
   the opaque color. `WFX-R10` Rec A.
8. R10 Rec B soft shoreline contact feather. Under 0.05 ms. Removes the hard waterline seam.
   `WFX-R10` Rec B.
9. R03 PMREM env sample replacing the flat sky in the Fresnel. Under 0.1 ms per frame plus a
   one-time build while the sun is pinned. The real horizon fix, depends on R05 owning the
   single PMREM build. `WFX-R03`, `WFX-R05` R05-3.
10. R02 detail normal map for fine ripple the mesh cannot carry. Under 0.1 ms, and the
    vertex stage gets cheaper from fewer Gerstner terms. `WFX-R02`.
11. R06 phase-coupled foam run-up plus terrain wet-sand band. Under 0.05 ms each, no new
    pass. `WFX-R06`.
12. R08 underwater FogExp2 swap and depth-graded tint, submerged only. About zero ms,
    active only below the waterline. `WFX-R08`.
13. R07 weak seabed-local caustics. Under 0.5 ms, low payoff in the default far view, ship
    weak or defer. `WFX-R07` R07-A.
14. R12 surface-from-below underside material. Under 0.3 ms, only while submerged, latent
    until a dive mode relaxes the no-dunk camera clamp. `WFX-R12`.

Below the line, gated or cut. R03 planar Reflector, high preset only, adds a full render.
R07 god-rays, cut for the default view, defer to a confirmed dive view behind a preset. FFT
ocean, cut. R05 PMREM per-frame regen, only if the sun is ever animated, and then it must be
throttled.

---

## 5. Collision map

Every SalishScene.tsx and globals.css edit a later WFX build or integrate needs, with the
twin and LGC owners that also edit those files, and a recommended serialization order.

### SalishScene.tsx, the convergence file, the contested seam

WATER-FX needs these edits landed in `SalishScene.tsx`.

- R05 exposure and the optional sun disc, in the `onCreated` callback and the `<Canvas>`
  element at lines 1007 to 1011. `WFX-R05` section 5.
- R04 fog mode swap to FogExp2 or the corrected near and far, where the fog is owned in the
  realism mount and retuned by `FogTuneRig`. `WFX-R04` R3 and section 5.
- R03 and R05 `scene.environment` assignment for the PMREM env, slotting next to the
  existing `background: false` sky-dome seam at lines 245 to 255. `WFX-R03` section 5.
- R03 rewire of the water `uSkyColor` feed at line 303 from the flat `skyColor(...)` to the
  env sample or the R01 gradient.
- R10 Rec C1 `camera.far` tighten at lines 550 to 554. `WFX-R10` Rec C1.
- The new water uniform feeds passed into the `Water2Rig` option object at lines 275 to 326,
  for R01 `uRoughness` and the sky-gradient stops, R09 `uAbsorption`, R10 `uRefractStrength`
  and `uContactSoftness`, R06 `uRunup`. These are public `Water2Options`, but the option
  object itself is constructed in `SalishScene.tsx`, so adding fields touches the file.

Who else edits `SalishScene.tsx`, from `wave_shape.yml`.

- W4 integrator is the sole convergence-file editor of its wave, owning the full wire-up of
  sky, materials, water2, underwater, and modes. `wave_shape.yml` line 190.
- W2.6 datum-integrator owns `SalishScene.tsx` plus `depthWater.ts` plus `useTilesLayer.ts`
  together, and changes the water level source. `wave_shape.yml` line 93. This is gated and
  uncommitted as of 2026-06-28.
- W-CAM camera-rig edits the camera rig only and must coordinate edit order with W4 and
  W-LABELS. `wave_shape.yml` lines 104 and 109.
- W-LABELS scene-mount edits the label mount in `SalishScene.tsx` and the `.scene-label`
  family in `globals.css`. `wave_shape.yml` line 133.
- W3 does NOT edit `SalishScene.tsx` this wave, it is sandbox-only. `wave_shape.yml` line
  163. So W3 is not a `SalishScene.tsx` collision, only a `depthWater.ts` and materials
  collision, handled below.

### globals.css, the LGC and labels seam

WATER-FX needs no `globals.css` edit. The collision there is between LGC and W-LABELS, and
it is relevant only because the WFX integrate edit to `SalishScene.tsx` shares the same
serialization queue.

- LGC owns the Part A design tokens dropped into `web/app/globals.css :root` and the
  `.glass-surface` and chat-shell classes. `TOKEN_HANDOFF.md` lines 9 to 11 and 55 to 61.
- W-LABELS owns the `.scene-label` family in `globals.css` and is sequenced after the LGC
  token drop and after the RP2 resting framing. `wave_shape.yml` lines 121 and 133,
  `TOKEN_HANDOFF.md` lines 37 to 41.

### depthWater.ts and waterTuning.ts, the shared shader seam

These are not the convergence file but they are the second contested seam, because four WFX
edits plus two twin owners all want the same fragment color path.

- `depthWater.ts` is wanted by W2.6 datum-integrator (`wave_shape.yml` line 93), by W3
  water-upgrade in the sandbox (`wave_shape.yml` line 175), and by the combined WFX color
  path of R01, R03, R09, and R10 Rec A. WFX-R01 section 6, WFX-R10 section 5, and WFX-R09
  section 5 all independently say these must merge into one editor, because R01 owns the
  Fresnel and specular, R03 owns what the surface reflects toward, R09 owns the per-channel
  absorption, and R10 Rec A owns the seabed color the absorption attenuates. Four agents
  rewriting lines 272 to 291 separately would collide.
- `waterTuning.ts` is owned by the WS-BATHY style owner, and the R09 and R11 coefficient
  re-balance and deep-tint retarget reverse the original navy intent there. WFX-R09 section
  5 and WFX-R11 section 5.
- `terrainStylist.ts` is W3 terrain-material and W2.6 tint-scale-fix territory, and the R06
  wet-sand band lands there, not in water2. WFX-R06 section 5.

### Recommended serialization order

1. W2.6 datum-integrator first, gated and committed. It changes the water level source and
   edits `SalishScene.tsx`, `depthWater.ts`, and `useTilesLayer.ts` together, and every
   WATER-FX water edit assumes the corrected NAVD88 0 m datum. Nothing else touching those
   files should land before it.
2. LGC Part A tokens into `globals.css :root`. Unblocks the labels styling, independent of
   WFX.
3. W-PERFUX RP2 resting framing and W-CAM camera rig, which also fix `camera.far` framing,
   so the R10 Rec C1 far tighten should be folded into the W-CAM edit rather than landed
   separately, since W-CAM must sign off on any far-plane change anyway.
4. W3 water-upgrade and the WFX-BUILD net-new water modules, both sandbox-only and parallel,
   no `SalishScene.tsx` edit. This is where the merged R01 plus R03 plus R09 plus R10 Rec A
   color-path rewrite of `depthWater.ts` is authored under a single editor, and where the
   R09 and R11 coefficient conflict is resolved against the WS-BATHY owner.
5. W-LABELS after the LGC tokens and RP2 framing, editing `globals.css .scene-label` and the
   `SalishScene.tsx` label mount.
6. WFX-INTEGRATE last, as a single serialized editor of `SalishScene.tsx`, landing exposure,
   fog, env assignment, the `uSkyColor` rewire, the water uniform feeds, and the camera.far
   change. The cleanest outcome is to merge the WFX-INTEGRATE editor into the W4 integrator
   role so there is exactly one convergence-file editor across W4 and WATER-FX, not two
   competing ones.

The single rule that prevents the worst collision. There must be one editor of
`SalishScene.tsx` per wave and one editor of `depthWater.ts` per build window. Today five
roles want `SalishScene.tsx`, the W2.6 datum-integrator, W-CAM, W-LABELS, the W4 integrator,
and the WFX integrate editor, and three roles want `depthWater.ts`, W2.6, W3 water-upgrade,
and the merged WFX color path. Collapsing each to a single serialized editor is the
prerequisite the charter collision lock at `WAVESET_CHARTER.md` lines 69 to 71 already
demands.

---

## 6. Open questions and recommended cuts for O0

1. Measure U. The whole budget turns on the cost of one full opaque scene render, estimated
   here at 2 to 5 ms desktop and 8 to 18 ms laptop. The twin W-PERFUX load-perf research is
   already measuring the tile count, LoD, and texture sizes that set it. No third full render,
   meaning the planar Reflector, should be approved until U is measured, because at the high
   end of the estimate the laptop is already over budget from the 2U baseline alone.

2. Resolve the red absorption coefficient. WFX-R09 recommends red 1.4 and WFX-R11 recommends
   red 3.0 for the same `uAbsorption` uniform. Both agree green 1.0 lowest and blue 3.0
   highest. O0 picks one value, it cannot be averaged silently. This also approves reversing
   the pending WS-BATHY navy intent toward turbid green, which crosses the style owner.

3. Confirm the dive view is in or out of scope for the demo. WFX-R07 god-rays, WFX-R08
   particulate and raymarch, and WFX-R12 surface-from-below are all latent until a dive mode
   relaxes the no-dunk camera clamp. If the demo stays top-down and orbit, recommended cut is
   god-rays entirely, caustics to a weak deferred term, and surface-from-below deferred not
   built. This is the single largest realism-per-ms decision in the lane.

4. Confirm the planar Reflector is a high-preset opt-in, never the default. The PMREM env
   sample carries the horizon fix at near-free per-frame cost. The Reflector adds a full
   scene render for the marginal gain of reflecting land. Recommended default is the env
   sample, Reflector gated to a quality tier that does not exist yet.

5. Confirm the renderer stays direct-to-screen with no EffectComposer. If no composer is
   stood up, god-rays and the optional underwater fullscreen tint are off the table on WebGL,
   which is the cleaner budget outcome. A composer should only be introduced once, costed at
   the W5 post-fx layer, not charged to any single WATER-FX effect.

6. Confirm the single-editor collapse. Merge the WFX integrate editor into the W4 integrator
   so `SalishScene.tsx` has one owner, and assign one editor for the merged R01 plus R03 plus
   R09 plus R10 color-path rewrite of `depthWater.ts`, sequenced after the W2.6 datum fix.

7. Correct the R01 premise before build. R01 section 1.2 states the renderer is
   `NoToneMapping` and highlights hard-clamp to white. ACES is on by the r3f default at
   exposure 1.0, verified by R04 and R05. The energy-conserving specular recommendation
   stands, but the build must pair it with the R05 exposure fix and not ship R01's stated
   cause.

8. Honesty label intact. Every realism lever changes how the water looks and asserts no
   measured depth, color, or sea state. The seabed read stays the modeled CUDEM topobathy.
   The acceptance frames in a later gated wave must be Read-examined for no white-sky and no
   stark-horizon regression, per `WAVESET_CHARTER.md` line 149, and the frame-time A/B must
   replace every estimate in section 2 with a measured number.

---

## Appendix, verified paths cited

- `web/lib/scene/water2/depthWater.ts` fragment block lines 225 to 295, specular lines 279
  to 286, flat-sky Fresnel lines 272 to 285, default sky line 113, navy deep line 111,
  pre-pass lines 375 to 383, material side FrontSide line 332, uniforms lines 333 to 355.
- `web/app/components/scene/SalishScene.tsx` Canvas and onCreated lines 1007 to 1011, pinned
  time line 146, pre-pass call lines 319 to 323, Water2Rig lines 275 to 326, camera near and
  far lines 550 to 554, background:false lines 245 to 255, uSkyColor feed line 303.
- `web/lib/scene/decor/sky.ts` Preetham uniforms lines 95 to 104, gradient fallback colors
  lines 121 to 122.
- `web/lib/scene/decor/horizonRing.ts` opaque fog-reliant material lines 226 to 233.
- `web/lib/scene/bathy/style/waterTuning.ts` pending extinction vector lines 55 to 59, navy
  deep line 35.
- `web/node_modules/three/examples/jsm/objects/Sky.js` sun term lines 203 to 212, via
  WFX-R05.
- `.cca/catalogue/O0/20260628_water-fx/WAVESET_CHARTER.md` budget lines 72 to 74, collision
  lock lines 69 to 71, Salish-green lock lines 65 to 66, accept lines 145 to 149.
- `.cca/catalogue/O0/20260627_terrain-bathymetry-twin/wave_shape.yml` W2.6 line 93, W-CAM
  lines 98 to 111, W-LABELS lines 118 to 135, W3 lines 159 to 178, W4 lines 180 to 197, W5
  post-fx line 207.
- `.cca/catalogue/O0/20260628_liquid-glass-console/TOKEN_HANDOFF.md` globals.css :root token
  ownership lines 9 to 11 and 55 to 61.
- Sibling findings WFX-R01 through WFX-R12 in
  `.cca/catalogue/O0/20260628_water-fx/research/`, harvested for the per-effect ms estimates
  and the per-doc faults and recommendations cited throughout.
