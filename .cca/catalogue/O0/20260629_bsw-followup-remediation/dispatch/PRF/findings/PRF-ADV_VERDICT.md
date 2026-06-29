# PRF-ADV — Adversarial review of the client-tier capture method

> Adversarial wave for BSWR-PRF. Audits the representativeness and honesty of the
> PRF-B harness against the locked PRF-Q methodology. No reassurance bias.
> Repo verified against `61ba1d69ee36cf605f7ba741bdaa1defa8762834`.
>
> Artifacts under review:
> - `infra/render_host/frametime_client_tier.mjs` (new harness)
> - `infra/render_host/render_route.mjs` (vsync-uncap flags added to launch)
> - `scripts/perf/client_tier_frametime.sh` (SSM driver, PRF-ACCEPT)
> - Evidence: `gate_captures/vsync_smoke_local.json`,
>   `gate_captures/vsync_flagcombo_probe_local.txt`,
>   `gate_captures/overbudget_probe_local.txt`

## ADV-1 CLOSED (O0-ruled) — build-complete, zero open P0/P1

O0 ruled ADV-1 (`PRF-ADV1-DECISION.md`): **adopt Option 1 — the vsync-quantised
30fps over-budget oracle — as the PRF verdict method.** ADV-1 is therefore CLOSED
as an O0-accepted method, NOT as a fabricated sub-refresh number. The method,
harness verdict wording, and §4 honesty lock were rewritten to the quantised-oracle
framing (`PRF-METHODOLOGY.md` ADV-1 amendment + §2/§3/§4/§6;
`frametime_client_tier.mjs` `classifyBucket` + method/honesty strings).
`subRefreshProven:false` stays recorded honestly. The harness, driver, and the
`render_route.mjs` flag addition stay.

Re-run probes (local, macOS pure-headless, 2026-06-29; no host, no paid surface):
- `gate_captures/vsync_smoke_local.json` — uncapped median 17.4 ms vs 16.7 ms capped
  control; `subRefreshProven:false`. The flags do not free-run rAF in pure headless.
- `gate_captures/overbudget_probe_local.txt` — the oracle catches a miss: 25 ms work
  → p95 35.4 ms (~33 ms bucket); 45 ms work → median 51.7 ms (~50 ms bucket). 2/10 ms
  work clamps at ~17 ms; throttle=4× rows clamp (ADV-2 wall-clock probe artifact).
- `node --check` (harness + render_route) and `bash -n` (driver) all clean.

**Open P0/P1: zero.** The verdict is defensible as a 30fps over-budget oracle.
ADV-2 (CPU-throttle busy-loop probe artifact) and ADV-3 (host Linux/Xvfb/T4 uncap
unconfirmed) are documented caveats, not blockers. PRF-ACCEPT (paid host A/B +
Option-2 `--smoke`) is staged for the batched host window (`PRF-ACCEPT-PLAN.md`),
NOT run.

The original §0-§8 below are the adversarial evidence as written at PRF-ADV; read
them through this closure (the §1 "P0" and §6 "ADV-1 open" are now resolved by the
O0 ruling above; the §6 ledger and §8 state are updated in place).

## 0. Verdict up front

**The harness is built and correct, but the locked PRF-Q decision-2 precondition
is NOT met: the two vsync-uncap flags do not break the 60Hz rAF cap in headless
chromium.** This was verified locally, not asserted. Therefore, per decision 2
("No frame-time number counts until this is verified"), the lane CANNOT proceed to
PRF-ACCEPT on the rAF-sub-refresh premise as written. This is a P0 against the
locked method and returns to O0 with two honest, evidence-backed paths forward.

The adversarial review also establishes a positive result O0 should weigh: the
vsync-paced rAF interval is a valid, honest **quantized over-budget oracle** for
the 30fps (33.3 ms) budget, which is the dispositive direction the charter
requires (catching a miss). It cannot resolve sub-refresh headroom, but the 30fps
pass metric does not need that.

## 1. P0 — vsync uncap by launch flag does not work in headless (verified)

Decision 2 required adding `--disable-gpu-vsync` / `--disable-frame-rate-limit`
and proving the sampler reports sub-16.67 ms. The local smoke
(`gate_captures/vsync_smoke_local.json`) on a trivial empty-rAF page returned:

| run | median | min | fps | verdict |
|---|---|---|---|---|
| uncapped (2 flags) | 17.7 ms | 16.7 ms | 57.1 | not sub-refresh |
| capped control | 16.7 ms | 15.6 ms | 60.0 | clean 60Hz lock |

