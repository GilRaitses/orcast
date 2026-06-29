# WATER-FX waveset charter (water + atmosphere shading realism)

- Lane code: **WFX**
- Owner: O0 (central orchestrator) dispatches; a background sub-orchestrator runs the waves.
- Type: **research-first** (Wave 1 read-only); build/integrate/accept waves are gated.
- `repo_state_verified_against`: origin/main `915e4cc77923de93ed5f7e9a75feab9eb2e12896` (branch main, 2026-06-28).
- Charter method: `~/.cursor/skills/waveset-orchestration/SKILL.md`.

## Intent (operator)

"We need the charter for the water fx ... which kicks off 13 research agents for water fx for
both bathymetry models and normal above-ground types of water. The shading is very bad, it's
distracting, it needs to be more real. And the horizon with the skybox is still very stark and
abrasive, the sky is white, there's no fog or light from sun."

Two faces of the same lane: the **above-surface** ocean (surface shading, waves, reflections,
sky/atmosphere/sun) and the **underwater / bathymetric** water (volumetrics, absorption, the
modeled-seabed read). The fault is realism: the current look is distracting and unreal.

## Grounding (verified paths, the real seams)

The twin's water + atmosphere is hand-written GLSL on `three` (no new dependency yet):

- `web/lib/scene/water2/depthWater.ts` - depth-driven ocean (`makeWater2`): a 6-wave Gerstner
  sum, a Beer-Lambert column read from an opaque-scene depth pre-pass, a **two-stop color lerp**
  (`mix(uColorShallow,uColorDeep,colorT)`), Fresnel-to-flat-sky, `pow(ndh,90)` specular +
  `pow(ndh,600)` glitter, a thin noise foam band. Water plane at scene Y=0.
- `web/lib/scene/bathy/style/` - `bathyTint.ts`, `deepRamp.ts`, `waterTuning.ts`, and
  **`WATER2_TUNING_REQUEST.md`** (a pending, un-adopted request to replace the two-stop color
  with per-channel RGB extinction `exp(-uAbsorption*column)`, `{r:3.0,g:1.6,b:0.9}`).
- `web/app/components/scene/realism/` - `sun.ts` (`makeSun`), `atmosphere.ts`, `palette.ts`,
  `water.ts` (legacy v1 flat plane), `applyRealism.ts`.
- `web/lib/scene/decor/` - `sky.ts`, `fogTuning.ts`, `horizonRing.ts` (the stark-horizon ring).
- `web/lib/scene/atmosphere/transition.ts` - above/below surface transition.
- Sandbox: `web/app/(sandbox)/water/` (`WaterSandboxScene.tsx`) - the tuning surface; `uDebug`
  mode renders water-column thickness as grayscale.
- Convergence file (DO NOT edit in research): `web/app/components/scene/SalishScene.tsx`.

### Root cause (stated, not guessed)
1. **Surface read is ad-hoc, not physical.** Color is a two-stop lerp (cannot do real
   wavelength-dependent absorption); specular/glitter exponents are hand-picked and read as
   "distracting" hard sparkle; Fresnel reflects a single flat sky color, which is what makes the
   horizon stark.
2. **Sky/atmosphere is flat.** No procedural sky bound to the sun, no aerial perspective / fog,
   no tonemapping-aware exposure - hence "white sky," "stark horizon," "no sun light."
3. **Underwater is thin.** No volumetric scattering / depth-of-visibility, generic blue rather
   than the Salish Sea's turbid green; the per-channel absorption request is unadopted; the
   surface-from-below (Snell window) is not handled.

The 3D-TWIN family already plans this work as `W3` (world-materials-and-shading: sky-env,
terrain-material, seafloor-material, water-upgrade) and `W4` (underwater-and-exploration-modes)
in `.cca/catalogue/O0/20260627_terrain-bathymetry-twin/wave_shape.yml`. WFX is the **research
spine that those build waves consume**: it does not duplicate them, it grounds them with
measured, ranked, file-cited findings before any shader is rewritten.

