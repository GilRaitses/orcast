# OS3 findings: EFI forecast-disclosure standard + proper-scoring (CRPS) alongside the deviance gate

Agent: OS3 background subagent, Open-Science Integration (OS) waveset, O0 forecast ML-ops lane.
Date: 2026-06-27 (America/New_York). Repo: `/Users/gilraitses/orcast`. This findings doc is the ONLY
file written (plus one STEP_LOG line). READ-ONLY research plus bounded reachability probes; no
convergence-file edit (`modeling/**`, `src/aws_backend/**`), no served/S3 write, no fetch-that-writes,
no ingest, no deploy, no promotion, no commit, no `git add`. Effective confidence stays 0.0; this
RECOMMENDS and SPECs only.

Hydration read in full first: `WAVESET_CHARTER.md` (section 2 OS3 row), `OS_DISPATCH.md` (OS3 source
pointers + rails), and the repo surfaces `modeling/validation/crossval.py`,
`modeling/validation/diagnostics.py`, `modeling/fit_kernels.py` (`_fitted_payload`,
`_confidence_from_gates`, the `report` dict), `src/aws_backend/promotion/supervisor.py` (the B.1
decision draft).

## 0. Scope and the one honesty statement up front

This lane specs how to (a) wrap the served forecast + confidence in the EFI metadata convention and
(b) add a proper score (CRPS on the NB2 predictive distribution) alongside the existing held-out
deviance-skill gate, WITHOUT changing the promotion bar, the confidence mapping, or the Hawkes
GOF diagnostic. It is disclosure and scoring hygiene plus external-standard alignment. It is NOT a
skill lever: it adds no covariate, no observation, and no parameter, so it does not and cannot move the
held-out CV mean-deviance-skill toward +0.144. Every count below is cited or marked NOT-MEASURED.

## 1. The EFI forecast standard (characterized; reachable; BSD-2-Clause)

Source: Ecological Forecasting Initiative (EFI) forecast standard,
`https://ecoforecast.org/ecological-forecast-standards/` (page reachable, HTTP 200) and repo
`https://github.com/eco4cast/EFIstandards` (reachable; license **BSD-2-Clause**, MEASURED via the
GitHub API; default branch `master`; last pushed 2023-10-19; not archived). The canonical write-up is
Dietze et al., "A community convention for ecological forecasting: Output files and metadata version
1.0" (Ecosphere 2023). BSD-2-Clause is a clean, permissive reuse license.

What the repo provides (MEASURED from the API contents listing): an R package with a metadata
validator (the `R/` + `man/` + `NAMESPACE` package surface) and three vignettes:
`flare-metadata-example.Rmd`, `logistic-metadata-example.Rmd`, `visualization-example.Rmd`. The
validator checks an EML-plus-`additionalMetadata` document against the convention; the vignettes show
building a compliant metadata record for a real forecast and visualizing it. There is no separate
Python validator in the repo (the convention is language-neutral; Python producers emit the same EML +
netCDF/CSV and can validate via the R tool or by schema). Reachability of the R validator from this
environment is NOT-MEASURED (no R runtime exercised here); the convention itself is the deliverable.

The three parts of the standard:

1. Output file tiers (volume vs expertise trade-off):
   - Tier 1: netCDF following CF conventions, with `ensemble` as a dimension where appropriate
     (preferred).
   - Tier 2: a semi-long CSV, one row per unique (issue datetime, prediction datetime, location,
     ensemble member, ...), state variables as columns.
   - Tier 3: like Tier 2 but each row is a summary statistic (mean, upper/lower CI) rather than an
     ensemble member.
2. Metadata: an expansion of the Ecological Metadata Language (EML). Two differences: (a)
   `additionalMetadata` tags carry forecast-specific information (uncertainty propagation, data
   assimilation) plus model-complexity summary fields designed for cross-forecast synthesis; (b) some
   EML tags optional in base EML are REQUIRED for a forecast (temporal resolution, output variables).
   The convention's `additionalMetadata/forecast` block documents the uncertainty classes a forecast
   may carry (initial conditions, parameters, drivers/random effects, process error, observation error)
   each with a present/absent flag and a complexity/propagation descriptor, plus a data-assimilation
   descriptor and a model-complexity summary.
