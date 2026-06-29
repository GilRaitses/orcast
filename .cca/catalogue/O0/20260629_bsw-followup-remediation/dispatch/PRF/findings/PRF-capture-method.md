# PRF-R2 — Capture method for an honest client-tier frame-time

> Read-only research finding (PRF-R wave). No host run, no harness edit, no commit.
> Repo verified against the PRF charter pin `61ba1d69ee36cf605f7ba741bdaa1defa8762834`.
> Authored by PRF-R2; answers to the PRF sub-orchestrator.
> Convention: **FACT** = read directly from code/docs (file:line). **REC** = my recommendation.
> No reassurance bias: each method below states plainly what it *cannot* honestly claim.

---

## 1. The existing rAF frame-time sampler (FACT, `infra/render_host/render_route.mjs`)

### What drives it
- **FACT** Opt-in via `ORCAST_PERF=1`. The flag is read at `render_route.mjs:21` (`const measurePerf = process.env.ORCAST_PERF === '1';`) and the sample window at `render_route.mjs:22` (`perfSampleMs = parseInt(process.env.ORCAST_PERF_MS || '3000', 10)` — **default 3000 ms**).
- **FACT** `render.sh` wires it: `PERF="${ORCAST_PERF:-0}"` (`render.sh:46`, **off by default**) and passes it into the host process as `ORCAST_PERF=$PERF` inside the SSM `node ~/orcast/render_route.mjs` invocation (`render.sh:83`). So the path is: operator sets `ORCAST_PERF=1` → `render.sh` → `aws ssm send-command` → host shell → `node render_route.mjs`.
- **FACT** The GL backend is chosen separately by `ORCAST_GL` (`render_route.mjs:30`), driven from `render.sh` by `ORCAST_RENDER_TARGET` (`render.sh:18-27`): target `gpu` → instance `i-0e66ac03c729ebe02` (Tesla T4) with `GLMODE=gpu`; target `cpu` → `i-04a649f91274e9fce` with `GLMODE=swiftshader`. Default target is `gpu` (`render.sh:20`).

### What it actually measures
- **FACT** The sampler runs **after** the screenshot, serially (`render_route.mjs:47` screenshot, then `:56` perf block), consistent with the "one GL context at a time" rule the comment cites (`render_route.mjs:52-54`).
- **FACT** It is a `requestAnimationFrame` interval sampler injected via `page.evaluate` (`render_route.mjs:58-88`). Each tick pushes `now - last` into `deltas[]` (`:64`), continues until `now - start >= sampleMs` (`:66`).
- **FACT** Warm-up handling: it drops **exactly one** interval — `deltas.shift()` (`render_route.mjs:70`) — described in-code as "drop the first interval (scheduling warm-up)" (`:69`).
- **FACT** Statistics (`render_route.mjs:72-83`): sorts the deltas; quantile helper `q(p) = sorted[min(len-1, floor(p*len))]` (`:73`); reports `meanMs`, `medianMs = q(0.5)`, `p95Ms = q(0.95)`, `p99Ms = q(0.99)`, `maxMs`, and `fps = 1000/mean`. All rounded to 2 dp.
- **FACT** It also reports the **real WebGL renderer** string via `UNMASKED_RENDERER_WEBGL` (`render_route.mjs:94-104`), so the JSON output (`:106-111`) records `glMode`, `glRenderer`, and `frameTime` together — i.e. every frame-time number is tagged with the GL backend that produced it. The RUNBOOK calls this out as the way to tell T4 from SwiftShader at a glance (`RUNBOOK.md:23-24`).

### Strengths (for a client-tier number)
- Measures the **end-to-end per-frame cadence of the live page** (main-thread JS + the r3f render loop + GPU work), not a synthetic micro-benchmark. The 2U depth-prepass + main-render baseline that `WFX-R13_perf_adversarial.md` (§1, lines 30-66) says dominates the frame is exactly what shows up in the rAF interval.
- Reports the **distribution** (median + p95 + p99 + max), which is the right shape for the pass metric the charter fixes (sustained median **and** p95 vs 33.3 ms/frame — `PRF_CHARTER.md:37-39`). Median resists one-off GC stalls; p95/p99/max expose them.
- The renderer string is captured alongside the number, which is the single most important honesty guard: a frame-time with `glRenderer = SwiftShader` is self-evidently not a GPU-tier number.

