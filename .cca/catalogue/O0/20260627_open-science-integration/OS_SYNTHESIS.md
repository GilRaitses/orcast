# OS-SYN: synthesis of the Open-Science Integration waveset (OS1 through OS5)

Agent: OS-SYN background subagent, Open-Science Integration (OS) waveset, O0 forecast ML-ops lane.
Date: 2026-06-27 (America/New_York). Repo: `/Users/gilraitses/orcast`. This synthesis is the ONLY file
written (plus one STEP_LOG line and the single permitted charter section-5 status-line edit). READ-ONLY;
no convergence-file edit (`modeling/**`, `src/aws_backend/**`), no served/S3 write, no fetch-that-writes,
no ingest, no deploy, no promotion, no commit, no `git add`. Effective confidence stays 0.0; this
RECOMMENDS and SPECs only. Every count is carried forward with its lane's MEASURED / NOT-MEASURED /
ESTIMATED label; nothing is fabricated and nothing promotes.

Synthesizes the five findings docs in `.cca/catalogue/O0/20260627_open-science-integration/`:
`OS1_effort_detectability.md`, `OS2_open_node_screen.md`, `OS3_forecast_standards_scoring.md`,
`OS4_inlabru_crosscheck.md`, `OS5_open_detector_crosscheck.md`.

## 1. Executive summary

The open-science scan was run against the five standing gaps and it landed one structural fix, one strong
observation lever, and three hygiene/QA enablers. (1) Effort/detectability denominator: OS1 found a fully
open method (PLOS One DOI `10.1371/journal.pone.0331942`) and the OSF coefficient repository (`6ctjq`,
`PL_coeffs.zip` ~242 KB plus `SPL_files.zip` ~42.8 MB) to build a per-(station, day) detection-area term
`D_det` that closes the structural form of the `log E` denominator TB4 and TA3 left NOT-MEASURED, as a
fixed multiplicative effort offset with zero added presence parameters. (2) Net-new summer presence-days:
OS2 measured the strongest open net-new summer source found anywhere in the program, Tekteksen (SIMRES,
Boundary Pass off Saturna Island, 11 JJA-2022 SRKW-certain presence-days, CC-BY-4.0), alone larger than
TB4's 6, inside about 26 net-new net JJA days total across the DCLDE-2027 corpus. (3) Forecast disclosure
and scoring: OS3 specced an EFI-standard metadata sidecar (BSD-2-Clause) and a report-only NB2-CRPS block
alongside the deviance-skill gate. (4) Modeling cross-check: OS4 specced an inlabru / R-INLA Bayesian
partial-pooling benchmark of the landed TA2, expected to reproduce the served +0.1547 and add calibrated
intervals. (5) Detector independence: OS5 characterized an open detector stack (PAMGuard, ANIMAL-SPOT /
ORCA-SPOT / ORCA-SPY, Koogu, Ketos, all GPL-3.0) to produce a second L0 ROC beside the served OrcaHello
ROC (AUC 0.8794, d' 1.6197) and to make the OS2/TB4 nodes detector-independent. The two levers (OS1
denominator, OS2 nodes) are coupled: OS1 unblocks honest rate-scoring of the OS2 nodes, and presence-days
are MEASURED but no CV-skill is credited until the effort frame lands. The other three are disclosure /
QA / characterization, not skill levers; none moves the +0.144 bar and none earns confidence.

## 2. What graduates to the single-editor integrate path (ranked)

Ranked by value to the goal first, with cost/readiness noted. The lever path is OS1 (keystone, unblocks
OS2) then OS2 (strongest observation lever); the cheapest standalone graduate that can land with no
operator gate is the OS3 CRPS block, so it is the recommended first CODE landing even though it is hygiene
not a lever (see the landing sequence note below the table).