3. Archiving (FAIR, three tiers): (a) archive the forecast BEFORE the verifying observations land,
   in a public archive that auto-uploads, is searchable, and assigns a DOI (not possible for
   hindcasts); (b) also archive the code (open repo or archive with a DOI); (c) also archive the
   running workflow via virtualization (Docker or Singularity).

## 2. Proper-scoring tools (characterized; reachable; licenses MEASURED)

The served forecast is a COUNT forecast: the GLM emits a per-(station, bin) rate `mu` and the
predictive law is NB2 (`Var = mu + alpha*mu^2`); `modeling/validation/diagnostics.py` already
constructs the NB2 predictive via `_nbinom_nq(mu, alpha)` to scipy `nbinom(n=1/alpha, p=n/(n+mu))` for
the PIT. So the natural proper score is the PARAMETRIC NB2 CRPS in closed form, not an ensemble CRPS.

| tool | language | license (MEASURED) | relevant function | applies to |
|---|---|---|---|---|
| `scoringRules` | R (CRAN v1.1.3) | GPL (>= 2) | `crps_nbinom(y, size, prob, mu)`, `logs_nbinom`, `crps(..., family="nbinom"/"pois")` | parametric NB2 / Poisson count predictive (closed form) |
| `scoringrules` | Python (PyPI v0.11.0) | Apache-2.0 | `crps_negbinom(obs, n, prob=p)` (closed form, Wei and Held 2014), `crps_poisson` | parametric NB2 / Poisson count predictive (closed form) |
| `xskillscore` | Python | Apache-2.0 | `crps_ensemble`, `crps_gaussian` (via `properscoring`) | ENSEMBLE or Gaussian forecasts only |

Which applies here: the NB2 parametric CRPS (`scoringrules.crps_negbinom` or scoringRules `crps_nbinom`)
maps directly onto the existing `(n, p)` the PIT already builds, so it needs NO ensemble sampling and no
new predictive object. `xskillscore`'s ensemble CRPS applies only if/when the forecast is emitted as a
sampled ensemble (the EFI Tier-1 netCDF `ensemble` dimension); it is not needed for the current
closed-form count forecast. The logarithmic score is `-log P(y | NB2) = -nbinom.logpmf(y, n, p)`, also
closed form from the same `(n, p)`.

How CRPS complements the existing deviance-skill metric (it does not replace it):

- The existing gate (`crossval.block_cv`) scores held-out POISSON DEVIANCE of the mean rate vs a
  per-effort climatology and reports `mean_deviance_skill = 1 - dev_model/dev_base`. That is a
  mean-rate, log-score-like quantity; it is the promotion-bar metric and is unchanged here.
- CRPS is a strictly proper score on the FULL predictive distribution (it rewards sharpness AND
  calibration together, in the units of the count), evaluated against the same held-out folds and the
  same climatology baseline as a CRPS SKILL SCORE (`1 - CRPS_model/CRPS_clim`), so it sits on the same
  "beats climatology" footing as the deviance-skill gate but reads the whole NB2 law, not just the mean.
- The PIT gate (`_held_out_pit`) already tests calibration (KS vs uniform); CRPS adds the
  sharpness-given-calibration axis the PIT does not score. Together (deviance-skill + PIT + CRPS) they
  are the EFI-style triad: accuracy, calibration, sharpness. CRPS is reported alongside; it does not
  enter `_confidence_from_gates` and does not change the +0.144 bar.

A self-contained closed-form alternative (no new dependency): the NB2 CRPS can be computed in-repo from
`scipy.stats.nbinom` via the Wei and Held (2014) closed form, so the spec does not require adding
`scoringrules` as a dependency unless the operator prefers the vetted implementation. Both paths give
the same number.

## 3. Mapping to the repo surfaces

