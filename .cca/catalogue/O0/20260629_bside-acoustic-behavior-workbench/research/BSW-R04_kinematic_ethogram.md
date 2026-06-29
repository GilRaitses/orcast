# BSW-R04 - Kinematic ethogram & behavior->motion mapping

> Read-only research finding (BSW-RESEARCH wave). Repo verified against `240570e`.
> Authored by explore agent 671e2766; written by the BSW sub-orchestrator.

## Summary

- **Orca twin motion is locked to the real SRKW DTAG driver** `web/public/orca/motion/orca_srkw_oo14_driver.{json,bin}` with `simulated: false`, `role: "driver"`, loaded by `loadBiologging()` and applied via `driveOrca()` each frame.
- **Humpback `dive_analysis.h5` is contrast/reference only**: 99,925 samples @ 5 Hz, 128 dives, 51 manual annotation rows, 9-class taxonomy, tagtools stroke/glide, ODBA/VDBA/jerk. It must never drive an orca. Contrast manifest at `web/public/orca/motion/humpback_mn09_203a_contrast.json` (`.bin` box-bound).
- **No shipped automated kinematic classifier in orcast.** The humpback minGRU is documented in the external repo (~66.8% claimed val accuracy in `training_summary.md`) but not wired. The orcast bundled DTAG fixture `data/dtag_analysis_results.json` is treated as `simulated: true` by `dtag.py`.
- **Ethogram basis**: 9 named classes from `behavior_mapping.json`, grounded in 50 expert-labeled frame windows in `log_mn09_203a.csv` (humpback calf `mn09_203a`), plus derived kinematic products in h5.
- **Proposed motion-clip contract** (greenfield, `web/lib/scene/orca/motion/clips/` does not exist yet): a clip is a **time window `[t0_s, t1_s]` into the SRKW driver bin**, sampled through the existing 7-channel `track.sample(t)`. Behavior class selects the window via kinematic matching on SRKW data, not by loading humpback motion.
- **Several humpback-specific feeding/display behaviors (Kick feeding, Noodle feeding, bubble-net variants) cannot be honestly reenacted on the orca** without SRKW-labeled segments. Cross-species label transfer is modeled/interpretive and must not be presented as measured orca behavior.

## Real SRKW driver format (orca, the one that drives motion) - cited

**Manifest**: `web/public/orca/motion/orca_srkw_oo14_driver.json`

| Field | Verified value |
|-------|----------------|
| `simulated` | **`false`** |
| `role` | `"driver"` |
| `species` / `ecotype` | `"orca"` / `"SRKW"` |
| `deployment` | `"oo14_264m"` |
| `license` / DOI | CC-BY-4.0 / `10.5281/zenodo.13308835` |
| `sample_rate_hz` | **5** |
| `n_samples` | **40,937** |
| `duration_s` | **8,187.4** (~136.5 min) |
| `n_channels` | **7** |
| `bin_file` | `orca_srkw_oo14_driver.bin` (1,146,236 bytes) |
| `layout` | interleaved sample-major float32 LE, shape `(n_samples, n_channels)` |

**Channel order** (locked in `biologging.ts` + manifest):

| Index | Name | Unit | Rig DOF |
|------:|------|------|---------|
| 0 | `t_s` | s | - |
| 1 | `body_yaw_rad` | rad | `setOrientation` yaw |
| 2 | `body_pitch_rad` | rad | `setOrientation` pitch |
| 3 | `body_roll_rad` | rad | `setOrientation` roll (full +/-pi; foraging rolls present) |
| 4 | `depth_m` | m, positive-down | `setDepthPose` |
| 5 | `fluke_phase_rad` | rad [0, 2pi) | `setFluke` phase |
| 6 | `fluke_amplitude` | 0..1 | `setFluke` amplitude |

**Stroke band** `[0.15, 0.6]` Hz; measured active-window median fluke rate **0.1833 Hz**. **Depth range** measured -2.543 to 155.125 m. Pitch |p95| 61.61 deg, roll |p95| 133.25 deg.

**Runtime path** (`OrcaController.ts`): `track.sample(elapsed*timeScale)` -> `driveOrca(rig, pose, wupm*depthScale)` (authoritative root orientation/depth/fluke) -> `physics.step` (bounded secondary flex) -> `mouth.setForagingContext` (modeled cue) -> `eyes.update`.

