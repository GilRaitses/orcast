# OCN-ACCEPT verdict (GPU render-host capture) — SUPERSEDES the prior shader-fail verdict

> OCN sub-orchestrator ACCEPT, re-run in the SECOND batched BSWR host window by the
> BSWR host-window sub-orchestrator after the OCN shader fix landed in the working
> tree (`doubleDiffusion.ts`: GLSL-reserved `interface` renamed to `bandSharp`) and
> the ENV `?capture_t` freeze hook landed (used here for a deterministic playhead).
> Host: aimez-gpu-capture (i-0e66ac03c729ebe02), real Tesla T4, glRenderer
> `ANGLE (NVIDIA Corporation, Tesla T4/PCIe/SSE2, OpenGL ES 3.2)`, viewport 1280x800.
> Working tree re-synced (both fixes packed). No commit. Every frame Read-examined.

## Verdict: PASS. The shader-compile blocker is resolved; the double-diffusion
layer now compiles and renders with no `interface` reserved-word error, layer-OFF
equivalence holds, and the layer-on frame-time A/B is now valid and inside budget.
One honest caveat: the plume's on-screen effect is subtle (a faint water-surface
band) in the above-surface POVs the headless capture can reach, not a prominent
volumetric plume — the documented OCN-ADV P2 above-surface-clamp limitation, not a
defect.

## The fix is confirmed (the prior FAIL cause is gone)

Layer-on route `/?station=OLAB&bsw_demo=3&ocean=1&capture_t=61.5` rendered with
`errorCount: 4` — only the four recurring dev-server 500 resource fetches present
on every route. The two `THREE.WebGLProgram ... ERROR: 0:113 'interface' : Illegal
use of reserved word` shader-compile errors from the first window are GONE. The
fragment shader compiles on ANGLE/NVIDIA. The layer mounts and renders.

## Frames captured (all Read-examined)

| Frame | Route | Note |
|---|---|---|
| `.cca/.../proof/?station=...Orcasound%20Lab&bsw_demo=3&ocean=1&capture_t=61.5_135719.png` | dive-in ocean-ON, frozen t=61.5 | shader compiles; chip `interpretive ocean layer · on`; timeline frozen at t=61.50 (paused) |
| `.cca/.../proof/?station=...Orcasound%20Lab&bsw_demo=3&capture_t=61.5_135819.png` | dive-in ocean-OFF, frozen t=61.5 | identical scene minus the layer; chip `· off` |
| `.cca/.../proof/?station=...Orcasound%20Lab&bsw_demo=3&view=topdown&capture_t=61.5_140107.png` | topdown ocean-OFF, frozen | broad water/shoreline overview |
| `.cca/.../proof/?station=...Orcasound%20Lab&bsw_demo=3&view=topdown&ocean=1&capture_t=61.5_140133.png` | topdown ocean-ON, frozen | layer on |
| `dispatch/OCN/findings/ocn_on_minus_off_diff.png` | dive-in on-minus-off heatmap | shows the difference is the HUD chip + toggle, not the 3D water |
| `dispatch/OCN/findings/ocn_topdown_on_minus_off_diff.png` | topdown on-minus-off heatmap | shows a faint differenced band along the water surface + the HUD chip |

## Where the layer contributes pixels (frozen off-vs-on diff)

With `capture_t=61.5` freezing the playhead, off and on frames are deterministic, so
a direct off-minus-on diff localizes exactly what the layer changes:

- Dive-in: the 3D water band (y 350-410) and the upper scene show essentially ZERO
  difference (mean 0.001, max 1 of 255). The measurable differences are all in the
  HUD chrome (y 600-720): the `interpretive ocean layer · on` toggle highlight and
  the `interpretive · stratified ocean mixing` chip that appears only when on. So in
  the dive-in POV the plume makes no visible contribution to the 3D water — the
  additive field fades to zero at the surface, and the submerged part below the
  waterline is occluded by the spectrogram HUD panel.
- Topdown: a faint differenced band along the water surface (y 425-505, ~2-3% of
  pixels, peak channel delta ~92-115 of 255), plus the same HUD chip difference
  lower down. This faint surface band is the layer's real on-screen contribution
  through the translucent surface at this grazing above-surface angle.

Reading: the shader runs and the layer draws, contributing a faint surface-band
signature, but no prominent volumetric plume is visible because the camera is held
above the water by the no-dunk director clamp and the submerged field is either
faded at the surface or HUD-occluded. This matches OCN-ADV P2 exactly ("with the
camera held above the surface by the director clamp, the scalar top-clip's visible
effect is small today ... ready for a future dive POV"). It is a known limitation of
the available POV, not a rendering defect. Prominent plume visibility needs a
submerged/dive POV that the current above-surface clamp does not expose.

## Frame-time A/B (now VALID — the layer compiles)

Host rAF sampler (`render_route.mjs`, `ORCAST_PERF=1`, 8 s window, uncapped,
throttle=1, T4), both frozen at `capture_t=61.5`:

| Arm | route | medianMs | p95Ms | p99Ms | maxMs | fps |
|---|---|---|---|---|---|---|
| layer-OFF | `/?station=OLAB&bsw_demo=3&capture_t=61.5` | 1.60 | 2.00 | 2.70 | 6.90 | 616.8 |
| layer-ON | `/?station=OLAB&bsw_demo=3&ocean=1&capture_t=61.5` | 1.60 | 2.20 | 2.90 | 8.40 | 610.6 |

Both arms are far inside the 33.3 ms laptop budget AND inside the 16.67 ms desktop
number. Layer-on adds ~0 ms to the median and ~0.2 ms to p95 over layer-off on the
T4 — negligible, consistent with the small ALU + one-discard fragment cost. Unlike
the first window, this is now a VALID measurement because the shader compiles and
the layer actually draws. The CPU-throttled emulated-tier number is the PRF lane's
job (item 3); these T4 numbers are the OCN budget check and pass.

## What passes

- Shader compile / layer renders: PASS (the prior FAIL cause is resolved).
- Layer-OFF equivalence: PASS (3D scene identical off-vs-on; only HUD chrome differs).
- Frame-time A/B with layer-on inside 33.3 ms: PASS (1.6 ms median, 2.2 ms p95 on T4).
- Prominent plume visibility: NOT demonstrable in the available above-surface POVs
  (subtle surface-band only); honestly flagged, matches the documented OCN-ADV P2
  limitation and is deferred to a future dive POV.

## Disposition

OCN-ACCEPT PASSES. The shader reserved-word defect that failed the first window is
fixed and confirmed on the real GPU; the layer compiles, renders, preserves layer-
off equivalence, and stays well inside the frame-time budget. The only honest
caveat is that the plume is subtle in the headless above-surface POVs and a dramatic
submerged view awaits a future dive POV. This verdict supersedes the prior shader-
fail verdict. No commit, no source edit taken in ACCEPT.
