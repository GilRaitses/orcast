# BSW-ACOUSTIC-ML charter (community-annotation acoustic classifier + MLops)

- Lane code: **BAM** (under family BSW)
- Owner: O0 dispatches; a background sub-orchestrator runs the gated waves.
- Type: research-first (grounded by BSW-RESEARCH R01/R02/R03/R05/R14); pipeline/train/eval gated.
- `repo_state_verified_against`: origin/main `240570e961913fb610c2765a4ef77cace3f216f1`.
- Charter method: `~/.cursor/skills/waveset-orchestration/SKILL.md`. Umbrella: `PROGRAM.md`.

## Intent (operator)
From the annotations of the communities that annotate the sounds, train the segmentation model for
the whale sounds in the hydrophones to describe it as what it thinks it is - classifying how many
and what type of orcas - and let that drive the replay with the orca models. Real model, no standin.

## Grounding (verified seams)
- Real hydrophone audio source: Orcasound (public). Station catalog already in-repo
  (`src/integrations/live_orcasound_feeds.json`: slug/bucket/node_name). Archived-audio access layout
  + license is BSW-R01; community annotation corpora + label schemas (Pod.Cast / OrcaHello / ONC /
  Watkins / DCLDE) + licenses are BSW-R02; method + honest-feasibility is BSW-R03.
- Existing modeling scaffolding (kinematic, not acoustic): `modeling/studies/common.py`
  (`STATION_COORDS`), `scripts/ml_services/dtag_*`. No acoustic model in-repo.
- Spectrogram input shares the front-end FFT path with BSH (compute the feature once).

## Locked decisions (do NOT reopen)
- **Real pipeline + a real first model.** annotations -> labels -> train -> eval, with the trained
  weights producing the demo's real classifier output. No canned/scripted detections.
- **Honest, achievable target set by R03.** "Count + type" is genuinely hard; the shipped claim is
  scoped to what the model actually achieves on held-out data (e.g. SRKW-call presence / call-type;
  source-count only if R03 shows it is real). The HUD reports the model's real confidence; it never
  asserts a count the model cannot support. No overclaiming.
- **License/privacy first.** Only openly-licensed audio + annotations, recorded with provenance +
  attribution; NC/ND/unclear -> STOP to O0. No personally identifying community data.
- **Weights + corpora to the box (S3), not git.** A small inference artifact + a `PROVENANCE.md`
  re-fetch pointer ship in-repo; raw audio/corpora/large weights are gitignored.
- **Eval is reported honestly:** train/val/test split, metrics (precision/recall/F1, confusion),
  and the failure modes. Reference point: the prior minGRU attempt in the whale-behavior repo
  reported 0% - this lane does not repeat that without honest metrics.
- **Two tracks separate:** this is the ACOUSTIC model (sound -> who/what). Kinematic behavior
  classification is BRE/BSS; this lane does not touch DTAG motion.

## Wave structure
- **BAM-DATA** (gated, web-enabled): fetch openly-licensed audio + annotation corpora w/ provenance;
  owns `infra/acoustic/data/` (gitignored heavy) + `infra/acoustic/PROVENANCE.md`.
- **BAM-PIPELINE** (gated): `modeling/acoustic/` - feature extraction (spectrogram/embeddings),
  label alignment from community annotations, training + eval scripts; reproducible, offline deps.
- **BAM-TRAIN** (gated): train the first real model on the box dev host; emit honest eval report +
  a small inference artifact; weights to the box.
- **BAM-ACCEPT** (gated): the model produces real output on the slice clip; metrics reported; the
  HUD claim matches measured performance.

## Acceptance criteria (hard, checkable)
- A trained model exists with a reproducible pipeline and an honest held-out eval report.
- On the demo slice clip the model produces a real classification (presence/type/[count if real]).
- All data + weights are license-clear and provenance-documented; heavy artifacts in the box.

## Escalation
Answers to O0. License/privacy ambiguity, infeasible "count+type" risk, overclaim risk, new
dependency, compute/host needs, or any gated step: pause and return to O0.

## Return contract
Dataset provenance list, pipeline file list, the honest eval report (metrics + failure modes), the
inference artifact + box pointer, the exact honest claim wording for the HUD, open questions for O0.