**Not the orca driver:** `orca_dev_track.json` (`simulated:true`); `humpback_mn09_203a_contrast.json` (`role:"contrast"`).

**Bake provenance:** `infra/orca/biologging/dev/bake_orca_srkw_driver.py` from `oo14_264mprh50.mat` (native 50 Hz PRH). SRKW `.mat` also carries `diveindices`/`TT` + `foraging_data.csv` (`kindet` prey-capture flags) per `PROVENANCE.md`, but **no 9-class ethogram is baked into the web driver**.

## Humpback h5 schema + derived products (contrast/reference ONLY) - cited dataset names

**File**: `/Users/gilraitses/whale-behavior-analysis/Visualization_Poster_Appendix/data/dive_analysis.h5`
**Schema**: `dive_analysis_schema_flat.json` (**121 dataset properties**). 99,925 samples @ 5 Hz.

### Raw / core sensor (measured)
`/depth/values` (`depth_values`), `/eti/values` (`eti_values`), `/data/pitch`, `/data/roll`, `/data/head`, `/data/Aw.1..3` (animal-frame accel; Az/heave for fluke). Paths from `Visualization_Poster_Appendix/scripts/data_config.yaml`.

### Dive detection & phases (derived, rule-based)
`/dives/dive_indices` (`dives_dive_indices`, **(128, 3)** start/max_depth/end); `/dives/metrics/*` (per-dive scalars: odba, vdba, max_depth, descent_rate, bottom_duration, ascent_rate, duration); `/dives/advanced_metrics/*`; `/dives/segments/dive_XXX`.

### Animal-frame kinematic metrics (derived, length 99925)
`/analysis/animal_frame_metrics/{odba,vdba,jerk_magnitude,jerk/x,y,z,acceleration_magnitude}`; `/analysis/derived_metrics/{depth,vertical_acceleration}`.

### Tagtools stroke/glide products (derived)
`/analysis/tagtools/behaviors/glides` **(670, 2)**; `/analysis/tagtools/behaviors/strokes/peaks` (2405,); `/.../troughs` (2439,); `/analysis/tagtools/animal_frame/acc_*`; `/analysis/tagtools/processed_data/calculated_{pitch,roll,heading}`. Humpback contrast bake cites fluke beat **0.2273 Hz** from stroke-peak median interval.

### Annotations & behavior validation (measured labels, humpback only)
`log_mn09_203a.csv` - **51 rows** (50 labeled events + 1 End); cols `eventStart`, `eventEnd`, `state`, `event`. `behavior_mapping.json` numeric ID -> class. `/analysis/validation/behaviors/types/*` boolean masks for 5 annotated names (Bubble feeding, Feeding loop, Kick feeding, Lunge in bubble net feeding?, Noodle feeding) - **not all 9 taxonomy classes have validation datasets in the flat schema**.

## Behavior taxonomy (the 9-class ethogram) and its data basis

**Registry**: `/Users/gilraitses/whale-behavior-analysis/behavior_mapping.json`

| ID | Class name | In `log_mn09_203a.csv` |
|----|------------|------------------------|
| 1 | `Exploratory_dives` | Yes (many) |
| 2 | `Feeding_loop` | Yes |
| 3 | `Kick_feeding` | Yes |
| 4 | `Noodle_feeding` | Yes |
| 5 | `Side_rolls` | Yes |
| 6 | `Side_rolls_and_loop` | Yes |
| 7 | `Surface_Active` | Yes |
| 8 | `Traveling` | Yes (1 window) |
| 9 | `Vertical_loop` | Yes |

**Data basis (layered):** (1) measured expert ethogram (frame-indexed intervals in csv, 5 Hz aligned); (2) derived kinematic context per interval (slice h5 arrays for depth/pitch/roll/head, ODBA/VDBA/jerk, stroke/glide overlap, dive phase); (3) automated classifier (NOT shipped - minGRU 66.8% claimed val accuracy, severe imbalance e.g. Class 9: 6 windows; orcast `dtag.py` returns `model_state: "not_trained"`); (4) SRKW open data has dive tables + `foraging_data.csv` `kindet` flags but **no 9-class manual ethogram**.

orcast API taxonomy: `TAXONOMY_VERSION = "unratified-0"` in `src/aws_backend/routers/dtag.py`; fixture uses rule-based dive types (`deep_travel`, `deep_exploration`), not the humpback 9-class set.

