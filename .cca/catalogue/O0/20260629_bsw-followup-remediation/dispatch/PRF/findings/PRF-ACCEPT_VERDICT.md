# PRF-ACCEPT verdict (client-tier frame-time, 30fps budget)

> PRF sub-orchestrator ACCEPT, run inside the batched BSWR host window by the
> BSWR host-window sub-orchestrator. Host: aimez-gpu-capture (i-0e66ac03c729ebe02),
> real Tesla T4, glRenderer `ANGLE (NVIDIA Corporation, Tesla T4/PCIe/SSE2, OpenGL
> ES 3.2)`, viewport 1280x800@1. Method: O0-adopted vsync-quantised over-budget
> oracle (PRF-ADV1-DECISION Option 1). No commit. Numbers cited, not asserted.

## Verdict: PASS 30fps with margin (emulated CPU-throttled LOWER BOUND on a
server-class T4 GPU). All four arms, including the heaviest BSW-on arm, land in
the one-refresh PASS-with-margin bucket, comfortably inside the 33.3 ms budget.
This is a LOWER BOUND and does NOT certify the real client GPU.

## Smoke (Option-2 ADV-3 host vsync-uncap confirmation)

`scripts/perf/client_tier_frametime.sh --smoke`, captured at
`gate_captures/smoke_20260629_host.json` (verbatim host stdout; the driver's
auto-save was skipped because the harness exits non-zero by design when
`subRefreshProven` is false).

- uncapped trivial-page median 17.1 ms, capped control 16.7 ms.
- `subRefreshProven: false` — on the trivial empty-rAF page the Linux/Xvfb/T4 host
  does NOT make `--disable-gpu-vsync` / `--disable-frame-rate-limit` free-run below
  one refresh; the synthetic compositor still paces ~60 Hz, matching pure headless.
  ADV-3 outcome: no bonus sub-refresh certification from the smoke. Option-1
  vsync-quantised oracle stands as the primary method.

Honest nuance (recorded, not overclaimed): the trivial-page smoke clamps, but the
REAL WebGL scene clearly is not pinned at 60 Hz on this host. In the A/B runs the
counted-window fps for the live scene is ~100-500 fps with per-frame minima of
0.8-3 ms, i.e. the live GL page resolves sub-refresh intervals here even though the
trivial page does not. Per the binding honesty lock I do not convert that into a
certified single frame-time number; I treat the readings as a vsync-quantised
lower-bound oracle and report the measured medians with their bucket.

## The binding BSW-on/off A/B (emulated 4x CPU throttle = the laptop lower bound)

`gate_captures/frametime_ab_emulated_20260629_132946.json`, `ORCAST_CPU_THROTTLE=4`,
3 serial runs/arm, 2 s warm-up dropped, 10 s counted window, real T4 GPU.

| Arm | route | medianOfMediansMs | worstRunP95Ms | bucket | reading |
|---|---|---|---|---|---|
| pair1-off | `/` | 3.0 | 4.0 | ~16.7 ms (one refresh) | PASS 30fps with margin |
| pair1-on | `/?station=OLAB&bsw_demo=3&ocean=1` | 9.4 | 11.5 | ~16.7 ms (one refresh) | PASS 30fps with margin |
| pair2-light | `/?station=OLAB&view=topdown` | 7.9 | 9.6 | ~16.7 ms (one refresh) | PASS 30fps with margin |
| pair2-heavy | `/?station=OLAB&view=topdown&ocean=1&bsw_demo=3` | 9.2 | 11.1 | ~16.7 ms (one refresh) | PASS 30fps with margin |

BSW-on-minus-off delta (emulated 4x): pair 1 on-minus-off = 9.4 - 3.0 = 6.4 ms;
pair 2 heavy-minus-light = 9.2 - 7.9 = 1.3 ms. The heaviest BSW-on arm's
median-of-medians (9.2 ms) and worst-run p95 (11.1 ms) are both below one refresh
(16.67 ms) and far below the 30fps budget (33.3 ms).

## The T4 server-class reference (throttle 1, the upper-bound sanity check)

`gate_captures/frametime_ab_t4_uncapped_20260629_133501.json`, `ORCAST_CPU_THROTTLE=1`.

