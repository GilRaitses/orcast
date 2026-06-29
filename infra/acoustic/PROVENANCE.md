# BAM acoustic classifier — provenance, licenses, attribution

Real, reproducible binary SRKW-call-presence classifier (the "acoustic
silhouette" of the sound). numpy + scipy + scikit-learn only (no torch, no
librosa). Heavy artifacts (raw `.ts`, decoded `.wav`, model `.joblib`) are
gitignored and re-fetched; the small real inference JSON + eval report ship
in-repo.

## Data assets

| Asset | Source | License | Attribution | Honesty |
|-------|--------|---------|-------------|---------|
| Orcasound Lab HLS audio (session `1629941419`, 2021-08-25 S10 L-pod bout) | `s3://audio-orcasound-net/rpi_orcasound_lab/hls/1629941419/` | CC BY-NC-SA 4.0 | "Orcasound - orcasound.net" | measured |

NonCommercial use authorized by owner sign-off (`SIGN_OFF.md` decision 1).
Derived model + features inherit NC + ShareAlike. The classifier weights are a
derivative of NC-SA audio; any box-published artifact must carry NC-SA terms.

## What the model is (honest scope)

- Task: **binary SRKW-call presence vs absence** per 3 s window (1.5 s hop).
- Reported as **estimate + confidence** with a held-out eval. See `eval_report.json`.
- Labels are **bout-level weak labels**: positives = windows inside the human +
  OrcaHello confirmed bout (`210825_1922-2007_OS_SRKW_L`); negatives = pre-bout
  ambient. The held-out split is **temporal within each pool** so train/test
  windows never overlap.

## What the model is NOT (anti-overclaim)

Not shipped, and must never be claimed: whale **count**, **pod / individual
ID**, **ecotype** (SRKW vs Bigg's), **call type**, **single vs multiple
callers**. The smallest real model that validates was trained this run; the
multi-category heads (call-type, single-vs-multiple) the owner sign-off
contemplates require window-level annotated corpora (Pod.Cast / OrcaHello /
DCLDE-2027) aligned to audio. That fetch + alignment is a **STOP-to-O0**
follow-on, not fabricated here.

## Honest eval headline (and its caveat)

The held-out metrics are high (selected RF model F1 ~0.99, AUPRC ~1.0 on the
temporal test slice). This is an **optimistic, partly-confounded** presence
estimate, not a pure per-call detector: positives and negatives are different
times of the same session, so the model can separate them partly on
session-level acoustic differences. This caveat travels in `eval_report.json`
and in `classification.json` and must travel into any HUD wording. HUD says
"estimated: SRKW call present (confidence X)", never a count or ID.

## Files

| File | Role | In git? |
|------|------|---------|
| `modeling/acoustic/fetch_orcasound_clip.py` | fetch + decode real audio | yes |
| `modeling/acoustic/features.py` | scipy log-mel silhouette features | yes |
| `modeling/acoustic/train_eval.py` | train + honest held-out eval | yes |
| `modeling/acoustic/infer_demo.py` | precomputed real inference JSON | yes |
| `modeling/acoustic/requirements.txt` | pinned offline deps | yes |
| `infra/acoustic/eval_report.json` | real held-out metrics + confounds | yes |
| `web/public/hydrophone/slice/classification.json` | precomputed inference (BRE/integrator contract) | yes (small) |
| `infra/acoustic/data/**` | raw `.ts` + decoded `.wav` | no (box) |
| `infra/acoustic/models/srkw_presence_v0.joblib` | weights + scaler | no (box) |

## Reproduce

```
python3 -m pip install -r modeling/acoustic/requirements.txt   # numpy scipy scikit-learn joblib
python3 modeling/acoustic/fetch_orcasound_clip.py
( cd modeling/acoustic && python3 train_eval.py && python3 infer_demo.py )
```

## Box pointers (heavy artifacts)

Suggested S3 home (mirrors the render-host reports bucket pattern):
`s3://198456344617-us-west-2-orcast-aws-backend-reports/bsw-acoustic/`
holding `data/wav/*.wav`, `models/srkw_presence_v0.joblib`. Re-fetch raw audio
from the public Orcasound bucket above (no credentials, `--no-sign-request`).
