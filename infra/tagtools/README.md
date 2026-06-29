# tagtools studio (BSS lane)

A reusable, offline biologging processing pipeline that re-implements
tagtools/animaltags-style DTAG stages in pure Python and numpy. It is the
reusable processing surface the orchestrated console can invoke, not a one-off
script.

## Dependency posture (O0 gate 2, posture 2)

No R runtime, no `animaltags`, no `plotly.js`. The stages here are documented
re-implementations that consume already-derived h5/CSV products and reproduce
tagtools-style outputs. Any raw recompute is baked offline and the heavy output
goes to the box, never git.

## Stages

| step_id | reproduces (h5) | output |
|---|---|---|
| `tagtools.calibration` | `data/Aw.{1,2,3}` | static accel magnitude (~1.0 g) |
| `tagtools.orientation` | `analysis/orientation_comparison/{pitch,roll}` | pitch/roll vs provided channels |
| `tagtools.odba` | `analysis/animal_frame_metrics/odba` | Overall Dynamic Body Acceleration |
| `tagtools.dive_detection` | `dives/dive_indices` | dive (start, max, end) indices |
| `tagtools.stroke_glide` | `analysis/tagtools/behaviors/{strokes,glides}` | stroke peaks/troughs, glides |

The orientation stage reproduces the provided pitch/roll channels to
floating-point precision (mean abs diff ~3e-10 rad), validating the
re-implementation. Dive and stroke/glide counts differ from the reference
because parameters are reported, not tuned to match. Those differences are
recorded honestly in each step summary.

## Source data

Humpback DTAG `mn09_203a` from the operator's `whale-behavior-analysis` repo.
Contrast/reference only; it never drives an orca. Set `BSS_DTAG_SOURCE_ROOT` to
point at the data root (defaults to `~/whale-behavior-analysis`). The DTAG data
is CC-BY-NC, non-commercial, authorized by O0 SIGN_OFF decision 1. Attribution:
humpback DTAG mn09_203a, whale-behavior-analysis dataset. See
`dispatch/BSS/ADVERSARIAL.md`.

## Run

```bash
python3 infra/tagtools/run_sandbox.py            # run + assert all stages
python3 infra/tagtools/run_sandbox.py tagtools.odba
python3 infra/tagtools/bake.py                   # write web fixture + box arrays
```

`bake.py` writes the small, real, derived summary fixture the annotation studio
reads at `web/lib/annotation/fixtures/dtag_mn09_203a.json`, and heavy per-sample
arrays to `infra/tagtools/out/box/` (gitignored). See `BOX_MANIFEST.md`.