`subRefreshProven: false`. Adding the flags made the cadence slightly noisier
around 60Hz; it did not free-run. Five flag combinations were probed
(`gate_captures/vsync_flagcombo_probe_local.txt`): bare GPU, GPU + 2 uncap flags,
+ `--disable-features=CalculateNativeWinOcclusion,IntensiveWakeUpThrottling`,
SwiftShader + uncap, + `--disable-threaded-animation/scrolling`. All sat at
16.7-18.2 ms median. None produced a sub-refresh interval.

Root cause: in headless chromium the rAF cadence is driven by a synthetic
compositor `BeginFrame` source that ticks at ~60Hz independent of GPU vsync.
`--disable-gpu-vsync` disables the GPU swap vsync; it does not remove the headless
BeginFrame pacing. So the rAF interval cannot resolve any frame whose true cost is
below one refresh period (16.67 ms). This is the exact failure R4 warned must be
verified at PRF-B and not asserted (`PRF-adversarial.md:110-117`).

**Severity P0** against decision 2 as literally written: there is no
flag-only-uncapped sub-16.67 ms number to be had in pure headless, so the premise
"break the cap, then trust the rAF frame-time" does not hold.

## 2. Positive result — the rAF interval is a valid 30fps over-budget oracle

This is the part O0 should weigh before treating §1 as fatal. The over-budget
probe (`gate_captures/overbudget_probe_local.txt`), a page burning a fixed wall
time per rAF callback, shows the signal DOES move once a frame exceeds the vsync
deadline:

| per-frame work | median rAF | p95 | max | reading |
|---|---|---|---|---|
| 2 ms | 18.4 ms | 18.8 | 18.9 | clamped at refresh |
| 10 ms | 18.5 ms | 18.8 | 18.8 | clamped (still < 16.7 of GPU-present budget) |
| 25 ms | 18.7 ms | 36.8 | 37.6 | spills to the next vsync (33 ms bucket) |
| 45 ms | 51.7 ms | 55.9 | 56.1 | spills two vsyncs (50 ms bucket) |

The interval quantises to refresh multiples (≈16.7 / 33.3 / 50 ms). Against the
**33.3 ms (30fps) budget** this is dispositive in the direction that matters:

- sustained median ≈16.7 ms → true cost < 16.7 ms → **PASS 30fps with margin**.
- cluster at ≈33.3 ms → true cost 16.7-33.3 ms → **at/under the 30fps budget**.
- sustained ≥50 ms → true cost > 33.3 ms → **FAIL 30fps**, and the miss is real.

What it cannot do: distinguish a 5 ms frame from a 16 ms frame (both read 16.7 ms).
That headroom is irrelevant to a 33.3 ms pass/fail. So an honest verdict CAN be
issued from the capped signal, provided the wording states it is a vsync-quantised
reading and never presents a clamped 16.7 ms as "the frame-time" (the fabricated-
headroom P0 from R4 §2a).

## 3. P1 — CPU throttle is not exercised by the busy-loop probe (probe artifact, not a harness defect)

The probe rows `busy=5ms throttle=4x` and `busy=10ms throttle=4x` stayed clamped at
~17.9-18.1 ms instead of spilling to higher buckets. This is a **probe artifact**,
not a harness bug: the probe burns a fixed WALL-CLOCK time (`while(now()<end)`),
and `Emulation.setCPUThrottlingRate` slows computation throughput, not the
wall-clock the loop waits on, so a "5 ms" wall-clock burn stays 5 ms under throttle
(it just does fewer iterations). Real scene work is a fixed AMOUNT of computation,
so a 4x throttle makes it take ~4x longer and WILL push CPU-bound frames into the
higher vsync buckets. The harness wiring itself is correct (page-scoped
`newCDPSession`, throttle applied before navigate). This row must not be read as
"throttle does nothing"; it must be re-verified on the real scene at PRF-ACCEPT.
Severity P1: a documentation/validation caveat, fixed by noting the probe limit.

## 4. P1 — local headless is not the host; the Linux/Xvfb/T4 path is unverified

The local smoke is macOS pure-headless. The render host is Linux with ANGLE/EGL +
`libGLX_nvidia` + **Xvfb** on a real T4 (`RUNBOOK.md:9-12`). On a virtual X display
the BeginFrame source can behave like a headed display, where `--disable-gpu-vsync`
genuinely uncaps. So the §1 P0 is proven for local pure-headless but is UNCONFIRMED
for the host. Resolving it needs a cheap host `--smoke` run
(`scripts/perf/client_tier_frametime.sh --smoke`), which is a small SSM call on the
GPU box. Per the escalation rule (any host run pauses to O0), this is returned to
O0, not self-run. Severity P1: bounded unknown with a cheap, named resolution.

## 5. P0 guards confirmed present in the harness