| Arm | medianOfMediansMs | worstRunP95Ms |
|---|---|---|
| pair1-off | 0.8 | 1.3 |
| pair1-on | 2.1 | 3.2 |
| pair2-light | 2.1 | 3.4 |
| pair2-heavy | 2.2 | 3.2 |

The two-number report for the heaviest BSW-on arm: emulated-4x lower bound = 9.2 ms
median / 11.1 ms worst-run p95; unthrottled T4 reference = 2.2 ms / 3.2 ms.

## Honest reading against the quantised buckets (binding wording)

- Every arm is in the `~16.7 ms (one refresh)` bucket, read as **"PASS 30fps with
  margin (true cost < one refresh; vsync-quantised, sub-refresh headroom
  unresolved)"**. No arm reaches the ~33.3 ms at-budget cluster, and none reaches
  the >= 50 ms FAIL bucket.
- The medians are NOT reported as "the frame-time is X ms". They are an emulated,
  CPU-throttled LOWER BOUND on a server-class (T4) GPU. A pass here does NOT certify
  the real client GPU, because the GPU work is not throttled and the T4 is faster
  than a client laptop iGPU. A genuinely representative client-GPU number still
  requires a real-device measurement (the standing human/hardware gate).
- The reading is vsync-quantised. On the trivial-page basis (smoke) the cap is not
  proven broken, so the oracle is dispositive only in the over-budget direction. It
  is dispositive here in the safe direction: a lower bound that lands well inside
  one refresh.

## Carried confounds (binding to cite, PRF-R3 / ADV)

1. **The OCN ocean layer did not actually render in the `&ocean=1` arms.** pair1-on
   and pair2-heavy (errorCount 18 vs the 12 baseline) carry the OCN double-diffusion
   fragment-shader compile error (`'interface' : Illegal use of reserved word`, the
   same defect OCN-ACCEPT returned). The ocean layer therefore contributed NO render
   cost to these arms. The BSW orca + spectrogram + slice cost IS included. So the
   on-arm numbers UNDERSTATE a future ocean-on cost; the ocean-on frame-time A/B
   must be re-run after the OCN reserved-word fix lands.
2. Camera differs on pair 1: off = the homepage cinematic POV, on = the station
   dive-in POV. The pair-1 on-vs-off delta conflates the BSW cost with a camera/POV
   change. Pair 2 (topdown light vs topdown heavy) holds the POV fixed and is the
   cleaner BSW delta (1.3 ms).
3. `OrcaRig` is always mounted; there is no slice-off toggle, so "off" is not a true
   zero-BSW scene.
4. The recurring four dev-server 500 resource fetches appear on every arm (12 =
   4 x 3 runs) and are not a scene defect.

## Disposition

PRF-ACCEPT PASSES the 30fps budget on the emulated CPU-throttled lower bound, with
the honesty qualifiers above intact. The result is a LOWER BOUND, not a real-device
certification. One caveat to feed back: the ocean-on cost is not yet measured
because the OCN layer shader fails to compile; re-run the on-arms after the OCN fix
for a complete ocean-inclusive number. Gate captures:
`gate_captures/smoke_20260629_host.json`,
`gate_captures/frametime_ab_emulated_20260629_132946.json`,
`gate_captures/frametime_ab_t4_uncapped_20260629_133501.json`. No commit.

---

# WINDOW-2 RE-RUN (ocean shader FIXED) — supersedes confound #1; ocean-on cost now real

> Re-run in the SECOND batched BSWR host window after the OCN shader fix landed
> (`doubleDiffusion.ts`: GLSL-reserved `interface` -> `bandSharp`). This is the
> ocean-on A/B the window-1 verdict called for. Same host (T4), same method, same
> honesty lock. No commit.

## Smoke re-confirmation

`gate_captures/smoke_20260629_window2_host.json`: uncapped trivial-page median
17.2 ms vs capped control 16.7 ms, `subRefreshProven: false` — unchanged. The trivial
page still does not break the cap; the Option-1 vsync-quantised oracle remains the
primary method. (Captured directly over SSM because the driver's `set -e` aborts on
the by-design non-zero exit before printing the JSON.)

## The CONFOUND #1 IS RESOLVED — the ocean layer now renders

