# TA4 -- in-repo derived covariates (F1 lunar x diel, A1 tide slack/max-flow, A3 +1-harmonic control)

Agent: TA4 (graduation waveset, Wave TA). Date: 2026-06-27 (America/New_York).
Repo: `/Users/gilraitses/orcast`. This is the only file this lane writes.

Scope: prototype-and-MEASURE only. No convergence-file edit, no served write, no
deploy/promote/commit. The production upload was hard-disabled in-process
(`fit_kernels._maybe_write_s3 = lambda: None`) and the fit ran with
`write_outputs=False` semantics (the harness never calls `run_fit`'s write path;
it only reads streams and scores variants through `block_cv`). Effective
confidence stays 0.0. Every number below is held-out, fold-stable 5-fold
`block_cv` mean-deviance-skill, never in-sample.

## 0. Result up front

**NO-GO for both F1 (lunar x diel) and A1 (tide slack/max-flow).** Measured on the
served 4-station data, both covariates have a NEGATIVE marginal held-out CV-skill,
and both are WORSE than the A3 "+1 tide harmonic" control (which is itself
marginally negative). No squeezed nonlinearity survives the 5-fold CV; the added
columns are pure degrees-of-freedom cost. This confirms the M3 prior (small
effects, collinear with the existing additive kernels) at the negative end of its
expected band, and supersedes M3's "GO (cheap, bounded)" prototype ranking for
F1/A1 -- they were worth running because they were nearly free, and the honest
read is that they buy nothing held-out.

## 1. What was built (in-repo signals only)

DRIFT-GUARD honored: in-repo temporal signals only. No terrain/bathymetry touched
the temporal gate (terrain stays `s_space`/validation-only per DE1 rows #6-10 /
DE2). F1 and A1 are constructed entirely from `modeling/design.py` (lunar, diel)
and `modeling/tide_harmonic.py` (the M2/S2/N2/K1/O1 harmonic predictor) -- no new
feed, no field data.

- **F1 lunar x diel** (M3 cat. F1): one column,
  `f1 = illumination_fraction(lunar) * night_weight(diel)`, where
  `illumination_fraction = (1 - cos 2pi*lunar)/2` (0 at new moon, 1 at full,
  matching `covariates.lunar_phase`) and `night_weight = (1 + cos 2pi*diel)/2`
  (1 at local solar midnight, 0 at noon; `diel` is the local-solar day fraction
  in `covariates.diel_phase`). B.2 role: (b) effect-modifier, fit from acoustic
  detections with the `log E` offset. Realized column: mean 0.250, std 0.279,
  max 0.999 -- genuine variance, not degenerate.
- **A1 distance-to-slack / distance-to-max-flow** (M3 cat. A1): two columns.
  From the in-repo harmonic tide reconstruction `V(t)` (R^2 = 0.847 on the served
  currents), slack = sign changes of `V` (7434 over the span), max-flow = sign
  changes of `dV/dt` (7993). For each bin centre, `d_slack` / `d_maxflow` =
  distance to the nearest such anchor, normalized by the M2 half-period
  (6.21 h) and clipped to [0,1]. B.2 role: (b) effect-modifier (the current
  series is a harmonic PREDICTION entered as a covariate, never presented as an
  observed current and never used to locate an animal).
- **A3 control "+1 tide harmonic"** (M3 cat. A3): the existing `k_tide` kernel
  raised from `n_harmonics=2` to `3` (one extra `cos_3, sin_3` block, 2 df). This
  is the honest control: any F1/A1 marginal gain must beat what merely spending
  the same kind of df on one more tidal harmonic would buy.

Linear extra columns (F1, A1) are centred+scaled on the TRAIN fold only and the
transform applied to the held-out fold, so CV does not leak test-fold scale.
Models are NB2 (the served primary family), const + 3 station dummies + per-cyclic
Fourier blocks + extra columns, with the `log(exposure)` offset, scored by
time-blocked `block_cv` (n_blocks=5), exactly the served gate.

## 2. Measured held-out CV mean-deviance-skill (5-fold block_cv, NB2, 4 stations)

