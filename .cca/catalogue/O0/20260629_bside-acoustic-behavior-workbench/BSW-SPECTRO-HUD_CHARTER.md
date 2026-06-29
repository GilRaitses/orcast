# BSW-SPECTRO-HUD charter (WebAudio spectrogram HUD + interpretive ocean-process layer)

- Lane code: **BSH** (under family BSW)
- Owner: O0 dispatches; a background sub-orchestrator runs the gated build waves.
- Type: research-first (grounded by BSW-RESEARCH R06/R09/R13); build/integrate/accept gated.
- `repo_state_verified_against`: origin/main `240570e961913fb610c2765a4ef77cace3f216f1`.
- Charter method: `~/.cursor/skills/waveset-orchestration/SKILL.md`. Umbrella: `PROGRAM.md`.

## Intent (operator)
A spectral visualizer like the research pages, as a HUD in the terrain-bathymetry model; and the
orca biosonar POV persisting a layer that carries the larger ocean processes - the double diffusion
of warm salty water going down and cold mineral-rich water coming up, like a lava lamp in both
directions - that you could replay.

## Grounding (verified seams)
- Today's spectrogram is a static ONC `<img>` PNG (`web/app/components/console/HydrophoneSignalPanel.tsx`
  via `src/aws_backend/routers/onc.py`, needs `ONC_API_TOKEN`). No WebAudio/canvas, no scrub.
- HUD-over-canvas precedent: drei `Html` hover labels + `web/lib/scene/picking/PerfHud.tsx` (DOM
  portal, `SHOW_PERF_HUD=false`); sandbox `StateHud` in `web/app/(sandbox)/journey/`. No 2D
  spectrogram canvas HUD exists.
- Audio comes from BST's player binding; the spectrogram feature is shared with BAM (compute once).
- Scene transition (above/below water): `web/lib/scene/atmosphere/transition.ts`; WFX env handle
  `web/lib/scene/wfx/realWfxEnv.ts`.

## Locked decisions (do NOT reopen)
- **Real spectrogram from real audio**, computed client-side (WebAudio/AudioWorklet FFT -> canvas/
  WebGL), so it does NOT depend on `ONC_API_TOKEN`. Scrub/slow-down moves a synced playhead; the
  HUD is the time authority the reenactment (BRE) follows.
- **Compute-neutral:** FFT off the main thread (AudioWorklet) where possible; the spectrogram
  renders to a 2D canvas/texture, not an extra full 3D pass. Costed against 60fps/30fps budget.
- **The double-diffusion / thermohaline layer is `interpretive`.** Double-diffusive convection /
  salt-fingering is real Salish Sea oceanography, grounded in cited stratification data (BSW-R09);
  but "orca biosonar perceives it" is speculative and **labeled interpretive on screen**, never
  presented as measured perception. It is a stylized volumetric/shader layer, gated/optional, that
  must not regress water realism (coordinate with WFX via O0).
- **House style:** built on `three` + existing shaders; a new audio/FFT/render dependency is a
  costed recommendation, not a default.

## Wave structure
- **BSH-BUILD** (gated, net-new): `web/lib/scene/hud/spectro/` (WebAudio FFT + canvas/WebGL
  spectrogram + scrub playhead) and `web/lib/scene/ocean/` (interpretive double-diffusion layer),
  tuned in a sandbox; `tsc`/lint clean; verified on the GPU render host.
- **BSH-INTEGRATE** (gated, single editor): mount the HUD + (optional) ocean layer into the twin;
  serialize `SalishScene.tsx`/`globals.css` vs LGC/CVP/WFX/ORCA/3D-TWIN.
- **BSH-ACCEPT** (gated): Read-examined frames - spectrogram tracks the audio, scrub moves the
  playhead, the ocean layer reads as a labeled interpretive layer, frame budget held.

## Acceptance criteria (hard, checkable)
- A real, scrubbable spectrogram renders from the slice clip's real audio (no ONC token needed).
- Scrub/slow-down moves a synced playhead that BRE can follow.
- The double-diffusion layer renders and is on-screen-labeled `interpretive`; no water regression.

## Escalation
Answers to O0. New dependency, perf-budget risk, WFX water-regression risk, the interpretive-claim
wording, convergence collisions, or any gated step: pause and return to O0.

## Return contract
Net-new file list + WIRING; GPU-host gate frames; the time-sync contract BRE consumes; the exact
interpretive-label wording; perf numbers; open questions for O0.
