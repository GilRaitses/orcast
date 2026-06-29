# OS5 findings: open-detector cross-check for the L0 ROC and detector-independence on a public node

Agent: OS5 background subagent, Open-Science Integration (OS) waveset, O0 forecast ML-ops lane.
Date: 2026-06-27 (America/New_York). Repo: `/Users/gilraitses/orcast`. This findings doc is the ONLY
file written (plus one STEP_LOG line). READ-ONLY research plus bounded reachability probes; no
convergence-file edit (`modeling/**`, `src/aws_backend/**`), no served/S3 write, no fetch-that-writes,
no ingest, no deploy, no promotion, no commit, no `git add`. Effective confidence stays 0.0; this
RECOMMENDS and SPECs only.

Hydration read in full first: `WAVESET_CHARTER.md` (section 2 OS5 row), `OS_DISPATCH.md` (OS5 source
pointers + rails), `research/signal_modeling/S1_node_sources.md` (the operator/detector-independence
framing), the OS2 screen and the TB4 verdict (independence axis), and the repo L0 surfaces
`modeling/fit_kernels.py` `_level0_detector_qc` and `modeling/studies/reports/level0_detector.json`.

## 0. Scope and the one honesty statement

This lane characterizes the open-detector stack and specs a bounded runbook to (a) produce a SECOND,
independent detector ROC to sit beside the existing OrcaHello L0 ROC, and (b) provide detector
INDEPENDENCE for the OS2/TB4 net-new nodes (a different detector on the same audio is genuinely
independent observation; re-running OrcaHello is not). No detector was run in this lane. It is L0
characterization and an independence enabler, NOT a temporal-skill lever: detector outputs feed OS2
presence-day extraction and the L0 ROC, never the kernels, so this does not and cannot move the held-out
CV mean-deviance-skill toward +0.144. Every number below is cited or marked NOT-MEASURED.

## 1. The two open needs this anchors to (the existing L0 ROC, MEASURED)

The served pipeline's L0 detector is the OrcaHello CNN; its operating point is already characterized in
`modeling/studies/reports/level0_detector.json` (MEASURED): ROC AUC 0.8794 (bootstrap 95% CI [0.8563,
0.9023], 1000 samples), d' 1.6197 at the median-confidence threshold 0.6814, overall detector precision
0.7114, from 758 OrcaHello confidence pairs (423 confirmed, 335 false positive) against human-moderated
labels. `_level0_detector_qc` (`fit_kernels.py`) surfaces the same outcome counts and false-positive
rate in the served report.

What is MISSING, and what OS5 supplies:

- (a) L0 ROC is a SINGLE-detector self-assessment (OrcaHello scores vs OrcaHello-team human review). An
  independent open detector run on the same audio against the same (or independent expert) labels gives
  a SECOND ROC and locates the OrcaHello operating point relative to it.
- (b) Detector independence for net-new nodes. S1 (Group A) and TB1 (section 5, risk 3) note the
  Admiralty Inlet OrcaHello nodes share the SAME operator and SAME detector as the served four, so they
  are location-independent but NOT detector-independent corroboration; TB4 (Boundary Pass) and OS2
  (Tekteksen/SIMRES, CarmanahPt) are valued precisely because their expert annotations are
  detector-independent. Running an OPEN detector on a public node's audio is the general way to
  manufacture detector-independence: the same audio scored by a different detector is a genuinely
  independent observation, whereas re-running OrcaHello adds none (the W6 re-shelving lesson, applied to
  detectors).

## 2. Open-detector stack (characterized; licenses + reachability, MEASURED 2026-06-27)

| tool | role | license (MEASURED via GitHub/GitLab API) | repo / reachability |
|---|---|---|---|
| PAMGuard | open detection/classification/localization platform; hosts external DL models via the Raw Deep Learning Classifier module; 2026 Tethys archiving integration | GPL-3.0 | `github.com/PAMGuard/PAMGuard` (very active, pushed 2026-06-25); `pamguard.org` |
| ANIMAL-SPOT | animal-independent PyTorch ResNet18 detector/classifier; orca is one of its trained species; imports into PAMGuard as a `.pk` model | GPL-3.0 | `github.com/ChristianBergler/ANIMAL-SPOT` (active, pushed 2024-04); data+models at DOI `10.17617/3.KQPPXF` (Max Planck Edmond) |
| ORCA-SPOT | the killer-whale-specific precursor (ResNet18 SRKW/NRKW call-vs-noise segmentation) | GPL-3.0 | `github.com/ChristianBergler/ORCA-SPOT` (Sci Rep 2019, DOI `10.1038/s41598-019-47335-w`) |
| ORCA-SPY | ANIMAL-SPOT + PAMGuard TDOA localization integration | GPL-3.0 | `github.com/ChristianBergler/ORCA-SPY` (active, pushed 2025-01; Sci Rep 2023, DOI `10.1038/s41598-023-38132-7`) |
| Koogu | Python (TensorFlow) bioacoustic ML detection toolkit; imports into PAMGuard | GPL-3.0 | `github.com/shyamblast/Koogu` (active, pushed 2025-09); pip `koogu` |
| Ketos | Python (TensorFlow) bioacoustic DL framework (MERIDIAN / Dalhousie); imports into PAMGuard | GPL-3.0 per MERIDIAN docs (NOT confirmed via the GitLab API probe, which did not expose the license field) | `gitlab.com/meridian-analytics/public/ketos`; `meridian.cs.dal.ca`; pip `ketos` |

