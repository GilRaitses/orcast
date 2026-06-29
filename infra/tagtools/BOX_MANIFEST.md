# Box manifest — tagtools studio

Heavy artifacts are written to the box (S3), never committed to git. This file
is the re-fetch pointer and provenance record (PROGRAM locked decision: heavy h5
derivatives and corpora go to the box).

## Source asset (input, CC-BY-NC)

License CC-BY-NC, non-commercial, authorized by O0 SIGN_OFF decision 1.
Attribution: humpback DTAG mn09_203a, whale-behavior-analysis dataset.

| item | location | size | license |
|---|---|---|---|
| Raw DTAG sensor CSV `mn09_203a.csv` | `~/whale-behavior-analysis/Visualization_Poster_Appendix/data/` | ~99,925 rows | CC-BY-NC |
| Expert annotation log `log_mn09_203a.csv` | same dir | 50 events | CC-BY-NC |
| Full `dive_analysis.h5` | not present locally; box | large | CC-BY-NC |

Re-fetch: set `BSS_DTAG_SOURCE_ROOT` to the data root before running the bake.

## Baked heavy outputs (gitignored: `infra/tagtools/out/box/`)

| file | contents | shape |
|---|---|---|
| `tagtools_calibration.npz` | accel magnitude per sample | 99,925 |
| `tagtools_orientation.npz` | recomputed pitch/roll per sample | 99,925 each |
| `tagtools_odba.npz` | ODBA per sample | 99,925 |
| `tagtools_dive_detection.npz` | dive_indices, max_depths, durations | (215,3)/215/215 |
| `tagtools_stroke_glide.npz` | stroke peaks/troughs, glide spans | varies |

Proposed box key prefix: `s3://<orcast-box-bucket>/bss/tagtools/mn09_203a/<bake_date>/`.

## Committed-shape derivative (small, real)

`web/lib/annotation/fixtures/dtag_mn09_203a.json` (~110 KB): metadata, the
9-class behavior taxonomy, the 50 expert annotations (whaleName dropped, no
human PII), per-step summaries, per-dive summary, and downsampled depth + ODBA
profiles (2000 points each). This is the only derived product the web studio
reads. License CC-BY-NC, non-commercial. Nothing is committed in this step
because commit remains a separate operator gate.

## Poster viz (B3 / posture 2)

Poster R/ggplot2 PNGs and the Plotly 3D dive-lattice HTML are baked OFFLINE by
the existing R scripts in `whale-behavior-analysis/Visualization_Poster_Appendix/`
and stored in the box. The managed HUD skills serve the baked artifacts with
honesty labels. No R runtime ships. The interactive 3D dive-lattice JS port
(react-three-fiber) is posture 3, DEFERRED (see studio WIRING note).