| # | graduate | source + license | MEASURED vs NOT-MEASURED | operator gate(s) | maps to existing lane |
|---|---|---|---|---|---|
| 1 | **OS1 `D_det` effort/detectability wire** (per-(station, day) detection-area offset on `log E`; byte-identical no-op default in a new `modeling/detection_range.py`, attaches in `design.py`/`effort.py`/`fit_kernels.py` after the TA3 `D_ais`) | OSF `6ctjq` coefficients + PLOS One DOI `10.1371/journal.pone.0331942`; OSF node license UNCONFIRMED (no tag), PLOS text CC-BY-4.0 | MEASURED: method, OSF files (`PL_coeffs.zip` ~242 KB, `SPL_files.zip` ~42.8 MB), per-site summer/winter ranges. NOT-MEASURED: OSF reuse license, zip internals, served-station ambient series, served-detector `DT`, CV-skill delta | OSF data-file reuse license; ONC Oceans 3.0 token (ambient + uptime, API 401); operator-accepted geoacoustic-class transfer from Mouat Point | **TA3 effort wire** (`log E` offset; the third multiplicative factor after uptime and `D_ais`) |
| 2 | **OS2 net-new summer nodes** (Tekteksen/SIMRES led, then CarmanahPt; build per-deployment presence-day records from the CC-BY-4.0 DCLDE annotations) | DCLDE-2027 corpus `Annotations.csv` (CC-BY-4.0); SIMRES / DFO_WDLP providers | MEASURED: Tekteksen 11 JJA-2022 certain days, CarmanahPt 4, about 26 net-new JJA days total. NOT-MEASURED: per-deployment effort/duty cycle; ESTIMATED: Swiftsure Bank as the largest untapped reservoir (JJA fraction NOT-MEASURED) | region expansion outside `SAN_JUAN_BOUNDS` (two-box gate, per TB1); per-deployment effort/`log E` (the OS1 gate); CC-BY-NC-SA on OrcaSound labels (avoid) | **TB4 / TB1 node ingest + region expansion** (`EXTRA_NODES`/`STATION_COORDS`, `geo_region.py` two-box) |
| 3 | **OS3 NB2-CRPS report-only block** (closed-form NB2 CRPS + CRPS-skill in `diagnostics.py`, computed in the existing `_held_out_pit` per-fold loop, written to `report["crps"]`) | in-repo `scipy.stats.nbinom` (Wei and Held 2014 form); optional `scoringrules` Apache-2.0 / `scoringRules` GPL>=2 | MEASURED: NB2 `(n, p)` already built for the PIT; closed form needs no ensemble. NOT-MEASURED: the CRPS values themselves (no fit run) | NONE (in-repo, no new dependency, byte-identical no-op until called) | **served disclosure / serve path** (report block; does not touch `_confidence_from_gates` or the bar) |
| 4 | **OS5 open-detector independence + second L0 ROC** (run ANIMAL-SPOT/ORCA-SPOT pretrained orca, or Koogu/Ketos via PAMGuard, on a public node; ROC + bootstrap CI vs expert labels, Jaccard vs OrcaHello) | PAMGuard / ANIMAL-SPOT / ORCA-SPOT / ORCA-SPY / Koogu GPL-3.0; Ketos GPL-3.0 per MERIDIAN; weights via Edmond DOI `10.17617/3.KQPPXF` | MEASURED: stack + licenses, existing OrcaHello L0 ROC AUC 0.8794 / d' 1.6197. NOT-MEASURED: out-of-domain (NRKW->SRKW) detector performance, audio size, runtime | open-detector model weights (out-of-domain); public audio access + download size; compute (PyTorch CPU feasible, GPU optional) | **L0 detector ROC** (`level0_detector.json`, a detector gate) + feeds **OS2** presence-day extraction (detector independence) |
| 5 | **OS3 EFI metadata sidecar** (`to_efi_metadata` + Tier-3 CSV, emission OFF by default; FAIR archiving) | EFI `eco4cast/EFIstandards` BSD-2-Clause | MEASURED: existing fit-report fills most required EFI fields. MISSING: forecast DOI, code DOI, optional container | FAIR DOI archiving (mint a forecast DOI before observations land; code DOI; optional Docker/Singularity), infra/operator | **served disclosure / serve path** (additive sidecar next to `fit_report.json`) |
| 6 | **OS4 inlabru / R-INLA cross-check** (offline Bayesian partial-pool benchmark of TA2; optional calibrated-interval disclosure) | inlabru CRAN GPL>=2; R-INLA GPL (not on CRAN, installs from r-inla.org); MEE DOI `10.1111/2041-210X.13168` | MEASURED: the landed ridge IS the MAP of inlabru's `iid` random intercept. NOT-MEASURED: R-runtime reachability, the benchmark result (no fit run) | R runtime + R-INLA install (offline) | **TA2 estimator** (`fit_glm` `partial_pool`); QA/benchmark + disclosure of station-effect intervals (composes with #5) |

Recommended landing sequence: land #3 (CRPS report-only block) first as the cheapest no-gate code
improvement; pursue #1 (OS1 effort wire) as the keystone in parallel, since its data-prep is gated on the
OSF license and the ONC token and it must precede honest scoring of #2; then #2 (the Tekteksen/DCLDE
nodes) once the effort frame exists and the region-expansion gate is decided; #4 (open-detector
independence) strengthens #2 and re-characterizes L0 whenever the weights/audio/compute gate is cleared;
#5 (EFI sidecar/FAIR) and #6 (inlabru benchmark) follow on their infra and R-runtime gates. Only #1 and #2
can eventually move held-out skill, and only after the effort frame lands; #3 through #6 are hygiene, QA,
and characterization that earn no confidence.

