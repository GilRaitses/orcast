# PRF-Q — Methodology (locked by O0 at the PRF-Q gate)

> Qualification finding for BSWR-PRF "client-tier-frametime-verify". This file
> records the methodology O0 fixed at the PRF-Q gate, BEFORE any frame-time
> number is produced. It is the binding spec for PRF-B (harness) and PRF-ACCEPT
> (the gated host run). Repo verified against the charter pin
> `61ba1d69ee36cf605f7ba741bdaa1defa8762834`.
>
> Inputs: PRF-R findings `PRF-client-tier.md` (R1), `PRF-capture-method.md` (R2),
> `PRF-scenes.md` (R3), `PRF-adversarial.md` (R4). The R-wave summary was returned
> to O0; O0 ruled. These decisions are LOCKED — do not reopen.

---

## ADV-1 amendment (O0-ruled, binding — read before §2/§4/§6)

`PRF-ADV` verified locally that the two vsync-uncap launch flags do NOT free-run
the rAF cadence below one refresh in pure headless chromium (the synthetic
compositor BeginFrame paces ~60Hz independent of GPU vsync), so the rAF interval
cannot resolve a sub-refresh frame-time. O0 ruled ADV-1 (`PRF-ADV1-DECISION.md`):
**adopt Option 1 — the vsync-quantised 30fps over-budget oracle — as the PRF
verdict method.** This supersedes the "uncap the cap, then trust the rAF
frame-time" premise that §2 step 2 and §6 were originally written against. The
substance below stands; the verdict framing is now the quantised oracle:

- The rAF interval quantises to refresh multiples (~16.7 / 33.3 / 50 ms). It is
  dispositive against the 30fps (33.3 ms) budget — it catches a real miss — but it
  **cannot resolve sub-refresh headroom**.
- `subRefreshProven:false` is recorded honestly and stays
  (`gate_captures/vsync_smoke_local.json`). The over-budget probe
  (`gate_captures/overbudget_probe_local.txt`) demonstrates the buckets: 25 ms
  work → ~33 ms bucket; 45 ms work → ~50 ms bucket.
- The uncap flags STAY (harmless; they may genuinely uncap on the Linux/Xvfb/T4
  host — ADV-3, unconfirmed). The CPU throttle STAYS (it pushes fixed-work scene
  frames into the higher buckets; the busy-loop probe null was a wall-clock probe
  artifact, ADV-2).

## 1. Client tier (the budget's target)

- Budget: **30fps = 33.3 ms/frame**, BSW-on. Defined in code as
  `FRAME_BUDGETS.laptop = { targetFps: 30, budgetMs: 1000/30 }`
  (`web/lib/scene/ocean/perf.ts:21-23`); never pinned to a named device in-repo.
- **Locked emulation target:** a **mid-2020s laptop integrated-GPU class**
  (the "weak laptop integrated GPU" the budget is implicitly held to, per
  `WFX-R13_perf_adversarial.md:59-60,128-130`), with a mobile multi-core CPU.
- The **GPU stays the host Tesla T4** (acknowledged optimistic for a GPU-bound
  twin). There is no honest GPU-tier emulation on this host (R2 §3: SwiftShader
  is software raster, not a GPU tier; resolution is a fill knob; the T4 is
  server-class). The CPU tier is emulated; the GPU tier is **not** — this is the
  central honesty caveat carried into the verdict.

## 2. Capture method (locked: "emulated client tier (method X)")

Method X =

1. **Host + GL:** headless Playwright chromium on the isolated render host, real
   Tesla T4 GPU (`ORCAST_GL=gpu` → `--use-gl=angle --use-angle=gl-egl
   --enable-gpu`). Never SwiftShader for a tier number (correctness-only,
   `render_route.mjs:3-6`).
