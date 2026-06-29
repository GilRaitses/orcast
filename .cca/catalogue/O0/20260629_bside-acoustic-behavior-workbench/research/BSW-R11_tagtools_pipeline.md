# BSW-R11 - tagtools / animaltags pipeline as console skills

> Read-only research finding (BSW-RESEARCH wave). Repo verified against `240570e`.
> Authored by explore agent 4c1ab2; written by the BSW sub-orchestrator.

## Summary

- **The baked h5 already contains most pipeline outputs.** `dive_analysis.h5` carries calibrated orientation (pitch/roll/heading), depth, ETI, dive detection (128 dives x 3 indices), per-dive ODBA + max depth + duration, and norm-jerk inputs. The default runtime for the studio should be **read the baked products**, not recompute.
- **Recompute primitives already exist in Python** in the operator's analysis repo (`prebake.py`-style derivations) and orcast precedent (`infra/orca/biologging/prebake.py`). For demo, expose **read + light recompute (norm-jerk, ODBA from accel slices)** as skills without an R runtime.
- **R `tagtools` is a costed upgrade, not the default.** `tagtools` (animaltags.org) is **GPL (>= 3)** - copyleft. Wrapping it in a hosted service is fine for internal/offline batch but it must stay a separate process (box/offline), never linked into the web bundle, and the GPL obligation recorded. `animaltags` Python port is also GPL-3.
- **Skill descriptors** map each canonical tagtools stage (calibrate -> orient -> dive-detect -> stroke/glide -> ODBA/VDBA/jerk) to a Central Casting T2 keyed skill that returns an artifact + provenance. Heavy outputs -> box/S3.
- **Standin-free fallback:** if recompute is out of scope, serve the baked h5 stage outputs (real, measured-derived) with the pipeline-stage label and a "precomputed offline" provenance note. Never fabricate a stage result.

## tagtools pipeline stages (canonical) mapped to data + runtime

`tagtools`/`animaltags` standard high-resolution tag workflow stages, mapped to what `dive_analysis.h5` already provides:

| Stage | tagtools fn (R) | h5 baked output | Runtime decision |
|-------|-----------------|-----------------|------------------|
| Load + decimate | `load_nc`, `decdc` | raw + 5 Hz resampled (`/analysis/metadata/sample_rate=5`) | **Read baked** |
| Calibration (acc/mag/press) | `crop`, `do_cal`, `spherical_cal` | calibrated `/data/{accel,mag,depth}` | **Read baked** (cal already applied) |
| Orientation (Euler) | `prh_predictor`, `m2h`, `a2pr` | `/data/{pitch,roll,head}` | **Read baked**; recompute optional from accel/mag |
| Dive detection | `find_dives` | `/dives/dive_indices` [128,3], `/dives/metrics/*` | **Read baked**; recompute via depth threshold primitive |
| Stroke / glide | `dsf`, `fln`, `njerk` | norm-jerk derivable (`calculate_normjerk()`); fluke rate not pre-baked | **Light recompute (Python)** or read if baked |
| ODBA / VDBA / jerk | `odba`, `njerk` | `/analysis/animal_frame_metrics/odba`, per-dive ODBA | **Read baked**; VDBA recompute from accel |
| Energetics summary | (derived) | `/dives/metrics/{odba,max_depth,duration}` | **Read baked** |

**Verdict:** default = read baked (measured-derived). Offer Python recompute for norm-jerk, ODBA window, VDBA, dive-threshold so a reviewer can re-derive and compare to baked (honesty check). R `tagtools` only for stages not reproducible in Python and only as offline batch.

## Runtime decision: R tagtools vs Python animaltags vs prebake primitives

| Option | License | Cost | Where it runs | Verdict |
|--------|---------|------|---------------|---------|
| **Read baked h5** | operator data license (verify) | ~0 | backend slice API | **Default** |
| **Python primitives** (`prebake.py` + numpy norm-jerk/ODBA) | repo MIT-ish + numpy BSD | low; no new heavy dep | backend/Lambda | **Recompute path** |
| **`animaltags` (Python port)** | **GPL-3** | medium; copyleft | separate offline process | Costed; isolate process; record GPL |
| **`tagtools` (R)** | **GPL (>=3)** | high; R runtime (+500 MB-1 GB) | offline box batch only | Costed upgrade; never in web bundle |

