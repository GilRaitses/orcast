# PRF-R4 — Adversarial: is an emulated client-tier frame-time honest, and how does the rAF sampler lie?

> Read-only research finding (PRF-R wave). No host run, no edits, no commit.
> Repo verified against the charter pin `61ba1d69ee36cf605f7ba741bdaa1defa8762834`
> (`PRF_CHARTER.md:6`). Mandate: attack the methodology, no reassurance bias.

## Question

1. Is an EMULATED client-tier number honest and representative at all, and when
   does it become misleading?
2. The rAF interval sampler in `infra/render_host/render_route.mjs` measures
   `requestAnimationFrame` intervals. Enumerate the ways that lies as a frame-time
   signal (vsync clamping, CPU-only throttle, main-thread vs GPU/compositor,
   warm-up, SwiftShader-not-a-client-GPU).
3. Headless caveats: does headless Chromium composite/vsync like a real tab?
4. The conditions under which the number is DEFENSIBLE, the required honesty
   wording, and the P0/P1 criteria for the eventual verdict.

---

## 0. Bottom line up front

An emulated number CAN be honest, but **only as an explicitly-labelled emulation
with its method stated, and only if the vsync cap is broken so the rAF interval
reflects real per-frame cost.** The sampler as it exists today does neither: it
ships no vsync-disable flag and no CPU throttling, and the two landed A/B verdicts
that used it (BSH, BRE) both returned numbers pinned at exactly the 60 Hz refresh
interval. Those numbers are honest as "under 60fps on a server GPU" and are a
**lie** if read as "the client-tier frame-time vs the 30fps budget."

---

## 1. Can an emulated client-tier number be honest at all?

Yes — conditionally. An emulation is honest when it (a) is reported as an
emulation with the exact method, never as a real device, and (b) measures a signal
that actually varies with per-frame cost at the tier being emulated. The charter
locks (a): "A throttled-profile number is reported as 'emulated client tier
(method X)', never as a real device" (`PRF_CHARTER.md:34-36`). R4's job is (b):
the emulation also has to be *representative*, and that is where it breaks.

It becomes MISLEADING under any of these conditions, each developed below:

- the measured signal is clamped (vsync) so it cannot resolve cost below the cap;
- the throttle only touches one of the two bottlenecks (CPU-only throttle on a
  GPU-bound scene);
- the emulator's hardware profile does not match the named tier (a CPU-throttled
  server GPU is not an iGPU's shared-bandwidth profile; SwiftShader is not any
  client GPU);
- the harness runs in a context (headless, offscreen) whose compositing/vsync
  behaviour differs from the real browser tab the budget is held against.

The binding tier is the **30fps laptop / weak integrated GPU** (per the sibling
R1 finding `PRF-client-tier.md:97-104`, grounding in `WFX-R13_perf_adversarial.md:59-60,128-130`).
An iGPU is GPU- and memory-bandwidth-bound, which is precisely the profile the
failure modes below fail to emulate.

---

## 2. The failure modes of the rAF interval sampler

The sampler is `render_route.mjs:55-92`. It pushes `now - last` deltas from nested
`requestAnimationFrame(tick)` over `perfSampleMs` (default 3000 ms,
`render_route.mjs:22`), drops one sample, and reports mean/median/p95/p99/max/fps.
The launch args are `render_route.mjs:31-35`.

### 2a. vsync clamping — SEVERITY: P0 for the 30fps budget

**The lie it produces:** a scene that renders faster than the refresh interval
reports the refresh interval (~16.67 ms @ 60 Hz), hiding all headroom; a scene
between 16.7 ms and 33.3 ms of real work waits for the next vsync tick and reports
~33.3 ms, manufacturing the appearance of "exactly at the 30fps budget" when the
real cost has up to 16 ms of slack. rAF interval is quantised to multiples of the
refresh period, so it cannot report the continuous per-frame cost the 30fps budget
is judged against.

**This is not theoretical — it already happened.** The two BSW A/B verdicts that
used this exact sampler both returned numbers pinned to the 60 Hz cap:

- BSH ocean ON/OFF: every column is 16.67 mean / 16.7 median / 16.7-16.8 p95 /
  16.8 p99 / 16.8 max / 60 fps for both runs
  (`.../dispatch/BSH/gate_screenshots/VERDICT.md:48-57`). The verdict states the
  caveat itself: "the rAF interval is vsync-capped at 60 Hz, so this confirms the
  layer stays UNDER the 60 fps budget on the T4 but cannot resolve headroom below
  the cap."
- BRE nMax-1 vs nMax-3: identical 16.67 / 16.7 / 16.7 / 16.8 / 16.8 / 60 for both
  (`.../dispatch/BRE/gate_screenshots/VERDICT.md:26-34`), same caveat.

