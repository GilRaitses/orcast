# PRF-ACCEPT plan (client-tier-frametime-verify)

Staged client-tier frame-time capture for the homepage Salish Sea twin against the
30fps (33.3 ms) budget, using the O0-adopted **vsync-quantised over-budget oracle**
(ADV-1 Option 1). This is one command from running. It is NOT run here. It needs
the batched BSWR host window open (paid host run = human gate, per PROGRAM.md).

`repo_state_verified_against`: 61ba1d69ee36cf605f7ba741bdaa1defa8762834

## Gate (human, batched)

PRF-ACCEPT is a paid host run on the Tesla T4 box (`aimez-gpu-capture`,
`i-0e66ac03c729ebe02`). Run it **inside the batched BSWR host window**, serial with
the OCN/ENV GPU captures — never concurrent (concurrent GL contexts corrupt
frame-time, the standing M3 rule). Do not run standalone, do not run now.

## What runs, in order (two commands, one window)

From the repo root, with AWS creds for the render-host account and the GPU box
running:

### 1. Option-2 host vsync `--smoke` (ADV-3 confirmation, cheap)

```
scripts/perf/client_tier_frametime.sh --smoke
```

- Purpose: resolve ADV-3 — does the Linux/Xvfb/T4 host make `--disable-gpu-vsync`
  / `--disable-frame-rate-limit` genuinely free-run, unlike pure headless?
- Writes `gate_captures/smoke_<ts>.json`.
- Read it: if `subRefreshProven:true` (uncapped median < 16.67 ms on the host), the
  host genuinely uncaps and the A/B below also yields true sub-refresh numbers as a
  **bonus** — but the Option-1 30fps verdict stays primary. If `false` (host also
  clamps, matching local), Option 1 already stands; no fallback work.

### 2. The BSW-on/off A/B (the binding capture)

```
scripts/perf/client_tier_frametime.sh --ab
```

- Brings up `next dev` on `127.0.0.1:3010` on the host, then runs the four locked
  arms SERIAL with CPU throttle 4× (the emulated laptop-iGPU lower bound):
  - `pair1-off`   `/`
  - `pair1-on`    `/?station=48.5583362,-123.1735774,Orcasound%20Lab&bsw_demo=3&ocean=1`
  - `pair2-light` `/?station=48.5583362,-123.1735774,Orcasound%20Lab&view=topdown`
  - `pair2-heavy` `/?station=...&view=topdown&ocean=1&bsw_demo=3`
- Then re-runs the same four arms at throttle 1 (the T4 server-class reference) for
  the mandatory two-number report.
- Writes `gate_captures/frametime_ab_emulated_<ts>.json` and
  `gate_captures/frametime_ab_t4_uncapped_<ts>.json`.

Default knobs (override via env if O0 re-fixes them): `ORCAST_GL=gpu`,
`ORCAST_VSYNC=uncapped`, `ORCAST_CPU_THROTTLE=4`, viewport `1280x800@1`,
warm-up 2000 ms, counted window 10000 ms, 3 serial runs (median-of-medians +
worst-run p95).

## How the verdict is read (O0 ADV-1 honesty conditions, binding)

The harness emits a per-arm `verdict.bucket` + `verdict.reading` via `classifyBucket`.
Read `medianOfMediansMs` (and `worstRunP95Ms`) for `pair1-on` and `pair2-heavy` (the
BSW-on arms) at throttle 4× against the quantised buckets:

- clamped **~16.7 ms median → "PASS 30fps with margin (true cost < one refresh)"**.
  NEVER written as "the frame-time is 16.7 ms" (forbidden fabricated-headroom claim).
- **~33.3 ms cluster → "at/under the 30fps budget"**.
- sustained **≥50 ms → "FAIL 30fps, the miss is real"** — dispositive.

If a BSW-on arm lands in the ≥50 ms bucket, the verdict says so plainly and returns
a **separate-optimization-lane recommendation** to O0 (PRF does not change scene
behavior, `PRF_CHARTER.md:67`). If `worstRunP95Ms` spills to a higher bucket while
the median clamps, report it as intermittent over-refresh frames (the harness flags
this in the `reading`).

The number stays an **emulated CPU-throttled LOWER BOUND on a server-class GPU**: a
clamped pass does NOT certify the real client GPU. The verdict states the method
verbatim and never drops "emulated" or "vsync-quantised".

## Evidence + verdict write-up

Capture the smoke JSON and the two A/B JSONs under `dispatch/PRF/gate_captures/`,
then write `dispatch/PRF/findings/PRF-ACCEPT_VERDICT.md` citing the measured
`medianOfMediansMs` + `worstRunP95Ms` per arm, the quantised bucket each lands in,
the per-arm `verdict.reading`, the BSW-on-minus-off delta, the host `--smoke`
`subRefreshProven` result (ADV-3 outcome), and the carried confounds (R3 §5: camera
differs on pair 1; always-on `OrcaRig`; no slice-off toggle). No commit without an
explicit operator request.