Every arm now reports `errorCount: 12` (= 4 dev-server 500s x 3 runs), the SAME
baseline as the off arms. The two `'interface' : Illegal use of reserved word`
shader-compile errors that inflated the window-1 on-arms to errorCount 18 are GONE.
The `&ocean=1` arms now actually compile and run the double-diffusion fragment, so
their cost is real for the first time.

## Binding BSW-on/off A/B (emulated 4x CPU throttle = laptop lower bound), ocean LIVE

`gate_captures/frametime_ab_emulated_20260629_142336.json`, `ORCAST_CPU_THROTTLE=4`,
3 runs/arm, 2 s warm-up dropped, 10 s counted window, real T4.

| Arm | route | medianOfMediansMs | worstRunP95Ms | bucket | reading |
|---|---|---|---|---|---|
| pair1-off | `/` | 4.0 | 19.1 | ~16.7 ms | PASS 30fps with margin |
| pair1-on | `/?station=OLAB&bsw_demo=3&ocean=1` (dive-in) | **22.2** | **48.0** | under 33.3 ms budget | PASS at-budget; p95 spills toward FAIL (intermittent over-refresh) |
| pair2-light | `/?station=OLAB&view=topdown` | 9.7 | 13.0 | ~16.7 ms | PASS 30fps with margin |
| pair2-heavy | `/?station=OLAB&view=topdown&ocean=1&bsw_demo=3` | 11.3 | 13.9 | ~16.7 ms | PASS 30fps with margin |

## T4 server-class reference (throttle 1)

`gate_captures/frametime_ab_t4_uncapped_20260629_142848.json`, `ORCAST_CPU_THROTTLE=1`.

| Arm | medianOfMediansMs | worstRunP95Ms |
|---|---|---|
| pair1-off | 0.8 | 1.3 |
| pair1-on | 2.2 | 3.5 |
| pair2-light | 2.3 | 3.4 |
| pair2-heavy | 2.5 | 3.9 |

Two-number report, heaviest dive-in ocean-on arm (pair1-on): emulated-4x lower bound
= **22.2 ms median / 48.0 ms worst-run p95**; unthrottled T4 reference = **2.2 ms /
3.5 ms**. The GPU free-runs sub-refresh on every arm (<=2.5 ms median at throttle 1),
so the 22.2 ms emulated cost is CPU-bound under the 4x throttle, not GPU-bound.

## Honest reading (binding wording), window 2

- The heaviest arm is now the DIVE-IN ocean-on POV (pair1-on), not the topdown. Its
  emulated lower-bound median is **22.2 ms** — under the 33.3 ms laptop budget, but
  ABOVE one refresh (16.7 ms), i.e. the "at-budget" zone, NOT the comfortable
  with-margin bucket the topdown arms keep. Its worst-run p95 is **48.0 ms**, just
  under the >= 50 ms FAIL bucket: intermittent over-refresh frames are present under
  4x CPU throttle. This is reported as "PASS the 33.3 ms 30fps budget on the median
  (emulated lower bound), with intermittent over-refresh p95" — NOT "the frame-time
  is 22.2 ms".
- The topdown ocean-on arm (pair2-heavy, 11.3 ms / 13.9 ms) and both light/off arms
  remain comfortably PASS-with-margin.
- Ocean-layer cost is now included. The dive-in on-arm rose from window-1's
  shader-broken 9.4 ms to a real 22.2 ms; most of that is the BSW reenactment + slice
  + the now-rendering ocean layer combined on the heavy dive-in POV under 4x throttle.
- Unchanged honesty: emulated = CPU-throttled LOWER BOUND on a server-class T4 GPU; a
  pass does NOT certify the real client GPU. The intermittent 48 ms p95 on the dive-in
  arm is the one number to watch on a real low-end laptop.

## Window-2 disposition

PRF-ACCEPT PASSES the 33.3 ms 30fps budget on the median for ALL arms with the ocean
layer now actually rendering (max median 22.2 ms, heaviest dive-in ocean-on). The
honest new caution, surfaced only because the shader fix made the measurement valid:
the dive-in ocean-on arm sits in the at-budget zone (22.2 ms median) with intermittent
p95 to ~48 ms (approaching the 50 ms FAIL bucket) under 4x emulated throttle — the
topdown arms keep full margin. Confound #1 from window 1 is resolved. Result remains a
LOWER BOUND, not a real-device certification. No commit.
