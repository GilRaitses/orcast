# BSW-R05 - Acoustic<->behavior coupling

> Read-only research finding (BSW-RESEARCH wave). Repo verified against `240570e`.
> Authored by explore agent 4271bff6; written by the BSW sub-orchestrator.

## Summary

- **Two tracks stay separate by charter:** hydrophone acoustic classification (BAM, R02/R03) answers **who/what is present**; DTAG kinematics (R04, `biologging.ts`) answers **how the modeled orca moves**. They meet only at the **scrub-synced timeline**, not as a single fused model.
- **Strong literature coupling exists on DTAG tags** (same animal, co-recorded sound + motion): slow clicks -> search, fast click trains -> pursuit, buzzes -> close-range targeting/capture attempts, often paired with deep dives and high jerk/roll. These are **measured on tagged whales** but **correlational at the dive-segment level**, not proof that any single hydrophone event caused a specific dive in the replay.
- **Hydrophone-only coupling is weaker:** discrete pulsed calls correlate with group activity and pod identity but **no call type maps exclusively to one behavior**; whistles skew toward social/travel; group-level click rates differ by observer-assigned state but do not recover individual dive kinematics.
- **Acoustic classification may legitimately drive:** spawn count (within model-supported bounds), presence/type labels in the HUD, and scene placement anchors. It must **not** drive depth, fluke phase, dive phase, or behavior->motion clip selection.
- **The shipped SRKW driver is kinematics-only:** `orca_srkw_oo14_driver.{json,bin}` exposes 7 channels; Tennessen foraging/buzz metadata lives in source `.mat`/`foraging_data.csv` but is **not baked into the web driver**.
- **`behavior_mapping.json` is humpback contrast taxonomy** (9 expert-labeled classes); it must never drive SRKW orca motion.

## Literature-grounded couplings (with citations + label)

### DTAG co-recorded acoustic + kinematic (strongest; same deployment)

| Coupling | Label | Evidence |
|---|---|---|
| Slow click trains (ICI >100 ms) shallow, large depth change -> prey search / area scanning | Measured / correlational | Holt 2017 (`10.1121/1.4969803`); Wright 2019 (`10.1121/1.5133388`) |
| Fast click trains (10<ICI<=100 ms) intermediate depth -> pursuit / closing | Measured / correlational | Wright 2019 (`10.1121/1.5133388`); Wright 2021 (`10.1111/mms.12836`) |
| Buzz trains (ICI<=10 ms) deepest, smallest depth change -> close-range targeting; often pre/concurrent with capture | Measured / correlational (capture confirmed in subset) | Wright 2019; Wright 2021; Tennessen 2024 (`10.1111/gcb.17490`) |
| Prey-handling sounds (crunch/tear) -> consumption/sharing at shallow depth | Measured / correlational | Wright 2021 (`10.1111/mms.12836`) |
| HMM State 1: deep dives + buzz + clicks + high jerk/roll -> deep prey pursuit/capture | Measured inputs, interpretive name | Tennessen 2019 (`10.1038/s41598-019-50942-2`) |
| HMM State 4: shallow + clicks, no buzz -> prey searching | Measured / interpretive | Tennessen 2019 |
| HMM State 5: shallow, rare clicks, low variance -> directional travel | Measured / interpretive | Tennessen 2019 |
| HMM State 2: shallow, no buzz, short -> surface respiration/recovery | Measured / interpretive | Tennessen 2019 |
| Foraging occurs in bouts (search->pursuit->recovery), not random dive-by-dive | Measured (transition probs) | Tennessen 2019; Tennessen 2024 |
| Vessel noise up -> up slow-click searching, down female buzz/pursuit, down capture | Measured (25 DTAG deployments) | Tennessen 2024 (`10.1111/gcb.17490`) |

### Social / contact vocalizations vs activity state

| Coupling | Label | Evidence |
|---|---|---|
| Discrete pulsed calls = intragroup contact/coordination; relative usage shifts with activity but **no call type exclusive to one behavior** | Correlational | Ford & Fisher 1989 (`10.1139/z89-105`) |
| Whistles more common in socializing/traveling; less useful during foraging | Correlational | Riesch et al. (PMC8404572) |
| Variable/aberrant calls increase during socializing + beach-rubbing | Correlational | Ford & Fisher 1989 |
| Pod-specific discrete call repertoires (J/K/L dialects) indicate pod affiliation / who, not a kinematic dive mode | Measured repertoire / interpretive ID | Ford call catalog tradition |