## 3. Dead-ends / NO-GO

- **Spatial LGCP / SPDE at the current N** (OS4 section 4): four stations in one roughly 8 by 9 km cluster
  facing one Haro Strait lane have no spatial leverage; an SPDE/LGCP mesh would invent unidentifiable
  structure and risk laundering a detector artifact into a spatial effect. Reserved for AFTER TB1 / TB4 /
  OS2 add spatially separated nodes; NO-GO now.
- **DORI-ONC as a net-new source for now** (OS2 section 3): about 1 TB, amateur labels (Jaccard 0.7,
  ecotype uncompared) over ONC data the expert DCLDE corpus already covers; net-new JJA NOT-MEASURED.
  NO-GO until an operator accepts the parse cost.
- **OrcaSound public archive re-shelving** (OS2 section 5): same nodes, operator, and detector family as
  the served four (the W6 lesson); net-new JJA approximately 0; labels CC-BY-NC-SA. NO-GO as a net-new
  source.
- **Treating CRPS / EFI (OS3) or the inlabru cross-check (OS4) as skill levers**: they add no covariate,
  observation, or parameter; they cannot move the held-out CV mean-deviance-skill toward +0.144 and earn
  no confidence. The inlabru benchmark is expected to REPRODUCE, not beat, the served +0.1547.
- **Trusting out-of-domain detector output as truth** (OS5 section 6): the pretrained orca weights are
  NRKW/Orchive-trained, out-of-domain for SRKW Salish Sea audio; raw output must be characterized (or a
  short SRKW fine-tune done), not assumed. NO-GO on treating it as ground truth.

## 4. Consolidated operator gates (across all five lanes)

