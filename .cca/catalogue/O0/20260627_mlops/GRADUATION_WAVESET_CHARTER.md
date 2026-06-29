# Graduation waveset charter (act on the SYN ranked plan: Tier A, Tier B, Dead-End drift audit)

Date: 2026-06-27 (America/New_York)
Lane: O0 orchestrator, forecast ML-ops (MLM + MLO)
Home: `.cca/catalogue/O0/20260627_mlops/`
Authority above this doc: `.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` section B and
`.cca/catalogue/O0/20260627_signal-modeling-launch-handoff/HANDOFF_CHARTER.md` section B.
Input: `research/signal_modeling/SYNTHESIS_signal_modeling.md` (the ranked graduate/dead-end plan) and
the five findings docs S1/S2/M1/M2/M3.

## 0. Why this waveset exists

The signal & modeling research campaign produced a ranked plan (SYN). This waveset acts on it with
deep parallel subagents in three waves:
- **Wave TA (Tier A)** -- extract the last fold-stable skill from the data we already have (model +
  effort levers). Cheap, no new sourcing.
- **Wave TB (Tier B)** -- ground genuinely new independent observation (the actual +0.144 lever).
  Heavier; carries an explicit modeling-region-scope decision.
- **Wave DE (Dead-End drift audit)** -- audit whether the now-adjudicated dead-end methods have
  drifted into repo TEXTS or METHODS as if they were live/recommended paths, and recommend
  remediation. Read-only.

Honesty is unchanged. Effective confidence is 0.0 and nothing in this waveset promotes it. A graduate
earns confidence later only via a passing gate on SERVED data + a recorded supervisor decision (B.1).
Every model/covariate is judged by held-out, fold-stable CV mean-deviance-skill toward **+0.144**,
never in-sample fit (anti-overfitting, the load-bearing rule).

## 1. The locked execution model this waveset obeys (do not violate)

These carry the established `wave_shape.yml -> frontier_dispatch.execution_model` plus B.

1. **One file, one owner; single convergence-file editor per wave.** The convergence files
   (`modeling/fit_kernels.py`, `modeling/studies/level2_multistation.py`,
   `modeling/studies/cross_station_consistency.py`, `src/aws_backend/sources/salmon.py`,
   `src/aws_backend/ingest_multistation.py`, `src/aws_backend/sources/*`) are NOT edited in parallel.
   The Tier A/B subagents therefore **do not edit convergence files**; each produces a
   prototype-and-measure report + a patch-spec (the `WIRING-*.md` / `PATCH-*.md` pattern). The actual
   convergence-file edit is a later **single-editor integrate step**, operator-gated.
2. **No concurrent heavy fit during a parallel wave.** Heavy fits run in `.venv-modeling` and clobber
   shared local state (`data/models/`). Tier A subagents that need a fit run it in an **isolated
   scratch dir** with `write_outputs=False`, OR the wave serializes the actual fits. No subagent
   writes `data/models/fit_report.json` or any served artifact.
3. **Refit safety (B.5/B.6).** Any fit against S3 sets
   `ORCAST_STORAGE_BACKEND=aws ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads AWS_REGION=us-west-2`
   AND disables the production upload (`fit_kernels._maybe_write_s3 = lambda: None` or
   `write_outputs=False`). A confidence change is a recorded supervisor decision, never a refit side
   effect.
4. **No fetch that writes the production store in a parallel wave.** Tier B grounding is **dry-run +
   runbook + measured net-new estimate** only; the production `acoustic_detections` / feed writes are
   a separate operator-/deploy-gated step (exactly as W6 was). External feeds via web; in-region /
   DFO feed probes via the aimez EC2 `i-04a649f91274e9fce` (B.9).
5. **Environments (B.7).** Heavy fit/studies: `.venv-modeling`. Stdlib ladder + mlops-gate: system
   `python3`. Backend: `.venv`. The `modeling/` pipeline + `data/models/` stay local-only/untracked.
6. **No agent commits (B.10).** Subagents write only their named findings/report doc (+ a patch-spec
   doc where stated). The orchestrator commits nothing without an explicit operator ask; surgical
   staging only, never `git add -A`.
7. **mlops-gate stays green at confidence 0.0** (`tools/waves/run-gate.sh mlops-gate`; the honesty
   guard: served confidence must not exceed earned).

## 2. Wave TA -- extract from existing data (model + effort)