### Fixed-hydrophone / group-observation proxies

| Coupling | Label | Evidence |
|---|---|---|
| Group click rate differs by behavior state (socializing > foraging > traveling > milling > resting) | Correlational (group-level) | Beneze et al. 2011 (`10.1121/1.3588650`) |
| Echolocation click presence on arrays indicates biosonar activity in area, not which individual dives | Correlational | Holt 2017 |

### In-repo kinematic track (no acoustic channels in replay driver)
`driveOrca(rig, pose, ...)` applies measured DTAG pose from pre-baked `.bin` (Tennessen 2024, DOI `10.5281/zenodo.13308835`) - measured telemetry. Humpback 9-class ethogram (`behavior_mapping.json`) -> motion clips for **contrast/reference only**.

### In-repo heuristics (NOT literature-grounded for replay; flag for O0)
`ml_behavioral_pipeline.py:307-363`: `echolocation_click`->+foraging score, `social_call`->+social score (interpretive heuristic, not validated SRKW coupling). `dtag_data_processor.py`: simulated buzz/click events with `context="foraging"` (simulated; must not ship as measured).

## What acoustic classification may legitimately DRIVE in the replay

(All assume honest HUD wording scoped to held-out eval; presence/call-type first; count only if R03 proves it.)

1. **Which orcas appear (spawn set):** 0/1/N `OrcaRig` instances anchored at encounter-relevant positions. Label: modeled count derived from measured hydrophone inference, with confidence shown. Pod/call-type identity only when model + schema support it.
2. **HUD / classification record fields (read-only):** SRKW presence/absence, call-type label(s), optional source-count band if eval supports. Interpretive activity hints only when labeled (e.g. "echolocation activity detected", not "foraging dive in progress").
3. **Timeline sync anchor only:** acoustic detections align scene time to BSH playhead; may mark interpretive timeline annotations on the spectrogram without retargeting kinematics.
4. **Multi-orca identity presentation, not motion:** different rigs may carry different call-type labels/badges; all share the same SRKW driver clip or distinct clips chosen by **kinematic** ethogram (R04), not by hydrophone buzz detection.
5. **Camera / POV context:** "activity detected" may bias default camera framing as a modeled UX choice, labeled interpretive.

**Cost-aware minimum (standin-free):** presence -> spawn 1 SRKW at station anchor; call-type -> HUD text only; motion always from `orca_srkw_oo14_driver`. Zero extra ML coupling cost.

## What it must NOT drive (anti-overclaim boundary)

1. **Kinematic DOFs:** depth, pitch, roll, yaw, fluke phase/amplitude come from DTAG telemetry, not hydrophone classifiers.
2. **Behavior->motion clip selection** is R04 kinematic ethogram work on DTAG segments, not BAM output.
3. **Causal claims across sensors:** detecting a buzz/S10 call on a shore hydrophone does not justify switching the visible orca into a deep pursuit dive / mouth-open cue / capture narrative unless the same DTAG deployment co-registers that instant (generally unavailable in the demo slice).
4. **Individual ID from passive audio alone** beyond what the trained model achieves; no "this is K27".
5. **Humpback behavior taxonomy on orca rigs.**
6. **Fabricated coupling in legacy scripts** (`ml_behavioral_pipeline.py`, simulated `dtag_data_processor.py`).
7. **Forecast/encounter claims:** acoustic detections indicate presence likelihood at stations, not visible surface behavior.

## Recommendations with cost + standin-free fallback

| Recommendation | Cost | Standin-free fallback |
|---|---|---|
| Keep BAM output contract to `{presence, call_types[], confidence, optional_count}`; BRE consumes only spawn + labels | Low (schema) | Presence-only -> 0 or 1 orca; ignore count |
| Pin all demo orcas to real SRKW driver until R04 ships clip library | Low (in repo) | Same driver for all; differentiate by label/color only |
| R04 clip library keyed by DTAG dive segments using Tennessen `foraging_data.csv` / shallow-deep segmentation on **tag depth**, not hydrophone | Medium (offline bake) | Single continuous driver; no clip switching |
| HUD honesty tiers: measured audio inference vs modeled 3D animal vs interpretive activity hint | Low | Drop interpretive hints; show call-type + confidence only |
| Optional timeline markers for classifier segments (no motion feedback) | Low | No markers |
| Do not add acoustic->mouth-open (OMOU) or acoustic->physics in B-side slice | Saves complexity | Mouth stays default unless DTAG buzz channel added later |
| If multi-orca count infeasible (R03), cap spawn at 1; show "multiple callers detected (unresolved)" | Low | Single orca + honest caveat |
| Future high-cost path: co-registered DTAG+audio replay where buzz aligns to depth spikes on same deployment | High (curation) | Defer post-slice |

