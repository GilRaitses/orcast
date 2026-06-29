# BAM window-level label manifests

This directory holds the small, in-repo contract that turns a license-cleared
annotation corpus into true window-level training labels. It is the
`to_strengthen` follow-on that `infra/acoustic/eval_report.json` flags as
STOP-to-O0. Heavy audio and raw annotation dumps stay in the box and are
gitignored. Only the manifest JSON and the eval report ship in-repo.

## Files

| File | Role | In git |
|------|------|--------|
| `window_label_manifest.schema.json` | JSON Schema for a manifest | yes |
| `EXAMPLE_window_label_manifest.json` | illustrative template, not real data | yes |
| `<head>_<corpus>_v1.json` | a real manifest, produced at BAM-DATA | yes, small |

## How a manifest is produced (BAM-DATA, O0-gated)

1. O0 approves a corpus fetch after license and privacy are verified per asset.
   DCLDE-2027 collated `Annotations.csv` is the OPEN anchor under CC-BY-4.0.
   Pod.Cast, OrcaHello, Watkins, and DORI-ONC stay STOP-to-O0 per BSW-R02.
2. Raw audio and raw annotations are mirrored to the box and gitignored.
3. `modeling/acoustic/windows.py` parses the annotation file into the common
   `Annotation` record, then `label_windows` assigns each 3 s window a label by
   time overlap with the annotations.
4. The aligned windows, per-clip `dataset` and `date` group keys, class balance,
   and any privacy scrubbing are written into a manifest that validates against
   the schema.

## Split policy

The default policy is `leave-station-day-out`. Whole `(dataset, date)` groups
are held out for test, so train and test never share a station-day. This is the
cross-station and cross-day generalization the v0 slice never measured, because
v0 used a temporal split inside a single session. `train_eval.grouped_train_test_split`
implements the hold-out and records the held-out groups in the eval report, so
the reported metric always carries the split it was measured on.

## Label QC requirements

Every real manifest records, under `label_qc`, the class balance, the number of
clips, annotations, and windows, and any annotations dropped for missing times
or ambiguous labels. Free-text moderator comments are never copied into a
manifest. OrcaHello comments in particular are treated as potential personally
identifying data per BSW-R02 and are excluded.

## Honest head limits

`modeling/acoustic/heads.py` is the registry of what a head is allowed to claim.
`presence`, `ecotype`, and `call_type` are eval-supported on the OPEN DCLDE
anchor. `single_vs_multiple` is eval-unsupported, because BSW-R02 finds no
license-clear corpus that provides verified source-count labels. The manifest
schema permits a `single_vs_multiple` manifest for diagnostic measurement only.
`assert_shippable` refuses to wire that head into the served `classification.json`.
Source count is an O0 decision, not a default.