Deep parallel subagents, one per Tier-A graduate. Each: prototype in isolation, measure through the
existing `block_cv` harness (write_outputs=False), report per-fold CV mean-deviance-skill + PIT +
fold-stability vs the +0.144 bar, and emit a patch-spec for the later single-editor integrate. No
convergence-file edit, no served write, no commit.

| Lane | Graduate (SYN) | Owns (findings + spec) | Exit bar |
|------|----------------|------------------------|----------|
| TA1 | 2-state occupancy MMPP (latent present/absent chain modulating the Poisson rate) | `research/signal_modeling/graduation/TA1_occupancy_mmpp.md` | per-fold CV-skill + does it fix the time-rescaling GOF; GO/NO-GO + patch-spec |
| TA2 | Hierarchical/partial-pooling NB + regularization (nested-CV) + presence-hurdle reframe | `.../graduation/TA2_hierarchical_nb.md` | per-fold CV-skill + calibration; GO/NO-GO + patch-spec |
| TA3 | AIS-derived effort/noise term in `log E` | `.../graduation/TA3_ais_effort.md` | sourced AIS effort covariate + skill delta from a cleaner `log E`; GO/NO-GO + patch-spec |
| TA4 | In-repo derived covariates F1 (lunar x diel) + A1 (tide slack/max-flow) with the A3 +1-harmonic control | `.../graduation/TA4_inrepo_covariates.md` | marginal CV-skill vs control; GO/NO-GO + patch-spec |
| TA5 | Physics shape priors (monotonic dose-response / smoothness) on existing kernels | `.../graduation/TA5_shape_priors.md` | variance/calibration effect; GO/NO-GO + patch-spec |

TA gate: each lane lands a measured report with per-fold held-out CV-skill (never in-sample) + a
GO/NO-GO + a patch-spec. Nothing promotes. The integrate step (editing `fit_kernels.py` etc.) is a
separate single-editor, operator-gated step.

## 3. Wave TB -- ground new independent observation (the +0.144 lever)

Deep parallel subagents, one per Tier-B graduate. Each: produce a grounding runbook + a DRY-RUN
measured net-new estimate (presence-days for nodes; incremental fold-stable CV-skill for covariates) +
a patch-spec. NO production fetch-that-writes, NO convergence-file edit, NO commit. The region
expansion in TB1 is flagged as an explicit operator scope decision.

| Lane | Graduate (SYN) | Owns | Exit bar |
|------|----------------|------|----------|
| TB1 | Ground Port Townsend + Bush Point (OrcaHello), widened region gate | `.../graduation/TB1_port_townsend_bush_point.md` | dry-run net-new SRKW presence-days + region-expansion decision memo + `log E` effort plan + runbook |
| TB2 | SST-front gradient covariate (MUR/VIIRS), orthogonalized vs season | `.../graduation/TB2_sst_front.md` | dry-run incremental CV-skill of the front gradient + provenance + patch-spec |
| TB3 | Real Albion feed refresh + run-anomaly covariate (D1) | `.../graduation/TB3_albion_anomaly.md` | live-feed refresh runbook (EC2) + anomaly construction + re-test vs G3 bar (stays WITHHELD) |
| TB4 | Ground ONC / JASCO Boundary Pass (ECHO published dataset) | `.../graduation/TB4_onc_boundary_pass.md` | presence-day extraction plan + duty-cycle effort + independence assessment + runbook |
| TB5 | SalishSeaCast subtidal currents + shear (enables M3-B1) | `.../graduation/TB5_salishseacast_currents.md` | de-tided residual/shear recipe + provenance + conditional payoff (depends on more nodes) |