### Limits (what it cannot honestly claim as-is)
1. **rAF interval ≠ pure render cost; it conflates the schedule with the work.** The in-code comment (`render_route.mjs:49-54`) asserts the context is "vsync-capped" so a slow frame spaces the callbacks out. That is only true *if* the headless context actually vsyncs. **Headless Chromium frequently does NOT present to a real display and does NOT vsync-cap**, so rAF can either (a) free-run as fast as the render allows (interval ≈ raw frame cost, *uncapped* — good for cost, but then "we hit 30fps" cannot be read off a capped 33.3/16.7 plateau) or (b) be driven by Chromium's internal `BeginFrame` scheduler at a fixed cadence regardless of GPU load (interval pinned near a constant — *hides* slow frames). Which of the two you get is host/flag-dependent and is **not pinned** in the current harness. This is the central caveat to cross-check with R4 (vsync/headless honesty).
2. **Sample window is short.** 3000 ms default (`render_route.mjs:22`) at ~60 fps is ~180 frames; at a throttled ~20 fps it is ~60 frames. A p95 over 60 samples is the 57th-of-60 value — noisy. p99 over 60 samples is essentially `max`. **REC:** ≥ 8-10 s post-warm-up for a stable p95, and treat p99 as indicative only unless the window is much longer.
3. **Warm-up drop of one frame is insufficient.** Shader compile, texture upload, tile streaming (the CUDEM tileset per `WFX-R13` §1) and JIT warm-up span **many** frames, not one. Dropping only `deltas[0]` (`render_route.mjs:70`) leaves shader-compile spikes in the distribution, inflating p95/p99/max. **REC:** discard the first ~1-2 s of samples, not one frame.
4. **Single run, no repeat aggregation.** The harness emits one distribution per invocation. There is no multi-run median-of-medians, so run-to-run variance is invisible.
5. **No CPU/GPU tier control in the measured path.** As written it measures whatever the host is: a T4 (server-class) or SwiftShader (software raster). Neither is a client laptop tier — `RUNBOOK.md:25-27` and `PRF_CHARTER.md:13-14` both say the T4 number is an upper-bound sanity check, not the binding client-tier budget.

---

## 2. CDP CPU throttling — `Emulation.setCPUThrottlingRate` (mechanics + wiring)

### Mechanics (FACT about the CDP method; REC for how to apply it here)
- `Emulation.setCPUThrottlingRate` takes a single param `{ rate }`, a **slowdown multiplier**: `rate: 1` = no throttle, `rate: 4` = main thread runs ~4× slower. It is implemented in V8/Blink as a busy-wait inserted into task execution, so it slows **main-thread CPU work** (JS, layout, the rAF callback, raster scheduling on the main thread).
- **It does NOT throttle the GPU.** Shader execution, fill-rate, and the GPU process are untouched. It also does not perfectly model a slower memory subsystem or a different CPU microarchitecture — it is a uniform time-dilation of main-thread tasks, not a cycle-accurate model of a specific client CPU.
- **Honesty consequence:** a CPU-throttled run honestly emulates the **CPU-bound portion** of the frame (the r3f update loop, depth-prepass *dispatch*, JS-side BSW work — spectrogram Worker coordination, multi-orca update). It does **not** emulate a weaker **GPU**. So the only honest label is "CPU throttled to Nx; GPU = <the real glRenderer>".

### Wiring through Playwright (REC, grounded in the harness's actual API surface)
- **FACT** `render_route.mjs` uses Playwright `chromium` (`render_route.mjs:9-10`), launches `chromium.launch` (`:37`), and creates the page with `browser.newPage(...)` (`:38`).
- **REC** Playwright exposes CDP on chromium two ways:
  - `const client = await page.context().newCDPSession(page);` — a **page/target-scoped** session. This is the correct one for CPU throttling because the rate is applied to the page's renderer.
  - `const client = await browser.newBrowserCDPSession();` — a **browser-scoped** session (no page target); useful for browser-global domains, **not** for per-page `Emulation.*`.
- **REC** Minimal wiring (illustration only — PRF-B implements it, not this wave):