### 3.1 The served disclosure and gate surfaces today (read, MEASURED)

- `_fitted_payload` (`fit_kernels.py`) builds the served payload: `confidence`, `fitted_at`,
  `bin_hours`, `version`/`repr_id`/`run_id`, `dataset_snapshot_id`, `acoustic_span`,
  `detections_unreviewed_candidates`, `season_extrapolated`, `covariates_excluded`,
  `smoothness_regularized`, `smoothness_lambda`, plus the fitted kernels (`to_fitted_dict`).
- The `report` dict carries the validation surface: `cv` (`gate_pass`, `mean_deviance_skill`,
  `per_fold_deviance_skill`), `time_rescaling.pooled_pass_exp`, `pit` (`calibrated`, `ks_pval`),
  `pit_poisson`, `level1_psth`, `metrics` (`mcfadden_r2`, `deviance`, `loglik`, `aic`, `bic`),
  `family`, `dispersion_alpha`, `pearson_dispersion`, `covariates_fit`, `station_effects`,
  `n_detections`, `n_bins`, `effort_assumed_continuous`, `overdispersion`, `acoustic_span`,
  `generated_at`.
- `_confidence_from_gates` maps gates to confidence (saturating CV-skill term + 0.5/0.5 gate factor +
  PIT bonus + Level-1 bonus, capped), calibrated so confidence crosses the 0.6 promote threshold only at
  CV skill about +0.144. MUST NOT be changed by this lane.
- `supervisor._deterministic_decision` drafts promote/hold: promote iff `confidence >= 0.6` AND
  `cv_gate_pass` AND `pit_calibrated`; the human records the call in a DECISION_RECORD (B.1; the
  promotion protocol is `research/forward/G2_promotion_protocol.md`). MUST NOT be changed.

### 3.2 EFI metadata field mapping (which EFI fields the existing fields fill, what is missing)

| EFI convention field | existing repo source | status |
|---|---|---|
| `forecast` issue datetime | `_fitted_payload.fitted_at` / `report.generated_at` | MEASURED (present) |
| temporal resolution (required EML) | `bin_hours` | MEASURED |
| output variable(s) | detection-count rate `mu` per (station, bin); `covariates_fit` | MEASURED |
| spatial location | `station_effects` keys + station coords (`STATION_COORDS`) | MEASURED |
| dataset / provenance id | `dataset_snapshot_id`, `repr_id`, `run_id` | MEASURED |
| process uncertainty | NB2 `dispersion_alpha` (`Var = mu + alpha*mu^2`) | MEASURED |
| parameter uncertainty | ridge / partial-pool penalty + the fitted CIs (`smoothness_lambda`, baseline_enablers) | MEASURED (present, qualitative) |
| driver/covariate uncertainty | `covariates_fit`, `covariates_excluded`, `tide_overlaps_acoustic` | MEASURED (presence) |
| observation error | `detections_unreviewed_candidates`, `effort_assumed_continuous` (the OS1 `log E` gap) | MEASURED (disclosed as caveats) |
| initial conditions / data assimilation / propagation | none (this is a static GLM, not a state-space DA forecast) | absent by design (state `present=false`) |
| validation metadata | `cv.mean_deviance_skill`, `pit.calibrated`, `time_rescaling`, `metrics`, the new CRPS (section 3.3) | MEASURED |
| model complexity summary | `covariates_fit` count, `station_effects`, `family`, `n_bins`, `n_detections` | MEASURED |
| forecast DOI / FAIR archive-before-observations | none today (artifacts go to the models S3 bucket, not a DOI archive) | **MISSING** (operator gate) |
| code DOI | the git repo exists; no release DOI minted | **MISSING** (operator gate) |
| containerized workflow archive | Docker/Singularity image of the fit workflow | **MISSING** (optional EFI tier) |

So the existing fit-report already fills most required EFI fields directly; the gaps are the FAIR
archiving tier (a DOI minted for the forecast before observations land, a code DOI, an optional
container), which are operator/infra decisions, not model changes.

