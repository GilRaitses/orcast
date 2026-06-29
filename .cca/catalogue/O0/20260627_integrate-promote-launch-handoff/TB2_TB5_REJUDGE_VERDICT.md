# TB2 (SST-front) + TB5 (currents) re-judge vs the clean baseline (step 4)

Orchestrator O0 (integrate / measure-on-served / promote). Date: 2026-06-27. Repo `main` at `9a00e15`.
Serialized after steps 1-2 (TA5 smoothness + TA2/TA3 clean baseline). Nothing promotes; nothing serves
from these covariates. Default served fit byte-identical (aperiodic wire OFF). `mlops-gate` green at
served confidence 0.0; `data/models/fit_report.json` untouched. Effective confidence 0.0.

## What was landed (the estimator support TB2 §3.2 / TB5 §6 named as the prerequisite)

The two levers both need APERIODIC effect-modifier support the estimator did not have (it built Fourier
columns only). Landed as a strict byte-identical no-op (same posture as the TA3 AIS wire when its feed
is infeasible), single convergence-file editor:

- `modeling/estimator.py`:
  - `fit_glm(linear_covariates=())` -- each named covariate present-and-finite enters as ONE
    standardized linear column `{name}__lin` (an effect-modifier with the `log E` offset), NOT a Fourier
    kernel and NOT penalized; `FittedModel` carries `linear_covariates` / `linear_scalers` (train
    mean/sd) / `linear_effects` (coef); `predict` and `log_rate` re-standardize with the stored TRAIN
    scaler (leakage-safe). Empty default -> no columns -> byte-identical.
  - `make_fit_predict(linear_covariates=(), season_orthogonalize=False)` + `_season_orthogonalize`:
    the **B.2 RAIL** for TB2 -- on the TRAIN fold only, each covariate is regressed on the season
    Fourier basis and the train-estimated seasonal component is subtracted from BOTH train and test, so
    only the season-orthogonal residual is ever credited and the residualization is per fold
    (leakage-safe). Default OFF.
- `modeling/design.py` `build_design(linear_by_station=None)`: optional
  `station -> covname -> (times, values)` feed, linearly interpolated onto the bin centres, NaN outside
  the span (handled exactly like the `tide` NaN path). Default None -> strict no-op.

### Synthetic validation (no served data; the feed is operator-gated)

| check | result |
|---|---|
| byte-identical default (`linear_covariates=()`) | **PASS** -- intercept identical to 1e-10, `linear_effects={}` |
| season-COLLINEAR "front" + season-orthogonalize | **PASS** -- marginal CV-skill **-0.0001** (cannot launder `k_season`; B.2 RAIL holds) |
| season-INDEPENDENT informative covariate | **PASS** -- marginal **+0.140**, recovered coef 0.575 (a real effect-modifier IS credited) |

The wire is therefore correct and leakage-safe: it credits a genuinely season-orthogonal driver and
refuses a season-collinear one. It is ready to MEASURE either lever the moment a real feed lands.

## The re-judge (why the clean baseline does not change either verdict)

The step-1/2 clean baseline (TA5 smoothness +0.169/conf 0.63; TA2 partial-pool+ridge +0.155/conf 0.61)
is a **regularization / variance-reduction** win on the SAME 4-clustered-station served store. It does
**not** add a spatial dimension. The leverage of BOTH TB2 and TB5 is fundamentally **spatial** (a front
is *somewhere*; presence is higher near it), and the four served stations sit in one ~8x9 km cluster,
so the field is nearly constant across them. Two consequences:

1. **The geometry that damps both levers is untouched by the clean baseline.** Whatever was damped at
   the overfit FE baseline is equally damped at the regularized baseline.
2. **The bar is no longer the covariate's job.** The clean baseline already clears +0.144 via variance
   reduction, so a small geometry-damped covariate is no longer load-bearing for promotion; adding a
   weak/noisy column to an already-calibrated fit risks a **negative** marginal. The keep/drop test is
   now strictly "does it add fold-stable MARGINAL skill ON TOP of the regularized baseline," a higher
   hurdle than against the old FE baseline.

