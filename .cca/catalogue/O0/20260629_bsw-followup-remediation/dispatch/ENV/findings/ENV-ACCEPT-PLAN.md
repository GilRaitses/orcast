# ENV-ACCEPT plan (env-handle-consolidation) — frozen-frame capture + parity sequence

- Lane `ENV` (BSWR). This refreshes the ACCEPT plan after the ENV-B build-loop
  iteration that added the deterministic frozen-frame capture hook.
- Validation this rotation: `tsc --noEmit` exit 0, no lint errors. No host run, no commit.
- The GPU render-host capture itself stays a human gate. This doc is the exact
  next-window sequence O0 hands the host operator.

## Why the prior ACCEPT attempt could not test the bar

The slice timeline opened with `seek(SLICE_DEFAULT_T, { play: true })`, then the
reenactment advanced on real-delta `useFrame`. So the pool pose swept continuously
and two byte-identical renders landed at different playheads, giving roughly 0.95
windowed SSIM from animation phase alone, far below the 0.99 bar, before any real
lighting difference could be measured. The comparator could not distinguish a
parity pass from animation jitter.

## Freeze-hook design choice (and why)

Chosen: option (b), a query hook on the slice. `?capture_t=<seconds>` makes
`SliceRig` seek the timeline to that playhead and HOLD it paused
(`authority.seek(captureT, { play: false })`), and suppresses the top-down orbit so
the camera holds a fixed framing. Inert when the param is absent, production plays
as before.

Rejected: option (a), the render-harness injection in
`infra/render_host/render_route.mjs`. It would need the page to expose a
capture-only global the harness can reach, plus a harness edit. The query hook is
strictly smaller, needs no global, and needs NO harness change at all. It also
matches the existing deterministic-capture convention in `SalishScene.tsx`, where
`?station`, `?view`, `?ocean`, and `?bsw_demo` are already query hooks read in one
place. `render_route.mjs` is therefore left untouched by ENV this rotation (its
existing working-tree change belongs to the PRF lane).

Where it lives. The capture params are parsed once in the outer `SalishScene`
capture effect (the same effect that reads `?station`/`?view`/`?ocean`/`?bsw_demo`),
held as `captureFreezeT` state, and threaded through the scene component to
`SliceRig` exactly like `demoCount`. In `SliceRig`:
- The timeline seed branches: `captureFreezeT != null` -> `seek(captureFreezeT, { play: false })`, else the normal `seek(SLICE_DEFAULT_T, { play: true })`.
- The POV context resolver suppresses the orbit under capture: top-down uses `{ orbit: captureFreezeT == null }`, so a capture holds the overview static while normal use keeps the slow orbit.

## Why the frozen frame is deterministic (static trace)

1. Paused playhead is constant. `seek(t, { play:false })` sets the audio engine's
   committed `startOffset = t` and `_playing=false`, so `authority.currentTimeS`
   returns the constant `t` every frame (`audioEngine.ts:84-91, 128-143`).
2. The pool reads the frozen playhead. `SliceRig`'s `useFrame` calls
   `driver.update(dt, cam)`, and `TimelineDriver` reads `timeline.currentTimeS`
   (constant) and calls `pool.update(dt, t, cam)` (`TimelineDriver.ts:57-66`). With
   `t` constant, each instance samples a constant clip time, so the pose target is
   constant.
3. Per-orca damped state converges. The secondary-dynamics springs, the mouth
   foraging smoother, and the eye gaze are damped integrators driven by constant
   inputs (yaw-rate to zero, constant fluke phase/amp, static camera). With
   constant forcing they converge to a unique fixed point regardless of the dt
   path, so after the host settle window (`waitMs`, default 9000 ms) two runs land
   at the same steady pose.
4. Camera holds static. The hydrophone dive-in is a 2500 ms `flyTo` that completes
   and holds; the top-down fly-in completes and, with the orbit suppressed under
   capture, also holds. Both settle well inside `waitMs`, to a deterministic end
   pose that is a pure function of station geo and altitude.

Net: the pool pose and the camera are deterministic after settle, which collapses
the SSIM noise floor toward 1.0. No harness edit is needed for the one-frame wait,
because the existing `waitMs` settle is thousands of frames after the seek-and-hold.

### Honest residual (flagged)