## Locked decisions (do NOT reopen)

- **Research wave is read-only.** Wave 1 agents write ONLY their own
  `research/WFX-RNN_<topic>.md`. No edits to `web/`. No `next dev`/`next build` in the wave.
- **Built on `three`; a new dependency is a recommendation, not a default.** Any proposal to add
  a lib (e.g. an FFT-ocean or postprocessing pass) must state the bundle/perf cost and a
  three-only fallback. Hand-written shaders remain the house style.
- **Honesty label holds: "modeled, not measured."** Realism upgrades change how water looks;
  they assert no measured depth. The seabed read stays the modeled CUDEM topobathy.
- **Salish Sea is turbid and green, not tropical blue.** Color targets follow real regional
  optics (high CDOM/turbidity, Jerlov coastal water type), not a generic clear-ocean blue.
- **The per-channel RGB-absorption request already exists** (`WATER2_TUNING_REQUEST.md`); WFX-R09
  evaluates and extends it, it does not re-discover it.
- **Convergence-file collision lock.** Any later WFX build/integration that touches
  `SalishScene.tsx` or `globals.css` serializes via O0 against the twin lanes that also edit them
  (`W-CAM`, `W-LABELS`, `W3`, `W4`) and the LGC lane. Research touches none of these.
- **Frame budget is a first-class constraint:** 60fps desktop / 30fps laptop; the depth pre-pass
  already costs one full scene render, so every added pass (reflection, volumetrics, caustics)
  is costed against that budget in WFX-R13.

## Wave structure

### Wave 1 - WFX-RESEARCH (parallel, read-only, 13 agents)
Each owns ONE findings doc under
`.cca/catalogue/O0/20260628_water-fx/research/`. Every finding cites real files/paths and, where
it claims a perf cost, a measured or clearly-estimated number. One adversarial member.

Above-surface ocean + environment:
1. **WFX-R01 surface-BRDF** (`WFX-R01_surface_brdf.md`) - physically-based ocean surface: real
   Fresnel (Schlick at IOR 1.33), energy-conserving specular, sky-reflection vs the current
   ad-hoc `pow(ndh,90/600)` glitter; why the present specular reads as "distracting"; concrete
   replacement.
2. **WFX-R02 wave-spectrum** (`WFX-R02_wave_spectrum.md`) - replace the hand-tuned 6-Gerstner sum
   with an oceanographic spectrum (Pierson-Moskowitz / JONSWAP) or FFT (Tessendorf) feasible on
   `three`; choppiness; fetch/scale appropriate to the Salish Sea; vertex cost.
3. **WFX-R03 reflections** (`WFX-R03_reflections.md`) - planar reflection vs SSR vs env-cube for a
   real horizon/sky reflection; tradeoffs and the fix for the flat-sky-Fresnel stark look.
4. **WFX-R04 sky-atmosphere** (`WFX-R04_sky_atmosphere.md`) - procedural sky (Preetham/Hosek)
   bound to `makeSun`, aerial perspective / distance fog, horizon blend; fixes white sky + stark
   `horizonRing`; ground against `decor/sky.ts`, `realism/atmosphere.ts`, `horizonRing.ts`.
5. **WFX-R05 lighting-tonemap** (`WFX-R05_lighting_tonemap.md`) - sun disk, exposure, ACES
   tonemapping, PMREM environment from the sky; diagnose whether "white sky" is an
   exposure/tonemap problem; renderer settings.
6. **WFX-R06 shoreline-foam-wetness** (`WFX-R06_shoreline_foam.md`) - realistic foam at the
   waterline, wave run-up, wet-sand darkening; improve the current thin noise band without
   washing land.
7. **WFX-R07 caustics-godrays** (`WFX-R07_caustics_godrays.md`) - surface caustics projected on the
   seabed and volumetric light shafts (both top-down and underwater); cheap vs accurate options.

