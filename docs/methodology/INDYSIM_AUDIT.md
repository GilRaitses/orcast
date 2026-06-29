# INDYsim audit: reusable kernel-estimation methodology for orcast

What it is: an audit of the `INDYsim` repository (`GitHub: GilRaitses/indysim`, local canonical copy `/Users/gilraitses/InDySim`) for kernel-estimation and point-process methods that can be lifted into orcast's forecast-kernel program.

How it was produced: a wave of three read-only subagents, each auditing one method cluster and mapping it against [FORECAST_KERNELS.md](FORECAST_KERNELS.md) and [CALIBRATION_STUDIES.md](CALIBRATION_STUDIES.md):
- Kernel parameterization / fitting / basis selection / uncertainty — [kernel cluster](e08ee5fa-78fa-4a81-9e95-751955b5bcc4)
- PSTH / reverse correlation / point-process goodness-of-fit — [PSTH cluster](0b9903cf-63a5-4d87-b50b-1cb93ce2a5c5)
- GLMM / validation / manuscript narrative — [GLMM cluster](8d0f7fb6-6adb-4fa5-8240-f2b87ba4e9cc)

All paths below are under `/Users/gilraitses/InDySim/code/` unless noted.

## Headline finding

INDYsim is not just "related" — it is a **worked, published instance of the exact estimator orcast specifies**. The project models optogenetically-driven reorientation ("turn") timing in *Drosophila* larvae (GMR61 channelrhodopsin line, tracked at 20 Hz under a 30 s square-wave LED cycle). The scientific object is a **linear-nonlinear-Poisson (LNP) cascade fit as a negative-binomial GLM with a log link**, with interpretable temporal kernels, a random intercept per unit, leave-one-group-out cross-validation with a pass/fail gate, a binomial null test, time-rescaling/KS calibration, and an explicit "validation is modest, not strong" honesty framing.

That is, line for line, the program in orcast's `CALIBRATION_STUDIES.md`. The only thing that changes is the sensor: a larva instead of a hydrophone.

## The structural match

| INDYsim | orcast |
|---|---|
| Larval reorientation event (`is_reorientation_start`) | Acoustic detection at a hydrophone |
| LED stimulus (30 s cycle: 10 s on / 20 s off) | Cyclic covariate (tide, diel, lunar, season) |
| `time_since_stimulus` (latched LED onset) | Phase within a cycle (hours since flood onset, since sunrise, days since new moon) |
| Track (one larva), random intercept `(1\|track)` | Station (one hydrophone), random effect `a_station` |
| Frame exposure (uniform, 20 Hz) | Station uptime / observation effort `E(x,t)` |
| Gamma-difference temporal kernel | Cyclic kernel `k_diel`, `k_tide`, `k_lunar`, `k_season` |
| NB-GLM log-rate model | `log lambda(x,t)` log-linear Poisson model |

## The four required ports (apply to any lift)

Every reuse below reduces to the same handful of domain changes:

1. **Add the effort offset `log E(x,t)`.** INDYsim assumes uniform exposure (constant frame rate) and folds effort into the intercept. orcast's central methodological risk *is* heterogeneous effort, so the offset is mandatory. Plumbing is trivial (`statsmodels GLM(..., offset=log_effort)`); INDYsim has no worked example of it. This is the single change that separates a portable demo from a defensible orcast estimate.
2. **Swap the causal log-spaced raised-cosine basis for a periodic basis** on the cyclic kernels (tide/diel/lunar/season). INDYsim's `sin/cos` phase terms (`hazard_model.py: compute_phase_covariates`) are already exactly this for the cyclic case.
3. **Fit ≥4 covariate kernels jointly.** INDYsim effectively fits one driven kernel; orcast needs the additive sum of cyclic + spatial terms.
4. **Switch the family NB → Poisson** (orcast's model form is Poisson; keep NB available as an overdispersion robustness check).

## What to lift, by category

### Liftable — copy with minimal edits (same math, rename variables)

| INDYsim asset | orcast target | Effort |
|---|---|---|
| `time_rescaling_test.py` (Brown 2002: rescale IEIs by cumulative intensity, KS vs Exp(1)/Uniform, QQ, per-unit-then-pool) | The cross-cutting point-process GOF behind **every** fitness gate; PIT/reliability gate (L3) | S–M |
| `validate_factorial_cv.py` → `leave_one_experiment_out_cv`, `fit_and_predict` | L2/L3 **held-out CV with a go/no-go gate**; swap group key → time-block, rate-ratio gate → held-out deviance vs climatology | S |
| `compute_loeo_null_test.py` → `binomial_test` (exact binomial + Clopper-Pearson CI + honest interpretation strings) | The **null/shuffle pass-rate test** at every level's gate | S |
| `compute_reverse_correlation.py` → `compute_shuffled_baseline` | L1 **phase-shuffle null** for PSTH, essentially free | S |
| `compute_deviance_residuals.py` → `compute_nb_deviance_residuals` | Residual diagnostics for any station/cell fit | S |
| `add_model_metrics.py` → `compute_null_llf_from_data` | **McFadden pseudo-R² / "beats climatology"** skill reporting | S |
| `compute_effect_sizes.py`, `compute_cliffs_delta.py` | Effect-size reporting for kernel contrasts (diel vs tidal strength) | S |
| `bootstrap_kernel.py` (track → time-block resampling) | Kernel confidence bands | M |

### Adaptable — same skeleton, one structural change

| INDYsim asset | Change for orcast | Effort |
|---|---|---|
| `generate_psth_comparison.py` → `compute_psth_with_ci`, `compute_psth_single_experiment` | Replace the `n_cycles*bin_width` denominator with **per-bin station uptime**; generalize LED-onset alignment to arbitrary cyclic phase | M |
| `generate_psth_vs_kernel_verification.py` (PSTH vs fitted-kernel overlay = the L2 consistency gate) | Add effort normalization; otherwise the `baseline*exp(K)` overlay transfers as-is | M |
| `hazard_model.py` (NB-GLM with raised-cosine bases, `sin/cos` cyclic covariates, exposure offset, cluster-robust SE, `extract_kernel_shape` + `kernel_confidence_bands`, `cross_validate_kernel_params`) | Switch CV to **time-blocked whole-cycle folds**; add the 5 environmental smooths; drop larval covariates (speed/curvature). This is the actual joint estimator (Method 3). | L |
| `fit_biphasic_model.py` → `fit_with_constraints` (penalized likelihood: ridge + 2nd-difference smoothness + per-coef bounds + approx-Hessian SEs) + `select_kernel_bases.py` AIC selection loop | Best single fitter template; add periodic basis + effort offset | M |
| `analytic_hazard.py` → `AnalyticHazardModel`, `simulate_events_thinning` | Coefficient-holding λ-serving runtime + a **generative/null-data engine** to test the GOF battery; replace LED-keyed kernel with `Σ k_*(covariate)` | M |
| `fit_glmm.py` (Bambi `(1|track)` + PyMC + ArviZ) | Rename `track` → `station`: this **is** orcast's station random effect + NB overdispersion + convergence diagnostics in one place | S |
| `prepare_binned_data.py`, `engineer_dataset_from_h5.py` | Template for the **(station, time-bin) count table with effort offset**; `Y` = detections/bin, `exposure` = station uptime, covariates = environmental phase, group = station | M |

### Conceptual — the idea transfers, the code does not

- The **gamma-difference analytic kernel shape** is sensory-transduction-specific; orcast uses periodic splines. But the manuscript's argument — *a compact, interpretable kernel (6 params) matches a flexible black box (12 params) at R²≈0.96* — ports directly as orcast's rationale for separable log-linear kernels.
- The **three-backend strategy** (statsmodels fixed-effects as the primary reported model; glmmTMB/Bambi GLMM only as a robustness check showing coefficients barely move; pure-Python scipy fallback) is a process pattern worth copying so orcast isn't blocked on rpy2/PyMC availability.
- The **explicit rate-calibration disclosure** (apply a global `log(N_emp/N_sim)` correction to β₀, state that it preserves kernel shape and all relative contrasts) is exactly orcast's "calibrate the level, kernels carry the shape" — and a writing template.
- The **"validation is modest"** narrative (report LOEO rate ratio 1.03 ± 0.31, 58% pass, binomial p=0.39, and call it modest) is the literal embodiment of orcast's honesty principle.

## Watch-outs (do not lift these for gates)

- **`cv_analytic_kernel.py` is not real held-out CV.** It perturbs the global fitted kernel with synthetic noise rather than refitting on held-out data. Use `validate_factorial_cv.py`'s LOEO instead.
- **`compare_kernel_forms.py` computes AIC/BIC on the fitted *curve* under a Gaussian assumption**, not on the event data. orcast's gates need data-likelihood deviance, blocked by time.
- **Reverse correlation here is un-whitened STA only.** orcast wants whitened STA / spike-triggered covariance to separate correlated covariates (tide vs current). That piece is new work, not a lift.
- **No effort offset anywhere.** See port #1 — this is the recurring gap.

## Top lifts, ranked across the whole audit

1. **Time-rescaling GOF** — `time_rescaling_test.py` (+ `compute_time_rescaling.py`). The single highest-leverage lift: domain-agnostic, it is the validator behind every L1–L4 fitness gate. Only the λ source changes. **S–M.**
2. **Held-out CV harness with a fitness gate** — `validate_factorial_cv.py`. The operational core of "each level is a go/no-go on held-out data." **S.**
3. **PSTH machinery + phase-shuffle null** — `generate_psth_comparison.py` + `compute_reverse_correlation.py:compute_shuffled_baseline`, with the `generate_psth_vs_kernel_verification.py` overlay as the L2 consistency check. Real work is the effort/occupancy denominator. **M.**
4. **Binomial null test + honest reporting** — `compute_loeo_null_test.py`. ~150 lines of scipy, no domain coupling, encodes the exact honesty posture. **S.**
5. **Joint LNP estimator** — `hazard_model.py` (+ `fit_biphasic_model.py`'s penalized fitter, `prepare_binned_data.py`'s binning, `run_hazard_pipeline.py`'s orchestration). The actual Method-3 estimator; already has effort offset, random grouping, cyclic terms, CI bands. **L.**

## INDYsim as a template for orcast's Level 0–4 build

INDYsim is a single-unit, fully-executed pass through orcast's leveled plan, which makes it a working blueprint:

- **L0 (instrument characterization).** INDYsim's event-detection thresholds + complete-vs-incomplete-track representativeness test → orcast's OrcaHello d′/ROC and station-effort series. Same discipline: characterize the detector before modeling presence.
- **L1 (single-covariate PSTH vs null).** INDYsim's per-condition PSTH + gamma kernel fit validated against permutation/binomial null → orcast's PSTH-vs-phase-shuffle per cyclic covariate.
- **L2 (joint temporal LNP separating correlated cycles).** INDYsim's pooled NB-GLM with additive kernels + the requirement that joint fits agree with marginal PSTHs → orcast adds the effort offset, station random effect (already present as `(1|track)`), and periodic splines.
- **L3 (full field + calibration).** INDYsim's LOEO skill, time-rescaling KS calibration, deviance residuals → orcast's "held-out skill beats baseline; PIT roughly uniform."
- **L4 (population decoding).** No INDYsim equivalent — genuinely new orcast work — but everything feeding it (per-unit LNP fits, honest CV gates, calibrated uncertainty, the modest-until-earned narrative) is demonstrated end-to-end and can be copied as scaffolding around the new decoder.

## Recommended first move

Lift the validation trio first, before touching the estimator: `time_rescaling_test.py` + `validate_factorial_cv.py` + `compute_loeo_null_test.py`. They are low-effort, domain-agnostic, and they are the gate enforcers — having them in place means every subsequent estimator change is measured against an honest held-out standard from day one.
