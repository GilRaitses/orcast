# Orchestrator dispatch prompt (integrate / measure-on-served / promote rotation)

## One-liner to paste into the fresh thread

```
Hydrate as O0 (forecast ML-ops integrate/measure-on-served/promote lane) from .cca/catalogue/O0/20260627_integrate-promote-launch-handoff/ORCHESTRATOR_DISPATCH_PROMPT.md and ack per HANDOFF_CHARTER.md §G before acting.
```

## Full paste block (the dispatch prompt the one-liner points at)

```
You are resuming as the orcast forecast ML-ops orchestrator (O0, MLM + MLO). Your job this thread is to
ACT on the graduation waveset's measured synthesis: integrate the one lever that cleared the bar, build
the clean baseline, measure the real new-observation lever, and bring a promotion DECISION back to the
operator. This is the first work in this lane that edits convergence files and runs SERVED-store fits.
Hydrate from files, not from any chat transcript linearly.

Read in order before acting:
1. .cca/catalogue/O0/20260627_integrate-promote-launch-handoff/HANDOFF_CHARTER.md
2. .cca/catalogue/O0/20260627_integrate-promote-launch-handoff/HYDRATION_PACKET.md
3. .cca/catalogue/O0/20260627_mlops/research/signal_modeling/graduation/SYNTHESIS_graduation.md
4. the TA5 / TA2 / TA3 / TB4 lane docs (the patch-specs + measurement plans) under that graduation/ dir

What measurement established (the graduation waveset, now DONE): every candidate was scored against the
held-out, fold-stable +0.144 bar. The two SYN flagships fell -- TA1 (2-state MMPP) is a per-fold
re-leveling artifact that breaks PIT and does NOT repair the time-rescaling GOF; TB1 (Port Townsend +
Bush Point) adds 25 net-new region presence-days but 0 in summer. One sleeper cleared the bar: TA5
(physics smoothness shape prior) = +0.177 (5/5 folds, across-fold lower bound +0.111, PIT calibrated) on
the EXPERIMENT store, NOT yet on the served store. The real new-observation lever is TB4 (ONC/JASCO
Boundary Pass): summer coverage YES, independent operator/detector/corridor, disjoint 2015-2019 epoch,
summer SRKW count unmeasured. TA2 (partial-pooling NB) + TA3 (AIS effort) are enablers (fold-stability +
a non-flat log E), not skill. TA4, TB5-at-N, TB3-as-lever, and all drift-guard dead-ends held NO-GO.

Locked, do not reopen (restate in the ack): effective confidence is 0% and only rises on a passing SERVED
gate PLUS a recorded supervisor decision (src/aws_backend/promotion/supervisor.py) -- never a refit side
effect; you may RECOMMEND a promotion, the operator/supervisor makes it. Judge every change by held-out,
fold-stable CV mean-deviance-skill (+0.144, >=4/5 folds, across-fold lower bound, PIT calibrated), never
in-sample fit. The TA5 +0.177 is on the EXPERIMENT store and means nothing until it reproduces on the
SERVED store (single-station + post-ingest served 4-station). Convergence files are edited ONE owner at a
time -- serialize the integrates (TA5, then TA2, then TA3, then TB measurement); apply each lane's
PATCH-SPEC, keep defaults byte-identical (opt-in via flag). The store is bucket
198456344617-us-west-2-orcast-aws-backend-raw-payloads in us-west-2 (NOT the config default); keep the
production upload DISABLED (fit_kernels._maybe_write_s3 = no-op or write_outputs=False) until the operator
explicitly approves a promotion -- measure first. modeling/ + data/models/ are local-only (untracked);
heavy fits use .venv-modeling, the ladder + mlops-gate use system python3; keep mlops-gate green at
served confidence 0.0. TB4's summer measurement parses the PUBLISHED ECHO Annotations.csv read-only; any
TB4 ingest or TB1 region expansion is a SEPARATE operator-/deploy-gated step. DFO/external feeds via aimez
EC2 i-04a649f91274e9fce. No commit or push without an explicit operator ask; surgical staging only (never
git add -A). The DE source-doc drift fixes are recommended-not-applied; landing them is a low-risk
text-only parallel cleanup that must preserve Hawkes-as-GOF-diagnostic. Do not read the chat transcript
linearly.

First action after the ack: execute step 1 -- integrate the TA5 smoothness prior (estimator.py +
fit_kernels.py, patch-only, nested-CV lambda, default byte-identical) and RE-MEASURE it on the served
store under the G2 gate (upload disabled). Report the served per-fold CV-skill verdict; if it clears
fold-stable +0.144, bring a recommended supervisor promotion to the operator. Then serialize steps 2-4
(TA2+TA3 baseline; TB4 summer count; re-judge TB2/TB5). Step 5 (DE drift fixes) can run alongside.

Return the section G ack from HANDOFF_CHARTER.md before acting.
```

## Pointer table (file, not transcript)

| Need | File |
|------|------|
| Locked decisions + the served-vs-experiment distinction + serialize rule | `HANDOFF_CHARTER.md` (B) |
| Ordered read list | `HYDRATION_PACKET.md` |
| The ranked measured plan + the step sequence | `research/signal_modeling/graduation/SYNTHESIS_graduation.md` (sections 1-4) |
| TA5 lever + estimator/fit_kernels patch-spec | `research/signal_modeling/graduation/TA5_shape_priors.md` |
| Baseline enablers + patch-specs | `research/signal_modeling/graduation/TA2_hierarchical_nb.md`, `TA3_ais_effort.md` |
| TB4 summer-count measurement plan | `research/signal_modeling/graduation/TB4_onc_boundary_pass.md` |
| Conditional covariates + patch-specs | `research/signal_modeling/graduation/TB2_sst_front.md`, `TB5_salishseacast_currents.md` |
| Drift remediations (recommended-not-applied) | `research/signal_modeling/graduation/DE1_text_drift.md`, `DE2_method_drift.md`, `DE3_strategy_drift.md` |
| The +0.144 bar + served gate definition | `research/forward/G2_promotion_protocol.md` |
| AWS refit recipe + upload-disable | `HANDOFF_CHARTER.md` (B.5, B.6) |
| Machine-readable lane state | `wave_shape.yml` (`signal_modeling_graduation:`) |
| Full lineage | `STEP_LOG.md` (the graduation TA/TB measured entry) |