### TB2 -- SST-front gradient: GO-CONDITIONAL, marginal NOT-MEASURED here, demoted

- **Real marginal: NOT-MEASURED.** TB2 §1.3 already measured that the canonical MUR hosts
  (PFEG/PO.DAAC ERDDAP) reset from this sandbox; only a 5 km blended cross-check was reachable, which
  under-states channel fronts and cannot be used for the gated number. With no reachable MUR/VIIRS feed
  the season-orthogonal front column cannot be built, and **fabricating it would violate B.2**. The
  measurement is gated on the operator feed (EC2/S3 escape hatch per B.9), then run through the
  now-landed `season_orthogonalize=True` wire vs the regularized baseline.
- **Re-judge:** TB2's own expected band was +0.01-0.03 (up to +0.05) marginal against the OLD baseline.
  Against the clean baseline that already clears the bar, its bar-closing rationale is **gone**; it
  remains a genuinely independent physical driver but is **demoted** to a refinement to be measured only
  if/when the feed lands. **Keep/drop = DEFER (do not drop the wire; drop it from the near-term
  promotion path).** GO stays CONDITIONAL on (a) sourcing MUR/VIIRS (not 5 km blended), (b) the
  season-orthogonal residual showing fold-stable POSITIVE marginal vs the regularized baseline,
  (c) absolute SST never entering (B.2 RAIL, enforced by the landed orthogonalization).

### TB5 -- SalishSeaCast subtidal currents: NO-GO at current N, deferred behind TB1/TB4

- **Re-judge: unchanged -- NO-GO at the current 4-clustered-station geometry.** TB5 §5 is binding:
  the spatial-front leverage does not exist until presence is spatially resolved, and the temporal
  residue is collinear with `k_tide`/`k_lunar`; scoring it now measures ~0 at best and laundered tidal
  variance at worst. The clean baseline does not add spatial separation, so nothing in step 1-2 unlocks
  it.
- **Integration order is binding (TB5 §6): never integrate B5 before the TB1/TB4 nodes.** Step 3's TB4
  measurement returned only **6 disjoint-epoch SRKW summer presence-days** (Boundary Pass, JJA-2016
  only) and is **GO-conditional-DEFERRED, not ingested**; TB1's nodes add 0 summer days. So TB5's
  unlock precondition -- spatially separated nodes actually in the served store -- is **still unmet**.
- **Real marginal: NOT-MEASURED (correctly not attempted).** SalishSeaCast reachability is also
  NOT-MEASURED (TB5 §1). The shared aperiodic wire above already covers TB5's estimator need
  (`subtidal_conv`/`subtidal_strain`/`okubo_weiss` are aperiodic columns by the same path); TB5
  additionally needs the de-tide module (`modeling/subtidal_currents.py`) + the collinearity guard,
  which are **deliberately NOT landed now** per TB5 §6 ("integrating it before the nodes wires a
  covariate that cannot pay off"). **Keep/drop = DEFER, strictly after TB1/TB4 node grounding.**

## Honest reading

- Step 4's keep/drop decision resolves to **DEFER both** on the served store as it exists today: TB2's
  feed is unreachable here (marginal NOT-MEASURED, fabrication refused) and its bar role is gone under
  the clean baseline; TB5 is geometry-blocked and order-gated behind node grounding that has not landed.
  Neither is dropped as a future lever; both are dropped from the near-term promotion path.
- The reusable aperiodic + season-orthogonal estimator support is now in place and proven leakage-safe,
  so when an operator lands a MUR/VIIRS or SalishSeaCast feed the marginal is a single
  `write_outputs=False` `block_cv` run vs the regularized baseline -- no further convergence edit
  needed for TB2; only the de-tide derive module remains for TB5 (gated on nodes).

## Rails confirmed

No promotion, deploy, ingest, field fetch-to-write, store write, S3 write, or commit. No covariate
value fabricated (real marginals MEASURED would require feeds unreachable here; left NOT-MEASURED).
Default served fit byte-identical (aperiodic wire OFF). `mlops-gate` ALL PASS at served confidence 0.0.
`data/models/fit_report.json` untouched. `modeling/` stays untracked. Effective confidence 0.0.
