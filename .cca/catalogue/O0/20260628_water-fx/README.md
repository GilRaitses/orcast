# WATER-FX lane (WFX)

Water + atmosphere shading realism for the Salish Sea 3D twin - both the above-surface ocean
(surface BRDF, waves, reflections, sky/sun/fog) and the underwater / bathymetric water
(volumetrics, per-channel absorption, the modeled-seabed read). Started because the current
shading reads distracting and unreal: white sky, stark horizon, hard glitter, generic blue.

Files:
- `WAVESET_CHARTER.md` - authority doc, grounding, root cause, locked decisions, wave structure.
- `wave_shape.yml` - machine-readable shape; the 13 research agents (WFX-R01..R13) + gated build/integrate/accept.
- `ORCHESTRATOR_DISPATCH_PROMPT.md` - the paste block for the background sub-orchestrator.
- `research/` - the 13 findings docs + `SYNTHESIS_water_fx.md` (created by the wave).

How to start: dispatch the sub-orchestrator with `ORCHESTRATOR_DISPATCH_PROMPT.md`. It runs the
13-agent read-only research wave, writes the synthesis, and returns to O0. Build/integrate/accept
are O0-gated.

Feeds the 3D-TWIN family's `W3` (world-materials-and-shading) and `W4` (underwater) in
`.cca/catalogue/O0/20260627_terrain-bathymetry-twin/`. Research is read-only; no code changes,
no commits (operator gate).

Status: chartered + research wave dispatched 2026-06-28.