Data anchor: 2089 detections, 4 stations, 66,899 station-hour bins; tide harmonic
R^2 = 0.847, overlaps acoustic; selected cyclic covariates = {diel, tide, lunar,
season} all at full phase coverage. The **baseline B0 reproduces the served
+0.078** mean-deviance-skill exactly (0.0778), which validates the harness against
the served fit.

| Model | per-fold skill [f0..f4] | mean skill | min fold | folds>0 | marginal vs B0 |
|---|---|---|---|---|---|
| **B0** (diel2,tide2,lunar2,season2) | -0.0381, 0.0648, 0.1401, 0.0662, 0.1559 | **+0.0778** | -0.0381 | 4/5 | -- |
| **A3** control (tide -> 3 harm) | -0.0428, 0.0556, 0.1328, 0.0676, 0.1570 | +0.0740 | -0.0428 | 4/5 | **-0.0038** |
| **F1** (B0 + lunar x diel) | -0.0685, 0.0657, 0.1316, 0.0613, 0.1514 | +0.0683 | -0.0685 | 4/5 | **-0.0095** |
| **A1** (B0 + slack/max-flow) | -0.0581, 0.0636, 0.1374, 0.0669, 0.1522 | +0.0724 | -0.0581 | 4/5 | **-0.0054** |
| A3 + F1 | -0.0737, 0.0567, 0.1252, 0.0626, 0.1525 | +0.0647 | -0.0737 | 4/5 | -0.0131 |
| A3 + A1 | -0.0621, 0.0555, 0.1303, 0.0677, 0.1534 | +0.0690 | -0.0621 | 4/5 | -0.0088 |

### Marginal CV-skill of each covariate vs the A3 control (the asked-for number)

- **A3 (+1 tide harmonic) marginal vs B0: -0.0038** (one more harmonic already
  buys nothing held-out; it slightly hurts on average).
- **F1 marginal vs B0: -0.0095** -- worse than the A3 control. F1's per-fold
  marginal is negative in 4/5 folds (only +0.0009 on fold 1), and it makes the
  worst fold (f0) markedly more negative (-0.0381 -> -0.0685).
- **A1 marginal vs B0: -0.0054** -- also worse than the A3 control. A1's per-fold
  marginal is negative in 4/5 folds (only +0.0007 on fold 3) and likewise
  degrades the worst fold (-0.0381 -> -0.0581).
- Adding F1 or A1 ON TOP of the A3 control (A3+F1, A3+A1) makes things strictly
  worse still, so the covariates are not buying anything that the harmonic budget
  competes for either.

### Fold-stability read (G2 definition)

The bar is fold-stable >= +0.144 (>=4/5 folds individually positive, across-fold
lower bound >= +0.078). B0 itself does NOT clear that bar (worst fold -0.0381,
below the +0.078 lower bound). Every TA4 addition (A3, F1, A1) lowers the mean,
lowers the worst-fold floor, and does not change the 4/5 positive count -- so all
three move the fit AWAY from fold-stability, not toward it. None approaches +0.144.

## 3. GO / NO-GO

| Lever | Marginal held-out CV-skill | Fold-stable? | Verdict |
|---|---|---|---|
| F1 lunar x diel | -0.0095 (worse than A3 control) | no (worsens worst fold) | **NO-GO** |
| A1 slack/max-flow | -0.0054 (worse than A3 control) | no (worsens worst fold) | **NO-GO** |
| A3 +1 tide harmonic (control) | -0.0038 | no | (control: buys nothing) |