## Proposed behavior -> motion-clip mapping for the orca rig (parameters per class)

### Rig DOF inventory
**Authoritative (7-channel driver):** body yaw/pitch/roll -> root rotation; depth_m -> `Y=-depth_m*worldUnitsPerMeter`; fluke phase/amp -> caudal beat. **Layered (modeled, bounded):** OPHYS spineYaw/bankRoll/caudalFollow from yaw rate + fluke phase velocity; OMOU jaw open 8-15 deg when depth>5 m + elevated flukeAmp (foraging **cue**, not eating); OEYE gaze (near LOD). **Not in DTAG driver:** pectoral, head offset (any use = modeled).

### Motion-clip contract (proposed for BRE)
```typescript
// web/lib/scene/orca/motion/clips/ (greenfield)
interface BehaviorMotionClip {
  driverUrl: "/orca/motion/orca_srkw_oo14_driver.json";  // always SRKW
  t0_s: number;
  t1_s: number;
  behaviorClass: BehaviorClassId;  // 1..9 from ethogram
  loop: boolean;
  honesty: "measured" | "modeled";
  selection: "srkw_native_segment" | "srkw_kinematic_match" | "continuous_fallback";
}
```
Playback `pose = track.sample((t - t0_s) % (t1_s - t0_s) + t0_s)` - still real SRKW samples, no synthetic swim.

### Per-class signature -> SRKW clip selection -> rig parameters

| Class | Kinematic signature (h5 + annotations) | SRKW clip selection rule | Primary channels (measured) | Secondary (modeled) |
|-------|----------------------------------------|--------------------------|-----------------------------|---------------------|
| 1 Exploratory_dives | Moderate depth excursions; mixed phases; mid ODBA | SRKW `diveindices` segments, moderate max_depth, non-extreme roll | all 7 ch; fluke_amp ~0.4-0.8 | standard OPHYS; OMOU cue if depth>5 |
| 2 Feeding_loop | Closed heading path + sustained depth | high heading curvature integrated ~2pi | yaw/pitch/depth/fluke | OPHYS bank elevated |
| 3 Kick_feeding | Short bursts, high jerk/ODBA spikes | **FAKE RISK** humpback-specific; only if SRKW matched by jerk peaks + shallow depth | fluke_amp high, pitch volatile | OMOU modeled cue |
| 4 Noodle_feeding | Slow surface skimming | **FAKE RISK** on orca | shallow depth<5, low-mid fluke | depth/yaw if shallow SRKW interval |
| 5 Side_rolls | \|roll\| elevated (>60 deg) | SRKW roll p95 133 deg supports; \|roll\|>1.0 rad sustained | roll, pitch, fluke | OPHYS bank |
| 6 Side_rolls_and_loop | high roll + heading loop | roll threshold + heading curvature | roll + yaw + depth | OPHYS spine/bank |
| 7 Surface_Active | shallow, high twistiness/ODBA | depth<3 m + elevated fluke_amp | depth, fluke high | OMOU cue; no pectoral slap |
| 8 Traveling | stable heading, steady stroking | low heading variance + active fluke (~0.18 Hz) | yaw stable, fluke continuous | default OPHYS |
| 9 Vertical_loop | pitch/depth oscillation loop | monotonic depth cycle + pitch sign changes | pitch, depth, fluke | OPHYS spine flex |

**Clip index construction (offline):** run tagtools-equivalent stroke/glide + dive segmentation on **SRKW `.mat`**; compute per-class kinematic fingerprint vectors from humpback labeled windows; score SRKW candidate windows vs fingerprint; accept above threshold; store in `clips/manifest.json` with `honesty: "measured"` if SRKW-native else `"modeled"`. Hold constant (do not behavior-map): worldUnitsPerMeter, depthScale, timeScale, OPHYS spring coeffs; fluke rate always from data phase derivative.

## Measured vs modeled labeling

| Layer | Label |
|-------|-------|
| SRKW 7-channel samples | **measured** |
| Humpback h5 sensor rows | **measured** (contrast only) |
| Humpback 9-class interval labels | **measured** (humpback ethogram) |
| Applying humpback class name to orca | **modeled / interpretive** (disclose cross-species) |
| Orca mesh/skinning/materials | **modeled** |
| OPHYS spine/bank/caudal lag | **modeled** |
| OMOU jaw foraging cue | **modeled** (not feeding) |
| OEYE gaze, pectoral/head-offset | **modeled** |
| `orca_dev_track` / `dtag_analysis_results.json` | **simulated** |
| minGRU / RF feeding classifier | **not_trained** in orcast API |
| SRKW window matched to humpback fingerprint | **measured motion, modeled classification** (split label) |

