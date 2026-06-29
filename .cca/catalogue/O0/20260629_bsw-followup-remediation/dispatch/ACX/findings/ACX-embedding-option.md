# ACX-R3 — learned-embedding option (costed), vs the feature-only path

Read-only research finding for ACX-Q. **This is an O0-COSTED option, never a
default and never self-approved.** No code edited, no weights/corpus downloaded,
no install, no training. All model facts are from the open web (cited inline);
all repo facts are from the landed pipeline and `eval_report_dclde_v1.json`.

## Summary (recommendation framing)

A learned audio embedding is the single most credible lever for the **ecotype-TKW**
head, and the literature is unusually direct: the most relevant published
benchmark probes exactly our task — killer-whale ecotype classification on DCLDE
killer-whale audio — and shows pretrained bioacoustic embeddings reach few-shot
one-vs-all ROC-AUC of **0.90–0.945** on orca ecotype (Burns et al., *Perch 2.0
transfers 'whale' to underwater tasks*, NeurIPS 2025 workshop, arXiv:2512.03219).
The current 129-dim log-mel silhouette gets ecotype macro AUPRC 0.679 (logreg) /
0.739 (rf) and TKW f1 0.434 / 0.277 on our leave-station-day-out split. So the
embedding ceiling is plausibly much higher — **but those benchmark numbers are
few-shot ROC-AUC on a different split and are not a TKW-f1 lift on our split; the
benefit is unverified until trained and gated.** The important and slightly
counter-intuitive finding: the best license-clear embedding for this task is a
**TensorFlow** model (the Perch family, Apache-2.0), **not torch**; the torch and
NC options are either license-blocked or weaker. For **call_type**, an embedding
improves call-morphology representation but does **not** fix the binding
constraint (sparse, single-station coarse labels — see ACX-R2), so it is not a
standalone fix there. Recommendation to ACX-Q below; every gated item is named.

## Candidate embedding survey

Embedding dim / window / sample-rate / params from Burns et al. 2025 Table 1
(arXiv:2512.03219), cross-checked against each model's own card. "Marine
relevance" is grounded in that paper's DCLDE-2026 **orca-ecotype** few-shot
linear-probe ROC-AUC (k=8 / k=16), which is the closest published analogue to
our ecotype-TKW head.

| Model | Arch | Embed dim | Params | Framework dep | CPU vs GPU inference | Weights license | Marine / ecotype relevance |
|---|---|---|---|---|---|---|---|
| **Perch 2.0** | EfficientNet-B3 | 1536 | 101.8M (12M backbone + 91M class head) | TensorFlow ≥2.20 | CPU variant now exists in perch-hoplite v1.0.1 (`perch_v2_cpu`, auto-selected w/o GPU); GPU faster | **Apache-2.0** | **Top** on DCLDE orca ecotype: 0.917 / 0.945; tSNE shows best TKW↔NRKW boundary. ~no marine in training. |
| **BirdNET V2.3** | EfficientNet-B0-like | 1024 | 20.0M | TensorFlow / TFLite (CPU-friendly; ONNX exports exist) | CPU-trivial | **CC-BY-NC-SA-4.0 (NC → STOP)** | 2nd-best ecotype: 0.905 / 0.933. License blocks it (see Licenses). |
| **Perch 1.0 / Perch 8** | EfficientNet-B1 | 1280 | 23.9M | TensorFlow | CPU-feasible | **Apache-2.0** | Strong ecotype: 0.901 / 0.931. Lighter than Perch 2.0. |
| **SurfPerch** | EfficientNet | 1280 | 24.2M | TensorFlow | CPU-feasible | **Apache-2.0** | Ecotype 0.859 / 0.903 (reef-tuned). |
| **GMWM** (Google multispecies whale) | CNN (spectrogram) | 1280 | 4.1M | TensorFlow SavedModel | CPU-trivial (tiny) | **Apache-2.0** | The *actual whale model*, yet **weakest** ecotype transfer: 0.764 / 0.821; off-the-shelf classifier head only 0.612. tSNE: poor linear separability. |
| **AVES-bio** (animal HuBERT) | HuBERT (transformer) | 768 | 94.4M | torch / torchaudio (ONNX export exists) | CPU-feasible, slower (transformer) | v1 repo MIT (code); **AVES2 weights cards say CC-BY-NC-SA-4.0 → STOP/verify** | General-audio ecotype 0.825 / 0.879; tSNE entangles TKW↔NRKW and SRKW. |
| **BirdAVES (large)** | HuBERT-large | 1024 | 315.4M | torch / torchaudio | GPU recommended (large) | same AVES caveat | ecotype 0.809–0.865; heaviest. |
| **PANNs CNN14** | CNN14 | 2048 | ~81M | **torch** | CPU-feasible | **CC-BY-4.0** (Zenodo weights) | Not in the DCLDE benchmark; AudioSet general-audio. License-clear torch option; expected ~general-audio tier, **unverified**. |
| **YAMNet** | MobileNetV1 | 1024 | ~3.7M | TensorFlow / TFLite / ONNX | CPU-trivial | **Apache-2.0** | General audio (16 kHz, 125–7500 Hz). Cheapest possible; weakest representation; not benchmarked on ecotype. |
| **VGGish** | VGG-11-like | 128 | ~62M | TensorFlow | CPU-feasible | **Apache-2.0** | Legacy AudioSet embedding; superseded by the above. |
| **NatureLM-audio** | BEATs + Q-Former + Llama-3.1-8B | LLM (not a fixed embedding) | ~8B | torch (heavy) | **GPU-only, heavy** | **CC-BY-NC-SA-4.0 (NC → STOP)** | Audio-language model, not a lightweight embedder; out of scope on cost + license. |

