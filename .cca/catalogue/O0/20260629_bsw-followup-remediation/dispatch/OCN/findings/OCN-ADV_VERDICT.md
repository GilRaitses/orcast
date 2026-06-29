# OCN-ADV verdict (adversarial re-audit of the landed OCN-B + OCN-INT work)

> OCN sub-orchestrator, adversarial pass. Repo base `61ba1d6`. No commit. This
> audits label honesty, the load-time guard, layer-off water regression, and
> perf against the locked decisions. GPU pixel-equivalence and the frame-time A/B
> are the OCN-ACCEPT gate and are not asserted here.

## Verdict

Zero open P0 or P1. The build holds the interpretive lock, the measured fact
lives only where it belongs, the load-time guard is exercised by CI, and the
layer-off path is unchanged by construction. Three items are logged as P2 or
deferred, none blocking.

## Re-audit against the R4 P0 ledger

### P0-1 negated-phrase guard trap. CLOSED.

The shipped provenance keeps the two words of every forbidden phrase apart. It
says "depth, temperature, and salinity" rather than "thermohaline", and "stylized
interpretation" rather than "salt fingering observed". The offline bake runs the
same substring check before writing, and the CI test runs the exact mount-time
call `assertNoForbiddenClaim(INTERPRETIVE_OCEAN_LABEL, INTERPRETIVE_OCEAN_DETAIL, profile.provenance)`
plus a known-bad string that must throw. Both pass.

### P0-2 honesty stamp `measured` stays false. CLOSED.

`doubleDiffusion.ts` was not changed in the honesty stamp. `measured` and
`modeledNotMeasured` remain the literal `false`. The only field that now carries
the measured cast is `dataSources`, populated from `profile.provenance`. The
profile `origin` is `"measured-ctd"`, which describes the cast, while the stamp
describes the visualization and stays interpretive.

## Label honesty

`INTERPRETIVE_OCEAN_LABEL` and `INTERPRETIVE_OCEAN_DETAIL` are byte-unchanged, so
the load-time guard is not re-entered and the on-screen chip wording is exactly
what shipped before. The provenance names the cast a nearby analog, not an
on-site station, which matches the geographic reality that the accession has no
San Juan Channel cast. No claim exceeds the evidence.

## Layer-off water regression

Layer-off equivalence holds by construction, not by assertion. `OceanProcessRig`
mounts only when `oceanOn` is true, and `oceanOn` defaults false, so the default
homepage frame adds nothing to the scene. The shader top-clip and the pre-pass
exclusion callbacks execute only when the layer's meshes render, which only
happens when the layer is mounted and visible. The profile change from analytic
to measured affects only the layer-on appearance. Nothing in the layer-off path
changed.

Regression vectors from R4, re-checked against the code:

| Vector | Status |
|--------|--------|
| Rebind, clear, resize, or render into `depthTarget` | Not done. OCN never touches `Water2Handle`. |
| Second depth pre-pass or second render | Not added. The layer draws inside the existing scene render. |
| renderOrder or blending leak when off | The rig is unmounted when off, so nothing is submitted. |
| A second PMREM bake from consuming `WfxEnvHandle` | `makeRealWfxEnv` is never called by OCN. The surface-Y source is the scalar `surfaceY` prop. |
| On-state seabed tint from the pre-pass | Closed by the colorWrite suppression while rendering to an offscreen target. |

The byte-for-byte layer-off GPU comparison across open water, shoreline, and
submerged remains the OCN-ACCEPT step.

## Perf

Layer-off cost is zero because the rig is unmounted. Layer-on adds a small set of
ALU operations and one discard in the fragment shader, three scalar uniforms, and
two per-object render callbacks that read the current render target. No texture
sample was added by the top-clip and no render pass was added. This sits inside
the BSW-R09 estimate of about 0.3 to 0.8 ms at 1080p when submerged. The binding
number is the 33.3 ms laptop budget. The measured frame-time A/B is the
OCN-ACCEPT step and is not asserted here.

## P2 and deferred, non-blocking

- P2. The per-fragment Water2 seabed depth-texture clip is deferred per O0. With
  the camera held above the surface by the director clamp, the scalar top-clip's
  visible effect is small today, but it is correct and free and is ready for a
  future dive POV.
- P2. The CI test reproduces the guard call rather than instantiating the THREE
  layer, because the node test runner cannot resolve `doubleDiffusion.ts`'s
  extensionless imports. The full construct path is compiled by tsc and the web
  build and is exercised at OCN-ACCEPT. Flagged in OCN-METHODOLOGY.
- P2. The shipped profile resamples 9 real bottle-fire samples to 64. The
  continuous 0.5 dbar NANOOS downcast is a later refinement, recorded in
  PROVENANCE.

## Validation snapshot

- `tsc --noEmit` clean.
- ESLint clean on every edited file.
- `node --test lib/scene/ocean/**/*.test.mts` passes 4 of 4.
- Raw CSV is gitignored, the baked JSON is tracked-eligible.

## Loop status

No open P0 or P1, so no loop back to OCN-B or OCN-INT is required. The next step
is OCN-ACCEPT, which is the GPU render-host gate and is paused for O0.