```js
const client = await page.context().newCDPSession(page);
await client.send('Emulation.setCPUThrottlingRate', { rate: ORCAST_CPU_THROTTLE }); // e.g. 4
// apply BEFORE the settle/sample so warm-up is also throttled consistently
```

  Apply it after `newPage` (`render_route.mjs:38`) and **before** `page.goto`/the settle, so warm-up and the sampled window are under the same throttle. Record the `rate` into the output JSON next to `frameTime` (`render_route.mjs:106-111`) so every number carries its throttle.
- **FACT/constraint** This is explicitly allowed: `PRF_CHARTER.md:40-42` and the dispatch lock (`ORCHESTRATOR_DISPATCH_PROMPT.md:22`) permit `Emulation.setCPUThrottlingRate`. `CDP Input.*` is **not** used (focus-sensitive) — and note that constraint is also true of the operator's cursor-ide-browser MCP (`browser_cdp` exists but `Input.*` is denied); that operator browser is **separate** from the host harness, which runs its own Playwright chromium.

---

## 3. GPU-tier emulation — options + honesty rating

**FACT:** there is **no** CDP "GPU throttle" method. CDP can slow the CPU and the network, not the GPU. So a "weaker GPU tier" can only be approximated by changing *what GPU/rasterizer runs* or *how many pixels it must fill*. Enumerated options and their honesty:

| Option | What it does | Honesty rating | Verdict |
|---|---|---|---|
| **(a) ANGLE backend = real T4** (`ORCAST_GL=gpu`, `render_route.mjs:31-33`: `--use-gl=angle --use-angle=gl-egl --enable-gpu`) | Real NVIDIA Tesla T4 GPU via ANGLE/EGL. `glRenderer = "ANGLE (NVIDIA…Tesla T4…)"` (`RUNBOOK.md:11-12`). | **Honest only as a server-class upper bound.** It is a *real* GPU number but a *faster-than-client* GPU. | Honest **upper bound** label; a **lie** if reported as "client tier". |
| **(b) ANGLE backend = SwiftShader** (`ORCAST_GL=swiftshader`, default, `render_route.mjs:34-35`: `--use-angle=swiftshader-webgl --enable-unsafe-swiftshader`) | **CPU software rasterizer.** No GPU at all. The harness header itself says this is "correctness only … NOT a client-tier perf measurement" (`render_route.mjs:3-6`). | **Dishonest as any GPU tier.** SwiftShader is not "a weaker GPU" — it is a different cost model (CPU-bound fill, no fixed-function GPU pipeline). Its frame-time correlates with neither a fast nor a slow client GPU. | **Lie** if reported as a client GPU tier. Correctness-only. |
| **(c) Resolution / deviceScaleFactor scaling** (viewport `ORCAST_VW/VH`, `render_route.mjs:25-26,38`; `deviceScaleFactor` would be added) | Scales the pixel count the fragment stage must fill. Fill/fragment cost is roughly linear in pixels. | **Honest as a fill-rate knob, NOT as a GPU-tier knob.** Lowering pixels lowers GPU fill on the *same* (T4) architecture; it does not turn a T4 into a laptop iGPU (different ALU count, bandwidth, driver). | Honest **only** when reported as "rendered at WxH @ scale S"; does **not** by itself make the number "client tier". |
| **(d) `--gpu` / ANGLE flags forcing a lower path** (e.g. `--use-angle=…`, blocklist toggles) | Selects a backend/driver path. There is **no** flag that makes a T4 perform as a specific weaker GPU tier. | **No honest "downgrade" exists.** Forcing SwiftShader = option (b). Forcing a different ANGLE backend on the same T4 changes the driver path, not the silicon. | Cannot honestly emulate a weaker GPU tier. |

### Bottom line on GPU emulation (honesty)
- **There is no defensible way on this host to emulate a *weaker GPU tier* and call the result a client-GPU number.** The T4 is too fast (upper bound); SwiftShader is not a GPU at all (correctness-only); resolution scaling is a fill knob on the wrong silicon.
- The only **honest** GPU-bound combination available here is: **real T4 GPU (a) + CPU throttle (§2) + resolution matched to the target client device (c)**, reported as *"CPU emulated to Nx; rendered at the client viewport; GPU = real Tesla T4 (server-class, so GPU-bound cost is an UPPER BOUND of client speed → a LOWER BOUND on client frame-time)."* That is honest because it never claims a client GPU; it states the GPU is faster than the target and therefore the GPU-bound part of the frame is optimistic.
- A genuinely representative **GPU-tier** number requires a **real client GPU** — a human/hardware gate (`PRF_CHARTER.md:42`, `wave_shape.yml:83`).