Sources: Burns et al. 2025 (arXiv:2512.03219) Table 1–2; Perch 2.0 (arXiv:2508.04665,
Apache-2.0, HF `cgeorgiaw/Perch`); perch-hoplite GitHub (TF install + `perch_v2_cpu`);
`google/multispecies-whale-detection` (Apache-2.0); BirdNET-Analyzer docs/FAQ
(CC-BY-NC-SA-4.0 models); earthspecies/aves (MIT code) + HF `EarthSpeciesProject/esp-aves2-*`
(CC-BY-NC-SA-4.0 weights); PANNs (arXiv:1912.10211, Zenodo weights CC-BY-4.0);
TensorFlow Models YAMNet/VGGish READMEs (Apache-2.0); NatureLM-audio (HF, CC-BY-NC-SA-4.0).

### License verdicts (every model flagged; this is the decisive axis)

- **License-clear for our use (Apache-2.0 or CC-BY-4.0):** Perch 2.0, Perch 1.0/Perch 8,
  SurfPerch, GMWM, YAMNet, VGGish (all Apache-2.0, TensorFlow); **PANNs CNN14 (CC-BY-4.0, torch).**
  Attribution required; no ShareAlike/NC conflict with the corpus.
- **STOP-to-O0 (NonCommercial):** **BirdNET** (CC-BY-NC-SA-4.0), **AVES2 / esp-aves2 weights**
  (CC-BY-NC-SA-4.0 per HF cards — note the *code* is MIT but the *weights* are NC-SA; original
  AVES-v1 weights are license-ambiguous and must be verified per checkpoint), **NatureLM-audio**
  (CC-BY-NC-SA-4.0). All three are NC → blocked for any commercial posture.
- **Corpus-interaction flag (must be in the O0 decision):** the DCLDE-2027 corpus is
  **CC-BY-SA-4.0**; ShareAlike + attribution travel into the embedding cache and the trained
  classifier (the derivative), regardless of which embedding model is used. An **NC-SA** weights
  license (BirdNET / AVES2 / NatureLM) is **incompatible** with the corpus's non-NC ShareAlike:
  the derivative would have to be simultaneously CC-BY-SA-4.0 *and* CC-BY-NC-SA-4.0, which cannot
  both hold. That makes the NC models a **hard STOP** unless O0 explicitly accepts an
  NC-only posture for the whole derivative. Apache-2.0 / CC-BY-4.0 weights have **no** such
  conflict (the SA from the corpus simply carries onto the derivative).

## Cost analysis

