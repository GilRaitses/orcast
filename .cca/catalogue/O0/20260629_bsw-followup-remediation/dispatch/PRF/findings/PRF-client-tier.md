# PRF-R1 — Client tier the 30fps budget is defined against

## Question

What hardware tier is the 30fps budget (and the paired 60fps budget) defined
against? What is the project's stated target device / client tier? Recommend 1-3
representative client GPU/CPU classes the emulated tier should stand for, grounded
in what the repo states rather than invented hardware.

## Findings

### 1. Where the budget is stated, and what device class it is tied to

The budget is stated identically in two forms across code and docs. Both forms
name a usage class ("desktop", "laptop") but neither pins a specific GPU/CPU
model.

Code source of truth, `web/lib/scene/ocean/perf.ts:14-24`:

```14:24:web/lib/scene/ocean/perf.ts
/** Desktop and laptop frame budgets the A/B is judged against. */
export interface FrameBudget {
  label: string;
  targetFps: number;
  budgetMs: number;
}

export const FRAME_BUDGETS: { desktop: FrameBudget; laptop: FrameBudget } = {
  desktop: { label: "60 fps desktop", targetFps: 60, budgetMs: 1000 / 60 },
  laptop: { label: "30 fps laptop", targetFps: 30, budgetMs: 1000 / 30 },
};
```

So the binding numbers are 60fps = 16.67 ms (`desktop`) and 30fps = 33.3 ms
(`laptop`). The labels are the only device class attached, and they are usage
words, not hardware.

The same pairing is restated in many places. Representative citations:

- `web/lib/scene/hud/spectro/WIRING.md:184` — "`FRAME_BUDGETS` (60 fps desktop =
  16.67 ms, 30 fps laptop = 33.3 ms)".
- `infra/render_host/render_route.mjs:20` — "binding client-tier (60fps-desktop /
  30fps-laptop) budget."
- `.cca/catalogue/O0/20260628_water-fx/WAVESET_CHARTER.md:72` — "Frame budget is a
  first-class constraint: 60fps desktop / 30fps laptop".
- `.cca/catalogue/O0/20260627_terrain-bathymetry-twin/wave_shape.yml:170` —
  "frame_budget: 60fps-desktop / 30fps-laptop".
- `.cca/catalogue/O0/20260628_water-fx/research/WFX-R03_reflections.md:180` —
  "60fps desktop is a 16.7 ms frame, 30fps laptop is a 33.3 ms frame."
- `.cca/catalogue/O0/20260628_water-fx/research/WFX-R08_underwater_volumetrics.md:112`
  — "Budget is 60 fps desktop and 30 fps laptop, which is 16.6 ms and 33.3 ms per
  frame."

### 2. What device the budget is held against on the render host

The render host is explicitly NOT the client tier. The runbook flags the Tesla T4
as a server-class upper bound.

`infra/render_host/RUNBOOK.md:25-27`:

```25:27:infra/render_host/RUNBOOK.md
- **Perf caveat:** the T4 gives a REAL-GPU baseline, but it is a server-class GPU,
  not a client laptop tier. Treat `U` numbers from here as an upper-bound sanity
  check, not the binding client-tier budget.
```

`infra/render_host/render_route.mjs:5-6` and `:17-20` repeat that the host number
is correctness/upper-bound only and "U must be measured on real client GPUs, not
here", and call the 30fps-laptop pairing the "binding client-tier" budget.

The BSW ACCEPT verdicts inherited this caveat verbatim. `.../dispatch/BSH/gate_screenshots/VERDICT.md:56-57`
— "The T4 is a server-class GPU, so per the RUNBOOK this is an upper-bound sanity
check, not the binding 30 fps-laptop client-tier number." The BRE verdict says the
same at `.../dispatch/BRE/gate_screenshots/VERDICT.md:34`.

### 3. The closest the repo comes to a concrete device class

No file in the repo names a GPU vendor, GPU model, SoC, or CPU class for the
client tier. The most concrete characterization is in the predecessor adversarial
perf research, which describes the two tiers by GPU type, not by model.

`.cca/catalogue/O0/20260628_water-fx/research/WFX-R13_perf_adversarial.md:58-60`:

```58:60:.cca/catalogue/O0/20260628_water-fx/research/WFX-R13_perf_adversarial.md
Estimated value of U, labeled estimated, no measurement taken. On a desktop discrete GPU
rendering the streamed multi-LoD CUDEM tileset I estimate U at 2 to 5 ms. On a weak laptop
integrated GPU I estimate U at 8 to 18 ms. The wide band is honest. The tile count, the
```

Same file, `:128-130`, names the laptop as the binding tier:

```128:130:.cca/catalogue/O0/20260628_water-fx/research/WFX-R13_perf_adversarial.md
clear headroom. Against a laptop frame of 33.3 ms minus 2U of 16 to 36 ms, the default
the high end. The binding constraint is the laptop, and the binding cost is U, not the
```

So the implicit reading the repo holds the 30fps budget to is:

- "desktop" = a **desktop discrete GPU**. `WFX-R13:58`.
- "laptop" = a **weak laptop integrated GPU**. `WFX-R13:59-60`.

The 30fps/laptop/iGPU tier is treated as the binding constraint, because at the
2U baseline a laptop iGPU is already at or over its 33.3 ms budget from the depth
pre-pass alone. `WFX-R13:64-66` and `:128-130`.

### 4. Is a device class ever pinned explicitly?

No. Searching the codebase and catalogue for any named hardware class tied to the
budget (Intel Iris/Xe, Apple M-series, Radeon, Adreno/Mali, GTX/RTX, "integrated
GPU" as a named target, a CPU model) returns no result that pins the client tier
to a specific device. The only attached classes are the usage words "desktop" and
"laptop" in `FRAME_BUDGETS`, plus the GPU-type prose "desktop discrete GPU" and
"weak laptop integrated GPU" in WFX-R13. The 30fps number itself is a vsync target
(`budgetMs: 1000 / 30` in `perf.ts:23`), not a device benchmark.

## Recommended representative client tier(s)

The budget should be emulated against the laptop/integrated-GPU tier, because the
repo names that as the binding constraint. Recommended representative classes,
ranked, all defensible from the repo's own "weak laptop integrated GPU" wording at
`WFX-R13:59-60`:

1. **Primary (binding): a mid-2020s laptop integrated GPU.** This is the literal
   tier the repo binds the 30fps budget to. A defensible stand-in is an Intel
   Iris Xe class iGPU or an Apple M-series base iGPU, paired with a 4-to-8 core
   mobile CPU. Reasoning: the repo's only device-type characterization of the
   laptop tier is "weak laptop integrated GPU", and it explicitly calls the laptop
   the binding constraint at `WFX-R13:128-130`. An iGPU has no dedicated VRAM and
   shares memory bandwidth with the CPU, which is exactly the profile that makes
   the streamed multi-LoD tileset 2U baseline expensive at `WFX-R13:64-66`.

2. **Secondary (sanity ceiling): a mid-tier discrete laptop/desktop GPU.** This
   maps to the repo's 60fps "desktop discrete GPU" tier at `WFX-R13:58`. It is not
   the binding number, but it brackets the headroom the T4 upper bound cannot
   resolve, since the T4 result is vsync-capped at 60 Hz and only proves "under
   60fps", per `WFX-R13:53-56` style caveats and the BSH verdict at
   `.../BSH/gate_screenshots/VERDICT.md:53-57`.

3. **CPU class:** a mobile multi-core CPU in the 4-to-8 core range to match the
   laptop iGPU pairing. The repo does not state a CPU model, so this is the only
   honest framing. The capture method lane PRF-R2 is the place to fix the exact
   CDP `Emulation.setCPUThrottlingRate` factor, per `PRF_CHARTER.md:40-42`.

Honesty constraint per `PRF_CHARTER.md:34-36`: whatever tier is emulated must be
reported as "emulated client tier (method X)", never as a named real device,
unless a real device is actually used.

## Open questions / gaps

1. The repo never pins a specific GPU/CPU model for the client tier. PRF-Q must
   choose the representative iGPU/CPU emulation target, since the charter only
   says "30fps laptop / iGPU" in prose, not a benchmarkable device. `PRF_CHARTER.md:53`.
2. The "weak laptop integrated GPU" U estimate of 8-18 ms at `WFX-R13:59-60` is an
   estimate with no measurement. Whether a CDP-throttled T4 can faithfully emulate
   an iGPU's shared-memory-bandwidth profile is a PRF-R2/PRF-R4 question, not
   settled here.
3. The 30fps number is a vsync target, not a device pass/fail benchmark. The host
   rAF sampler is vsync-capped, so it confirms "under 60fps" but cannot resolve
   sub-cap headroom. `WFX-R13:53-56`. A representative tier emulation has to break
   the vsync cap to expose a real per-frame cost, which is a PRF-R2 method concern.

## TL;DR for the orchestrator

The 30fps budget is NOT pinned to a named device anywhere in the repo. It is
defined in code as `FRAME_BUDGETS.laptop = { 30 fps, 33.3 ms }` at
`web/lib/scene/ocean/perf.ts:21-23`, attached only to the usage word "laptop", and
restated everywhere as the "30fps laptop" half of a "60fps desktop / 30fps laptop"
pair. The one concrete device-type description is in WFX-R13, which holds the
30fps tier to a "weak laptop integrated GPU" and the 60fps tier to a "desktop
discrete GPU", and names the laptop iGPU as the binding constraint. The render
host T4 is explicitly a server-class upper bound, not the client tier
(`infra/render_host/RUNBOOK.md:25-27`). Recommended representative client tier to
emulate: a mid-2020s laptop integrated GPU such as Intel Iris Xe class or Apple
M-series base, with a 4-to-8 core mobile CPU, reported honestly as an emulated
tier. PRF-Q must pick the exact emulation target, because the repo gives a tier
description, not a benchmarkable device.