- SwiftShader is never the tier path: default `ORCAST_GL=gpu`; the driver pins
  `GL=gpu`; SwiftShader stays correctness-only (R4 §2e). PASS.
- Two numbers, never one: the driver captures both the CPU-throttled emulated A/B
  and the throttle=1 T4 reference, each tagged with `glRenderer` + throttle +
  viewport + vsync (decision 3). PASS.
- Honesty string is emitted in the `--ab` output (`emulated ... LOWER BOUND ... a
  pass does NOT certify the real client GPU`). PASS.
- Hardened sampler: ~2 s warm-up window dropped (not one frame), ≥10 s counted
  window, ≥3 serial runs, median-of-medians + worst-run p95. PASS.
- No scene change: the harness, driver, and the render_route flag addition touch
  only harness code; SalishScene and the scene graph are untouched. PASS.

## 6. Open P0/P1 ledger

| ID | Sev | Issue | Resolution | Status |
|---|---|---|---|---|
| ADV-1 | P0 | Flag-only vsync uncap does not produce sub-16.67 ms in headless (decision 2 precondition unmet locally) | O0 ruled (`PRF-ADV1-DECISION.md`): adopt Option 1, the vsync-quantised 30fps over-budget oracle, as the verdict method | **CLOSED** (O0-accepted method; not a fabricated number) |
| ADV-2 | P1 | CPU-throttle effect not shown by the busy-loop probe (probe artifact) | Re-verify on the real scene at PRF-ACCEPT; documented caveat | OPEN as documented caveat (not a blocker) |
| ADV-3 | P1 | Host (Linux/Xvfb/T4) uncap behaviour unconfirmed | Cheap host `--smoke` queued into the batched host window | OPEN as documented caveat (not a blocker) |

**Open P0/P1 blocking build-complete: zero.** ADV-1 is closed by the O0 ruling.
ADV-2/ADV-3 are documented caveats carried into the verdict, not blockers.

## 7. Recommendation to O0 (the decision PRF cannot self-approve)

Decision 2 as written cannot be satisfied in pure headless. Three honest options,
in PRF's recommended order:

1. **Accept the quantised vsync oracle (recommended, no new method, no new gate).**
   Keep the capped rAF interval and report the verdict against 33.3 ms as a
   quantised reading: a sustained ≈16.7 ms median is an honest PASS (true cost is
   under one refresh, well under 33.3 ms); a sustained ≥50 ms is an honest, real
   FAIL. The honesty wording states the signal is vsync-quantised and cannot
   resolve sub-refresh headroom. This is dispositive for the charter's core ask
   (catch a 30fps miss) and needs no further harness work. The CPU throttle still
   does its job: it pushes CPU-bound frames into the over-budget buckets.

2. **Confirm the host uncap first (cheap host run, O0-gated).** Run
   `client_tier_frametime.sh --smoke` on the T4 box. If Xvfb makes the flags
   genuinely uncap there, decision 2 is satisfied as written and we get true
   sub-refresh frame-times. If it also clamps, fall back to option 1. Cost: one
   short SSM smoke; this is a host-run gate.

3. **Add a true frame-cost signal (method change, larger).** Drive frames or read
   GPU frame time via CDP Tracing (`disabled-by-default-devtools.timeline.frame`,
   `DrawFrame` durations) instead of the rAF interval. This yields a real
   sub-refresh per-frame cost but is a methodology change beyond the locked
   rAF-interval approach, so it needs O0 sign-off and more PRF-B work.

PRF recommends option 1 for the verdict, with option 2 as a cheap confirmation if
O0 wants to attempt a true uncapped number, and option 3 only if a sub-refresh
frame-COST number (not a 30fps pass/fail) is required.

## 8. State

- Harness, driver, and flag addition are complete and syntax-clean (re-checked
  2026-06-29: `node --check` harness + render_route, `bash -n` driver all pass).
  No commit.
- The method is defensible AS A 30FPS OVER-BUDGET ORACLE (Option 1, O0-adopted). It
  is NOT a sub-refresh frame-time meter via flags alone (ADV-1, honestly recorded);
  it does not need to be for a 30fps pass/fail.
- Build-complete: ADV-1 CLOSED, zero open blocking P0/P1. ADV-2/ADV-3 are documented
  caveats. The verdict wording carries O0's binding honesty conditions
  (`PRF-METHODOLOGY.md` §4; `frametime_client_tier.mjs` `classifyBucket`).
- PRF-ACCEPT (the full paid host A/B + the Option-2 `--smoke`) remains GATED and is
  NOT run. It is staged one command from running for the batched host window:
  `PRF-ACCEPT-PLAN.md`.
- PAUSED at build-complete, returning to O0 with the verdict-wording diff and the
  staged host commands.
