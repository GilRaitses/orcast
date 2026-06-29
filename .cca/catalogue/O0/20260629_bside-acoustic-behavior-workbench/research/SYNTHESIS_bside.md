# SYNTHESIS - B-SIDE Acoustic + Behavior Research Workbench (BSW)

> Sub-orchestrator synthesis of BSW-RESEARCH (Wave 1). Read-only. Repo verified against `240570e`.
> Inputs: the 14 findings docs `research/BSW-R01..R14`. This document is for O0 sign-off; no later wave was started.

---

## 0. One-paragraph verdict

A real, no-standin end-to-end slice is achievable **only if O0 resolves the license blocker first**: Orcasound archived audio and the community annotation corpora (Pod.Cast, OrcaHello) are **CC BY-NC-SA 4.0** (NonCommercial + ShareAlike), which is incompatible with a commercial/hosted demo and forces derived models under the same NC terms. The clean path is to build the slice on genuinely open data (**DCLDE-2027 CC-BY 4.0** for labels; a **CC-BY/CC0 audio clip**), keep the acoustic classifier to an **honest target of binary SRKW-call presence + confidence** (count/type/pod-ID are NOT achievable), drive **which** orca clip spawns from acoustic presence while motion comes from the **real SRKW DTAG driver** (labeled "representative, not the recorded animal"), and render the double-diffusion ocean layer as **interpretive**. Everything else (station player, spectrogram HUD, multi-orca reenactment, studio/skills) is buildable on `three` + WebAudio with compute-neutral budgets, gated behind a serialized edit order on the `SalishScene.tsx` nexus.

---

## (a) Ranked, sequenced build plan across the five charters

Costs are engineering-day estimates (clearly labeled estimated), excluding O0 license-clearance latency.

| Rank | Phase | Charter / lane | What lands | Depends on | Est. cost | Standin-free fallback |
|------|-------|----------------|-----------|------------|-----------|------------------------|
| 0 | A | **License clearance (O0)** | DCLDE-2027 + CC-BY/CC0 clip approved; NC assets excluded | - | O0 gate | none - hard gate |
| 1 | A | **LGC tokens** (external lane) | glass tokens in `globals.css` | - | external | `.bsw-glass` local fallback |
| 2 | B | **BST** station + camera POV | hydrophone equipment mesh at real lat/lng on seabed; POV via `director.ts`; `streamUrl` plumbed | A | 4-6 d | parametric three rig; label-only station if no live URL |
| 3 | C | **BSH** spectrogram HUD + `SpectroTimelineAuthority` | Worker STFT spectrogram, scrubbable Canvas HUD; timeline authority for downstream | 2 (streamUrl) | 4-6 d | static spectrogram PNG (current) until live |
| 4 | C | **BSH** ocean-process layer | interpretive additive layer reading Water2Rig depth target; gated off default | Water2Rig | 2-3 d | layer disabled; HUD ships without it |
| 5 | D | **BAM** acoustic classifier output | presence + confidence inference for the chosen clip | 3 (timeline) | 5-8 d | precomputed real inference JSON; real open detector (OrcaHello-style if license ok) |
| 6 | E | **BRE** multi-orca reenactment | N `OrcaController` instances, shared geometry, scrub-synced to timeline; acoustic presence -> spawn, DTAG -> motion | 3,5, R04 clips | 5-7 d | single orca, real driver clip, scrub-synced |
| 7 | F | **BSS** studio + skills + capture | annotation studio (read h5 slices), managed skill catalog, poster-viz HUD, director behavior-capture | C-E | 6-10 d | read-only studio + pre-baked artifacts |