### 3.3 Where CRPS attaches (additive, no-op to confidence and promotion)

CRPS is computed on the SAME held-out folds the PIT already uses. `_held_out_pit` (`fit_kernels.py`)
already refits per fold and holds the per-fold `(mu, alpha)` NB2 predictive, so the CRPS is computed in
the same loop or a sibling helper, then written to a NEW `report["crps"]` block:
`{ "nb2_crps_mean", "per_fold", "crps_skill_vs_climatology", "logscore_mean" }`. It is REPORT-ONLY: it
is not read by `_confidence_from_gates` and not read by `supervisor._summarize_gates`, so confidence and
the promote/hold decision are byte-identical. It can optionally be surfaced as additional cited evidence
in the DECISION_RECORD, but never as a gate that changes the bar.

## 4. Value (honest)

This is disclosure/scoring hygiene and external-standard alignment. Concretely it buys: (a) a
machine-readable, EFI-compliant metadata record so the served forecast is interoperable, searchable, and
citable (and the uncertainty/observation-error caveats, including the OS1 flat-`log E` gap, are
disclosed in a standard schema rather than ad hoc payload keys); (b) a strictly proper score (CRPS) that
reads the full predictive distribution, complementing the mean-rate deviance-skill and the PIT
calibration test as the accuracy/calibration/sharpness triad; (c) FAIR archiving discipline
(archive-before-observations + DOI) that grounds the served forecast record and the supervisor decision.
It does NOT add skill: no covariate, observation, or parameter changes, so it cannot move the held-out
CV mean-deviance-skill toward +0.144 and earns no confidence. Effective confidence stays 0.0.

## 5. PATCH-SPEC (for the later single-editor integrate; NO code edited here; byte-identical no-op default)

Not applied in this run. Surfaces a later single editor would touch, each additive and default-inert:

1. New pure functions in `modeling/validation/diagnostics.py` (no I/O, mirrors the existing pure
   diagnostics): `crps_nbinom(y, mu, alpha)` (closed form via the existing `_nbinom_nq(mu, alpha)` and
   `scipy.stats.nbinom`, the Wei and Held 2014 form; reduces to `crps_poisson(y, mu)` when `alpha==0`)
   and `crps_skill(y, mu, mu_base, alpha)` returning `1 - CRPS_model/CRPS_base`. Pure additions; they
   change no existing function output, so all current reports are byte-identical until called.
2. `modeling/validation/crossval.py` `block_cv`: OPTIONAL per-fold CRPS. Because `block_cv`'s
   `fit_predict` returns only `mu` (no `alpha`), the clean attachment is NOT here; prefer computing CRPS
   in the `_held_out_pit` path (which already has per-fold `(mu, alpha)`). If a per-fold CRPS in
   `block_cv` is wanted, add an OPTIONAL `predictive_alpha` callback defaulting to `None`; with `None`
   the function is byte-identical (no CRPS computed).
3. `modeling/fit_kernels.py`: add `report["crps"]` (section 3.3) computed alongside `_held_out_pit`.
   Do NOT touch `_confidence_from_gates` or its constants, and do NOT add `crps` to
   `supervisor._summarize_gates`. The confidence number and the promote/hold draft are unchanged
   (verifiable: with the CRPS block present, `_confidence_from_gates(report)` returns the identical
   value because it reads only `cv`, `time_rescaling`, `pit`, `level1_psth`).
4. New pure module `modeling/disclosure/efi_metadata.py` (or a function): `to_efi_metadata(payload,
   report) -> dict` mapping the section-3.2 fields into an EFI `additionalMetadata` record, and
   `to_efi_tier3_csv(forecast)` emitting the Tier-3 summary CSV (mean, lower/upper CI per issue and
   prediction datetime and location). Emission is OFF by default (gated by an explicit flag, e.g.
   `ORCAST_EMIT_EFI=1` or a `run_fit(emit_efi=False)` default), so served S3 artifacts are
   byte-identical; when on, it writes an ADDITIONAL sidecar artifact next to `fit_report.json`, never
   replacing or mutating the existing coefficients/report.
