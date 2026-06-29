# ACX Path B (Perch 2.0) — O0 decision (batch the box run)

- Lane `BSWR-ACX` (acoustic-heads-strengthen). Decider: O0.
- Repo base pin `61ba1d69ee36cf605f7ba741bdaa1defa8762834`. No commit.

## Context

ACX-B/TRAIN/ADV is complete. Path A (feature-only, offline) is an honest
**NO-SHIP**: 5-seed leave-station-OUT median TKW f1 0.7037 / recall 0.8027 but
SRKW f1 0.6934, below the fixed 0.84 guard. The apparent TKW jump is the
leave-station-OUT prior inversion (held-out folds are TKW-heavy AMAR recorders),
bought by degrading SRKW; the three-part bar correctly refuses it. Outcome stands:
no reliable lift, ecotype wording unchanged, `classification.json` untouched.

Path B (Perch 2.0 learned embeddings into the same head/protocol) is the only
remaining shot at a genuine ecotype lift. The hard license guard is CLEAR (Perch
2.0, perch-hoplite, perch/chirp, TF/tf-hub/kagglehub all Apache-2.0; numpy/scipy/
sklearn BSD; ShareAlike carries onto the derivative with no conflict). It needs a
box: TF ~2.20 (no Python-3.14 wheel), a kagglehub weights download, and an ffmpeg
re-fetch + forward pass over ~5,525 windows, GPU recommended.

## Decision

**Fold the Path B box run into the single batched BSWR host window**, alongside the
OCN + ENV GPU captures, the PRF-ACCEPT A/B, and the PRF Option-2 `--smoke`. It is
pre-approved in principle at ACX-Q and license-clear, but it is a host/compute
spin-up, so it runs under the same batched, operator-opened host gate — NOT
standalone and NOT now. The box stays down until that window opens.

When the window opens, the staged runner extracts the embedding cache on the box
and evaluates Path B on the identical 5-seed leave-station-OUT protocol; the
MEDIAN decides against the same fixed bar (TKW f1 > 0.434 AND recall >= 0.478 AND
SRKW f1 >= 0.84).

- If Path B clears the bar -> proceed to the `ACX-ACCEPT` `classification.json`
  contract/count-basis gate (a separate O0 decision: synchronized update to
  `classes`, `honesty.not_claimed`, `spawnCountBasis`, exact HUD wording).
- If Path B also misses -> the Path A honest NO-SHIP outcome is final; ecotype
  wording unchanged, `classification.json` untouched, lane closes remediated with
  a measured negative result.

The `ACX-ACCEPT` contract gate is moot until/unless Path B clears.
