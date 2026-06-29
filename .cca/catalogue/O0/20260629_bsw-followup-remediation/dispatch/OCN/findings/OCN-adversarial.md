# OCN-R4 adversarial audit, measured-ocean-stratification

Read-only research finding. OCN-R wave. I answer to the OCN sub-orchestrator. I edited no code and committed nothing. This file is the only artifact.

Repo seams read in full: `web/lib/scene/ocean/interpretiveOceanLayer.ts`, `web/lib/scene/ocean/doubleDiffusion.ts`, `web/lib/scene/ocean/stratification.ts`, `web/lib/scene/ocean/perf.ts`, `web/lib/scene/ocean/index.ts`, `web/lib/scene/water2/depthWater.ts` `Water2Handle` and `renderDepthPrepass`, `web/lib/scene/wfx/WIRING-slice-note.md`, `.cca/CLAIM_BOUNDARIES.md`, `.cursor/rules/prose-gate.mdc`, `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/research/BSW-R09_ocean_process_layer.md`, plus the OCN charter and dispatch prompt.

## Verdict

The planned work is buildable inside the existing honesty frame, but it carries one unavoidable P0 trap that will crash the layer at import time if the author writes the measured provenance the natural way. The guard does a plain case-insensitive `includes()`, so a negated forbidden phrase still throws. Everything else is containable with the checklists below.

## P0 ledger

### P0-1 Negated forbidden phrase still trips the substring guard

This is the top finding. `assertNoForbiddenClaim` lowercases each text and runs `lower.includes(phrase)` against every entry in `FORBIDDEN_OCEAN_CLAIMS`. It has no word boundary, no negation awareness, and no context. A sentence that NEGATES a forbidden claim still contains the forbidden substring and therefore throws.

```13:47:web/lib/scene/ocean/interpretiveOceanLayer.ts
export const FORBIDDEN_OCEAN_CLAIMS = [
  "measured thermohaline",
  "biosonar perception",
  "biosonar reveals",
  "what the whale sees",
  "salt fingering observed",
] as const;

export function assertNoForbiddenClaim(...texts: string[]): void {
  for (const text of texts) {
    const lower = text.toLowerCase();
    for (const phrase of FORBIDDEN_OCEAN_CLAIMS) {
      if (lower.includes(phrase)) {
        throw new Error(`interpretiveOceanLayer: forbidden claim in copy: ${phrase}`);
      }
    }
  }
}
```

This guard runs at module load on the shipped labels (line 50) and again at layer construction on `profile.provenance` (line 164 of `doubleDiffusion.ts`). The new measured-CTD provenance string is the most exposed surface, because the author writing it WANTS to disclaim "this is not measured thermohaline structure" and to note "salt fingering is not observed in the open Salish basin". Both of those honest disclaimers contain a forbidden substring verbatim and will throw at construction. The BSW campaign already crashed once on a negated "biosonar perception" phrase, so this is a demonstrated failure mode, not a hypothetical.

A throw here is not a soft fail. `createDoubleDiffusionLayer` runs at scene mount, so a bad provenance string takes down the whole scene, not just the ocean layer.

Forbidden substrings a measured-CTD provenance is most likely to include by accident, with safe rewrites:

| Forbidden substring | Tempting wording that throws | Why it throws | Safe phrasing |
|---|---|---|---|
| `measured thermohaline` | "measured CTD cast, not measured thermohaline structure" | `measured thermohaline` appears verbatim even though negated | "measured CTD cast of depth, temperature, and salinity" |
| `measured thermohaline` | "this measured profile resolves the thermohaline structure" if `measured` and `thermohaline` ever land adjacent after edits | substring match across an edit | keep the word `thermohaline` out of the provenance entirely, say "halocline depth and density gradient" |
| `salt fingering observed` | "salt fingering is not observed in the open basin" | `salt fingering observed` appears verbatim | "salt fingering is a stylized interpretation, not a depiction of this cast" |
| `salt fingering observed` | "no salt fingering staircases were observed here" | verbatim substring | "the open Salish basin does not routinely show classic staircases" with the words `fingering` and `observed` kept apart |
| `biosonar perception` | "this is not measured biosonar perception" | verbatim substring | "this is not a depiction of how an orca senses its surroundings" (the wording the shipped `INTERPRETIVE_OCEAN_DETAIL` already uses) |

The rule for authors is simple. Do not place the two words of any forbidden phrase next to each other in any shipped string, even to deny the claim. Express the negation with different words.

### P0-2 The honesty stamp `measured` flag must stay `false` after origin becomes `measured-ctd`

The locked decision is that grounding the PROFILE in a measured cast does NOT make the visualization measured. The userData stamp encodes that distinction in two fields that mean different things.

```33:41:web/lib/scene/ocean/doubleDiffusion.ts
export interface OceanProcessHonestyLabel {
  kind: "interpretive";
  measured: false;
  modeledNotMeasured: false;
  label: string;
  dataSources: string[];
  speculativeClaim: string;
}
```

