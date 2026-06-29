# ACX Path B verdict (Perch 2.0 box run)

> ACX sub-orchestrator Path-B ACCEPT, attempted inside the batched BSWR host
> window by the BSWR host-window sub-orchestrator on the GPU box
> (aimez-gpu-capture, i-0e66ac03c729ebe02, Tesla T4 15 GB, Python 3.10.12, ffmpeg
> present). No commit. `web/public/hydrophone/slice/classification.json` NOT touched.

## Verdict: BLOCKED — Path B could not run. Returned to O0. No fabricated numbers.

Path B (Perch 2.0 learned embeddings into the same head/protocol) could not be
executed on the GPU box because its staged preconditions are absent from the box
and from all account S3 buckets, and a required credential is missing. Per the
dispatch escalation rule, this item is STOPPED and the exact blockers are returned
to O0 rather than improvised around. The local `eval_report_dclde_v2.json` is left
unchanged with Path B `not_run` (the honest state); no Path B metrics were
synthesized.

## Blockers (each verified on the box, 2026-06-29)

1. `features_v1.npz` is ABSENT. The staged 5,525-window feature + row-identity
   cache that the entire Path B protocol must align to 1:1 by `(dataset, soundfile,
   t0)` does not exist on the box and is not in any S3 bucket in the account.
   - Box: `sudo find / -name "*.npz"` returns only matplotlib/numpy sample files in
     the unrelated `pax_cv` venv. No `features_v1.npz`, no `perch_embeddings_v1.npz`.
   - S3: searched `198456344617-us-west-2-orcast-aws-backend-reports`,
     `aimez-data`, and the other account buckets for `feature|perch|dclde|npz`. No
     match. `aimez-data/orcast/` holds only the BRE/BSS biologging `.mat`/`.bin`
     data, not the ACX acoustic features.
   - The dispatch presupposes this file is staged ("aligned 1:1 to features_v1.npz
     rows"). It lived only in the ACX lane's original local environment and was
     never persisted to the box or S3 (PROGRAM lock #4 routes heavy assets to S3,
     but this one was not uploaded).

2. No Kaggle credentials on the box, and the host-window sub-orchestrator does not
   hold them. `~/.kaggle/kaggle.json` is missing, `KAGGLE_USERNAME` / `KAGGLE_KEY`
   are unset. `kagglehub.model_download` of the Perch 2.0 weights authenticates
   against Kaggle and cannot proceed without a credential. This is precisely the
   missing-credential case the dispatch says to STOP on. Even a full features
   rebuild (blocker 1) could not complete Path B without this.

3. Supporting gaps (each would also need resolving): no TensorFlow env on the box
   (TF ~2.20 + perch-hoplite must be installed fresh on Python 3.10), the
   `modeling/acoustic` code is not on the box (the render `render.sh` syncs only
   `web/`), and the DCLDE-2027 `Annotations.csv` needed to rebuild features is not
   on the box (the GCS directory listing returns 404, and only specific object
   paths are fetchable).

## Why I did not improvise a rebuild

Reconstructing `features_v1.npz` from scratch (fetch `Annotations.csv`, re-fetch
and featurize 5,525+ audio windows from the public GCS bucket, then re-derive the
row identity) is a large corpora pipeline well beyond the staged "extract
embeddings over the already-staged windows" plan, and it would still not clear the
Kaggle-credential blocker for the Perch weights. A rebuild also risks silently
shifting the row-identity basis the Path A baseline was computed against if any
audio fetch 404s or drops rows. Improvising this is outside the ACCEPT mandate and
the dispatch's STOP-on-missing-credential rule.

## License re-check status

Not reached. The license re-check is to be run against the actual downloaded
artifacts; no artifact was downloaded (blocker 2), so there is nothing to re-check.
The pre-download license guard recorded by the lane (Perch 2.0 weights, perch-
hoplite, perch/chirp, TF / tf-hub / kagglehub all Apache-2.0; numpy/scipy/sklearn
BSD; CC-BY-SA-4.0 corpus ShareAlike travels onto the derivative with no conflict)
is unchanged and remains CLEAR in principle. The binding re-check on the real
downloaded weights is still pending and is deferred until the weights can be pulled.

## Standing ACX result (unchanged by this attempt)

Path A (feature-only, offline, already computed) remains the honest NO-SHIP:
5-seed leave-station-OUT median TKW f1 0.7037, TKW recall 0.8027, SRKW f1 0.6934 —
SRKW f1 is below the fixed 0.84 guard, so the three-part bar refuses it. With Path
B blocked, no path clears the bar in this window. `overall.ships=false`, ecotype
wording unchanged, `classification.json` untouched. The `ACX-ACCEPT` contract gate
remains moot.

## What O0 must supply for Path B to run in a future window

1. The original `features_v1.npz` staged to the box or S3 (preferred — preserves
   the exact row identity the Path A baseline used), OR an explicit authorization
   and budget to rebuild the full corpora -> features pipeline on the box.
2. Kaggle credentials (`~/.kaggle/kaggle.json` or `KAGGLE_USERNAME`/`KAGGLE_KEY`)
   on the box so kagglehub can download the Apache-2.0 Perch 2.0 weights.
3. With those two in place, the staged runners (`perch_embed.py` then
   `train_dclde_v2.py`) plus a TF ~2.20 + perch-hoplite install will execute the
   embedding extraction and the identical 5-seed leave-station-OUT evaluation; the
   median decides against the fixed bar, and the license re-check runs on the real
   weights before use.

## Disposition

ACX Path B STOPPED at the missing-precondition / missing-credential blocker and
returned to O0. No commit, no `classification.json` edit, no fabricated Path B
metrics, no `eval_report_dclde_v2.json` change. Weights + embeddings would stay on
the box and gitignored when the run becomes possible.