---

## 4. Emulated-on-T4-host vs a REAL client-tier device

| Axis | Emulated on T4 host (CPU throttle + resolution + real T4 GPU) | Real client-tier device |
|---|---|---|
| CPU-bound frame cost | Honestly modeled by `setCPUThrottlingRate` (a uniform slowdown, not a specific microarch) | Exactly the target |
| GPU-bound frame cost | **Optimistic** — T4 >> laptop iGPU; the 2U fill baseline (`WFX-R13` §1-2) is understated | Exactly the target |
| Repeatability / isolation | High — serial on an isolated EC2, no thermal/throttle noise, scriptable over SSM (`render.sh`) | Lower — thermal throttling, background apps, OS scheduler, battery vs AC |
| Cost / gate | Already-running host; `ORCAST_PERF=1` flag, no acquisition | Hardware acquisition = **human/O0 gate** (`PRF_CHARTER.md:42`, `wave_shape.yml:83`) |
| What it can honestly claim | "emulated client tier (CPU Nx, viewport WxH, GPU = T4 server-class upper bound)" → a **lower bound on client frame-time** | "measured on <device model>, <GPU>, <OS/browser>" → the real number |

**How each is reported honestly:**
- **Emulated:** verdict must read e.g. *"Emulated client tier — method: Playwright headless chromium, real Tesla T4 GPU (glRenderer recorded), `Emulation.setCPUThrottlingRate` rate=N, viewport WxH @ scale S, sample T s × R runs. GPU is server-class, so the GPU-bound portion is an upper bound on client GPU speed; the reported frame-time is therefore a **lower bound** (optimistic) for the named client tier. Not a real-device measurement."*
- **Real device:** verdict records the exact device, GPU string (same `UNMASKED_RENDERER` capture as `render_route.mjs:94-104`), OS, browser build, AC/battery, and whether the page was foreground; no emulation qualifier needed.

---

## 5. Stable median + p95 recipe (mechanics; cross-check vsync with R4)

**REC**, building on the existing sampler:
1. **Warm-up:** discard the first **~1-2 s** of samples (not just one frame as `render_route.mjs:70` does). Let shader compile, tile streaming and JIT settle before counting.
2. **Sample window:** **≥ 8-10 s** of *counted* frames (raise `ORCAST_PERF_MS`, `render_route.mjs:22`). This gives ~150-600 counted intervals depending on tier, enough for a stable p95. Treat p99/max as indicative unless the window is much longer.
3. **Repeats:** **≥ 3 independent runs** (fresh page each time). Report **median-of-medians** and the **max of the per-run p95** (conservative), plus run-to-run spread. A single run is not sufficient for a verdict.
4. **Serial isolation:** one GL context at a time on the isolated host — already mandated (`render_route.mjs:52-54`, `PRF_CHARTER.md:47-48`, `wave_shape.yml:28`). Do not run a second render concurrently; concurrent contexts corrupt frame-time.
5. **Vsync / headless (DEFER honesty call to R4; mechanics here):** the number is only meaningful if the rAF cadence is *not* artificially pinned. Two honest options:
   - **Uncapped render-cost mode:** ensure headless does not vsync-cap (the typical headless default), so the rAF interval reflects true per-frame cost; then compare the *cost* directly to the 33.3 ms budget. This is the cleaner "did we exceed the budget" signal and matches what the in-code comment *assumes* but does not enforce (`render_route.mjs:49-54`).
   - **Presented/vsync mode:** if a compositor cap is present, a frame at the cap reads as the refresh interval and *hides* overruns — must be detected and rejected, or the cap raised above 30 fps, before trusting the median.
   The harness must **record which regime it ran in** (e.g. log whether frames cluster at a fixed cadence) so the verdict is not read off a hidden cap. This is the main item to reconcile with R4's vsync/headless analysis.
6. **Tag every number** with: `glRenderer`, `glMode`, CPU throttle rate, viewport/scale, sample seconds, run count. The harness already emits `glMode`/`glRenderer`/`frameTime` together (`render_route.mjs:106-111`); extend with throttle+viewport+runs in PRF-B.

