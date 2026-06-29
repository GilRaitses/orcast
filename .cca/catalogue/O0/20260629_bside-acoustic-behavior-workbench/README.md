# B-side acoustic + behavior research workbench (BSW)

The behavior-analysis "B-side" of orcast: a hydrophone station player + scrubbable spectrogram HUD
+ community-annotation-trained acoustic classifier + DTAG-driven orca reenactment in the 3D twin,
plus an annotation + tagtools pipeline studio the orchestrated console can invoke. Acoustic (who/
what is out there) and kinematic (how it moves) joined in a scrub-synced replay, viewable from the
hydrophone POV or top-down. No standins: the demo slice is real audio -> real spectrogram -> real
classifier output -> reenactment from real DTAG kinematics.

Files:
- `PROGRAM.md` - umbrella authority: intent, grounding (verified paths), locked decisions, the five charters.
- `wave_shape.yml` - machine-readable shape: the ~14-agent read-only research wave (BSW-R01..R14) + the five charters' phased waves.
- `ORCHESTRATOR_DISPATCH_PROMPT.md` - paste block for the background sub-orchestrator.
- `BSW-STATION_CHARTER.md` - hydrophone model + station player + camera POV-selection object (BST).
- `BSW-ACOUSTIC-ML_CHARTER.md` - community-annotation MLops + first real acoustic classifier (BAM).
- `BSW-SPECTRO-HUD_CHARTER.md` - WebAudio spectrogram HUD + interpretive ocean-process layer (BSH).
- `BSW-REENACTMENT_CHARTER.md` - scrub-synced multi-orca reenactment + camera POV (BRE).
- `BSW-STUDIO-SKILLS_CHARTER.md` - annotation UI + tagtools pipeline studio + managed HUD skills (BSS).
- `research/` - the ~14 findings docs + `SYNTHESIS_bside.md` (created by the wave).
- `SIGN_OFF.md` - O0/operator ratification of the real demo-slice spec (created at slice-def time).

How to start: dispatch the sub-orchestrator with `ORCHESTRATOR_DISPATCH_PROMPT.md`. It runs the
~14-agent read-only research wave, writes `research/SYNTHESIS_bside.md`, and returns to O0. The real
demo slice and the five breadth charters are O0-gated.

Serializes against LGC / CVP / ORCA / WFX / 3D-TWIN on `SalishScene.tsx`, `globals.css`,
`AdaptiveExplore.tsx`, `ActiveSurfaceHost.tsx`. Research is read-only; no code changes, no commits
(operator gate).

Status: chartered 2026-06-29; research wave dispatch pending.