The `measured` field is typed as the literal `false`, and it describes the VISUALIZATION, not the profile. When the profile origin flips from `"analytic"` to `"measured-ctd"`, the only field that should change is `dataSources`, which already pulls from `profile.provenance` at line 216. The author must not "upgrade" `measured` to `true` to reflect the measured cast. The fact that the cast is measured lives in the provenance string inside `dataSources`, never in the `measured` boolean. I recommend the type stays the literal `false` exactly as written so a flip is a TypeScript error, not a review catch.

## P1 ledger

### P1-1 The exact honesty boundary the label must keep

The label must split what is measured from what is interpretive at the level of the profile inputs versus the motion. The boundary the label and provenance must hold is this. The CTD cast measures three things, depth, temperature, and salinity, at a cited station, and that is all that is measured. The halocline placement and band sharpness are DERIVED from those measured numbers through the density proxy in `stratificationToTexture`. The descending and rising finger motion, the opposed scroll, the colors, and the lava-lamp readout are interpretive and are not measured, not modeled microstructure, and not orca perception.

Concretely, a safe measured provenance string reads like the analytic one but swaps the origin claim and keeps every forbidden two-word pair apart:

```text
measured CTD cast (depth, temperature, salinity) near <station>, NANOOS CruiseSalish, NCEI Accession 0307188, CC0. Halocline depth and density gradient derived from the cast. The mixing motion is a stylized interpretation, not measured microstructure.
```

That string contains no forbidden substring, names the measured variables, attributes the CC0 source, and keeps the motion interpretive. The existing `INTERPRETIVE_OCEAN_DETAIL` already states the boundary well and should be reused unchanged where possible, since editing it risks re-tripping the load-time guard for zero benefit.

### P1-2 Water-regression vectors and the layer-off equivalence test

The lock is that layer-off frames are pixel-equivalent to pre-OCN WFX, and OCN mutates none of WFX water, `scene.environment`, `scene.fog`, or `scene.background`. The depth-aware clip is where this can break. Concrete vectors:

| Vector | How it regresses water | Off-state safety |
|---|---|---|
| (a) Reading `Water2Handle.depthTarget` | If OCN calls `renderer.setRenderTarget(depthTarget)`, `.clear()`, or `.setSize()` on it, or renders into it, it corrupts the seabed color/depth the water shader samples as `uSceneColor` / `uDepthTexture` | Read `depthTarget.texture` and `depthTarget.depthTexture` as a sampler only. Never bind, clear, resize, or render into it. |
| (b) Second depth pre-pass or second render | A new `renderer.render(scene, camera)` or a new prepass is a third full pass, breaks the "one pre-pass only" invariant, and changes timing and possibly output | No new render call. The layer draws inside the existing scene render as additive geometry. |
| (c) renderOrder / blending leak when off | The group is `visible=false`, so three.js skips the subtree in `projectObject` and nothing is submitted | Verified safe as written. Keep `group.visible = false` the single gate. Do not add the meshes to a render list that ignores `visible`. |
| (d) Consuming `WfxEnvHandle` triggers a second PMREM bake | `WIRING-slice-note.md` shows `SliceRig` already calls `makeRealWfxEnv` a second time. A third bake for plume tints overlaps ENV and adds GPU cost | Consume the existing published env handle read-only for color harmony. Do not call `makeRealWfxEnv` from OCN. If no handle is published, that is a coordination return to O0, not a bake by OCN. |

A subtle on-state note that is not an off-state regression but matters for plausibility. `renderDepthPrepass` renders the entire scene with the water mesh hidden. When the layer is ON and added to the scene, its additive meshes are also drawn into `depthTarget` during the prepass, so their color leaks into the seabed color the water samples. It will not corrupt depth because `depthWrite:false`, but it can tint the water. When the layer is OFF this cannot happen because `group.visible=false` excludes it from both renders, so the off-state equivalence is preserved. The builder should exclude the layer from the prepass for on-state correctness, by hiding it the way the water mesh is hidden, or by a camera layers mask.

Second subtle note on the clip itself. Clipping the plume against the water SURFACE is a world-Y test against the surface level, not a depth-buffer read. The existing `depthTarget` holds the opaque scene with the water mesh hidden, so the surface is NOT in that buffer. The `depthTarget` is for seabed occlusion, not surface clipping. Conflating the two will send the author hunting a surface depth that the existing seam does not contain. Surface clip is a cheap plane discard against the surface Y. Seabed occlusion is the depth sample.

Layer-off equivalence test:

```text
1. Build pre-OCN WFX at the OCN base commit. Capture a GPU frame at a fixed
   camera pose, fixed clock time, fixed seed, fixed canvas size and dpr.
   Cover three states: open water, shoreline, submerged.
2. Build OCN with the layer present but setEnabled(false). Capture the same
   three frames at the identical pose, time, seed, size, dpr.
3. Read-examine each pair. Per-pixel diff must be zero, or within lossless
   encoder noise if the capture is not bit-exact.
4. Any nonzero structured diff fails the gate and points at one of (a)-(d).
```