---

## 6. Recommended method

**Recommended: "emulated client tier (method X)"**, where **method X = headless Playwright chromium on the isolated host, real Tesla T4 GPU, `Emulation.setCPUThrottlingRate` at the rate PRF-Q fixes for the chosen CPU tier, client-matched viewport+deviceScaleFactor, ≥1-2 s warm-up dropped, ≥8-10 s counted window, ≥3 serial runs, median-of-medians + worst-run p95, with the vsync regime recorded.**

**Reported honestly as:** *an emulated client-tier frame-time whose CPU tier is throttled and whose GPU is a server-class T4 — therefore a LOWER BOUND (optimistic) on the named client tier's frame-time, not a real-device measurement.* If that lower bound already misses 33.3 ms, the miss is real and dispositive; if it passes, it is **not** sufficient to claim the real client tier passes (the GPU-bound part is understated) — that requires the real-device path.

**Rejected alternatives:**
- **SwiftShader as a "weak GPU" proxy** — rejected: it is CPU software raster, not a GPU tier; the harness header itself says correctness-only (`render_route.mjs:3-6`). Reporting it as a client GPU number is a lie.
- **Bare T4 number reported as the client tier** — rejected: server-class upper bound (`RUNBOOK.md:25-27`, `PRF_CHARTER.md:13-14`); this is the exact gap that chartered this lane.
- **Resolution scaling alone to "downgrade" the GPU** — rejected: a fill knob on the wrong silicon; honest only as a viewport label, not a tier.
- **Real-device-first** — not rejected on merit (it is the gold standard) but it is a **human/hardware gate** (`PRF_CHARTER.md:42`); the emulated lower-bound is the defensible thing this lane can run now, with the real device named to O0 as the gate to close the GPU-tier gap.

---

## 7. Open questions / human gates
1. **CPU throttle rate** to model the PRF-R1 client tier — fixed by PRF-Q before any run (`PRF_CHARTER.md:37-39`). `setCPUThrottlingRate` is a uniform slowdown, not a named-CPU model; PRF-Q must justify the multiplier against R1's target device.
2. **Vsync/headless regime** — must be pinned and recorded (reconcile with R4). The current sampler *assumes* a vsync cap (`render_route.mjs:49-54`) but does not enforce or detect it.
3. **GPU-tier gap is unclosable on this host** — does O0 accept the emulated **lower bound** as the lane's deliverable, or open the **real client GPU** acquisition gate (`PRF_CHARTER.md:42`, `wave_shape.yml:83`)? The emulated number cannot, by itself, certify a *pass* of the real client tier.
4. **Sample length & repeat count** raise host run time/cost — a human gate per `ORCHESTRATOR_DISPATCH_PROMPT.md:37` and `wave_shape.yml:84`.
5. **BSW-on vs BSW-off A/B** must run under *identical* throttle+viewport+vsync settings serially so the BSW cost is isolated (charter acceptance, `PRF_CHARTER.md:66`); the A/B driver is PRF-B's job.

---

## 8. TL;DR
- The in-repo rAF sampler (`render_route.mjs:56-92`, `ORCAST_PERF=1`) honestly measures the **live page's per-frame cadence** with median/p95/p99 and tags it with the real `glRenderer` — but its 3 s window, single dropped warm-up frame, single run, and **unenforced vsync assumption** make it not yet verdict-grade, and it measures whatever host GPU it runs on (T4 or SwiftShader), neither of which is a client tier.
- **CPU throttling** (`Emulation.setCPUThrottlingRate`, wired via `page.context().newCDPSession(page)`) honestly emulates the **CPU-bound** part of the frame; it does **not** touch the GPU.
- **There is no honest GPU-tier emulation on this host.** T4 = server-class upper bound; SwiftShader = correctness-only software raster (not a GPU tier); resolution = a fill knob, not a tier. A real client-GPU number is a **human gate**.
- **Recommendation:** report an **emulated client tier** = real T4 GPU + CPU throttle + client viewport + the stable recipe (≥1-2 s warm-up dropped, ≥8-10 s window, ≥3 serial runs, recorded vsync regime), explicitly labeled a **lower bound** on the named client tier because the GPU is faster than client. A miss is dispositive; a pass does **not** certify the real client tier — that needs the real device.
