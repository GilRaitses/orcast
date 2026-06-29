# BSS studio managed HUD skills

This document describes the net-new Central Casting skills added by the BSS lane.
They extend the existing skill catalog. Tiers and honesty labels are preserved.
All three are tier T1 and public.

## Skills

| id | tier | truth label | what it serves |
|---|---|---|---|
| `run_tagtools_step` | T1 | derived | one tagtools pipeline step summary with provenance |
| `render_poster_viz` | T1 | baked | a baked poster visualization descriptor with a box pointer |
| `capture_behavior` | T1 | measured_behavior_modeled_camera | a director capture spec for a real classified DTAG behavior |

## Honesty

`run_tagtools_step` serves a re-implemented tagtools stage computed offline from
the real humpback DTAG mn09_203a. The orientation stage reproduces the provided
pitch and roll channels to floating point precision. Dive and stroke counts
differ from the reference and each step reports that difference rather than
hiding it.

`render_poster_viz` never invokes an R or plotly runtime. The poster figures are
baked offline by the existing R scripts and stored in the box. The skill returns
a descriptor and a box key, labeled baked. The interactive 3D dive lattice has a
deferred JavaScript port marked `deferred-posture-3-react-three-fiber`.

`capture_behavior` pulls a real classified behavior from a real DTAG dive window
and turns it into a block, camera test, and screen test spec on the
demo-production director. The behavior and dive geometry are measured. The animal
mesh and the camera move are modeled. The humpback example is contrast and
reference only and never drives an orca.

## Dependency posture

These skills follow O0 gate 2 posture 2. No R runtime, no animaltags runtime, no
plotly.js. Raw recompute and poster render are baked offline and boxed. The
managed skills serve the baked artifacts with honesty labels.

## License

The source DTAG data is CC-BY-NC, non-commercial, authorized by O0 SIGN_OFF
decision 1. Attribution is humpback DTAG mn09_203a, whale-behavior-analysis
dataset. Every derived artifact carries the CC-BY-NC label and attribution. Use
stays non-commercial. See `dispatch/BSS/ADVERSARIAL.md`.

## Wiring

The skills register in `src/aws_backend/casting/skills_manifest.json` and the
dispatch table in `src/aws_backend/casting/skills.py`. They are registered with
`enabled` false so the public catalog count is unchanged at build time. The
BSS-INTEGRATE step enables them, allowlists their console panels, and is O0
gated. Build-time proof runs the handlers directly with
`python3 -m src.aws_backend.casting.studio_skills`. See `dispatch/BSS/WIRING.md`.