5. Validate the emitted record against the EFI convention (the BSD-2-Clause R validator, or a schema
   check) as a CI/offline step; this is a check, not a served-path change.
6. FAIR archiving (operator/infra, not a model change): mint a DOI for the forecast artifact before the
   verifying observations land (a public archive that auto-uploads and is searchable), a code DOI, and
   optionally a Docker/Singularity image. These are the section-3.2 MISSING fields and are
   deploy/operator-gated.

Promotion remains a separate B.1 supervisor decision on served data; nothing here promotes. The Hawkes
self-excitation report stays exactly as is (a GOF diagnostic that never feeds the served intensity,
timing verdict, or confidence); CRPS does not touch it.

## 6. DE drift note

None required. This doc specs additive code surfaces (`diagnostics.py`, `crossval.py`, `fit_kernels.py`
report block, a new `disclosure/efi_metadata.py`) and external-standard alignment; it touches no
DE-flagged prose doc (`M2_nonlinear_physics.md`, `wave_shape.yml` objectives, `ORCHESTRATOR_NOTES.md`,
the wildlife register). It is consistent with `research/forward/G2_promotion_protocol.md`: the +0.144
bar, the confidence mapping, and the promote/hold rule are explicitly unchanged. No stale GO is
superseded.

## 7. Return summary

- Doc path: `.cca/catalogue/O0/20260627_open-science-integration/OS3_forecast_standards_scoring.md`.
- EFI standard (BSD-2-Clause, reachable): 3 output tiers (netCDF / semi-long CSV / summary CSV), an
  EML + `additionalMetadata` convention (uncertainty propagation, data assimilation, model complexity;
  some EML tags made required), 3-tier FAIR archiving (forecast-before-observations + DOI, code DOI,
  container). The existing fit-report fills most required fields; the gap is the FAIR archiving/DOI tier
  (operator/infra).
- Scoring (licenses MEASURED): the served forecast is an NB2 COUNT predictive, so the parametric NB2
  CRPS applies (`scoringrules.crps_negbinom`, Apache-2.0; or scoringRules `crps_nbinom`, GPL>=2),
  mapping directly onto the `(n, p)` the PIT already builds; closed-form, no ensemble needed.
  `xskillscore` (Apache-2.0) ensemble CRPS applies only to a sampled-ensemble forecast. CRPS complements
  (does not replace) the deviance-skill gate and the PIT, as the sharpness axis of the
  accuracy/calibration/sharpness triad.
- OS3 GO/NO-GO: **GO (spec/build-gated) on (a) emitting an EFI-compliant metadata sidecar for the served
  forecast and (b) adding a report-only NB2-CRPS block alongside the deviance-skill gate and PIT, both as
  byte-identical no-op-default additions that leave `_confidence_from_gates`, the 0.6/+0.144 promotion
  bar, and the Hawkes GOF untouched. NO-GO on treating any of this as a skill lever: it does not move
  +0.144 and earns no confidence.**
- Single highest-value next action: land the report-only NB2-CRPS block first (closed-form, in-repo via
  `scipy.stats.nbinom`, computed in the existing `_held_out_pit` per-fold loop), since it is the cheapest
  additive disclosure improvement and needs no new dependency or infra; defer the EFI sidecar and the
  FAIR DOI archiving to the operator/infra gate.
- Operator gate hit: FAIR archiving (a DOI minted for the forecast before observations land, a code DOI,
  an optional container) is infra/operator-gated and is the only EFI field set the current pipeline does
  not already fill; adopting `scoringrules` as a dependency vs the in-repo closed form is a minor
  operator preference.
- Confirmation: nothing edited in `modeling/**` or `src/aws_backend/**`, nothing fetched-to-write,
  ingested, deployed, promoted, or committed; EFI/scoring sources accessed read-only; only this one
  findings doc plus a STEP_LOG line written; `_confidence_from_gates`, the promotion bar, and the Hawkes
  diagnostic untouched; effective confidence 0.0.