A flat 16.67 across two different feature loads (ocean on vs off, 1 orca vs 3) is
the signature of a clamp, not of measurement: the signal did not move because it
*could not* move below the cap. So the clamp is empirically confirmed for this
harness on the T4 path.

**The harness does NOT disable vsync.** The args are `--use-gl=angle`,
`--use-angle=...`, `--enable-gpu` / `--enable-unsafe-swiftshader`,
`--ignore-gpu-blocklist`, `--no-sandbox`, `--window-size`
(`render_route.mjs:31-35`). There is no `--disable-gpu-vsync` and no
`--disable-frame-rate-limit` anywhere in the harness (confirmed by repo-wide
search; the only hits are in this finding's own context). The sampler's inline
comment claims "on a vsync-capped headless context [the interval] reflects the
per-frame main-thread + GPU cost: if a frame exceeds the refresh budget the rAF
callbacks space out" (`render_route.mjs:49-54`). That claim is **half true and
dangerously incomplete**: callbacks only space out for frames *over* the cap;
every frame *under* the cap is flattened to 16.67, which is exactly the regime the
empirical data sat in. For the 60fps budget a clamped reading is a valid PASS; for
the **30fps budget** a clamped 16.67 reading proves only "real cost is somewhere in
0-16.67 ms," and a clamped 33.3 reading is ambiguous over "real cost 16.7-33.3 ms."
Neither is the frame-time the budget asks for.

**Headless behaviour must be verified at PRF-B, not asserted.** What headless
Chromium does for vsync depends on flags and headless mode (see §3). The empirical
T4 data shows *a* 60 Hz clamp is in effect on that path; whether
`--disable-gpu-vsync` / `--disable-frame-rate-limit` actually uncaps rAF under
this ANGLE/EGL + `headless:true` (`render_route.mjs:37`) configuration **must be
verified at PRF-B by adding the flag and confirming the rAF intervals stop pinning
to 16.67**. Do not assert it works until the output shows sub-16.67 and
above-16.67 intervals.

### 2b. CPU-only throttling (`Emulation.setCPUThrottlingRate`) — SEVERITY: P1, P0 if mislabelled

**The lie it produces:** `setCPUThrottlingRate` throttles the **main-thread CPU
only** — not the GPU, not the raster/compositor threads, not memory bandwidth. A
GPU-bound scene (and the twin is GPU-bound: 2U of full opaque scene renders per
frame, `WFX-R13_perf_adversarial.md:53-66`) has its dominant cost **understated**
by CPU throttling alone, because the throttle never touches the GPU work that
dominates the frame. So a "4x CPU-throttled" emulation of a weak laptop iGPU can
report a comfortable frame-time while the actual iGPU — bottlenecked on fill rate
and shared memory bandwidth, not main-thread JS — would miss budget.

**Not yet implemented.** `setCPUThrottlingRate` appears nowhere in the harness; it
is only named as *allowed* in the charter (`PRF_CHARTER.md:40-42`,
`wave_shape.yml:30`). PRF-B will add it. R4's warning is that adding CPU throttle
**without** a GPU-tier emulation produces a number that is honest about the CPU
tier and silent about the GPU tier — and the GPU tier is the binding one.

**Second-order distortion:** throttling can also *serialise* work that is normally
parallel (main-thread script that overlaps GPU/compositor work on a real device
gets stretched under throttle), which can *over*state cost on a CPU-light frame.
The direction of the error is not fixed, which is itself a reason the number needs
validation against a real device rather than trust.

### 2c. rAF runs on the main thread; GPU/compositor cost may not be captured — SEVERITY: P1

rAF callbacks fire on the **main thread**. When rendering is offloaded
(compositor-driven, GPU process, raster workers), the rAF interval can return
before the GPU has finished the frame, so the interval measures main-thread
pacing, not GPU frame cost. Combined with 2b this compounds: the one knob we have
(CPU throttle) hits the one thread the GPU cost is *not* on. For a GPU-bound twin,
rAF interval is a weak proxy for the thing that actually blows the 30fps budget.
The honest signal for a GPU-bound scene is a **GPU timer / CDP tracing frame
time**, not the rAF interval; whether PRF-B can get that on this host **must be
verified at PRF-B**.

Background-tab throttling is a related risk: a headless page with no foreground
can have rAF throttled to ~1 Hz. The empirical 60 Hz cadence shows that did NOT
happen on the T4 path, but it is a known failure mode to re-check whenever the
launch context changes (new headless mode, no `--window-size`, etc.).

### 2d. Warm-up: only ONE sample dropped — SEVERITY: P1

The sampler drops exactly one delta: `deltas.shift()` (`render_route.mjs:69-70`),
commented "scheduling warm-up." One frame is not enough warm-up exclusion for a
3D twin: first-frame shader compile, texture/tile upload, JIT, and streamed-tile
loads (the CUDEM multi-LoD tileset, `WFX-R13:59-60`) produce transients across the
first many frames, not just the first. Dropping one sample leaves those spikes in
the p95/p99/max tails (and slightly in the mean). With the vsync clamp in effect
this was masked (everything pinned at 16.67); once vsync is disabled at PRF-B the
warm-up tail will reappear and a one-sample drop will inflate p95. Fix at PRF-B:
drop a fixed warm-up window (e.g. first ~30 frames) or sample only after a
quiescence check, and report the window.

Related: the default 3000 ms / ~180-frame window (`render_route.mjs:22`) is
**short** relative to the charter's ask for a *sustained* median + p95
(`PRF_CHARTER.md:38`). A 3 s window can miss periodic GC pauses and tile-stream
hitches. "Sustained" should be a longer window fixed at PRF-Q.

### 2e. SwiftShader is NOT a client GPU tier — SEVERITY: P0 if reported as client tier

`ORCAST_GL=swiftshader` (default, `render_route.mjs:30,34-35`) is software GL on
the CPU host. The code says so itself: "Software GL is fine for CORRECTNESS frames
... it is NOT a client-tier perf measurement" (`render_route.mjs:4-6`); the runbook
calls the CPU/SwiftShader box "Correctness-only fallback" (`RUNBOOK.md:13-14`).
SwiftShader is far slower than and bottlenecked differently from any real client
GPU (CPU-rasterised, no fixed-function texture units, no real fill-rate model), so
a SwiftShader frame-time reported as "client tier" is a **fabrication in both
directions** — wrong magnitude, wrong bottleneck. It is neither the iGPU tier nor
an upper bound; it is a different machine. P0 if it ever leaves the harness as a
client-tier number.

---

## 3. Headless caveats — does headless Chromium composite/vsync like a real tab?

Not necessarily, and the repo cannot fully answer it. The harness launches
`chromium.launch({ headless: true, args })` (`render_route.mjs:37`). Open issues
the verdict must not paper over:

- **Headless mode is unspecified.** Playwright's `headless:true` selects a headless
  Chromium; whether it is old-headless or new-headless (`--headless=new`) is not
  pinned in the harness, and the two differ in how they composite and schedule
  frames. **Must be verified at PRF-B** by recording the actual headless mode and
  the BeginFrame cadence.
- **No real display refresh.** Headless renders offscreen with no physical vsync
  source. Chromium's frame scheduler can still impose a default 60 Hz BeginFrame
  cadence (which is consistent with the empirical 16.67 ms pinning in §2a), so the
  rAF interval reflects a *synthetic* refresh, not real client hardware. A
  synthetic 60 Hz clamp is the worst case for the 30fps question: it both hides
  sub-cap cost and is not even the client's real refresh behaviour.
- **Offscreen path may differ from on-screen swap.** Whether ANGLE/EGL on this host
  vsync-locks the swap the same way a real tab does is unknown from the repo.
  **Must be verified at PRF-B** by toggling `--disable-gpu-vsync` and checking
  whether the rAF distribution un-pins.

The honest reading: the headless T4 path produced a vsync-pinned signal, so until
PRF-B demonstrates an uncapped, GPU-time-true measurement, headless rAF interval is
a 60fps PASS/FAIL oracle, not a 30fps frame-time meter.

---

## 4. Conditions for a DEFENSIBLE number

A produced number is defensible vs the 30fps budget only if ALL of:

1. **Vsync is broken and proven broken.** PRF-B adds `--disable-gpu-vsync`
   (and/or `--disable-frame-rate-limit`) AND shows the rAF interval distribution
   no longer pins to 16.67 ms (i.e. it shows values both below and above the old
   cap). If the distribution still pins, the number is not usable for the 30fps
   budget. (Alternative that is strictly better: a GPU/CDP-traced frame time
   instead of the rAF interval.)
2. **The GPU bottleneck is emulated, not just the CPU.** CPU-only throttling is
   paired with a GPU-tier emulation, OR the verdict states explicitly that only the
   CPU tier was emulated and the GPU cost is the *measured host GPU* (a server T4),
   making the result an upper bound, not the iGPU tier.
3. **Not SwiftShader.** The client-tier number comes from a real GPU path
   (`ORCAST_GL=gpu`), never the software-GL fallback.
4. **Warm-up excluded and the window is sustained.** A fixed warm-up window is
   dropped (not one sample) and the sample window is long enough to count as
   sustained, both fixed at PRF-Q.
5. **Serial capture.** One GL context at a time (`PRF_CHARTER.md:47-49`), already
   the standing rule.
6. **BSW-on/off A/B at the same tier**, so the BSW cost is isolated
   (`PRF_CHARTER.md:66`).

If any of 1-3 fails, the number is not a client-tier frame-time and must not be
reported as one.

---

## 5. Required honesty wording for the verdict

The verdict must carry, verbatim in substance:

> Emulated client tier (method X): real-GPU host = Tesla T4 server-class GPU; CPU
> throttled to {N}x via CDP `Emulation.setCPUThrottlingRate`; GPU tier emulated by
> {method / "not emulated — host GPU is a server-class T4, so the GPU cost is an
> upper bound, not a laptop iGPU"}; vsync {disabled via `--disable-gpu-vsync` and
> confirmed un-pinned / still capped at 60 Hz}; rAF-interval sampler, {N} frames,
> first {K} dropped as warm-up. This is NOT a real client device. Median {x} ms,
> p95 {y} ms vs the 33.3 ms (30fps) budget.

It must NOT say "30fps laptop measured," must NOT drop the "emulated" word, must
NOT present a vsync-clamped reading as the frame-time, and must NOT smooth a budget
miss (a miss returns a separate-optimization-lane recommendation to O0 per
`PRF_CHARTER.md:67`).

---

## 6. P0 vs P1 criteria for the eventual verdict

**P0 — the number is a lie (block the verdict):**

- An emulated number reported as a real device, or with the word "emulated"
  dropped (`PRF_CHARTER.md:34-36`).
- A SwiftShader/software-GL number reported as a client-tier frame-time (§2e).
- A vsync-clamped rAF reading reported as the frame-time vs the 30fps budget
  without disclosing the clamp — i.e. fabricated headroom (§2a; this is what would
  have happened if the BSH/BRE 16.67 numbers had been presented as "we hit the
  budget with margin" instead of "under 60fps, cannot resolve sub-cap").
- A CPU-only-throttled number presented as a full client-GPU-tier emulation for the
  GPU-bound twin (§2b), with no statement that the GPU cost is the host T4.

**P1 — the number needs a caveat (verdict passes with the caveat stated):**

- Vsync broken and number un-pinned, but emulation fidelity (CPU-only throttle vs a
  real iGPU's shared-memory-bandwidth profile) not validated against a real device
  (§2b) — report as emulated with the fidelity gap named.
- Short sample window or one-sample warm-up drop inflating the tails (§2d) — report
  the window and caveat the p95.
- Headless mode / offscreen compositing not matched to a real tab (§3) — state it
  and recommend a real-device confirmation as the O0/human gate
  (`PRF_CHARTER.md:42`).

The dividing line: **P0 = the reader is misled about WHAT was measured** (real vs
emulated, real GPU vs software, clamped vs true). **P1 = the reader knows what was
measured but its representativeness of the real client tier has a stated, bounded
gap.**

---

## 7. TL;DR

- **Can an emulated number be honest?** Yes — but only labelled "emulated client
  tier (method X)" and only if the vsync cap is broken so the signal reflects real
  per-frame cost. As-is, the harness does neither.
- **Top failure modes.**
  1. **Vsync clamping (P0 for 30fps).** rAF interval quantises to the refresh
     period; the harness ships no `--disable-gpu-vsync` (`render_route.mjs:31-35`)
     and the two landed A/B verdicts both pinned at exactly 16.67 ms
     (`BSH...VERDICT.md:48-57`, `BRE...VERDICT.md:26-34`) — empirical proof the
     signal could not move below 60 Hz. Good for "under 60fps," useless for the
     33.3 ms budget.
  2. **CPU-only throttle (P1, P0 if mislabelled).** `setCPUThrottlingRate` (not yet
     in the harness) throttles only the main thread; the twin is GPU-bound (2U,
     `WFX-R13:53-66`), so a CPU-throttled server GPU understates the iGPU cost.
  3. **Headless compositing/vsync (P1, with an unverified P0 risk).** Offscreen, no
     real display refresh, headless mode unpinned (`render_route.mjs:37`); whether
     vsync can be uncapped here **must be verified at PRF-B**.
  Plus: SwiftShader is not a client GPU (P0 if reported as one,
  `render_route.mjs:4-6`); the one-sample warm-up drop (`render_route.mjs:69-70`)
  and 3 s window are too thin for a sustained p95.
- **Honesty wording the verdict must carry:** "emulated client tier (method X)" —
  naming the CPU throttle factor, whether the GPU tier was emulated or is the host
  T4 upper bound, whether vsync was disabled and confirmed un-pinned, and the
  warm-up/window — reported as median + p95 vs 33.3 ms, never as a real device,
  never with the clamp hidden, never smoothing a miss.
