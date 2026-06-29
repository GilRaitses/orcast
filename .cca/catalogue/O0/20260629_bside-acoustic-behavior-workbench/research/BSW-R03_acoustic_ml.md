# BSW-R03 - Acoustic ML feasibility

> Read-only research finding (BSW-RESEARCH wave). Repo verified against `240570e`.
> Authored by explore agent 15e835f5; written by the BSW sub-orchestrator. No training, no downloads.

## Summary

- **No acoustic classifier exists in-repo today.** `modeling/` is Poisson/GAM encounter-intensity work (stdlib + numpy/scipy offline); `scripts/ml_services/dtag_*` and `behavioral_ml_service.py` are kinematic/DTAG tabular ML, not hydrophone spectrogram classification. `modeling/acoustic/` does not exist.
- **The current hydrophone UI is a static ONC spectrogram PNG**, not ML output. `HydrophoneSignalPanel.tsx` renders a proxied image; there is no classifier, confidence bar, or call-type label wired in.
- **OrcaHello's published SRKW detector is binary presence-only** (ResNet50 on mel spectrograms, OrcaHello-RAIL). External hackathon eval reports AU-PRC ~0.86 for ResNet50 vs ~0.27 for a VGGish baseline. It explicitly does **not** do call-type or source-count.
- **Honest demo target:** train a **small real model** (our weights, our eval) for **SRKW-call-like presence per 2-4 s window** on a fixed demo clip, reporting **real softmax/sigmoid confidence**. Optionally add **coarse call-type** (3-7 classes) if BSW-R02 data supports it.
- **Not achievable for the demo:** exact vocalizing-whale count, pod/matriline ID, ecotype (SRKW vs Bigg's), hydrophone-to-whale localization, or "how many orcas are out there" language. Polyphonic overlapping calls and count-from-single-hydrophone are open research problems.
- **Cautionary precedent:** the whale-behavior-analysis minGRU path reported 0% validation accuracy when labels collapsed to a single "Unlabeled" class; presentation docs claimed 66.8% validation accuracy that the repo could not reproduce.

## In-repo findings (cited)

### Modeling stack is temporal/statistical, not acoustic CNN
`modeling/studies/common.py` loads cached OrcaHello **detection timestamps** for Poisson/GAM studies, not audio features:

```23:29:modeling/studies/common.py
# In-region hydrophone coordinates (match the CAND waveset and Orcasound catalog).
STATION_COORDS: Dict[str, Tuple[float, float]] = {
    "orcasound_lab": (48.5583362, -123.1735774),
    "north_san_juan_channel": (48.591294, -123.058779),
    "andrews_bay": (48.5500299, -123.1666492),
    "haro_strait": (48.516, -123.152),
}
```

`modeling/requirements.txt` lists numpy/scipy/statsmodels only - no torch, tensorflow, librosa, or onnxruntime.

### ML services are DTAG/kinematic, not hydrophone classifiers
- `scripts/ml_services/dtag_data_processor.py` defines `DTAGAcousticEvent` with `call_type` fields but ingests BigQuery DTAG deployments, not hydrophone WAV corpora.
- `scripts/ml_services/behavioral_ml_service.py` trains sklearn `RandomForestClassifier` on tabular sighting/behavior features, not spectrograms.

### Deployed backend has no ML inference stack
`tools/deployment/aws/requirements.txt`: fastapi, boto3, requests, psycopg - no torch/onnxruntime. PyTorch appears only in `cloud-run-gemma/requirements.txt` (LLM path, unrelated).

### Hydrophone panel: static spectrogram only

```59:70:web/app/components/console/HydrophoneSignalPanel.tsx
          {data.enabled && data.spectrogram_url ? (
            <img
              src={data.spectrogram_url}
              alt="Recent ONC hydrophone spectrogram"
              className="hydrophone-spectrogram"
              loading="lazy"
            />
          ) : (
            <p className="muted" style={{ fontSize: "0.85rem" }}>
              {data.message ??
                "Live ONC spectrogram requires ONC_API_TOKEN on the backend. Station metadata shown."}
```

ONC relay (`src/aws_backend/sources/onc.py`) fetches pre-generated PNG spectrograms; no audio decode, no FFT, no model.

### OrcaHello is consumed as API detections, not run in-repo
`docs/methodology/methodology.tex` honesty guardrails: orcast does not run live ML; it consumes the OrcaHello detections API. No pod or ecotype identity is shown unless a source field provides it. `src/aws_backend/sources/orcahello.py` maps detections to `unreviewed_acoustic_candidate` vs `confirmed_acoustic_detection`; coordinates are **hydrophone position**, not whale GPS.

### Measured OrcaHello detector QC (in-repo, not our model)
`modeling/studies/reports/level0_detector.json` (MEASURED on cached moderated outcomes): Total cached records 1,359; overall moderator precision **0.7114**; ROC AUC (confidence vs confirmed/FP) **0.8794** (95% CI 0.856-0.902); d' 1.6197. This characterizes **OrcaHello's production detector**, not a model orcast trains.

### Annotation volume signals (for training feasibility)
- 334 cached reviewed OrcaHello annotation records across four stations; 761 acoustic detection history records at `haro_strait` (2020-2021).
- Pod.Cast: ~15 hours crowd-validated SRKW call annotations (CC BY-NC-SA 4.0).
- DCLDE-2027 (CC BY 4.0): 200k+ annotations; Strait of Georgia ULS alone has **1,263 SRKW** call/whistle annotations.

### minGRU cautionary tale (whale-behavior-analysis, external repo)

| Finding | Source |
|---------|--------|
| Validation accuracy **0.00** (469 samples, all predicted Unlabeled) | `whale-behavior-analysis/assets/validation/classification_report.txt` |
| Training metrics in presentation docs **not reproducible**; model collapsed to trivial class | `whale-behavior-analysis/whale_project_magniphyfactcheck.yaml` |

Lesson: small labeled sets + class imbalance + unverified metrics -> 0% usable model. BAM must publish held-out metrics before any HUD claim.

## Method survey (spectrogram CNN / embeddings / OrcaHello) with licenses

### 1. Spectrogram CNN classifiers (recommended primary path)
Pattern: WAV -> mel/power spectrogram -> CNN (ResNet18/50, EfficientNet) -> softmax.

| Reference | Task | Reported performance | License / notes |
|-----------|------|---------------------|-----------------|
| **OrcaHello SRKW Detector V1** | Binary SRKW call presence | External hackathon AU-PRC **~0.861** (ResNet50); VGGish baseline **~0.269** | **OrcaHello-RAIL**; mel 256x312, 4 s windows |
| **Bergler et al. 2019** (N. resident call types) | 12-class call type + noise | Test accuracy **96%**, mean **94%** (semi-supervised ResNet18; **514 labeled clips**) | Academic; Orcalab data permission |
| **ANIMAL-SPOT / ORCA-SPY** (Sci Rep 2023) | Binary orca vocalization segmentation | Mean detection accuracy **97.9%** (ResNet18) | Springer; does **not** count sources or classify call types in one pass |
| **Dalhousie Siamese SRKW study** (2024 thesis) | 17 call types (aug.) / 9 OOT | CNN **97.8%** / Siamese **98.5%** on augmented; OOT precision lower | Thesis; ESTIMATE generalization uncertain |

Best match for BAM charter. Train/fine-tune a small ResNet18/MobileNet on Pod.Cast + DCLDE SRKW segments. Align mel params with OrcaHello (256 mel, ~4 s) for transfer-learning option.

### 2. Audio embeddings + shallow classifier

| Model | Embedding | Pretraining | License | Whale relevance |
|-------|-----------|-------------|---------|-----------------|
| **VGGish** (AudioSet) | 128-D | YouTube-scale | Code Apache 2.0; weights CC BY 4.0 | OrcaHello hackathon baseline; weak alone (AU-PRC ~0.27) |
| **BirdNET** | logits + emb | bird vocalizations | Code MIT; models CC BY-NC-SA 4.0 | Wrong taxa; generic baseline only |
| **Perch / Perch 2.0** (Google) | 1536-D | 15k species incl. some marine | Apache 2.0 (code) | Strong transfer; research-only for orcast pilot |
| **AVES / AVEX** (Earth Species) | 768-D HuBERT-style | animal audio | MIT (AVEX) | Good for few-shot linear probe; needs TF/torch |

Freeze embedding -> linear probe / small MLP. Works with few labels but heavy deps. Recommended **fallback** only.

### 3. OrcaHello detection model (external, production reference)
ResNet50 + custom head on mel spectrogram (1x256x312); binary P(SRKW call present) per segment; thresholds global 0.6/local 0.5; license **OrcaHello-RAIL** (conservation restrictions, no MMPA violation, no captive-industry use). Explicit limitations: no fine-grained call type; no other species without retrain; station/environment bias.

**Critical for BAM:** Calling the OrcaHello API or running their unchanged weights is **not** "community-annotation-trained model" per charter. Acceptable paths: (1) train our own small CNN on open annotations (preferred); (2) fine-tune OrcaHello ResNet50 on held-out community labels with separate eval (still RAIL-bound). Do **not** present OrcaHello API confidence as BAM model output.

## HONEST achievable target for the demo (what IS achievable)

### Primary target (recommended ship bar)
**Task:** Binary **SRKW-call-like vocalization present / absent** per analysis window (2-4 s, hop ~1 s) on the fixed demo slice clip.

**HUD claim (exact wording template):**
> "Acoustic classifier (v0): **SRKW-call-like sound** in this window - confidence **{p}%** (held-out test F1 **{f1}**). Hydrophone location only; **not** whale count or pod ID."

**To call this achieved:** reproducible pipeline in `modeling/acoustic/` (feature -> train -> eval -> export); held-out test set with documented split; on demo clip a **real forward pass** output; confidence = model posterior (not scripted).

### Stretch target (only if label census supports it)
Coarse call-type / call-family among **K <= 7** classes with **>= 50 training examples each**. HUD add-on shows class + macro-F1. Do not ship without meeting per-class support thresholds on test split.

### What "real trained model" means here
Weights trained/fine-tuned on **open-licensed** annotation corpora (R02); eval report checked into `infra/acoustic/`; segment-level predictions JSON with `model_version`, `train_run_id`, `confidence`, `class_probs`.

## What is NOT achievable (explicit anti-overclaim list)

| Claim | Why not | Demo rule |
|-------|---------|-----------|
| "N orcas vocalizing" / source count | Single hydrophone, overlapping calls, no localization labels; polyphonic AED unsolved at demo scale | Never show a count integer from the classifier |
| Pod / matriline / individual ID | Requires DTAG or multi-hydrophone beamforming + large ID corpus | Out of BAM scope |
| Ecotype (SRKW vs Bigg's) | Needs ecotype-labeled data + careful eval | Do not show ecotype unless held-out F1 meets bar |
| Whale GPS / map pin from acoustic | Detection coords = hydrophone | Keep hydrophone marker only |
| "Confirmed orca present" from ML alone | OrcaHello unreviewed ~61% precision at Orcasound Lab | Use "call-like vocalization detected" language |
| Production OrcaHello parity | Their model trained on years of data | Cite their AU-PRC as external reference, not ours |
| Live fleet-wide real-time classification | App Runner has no ML stack | Demo slice only |
| 100% accuracy / "AI identifies whales" | Forbidden claim pattern (`CLAIM_BOUNDARIES.md`) | Bind to measured F1 + confidence |

## Eval plan + expected metric ranges (clearly labeled estimates)

**Dataset:** DCLDE SRKW calls (CC BY 4.0) + Pod.Cast (NC-SA, pending O0) + Orcasound negatives. Segment extraction to 4.0 s mel (256 mel, 16-20 kHz). Negatives: random no-KW segments, boat/engine, other mammals.

**Split (avoid leakage):** Train 70% / Val 15% / Test 15%, grouped by **recording file / day / deployment** (never split windows from one file across splits). Prefer **held-out stations or months** for test.

**Metrics:** binary - precision, recall, F1, confusion, AU-PRC; multi-class - per-class P/R/F1, macro-F1, confusion; calibration (reliability/ECE optional); failure-mode list (FP sources with counts).

**Expected ballpark (ESTIMATES, first small model ~500-3000 segments):**

| Task | Metric | In-distribution test | Cross-station test |
|------|--------|----------------------|--------------------|
| Binary SRKW-call presence (small CNN / ResNet18 ft) | F1 | **0.65-0.85** | **0.55-0.75** |
| Binary (sklearn RF on log-mel stats) | F1 | **0.55-0.70** | **0.45-0.60** |
| Coarse 5-7 class call type | Macro-F1 | **0.40-0.65** | **0.30-0.50** |
| Source count | - | **Not evaluable** | **Do not report** |

External anchors (MEASURED elsewhere): OrcaHello ResNet50 AU-PRC ~0.861 vs VGGish ~0.269; in-repo OrcaHello moderator precision 0.711, ROC AUC 0.879. **If held-out test F1 < 0.50 for binary task, demo shows "low confidence / experimental classifier" and withholds call-type claims entirely.**

## Recommendations with cost + standin-free fallback (incl. dependency decision)

| Option | Training deps | Inference deps | Demo fit | Standin-free fallback |
|--------|--------------|----------------|----------|----------------------|
| **A (recommended)** | PyTorch + librosa (offline `modeling/requirements.txt`) | **onnxruntime** on App Runner OR precomputed JSON from train script | Best accuracy / charter alignment | Precompute segment predictions at BAM-TRAIN; serve via `/api/acoustic/classify` reading JSON + ONNX hash - no canned labels |
| **B (lighter)** | scikit-learn + librosa/numpy | none (joblib in S3) | Weaker but deployable on current stack | Same precompute path; confidence = `predict_proba` |
| **C (not recommended primary)** | TensorFlow + Perch/AVES | TF or heavy torch | Research / few-shot | Linear probe weights only; still real inference |

**Do not add PyTorch to App Runner** unless live inference is required. **Do not add onnxruntime-web** to the browser unless BSH perf budget explicitly accepts it.

**Option A detail:** `modeling/acoustic/` mel extract + ResNet18 train + export ONNX (~5-15 MB); train on box, emit `eval_report.json` + `predictions_demo_slice.json`; FastAPI route `POST /api/acoustic/classify` with onnxruntime (COST ~50-150 MB image, ~50-200 ms CPU/window) or precomputed-JSON fallback (HUD still shows real `confidence`).

**Forbidden anti-patterns:** scripting `{class: "SRKW", count: 3}`; piping OrcaHello API confidence into BAM HUD as "our classifier"; uniform 33% probs (minGRU failure); BirdNET "whale" logits without SRKW fine-tune.

**HUD integration (BSH + BAM):** BSH computes spectrogram once (WebAudio FFT); BAM consumes same mel tensor offline or via API. Overlay: shaded window + label + numeric confidence + eval-report version caption (`model_version`, `eval_test_f1`, `held_out_station`).

## Open questions / overclaim-risk flags for O0

1. **R02 label census:** per-class counts and licenses not yet in repo. Blocker for stretch call-type target.
2. **Demo slice selection:** which exact WAV/station/time? Must overlap enough positive windows.
3. **Fine-tune OrcaHello vs train-from-scratch:** RAIL allows use but derivative weights inherit restrictions; does "community annotations" require open-only training?
4. **ONC audio access:** historical ONC audio may need token/agreement; Orcasound S3 may suffice.
5. **Cross-lane coupling:** BRE reenactment must not imply N whales based on classifier output.
6. **Claim boundary gap:** `CLAIM_BOUNDARIES.md` has no ALLOWED row for acoustic classification yet - O0 must add before public demo language.
7. **Negative-class dominance:** require balanced eval and report prevalence baseline (inverse minGRU failure).

## Sources

### In-repo
- `modeling/studies/common.py`, `modeling/requirements.txt`, `modeling/studies/reports/level0_detector.json`
- `scripts/ml_services/dtag_data_processor.py`, `scripts/ml_services/behavioral_ml_service.py`
- `src/aws_backend/routers/onc.py`, `src/aws_backend/sources/onc.py`, `src/aws_backend/sources/orcahello.py`
- `web/app/components/console/HydrophoneSignalPanel.tsx`
- `docs/ml/ORCA_ML_INTEGRATION.md`, `docs/devpost/model-card-lite.md`, `docs/methodology/methodology.tex`
- `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/{BSW-ACOUSTIC-ML_CHARTER.md,BSW-SPECTRO-HUD_CHARTER.md}`
- `.cca/catalogue/O0/20260627_bside-build/BSIDE_CHARTER.md`, `.cca/CLAIM_BOUNDARIES.md`
- `/Users/gilraitses/whale-behavior-analysis/assets/validation/classification_report.txt`, `whale_project_magniphyfactcheck.yaml`

### External

| Resource | URL | License |
|----------|-----|---------|
| OrcaHello SRKW Detector V1 | https://huggingface.co/orcasound/orcahello-srkw-detector-v1 | **OrcaHello-RAIL** |
| OrcaHello eval methodology | https://github.com/orcasound/aifororcas-livesystem/blob/main/ModelEvaluation/readme.md | repo MIT |
| Orcasound open data | https://registry.opendata.aws/orcasound/ | **CC BY-NC-SA 4.0** |
| DCLDE/Palmer 2025 corpus | https://www.nature.com/articles/s41597-025-05281-5 | dataset **CC BY 4.0** |
| Bergler 2019 call-type CNN | https://www5.informatik.uni-erlangen.de/Forschung/Publikationen/2019/Bergler19-DRL.pdf | Academic / Orcalab permission |
| ORCA-SPY / ANIMAL-SPOT | https://link.springer.com/article/10.1038/s41598-023-38132-7 | Springer |
| VGGish | https://github.com/tensorflow/models/tree/master/research/audioset/vggish | Code Apache 2.0; weights CC BY 4.0 |
| Perch | https://github.com/google-research/perch | Apache 2.0 |
| AVEX / AVES | https://github.com/earthspecies/avex | MIT |
| BirdNET | https://github.com/birdnet-team/birdnet | Code MIT; models CC BY-NC-SA 4.0 |

**Verdict:** Ship a real, small, eval-documented binary presence classifier with honest confidence on a fixed demo clip. Treat call-type as optional stretch. **Do not ship count, ecotype, or pod claims.** Gate public wording on measured held-out F1 and update `CLAIM_BOUNDARIES.md` before demo capture.