## Recommendations with cost + standin-free fallback

1. **Ship v1 clips as SRKW time windows only** - offline fingerprint match -> `clips/manifest.json`. Runtime cost: one extra float offset in `track.sample()` (negligible).
2. **Compute stroke/glide on SRKW `.mat` once** (reuse `prebake.py` primitives; ~minutes offline). Enables honest glide behavior (fluke_amp -> 0).
3. **Near-term classifier: rule-based kinematic scorer**, not minGRU - features already in pipeline. No GPU training gate.
4. **Restrict demo slice to classes with SRKW matches** - prioritize **Side_rolls (5)**, **Traveling (8)**, **Exploratory_dives (1)**. Defer Kick/Noodle feeding (3,4) until SRKW labels exist.
5. **Bake SRKW sub-clips to box (S3)** if scrub sync needs many windows; manifest in git (~KB).
6. **Honesty UI string per clip:** e.g. "motion: measured SRKW DTAG (oo14_264m); behavior label: modeled match to humpback ethogram class Side_rolls".

**Standin-free fallback:** no classifier -> play continuous SRKW driver, classify only depth phase from SRKW `diveindices`; no clip match -> continuous driver at current scrub time, HUD `behavior: unclassified`; no SRKW feeding segments -> do not depict Kick/Noodle feeding; humpback bin unavailable -> schema + JSON stats only, never load humpback as driver; ML not ready -> expert/rule labels + measured SRKW windows, never `orca_dev_track` in demo.

## Open questions for O0

1. **Ratify taxonomy**: adopt humpback 9-class as `taxonomy_version: "mn09-ethogram-v1"` for kinematic track, or define a reduced SRKW-native ethogram (dive + foraging + roll only)?
2. **Cross-species honesty**: is "measured SRKW motion + modeled humpback-derived behavior label" acceptable on the HUD, or must labels be SRKW-native only?
3. **Demo behavior subset**: which 1-2 classes must the first BRE slice reenact? (Rec: Traveling + Side_rolls.)
4. **SRKW annotation investment**: partnership path to label `oo14_264m` intervals (or use `foraging_data.csv` `kindet` as a binary foraging class only)?
5. **Clip storage**: runtime window into monolithic SRKW bin vs pre-cut sub-bins per class (box vs git)?
6. **Classifier path**: rule-based kinematic v1 vs retrain/export minGRU weights?
7. **Manifest rate discrepancy**: deployed JSON lists `sample_rate_hz: 5` while `driver_stats.out_rate_hz: 25` - confirm canonical playback rate for scrub sync.
8. **`motion/clips/` API**: single active clip vs playlist synced to BSH playhead segments?

## Sources

**Orcast (motion + rig):** `web/lib/scene/orca/motion/biologging.ts`, `web/lib/scene/orca/OrcaController.ts`, `web/lib/scene/orca/rig/OrcaRig.ts`, `web/lib/scene/orca/physics/secondaryDynamics.ts`, `web/lib/scene/orca/mouth/orcaMouth.ts`, `web/public/orca/motion/orca_srkw_oo14_driver.{json,bin}`, `orca_dev_track.json`, `humpback_mn09_203a_contrast.json`, `infra/orca/biologging/dev/bake_orca_srkw_driver.py`, `infra/orca/biologging/prebake.py`, `infra/orca/biologging/OG-R_h5_mapping.md`, `infra/orca/biologging/data/tennessen2024_srkw_dtag/PROVENANCE.md`, `src/aws_backend/routers/dtag.py`, `data/dtag_analysis_results.json`

**Whale-behavior (contrast ethogram + h5):** `dive_analysis_schema_flat.json`, `DATA_BINDING_MANIFEST.md`, `behavior_mapping.json`, `Visualization_Poster_Appendix/data/log_mn09_203a.csv`, `Visualization_Poster_Appendix/scripts/data_config.yaml`, `Visualization_Poster_Appendix/data/dive_analysis.h5` (schema only), `presentation/training_summary.md`

**BSW program:** `PROGRAM.md`, `BSW-REENACTMENT_CHARTER.md`, `wave_shape.yml`
