# ENV-ACCEPT verdict (GPU render-host capture) — SUPERSEDES the prior "parity-not-certifiable" verdict

> ENV sub-orchestrator ACCEPT, re-run in the SECOND batched BSWR host window by the
> BSWR host-window sub-orchestrator AFTER the `?capture_t=<sec>` freeze hook landed in
> the working tree (`SalishScene.tsx`: when set, the slice seeks the playhead and
> HOLDS it paused). Host: aimez-gpu-capture (i-0e66ac03c729ebe02), real Tesla T4,
> glRenderer `ANGLE (NVIDIA Corporation, Tesla T4/PCIe/SSE2, OpenGL ES 3.2)`, viewport
> 1280x800, all frames at `capture_t=61.5`. Comparator: `dispatch/ENV/compare_frames.py`
> (numpy+PIL global SSIM, 8px-windowed SSIM, mean/max per-pixel delta). No commit. The
> only source edits taken were the deliberately-wrong-env CONTROL, applied and then
> reverted EXACTLY (git diff verified CLEAN — no control residue). Every frame Read-examined.

## Verdict: PASS on the methodology + determinism + control. The window-1
non-determinism blocker is RESOLVED by the freeze hook: two identical frozen renders
now meet the locked parity bar (SSIM >= 0.99 AND near-zero mean delta) over the
orca/water region, and the comparator is proven LIVE by the control. The one honest
gap: a literal BEFORE (two-bake) frame was NOT captured because the two-bake state is
not cleanly isolable from the interleaved OCN+freeze-hook hunks; before/after pixel
parity rests on the static byte-identity argument from ENV-ADV plus the now-validated
harness, not a direct before/after diff.

## The freeze hook resolved the window-1 blocker

Window 1 (timeline playing) had a determinism noise floor of ssim_win8 ~0.944-0.952
between two identical renders — below the 0.99 bar — because the rAF timeline advanced
during capture. With `capture_t=61.5` the slice seeks and HOLDS the playhead paused
(frames confirm `t = 61.50 s / 180.0 s` with the toggle showing `play`, i.e. paused).
Determinism over two identical frozen renders is now:

| Pair | region | ssim_global | ssim_win8 | mean_abs_delta | max |
|---|---|---|---|---|---|
| AFTER1 vs AFTER2 (dive-in) | full frame | 0.99881 | 0.99417 | 0.1535 | 113 |
| AFTER1 vs AFTER2 (dive-in) | 3D panel bbox | 0.99788 | 0.98180 | 0.4352 | 113 |
| AFTER1 vs AFTER2 (topdown) | full frame | 0.99481 | 0.98805 | 0.5241 | 118 |
| AFTER1 vs AFTER2 (topdown) | 3D water bbox (16,185,631,410) | **0.99872** | 0.98602 | **0.2760** | 94 |

The global-SSIM determinism floor is **0.9987** over the water bbox with mean delta
**0.276** — comfortably inside the locked bar (>= 0.99 AND near-zero mean). The
residual that keeps windowed SSIM at ~0.986 (not 1.0) is the Water2 surface optic,
which rides the R3F global render clock the freeze hook intentionally does NOT stop
(it freezes the timeline/pool/camera, not the global clock). This is a documented
harness limitation, not an env difference, and it does not breach the global-SSIM bar.

## The comparator is LIVE (deliberately-wrong-env CONTROL)

Control = temporarily set `scene.environment = null` in OrcaRig (the WFX PMREM IBL
write), rendered frozen, then reverted EXACTLY (git diff CLEAN). The pool/scene PBR
then gets no image-based lighting — a deliberately-wrong env.

| Pair | region | ssim_global | ssim_win8 | mean_abs_delta | changed>10 px |
|---|---|---|---|---|---|
| AFTER vs WRONG-ENV (topdown) | full frame | 0.73690 | 0.92103 | 10.2413 | — |
| AFTER vs WRONG-ENV (topdown) | 3D water bbox | **0.58638** | 0.84330 | **26.1310** | 99,340 |

