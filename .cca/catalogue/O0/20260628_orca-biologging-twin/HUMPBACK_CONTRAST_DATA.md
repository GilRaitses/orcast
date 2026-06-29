# Humpback contrast dataset (located 2026-06-28)

The operator's real humpback DTAG export, for the orca-vs-humpback motion contrast and as a
real animaltags-style H5 to validate the OG-PREBAKE baker. Read-only; do not copy the 54M H5
into orcast. Reference it by absolute path.

## Location (external repo, not orcast)
- H5 (consolidated): `/Users/gilraitses/whale-behavior-analysis/Visualization_Poster_Appendix/data/dive_analysis.h5` (54M, tracked in that repo)
- Raw sensor CSV: `.../data/mn09_203a.csv` (21M, ~99,925 rows @ 5 Hz)
- Event log: `.../data/log_mn09_203a.csv`
- Flat schema: `/Users/gilraitses/whale-behavior-analysis/dive_analysis_schema_flat.json`
- Provenance/lineage: `/Users/gilraitses/whale-behavior-analysis/DATA_BINDING_MANIFEST.md`

## Animal
- ID `mn09_203a`, name "lavaliers_Calf". `mn` = Megaptera novaeangliae (**humpback**). 5 Hz tag.
- 128 detected dives over ~5.5 h. Behaviors annotated: Exploratory_dives, Feeding_loop,
  Kick_feeding, Noodle_feeding, Side_rolls, Side_rolls_and_loop, Surface_Active, Traveling,
  Vertical_loop.

## H5 paths that map onto the OG-R rig contract
| OG-R channel -> rig DOF | H5 path |
|---|---|
| depth (m, +down) -> world Y | `/depth/values` (+ `/eti/values` time index) |
| pitch -> body_pitch | `/data/pitch` (radians) |
| roll -> body_roll | `/data/roll` (radians) |
| heading -> body_yaw | `/data/head` (radians) |
| accel (whale frame) -> fluke beat (Az band) | `/data/Aw.1`, `/data/Aw.2`, `/data/Aw.3` |
| dive segmentation | `/dives/dive_indices` (3xN: start, max_depth, end) |
| per-dive metrics (contrast stats) | `/dives/metrics/{odba,vdba,descent_rate,descent_duration,bottom_duration,ascent_rate,ascent_duration}` |
| activity | `/analysis/animal_frame_metrics/{odba,vdba,jerk_magnitude}` |

This layout is per-sample and standard animaltags - directly bakeable by OG-PREBAKE's `prebake.py`.

## Use (two roles, both honest)
1. **Contrast baseline (OG-DATA):** compute the REAL humpback dive/movement distribution from this
   H5 (max-depth histogram, descent/ascent rate, fluke-beat Hz from the Az band, dive-bout
   structure, behavior mix) and put it in `OG-DATA_orca_vs_humpback.md` as the humpback column of
   the species parameter table. The orca column comes from open orca data (OG-DATA search).
2. **Real-H5 baker validation (OG-PREBAKE):** point `prebake.py` at this H5 as a real test input
   to prove the bin/JSON pipeline works on real per-sample data. Output is labeled **humpback
   (contrast)**, NOT the orca driver source - the orca twin must not be driven by humpback motion.

## Honesty
Humpback data is real and the operator's own. The orca motion is parameterized from open orca
data contrasted against this humpback baseline; never present humpback kinematics as orca.