This must be Read-examined on the actual frames, never asserted from code inspection.

### P1-3 Perf budget and the binding tier

| Item | Budget |
|---|---|
| Layer off | Adds 0 cost. `group.visible=false` skips render traversal. The only residual is the per-frame `update()` uniform write. |
| Layer on, baseline plume | BSW-R09 estimate ~0.3 to 0.8 ms at 1080p when submerged. |
| Layer on, depth-aware sampling | Per-fragment `depthTarget` sampling adds cost on top of the BSW-R09 estimate. Must be measured, not estimated, on the GPU host. |
| Desktop budget | `FRAME_BUDGETS.desktop` mean 16.67 ms. |
| Laptop budget | `FRAME_BUDGETS.laptop` mean 33.3 ms. This 30 fps client tier is the BINDING number. Cross-ref the PRF lane. |

The `update()` call writes `uTime` every frame even when the layer is off, since the host useFrame is unconditional. The cost is a single uniform assignment and is effectively zero, but I flag that the host should gate `update()` on `enabled` so off truly means no work. The frame-time A/B in `runFrameTimeAB` runs conditions strictly serially, which is correct, since concurrent GL contexts corrupt frame timing. Off the GPU host the numbers type-check but are not authoritative.

## P2 ledger

### P2-1 The guard list is union-only and should never weaken

`FORBIDDEN_OCEAN_CLAIMS` is the union of the original stub guard and the BSW-R09 forbidden copy. The measured upgrade must not remove any entry to make a provenance string pass. The correct move is always to reword the provenance, never to soften the guard.

### P2-2 `dataSources` is the single place the measured fact lives

After the upgrade, `dataSources: [profile.provenance]` carries the CC0 attribution and the NCEI accession. The HUD attribution should render from this field. No second copy of the provenance should be introduced, to avoid drift between the stamp and the chip.

## The module-load guard, exact rule and author checklist

Rule. `assertNoForbiddenClaim(...texts)` lowercases each text and throws if `lower.includes(phrase)` is true for any phrase in `FORBIDDEN_OCEAN_CLAIMS`. The match is case-insensitive, has no word boundaries, ignores negation, and ignores punctuation between the words only when the words are adjacent as a substring. It runs at import on `INTERPRETIVE_OCEAN_LABEL` and `INTERPRETIVE_OCEAN_DETAIL`, and at construction in `createDoubleDiffusionLayer` on `INTERPRETIVE_OCEAN_LABEL`, `INTERPRETIVE_OCEAN_DETAIL`, and `profile.provenance`.

```49:50:web/lib/scene/ocean/interpretiveOceanLayer.ts
// Assert at module load that the shipped labels carry no forbidden claim.
assertNoForbiddenClaim(INTERPRETIVE_OCEAN_LABEL, INTERPRETIVE_OCEAN_DETAIL);
```

```162:164:web/lib/scene/ocean/doubleDiffusion.ts
  const profile = opts.profile ?? analyticHaloclineProfile();
  // Guard the provenance string the same way the labels are guarded.
  assertNoForbiddenClaim(INTERPRETIVE_OCEAN_LABEL, INTERPRETIVE_OCEAN_DETAIL, profile.provenance);
```

Checklist for the bake and label authors:

```text
[ ] The measured provenance contains none of these adjacent pairs, even negated:
    "measured thermohaline", "biosonar perception", "biosonar reveals",
    "what the whale sees", "salt fingering observed".
[ ] Lowercase the final provenance and run includes() for each phrase locally
    before shipping the bake.
[ ] Disclaim measurement with different words, e.g. "depth, temperature,
    salinity" instead of "thermohaline", and "stylized interpretation"
    instead of "salt fingering observed".
[ ] Keep INTERPRETIVE_OCEAN_DETAIL unchanged unless required, since any edit
    re-enters the load-time guard.
[ ] Honesty stamp measured stays the literal false. dataSources carries the
    measured provenance. modeledNotMeasured stays false.
[ ] Run createDoubleDiffusionLayer with the new profile in a unit test so a
    forbidden provenance throws in CI, not at scene mount.
```

## The pass metric for OCN-Q, stated crisply

The layer passes when all three hold on a Read-examined GPU frame, never asserted from code.

1. Layer-off pixel-equivalence. Frames captured with `setEnabled(false)` match the pre-OCN WFX build per-pixel across open water, shoreline, and submerged, at identical pose, time, seed, size, and dpr.
2. Layer-on physical plausibility. No plume above the water surface, correct depth placement against the surface, and depth-clipped against the seabed, with the honesty chip and provenance visible.
3. Frame-time A/B within budget. Run serially on the GPU host. Layer-off mean is within capture noise of the baseline mean. Layer-on mean is within the binding laptop budget of 33.3 ms, with the desktop 16.67 ms reported alongside.

A run that asserts any of these from inspection instead of a Read-examined frame fails the gate.