**New dependency weight** (CPU-only, clean venv; web-measured):
- **TensorFlow** (Perch/GMWM/YAMNet path): ~1.6 GB, ~33 packages. Perch 2.0 needs **TF ≥ 2.20**.
- **torch** (PANNs / AVES path): ~950 MB, ~12 packages (CPU wheel; CUDA adds the multi-GB `nvidia-*` stack).
- **onnxruntime** (if a model is exported to ONNX — YAMNet/VGGish/BirdNET/AVES/PANNs can be; **Perch v2 cannot** cleanly, its JAX `XlaCallModule` ops don't convert): ~140 MB, ~6 packages — the lightest framework, inference-only.

  Either way this is a **new heavy dependency** outside the locked numpy/scipy/sklearn/joblib
  stack — an explicit O0 gate. Weights go **to the box, gitignored**, per charter decision 6; only
  the small inference JSON + eval + a re-fetch pointer ship in-repo.

**Box compute need:** any box run is a human gate regardless. Embedding extraction is a
forward pass per window. The repo currently has **~5,525 featurized windows** (presence set;
ecotype ~3,786); an embedding path re-extracts over those plus any added TKW / coarse-call
windows (plausibly up to ~10–50k windows). Order-of-magnitude **estimates** (unverified, hardware-
dependent):
- GMWM / YAMNet (≤4M params): CPU near-real-time → ~minutes for 5–50k windows.
- Perch / SurfPerch / BirdNET (12–24M CNN): CPU ~minutes–tens-of-minutes for 5–50k; GPU minutes.
- AVES / BirdAVES (95–315M transformer): CPU ~roughly real-time → ~1–3 h for 5–50k; GPU strongly preferred.

  Extraction is **one-time** (cache the embeddings to the box), so the cost is paid once, not per train.

**Downstream classifier:** **unchanged** — still sklearn logreg / rf on the embedding vectors
(class-balanced / threshold-tuned as ACX-R1 proposes). Lightweight (seconds–minutes), **no new
dependency**, reproducible offline. The embedding only replaces the 129-dim feature vector.

## Expected-benefit assessment (literature-grounded, explicitly unverified-until-trained)

**(a) ecotype-TKW.** Current: ecotype macro AUPRC 0.679 (logreg) / 0.739 (rf); **TKW f1 0.434
(logreg) / 0.277 (rf)** on leave-station-day-out, ~19:1 SRKW:TKW. The most relevant published
result (Burns et al. 2025, DCLDE-2026 orca-ecotype few-shot linear probe, ROC-AUC k=8 / k=16):
Perch 2.0 **0.917 / 0.945**, BirdNET **0.905 / 0.933**, Perch 1.0 **0.901 / 0.931**, AVES-bio
0.825 / 0.879, GMWM 0.764 / 0.821. tSNE in that paper shows Perch 2.0 / BirdNET produce a clean
TKW↔NRKW boundary that general-audio (AVES) and the whale model (GMWM) blur. **Honest caveats
before reading this as a TKW lift:** (1) those are *multiclass one-vs-all ROC-AUC*, not AUPRC and
not a per-class TKW f1 — ROC-AUC is optimistic under our 19:1 imbalance; (2) *few-shot* (8–16 per
class) on a *balanced* probe ≠ our full imbalanced train; (3) DCLDE-2026 ecotype split ≠ our
leave-station-day-out split, so the cross-station/cross-day generalization confound is **not**
controlled in their number; (4) the imbalance and the sparse-TKW-station-days confound persist
regardless of features. **Conclusion: embeddings clearly carry ecotype-discriminative structure the
presence-oriented silhouette lacks, so a lift over TKW f1 0.434 is plausible and well-motivated —
but the magnitude is unknown and only an eval on our split (gated) can claim it.**

**(b) coarse call_type.** Current head collapses (whistle recall 0.0, macro-f1 0.43) on a single
test station (LimeKiln), 38 whistle windows. The Perch literature documents embeddings supporting
"call type / dialect" tasks, so an embedding would improve the *morphology-representation* side of
the problem. **But the binding constraint here is label coverage, not feature richness:** the
collapse is driven by sparse, mostly single-station coarse labels and the S1-S40-vs-coarse problem
(ACX-R2's topic). An embedding does **not** manufacture cross-station whistle labels. **Conclusion:
an embedding is necessary-not-sufficient for call_type; it should only be costed for call_type
*jointly* with ACX-R2's relabel budget, and call_type still ships only if a leave-station-out eval
clears non-trivial minority recall.**

## Trade-off table

| Path | New dep | Box compute | License work | Expected ceiling (TKW) | Honesty risk |
|---|---|---|---|---|---|
| **Do nothing (stay feature-only)** | none | none | none | Capped at TKW f1 ~0.43 (logreg); ecotype stays "SRKW-dominated, low-confidence TKW" | Lowest; already honest. Baseline. |
| **Feature-only + rebalance/threshold (ACX-R1)** | none (sklearn) | none (offline) | none | Modest lift over 0.43 from class-weighting / threshold-tuning; bounded by silhouette's morphology blindness | Low; measurable on existing split |
| **Embedding — best (Perch 2.0)** | **TensorFlow ≥2.20** (~1.6 GB, 33 pkgs) | extract ~5–50k windows once (CPU mins–tens-mins, or GPU); box run is a gate | **Apache-2.0 — clear**; derivative carries corpus CC-BY-SA | Highest; benchmark ROC-AUC 0.917–0.945 on orca ecotype (unverified on our split) | Moderate: must not quote benchmark ROC-AUC as our number; claim only the trained eval |
| **Embedding — cheapest license-clear torch (PANNs CNN14)** | **torch** (~950 MB, 12 pkgs) | extract once (CPU-feasible) | **CC-BY-4.0 — clear** | General-audio tier (~AVES-bio band, **not benchmarked on ecotype**), below Perch | Moderate + unverified benefit |
| **Embedding — cheapest compute (GMWM or YAMNet)** | TF (GMWM/YAMNet tiny) | trivial (≤4M params) | Apache-2.0 — clear | **Low** — GMWM 0.764/0.821 (worst transfer), YAMNet not benchmarked | Risk of paying the dep cost for little gain |
| **Embedding — NC models (BirdNET / AVES2 / NatureLM)** | TF or torch | varies | **STOP-to-O0**: NC + NC-SA conflicts with corpus CC-BY-SA | BirdNET ecotype 0.905/0.933 (strong) but **license-blocked** | High: shipping an NC-derived claim is a license violation |

## Recommendation for ACX-Q

1. **If O0 approves a learned-embedding cost, the recommended model is Perch 2.0
   (Apache-2.0, TensorFlow ≥2.20, 1536-dim, CPU-capable via `perch_v2_cpu`).** It is the
   top published performer on the exact orca-ecotype task, it is license-clear (no NC, no
   ShareAlike conflict with the corpus), and CPU inference now exists so a box GPU is a
   speed-up, not a hard requirement. Cheapest license-clear fallbacks if box compute or the
   1.6 GB TF dep is judged too heavy: **Perch 8 / SurfPerch** (Apache-2.0, ~24M, also strong),
   or **PANNs CNN14** (CC-BY-4.0, **torch**, if O0 prefers torch over TF — accepting a weaker,
   unverified general-audio benefit).
2. **Scope it to ecotype-TKW first.** Cost call_type embedding only jointly with ACX-R2's
   relabel budget; embedding alone will not lift call_type.
3. **Keep the downstream classifier on sklearn** (logreg/rf on the embedding), so the only
   new surface is the one-time embedding extractor + its dependency.

**Rejected alternatives (with reason):**
- **BirdNET V2.3** — strong on ecotype (0.905/0.933) and CPU-light, but **CC-BY-NC-SA-4.0**: NC
  blocks commercial use and its NC-SA conflicts with the corpus's CC-BY-SA → STOP.
- **AVES / BirdAVES** — torch-native and animal-pretrained, but **weaker on ecotype** (entangles
  TKW↔NRKW per tSNE) **and** AVES2 weights are CC-BY-NC-SA-4.0 (same STOP). The MIT label applies
  to code, not the weights — do not conflate.
- **GMWM (the actual whale model)** — Apache-2.0 and tiny, but the **worst** ecotype transfer in the
  benchmark; paying a dep cost for the weakest representation is not justified.
- **NatureLM-audio** — ~8B-param GPU-only audio-LLM and CC-BY-NC-SA-4.0: wrong tool (not a light
  embedder) and license-blocked.
- **VGGish / YAMNet** — Apache-2.0 and cheap, but legacy/general-audio with the lowest expected
  ceiling; only worth it if O0 wants the absolute-minimum-compute probe.

## EXACT gated items O0 must decide (none self-approved)

1. **New dependency.** Add a learned-embedding framework outside the locked numpy/scipy/sklearn/
   joblib stack: **TensorFlow ≥2.20 (~1.6 GB)** for the recommended Perch path, **or torch
   (~950 MB)** for the PANNs path, **or onnxruntime (~140 MB)** if an ONNX-exportable model is used.
   (Note: the charter says "torch"; the evidence says the best license-clear option is **TensorFlow** —
   O0 should pick the framework, not assume torch.)
2. **Weights download + its license.** Fetch the chosen pretrained weights **to the box,
   gitignored**, with a re-fetch pointer in-repo. Confirm the weights license: **Apache-2.0
   (Perch/GMWM/YAMNet) or CC-BY-4.0 (PANNs) = clear; BirdNET/AVES2/NatureLM = NC-SA = STOP.**
   Confirm the corpus CC-BY-SA-4.0 ShareAlike carries onto the embedding cache + trained classifier.
3. **Box compute / GPU time.** One-time embedding extraction over ~5,525 (and any added TKW/
   coarse-call) windows, then training the sklearn head — a human-gated box run. CPU is feasible
   for the recommended model; GPU is a speed-up.

**Honesty locks honored:** no claim here exceeds what a held-out eval on our leave-station-day-out
split would support; the benchmark numbers are flagged as off-split / few-shot / ROC-AUC and are
**not** quoted as our result; every model's license is flagged; the embedding path is **gated and
never self-approved.** ACX-R3 wrote only this file; no pipeline, served JSON, eval, or manifest was
touched.
