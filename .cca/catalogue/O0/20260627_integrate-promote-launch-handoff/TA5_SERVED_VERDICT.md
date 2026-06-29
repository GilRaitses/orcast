# TA5 served-store verdict + recommended supervisor promotion (step 1)

Orchestrator O0 (integrate / measure-on-served / promote). Date: 2026-06-27 (America/New_York).
Repo `main` at `9a00e15`. This is a MEASURED decision aid; nothing here promotes. Effective
confidence stays 0.0 until the operator records a B.1 supervisor decision. No served artifact written
(`write_outputs=False`, `_maybe_write_s3` disabled), no commit.

## What was done

Integrated the TA5 smoothness (roughness) prior into the convergence files, patch-only, default
byte-identical (opt-in via `run_fit(smoothness_prior=True)` / `ORCAST_SMOOTHNESS_PRIOR=1`):
- `modeling/estimator.py` `fit_glm`: optional `smoothness_lambda`/`smoothness_order`; ridge penalty
  `lambda * h^(2*order)` on the Fourier coefficients (`const`/`st__*` unpenalized) via
  `GLM.fit_regularized(L1_wt=0.0)`; penalized fits suppress the delta-method kernel CI bands.
- `modeling/fit_kernels.py` `run_fit`: nested-`block_cv` lambda selection (per outer fold for CV/PIT;
  single nested selection on the full data for the served coefficients), the `n_harmonics=1` control,
  and the honesty report block; serving disclosure that penalized curves are smoothness-regularized
  predictive objects, not unbiased shapes.

Re-measured on the SERVED store under the B.5 env (`ORCAST_STORAGE_BACKEND=aws`, bucket
`198456344617-us-west-2-orcast-aws-backend-raw-payloads`, `us-west-2`), upload disabled.

## Measured served verdict (held-out 5-fold block_cv, NB2)

The live served `acoustic_detections` stream now reads as 4 stations / 2089 detections / 66,899 bins
(the W6 3-node ingest has landed). The smoothness-OFF baseline reproduces the charter's recorded
served W7 state exactly (+0.0778 -> confidence 0.49), validating the harness against the served gate.

### Served 4-station (the binding served gate)

| Variant | per-fold skill | mean | folds>0 | across-fold LB | PIT (KS p) | confidence |
|---|---|---|---|---|---|---|
| OFF (baseline) | -0.038, 0.065, 0.140, 0.066, 0.156 | **+0.0778** | 4/5 | +0.004 | calibrated (0.364) | 0.49 |
| **ON (TA5)** | 0.076, 0.176, 0.242, 0.202, 0.147 | **+0.1686** | **5/5** | **+0.109** | **calibrated (0.090)** | **0.63** |
| n_harmonics=1 control | -- | +0.0835 | 5/5 | -- | -- | -- |

Selected lambda: full-data 0.01; per-fold nested picks `[0.003, 0.003, 0.01, 0.003, 0.01]` (stable,
consistently small -- not a lucky selection). The hard 1-harmonic control reaches only +0.0835, so the
+0.169 lift is GRADED shrinkage of the whole kernel shape, not fewer harmonics (TA5 §3 confirmed on
served data).

### G2 robust-skill check vs the +0.144 bar (served 4-station, ON)

| G2 criterion | requirement | TA5 served (ON) | pass? |
|---|---|---|---|
| point margin | mean skill >= +0.144 | +0.1686 | YES |
| fold stability | >= 4/5 folds positive | 5/5 | YES |
| variance lower bound | mean - t*SE >= +0.078 | +0.109 | YES |
| calibration | held-out PIT calibrated | KS p 0.090 (> 0.05) | YES |
| Level-1 corroboration | a kernel beats its null | diel, lunar, season | YES |

All five robust-skill bands clear on the SERVED store. P0-map confidence 0.63 >= 0.6.

### Served single-station (haro_strait only -- the pre-ingest served fit, for the flagged risk)