2. **Vsync flags + quantised reading (ADV-1-amended).** Add `--disable-gpu-vsync`
   and `--disable-frame-rate-limit` to the chromium launch. The sampler is
   vsync-pinned at ~16.67 ms — empirically confirmed: BSH and BRE A/B verdicts
   both returned a flat 16.67 ms across different feature loads
   (`BSH .../VERDICT.md:48-57`, `BRE .../VERDICT.md:26-34`), and PRF-ADV proved
   the flags do NOT break that cap in pure headless (`vsync_smoke_local.json`,
   `subRefreshProven:false`). Per O0's ADV-1 ruling the rAF interval is therefore
   used as a **vsync-quantised 30fps over-budget oracle**, not a sub-refresh
   frame-time meter: it clamps to refresh multiples and spaces out once a frame's
   true cost exceeds a refresh deadline (verified, `overbudget_probe_local.txt`).
   The flags stay (harmless; may genuinely uncap on the host — ADV-3).
3. **CPU throttle:** `Emulation.setCPUThrottlingRate` via
   `page.context().newCDPSession(page)` (page-scoped), applied BEFORE the
   navigate/settle so warm-up is throttled consistently. Rate is the emulation
   knob for the laptop CPU tier (default 4×; PRF-B records the exact rate used).
4. **Client viewport:** client-matched viewport + `deviceScaleFactor` (default
   1280×800 @ 1, the demo viewport; recorded in output).
5. **Hardened rAF sampler:** drop a longer **warm-up** (first ~2 s, not one
   frame as `render_route.mjs:70` does), **counted window ≥ 8–10 s** (not the 3 s
   default at `render_route.mjs:22`), **≥ 3 serial runs** → report
   **median-of-medians** and the **worst-run p95**. Serial only (one GL context
   at a time; concurrent contexts corrupt frame-time).

**Rejected alternatives (from R2/R4):** SwiftShader-as-weak-GPU (a lie; software
raster, wrong magnitude and bottleneck); bare T4 reported as the client tier (the
server-class upper bound this lane exists to correct); resolution-scaling alone as
a GPU downgrade (a fill knob on the wrong silicon); real-device-first (the gold
standard but a human/hardware gate — deferred per §5).

## 3. Two clearly-labeled numbers (never one)

Every capture reports BOTH, each tagged with `glRenderer` + CPU throttle rate +
viewport + vsync state:

- **(a) T4 reference (server-class):** `ORCAST_GL=gpu`, throttle rate 1, vsync
  flags on. A vsync-quantised reading on the real host GPU: a clamped ~16.7 ms
  median means the T4's true cost is under one refresh, NEVER reported as a literal
  16.7 ms frame-time. Honest label: **server-class upper bound** (faster than any
  client GPU).
- **(b) Emulated laptop-iGPU lower bound:** `ORCAST_GL=gpu`, CPU throttle rate N,
  client viewport, vsync flags on. Same vsync-quantised reading. Honest label:
  **CPU-throttled lower bound on a server-class GPU** — optimistic for the named
  client tier because the GPU work is not throttled. The CPU throttle pushes
  fixed-work scene frames into the higher over-budget buckets when they are
  CPU-bound.

## 4. Pass metric + honesty lock

- **Pass metric:** sustained **median AND p95** rAF interval read as quantised
  buckets vs **33.3 ms/frame**, BSW-on, at the emulated tier (b). Median-of-medians
  across ≥3 runs; worst-run p95.
- **HONESTY LOCK (verdict wording, binding — O0 ADV-1 conditions verbatim):**
  - The reading is **vsync-quantised** and **cannot resolve sub-refresh headroom**
    (a 5 ms frame and a 16 ms frame both read ~16.7 ms).
  - A clamped **~16.7 ms median → "PASS 30fps with margin (true cost < one
    refresh)"**, and is **NEVER reported as "the frame-time is 16.7 ms"** (that is
    the forbidden fabricated-headroom claim from PRF-R4).
  - A sustained **~33.3 ms cluster → "at/under the 30fps budget"**.
  - Sustained **≥50 ms → "FAIL 30fps, the miss is real"** and is dispositive (the
    real client GPU is slower, so it also misses).
  - The emulated number stays a **CPU-throttled lower bound on a server-class GPU**;
    a pass does **NOT** certify the real client GPU. The verdict states the method
    verbatim, never drops "emulated", and never smooths a miss (a miss returns a
    separate-optimization-lane recommendation to O0 per `PRF_CHARTER.md:67`).

## 5. Real client-GPU device — deferred

No real client-GPU device up front. Escalate hardware acquisition to O0 **only
if** the emulated lower bound passes and certification of the real client tier is
required. Host run cost/time remains the human gate at PRF-ACCEPT.