## Open questions / overclaim-risk flags for O0

1. **Cross-sensor identity gap:** demo slice pairs Orcasound hydrophone audio with `oo14` SRKW DTAG kinematics from a different context. Scrub sync is **illustrative**, not a reconstructed encounter. Flag on-screen.
2. **Buzz->dive temptation:** literature links buzzes to pursuit on **tags**, but hydrophone classifiers rarely resolve buzz trains to individual kinematic dives. Wiring buzz detection -> deep dive would be fake coupling.
3. **Call-type -> behavior state:** Ford 1989 rejects exclusive call-behavior mapping. "S10 = excitement/foraging" without interpretive labeling overclaims.
4. **Beneze 2011 vs Tennessen 2019 tension:** group click rates highest in socializing, not foraging, while tag-level foraging shows abundant clicks in search state. "More clicks = foraging" HUD text would overclaim.
5. **Count + type feasibility (R03 gate):** spawning N rigs from unresolved count is an overclaim risk.
6. **Legacy simulated DTAG path** (`data/dtag_analysis_results.json` simulated; `/api/dtag/*` not on web proxy). Do not present as measured coupling.
7. **`dtag_behavioral_analyzer.py` fallbacks** synthesize depth/acoustic when missing - any clip from this without real h5 input is standin motion.
8. **Sex/pod kinematic differences** (Tennessen 2019) are population patterns, not something acoustic pod labels should drive per-individual.
9. **OMOU foraging mouth cue** requires DTAG foraging/buzz context, not hydrophone classification.
10. **CLAIM_BOUNDARIES:** do not emit "orca species ID from audio" or "predicted dive behavior" as system capability; B-side is replay + honest inference labels only.

## Sources

### In-repo
- `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/{PROGRAM.md,BSW-ACOUSTIC-ML_CHARTER.md,BSW-REENACTMENT_CHARTER.md,wave_shape.yml}`
- `web/lib/scene/orca/motion/biologging.ts`, `web/public/orca/motion/orca_srkw_oo14_driver.json`
- `infra/orca/biologging/data/tennessen2024_srkw_dtag/PROVENANCE.md`, `infra/orca/biologging/OG-R_h5_mapping.md`
- `.cca/catalogue/O0/20260628_orca-biologging-twin/ORCA-MOUTH_CHARTER.md`
- `src/data-processing/ml_behavioral_pipeline.py`, `scripts/ml_services/dtag_data_processor.py`
- `/Users/gilraitses/whale-behavior-analysis/behavior_mapping.json` (humpback 9-class; contrast only)

### External (literature)
- Tennessen 2024 (vessel noise; search/pursuit/capture): https://doi.org/10.1111/gcb.17490
- Tennessen 2019 (HMM acoustic + kinematic states): https://doi.org/10.1038/s41598-019-50942-2
- Wright 2019 (click-train ICI phases): https://doi.org/10.1121/1.5133388
- Wright 2021 (echolocation + prey-handling): https://doi.org/10.1111/mms.12836
- Holt 2017 (DTAG echolocation foraging): https://doi.org/10.1121/1.4969803
- Ford & Fisher 1989 (call usage vs activity): https://doi.org/10.1139/z89-105
- Beneze 2011 (group click rate vs state): https://doi.org/10.1121/1.3588650
- Riesch et al. (SRKW stereotyped whistles vs context): https://pmc.ncbi.nlm.nih.gov/articles/PMC8404572/
- Tennessen 2024 open DTAG data (SRKW driver source): https://doi.org/10.5281/zenodo.13308835
- SRKW call catalog: https://www.orcasound.net/data/product/SRKW/call-catalog/srkw-orca-call-catalog.html
