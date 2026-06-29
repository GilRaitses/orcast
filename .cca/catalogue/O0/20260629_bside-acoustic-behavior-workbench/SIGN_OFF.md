# BSW sign-off - real demo-slice spec ratification

O0 + owner ratification of the `BSW-RESEARCH` synthesis
(`research/SYNTHESIS_bside.md`) and the real demo-slice spec. Repo verified against `240570e`.
Owner-direct calls are marked **OWNER**; the rest are O0 reasonable sign-offs within the charter's
locked decisions. No standins; no overclaim.

| # | Decision | Call | Basis |
|---|----------|------|-------|
| 1 | License blocker (CC BY-NC-SA on Orcasound audio + Pod.Cast + OrcaHello) | **OWNER: AUTHORIZE NC.** Owner declares orcast non-commercial / conservation, so Orcasound archived audio + Pod.Cast + OrcaHello annotations are usable. Derived models inherit NC + ShareAlike; every asset records source URL + license + attribution. Truly unclear-license sets (LiveOcean no-license, ONC partner subsets unless cleared) stay excluded. | Owner is the legal decision-maker; conservation/non-commercial use is within CC BY-NC-SA. Unblocks the richest annotation corpora. |
| 2 | Acoustic model target | **OWNER-DIRECTED: statistical "acoustic-silhouette" modeling of the labels the corpora actually carry.** Where annotations label presence / call-type / single-vs-multiple callers, those labeled recordings are training inputs; the model estimates those categories and reports an **estimate + confidence** with honest held-out eval (precision/recall/F1, confusion, failure modes). HARD LINE: it is the model's statistical inference, labeled as an estimate; no claim of exact whale count or pod/individual ID beyond validated performance. UI wording is "estimated: SRKW call present / multiple callers (confidence X)", never "3 orcas, J-pod". Supersedes the synthesis "presence-only" floor. | Owner: the annotations themselves say "one thing or multiple", so they are a legitimate statistical-modeling input for the sound silhouette. Honesty held by estimate+confidence framing + real eval. |
| 3 | Scope this pass | One real vertical slice **B -> C -> D -> E** (station -> spectrogram+timeline -> silhouette classifier -> scrub-synced reenactment). BSS studio/skills + the ocean layer are follow-on. | Operator's earlier "charter + one thin real slice"; proves the full no-standin chain end-to-end. |
| 4 | Classifier runtime | Precomputed REAL inference JSON for the demo clip, baked offline from the trained model (real output, not synthetic); `onnxruntime-web` only if live in-browser inference is later required. | Low risk, real output, no heavy browser dep. |
| 5 | Spectrogram compute | Web Worker STFT, precomputed + scrubbable Canvas/WebGL HUD; no ONC token dependency. | Compute-neutral, no new dep, real audio. |
| 6 | Multi-orca | N `OrcaController` skinned instances, shared geometry/materials, LOD by distance; not skinned-InstancedMesh. | R08; joins the single Water2Rig depth pre-pass (no third full render). |
| 7 | Interpretive ocean layer | Off by default; additive transparent mesh reading the existing depth pre-pass (no raymarch, no new full render); mandatory `interpretive · stratified ocean mixing` chip; forbid "measured thermohaline" / "biosonar perception" copy. | R09; honesty lock. |
| 8 | LGC glass tokens | Consume when LGC ships; `.bsw-glass` local fallback meanwhile (namespaced, no global glass vars). | LGC unbuilt; do not block B-side. |
| 9 | SalishScene.tsx mount-order arbiter | **BSW-SLICE-INTEGRATE is the single editor** for the BSW slice merge; serializes vs WFX/ORCA/LGC/CVP/3D-TWIN via O0; preserves the single-depth-pre-pass invariant. | R13 nexus risk; one owner. |
| 10 | Camera dive-clamp owner | BST relaxes `director.ts` underwater clamp for the slice's hydrophone-POV/dive, coordinated with CVP (camera owner) via O0. | R07/R13; gates dive POV + ocean layer. |
| 11 | Poster R runtime | Offline R batch on the box (reuse `run_all.R`), serve cached PNG/HTML; JS/Plotly port only for the interactive lattice if needed. | R10; no hosted R service. |
| 12 | tagtools | Read baked h5 stage outputs by default; `tagtools` R (GPL-3) isolated to offline batch only - never bundled/linked into the hosted app. | R11; GPL-3 isolation. |
| 13 | Heavy assets | Meshes, audio clips, classifier weights, poster artifacts, capture mp4 -> box/S3, gitignored, with a re-fetch PROVENANCE pointer. | Lean-repo policy. |
| 14 | Build/verify/train hosts | All slice build + verification + any training run on the real aimez box dev hosts (GPU render host `infra/render_host/render.sh` + the box), NOT local dev servers. | Operator standing instruction (local dev servers unreliable). |
| 15 | Cross-sensor representativeness | Mandatory on-screen label: "Kinematics are representative SRKW DTAG motion, not the recorded animal." Acoustic presence picks which clip spawns + HUD label; it never drives the literal trajectory. | R05; audio and DTAG are different animals. |

## Resolved open questions (from synthesis (e))
Q1 license -> #1 (authorize NC). Q2 scope -> #3 (one vertical slice). Q3 runtime -> #4 (precomputed
JSON). Q4 mount arbiter -> #9 (BSW-SLICE-INTEGRATE). Q5 dive-clamp -> #10 (BST + CVP via O0).
Q6 LGC timing -> #8 (.bsw-glass fallback). Q7 h5 redistribution -> contrast/reference only, hosting
scope stays a STOP-to-O0 for BSS (follow-on, not in the slice). Q8 R runtime -> #11 (offline batch).
Q9 equipment mesh -> parametric `three` rig default (external CAD only if license-clear). Q10
LiveOcean/ONC -> excluded unless cleared (#1).

## Locked REAL slice spec (built this pass)
- **Station:** Orcasound Lab (Haro Strait), equipment mesh on the seabed via `projectToScene` +
  substrate sample; camera POV (hydrophone POV + top-down) via `director.ts`.
- **Clip + labels:** with NC authorized, the R01 Orcasound SRKW clip + Pod.Cast/OrcaHello labels are
  in-scope (NC+attribution recorded), complemented by DCLDE-2027 (CC-BY 4.0). Provenance recorded
  per asset (station, UTC, URL, license, sample rate).
- **Model:** statistical acoustic-silhouette classifier over the labeled categories the corpora
  provide (presence / call-type / single-vs-multiple), reported as estimate + confidence with honest
  held-out eval; shipped as precomputed real inference JSON for the clip.
- **Reenactment:** acoustic estimate -> which orca clip(s) spawn + HUD label; real SRKW DTAG driver
  (`orca_srkw_oo14_driver.json`, CC-BY-4.0) -> motion; representativeness label mandatory.
- **Honesty set on screen:** measured (audio/spectrogram/DTAG) · modeled (orca/equipment mesh,
  classifier inference) · interpretive (ocean layer) · representativeness note.

Status: signed 2026-06-29. Slice build (BST/BSH/BAM/BRE, net-new, host-verified, gated) authorized
to dispatch; integrate + commit remain O0/operator gates.