All six are open source (GPL-3.0, MEASURED for five; Ketos is GPL-3.0 per MERIDIAN but the SPDX was not
exposed by the probe, marked accordingly). PAMGuard's Raw Deep Learning Classifier is the common harness:
an ANIMAL-SPOT/ORCA-SPOT `.pk`, a Ketos model, or a Koogu model loads into the same module, so the spec
can run any of them through one tool. Reachability of the repos and the model-hosting DOI is confirmed at
the metadata level; downloading model weights and audio is the operator-gated runbook step (section 3).

Pretrained killer-whale model availability: ORCA-SPOT/ANIMAL-SPOT ship a killer-whale model trained on a
large orca corpus (the ANIMAL-SPOT paper reports 17,104 orca + 44,323 noise excerpts), retrievable via
the Edmond DOI `10.17617/3.KQPPXF`. IMPORTANT domain caveat (NOT-MEASURED): that corpus is built largely
on Northern Resident / OrcaLab (Orchive) recordings, so applying it to Salish Sea SRKW audio is an
out-of-domain transfer; its operating point on SRKW Salish Sea audio is NOT-MEASURED and must be
characterized by the runbook (section 3), not assumed.

## 3. Bounded runbook (NOT executed here; isolated read-only scratch)

Goal: one independent open-detector ROC plus an agreement check, on a public node, read-only.

Target node (choose by what is open): the highest-value target is an OrcaSound public node (for example
Orcasound Lab or Bush Point), because it is the ONLY place where open audio, OrcaHello detections, AND
human-moderated labels coexist, so it yields BOTH the independent ROC (vs the human labels) AND the
OrcaHello-vs-open agreement (Jaccard) in one pass. Audio is on the AWS Registry of Open Data
(`registry.opendata.aws/orcasound/`); labels are CC-BY-NC-SA (OS2 section 5). The secondary target is a
DCLDE / Tekteksen-SIMRES deployment (CC-BY-4.0 expert annotations, OS2 section 2), which gives the
detector-independence ROC at an actual net-new OS2 node but has no OrcaHello overlap there.

Steps:

1. Fetch a BOUNDED audio window read-only to an isolated scratch dir outside the repo (a few SRKW
   encounter windows plus matched noise windows, not the full archive; bound the download). No repo-store
   write, no ingest.
2. Acquire the open detector read-only: ANIMAL-SPOT/ORCA-SPOT pretrained orca `.pk` from the Edmond DOI
   `10.17617/3.KQPPXF`, run either standalone (PyTorch) or via the PAMGuard Raw Deep Learning Classifier;
   alternatively a Ketos or Koogu orca model in the same PAMGuard module.
3. Score the audio windows: produce per-window detector scores, then a ROC against the labels using the
   SAME method as the existing L0 artifact (`roc_auc` + 1000-sample bootstrap 95% CI; d' at a stated
   threshold), so the open detector's ROC is directly comparable to the OrcaHello AUC 0.8794 / d' 1.6197.
4. Agreement vs OrcaHello where both exist (OrcaSound node): per-window Jaccard / Cohen's kappa between
   the open-detector positives and the OrcaHello detections; report the confusion against the human
   labels for both detectors side by side.
5. Output: a scratch ROC report (no repo write). Compare the open detector's AUC/d'/operating point to
   the OrcaHello L0 numbers and report the detector-independence (how often the two detectors agree, and
   on which encounters one catches what the other misses).

Gates, honestly (each NOT-MEASURED until the runbook is run):

- Model weights: the pretrained orca `.pk` is retrievable via the Edmond DOI, but it is out-of-domain
  (NRKW/Orchive training vs SRKW Salish Sea); a domain-shift characterization (or a short fine-tune on a
  labelled SRKW subset) may be needed. Weights-on-SRKW performance NOT-MEASURED.
- Audio access + size: OrcaSound FLAC/WAV is large; the runbook must bound to encounter windows.
  Per-node audio volume and download feasibility from this environment NOT-MEASURED.
- Compute: ANIMAL-SPOT is PyTorch; CPU inference on a bounded clip set is feasible, GPU only speeds it.
  No GPU is assumed; runtime NOT-MEASURED.
