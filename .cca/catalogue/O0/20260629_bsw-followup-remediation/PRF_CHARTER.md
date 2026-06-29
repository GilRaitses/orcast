# PRF — client-tier-frametime-verify (waveset charter)

- Lane code: `PRF`  Family: `BSWR`  Owner: dispatched sub-orchestrator (answers to O0)
- Type: verification (measure + harness; light code), GPU/host-run
- Home: `.cca/catalogue/O0/20260629_bsw-followup-remediation/` ; dispatch `dispatch/PRF/`
- `repo_state_verified_against`: `61ba1d69ee36cf605f7ba741bdaa1defa8762834`
- Umbrella: `PROGRAM.md`

## Intent

Produce an honest client-tier frame-time number for the homepage twin with the
BSW features on, against the binding 30fps budget. The landed ACCEPT captures
used the Tesla T4 render host, which the runbook itself flags as a server-class
upper bound, not the client-tier budget the project is held to.

## Grounding (real seams + verified root cause)

- `infra/render_host/RUNBOOK.md` states the perf caveat directly: the T4 gives a
  real-GPU baseline but is a server-class GPU, not a client laptop tier; treat
  its frame-time numbers as an upper-bound sanity check, not the binding
  client-tier budget.
- `infra/render_host/render_route.mjs` was extended this session with an opt-in
  rAF frame-time sampler and a viewport override; `render.sh` drives it via SSM
  to the GPU or CPU/SwiftShader host.
- The BSW ACCEPT verdicts cite frame-time from this T4 path, so the binding
  client-tier number is not yet measured.

Root cause: there is a real-GPU upper-bound measurement, and a software-GL
correctness fallback, but no representative client-tier measurement and no agreed
client-tier capture methodology.

## Locked decisions (do NOT reopen)

1. Honest representativeness is the whole point. A throttled-profile number is
   reported as "emulated client tier (method X)", never as a real device unless a
   real device is used. The verdict states exactly how the tier was emulated.
2. The pass metric is fixed in `PRF-Q` BEFORE the run: a sustained median (and a
   95th-percentile) frame-time at the chosen client tier, with the BSW features
   on, against the 30fps budget (33.3 ms/frame).
3. CDP `Emulation.setCPUThrottlingRate` and GPU-tier emulation are allowed for an
   emulated tier; CDP `Input.*` is not used (focus-sensitive). A real client-tier
   device is an O0/human gate (hardware acquisition).
4. This is a verification lane. It adds harness code only (sampler config,
   throttling, a capture script); it does not change scene behavior. Any scene
   change that the measurement reveals as needed is a return to O0 to charter a
   separate optimization lane.
5. Measurement is serial on an isolated host. Concurrent contexts corrupt
   frame-time numbers (the standing M3 / frame-time A/B rule).

## Wave structure

- `PRF-R` (research + discovery, read-only). Parallel; each owns one `dispatch/PRF/findings/PRF-<TOPIC>.md`:
  - R1 client tier: what hardware tier the 30fps budget is defined against; representative client GPU/CPU classes; the project's stated target device.
  - R2 capture method: CDP CPU throttling + GPU-tier emulation on the render host vs a real client-tier device; the rAF sampler already in `render_route.mjs`; how to get a stable median + p95.
  - R3 scenes-to-measure: the homepage twin with BSW features on (slice mounted, spectrogram, multi-orca pool, ocean layer), and the BSW-on vs BSW-off A/B.
  - R4 adversarial: is an emulated number honest and representative; the ways a throttled profile lies; vsync and headless caveats.
- `PRF-Q` (qualify methodology). GATED. Fixes the client tier, the capture method (emulated-with-method-X or real-device), and the pass metric; flags any real-hardware need to O0. Returns to O0.
- `PRF-B` (implement). Net-new client-tier capture harness (throttling + sampler config + the BSW-on/off A/B driver) under `infra/render_host/**` or `scripts/**`; no scene change.
- `PRF-ADV` (adversarial review). Audits representativeness and the number's honesty; loops back to `PRF-B` until the method is defensible.
- `PRF-ACCEPT` (accept). GATED. Runs the capture serial on the isolated host; writes the median + p95 + method to `gate_captures/`; honest verdict vs the 30fps budget, stating the emulation method.

## Acceptance criteria (hard, checkable)

- A measured client-tier frame-time (median + p95) with BSW features on, captured serial on an isolated host, written to `gate_captures/` with the exact capture method recorded.
- The verdict states whether the tier is emulated (and how) or a real device, and compares against the 33.3 ms/frame (30fps) budget without reassurance bias.
- A BSW-on vs BSW-off A/B at the same tier, so the BSW feature cost is isolated.
- If the budget is missed, the verdict says so plainly and returns a separate-optimization-lane recommendation to O0 (PRF does not change scene behavior).

## Escalation

Per PROGRAM.md. Pause and return to O0 on any real-hardware acquisition, host run
cost, a budget miss that implies a scene change, or commit.
