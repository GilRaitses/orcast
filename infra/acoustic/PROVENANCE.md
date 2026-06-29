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
| `modeling/acoustic/features.py` | scipy log-mel silhouette features (+ segment + start-aligned helpers) | yes |
| `modeling/acoustic/windows.py` | annotation to window-level label alignment + corpus parsers | yes |
| `modeling/acoustic/heads.py` | honest head registry + multiclass eval + anti-overclaim guard | yes |
| `modeling/acoustic/train_eval.py` | binary presence train + gated window-level head harness | yes |
| `modeling/acoustic/build_dclde_salish.py` | offline window-level label stats (no audio, no train) | yes |
| `modeling/acoustic/fetch_features_dclde.py` | segment-targeted audio fetch + feature cache (BY-SA) | yes |
| `modeling/acoustic/train_dclde.py` | cross-station presence + ecotype train (CPU sklearn) | yes |
| `modeling/acoustic/call_type_diag.py` | call_type diagnostic (pulsed_call vs whistle), not shipped | yes |
| `modeling/acoustic/infer_demo.py` | precomputed real inference JSON | yes |
| `modeling/acoustic/requirements.txt` | pinned offline deps | yes |
| `infra/acoustic/eval_report.json` | v0 binary presence metrics + confounds (live contract) | yes |
| `infra/acoustic/eval_report_dclde_v1.json` | v1 cross-station presence + ecotype eval (BY-SA) | yes (small) |
| `infra/acoustic/manifests/*.json` + `README.md` | window-level label manifest schema + split policy | yes (small) |
| `web/public/hydrophone/slice/classification.json` | precomputed inference (BRE/integrator contract) | yes (small) |
| `infra/acoustic/data/**` | raw `.ts` + decoded `.wav` + fetched corpora | no (box) |
| `infra/acoustic/models/*.joblib` | weights + scaler | no (box) |

## Window-level corpora follow-on (GATED, STOP-to-O0)

This is the `eval_report.json` `to_strengthen` path. The pipeline to ingest it
is scaffolded and runs offline, but no corpus has been fetched and no head has
been trained. Both are O0 gates.

### Candidate corpora and license verdict (from BSW-R02)

| Corpus | Labels | License | Verdict |
|--------|--------|---------|---------|
| DCLDE-2027 killer-whale dataset (collated + per-provider originals + audio) | ecotype, KW, S1-S40 call catalog | **CC-BY-SA-4.0** (root legalcode; see license ruling below) | OPEN with ShareAlike, the anchor |
| Pod.Cast rounds | binary SRKW presence | CC-BY-NC-SA 4.0 | STOP-to-O0 (NC+SA) |
| OrcaHello | presence outcome, free-text comments | CC-BY-NC-SA 4.0 | STOP-to-O0 (NC+SA, comment PII) |
| Watkins | global ecotype signal types | non-commercial / unclear | STOP-to-O0 |
| DORI-ONC amateur | species/ecotype, pre-release | CC-BY (pre-release) | STOP-to-O0 |

NC-AUTHORIZED applies only to the already-shipped Orcasound Lab demo audio per
`SIGN_OFF.md`. A STOP-to-O0 corpus must not be trained or shipped until O0
clears its license. `modeling/acoustic/heads.py` enforces this in code via
`assert_shippable`.

### Heads the corpora honestly support (measured, not assumed)