TB gate: each lane lands a runbook + a DRY-RUN measured estimate + a go/no-go. The actual fetch +
ingest + region expansion + refit are SEPARATE operator-gated waves (TB1's region expansion is the
operator's modeling-scope decision; nothing here writes the served store).

## 4. Wave DE -- dead-end drift audit (read-only)

The SYN named a set of adjudicated dead-ends. This wave audits whether any of them now appear in the
repo as live/recommended/aspirational paths ("drift sources") that could mislead a future actor, and
recommends remediation. READ-ONLY: it applies no edit and commits nothing; it produces a drift-source
register + a prioritized remediation list. The adjudicated dead-end set to hunt for:

- Modeling: full PINN; reservoir computing / ESN; delay-embedding / EDM forecasting; neural TPPs;
  SDE/diffusion movement models; self-exciting **Hawkes-as-skill** (vs the allowed GOF diagnostic);
  GP-modulated intensity / spatial LGCP at current N; synthetic data augmentation; NB->ZI/hurdle
  count upgrade.
- Covariates: CUTI/BEUTI upwelling (out of coverage); HF-radar currents (in-region shadow);
  bathymetry/terrain credited ON THE TEMPORAL GATE (vs its allowed `s_space`/validation role).

| Lane | Scope | Owns | Exit bar |
|------|-------|------|----------|
| DE1 | Methodology + charter TEXTS (`docs/methodology/**`, `.cca/catalogue/**` prose, READMEs) | `.../graduation/DE1_text_drift.md` | register: file -> quote -> why it is now a drift source vs SYN -> recommended edit |
| DE2 | CODE + METHODS (`modeling/**`, `src/aws_backend/**`) -- is any dead-end implemented/wired/served, or at risk of leaking into the served path? | `.../graduation/DE2_method_drift.md` | register: symbol/path -> current behavior -> drift/leak risk -> recommended remediation |
| DE3 | Operator-facing STRATEGY (`ORCHESTRATOR_NOTES.md`, handoff charters, PIML strategy) | `.../graduation/DE3_strategy_drift.md` | register: where strategy still points at a dead-end without the adjudicated caveat -> recommended caveat/edit |

DE gate: the three registers land with concrete file/line/symbol citations + a prioritized
remediation list. **Remediation is RECOMMENDED, not applied** -- any actual edit is a separate
operator-gated step (and the Hawkes diagnostic vs Hawkes-as-skill distinction must be preserved, not
deleted).

## 5. Shape

```
TA  extract-from-existing-data (parallel; prototype+measure, no convergence edit, no served write)
  TA1 occupancy MMPP        TA2 hierarchical NB       TA3 AIS effort
  TA4 in-repo covariates    TA5 shape priors
TB  ground-new-observation (parallel; dry-run+runbook+patch-spec, no fetch-that-writes)
  TB1 Port Townsend+Bush Pt TB2 SST front  TB3 Albion anomaly  TB4 ONC Boundary Pass  TB5 SalishSeaCast
DE  dead-end drift audit (parallel; READ-ONLY register + remediation recommendations)
  DE1 text drift  DE2 method drift  DE3 strategy drift
```

The three waves are independent and can run in parallel; DE is read-only and the safest to run first.
TA and TB findings feed a later, separate, single-editor, operator-gated integrate/deploy/promote
wave. Findings dir: `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/graduation/`.

## 6. Gates / operator decisions

- TA launch; TB launch; DE launch (each an operator gate).
- TB1 modeling-region expansion (out-of-box nodes) -- an explicit operator scope decision.
- Any convergence-file integrate of a TA/TB graduate -- a separate single-editor step.
- Any production fetch-that-writes / ingest / deploy (TB) -- operator-/deploy-gated.
- Any confidence promotion -- a passing gate on SERVED data + a recorded supervisor decision (B.1).
- Any commit or push -- explicit operator request only; surgical staging only.

## 7. Status

- **Wave DE -- COMPLETE (2026-06-27).** Registers landed: `DE1_text_drift.md` (13 drift sources: 4
  high/5 med/4 low), `DE2_method_drift.md` (0 HIGH/2 MED/8 LOW; served code clean, Hawkes contained),
  `DE3_strategy_drift.md` (16: 2 P0/7 P1/6 P2/1 P3). Conclusion: no dead-end leaks into the served
  path; all drift is prose. Remediation is RECOMMENDED, not applied (separate operator-gated step).
- **Waves TA / TB -- RECALIBRATED FROM DE, ready to launch.** `GRADUATION_DISPATCH.md` now carries a
  binding drift-guard preamble (RECALIBRATION FROM DE): SYN section 2 dead-end set overrides any stale
  GO in the source docs TA/TB read (M2 LGCP "GO"; wave_shape objectives; ORCHESTRATOR_NOTES LGCP/ZI;
  wildlife register feed-first L3 + CUTI/BEUTI), and TA/TB patch-specs that touch a flagged doc append
  a DE drift note for the integrate step.

Launch of TA/TB is the next operator gate. Nothing here promotes; effective confidence stays 0.0.