Underwater / bathymetric water:
8. **WFX-R08 underwater-volumetrics** (`WFX-R08_underwater_volumetrics.md`) - exponential depth
   fog, particulate in-scatter, visibility falloff; defines the `web/lib/scene/underwater/`
   module W4 will build; transition continuity with `atmosphere/transition.ts`.
9. **WFX-R09 rgb-absorption** (`WFX-R09_rgb_absorption.md`) - evaluate + extend the pending
   per-channel Beer-Lambert extinction (`WATER2_TUNING_REQUEST.md`); Jerlov water-type
   coefficients for the Salish Sea; backward-compat with `uDepthColorScale`.
10. **WFX-R10 seabed-interaction** (`WFX-R10_seabed_interaction.md`) - depth pre-pass quality,
    refraction of the modeled seabed through the surface, soft shoreline contact/edge; artifacts
    in the current `uInverseViewProjection` reconstruction.
11. **WFX-R11 salish-optics** (`WFX-R11_salish_optics.md`) - real optical properties of the Salish
    Sea (CDOM, turbidity, secchi depth, seasonal phytoplankton green); truthful color targets +
    citations; feeds R09 coefficients honestly.
12. **WFX-R12 surface-from-below** (`WFX-R12_surface_from_below.md`) - the underside of the water
    surface when diving: Snell's window, total internal reflection, ripple-from-below; current
    underside handling and the dive transition.

Cross-cutting:
13. **WFX-R13 perf-adversarial** (`WFX-R13_perf_adversarial.md`) - frame-budget accounting for the
    full stack (depth pre-pass + reflection + volumetrics + caustics + sky), KTX2/precision, and
    an **adversarial** hunt for what currently reads "distracting"/unreal and for the white-sky /
    stark-horizon regression; ranks the levers by realism-gain-per-ms; flags every SalishScene.tsx
    / globals.css collision with W3/W4/W-CAM/W-LABELS/LGC.

Plus a **synthesis** doc `research/SYNTHESIS_water_fx.md` (the sub-orchestrator writes it):
the ranked, sequenced build plan the twin's W3/W4 (or a new WFX-BUILD wave) consumes.

### Wave 2 - WFX-BUILD (parallel, NEW files; GATED on O0)
Net-new shader/material modules under `web/lib/scene/...` + per-module WIRING docs, tuned in the
`/water` and `/world` sandboxes. `tsc` clean. No SalishScene edits. Maps onto the twin's W3
agents where they overlap (avoid duplicate ownership; coordinate via O0).

### Wave 3 - WFX-INTEGRATE (single serialized editor; GATED on O0)
Lands the chosen stack in `SalishScene.tsx`. Serializes against W-CAM/W-LABELS/W3/W4/LGC.

### Wave 4 - WFX-ACCEPT (GATED on O0)
Read-examined before/after frames at: open-water surface, shoreline, dive/underwater, horizon at
sunrise/noon/sunset. Verdict: water reads physical (not distracting), sky/horizon soft with sun
and fog, underwater is turbid-green Salish optics, all within frame budget. Honest, evidence-cited.

## Acceptance criteria (hard, checkable)
- Wave 1: 13 findings docs + synthesis, each citing real files; perf claims carry numbers; a
  ranked, sequenced plan exists; no code changed.
- Build/accept (later, gated): before/after frames Read-examined; frame-time A/B within budget;
  no white-sky / stark-horizon regression; honesty label intact.

## Escalation (operator-protection catch)
The dispatched sub-orchestrator answers to **O0, not the human operator**. On any decision,
trade-off, new-dependency choice, locked-decision conflict, regression, or a gated/destructive/
scope-expanding step, **pause and return the question to O0** in the summary. Gated waves (2-4)
require O0 approval. No commit/push inside the waves; commit is an operator gate.