- Labels: OrcaSound human-moderated labels (CC-BY-NC-SA) or DCLDE expert annotations (CC-BY-4.0) are the
  truth set; their per-window alignment to the audio is the remaining data-prep gate.

## 4. Role (honest)

This is L0 detector characterization plus a detector-independence enabler for the OS2/TB4 net-new nodes.
It is NOT a temporal-skill lever. The open detector's outputs feed (i) the L0 ROC (a detector-quality
gate, `required_before_full_confidence`, not a kernel input) and (ii) OS2 presence-day extraction (a
detector-independent presence signal at a net-new node). Neither path changes the served kernels,
`_confidence_from_gates`, or the +0.144 bar, so OS5 earns no confidence and moves no skill. Its value is
(a) a second ROC that locates the OrcaHello operating point and (b) converting an OS2/TB4 node from
"expert-annotation-dependent" to "reproducible by an open detector", which strengthens the independence
claim several verdicts lean on.

## 5. DE drift note

None required. This doc characterizes external tools and specs an offline benchmark; it touches no
DE-flagged prose doc (`M2_nonlinear_physics.md`, `wave_shape.yml` objectives, `ORCHESTRATOR_NOTES.md`,
the wildlife register). It is consistent with S1/TB1/TB4/OS2: detector independence is the axis those
verdicts use, and OS5 supplies the open detector that realizes it. No stale GO is superseded; the +0.144
bar and the confidence map are untouched (the L0 ROC is a detector gate, not a confidence input).

## 6. GO / NO-GO

GO (spec/runbook, operator-gated on model weights + audio + compute) on running an open detector
(ANIMAL-SPOT / ORCA-SPOT pretrained orca, GPL-3.0, standalone or via the PAMGuard Raw Deep Learning
Classifier) on a public OrcaSound node to produce an independent L0 ROC (AUC + bootstrap CI, comparable
to the OrcaHello 0.8794) plus an OrcaHello-vs-open Jaccard, and on a DCLDE/Tekteksen-SIMRES deployment to
realize detector-independence at an OS2 net-new node. NO-GO on any temporal-skill credit (not a +0.144
lever; earns no confidence). NO-GO on treating an out-of-domain pretrained detector's raw output as
ground truth: the NRKW-to-SRKW domain shift must be characterized (or a short SRKW fine-tune done), not
assumed.

## 7. Return summary

- Doc path: `.cca/catalogue/O0/20260627_open-science-integration/OS5_open_detector_crosscheck.md`.
- Open-detector stack (licenses MEASURED): PAMGuard GPL-3.0 (the DL-hosting platform, 2026 Tethys
  integration), ANIMAL-SPOT / ORCA-SPOT / ORCA-SPY GPL-3.0 (killer-whale PyTorch detection, Sci Rep DOIs
  `10.1038/s41598-019-47335-w` and `10.1038/s41598-023-38132-7`, weights via Edmond DOI
  `10.17617/3.KQPPXF`), Koogu GPL-3.0, Ketos GPL-3.0 (per MERIDIAN; SPDX not exposed by the probe). All
  open source and PAMGuard-loadable.
- Anchor (MEASURED): the existing OrcaHello L0 ROC AUC 0.8794 (CI [0.856, 0.902]), d' 1.6197; OS5 adds an
  independent second-detector ROC beside it and a detector-independence check for OS2/TB4 nodes.
- OS5 GO/NO-GO: GO (spec/runbook, operator-gated) on the open-detector ROC + OrcaHello Jaccard on a public
  OrcaSound node and the detector-independence check on a Tekteksen/DCLDE deployment; NO-GO on any skill
  credit (not a +0.144 lever) and NO-GO on trusting out-of-domain pretrained output as truth without a
  domain-shift characterization.
- Single highest-value next action: run the open detector on ONE public OrcaSound node (open audio +
  OrcaHello detections + human labels coexist there) to get the independent ROC and the OrcaHello-vs-open
  Jaccard in one bounded pass, comparable to the existing AUC 0.8794, before extending to a net-new OS2
  node.
- Operator gates hit: (1) model weights (pretrained orca `.pk` via Edmond DOI `10.17617/3.KQPPXF`, but
  NRKW/Orchive-trained, out-of-domain for SRKW Salish Sea, performance NOT-MEASURED); (2) audio access +
  download size (OrcaSound FLAC/WAV is large; bound to encounter windows; feasibility NOT-MEASURED);
  (3) compute (PyTorch CPU inference feasible, GPU optional; runtime NOT-MEASURED); plus label alignment.
- Confirmation: nothing edited in `modeling/**` or `src/aws_backend/**`, nothing fetched-to-write,
  ingested, deployed, promoted, or committed; no detector run (no weights or audio fetched here); repos
  probed read-only; only this one findings doc plus a STEP_LOG line written; the served L0 gate, the
  +0.144 bar, and `_confidence_from_gates` untouched; effective confidence 0.0.
