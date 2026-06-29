# Open-Science Integration (OS) waveset charter

Date: 2026-06-27 (America/New_York)
Lane: O0 orchestrator, forecast ML-ops (integrate / measure-on-served / promote)
Home: `.cca/catalogue/O0/20260627_open-science-integration/`
Authority above this doc:
- `.cca/catalogue/O0/20260627_integrate-promote-launch-handoff/HANDOFF_CHARTER.md` (B/C/G)
- `.cca/catalogue/O0/20260627_signal-modeling-launch-handoff/HANDOFF_CHARTER.md` section B
- `research/signal_modeling/SYNTHESIS_signal_modeling.md` + graduation verdicts (TA5/TA2/TA3/TB4/TB2/TB5/DE)
Input: the open-tools/open-data literature scan run 2026-06-27 (this thread), keyed to the standing
gaps in the graduation verdicts.

## 0. Why this waveset exists

The graduation waveset left two load-bearing items NOT-MEASURED and one standard un-adopted:
- The acoustic **effort / detectability denominator** (`log E`) that TB4 (Boundary Pass presence-days)
  and TA3 (AIS noise) both flagged. Without it, presence-only counts bias the rate (B.2), so no new
  node can be scored honestly.
- A reachable, license-clear **inventory of net-new summer presence-day sources** beyond the four
  served nodes (the binding L3 lever).
- An external, citable **probabilistic-forecast disclosure + scoring standard** to ground the served
  forecast record and the supervisor decision.

A bounded open-science scan found concrete, open resources that close each of these. This waveset
grounds them into reusable specs and measured estimates so a later single-editor integrate can act on
them. It is RESEARCH and SPEC only.

Honesty is unchanged. Effective confidence is 0.0 and nothing here promotes it. A graduate earns
confidence only later via a passing gate on SERVED data plus a recorded supervisor decision (B.1).
Every model/covariate is judged by held-out, fold-stable CV mean-deviance-skill toward +0.144, never
in-sample fit.

## 1. Locked execution model (do not violate)

1. **Read-only research + spec.** Lanes read the web and the repo and WRITE ONLY their named findings
   doc under this folder (or `research/signal_modeling/` where stated). NO convergence-file edit
   (`modeling/**`, `src/aws_backend/**`), NO served-store / S3 write, NO production fetch-that-writes,
   NO ingest, NO deploy, NO promotion, NO commit (B.5/B.6/B.10).
2. **No fabricated numbers (B.2/B.3).** Every count, skill, or coefficient is MEASURED from a cited
   source or marked NOT-MEASURED / ESTIMATED. License + provenance + reachability recorded per source.
3. **Single background subagent, serialized lanes.** One subagent executes the lanes in priority order
   (OS1 first), one findings doc per lane, then the OS-SYN synthesis. The orchestrator (this thread)
   reviews each doc and steers/resumes. The subagent does not spawn parallel heavy work.
4. **Feeds the existing integrate path.** OS findings carry PATCH-SPECs in the established
   `WIRING-*/PATCH-*` style and append a DE drift note when they touch a DE-flagged doc. The actual
   convergence edit / fetch / ingest / promotion are SEPARATE operator-gated steps.
5. **mlops-gate stays green at confidence 0.0** (`tools/waves/run-gate.sh mlops-gate`).
6. **Environments (B.7).** Any optional prototype fit: `.venv-modeling`, `write_outputs=False`,
   `fit_kernels._maybe_write_s3 = lambda: None`. Stdlib + gate: system `python3`.

## 2. Wave OS lanes (serialized by the background subagent, priority order)

| Lane | Scope | Owns (findings) | Exit bar |
|------|-------|-----------------|----------|
| **OS1** (load-bearing) | Acoustic effort / detectability `log E` denominator from OPEN sources: OSF `osf.io/6ctjq` SPL + propagation-loss coefficients + the DFO Salish Sea Monte Carlo detection-range method (PLOS One 2025, DOI 10.1371/journal.pone.0331942) + ONC Oceans 3.0 uptime/duty metadata | `OS1_effort_detectability.md` | a reusable per-(station,day) `log E` detectability spec that closes the TB4/TA3 NOT-MEASURED denominator; license/provenance; PATCH-SPEC + DE note; GO/NO-GO |
| **OS2** | Net-new summer (JJA) presence-day source screen from OPEN archives: NCEI Passive Acoustic Archive / DCLDE-2027 (23 locations), DORI-ONC (HF, CC-BY, ~1 TB), the 30-year SRKW curation (arXiv 2602.09295) literature map, OrcaSound public (CC-BY-NC-SA) | `OS2_open_node_screen.md` (extends S1) | per-source net-new JJA presence-day estimate (MEASURED where the annotation set is public, else ESTIMATED with the literature day-counts) + independence + license + GO/NO-GO |
| **OS3** | External probabilistic-forecast disclosure + scoring: EFI standards (`eco4cast/EFIstandards`, EML extension, FAIR archiving) + proper scores (`scoringRules` R / `scoringrules` + `xskillscore` Python, CRPS/log score) | `OS3_forecast_standards_scoring.md` | spec to (a) wrap the served forecast + confidence in the EFI metadata convention and (b) add CRPS alongside the deviance-skill gate, mapped to the supervisor/DECISION_RECORD flow; PATCH-SPEC; GO/NO-GO |
| **OS4** | Open modeling-tool cross-check: R-INLA / inlabru partial-pooling NB (the TA2 graduate's principled form) and SPDE/LGCP as the post-node-expansion path ONLY | `OS4_inlabru_crosscheck.md` | a spec + honest cross-check plan (does an inlabru partial-pooling NB reproduce the landed served +0.155?), keeping spatial-LGCP-at-current-N as the SYN dead-end; GO/NO-GO |
| **OS5** | Open detector cross-check for L0 ROC + detector-independence on new nodes: PAMGuard (+ Tethys), ANIMAL-SPOT/ORCA-SPY, Ketos, Koogu | `OS5_open_detector_crosscheck.md` | a detector-independence + L0 ROC runbook using an open detector against a public node; GO/NO-GO |
| **OS-SYN** | Synthesis | `OS_SYNTHESIS.md` | rank what graduates to the integrate path, cheapest high-value first, dead-ends; map each to the existing graduation lanes; nothing promotes |

## 3. Shape

```
OS1 effort/detectability log E      (load-bearing; closes TB4/TA3 denominator)
OS2 open-node JJA presence screen   (extends S1; the +0.144 observation lever)
OS3 EFI standards + CRPS scoring    (served-forecast disclosure + scoring grounding)
OS4 inlabru partial-pooling NB      (cross-check the landed TA2; LGCP only post-nodes)
OS5 open detector ROC/independence  (L0 + cross-node detector independence)
OS-SYN synthesis -> feeds the single-editor integrate path
```

## 4. Gates / operator decisions

- OS waveset launch (this charter).
- Any convergence-file integrate of an OS PATCH-SPEC: a separate single-editor step.
- Any production fetch-that-writes / ingest / deploy: operator-/deploy-gated.
- Any confidence promotion: a passing gate on SERVED data + a recorded supervisor decision (B.1).
- Any commit or push: explicit operator request only; surgical staging.

## 5. Status

- **COMPLETE 2026-06-27.** All five lanes (OS1-OS5) plus the OS-SYN synthesis executed and accepted by
  the orchestrator; findings in `OS1`-`OS5` docs and the ranked plan in `OS_SYNTHESIS.md`. Nothing here
  promoted; effective confidence stayed 0.0. Graduates and operator gates handed to the single-editor
  integrate path (OSF license + ONC token unblock the keystone OS1 effort frame).
