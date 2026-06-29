# WATER-FX O0 sign-off (2026-06-28)

Ratifies the open questions in `research/SYNTHESIS_water_fx.md` section 8. O0 has
authority for these; the operator authorized "sign off where reasonable." All calls
adopt the research recommendation unless noted. Honesty label intact: every lever
changes how water/sky look and asserts no measured depth, color, or sea state.

| # | Decision | Call | Basis |
|---|---|---|---|
| 1 | Absorption ordering | **Green-survives** (reverse the clear-ocean default); retarget deep tint navy -> turbid green `#13302b` | Measured Strait of Georgia optics, R09 + R11 |
| 2 | Red coefficient | **R11 `uAbsorption ~ {r:3.0, g:1.0, b:3.0}`** | R11 is the optics owner |
| 3 | Detail normal map | **Allow** a small KTX2 tiling normal map; procedural-noise fallback on lowest tier | R02 |
| 4 | Dive / underwater view | **IN SCOPE** | The underwater orca view is a stated product requirement; unblocks R08 underwater volume + R12 underside material |
| 5 | Planar Reflector | **High-preset opt-in only, never default** | R03 + R13 budget |
| 6 | EffectComposer | **Stay direct-to-screen**; a composer only at a single future W5 post layer; no pmndrs `postprocessing` runtime dep | R13 |
| 7 | God-rays | **Cut for default**; caustics ship **weak**; full shafts deferred behind the dive preset | R07 + R13 |
| 8 | Measure `U` | **Required before any third full render** (Reflector stays gated until measured) | R13 |
| 9 | Editor discipline | **Single editor of `depthWater.ts`** for the merged R01+R03+R09+R10+R06 rewrite, **sequenced after W2.6 datum-integrator**; **WFX-INTEGRATE merges into the W4 SalishScene editor** | Section 6 collision map |
| 10 | Lane home | **Land through twin W3/W4** (no parallel WFX-BUILD double-owning the shared files) | Section 7 |

## Build gating consequence
WATER-FX build is **NOT a Wave-0 parallel lane**: it is blocked on W2.6 datum-integrator
landing first and contends `depthWater.ts` / `SalishScene.tsx`. It is sign-off-ready and
queued behind W2.6 under a single serialized editor. No WFX build dispatched now.

## WS-BATHY owner ratification (2026-06-29)
The operator, who owns the WS-BATHY style file `web/lib/scene/bathy/style/waterTuning.ts`,
signed off on the decision-1/2 green-survives retarget. Applied to the owner's file:
- `WATER_TUNED_SHALLOW` `#2f8fa6` -> `#4f8c79`
- `WATER_TUNED_DEEP` `#0b2140` (navy) -> `#13302b` (turbid green)
- `PROPOSED_RGB_EXTINCTION` `{r:3.0,g:1.6,b:0.9}` (clear-ocean, blue-survives) ->
  `{r:3.0,g:1.0,b:3.0}` (R11 green-survives)

This unblocks the cross-owner item flagged by WFX. The W4 single editor consumes these
constants when wiring the `Water2Rig` absorption/tint feeds; final green-survives look is
verified in-scene on the GPU render host at integrate, not in the /water sandbox (which
uses its own rig controls and does not read `waterTuning.ts`).