GPL note: GPL is fine to run as a separate tool/service and to ship its *outputs* (data is not a derivative work); do not statically/dynamically link GPL into proprietary web code. Keep R/animaltags as an isolated batch job on the box; web reads artifacts.

## Skill descriptors (Central Casting, T2 keyed)

Each stage = one skill in `skills_manifest.json`, dispatched in `skills.py`, paired with `pipeline_studio` panel.

```json
{
  "id": "run_tagtools_dive_detect",
  "tier": "T2", "geo_required": false,
  "wraps": "infra/tagtools/dive_detect.py",
  "inputs": { "deployment_id": "mn09_203a", "depth_threshold_m": "number", "min_duration_s": "number" },
  "produces_annotations": ["artifact_citation"],
  "data_bindings": ["/depth/values", "/eti/values"],
  "honesty": "measured-derived",
  "provenance": { "source": "tagtools-port", "license": "GPL-3-isolated", "runtime": "offline-batch" }
}
```

Companion descriptors: `run_tagtools_orientation`, `run_tagtools_odba`, `run_tagtools_normjerk`, `run_tagtools_stroke_glide`, `read_tagtools_baked_stage` (T1; serves baked output for any stage). All return `{artifact_url, content_hash, generated_at, stage, params, honesty}`. Writes/mutations T2; pure baked reads T1.

## Recommendations with cost + standin-free fallback

| Rec | Detail | Cost | Fallback |
|-----|--------|------|----------|
| R1 | Default studio = baked h5 reads via slice API | low | n/a (this is the floor) |
| R2 | Python recompute for norm-jerk/ODBA/VDBA/dive-threshold; compare-to-baked honesty toggle | ~2 eng-days | read baked only, label "precomputed offline" |
| R3 | `animaltags`/`tagtools` only as isolated offline box batch; record GPL; ship outputs only | ~2-3 eng-days + R/py env | skip; baked + Python primitives cover demo |
| R4 | All stage artifacts -> S3/box with content hash + provenance; web carries pointers | infra only | n/a |
| R5 (O0) | Confirm h5 + derived-output redistribution license | O0 gate | keep artifacts internal/keyed |

Standin-free fallback: serve real baked stage outputs from real h5 with stage label + "precomputed offline" provenance. Never synthesize a pipeline result.

## Open questions / flags for O0

1. h5 + derived-products license for hosting stage artifacts on the box?
2. GPL posture: is an isolated offline R/animaltags batch acceptable, or stay Python-primitives-only for demo?
3. Which stages must be live-recomputable in the demo vs read-baked?
4. Fluke-rate / stroke-glide not pre-baked: recompute in Python or defer?
5. Taxonomy/units provenance: confirm 5 Hz sample rate + calibration metadata travels with every artifact.

## Sources

**orcast (240570e):** `infra/orca/biologging/prebake.py`, `src/aws_backend/casting/{skills.py,skills_manifest.json,panels.py}`, `BSW-STUDIO-SKILLS_CHARTER.md`, `PROGRAM.md`, `research/BSW-R04_kinematic_ethogram.md`, `research/BSW-R10_annotation_studio_viz.md`

**whale-behavior-analysis (external):** `dive_analysis.h5`, `dive_analysis_schema_flat.json`, `behavior_mapping.json`, `Visualization_Poster_Appendix/scripts/03_composite_dashboard.R` (`calculate_normjerk()`), `DATA_BINDING_MANIFEST.md`

**External (URLs + licenses):**
| URL | License |
|---|---|
| https://github.com/animaltags/tagtools_r | GPL (>= 3) |
| https://github.com/animaltags/tagtools_py | GPL-3 |
| https://animaltags.org/ | project site / docs |
| https://doi.org/10.1111/2041-210X.13001 | Methods in Ecology & Evolution (tag tools paper) |