| Head | Backing corpus | Cross-station eval | HUD-claimable |
|------|----------------|--------------------|---------------|
| `presence` | DCLDE window-level (12 Salish stations) | macro-F1 0.67 | yes |
| `ecotype` (SRKW vs Bigg's/TKW) | DCLDE OPEN | macro-F1 0.65 (TKW F1 0.43) | yes |
| `call_type` | DCLDE originals (S1-S40 only) | macro-F1 0.43, whistle F1 0.0 | **no, refused** |
| `single_vs_multiple` | none | n/a | no, refused |

These verdicts changed after inspecting the REAL labels (not the BSW-R02
preview). The originals' `call_type` field is the SRKW **S1-S40 stereotyped-call
catalog** (S01/S04/S44/...), which the charter forbids claiming; the only coarse
signal labels (`signal_type` W/CK/BZ + Raven "whistle") are extremely sparse and
mostly single-station. A diagnostic coarse contrast (pulsed_call vs whistle)
collapses cross-station (whistle recall 0.0), so `call_type` is **not shipped**
and `heads.assert_shippable` refuses it. It is `to_strengthen`: a scoped
CK/W/BP relabel budget across providers, or an O0-costed learned embedding (the
129-dim log-mel silhouette is presence-oriented and too weak for call morphology).

`single_vs_multiple` stays blocked because no license-clear corpus has verified
source-count labels. Both blocked heads stay in the registry as explicit gaps,
never silently dropped, never shipped without O0 approval. Coarse ecotype
(SRKW vs Bigg's) is the honest ceiling for "who"; presence is the honest ceiling
for "what" — never a count, pod/individual ID, or S1-S40 catalog call.

### License ruling (binding): CC-BY-SA-4.0

The DCLDE-2027 killer-whale dataset ships a root license file **named**
`CC-BY-4.0.txt` whose **content is the CC BY-**SA**-4.0 legalcode**
("Attribution-ShareAlike 4.0 International"). This conflict was escalated; O0
ruled to **PROCEED under the conservative bundled legalcode, CC-BY-SA-4.0**
(operator approved, 2026-06-29). ND is absent, so a trained-model derivative is
permitted.

**Binding terms — ShareAlike + attribution travel with EVERY derivative**, both
boxed (weights, feature cache, segment audio) and in-repo (`eval_report_dclde_v1.json`,
any inference JSON):

- License: **CC-BY-SA-4.0**
- Attribution: *DCLDE-2027 killer whale annotations (DFO Canada / NOAA NCEI), CC-BY-SA-4.0*
- DOI: `https://doi.org/10.25921/15ey-mh50`
- Source: `https://storage.googleapis.com/noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales/`

The license file is mirrored in the box as `CC-BY-SA-4.0.txt` (the misnamed
original is preserved alongside). No per-provider license overrides exist; all
providers inherit this root license (verified — provider roots carry no LICENSE).
The model `.joblib` files and `eval_report_dclde_v1.json` carry the BY-SA license
+ attribution string inline.

### Fetched: DCLDE-2027 Salish subset (O0-approved 2026-06-29)

| Asset | Source | License | Size | Box (gitignored) |
|-------|--------|---------|------|------------------|
| Collated `Annotations.csv` (killer whales) | `.../Annotations.csv` | CC-BY-SA-4.0 | 50.5 MB, 207,574 rows | `data/corpora/dclde-2027/` |
| VFPA Boundary Pass originals `annot_BP_man_det.csv` | `.../vfpa/annotations/` | CC-BY-SA-4.0 | 276 KB, 2,032 rows | `.../originals/vfpa/` |
| SMRU Lime Kiln originals `annot_LimeKiln-Encounters_man_det.csv` | `.../smru/annotations/` | CC-BY-SA-4.0 | 184 KB, 1,471 rows | `.../originals/smru/` |
| SIMRES Tekteksen Raven `.selections.txt` (143 tables) | `.../simres/annotations/` | CC-BY-SA-4.0 | 1.6 MB | `.../originals/simres/` |
| Segment-targeted audio features (5,525 × 129 windows) | per-window ffmpeg HTTP input-seek (NOT whole-file) | CC-BY-SA-4.0 derivative | `features_v1.npz` 1.x MB | `data/corpora/dclde-2027/` |

Pod.Cast, OrcaHello, Watkins, DORI-ONC were NOT fetched (remain STOP-to-O0).
Free-text `comments` columns in the originals are NEVER parsed (R02 PII). The
per-provider originals' `kw_ecotype`/`call_type`/`signal_type` are read; comments
are dropped.

**Audio fetch was segment-targeted, not whole-file.** For each sampled
annotation a single 3 s window is pulled via `ffmpeg -ss <t> -i <https-url> -t 3`,
which range-requests only that slice (a 184 MB WAV or 40 MB FLAC seek completes in
1–3 s without downloading the file). Audio bytes are transient: decoded to 48 kHz
mono, hashed into the 129-dim log-mel feature, and the temp WAV deleted. Only the
feature matrix is cached. A whole-file fetch of the 2,019 annotated files would
have been ~143 GB; the segment feature cache is ~1 MB.

**Scope and data-availability findings.** Restricted to Salish `Dataset` keys
with audio actually present in the bucket: OrcaSound (orcasound_lab, bush_point,
port_townsend), JASCO_VFPA (BoundaryPass, HaroStraitNorth/South), JASCO_VFPA_ONC
(StraitofGeorgia), SMRU (LimeKiln), SIMRES (Tekteksen), DFO_WDLP (StrGeoN1,
StrGeoS1, SwanChan). **StrGeoN2 (AMAR617) and StrGeoS2 (AMAR779) are
annotation-only — their audio is 404 in the bucket — so they are dropped from the
audio-backed dataset.** Non-Salish providers (DFO_CRP open coast, ONC Barkley
Canyon, SIO WA outer coast, UAF Alaska) are excluded.

### Trained: bam-dclde-salish-v1 (honest cross-station/cross-day eval)

CPU sklearn (logreg + RandomForest) over the 129-dim scipy log-mel silhouette.
No torch, no new deps. Split: **leave-station-day-out** across 92 station-days
(minority TKW held in both train and test). Full report:
`infra/acoustic/eval_report_dclde_v1.json`. Weights → box
(`models/bam_presence_v1.joblib`, `bam_ecotype_v1.joblib`, BY-SA inline).

| Head | Classes | Test windows | Honest metric | Framing |
|------|---------|--------------|---------------|---------|
| `presence` | background / present | 1,841 | macro-F1 **0.67**, AUPRC 0.76 | real cross-station; far below v0's confounded within-session 0.99, as expected |
| `ecotype` | SRKW / TKW | 1,115 | macro-F1 **0.65**; SRKW F1 0.87, **TKW F1 0.43** | SRKW vs Bigg's; SRKW-dominated, TKW low-confidence |
| `call_type` (diagnostic) | pulsed_call / whistle | 154 | macro-F1 **0.43**, **whistle F1 0.0** | NOT shipped; S1-S40 forbidden + coarse labels too sparse → `to_strengthen` |

Honest headline: a real per-window presence + ecotype model that generalizes
*modestly* across stations. The drop from v0's 0.99 is the point — v0 was a
single-session confound; this is true cross-station generalization. `to_strengthen`:
the log-mel silhouette is presence-oriented and weak for ecotype TKW and any call
morphology; a learned audio embedding (torch, new dep — an O0/cost decision) is
the path to lift TKW and enable a coarse call_type head.

Reproduce offline (no audio, no train) the label stats:
`python3 modeling/acoustic/build_dclde_salish.py`. Re-fetch + train:
`python3 modeling/acoustic/fetch_features_dclde.py && python3 modeling/acoustic/train_dclde.py`
then `python3 modeling/acoustic/call_type_diag.py` for the diagnostic.

### classification.json contract status

**Unchanged this run.** The live `web/public/hydrophone/slice/classification.json`
is the v0 presence contract (BRE/integrator) on the Orcasound Lab demo clip.
bam-dclde-salish-v1 is a *different* model on a different corpus; promoting it (or
adding an ecotype field) means re-running inference on the served clip, which is
the ACCEPT step and a count-basis/contract change. Per O0, that is coordinated
separately — presence-only spawn semantics are not silently changed here. The new
model ships only as boxed weights + the in-repo `eval_report_dclde_v1.json`.

### Box layout for fetched corpora (re-fetch pointers)

Raw corpus audio and raw annotation files mirror to the box under
`s3://198456344617-us-west-2-orcast-aws-backend-reports/bsw-acoustic/corpora/<corpus>/`
and decode locally into `infra/acoustic/data/corpora/<corpus>/` (gitignored).
The small window-level manifest under `infra/acoustic/manifests/` is the only
in-repo artifact that points back at them.

### How to launch once O0 clears a fetch

1. BAM-DATA, with O0 go, fetches the OPEN DCLDE collated CSV plus the matched
   Salish-relevant provider audio, mirrors raw to the box, and writes a manifest
   validating against `manifests/window_label_manifest.schema.json`.
2. BAM-TRAIN, with O0 go, runs
   `python3 modeling/acoustic/train_eval.py --head-manifest infra/acoustic/manifests/<file>.json`
   on the box dev host. It trains a supported head with a leave-station-day-out
   split and emits an honest multiclass eval. Weights go to the box.
3. The served `classification.json` is extended only after O0 reviews the eval,
   and only with fields a supported head's held-out eval backs.

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