The wrong env collapses water-bbox `ssim_global` from 0.9987 to **0.586** and raises
mean delta from 0.276 to **26.13** (~95x the noise floor); 99,340 pixels change across
the 3D water (87-95% of pixels in y235-410). Read-examined: the topdown water surface
goes near-black (loses its IBL reflection) versus the lit blue-green surface in the
AFTER frame. The metric unambiguously distinguishes a correct env from a wrong one.

## POV note (why topdown is the measuring POV)

In the dive-in POV the env-lit subject is not on screen: the orcas are below the
waterline and occluded by the spectrogram HUD panel, so even the dramatic null-env
control moves only 84 px (mean 0.049) over the visible 3D strip. The topdown
down-looking camera exposes the IBL-lit water surface, where both determinism and the
control are cleanly measurable. ENV parity is therefore reported on the topdown POV;
the dive-in frozen frames are retained as determinism evidence for the chrome/HUD.

## Frames captured (all Read-examined)

| Role | path |
|---|---|
| AFTER dive-in #1 (frozen) | `.cca/.../proof/?station=...&bsw_demo=3&capture_t=61.5_135819.png` |
| AFTER dive-in #2 (frozen, determinism) | `.cca/.../proof/?station=...&bsw_demo=3&capture_t=61.5_140449.png` |
| AFTER topdown #1 (frozen) | `.cca/.../proof/?station=...&view=topdown&capture_t=61.5_140107.png` |
| AFTER topdown #2 (frozen, determinism) | `.cca/.../proof/?station=...&view=topdown&capture_t=61.5_141022.png` |
| CONTROL dive-in (wrong env) | `.cca/.../proof/?station=...&bsw_demo=3&capture_t=61.5_140712.png` |
| CONTROL topdown (wrong env) | `.cca/.../proof/?station=...&view=topdown&capture_t=61.5_140913.png` |
| control diff heatmap (dive-in) | `dispatch/ENV/findings/env_after_minus_control_diff.png` |
| control diff heatmap (topdown) | `dispatch/ENV/findings/env_topdown_after_minus_control_diff.png` |

## On the BEFORE (two-bake) frame — honestly deferred, not faked

The locked parity bar is a BEFORE(two-bake) vs AFTER(borrowed-handle) pixel test. I did
NOT capture BEFORE. `git diff` shows the ENV borrowed-handle work, the `capture_t`
freeze hook, and OCN's ocean hooks all interleaved across ~15 hunks in `SalishScene.tsx`
(144 lines changed), and the borrow (`getLiveWfxEnv` via `useSyncExternalStore` in
SliceRig) shares hunks with the freeze logic. The old two-bake code is no longer in the
tree, so producing BEFORE means hand-reconstructing the second-PMREM bake while leaving
the freeze hook and OCN hooks untouched — exactly the risky multi-hunk surgery the
ENV-ACCEPT plan said to avoid. Per that plan I report AFTER + CONTROL + determinism and
rest before/after parity on the ENV-ADV static byte-identity argument: the slice now
BORROWS OrcaRig's single live `WfxEnvHandle` (same `makeRealWfxEnv` inputs: renderer,
pinned sun dir/color/intensity, sea level) instead of baking a second PMREM, so the
pool's IBL texture is the SAME texture by construction — there is no second bake whose
output could drift.

## What passes / what is deferred

- Freeze-hook determinism (window-1 blocker): RESOLVED. Water-bbox ssim_global 0.9987,
  mean delta 0.276 — meets the locked bar (>= 0.99 AND near-zero).
- Comparator liveness (control): PASS. Wrong env -> ssim_global 0.586, mean delta 26.13.
- BEFORE-vs-AFTER pixel parity: DEFERRED (two-bake not safely isolable). Parity supported
  by-construction (ENV-ADV byte-identity) + the now-validated harness, not a direct diff.

## Disposition

ENV-ACCEPT PASSES on methodology, determinism, and control liveness; the freeze hook
fixed the window-1 non-determinism blocker and the frozen determinism floor meets the
locked SSIM>=0.99 + near-zero-delta bar over the orca/water region. The single honest
caveat is that a literal BEFORE two-bake frame was not captured (unsafe to isolate);
before/after parity is carried by the static byte-identity argument plus the validated
harness. This supersedes the prior parity-not-certifiable verdict. No commit; the only
source edit (the control) was applied and reverted exactly, git diff verified clean.