| gate | raised by | what it unblocks |
|---|---|---|
| **OSF data-file reuse license** (node `6ctjq` carries no license tag; read via the published view-only token, reuse terms unstated) | OS1 | the load-bearing `PL_coeffs.zip` (~242 KB) and therefore the entire `D_det` effort wire (#1) |
| **ONC Oceans 3.0 token** (UI 200, programmatic API 401 token-gated) | OS1, OS2 | per-station ambient SPL + uptime/duty series for `D_det` (#1) and the per-deployment effort denominator for the new nodes (#2) |
| **Region expansion outside `SAN_JUAN_BOUNDS`** (two-box gate, per TB1) | OS2 (and TB1/TB4) | grounding Tekteksen/SIMRES, CarmanahPt, Swiftsure Bank, and the other out-of-box net-new summer nodes (#2) |
| **R + R-INLA runtime** (INLA not on CRAN; installs from r-inla.org, reachable; R-runtime reachability NOT-MEASURED) | OS4 | the inlabru Bayesian partial-pool benchmark and calibrated station-effect intervals (#6) |
| **Open-detector weights / audio / compute** (NRKW->SRKW out-of-domain weights via Edmond DOI; OrcaSound audio download size NOT-MEASURED; PyTorch CPU feasible, GPU optional) | OS5 | the independent second L0 ROC and detector-independence for the OS2/TB4 nodes (#4) |
| **FAIR DOI archiving** (forecast DOI before observations land, code DOI, optional container; infra/operator) | OS3 | the only EFI field set the pipeline does not already fill, completing the EFI sidecar (#5) |

## 5. Single highest-value next action across the waveset

Confirm the OSF data-file reuse license for node `6ctjq` (request access on OSF or contact the authors,
Mouy / Austin / Yurk) and, with it, the ONC Oceans 3.0 token. Rationale: OS1 is the keystone of the only
genuine value path in this waveset. The `log E` effort denominator is the gate that TB4 and TA3 both left
NOT-MEASURED, and it is what makes the strong OS2 observation lever (Tekteksen, 11 MEASURED JJA days)
scorable as honest rate rather than biased presence-only counts. The reusable artifact is tiny (~242 KB of
`A`/`n` coefficients) and the method is fully open and characterized; everything downstream of the
effort frame, the OS2 node ingest, the de-biased `k_season`/`k_diel` kernels, and any eventual move toward
+0.144, is blocked behind that single license-plus-token confirmation. It is the cheapest unlock with the
largest reach.

## 6. Mapping to the existing graduation framework (an extension, not a parallel track)

Each graduate lands on an EXISTING S1/S2 + TA/TB lane, so the operator sees one continuous program:

- OS1 `D_det` extends the **TA3 effort wire**: it is the same `log E` multiplicative-offset role TA3
  established for `D_ais`, adding a third factor (uptime x `D_ais` x `D_det`) with zero presence
  parameters. It closes the structural denominator TB4 and TA3 flagged.
- OS2 extends **S1 node sources and the TB1/TB4 node-ingest + region-expansion** path: same
  `EXTRA_NODES`/`STATION_COORDS` + `geo_region.py` two-box mechanism, same "presence-days MEASURED, skill
  gated on the effort frame" honesty TB4 carried, same operator region-expansion decision TB1 framed.
- OS3 extends the **served disclosure / serve path**: an EFI-standard wrapper on the existing fit-report
  fields plus a report-only CRPS block beside the existing deviance-skill and PIT gates; the
  `_confidence_from_gates` map and the 0.6 / +0.144 promotion bar are unchanged.
- OS4 extends the **TA2 estimator** as a QA/benchmark: the landed `partial_pool` ridge is exactly the MAP
  of inlabru's `iid` random intercept, so the cross-check validates TA2 and (with OS3) can disclose
  calibrated station-effect intervals the penalized statsmodels fit suppresses.
- OS5 extends the **L0 detector ROC** (`level0_detector.json`) with an independent second detector and
  feeds **OS2** presence-day extraction with genuine detector-independence.

Honesty rails preserved throughout: nothing promotes (promotion stays a separate B.1 supervisor decision
on served data, `research/forward/G2_promotion_protocol.md`); effective confidence stays 0.0; presence-days
are MEASURED but skill is gated on the effort frame (OS1); the +0.144 bar and the confidence mapping are
unchanged; the Hawkes self-excitation report stays a GOF diagnostic only.

## 7. DE drift note

None required. This synthesis aggregates the five lane findings and touches no DE-flagged prose doc
(`M2_nonlinear_physics.md`, `wave_shape.yml` objectives, `ORCHESTRATOR_NOTES.md`, the wildlife register).
It is consistent with S1/S2 and the TA/TB graduates and with `SYNTHESIS_signal_modeling.md`: acoustic
detectability is effort (B.2), net-new summer presence-days are the binding L3 lever (DE3 / TB1
drift-guard) with skill gated on effort, and spatial LGCP at the clustered N stays the SYN dead-end. No
stale GO is superseded; the +0.144 bar and the confidence map are unchanged. If a later integrate touches
a DE1/DE3-flagged register that still reads "more nodes -> summer skill", attach the standing caveat
(presence-days measured; skill gated on the effort frame).

## 8. Return summary

- Doc path: `.cca/catalogue/O0/20260627_open-science-integration/OS_SYNTHESIS.md`.
- Top 3 ranked graduates: (1) **OS1 `D_det` effort/detectability wire** (keystone; closes the TB4/TA3
  `log E` denominator; maps to the TA3 effort wire; gated on OSF license + ONC token); (2) **OS2 net-new
  summer nodes** led by Tekteksen/SIMRES (MEASURED 11 JJA-2022 days, the strongest open net-new summer
  lever; maps to TB4/TB1 ingest + region expansion; gated on the OS1 effort frame + region expansion);
  (3) **OS3 NB2-CRPS report-only block** (cheapest, no gate, in-repo, byte-identical no-op; maps to the
  served disclosure path). Order rationale: OS1 unblocks honest scoring of OS2 and is the only structural
  fix; OS2 is the strongest observation lever but is biased without OS1; OS3-CRPS is the cheapest code
  landing of all and can go first as hygiene, but it is not a skill lever.
- Consolidated operator gates: OSF data-file reuse license (OS1); ONC Oceans 3.0 token (OS1, OS2); region
  expansion outside `SAN_JUAN_BOUNDS` (OS2); R + R-INLA runtime (OS4); open-detector weights/audio/compute
  (OS5); FAIR DOI archiving (OS3).
- Single highest-value next action: confirm the OSF `6ctjq` reuse license plus the ONC token, since the
  tiny `PL_coeffs.zip` (~242 KB) unblocks the OS1 effort frame on which both the de-biased kernels and the
  honest scoring of the OS2 Tekteksen nodes depend.
- Confirmation: nothing edited in `modeling/**` or `src/aws_backend/**`, nothing fetched-to-write,
  ingested, deployed, promoted, or committed; the five lane docs were read read-only; only this synthesis
  plus a STEP_LOG line and the single permitted charter section-5 status-line edit were written; the
  served gate, the +0.144 bar, and `_confidence_from_gates` untouched; effective confidence 0.0.