The hook freezes the pool pose and the camera. It does NOT freeze the global render
clock, so any continuous global-clock animation still advances, most relevant the
Water2 surface optic. Over the pool bounding box the orcas are opaque and dominate
the pixels, so the residual is expected to sit under the 0.99 SSIM and near-zero
mean-delta bar. If the next-window capture shows the water residual breaking the
bar over the bbox, the mitigation order is: first tighten the bbox to the orca
silhouettes, then, only if still needed, add a harness-driven capture-hold that
stops the R3F clock after settle (option a as a follow-up). That global-clock
freeze is intentionally NOT built this rotation, to keep the change minimal and
inert. This residual is stated so the verdict cannot overclaim "pixel-identical".

## Next-window capture sequence (exact)

Same render host, same viewport (`ORCAST_VW=1280 ORCAST_VH=800`), one GL context at
a time per SEQUENCING. Routes are passed via `ORCAST_ROUTE` (base64 transport in
render.sh) because of the `?`, `&`, and comma characters.

Frozen playhead for every frame below: `capture_t=61.5` (the presence-positive
`SLICE_DEFAULT_T`). Station `48.5583362,-123.1735774,Orcasound%20Lab`, `bsw_demo=3`.

A. BEFORE frames. Check out the parent commit that still has the slice's own second
   `makeRealWfxEnv` bake, then add the SAME `capture_t` hook there if it is not
   present, or capture the before frames from a build that has the freeze hook but
   restores the second bake. The before build must be frozen identically, the only
   difference under test is two PMREM bakes versus one shared handle.
   - A1 dive-in: route `/?station=48.5583362,-123.1735774,Orcasound%20Lab&bsw_demo=3&capture_t=61.5`
   - A2 top-down: route `/?station=48.5583362,-123.1735774,Orcasound%20Lab&bsw_demo=3&view=topdown&capture_t=61.5`

B. AFTER frames. The ENV-INT build (slice borrows OrcaRig's handle, second bake
   dropped), frozen identically.
   - B1 dive-in: same route as A1.
   - B2 top-down: same route as A2.

C. CONTROL frame (comparator sanity). A frame with a deliberately wrong env so the
   metric must move. Simplest honest control: capture B1's route on a build where
   the pool env is intentionally broken (for example the borrowed handle forced
   null so the pool skin/eyes get no envMap, or a mismatched PMREM). The control
   must score far below 0.99 against B1; if it does not, the comparator or the bbox
   is wrong and the parity result is meaningless.

## Pass metric (locked at ENV-Q)

Over the pool bounding box only (crop to the spawned orcas at the station, not the
whole frame):
- SSIM >= 0.99 for A1 vs B1 AND A2 vs B2, AND
- near-zero mean per-pixel absolute delta (within encoder and AA noise, order a few
  8-bit levels), with no localized saturated-black or blown-white region that would
  signal a missing or wrong envMap.
- The control C must score well below 0.99 against B1, proving the comparator moves.

Parity is the bar. Frame-time A/B (ORCAST_PERF=1) is reported as supporting
evidence, a small slice-mount improvement is expected from dropping one PMREM bake
plus one sky-dome build and one VRAM render target, but a speedup is not required
and is not the gate. All four frames are Read-examined per the visual-verification
rule, and the verdict cites the measured SSIM and mean-delta numbers, never a claim.

## Reuse by sibling lanes (noted, not owned by ENV)

The same `capture_t` freeze enables two sibling re-captures that previously had the
same animation-jitter problem:
- OCN layer-on plausibility re-capture: add `&ocean=1&capture_t=61.5` for a frozen
  frame with the interpretive double-diffusion layer on, comparable against
  layer-off.
- PRF ocean-on frame-time re-run: `&ocean=1&capture_t=61.5` with `ORCAST_PERF=1`
  gives a deterministic, comparable ocean-on scene state for the frame-time arm. A
  paused timeline still renders every frame, so per-frame cost stays representative
  while the scene state is reproducible. These are flagged for OCN and PRF to use,
  ENV does not run them.

## Gate

ENV-B build-loop iteration complete (freeze hook added, tsc clean, no lint, no
host run, no commit). The lane returns to O0 with the design choice, the diff, and
this plan, and remains paused before the human-gated ENV-ACCEPT GPU capture.