| Variant | mean | folds>0 | across-fold LB | confidence |
|---|---|---|---|---|
| OFF | -0.0473 | 2/5 | -- | 0.00 |
| ON (TA5) | +0.0037 | 4/5 | -0.082 | 0.27 |

On the single-station served fit TA5 flips the mean from negative to ~0 and 2/5 -> 4/5 folds (a real
variance-reduction / fold-stability gain) but does NOT clear +0.144 there (mean ~0, LB negative). The
§G risk is realized at single-station scale; the binding served gate is the live 4-station store, where
TA5 clears the bar robustly.

## Supervisor draft (deterministic; `src/aws_backend/promotion/supervisor.py`)

Run on the served 4-station TA5-ON report (`enable_bedrock=false`):

```
recommendation: promote
rationale: Confidence 0.63 (>= 0.6 threshold). Core gates (CV + calibration) pass. Recommend PROMOTE.
cited_gates: held-out CV beats climatology; PIT calibration holds; time-rescaling GOF fails;
             Level-1 null beaten by: diel, lunar, season
```

`time_rescaling_pass` stays false and does not block promotion under the current rule (timing credit
is carried by the adopted bin-level gate in `_confidence_from_gates`, not event-level Exp(1)).

## RECOMMENDED supervisor promotion decision (for the OPERATOR to record -- B.1)

This is a draft for the operator; the agent does not promote. To finalize, the operator records a B.1
decision in `DECISION_RECORD.md` (G2 §3b template) and re-runs the served fit with the prior ON and
the upload ENABLED only as the explicit promotion step.

```
## 2026-06-27 Recorded supervisor decision -- PROMOTE multi-station L2 + TA5 smoothness prior (W7)
- TRIGGER: served 4-station refit, B.4 store, write_outputs=False, upload disabled, ORCAST_SMOOTHNESS_PRIOR on.
- MEASURED: cv.mean_deviance_skill = +0.1686 (folds 5/5, across-fold lower bound +0.109),
  pit.calibrated = true (ks_pval 0.090), level1 {diel,lunar,season} beat null, confidence = 0.63.
- BASELINE (prior OFF): +0.0778 (4/5, LB +0.004) -> confidence 0.49 HOLD (reproduces recorded W7).
- SUPERVISOR DRAFT: promote (deterministic), rationale quoted above.
- ROBUST-SKILL CHECK (G2 §1B): margin >= +0.144 PASS; fold stability >= 4/5 PASS; LB >= +0.078 PASS;
  PIT calibrated PASS; Level-1 null beaten PASS.
- DECISION: <PROMOTE to confidence 0.63 | HOLD>.
- OPERATOR: <name>, <timestamp>. effective_confidence set to 0.63 on this record (or unchanged).
```

## Risks to state on the record

1. The served penalized PIT is calibrated but at KS p=0.090 (vs 0.364 OFF) -- comfortably above 0.05
   but closer to the threshold; re-confirm on the promotion-step refit.
2. Penalized kernel curves are smoothness-regularized PREDICTIVE objects, not unbiased PSTH tuning
   shapes (the 2nd harmonic is deliberately attenuated); serving may use them, publication as unbiased
   shapes must not (TA5 §4). The serving payload now carries `smoothness_regularized: true`.
3. Cross-station kernel consistency remains an L2 quality caveat (not a confidence-map input), and
   event-level time-rescaling stays WITHHELD (Hawkes self-excitation) -- both unchanged by TA5.
4. The integrated served +0.1686 is slightly below the TA5 experiment-store +0.177 (different alpha
   seed / harness); still clears every robust band. The single-station served fit does not clear.

## Rails confirmed

Nothing promoted, deployed, fetched-to-write, ingested, or committed. No served artifact / S3 write
(`write_outputs=False`, `_maybe_write_s3` disabled). Default served fit is byte-identical (prior OFF).
`effective_confidence` stays 0.0 until the operator records the B.1 decision above.