## 6. Smoke + over-budget probes (ADV-1-amended: validity proof, not an uncap gate)

The original premise — "the smoke must report sub-16.67 ms or no number is valid"
— is superseded by O0's ADV-1 ruling. The smoke is now run as a **clamp
confirmation**, and the over-budget probe is the **oracle-validity proof**:

- **Clamp confirmation (`vsync_smoke_local.json`):** on a trivial empty-rAF page,
  the uncap flags leave the cadence clamped (~17.4 ms uncapped vs 16.7 ms capped
  control). **`subRefreshProven:false`** — recorded honestly; no sub-refresh
  number is claimed. (Re-run local, macOS pure-headless, 2026-06-29.)
- **Over-budget validity (`overbudget_probe_local.txt`):** a page burning a fixed
  wall-clock per rAF, read by the harness's exact separate-sampler loop, shows the
  interval quantises to refresh multiples — 2/10 ms work clamps at ~17 ms, **25 ms
  work spills its p95 to the ~33 ms bucket, 45 ms work spills its median to the
  ~50 ms bucket**. This proves the oracle catches a 30fps miss. (Re-run 2026-06-29,
  matches the original within noise.) The throttle=4× rows stay clamped because a
  wall-clock burn is not slowed by CPU-throughput throttle — a probe artifact
  (ADV-2), not a harness defect; real fixed-work scene frames DO spill under
  throttle.
- **Host caveat (ADV-3, unconfirmed):** the Linux/Xvfb/T4 host MAY make the flags
  genuinely uncap. A single cheap `--smoke` is queued for the batched host window
  (see PRF-ACCEPT-PLAN); if it free-runs, true sub-refresh numbers are a bonus and
  the Option-1 verdict stays primary.

## 7. A/B plan (both arms, from R3)

Real toggles read at `SalishScene.tsx:1788-1819`. Orcasound Lab
`48.5583362,-123.1735774` is the only clip-bearing node (bakes spectro HUD +
reenactment); the other in-extent nodes are live-listen only and understate cost.

- **Pair 1 — total BSW cost (camera differs, flagged):**
  - off: `/`
  - on:  `/?station=48.5583362,-123.1735774,Orcasound%20Lab&bsw_demo=3&ocean=1`
  - Confound: camera path differs (resting orbit vs station dive-in) + LoD lift.
- **Pair 2 — incremental cost, camera held (`view=topdown` both sides):**
  - light: `/?station=48.5583362,-123.1735774,Orcasound%20Lab&view=topdown`
  - heavy: `/?station=48.5583362,-123.1735774,Orcasound%20Lab&view=topdown&ocean=1&bsw_demo=3`
  - Isolates the ocean layer + multi-orca pool only (both sides carry slice +
    spectro HUD).

**Settle (R3 §4):** the scene animates continuously; sample only after
establishing motion settles — wait for canvas + first tileset fit + tile
streaming quiescence, and for BSW-on additionally the ~3 s camera fly-to and the
slice `status: "ready"` chip — then sample the fixed window. Per-frame steps are
dt-capped (`Math.min(dt, 1/30)`), so a slow frame does not fast-forward animation.

**Gaps carried as confounds (R3 §5):** no slice-off toggle with camera held; no
spectro-HUD-independent toggle; the single always-on `OrcaRig` is in both arms;
LoD lift is coupled to engagement. The verdict reports these, it does not hide
them.

## 8. Files PRF-B owns (harness only; no scene change)

- `infra/render_host/frametime_client_tier.mjs` (new) — the capture harness
  (uncap + CDP CPU throttle + client viewport + hardened sampler + A/B driver +
  `--smoke`).
- `scripts/perf/client_tier_frametime.sh` (new) — the SSM driver for PRF-ACCEPT
  (mirrors `render.sh`; ships the harness, runs it serial on the host, pulls the
  metrics JSON to `gate_captures/`).
- `infra/render_host/render_route.mjs` — surgical harness-only edit: add the
  vsync flags and document that the sampler is a vsync-quantised over/under-budget
  oracle (the verified ADV-1 limit; flags are harmless and may uncap on the host).
  No scene behavior changes anywhere.
