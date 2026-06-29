# DE2 -- code / method dead-end drift register

Agent: DE2 (Wave DE, graduation waveset). Date: 2026-06-27 (America/New_York).
Scope: `modeling/**`, `src/aws_backend/**` only. Authority: SYN section 2 dead-ends; M1 sections
1.5/1.6-1.8; M2 sections 5-10; M3 categories B/E. Mode: read-only audit; recommend only; no deploy,
no fit-write, no commit. (Audit run by the DE2 subagent; landed to disk by the orchestrator because the
read-only explore agent cannot write files. Content is the subagent's verbatim register.)

## Executive summary

The served acoustic forecast path is a log-linear NB2 GLM with Fourier kernels on **`diel`, `tide`,
`lunar`, `season`** only. None of the adjudicated dead-end MODEL families (PINN, reservoir/ESN, EDM,
neural TPP, SDE-movement, GP/LGCP, synthetic augmentation, NB->ZI/hurdle upgrade) are implemented or
reachable from the default fit or `KernelForecaster` serving.

**Hawkes** is implemented but correctly isolated as an event-level GOF diagnostic inside
`_time_rescaling_report`, with explicit `diagnostic_only: True` in the fit-report payload.

Dead-end COVARIATES (CUTI/BEUTI, HF-radar currents, terrain-on-temporal-gate) have no adapters or
kernel wiring in scope. Bathymetry exists only for `s_space` / spatial metadata, not temporal kernels.

Remaining risks are operator/API misread (Hawkes branching in the gates JSON) and stale inline comments
that could mislead a future integrator -- not live method leakage.

**Hawkes correctly contained: YES.** Drift/leak risk counts: **HIGH 0 | MEDIUM 2 | LOW 8.**

## Register

| # | Symbol / path | Current behavior | Reachable from serving / default fit? | Risk | Recommended remediation |
|---|---------------|------------------|---------------------------------------|------|-------------------------|
| **GO -- Hawkes containment** |
| G1 | `_station_intensity_fn` -- `modeling/fit_kernels.py:485-530` | Builds `exp(b0 + station + Fourier kernels + log E)` from fitted GLM only; no history/self-excitation term | Yes (time-rescaling integrand) but kernel-only -- same form as serve | None (confirmed good) | CONFIRM: Hawkes is not here. Keep as the single source of truth for continuous intensity. |
| G2 | `KernelForecaster.log_intensity` -- `src/aws_backend/kernel_model/serve.py:324-345` | `intercept + station_effects + kernels[diel,tide,lunar,season]`; stdlib-only serve path | Yes -- provenance, sighting-assist, exploration tools | None (confirmed good) | CONFIRM: no Hawkes, no spatial/temporal dead-ends. |
| G3 | `_fit_hawkes1`, `_hawkes1_rescaled` -- `modeling/fit_kernels.py:1274-1351` | MLE single-exp Hawkes; docstring: "used ONLY as event-level GOF diagnostic... never added to served intensity" | No -- called only from `_time_rescaling_report` | None (present, contained) | Preserve diagnostic; add API remapping (see M1 row). |
| G4 | `_time_rescaling_report` -> `self_exciting` -- `modeling/fit_kernels.py:1405-1495` | Fits Hawkes per station; writes `diagnostic_only: True`, branching ratios, pooled KS; does not change intensity or confidence directly | No to served lambda; Yes to `fit_report.json` -> `/api/gates` | Low-Med (read misinterpretation) | Gate API: move under `diagnostics.*`; keep in fit report with banner. |
| **GO -- Default fit covariate boundary** |
| G5 | `CYCLIC`, `_select_covariates` -- `fit_kernels.py:61,793-832` | Default fit covariates = `("diel","tide","lunar","season")`; drops tide on non-overlap; drops low phase-coverage (e.g. `season_extrapolated`) | Yes -- `run_fit` -> `fit_glm` -> `fitted_kernels.json` | None (confirmed good) | Add regression test: `covariates_fit` subset of `CYCLIC` unless explicit fit_plan override. |
| G6 | `build_design` -- `modeling/design.py:130-143` | Columns: `y, exposure, diel, lunar, season, tide`; no salmon, depth, CUTI, currents-as-kernel | Yes -- sole design input to default fit | None (confirmed good) | CONFIRM: terrain/salmon cannot enter fit without design/fit_kernels change. |
| G7 | `fit_glm` / `PRIMARY_FAMILY="negbin"` -- `estimator.py:185-276`, `fit_kernels.py:83,682` | NB2 or Poisson GLM only; families restricted to `{poisson, negbin}` | Yes -- default fit + Lambda handler | None (confirmed good) | CONFIRM: no ZI/hurdle/LGCP/GP path exists. |
| **GO -- Spatial / terrain role split** |
| G8 | `BathymetryAdapter`, `spatial_enrichment.py` | ETOPO1 depth for grid cells; doc: "static spatial covariate behind `s_space`" | No to temporal kernels; Yes to spatial metadata / ingest | None (confirmed good) | CONFIRM: terrain is `s_space`/validation-only per M3-E. |
| G9 | `_spatial_provenance` -- `src/aws_backend/routers/kernel.py:65-79` | Returns `depth_m` as metadata; explicit note: "Intensity is temporal-only... not yet fitted as s_space" | Yes -- `/api/provenance` only (metadata) | None (confirmed good) | Keep note; do not add depth to `KernelForecaster.kernels`. |
| G10 | `_spatial_covariate_summary` -- `fit_kernels.py:427-441` | Depth min/max in fit report disclosure only; not merged into design matrix | No to fit/serve lambda | None (confirmed good) | No change needed. |
| **GO -- Absent dead-end implementations** |
| G11 | PINN / reservoir / ESN / EDM / neural TPP / SDE-movement / GP-LGCP / pyGAM | Not present in `modeling/` or `src/aws_backend/` Python (grep + `modeling/requirements.txt`: numpy/scipy/pandas/statsmodels only) | No | None | No code removal needed; optional `DEAD_END_METHODS` comment in `fit_plan` schema. |
| G12 | CUTI / BEUTI / HF-radar adapters | Not present in `src/aws_backend/sources/` (no matches) | No | None | CONFIRM: S2 dead-ends not wired. Block in source registry if added later. |
| G13 | NB->ZI / hurdle count upgrade | Not implemented; M1 cites statsmodels `HurdleCountModel` as feasible but unused | No | None | Do not add without TA2 graduation + explicit integrate. |
| G14 | `simulate.py` | Thinning / Poisson bin simulation for tests and null checks only | No -- tests + `test_level2.py` | None (present, contained) | CONFIRM: not synthetic training augmentation (M1 section 1.8 dead-end). |
| **MEDIUM -- Operator / comment drift (not live leakage)** |
| M1 | `GET /api/gates`, `fetch_gates` -- `routers/kernel.py:278-281`, `exploration/tools.py:35-40` | Exposes full `time_rescaling` including `self_exciting.branching_ratios` (0.79-0.96) alongside CV/PIT gates | Yes -- operator UI / exploration | Medium | Remap to `diagnostics.self_exciting_hawkes`; top-level timing gate = bin-level readout only; never show branching as "skill". |
| M2 | Stale comments vs `ADOPT_BIN_LEVEL_TIMING_GATE=True` -- `fit_kernels.py:756-757,1578-1582` | Comments say "NOT adopted / flag defaults OFF"; code sets `ADOPT_BIN_LEVEL_TIMING_GATE = True` and uses it in `_confidence_from_gates` | Yes -- misleads future editors of convergence file | Medium | Annotate comments to match supervisor decision (2026-06-27); cross-ref DECISION_RECORD. |
| **LOW -- Staged / study-only (contained but watch)** |
| L1 | `SalmonRunAdapter` + `ingest_salmon` -- `sources/salmon.py`, `ingest_timeseries.py` | Ingests `salmon_run_index` (incl. climatology fallback); not in `build_design` or `fit_glm` | No to current fit/serve; Yes to store (future wire risk) | Low | If `k_salmon` integrated (TB3), require `real_feed_only AND stock_aligned` gate from `salmon_lag.py`; withhold on climatology (B.3). |
| L2 | `level3_prey_space.py`, `salmon_lag.py` | L3 study: `s_space` precursor + `k_salmon` lag scan; status WITHHELD | No -- study ladder only (`run_studies.py`) | Low | Keep withheld; do not promote to `fit_kernels` without operator wave. |
| L3 | Scratch drivers `_ra_response_scratch.py`, `_rb_conditioning.py` | Standalone experiments; import `salmon_lag` read-only | No | Low | Mark `research/scratch/` or add module header "not reachable from fit/serve". |
| L4 | `time_rescaling_diag.json` rationale -- `studies/reports/time_rescaling_diag.json:340` | Historical text: "honest fix is... Hawkes-type intensity" | No -- static JSON artifact | Low | Add one-line caveat in study README: superseded by bin-level gate + Hawkes-as-diagnostic only. |
| L5 | `/forecast/*` -- `scoring.py`, `routers/forecast.py` | Hotspot heuristic (`aws-deterministic-hotspot-v1`); not kernel model | Parallel path, not dead-end drift | Low (informational) | Document architecture split: kernel = acoustic provenance; hotspot grid = legacy UI forecast. |
| L6 | `env_currents` / NOAA currents -- `sources/noaa.py`, `fit_kernels.py:601-622` | Harmonic tidal phase for `k_tide` only; not HF-radar / SalishSeaCast shear (M3-B1 dead-end at N) | Yes -- tide kernel only | Low | CONFIRM: currents enter as phase driver, not as B1 front covariate. SalishSeaCast integration remains TB5-gated. |
| L7 | NDBC detectability -- `fit_kernels.py:447-462` | Summary metadata: "not yet a fitted animal-behavior kernel" | No to fit | Low | Keep out of `log lambda` unless explicitly graduated as effort/noise in `log E` (TA3). |
| L8 | External prototype `/tmp/rd_burstiness_prototype.py` (M1 ref) | Absent from repo | No | None | N/A -- in-repo implementation is `fit_kernels._fit_hawkes1` only. |

## Prioritized remediation list

### P1 (do before next integrate wave)
1. **API diagnostic remapping (M1):** In `routers/kernel.py` `get_gates` and `exploration/tools.fetch_gates`, structure the response as `gates.timing` -> bin-level readout + event-level verdict (WITHHELD); `diagnostics.self_exciting_hawkes` -> branching ratios, KS, `diagnostic_only: true`, SYN cross-ref. Do NOT remove the Hawkes diagnostic (charter preserve nuance).
2. **Comment sync (M2):** Update `fit_kernels.py` lines ~756-757 and `_bin_level_timing_readout` docstring (~1578-1582) to reflect `ADOPT_BIN_LEVEL_TIMING_GATE = True` and link DECISION_RECORD supervisor decision.
3. **Regression guard:** Test that `fitted_kernels.json` kernel keys are a subset of `{diel,tide,lunar,season}` and that `_station_intensity_fn` output equals the GLM kernel sum (no hidden history term).

### P2 (harden against future drift)
4. **`fit_plan.json` schema:** Document allowed covariates; reject `k_salmon`, `depth`, `sst_front`, etc. unless `fit_plan_id` explicitly graduated.
5. **Source registry gate:** If adding oceanographic adapters, block-list `CUTI`, `BEUTI`, `HFRNet` in `sources/__init__.py` or the ingest router with a SYN dead-end comment.
6. **`k_salmon` wire protocol (when TB3 lands):** Require `SalmonRunAdapter.real_feed_only and stock_aligned` before entering `build_design`; mirror `salmon_lag.py` withhold logic.

### P3 (hygiene)
7. Relocate or banner scratch study modules (`_ra_*`, `_rb_*`) as non-production.
8. One-line caveat on `time_rescaling_diag.json` aspirational Hawkes wording.

## Explicit confirmations (good cases)

| Check | Verdict | Containment |
|-------|---------|-------------|
| Hawkes out of served intensity | PASS | Only in `_time_rescaling_report`; `_station_intensity_fn` and `serve.py` are kernel-only |
| ZI/hurdle/GP/LGCP/PINN/ESN/EDM/neural TPP/SDE | PASS | Not implemented in scope |
| Synthetic augmentation in CV/fit | PASS | `simulate.py` is test/null only |
| CUTI/BEUTI / HF-radar as covariates | PASS | No adapters |
| Terrain on `k_*` temporal gate | PASS | Depth in spatial metadata / L3 study only; temporal fit is CYCLIC-only |
| Hawkes-as-skill | PASS | Branching ratios diagnostic-only; do not feed `_confidence_from_gates` via Hawkes fit |

## Absent / untracked (B.7)

- `modeling/` is local-only; the audit covered 57 files present on disk.
- M1-referenced `/tmp/rd_burstiness_prototype.py` is not in the repo; superseded by in-tree `_fit_hawkes1`.

Nothing deployed, fetched-to-write, promoted, or committed. Effective confidence unchanged (0.0).