**If O0 wants one vertical slice (recommended given five-charter breadth, R14 risk #10):** land **B -> C -> D -> E** (station -> spectrogram+timeline -> presence classifier -> scrub-synced reenactment). That is the full "real audio -> real spectrogram -> real classifier output -> real DTAG kinematics" claim. BSS studio/skills + ocean layer become follow-on.

---

## (b) Recommended dependency decisions

| Decision | Recommendation | Cost | Three-only / standin-free fallback |
|----------|----------------|------|------------------------------------|
| Acoustic inference runtime | Precomputed real inference JSON for the demo clip; `onnxruntime-web` only if live inference is required | low / medium | precomputed JSON (real model output, baked offline) |
| Spectrogram compute | Web Worker STFT, precomputed + scrubbable | compute-neutral | n/a (WebAudio + Worker, no dep) |
| Multi-orca | N `OrcaController` SkinnedMesh instances, shared geometry/materials, LOD by distance; **not** InstancedMesh (skinned) | per-charter | single orca |
| Ocean-process layer | additive transparent mesh reading existing depth pre-pass; **no** new full render, **no** raymarch | 2-3 d | layer disabled |
| Poster viz / R | offline R batch on box (reuse `run_all.R`), serve cached PNG/HTML artifacts; JS port (Plotly.js) for interactive lattice + energetics | medium | pre-baked PNG/HTML; never synthetic figures |
| tagtools | read baked h5 stage outputs by default; Python primitives for recompute; **`tagtools` R (GPL-3) isolated offline batch only** | low-medium | baked reads labeled "precomputed offline" |
| Plotly bundle | iframe pre-rendered HTML for 3D lattice; plotly.js (~1-3 MB gz) only if interactivity required | medium | iframe HTML |
| LGC glass tokens | consume when shipped; `.bsw-glass` fallback meanwhile | low | local glass |
| Heavy assets | meshes, audio clips, classifier weights, poster artifacts, capture mp4 -> **box/S3**, not git | infra | n/a |

---

## (c) Convergence-file collision map (vs LGC / CVP / WFX / ORCA / 3D-TWIN)

| File | BSW touch | Other lanes | Risk | Mitigation |
|------|-----------|-------------|------|------------|
| `web/app/components/scene/SalishScene.tsx` | HydrophoneStationRig (BST), OceanProcessRig (BSH, after Water2Rig), multi-orca (BRE, OrcaRig slot), IntentDirectorRig (BST) | WFX, ORCA, LGC, CVP, 3D-TWIN | **HIGH (nexus)** | serialize Phases A-F; one mount-order arbiter; preserve single depth pre-pass invariant |
| `web/app/globals.css` | `.bsw-*` HUD CSS, `.hydrophone-spectrogram` (BSH) | LGC (glass token authority) | medium | namespace `bsw-*`; local glass fallback; no global glass vars |
| `web/app/components/AdaptiveExplore.tsx` | plumb `streamUrl` into `hydrophone_signal` props (237-245) | CVP, LGC (panel injection) | medium | one-prop edit; serialize |
| `web/app/components/ActiveSurfaceHost.tsx` | new `renderPanel` cases (spectrogram_hud, tag_series, dive_panel, label_editor, pipeline_studio, poster_*_hud, capture_studio) | all panel-adding lanes | low (additive) | namespaced ids |
| `web/lib/uiIntent.ts` | `PANEL_LABELS` + type entries | panel-adding lanes | low (additive) | additive only |
| `web/lib/scene/camera/director.ts` | POV (BST), behavior framing (BRE), **needs dive-clamp relax** for underwater | CVP (camera owner) | medium | O0/CVP decides clamp owner; layer dormant above water until then |

**Hard invariants:** (1) Water2Rig owns the only depth pre-pass; BSW layers join it, never add a third full render. (2) Mount order in `SalishScene.tsx` must be arbitrated by one owner across lanes.

---

## (d) CONCRETE proposed REAL demo-slice spec (for O0 sign-off)

> The slice proves: **real audio -> real spectrogram -> real classifier output (presence) -> real SRKW DTAG kinematics**, with honest labels throughout. Two source variants depending on license clearance.

**Station:** Orcasound "Orcasound Lab" hydrophone (Haro Strait / San Juan Island), real lat/lng, equipment mesh placed on seabed via `projectToScene` + `sampleSubstrate`. Camera POV: hydrophone-POV + top-down via `director.ts`.

**Archived clip (license-gated choice):**
- **Preferred (open):** a **CC-BY / CC0** SRKW vocalization clip (verify per-asset). If none is cleanly open, use a **DCLDE-2027 (CC-BY 4.0)** SRKW presence segment as the audio + label source.
- **Only if O0 clears NC use in writing:** the R01-recommended Orcasound clip (e.g. 2021-08-25 L-pod SRKW bout) - **CC BY-NC-SA 4.0, STOP-to-O0 by default.**
- Provenance recorded: station, UTC timestamp, source URL, license, sample rate (48 kHz AAC HLS).

**Acoustic dataset / labels:** **DCLDE-2027 (CC-BY 4.0)** for SRKW presence/ecotype training/validation. **Do NOT use** Pod.Cast / OrcaHello annotations in the shipped slice unless O0 clears CC BY-NC-SA.

**Annotation dataset (kinematic studio, follow-on):** humpback `dive_analysis.h5` + 51 manual spans (`log_mn09_203a.csv`) - **contrast/reference only**, license redistribution scope is a STOP-to-O0 (R10/R11).

**HONEST model target (BAM):** **binary SRKW-call presence + confidence score** over time, aligned to the spectrogram timeline. **Explicitly NOT:** count of whales, call-type/ecotype classification, pod/individual ID, localization. UI strings must never assert count or type. Inference shipped as precomputed real JSON for the clip (or live `onnxruntime-web` if built).

**Behavior -> motion mapping (BRE / R04, R05):**
- **Acoustic presence** -> *which* clip class spawns + HUD label ("SRKW call present, confidence X").
- **Real SRKW DTAG driver** (`orca_srkw_oo14_driver.json`, simulated:false, CC-BY-4.0) -> *how* the orca moves (yaw/pitch/roll/depth/fluke), selected by frame-window clip contract.
- **Mandatory label:** "Kinematics are representative SRKW DTAG motion, not the recorded animal." Acoustic never drives the literal trajectory (R05 separation).

**Interpretive ocean layer (BSH / R09):** off by default; if shown, `interpretive · stratified ocean mixing` chip, grounded in cited CC0 CruiseSalish T/S; forbid "measured thermohaline" / "biosonar perception" copy.

**Honesty label set on screen:** measured (audio, spectrogram, DTAG) · modeled (orca mesh, equipment mesh, classifier inference) · interpretive (ocean layer) · representativeness note (cross-sensor).

---

## (e) Open questions for O0

1. **License (BLOCKER):** Clear CC BY-NC-SA Orcasound audio + Pod.Cast/OrcaHello for the demo, or commit to the open path (DCLDE-2027 CC-BY + CC-BY/CC0 clip)? No NC asset ships until answered.
2. **Scope:** Land one vertical slice (B->C->D->E) end-to-end, or attempt all five charters at reduced depth? (R14 risk #10.)
3. **Classifier runtime:** Precomputed real inference JSON (low risk) acceptable, or is live in-browser inference (`onnxruntime-web`) required?
4. **Mount-order arbiter:** Who owns `SalishScene.tsx` merge serialization across WFX/ORCA/LGC/CVP/3D-TWIN/BSW?
5. **Camera dive-clamp:** CVP or BST owns relaxing `director.ts` underwater clamp (gates ocean layer + dive POV)?
6. **LGC timing:** Ship date vs BSW deadline - block on tokens or ship `.bsw-glass` fallback?
7. **whale-behavior h5 license:** Redistribution scope for hosting poster artifacts + multi-reviewer annotation writes (R10/R11)?
8. **R runtime:** Offline batch only (recommended), or App Runner R sidecar for on-demand poster regen?
9. **Equipment mesh:** Parametric three rig (default) or costed external CAD (verify mesh license)?
10. **LiveOcean / ONC partner sets:** Exclude (recommended) or clear licenses (R09)?

---

## Index of findings docs

| Doc | Topic |
|-----|-------|
| `research/BSW-R01_orcasound_audio.md` | Orcasound archived audio access + license |
| `research/BSW-R02_annotation_corpora.md` | Community annotation corpora survey |
| `research/BSW-R03_acoustic_ml.md` | Acoustic ML feasibility + honest target |
| `research/BSW-R04_kinematic_ethogram.md` | DTAG kinematic ethogram -> orca rig |
| `research/BSW-R05_acoustic_behavior_coupling.md` | Acoustic-behavior coupling (track separation) |
| `research/BSW-R06_spectro_hud.md` | Spectrogram HUD + timeline authority |
| `research/BSW-R07_station_player_camera.md` | Station player + camera POV |
| `research/BSW-R08_multiorca_reenactment.md` | Multi-orca instancing + scrub sync |
| `research/BSW-R09_ocean_process_layer.md` | Interpretive double-diffusion ocean layer |
| `research/BSW-R10_annotation_studio_viz.md` | Annotation studio + poster-viz skills |
| `research/BSW-R11_tagtools_pipeline.md` | tagtools/animaltags pipeline as skills |
| `research/BSW-R12_skill_catalog_capture.md` | Skill catalog + behavior-capture director |
| `research/BSW-R13_integration_seams.md` | Integration seams + collision map |
| `research/BSW-R14_adversarial.md` | Adversarial audit |