Interpretation (honest, per the lane's purpose): the squeezed nonlinearity the
two derived covariates could carry is already represented by the additive
NB2 kernels (F1 by `k_lunar`+`k_diel`; A1 by the 2-harmonic `k_tide`), so the
5-fold CV credits them nothing and charges them their df. This is the M3 verdict
realized at the low/negative end of its -0.01..+0.03 band. The value delivered is
the clean negative read: there is no cheap in-repo covariate that moves the gate;
the +0.078 -> +0.144 gap is the observation problem SYN names, not a
missing-transform problem.

## 4. PATCH-SPEC (for the later single-editor integrate)

This is a NO-GO patch-spec: the recommended integrate action is to NOT wire F1/A1
or raise `k_tide` to 3 harmonics, and to record why so the decision is not
re-litigated.

- **`modeling/fit_kernels.py`**: NO CHANGE. Do not add F1/A1 columns to the
  served design; keep `n_harmonics=2` for `k_tide` (the +1 harmonic control is
  marginally negative held-out, consistent with `k_tide`'s known cross-station
  instability). `CYCLIC` and `_select_covariates` stay as-is.
- **`modeling/design.py`**: NO CHANGE. Do not materialize `f1_lunar_diel` or the
  A1 distance columns in `build_design`. The construction recipes live here (this
  doc) if a future, higher-N regime wants to re-test them.
- **If a future actor insists on wiring them anyway**: gate behind the same
  held-out, fold-stable `block_cv` check used here, require the marginal vs the
  A3 control to be positive AND fold-stable (>=4/5 folds, worst-fold not
  degraded), and never credit an in-sample improvement. They fail that gate on the
  current 4-station data.
- **Reusable harness**: the scoring path is `modeling/validation/crossval.block_cv`
  driven by per-variant NB2 `(train,test)->mu` closures (const + station dummies +
  per-cyclic Fourier blocks at chosen harmonics + centred/scaled extra columns +
  `log(exposure)` offset). Re-run with the invocation in section 5 if N grows
  (e.g. after TB1 nodes land).

### DE drift note (for the integrate editor)

M3 (`research/signal_modeling/M3_derived_covariates.md`, section 3, ranks 3-4)
lists F1 and A1 as "GO (cheap, in-repo, bounded)". That ranking was a
prototype-recommendation to be scored later, not a graduation. This measurement
supersedes it: at the served 4-station N both are **NO-GO on held-out CV**. When
the integrate editor touches the SYN/M3 covariate plan, annotate F1/A1 as
"measured NO-GO (TA4): negative marginal CV-skill, see
`graduation/TA4_inrepo_covariates.md`" so the cheap-bounded label is not read as a
live GO. (This aligns with the DE posture that stale source-doc GOs are
superseded; no DE-flagged convergence doc is edited by this lane.)

## 5. Reproduction / harness invocation

Environment: `.venv-modeling`, repo root, S3 read with the refit-safety env and
the production upload disabled.

```bash
ORCAST_STORAGE_BACKEND=aws \
ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads \
AWS_REGION=us-west-2 \
PYTHONPATH=/Users/gilraitses/orcast \
.venv-modeling/bin/python <scratch_harness>.py
```

The scratch harness (kept outside the repo tree, not committed) sets
`fit_kernels._maybe_write_s3 = lambda: None`, reads streams via
`fit_kernels.read_streams`, builds the design with the harmonic tide phase, adds
F1/A1 columns (section 1 recipes), reproduces the served covariate selection, and
scores each variant through time-blocked `block_cv` (NB2, n_blocks=5). It writes
no served artifact (`data/models/*` untouched), edits no convergence file, and
calls no deploy/promote path.

## 6. Return contract

- **Doc path:** `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/graduation/TA4_inrepo_covariates.md`.
- **Measured numbers (held-out 5-fold block_cv mean-deviance-skill):** B0 +0.0778
  (reproduces served +0.078); A3 control +0.0740 (marginal -0.0038); F1 +0.0683
  (marginal -0.0095); A1 +0.0724 (marginal -0.0054). F1 and A1 are both negative
  marginal AND worse than the A3 +1-harmonic control; both degrade the worst-fold
  floor; none approaches +0.144.
- **GO/NO-GO:** NO-GO for F1 and NO-GO for A1.
- **Confirmation:** nothing was deployed, fetched-to-write, promoted, or
  committed; no convergence file edited; no served artifact written
  (`_maybe_write_s3` disabled, `run_fit` write path never invoked). mlops-gate
  untouched. Effective confidence stays 0.0.
