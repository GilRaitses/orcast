# STEP_LOG, MLOps wavesets (MLM + MLO)

All times America/New_York.

## 2026-06-27

- Chartered MLM (covariate modeling) and MLO (production platform) from
  `docs/methodology/FORECAST_KERNELS.md` and `CALIBRATION_STUDIES.md`, grounded in the cited
  ecology (Olson 2018; Thornton 2022; Chinook-tracking).
- Wrote `MLM_CHARTER.md`, `MLO_CHARTER.md`, `wave_shape.yml`.
- Scaffolding to follow: `modeling/studies/` (L0..L3 study scripts + gates), MLO-CI gate.

## 2026-06-27 (scaffolding executed)

- Built `modeling/studies/` (pure stdlib): `common.py`, `level0_detector.py`,
  `level1_psth.py`, `level2_joint.py`, `level3_prey_space.py`, `run_studies.py`. Reuses the
  cached OrcaHello index and the CAND set so it runs without the flaky live API.
- Ran the ladder (honest verdicts):
  - L0 detector: withheld (per-station effort + precision computed; ROC AUC needs scored feed).
  - L1 PSTH diel: PASS (modulation 1.79 beats the phase-shuffle null, p=0.0005, on 1359 cached detections).
  - L2 joint temporal: FAIL (held-out skill -0.018, time-rescaling KS fails, tide/season withheld by phase coverage). Confidence stays 0%.
  - L3 prey+space: withheld (s_space density precursor assembled from CAND; prey series + effort model + visual validation pending).
- MLO: delivered `tools/waves/gates/mlops-gate.sh` + wired `mlops-gate` into `run-gate.sh`.
  The gate runs the ladder and enforces the honesty guard (served confidence must not exceed
  what the gates earned). `./tools/waves/run-gate.sh mlops-gate` returns zero.
- MLO feature store / registry / scheduled retrain / monitoring remain chartered; the AWS
  infra (EventBridge, Step Functions, dashboards) is operator/deploy-gated.

## 2026-06-27 (MLM frontier parallel waves)

Dispatched three self-contained parallel subagent waves (orchestrator owns verification;
subagents wrote only their named surfaces, no commits).

- M-L0 (detector ROC/d', NOTES 6.2): re-pulled the OrcaHello reviewed outcomes live (403/SSL
  flake, succeeded with retries) into `orcahello_index.confidence.cache.json` (977 records;
  758 paired confidence+label: 423 confirmed, 335 false_positive). Extended
  `level0_detector.py` with a stdlib rank AUC (tie-averaged), 1000-sample bootstrap CI, and a
  log-linear-corrected d'. Verdict: **L0 PASS** — ROC AUC 0.879 (95% CI 0.856-0.902), d' 1.62.
  Detector is now characterized; effort portion was already satisfied.
- M-TIDE (PIML tide harmonic, NOTES 3.1/6.1): added `modeling/tide_harmonic.py` (M2/S2/N2/K1/O1
  least-squares model) and `modeling/studies/tide_coverage.py`. Fit to real NOAA harmonic
  current predictions (PUG1701/1702/1703, 50,112 samples), reconstruction R^2 0.970. Tide phase
  coverage over the acoustic timestamps rises to **1.000** vs the 0.42 baseline that excluded
  k_tide. The coverage exclusion that fails L2 is now liftable. The actual joint refit did NOT
  run: the AWS data store probe returned NoSuchBucket, so `data/models/fit_report.json` is
  unchanged and the L2 joint verdict stays **FAIL / confidence 0%** (honest). Joint refit with
  k_tide is pending AWS data access.
- M-L3 (salmon lag + s_space, NOTES 6.4): added `modeling/studies/salmon_lag.py` (daily presence
  vs run-timing lag scan over +/-30 d, circular-shift permutation null) and wired its summary
  into `level3_prey_space.py`. Source was the documented climatology fallback (live Albion/DART
  not reached), so the lag (best -30 d, r -0.10, p 0.33) is informational and **L3 stays
  WITHHELD** — cannot earn k_salmon credit on a placeholder feed.

Ladder after the waves: L0 PASS, L1 PASS (diel), L2 FAIL (frontier), L3 WITHHELD.
`./tools/waves/run-gate.sh mlops-gate` returns zero; honesty guard holds (served confidence 0.0
consistent with L2 fail). Effective confidence unchanged at 0%.

## 2026-06-27 (L2 follow-up: harmonic k_tide refit, operator-approved)

- Resolved the AWS store access: the timeseries data is in bucket
  `198456344617-us-west-2-orcast-aws-backend-raw-payloads` (region us-west-2), not the config
  default `orcast-raw-payloads` (that mismatch was the M-TIDE NoSuchBucket). acoustic_detections
  has haro_strait; env_currents has pug1701/1702/1703.
- Integrated the harmonic tide into the fit pipeline (local-only modeling tree, like the rest of
  it): added `HarmonicTidalPhase` to `modeling/tide_phase.py` (drop-in for the TidalPhase
  interface, backed by `modeling/tide_harmonic.HarmonicTide`), and `modeling/fit_kernels.py` now
  prefers the harmonic phase when currents exist (reconstruction R^2 > 0.5), falling back to the
  onset-interpolation TidalPhase otherwise. Recorded `tide_model` + `tide_reconstruction_r2`.
- Refit against the real S3 store (production model-artifact upload disabled: a confidence change
  is a recorded supervisor decision, not a refit side effect). Result, honest:
  - `k_tide` NOW ENTERS the joint fit: covariates_fit = [diel, tide, lunar]; tide phase coverage
    0.42 -> 1.00 (harmonic R^2 0.847 on the pooled pug170x current series; 18,480 current records).
  - L2 still FAILS: held-out CV mean deviance skill -0.047 (slightly worse than the -0.018 without
    tide), time-rescaling KS still fails, confidence stays 0.0. Adding k_tide did not earn skill.
    Season still excluded (0.75 coverage).
  - Takeaway matches NOTES section 4: the single-station sparse-count regime, not the covariate
    list, is the binding constraint. The harmonic model removed the coverage blocker so k_tide is
    now a fair test; the data on one station does not support positive skill.
- Updated `modeling/studies/reports/level2_joint_temporal.json` (now shows tide fitted, season
  withheld) and fixed `level2_joint.py` to name the actual excluded covariate(s) rather than the
  stale "tide/season" string. mlops-gate stays green; honesty guard holds (served confidence 0.0).

## 2026-06-27 (multi-station experiment, WILDLIFE recommendation #1)

- Acted on the WILDLIFE register's top recommendation (fit OrcaHello on all in-region Orcasound
  nodes). The production acoustic_detections stream has only haro_strait (761); the cached
  OrcaHello index carries three more in-region nodes (orcasound_lab 1029, andrews_bay 265,
  north_san_juan_channel 34). Built `modeling/studies/level2_multistation.py`: combine the
  production haro_strait stream with the cached nodes into a local memory store (no production
  store write), add the S3 harmonic-tide currents + uptime, and run the standard joint fit.
- Result (EXPERIMENT, not promoted): 4 stations, 2089 detections. All four temporal kernels now
  fit (diel/tide/lunar/season, phase coverage 1.0 each). Held-out CV mean deviance skill flips
  POSITIVE: +0.078 (4/5 folds) vs the single-station baseline -0.047. This is the first time the
  model beats climatology out of sample, and it confirms the binding constraint was the
  single-station regime, not the covariate list.
- Still FAIL / confidence stays 0% (honest): time-rescaling pooled KS still fails (p=0.0), and the
  L1 cross-station consistency is now testable (4 stations) but NOT yet consistent (per-kernel PSTH
  correlations 0.14-0.34, below the 0.5 bar). The experiment's internal gate score would be 0.5,
  but it is explicitly unpromoted (write_outputs disabled, mixed-provenance spike train, no
  supervisor decision). `modeling/studies/reports/level2_multistation.json` records this.
- This study imports the heavy fit pipeline, so it runs under .venv-modeling and is NOT added to
  run_studies / mlops-gate (which stay pure stdlib). mlops-gate remains green; served confidence 0.0.

## 2026-06-27 (frontier externalized as a parallel-subagent waveset)

- Operator asked to externalize the L2/L3 frontier as a waveset for parallel subagents, mirroring
  the terrain-bathymetry project home. Confirmed scope: Wave 1 = the L2-unblock modules (effort/log E
  for time-rescaling, cross-station consistency) PLUS the disjoint backend tracks (3-node ingest
  recipe, Albion/DART salmon validation), all in parallel; home = extend this existing
  `20260627_mlops/`; model = inherit.
- Wrote, into this home: `WAVESET_CHARTER.md` (parallel-dispatch canon; execution model with the
  convergence files named, refit-upload-disable, env split, no-agent-commits; the three waves; the
  per-agent prompt skeleton; gates + return contract; restated locked B-items), `DECISION_RECORD.md`
  (code surface verified from the repo + confirmed decisions + risks), `WAVE1_DISPATCH.md` (five
  self-contained agent prompts A-E, READY not launched), and a navigation `README.md`. Extended
  `wave_shape.yml` with a `frontier_dispatch:` block (W1/W2/W3 execution waves) alongside the
  existing `families:` level ladder (gate definition), without overwriting it.
- Convergence files for collision control: modeling `fit_kernels.py` + `studies/level2_multistation.py`;
  backend `sources/salmon.py` + `ingest_timeseries.py`. Wave 1 agents own only NEW files
  (`modeling/effort.py`, `modeling/studies/time_rescaling_diag.py`,
  `modeling/studies/cross_station_consistency.py`, `src/aws_backend/ingest_multistation.py`,
  `src/aws_backend/sources/salmon_validation.py`) and never edit a convergence file.
- No agents launched, no commit, no push. Wave 1 launch is the next operator gate.

## 2026-06-27 (Wave 1 launched + completed, operator go "execute")

Five parallel subagents ran (inherit model, none edited a convergence file, validate-only, no
agent commits, no production store / model-bucket write, S3 upload disabled). All five returned
honest measured results. New files owned (all local-only/untracked except the catalogue specs):

- A effort/log E (`modeling/effort.py` + `modeling/WIRING-effort.md`): built a per-station effort
  -> `log E` offset + exposure with a cross-namespace key resolver (`rpi_*` uptime keys vs acoustic
  station keys; that mismatch was the real cause of `effort_assumed_continuous=True`). Module is
  correct on synthetic transitioning uptime (log E std 3.26). But the REAL data is degenerate:
  `station_uptime` covers 2026-06-20..27 only, detections are 2020-2021 (zero overlap), constant
  within window, and `haro_strait` has no uptime node, so real per-station `log E` is flat.
  Conclusion: wiring effort is correct but a no-op today; it will not move time-rescaling.
- B time-rescaling diagnostic (`modeling/studies/time_rescaling_diag.py` + report): pinned the cause
  of pooled KS p=0.0. It is point-process burstiness/clustering, NOT effort, grid, or the kernels.
  All 4 stations fail individually; a constant-rate Poisson fails identically; 82% of pooled
  rescaled IEIs ~0; 63-91% of detections within 6 min of the prior one. Recommended fix: dedupe
  bursts to encounter-onset events or score GOF at the bin level (which NB PIT/dispersion already
  covers); honest outcome may be time-rescaling WITHHELD with the clustering reason, not a tuned gate.
- C cross-station consistency (`modeling/studies/cross_station_consistency.py` + report): per-kernel
  cross-station mean PSTH corr diel 0.336 / tide 0.136 / lunar 0.166 / season 0.159 (matches the
  0.14-0.34, all < 0.5). Diagnosis: a sparse-count artifact, not demonstrated heterogeneity, because
  within-station split-half reliability is itself below 0.5 for diel/tide/lunar (the PSTHs cannot
  reproduce themselves); season is reproducible-but-coverage-confounded. Effort normalization is a
  no-op (confirms A). `can_clear_0p5_bar_honestly = false` today; path = more detections/station
  (D's ingest) + coarser bins + partial-pooling scoring with split-half as the ceiling.
- D multi-station ingest dry-run (`src/aws_backend/ingest_multistation.py` + `WIRING-ingest.md`):
  dry-run counts orcasound_lab 1029, andrews_bay 296 raw / 265 after (t,id) dedupe,
  north_san_juan_channel 34 (total 1359 raw / 1328 stored). Reuses `_put_grouped_by_station`,
  `dry_run=True` default; `dry_run=False` is the operator/deploy-gated production write.
- E salmon Albion/DART (`src/aws_backend/sources/salmon_validation.py` + `PATCH-salmon.md` +
  `salmon_validation_findings.json`): DART (Columbia/Bonneville) reachable + parseable (269 daily
  rows, peak 2025-09-07, BEATS climatology); current `_fetch_columbia` fails only because it calls
  `.json()` on CSV, uses `outputFormat=csvSingle`, omits `year`, and misses the `Chin` column.
  Albion (Fraser/DFO) reachable but NOT machine-readable (daily CPUE published only as JPGs), so
  Fraser stays honestly disabled. Patch spec makes `_fetch_columbia` parse DART CSV and leaves
  `_fetch_fraser` returning `{}`. Caveat: DART's dominant peak is the Columbia FALL run, a different
  stock than the Fraser summer Chinook SRKW target; the Wave 3 lag scan must confirm alignment or
  L3 stays withheld.

Cross-agent conclusion (the honest headline): both L2 blockers are now DIAGNOSED, and neither is
clearable by Wave 2 wiring alone. Time-rescaling is bounded by detection burstiness (a modeling
change: burst-dedup / bin-level scoring, likely still withheld); cross-station consistency is bounded
by per-station sample size (needs D's production ingest to land and accumulate). Effort wiring is
correct but a no-op on the current disjoint uptime data. The one clean forward step is the DART
parser, which unblocks a REAL L3 lag scan in Wave 3. Effective confidence stays 0% (honest); no
promotion occurred.

## 2026-06-27 (Wave 2 integrated, operator-approved narrowed scope; feeds-down pause then resume)

Two integrators ran in parallel (single convergence-file editor per file; modeling vs backend,
disjoint), validate-only, no agent commits, no production store / model-bucket write, no promotion.
The operator stopped both mid-run while the DART/Albion feeds were in a maintenance window and
resumed them once the feeds were back online.

- Modeling integrator (sole editor of the modeling fit pipeline + L2 study/reports): wired Agent A's
  effort/log E into design.py build_design and fit_kernels.py _station_intensity_fn /
  _time_rescaling_report (VERIFIED no-op on the disjoint 2026 uptime vs 2020-2021 detections:
  effort_assumed_continuous stays true, log E flat); implemented Agent B's burst-dedup / encounter-
  onset time-rescaling re-score; applied Agent C's coarser-bin + split-half-ceiling cross-station
  scoring. Multi-station S3 refit (write_outputs=False, _maybe_write_s3 disabled) reproduced held-out
  skill +0.0778 (4/5 folds, beats climatology). Verdicts, honest: time-rescaling WITHHELD (event-level
  pooled KS p=0; encounter-onset re-score recenters mean to ~1.01 but pooled KS still p~7.5e-22, the
  onset process is itself clustered); cross-station NOT consistent (diel/tide noise-bound vs their own
  split-half, season coverage-confounded, lunar genuine heterogeneity to model later). mlops-gate exit
  0 (ALL PASS), served confidence 0.0 consistent with l2_gate=fail. data/models/fit_report.json
  untouched (confidence 0.0, n_stations 1).
- Backend integrator (sole editor of salmon.py + the L3 lag scan): applied PATCH-salmon.md to
  salmon.py (_fetch_columbia now parses DART CSV via a new _csv_text_to_rows helper + outputFormat=csv
  + year + retry past the err-/maintenance wrapper + `Chin` value key; _fetch_fraser returns {} since
  Albion is image-only/host-dead). Live re-validation through the real code path: DART 269 rows, peak
  2025-09-07=22928, fetch_run_index source=dart (not climatology_fallback). Real L3 lag scan over all
  detection years (real_feed_only): best lag -24 d, r -0.061, permutation p 0.699 -> does NOT beat the
  null AND stock-mismatched (DART Columbia fall vs Fraser summer Chinook). L3 WITHHELD. Added a
  stock-alignment guard (_STOCK_ALIGNED_SOURCES = {"albion"}) so a real-but-mismatched feed can never
  auto-PASS L3. salmon_lag.json + level3_prey_space.json updated with the honest verdict.

Ladder after Wave 2: L0 PASS, L1 PASS (diel; cross-station consistency not met), L2 FAIL
(time-rescaling withheld, cross-station not consistent), L3 WITHHELD (real DART feed now exercised
but fails the null and is the wrong stock). Effective confidence stays 0% (honest). No promotion.

Honest conclusion: the frontier did NOT move off 0%, and that is the correct outcome. The binding
constraints are now precisely characterized and DATA-bound, not wiring-bound:
1. L2 time-rescaling: detection-stream burstiness; a smooth NB intensity cannot pass event-level
   Exp(1) rescaling, and encounter-onset dedup still fails. Needs a clustering/self-excitation model
   or a bin-level GOF decision, not a tuned gate.
2. L2 cross-station consistency: per-station sample size; sparse nodes cannot even split-half-reproduce.
   Needs the operator/deploy-gated 3-node production ingest to land and accumulate.
3. L3: needs a stock-aligned Fraser-summer Chinook feed. DART (Columbia fall) is real but fails the
   null and is the wrong stock; Albion is not machine-readable.

Uncommitted local state (nothing committed, per B.10): modeling pipeline edits are local-only/untracked
(design.py, fit_kernels.py, effort.py). Tracked files now modified: salmon.py, salmon_lag.py,
level3_prey_space.py, level2_multistation.py, and the studies/reports/*.json verdicts. Report
timestamp-only churn (level0/1/2_joint/3/salmon_lag regenerated by the gate) should be restored before
any commit.

## 2026-06-27 (got the real stock-aligned salmon data; L3 still withheld, honestly)

Operator: "push and get the salmon data". Pushed the prior commit (484580f) to origin/main, then
sourced the real Fraser-summer Chinook (Albion) feed that L3 actually needs (DART was wrong stock).

- The DFO FOS Albion report (stat=CPTFM, fsub_id=242) is a Selenium-driven JS form whose host
  (www-ops2.pac.dfo-mpo.gc.ca) is DNS-blocked from this host; the isolated fetch server can reach
  the form but not drive it. The orcasalmon project (liu-zoe/orcasalmon) mirrors the real FOS
  Chinook CPUE as data/foschinook/fosYYYY.csv. Cached the real series for 2019-2025 under
  data/salmon/albion_fos/fosYYYY.csv (columns day,mon,year,...,cpue1,...; cpue1 = standard 8-inch
  gillnet CPUE). Provenance: DFO FOS, mirrored. 2026 is not in the mirror and is unreachable from
  this host (live feed needed on a DFO-reachable box).
- Wired src/aws_backend/sources/salmon.py `_fetch_fraser` to read the cached real Albion CSVs
  (added `_load_albion_fos`); the adapter now returns source=albion for 2020-2025 (verified: peaks
  late August, correct for the Fraser summer run), falling through to DART only for 2026.
- Re-ran the real L3 lag scan, honest:
  - Full span 2020-2026: best lag -23 d, r -0.070, permutation p 0.593; 2026 falls to DART so the
    source is mixed (albion,dart) and the stock-alignment guard records WITHHELD.
  - Focused Albion-only 2020-2025 (all real Fraser stock, stock_aligned=True): best lag +20 d,
    r 0.085, permutation p 0.4216 -> does NOT beat the null.
  Conclusion: getting the correct stock did not flip L3. The real Fraser-summer Chinook feed is now
  wired and available, but the daily presence-vs-run-timing signal is not significant on this
  detection set (binary daily presence over the cached multi-station OrcaHello index). L3 stays
  WITHHELD for a sound reason now (no significant lagged correlation on the correct stock), not
  "wrong stock / no real feed". Effective confidence unchanged at 0%; no promotion.
- Uncommitted (nothing committed for this step): src/aws_backend/sources/salmon.py (Fraser wiring),
  data/salmon/albion_fos/fos2019-2025.csv (real cached feed), modeling/studies/reports/salmon_lag.json
  (re-run verdict). Awaiting operator ask to commit.

## 2026-06-27 (W3 l3-chinook-lag: 2026 Albion via the aimez EC2; full-span stock-aligned)

Operator: "check the charter ... commit what you[have] ... try using the aws box to reach the salmon
of 2026, wire it". Confirmed we are mid the frontier_dispatch waveset (W1+W2 done); this is the W3
l3-chinook-lag step, not a new waveset.

- Committed + pushed the current real-Albion work (12e7054): salmon.py Fraser wiring +
  data/salmon/albion_fos/fos2019-2025.csv + the re-run salmon_lag.json.
- Reached the 2026 Albion feed via the aimez-services EC2 (i-04a649f91274e9fce; SSH
  ubuntu@44.197.243.177). DFO resolves there (www-ops2.pac.dfo-mpo.gc.ca -> 205.193.114.62) though
  it is DNS-blocked locally. Found the FOS form posts to rptCSbD.cfm?stat=CPTFM with
  lboYears/lboSpecies=124/lboFsub=242/cmdRunReport; a direct curl POST returns the report HTML (no
  Selenium needed). Parsed the 12-token rows and wrote data/salmon/albion_fos/fos2026.csv (57 rows,
  2026-05-01..2026-06-26; season in progress, summer peak not yet). Cleaned up the EC2 /tmp. Recipe
  recorded in WIRING-salmon-albion.md.
- Adapter now returns source=albion for ALL detection years 2020-2026 (single source, stock-aligned).
  Re-ran the full-span L3 lag scan: best lag +20 d, r 0.076, permutation p 0.394 -> does NOT beat
  the null. L3 stays WITHHELD, now for the cleanest reason: a real, complete, single-source,
  stock-aligned Fraser-summer Chinook feed shows no significant lagged correlation with SRKW
  acoustic presence on this detection set (binary daily presence over the cached multi-station
  OrcaHello index). This is a data/methodology result, not a wiring/stock/coverage gap. Effective
  confidence unchanged at 0%; no promotion.
- Refreshed wave_shape.yml frontier_dispatch (frontier_state + W1 done / W2 done / W3 in-progress);
  added WIRING-salmon-albion.md.

## 2026-06-27 (chartered the L2/L3 push research waveset)

Operator asked to charter a waveset to research how to push L3 (counts vs binary daily presence;
condition on season / time of day; temperature) and find more L2 "ammo", and to clarify whether the
L2 dependency remains the gated 3-node ingest.

- Clarified the L2 blocker map: L2 has TWO blockers with different deps. Time-rescaling is detection
  burstiness (a MODELING fix, ungated, attackable now); cross-station consistency is per-station
  sample size (GATED on the 3-node production ingest). So "the L2 dep remains the gated 3-node ingest"
  holds for cross-station only; time-rescaling and the L3 reformulation are ungated.
- Wrote RESEARCH_CHARTER.md + RESEARCH_DISPATCH.md (six investigation-first parallel agents, READY,
  not launched, model inherit): RA L3 response variable (counts/rate/count-GLM vs binary), RB L3
  conditioning (season / per-station / SRKW window), RC diel conditioning + temperature/SST source
  feasibility and honest role (effect modifier vs effort term per B.2), RD L2 burstiness modeling
  (self-excitation/Hawkes/refractory/hurdle or bin-level GOF -> does the timing gate pass honestly),
  RE L2 data-volume power analysis (detections/station for split-half >=0.5; what the 3-node ingest
  adds; confirm the binding dep), RF synthesis + ranked action plan. Added a research_dispatch block
  to wave_shape.yml. Findings live under .cca/catalogue/O0/20260627_mlops/research/.
- Investigation-first: findings docs are decision aids; no convergence-file edits, refit-safety on,
  no confidence promotion. The operator decides which findings graduate to a future W4 build wave.
- READY, not launched. Launch is the next operator gate. Nothing committed for this charter step.

## 2026-06-27 (research wave ran: RA-RF; corrected blocker map)

Launched the six-agent L2/L3 push research wave (operator "execute"); all returned honest findings
under `.cca/catalogue/O0/20260627_mlops/research/` (decision aids; no fits promoted, no convergence-
file edits, no confidence promotion, nothing committed by agents).

- RA L3 response variable: counts / rate / count-GLM do NOT beat the permutation null where binary
  failed (best p 0.193; GLM worst at 0.681). The response variable is NOT the L3 limiter. DEAD-END.
- RB L3 conditioning: the pooled test was diluted by off-season days (detections are fall/winter-
  heavy; the Albion run is summer). Conditioning to SRKW summer beats the null: Jun-Sep r=0.251
  p=0.013, May-Oct r=0.182 p=0.012 (best lag +20 d). Exploratory (window multiplicity ~Bonferroni
  -> 0.05; 36-63 summer presence days; still binary). Real L3 lever; L3 stays WITHHELD.
- RC diel + temperature: time-of-day irrelevant at the salmon timescale (active-window p 0.326 vs
  full 0.394). Temperature/SST data is available (NDBC 46088, CO-OPS 9449880) but is NO-GO as an
  animal kernel per B.2 (SST ~ f(day-of-year), collinear with k_season, redundant with k_salmon);
  at most a minor L0 detectability term. DEAD-END for a kernel.
- RD L2 burstiness: no ungated fix passes event-level Exp(1) time-rescaling. A Hawkes self-exciting
  model cuts the KS spike ~5.7x (branching ratio 0.79-0.96 = detector repeat-triggering, not
  independent animal events) but still fails (p 3.3e-33). The honest path is a BIN-LEVEL timing gate
  (held-out NB PIT calibrated AND CV skill > climatology); event-level stays WITHHELD. Methodology
  change to graduate via an operator-gated build wave.
- RE L2 data volume: REFUTES that the 3-node production ingest is the binding cross-station
  dependency -- the ingest reads the same cached OrcaHello records and adds zero new observations, so
  post-ingest reliability equals current. The binding issue is scoring resolution (24-bin too fine)
  + burstiness; the UNGATED fix is re-scoring consistency at 8-12 bins + partial pooling + burst-
  dedup (diel split-half 0.08->0.42 at 12 bins; lunar clears 0.5 now on both dense stations). The
  24-bin target (~14k-22k detections/station for diel) is effectively unreachable for years.
- RF synthesis (research/SYNTHESIS_L2_L3.md): ranked plan. Top UNGATED: U1 consistency re-score at
  8-12 bins + min per-bin count (highest L2 leverage), U4 pre-registered SRKW-summer L3 conditioning,
  U2/U3 partial pooling + burst-dedup, U5 Hawkes + bin-level GOF diagnostic. Graduate to a W4 build
  wave: (1) RD bin-level timing-gate redefinition + Hawkes diagnostic (operator-gated), (2) RE/RB
  coarser-bin + partial-pooling consistency re-score (ungated), (3) RB pre-registered summer L3
  conditioning + counts + held-out year. Dead-ends: RA counts, RC temperature/diel.

CORRECTED blocker map (supersedes the earlier note): L2 cross-station is NOT simply gated on the
3-node ingest; it is a scoring-resolution + burstiness problem with an ungated fix. L2 time-rescaling
has no event-level fix (bin-level gate is the honest path). L3's limiter is off-season pooling, not
the response variable; SRKW-summer conditioning is the lever. Effective confidence stays 0%.

Uncommitted: research/*.md + research/figures/ + modeling/studies/reports/{L3_response_variable,
L3_conditioning,L3_diel_temperature,L2_burstiness_timing,l2_data_volume}.json, plus untracked scratch
drivers (modeling/studies/_ra_response_scratch.py, _rb_conditioning.py, l2_data_volume_power.py) the
agents left for reproducibility. wave_shape.yml research_dispatch + STEP_LOG + README updated.

## 2026-06-27 (W4 build wave chartered from the research findings)

Operator: "proceed 1, 2. 2b) u decide". Chartered the W4 build/integrate wave and prepared the
research-findings commit.

- Wrote W4_BUILD_CHARTER.md + W4_BUILD_DISPATCH.md (two integrators, single convergence-file editor
  per file, READY, not launched):
  - Modeling integrator (sole editor of fit_kernels.py + cross_station_consistency.py): ITEM 1
    (UNGATED) re-score cross-station consistency at 8-12 bins + min per-bin count + partial pooling +
    burst-dedup (diel 0.08->0.42, lunar clears 0.5; tide stays flagged); ITEM 3 (GATED, WRITE-ONLY)
    Hawkes event-level diagnostic + a bin-level timing gate (held-out NB PIT AND CV-skill>climatology)
    behind a default-OFF flag -- do NOT adopt or promote.
  - Study integrator (sole editor of salmon_lag.py): ITEM 2 (UNGATED) pre-registered SRKW-summer
    (Jun-Sep, +lag) L3 conditioning + held-out year on the real Albion feed; L3 stays WITHHELD unless
    the held-out year also beats the null.
  - Dead-ends not built: RA counts, RC temperature/diel.
- The one confidence-bearing change (item 3, the bin-level timing gate) is operator/supervisor-gated:
  effective_confidence rises ONLY on a recorded supervisor decision (B.1); W4 writes it OFF. Items 1+2
  do not promote.
- Added W4 to wave_shape.yml frontier_dispatch (status dispatch-ready; frontier status now
  W1-W2-W3-done-W4-chartered).
## 2026-06-27 (W6 DEPLOYED: 3-node multi-station ingest landed in the SERVED store)

Operator: "push push push / w6 deploy!!". Pushed the 4 pending commits to origin/main (CI re-runs with
the salmon fix) and executed the W6 production ingest.

- Pre-flight (read-only, all G1 pre-deploy gate items green): creds = account 198456344617; pre-write
  store.list_stations(acoustic_detections) == ['haro_strait'] (rollback target recorded); dry-run
  reproduced 1029/265/34 = 1328; mlops-gate green; no fit bundled.
- WRITE executed: ingest_multistation_acoustic(store, dry_run=False) against bucket B.4 (us-west-2),
  put_grouped_result records=1359. POST store.list_stations = [andrews_bay, haro_strait,
  north_san_juan_channel, orcasound_lab] (4 stations). Per-station get_series: orcasound_lab 1029,
  andrews_bay 265, nsj 34; haro_strait 761 UNCHANGED (verified pre==post). Idempotent (station,t,id);
  reversible (rollback deletes only the 3 new prefixes).
- HONEST STATE: the served STORE is now 4-station, but the served FIT is still single-station (no refit
  ran). No supervisor call, no promotion -> effective_confidence stays 0.0; L2 still FAIL. This is
  plumbing/forward-accumulation, NOT an L2 pass and NOT a confidence change (RF C2).
- Registry: W6 -> done (deployed block recorded); W7 -> ready (next gate); campaign status
  P0-W5-W6-done-W7-ready.
- NEXT (W7, gated): refit SERVED multi-station (upload disabled, write_outputs=False) to MEASURE served
  held-out CV-skill. Per G2 it should land ~+0.078 -> confidence 0.49 = HOLD (below the 0.6 supervisor
  threshold), so it does NOT promote: the operator either WAITS for skill ~+0.144 or records an explicit
  B.1 decision to serve a sub-0.6 caveated confidence. Promotion is never automatic.

## 2026-06-27 (W5 grounding wave DONE; W6/W7/W8 conditions now grounded)

Operator: "launch it, then commit but check why git build is failing." Launched W5 (G1/G2/G3) in
parallel; all three returned grounding docs under research/forward/. Also diagnosed + fixed the red CI
(see the CI note below).

- G1 ingest-deploy (research/forward/G1_ingest_deploy.md): GO on the plumbing, operator-gated. One-shot
  idempotent (station,t,id) write of the 3 cached nodes (orcasound_lab +1029, andrews_bay +265, nsj +34
  = +1328) into the SERVED store; reads the cache (no fetch_history/403 surface), ~180 S3 ops, reversible
  (rollback never touches haro_strait). Flips served CV-skill -0.047 -> ~+0.078 (4/5 folds). NO-GO on
  calling it a consistency fix or a promotion: +1328 to the SERVED store but 0 net-new to the analysis
  universe (same cached rows). orcasound_lab load-bearing; nsj negligible.
- G2 promotion-protocol (research/forward/G2_promotion_protocol.md): two bands, do not conflate. HOLD
  (0<conf<0.6): served skill>0, >=4/5 folds -> +0.078 maps to 0.49 -> supervisor HOLDs. PROMOTE
  (conf>=0.6): served skill >=+0.144 AND >=4/5 folds AND across-fold lower bound (mean-t*SE) >=+0.078 AND
  PIT calibrated AND a beaten L1 null. Curve +0.078->0.49, +0.144->0.60, cap 0.75; if PIT not calibrated
  max reachable 0.35. The ingest ALONE does NOT promote (lands at 0.49 HOLD). Consistency is NOT a
  confidence-map input; its gains come from the coarser-bin re-score, not the ingest. W7 Case 2 default =
  WAIT for ~+0.144, or the operator records an explicit B.1 sub-0.6 caveated display.
- G3 L3 (research/forward/G3_l3_grounding.md): GO now on wiring the live 2026 Albion fetch (cache stops
  2026-06-26, before the peak; via aimez EC2). NO-GO on any L3 promotion. The L3 lever is summer
  PRESENCE-DAYS (the W6 ingest accruing summers), NOT the salmon feed. Power: Bonferroni x4 pushes
  in-sample p 0.013->0.052 (fails); only frozen pre-registration rescues it. Need n>=8 seasons, ~10-15
  presence-days/yr, LOYO >=3-of-n, fresh OOS on NEW data. All fail today -> L3 stays WITHHELD-with-flag.
- KEY CROSS-CUT: the W6 ingest is worth deploying (safe, reversible, near-zero cost, and the L3 lever),
  but it lands served confidence at 0.49 HOLD -- it is NOT an L2 pass and NOT a promotion. The honest
  framing (plumbing, not a fix) is the top residual risk to manage.
- Registry: W5 marked done; w5_findings block added; W6 -> gated-operator-deploy (awaits ONLY operator
  approval + the production write); W7 -> two-band decision gate; W8 -> depends_on W6 (the real L3 lever).
- Effective confidence unchanged 0.0. Grounding docs committed; nothing promoted.

## 2026-06-27 (CI red fixed: stale salmon tests vs the real Albion cached-feed path)

Operator asked to check why the git build is failing. AWS Backend CI was red on main since the real
Fraser feed was wired: tests/aws_backend/test_salmon.py had 4 tests mocking requests.get and the old
climatology/DART-JSON fallback, but _fetch_fraser now reads cached FOS CSVs and DART parses CSV. Fixed
the tests (empty_albion_cache fixture controlling _ALBION_FOS_CACHE_DIR; cached-CSV Albion test; DART
CSV fallback). 225 tests/aws_backend pass, compileall clean. Committed f3eff79. (Not pushed unless asked.)

## 2026-06-27 (forward-path campaign chartered; P0 confidence-cliff fix dispatched in parallel)

Operator: "charter a multi wave research campaign to structure and ground the forward path ... if there's
something that you can already deploy ... deploy it in the parallel subagent and begin charting what the
research will need for everything else."

- Premise: after the W4 adoption, the path off 0% collapses to one binding fact -- the served L2 timing
  gate earns credit the moment the SERVED fit's held-out CV-skill turns positive (served single-station
  -0.047 vs 4-station experiment +0.078); closing that gap is the deploy-gated 3-node ingest; on current
  scoring it would slam confidence to 1.0.
- Wrote CAMPAIGN_CHARTER.md + CAMPAIGN_DISPATCH.md. Structure: one parallel deploy (P0) + a
  research/grounding wave (W5) that gates three downstream waves (W6 deploy ingest, W7 promote
  multi-station, W8 L3 live feed + re-test). Nothing promotes; build is gated; promotion needs a passing
  gate on SERVED data + a recorded supervisor decision (B.1).
- Objectives mapped: O1 production multi-station ingest (deploy-gated), O2 confidence-cliff fix
  (code-only -> P0, running now), O3 honest multi-station promotion (gated), O4 L3 grounding (gated).
- PARALLEL DEPLOY (P0, executing now): a modeling subagent graduates _confidence_from_gates so a +skill
  multi-station fit promotes to an effect-size-scaled, sub-1.0 value instead of a binary 1.0; invariants
  = served confidence stays EXACTLY 0.0, mlops-gate green, local-only/untracked (B.6), no commit. Safe:
  it only makes promotion MORE conservative and nothing is promoted today.
- W5 grounding agents (dispatch-ready, launch is the next operator gate): G1 ingest-deploy grounding
  (runbook + pre-deploy gate + net-new-detection estimate, grounds W6), G2 promotion-protocol grounding
  (robust-skill definition + served refit spec + supervisor decision-record format + consistency-after-
  ingest projection, grounds W7), G3 L3 grounding (live 2026 Albion fetch + presence-year power analysis
  + decision bar, grounds W8). Findings under research/forward/.
- Added forward_path_campaign block to wave_shape.yml (P0 running; W5 dispatch-ready; W6/W7/W8 gated).
- Effective confidence unchanged 0.0.

- P0 DONE (confidence-cliff fix landed, local-only modeling/fit_kernels.py, not committed): replaced the
  flat 0.25-per-quarter sum in _confidence_from_gates with an evidence-scaled, saturating map past the
  0.0 floor: evidence = 0.50 * (0.5*cv_pass + 0.5*timing_gate) * (1 - exp(-max(skill,0)/0.12)), + 0.15
  PIT (timing-gated) + 0.10 level1, capped at 0.75. Gate pass/fail definitions untouched.
  - Served confidence stays EXACTLY 0.0 (served CV-skill -0.047 fails the floor). mlops-gate ALL PASS,
    honesty guard served_confidence=0.0 l2_gate=fail OK. Timestamp-only ladder churn restored.
  - CONSEQUENCE for the forward path: the +0.078 multi-station EXPERIMENT margin now maps to 0.49 (HOLD,
    not promoted) instead of the old binary 1.0; crossing the supervisor 0.6 threshold now requires CV
    mean-deviance-skill ~+0.144 (about double +0.078). So the 3-node ingest ALONE (which flips served
    skill toward the experiment's +0.078) would lift served confidence to ~0.49 but NOT auto-promote.
    W7 promotion now needs either larger/robust skill or an explicit operator decision about a sub-0.6
    served display. This is the key thing G2 must ground.
  - The "armed 1.0 cliff" risk recorded in DECISION_RECORD sec 4 is now MITIGATED: promotion is
    effect-size-scaled and capped at 0.75, and 0.6 means robust skill, not one lucky fold.

## 2026-06-27 (supervisor decision: ADOPT bin-level L2 timing gate -- still 0.0, now armed)

Operator: "commit and approved adoption". Recorded the B.1 supervisor decision to adopt the W4 item-3
bin-level timing gate. Full record in DECISION_RECORD.md section 4.

- Flipped ADOPT_BIN_LEVEL_TIMING_GATE False->True in modeling/fit_kernels.py (local-only/untracked, B.6;
  the decision itself is recorded in the tracked DECISION_RECORD.md).
- Honest framing recorded as such: event-level Exp(1) is inappropriate for a detector-chatter stream
  (Hawkes branching 0.79-0.96, pooled KS p=3.3e-33); GOF scored at the served per-bin-count target
  (held-out NB PIT calibrated AND held-out CV-skill > climatology; CV-skill is the load-bearing half).
- VERIFIED EMPIRICALLY (flag ON): served single-station fit (haro_strait, n=761) has CV mean-deviance-skill
  = -0.047 (< 0), so the load-bearing CV-skill half FAILS -> bin_level_verdict=fail, timing_gate=False,
  _confidence_from_gates = 0.0. mlops-gate = ALL PASS, honesty guard served_confidence=0.0 l2_gate=fail OK.
  NO promotion. Adoption is data-earned, not automatic.
- ARMED (risk recorded): if a SERVED fit had CV-skill +0.078 (the 4-station EXPERIMENT value, not served),
  _confidence_from_gates would jump to 1.0 (all four 0.25 quarters) -- a hard cliff from the pre-existing
  scoring. The +0.078 becomes served only after the deploy-gated 3-node production ingest. Until then
  served confidence stays 0.0.
- L3: NOT promoted. The summer-conditioned held-out flag stays FLAGGED-FOR-DECISION; L3 WITHHELD.
- Committed the W4 tracked deliverables on this operator ask (surgical staging, B.10); fit_kernels.py +
  the served fit_report.json stay local/untracked (B.6).

## 2026-06-27 (W4 build wave EXECUTED -- both integrators returned; confidence still 0.0)

Operator: "execute". Launched both W4 integrators in parallel (disjoint files); both returned honest.

- Modeling integrator (fit_kernels.py + cross_station_consistency.py):
  - ITEM 1 (UNGATED, APPLIED) cross-station consistency re-scored at 12 bins + min per-bin count +
    partial pooling + burst-dedup-to-encounter-onset, plus a latent ordering-bug fix so a
    coverage-confounded kernel is no longer mislabeled "consistent". 4-station memory store
    (prod haro_strait from S3 + cached OrcaHello for the 3 nodes): diel dense split-half 0.04->0.37,
    lunar clears 0.5 (haro 0.67, andrews 0.81), tide unstable -> KEPT FLAGGED (not forced), season
    coverage_confound. Overall verdict still NO (4-stn bar not cleared honestly). Reproducibility-criterion
    fix; does NOT promote.
  - ITEM 3 (GATED, WRITTEN, NOT ADOPTED): Hawkes self-exciting event-level GOF diagnostic in
    _time_rescaling_report (branching ratios haro 0.79 / orcasound 0.80 / andrews 0.96 / nsj 0.91;
    pooled KS recenters 0.979->1.002 but pooled KS p=3.3e-33 still fails) -> event-level Exp(1) verdict
    stays WITHHELD, flagged diagnostic_only. Bin-level timing gate (held-out NB PIT p=0.364 calibrated
    AND CV mean-deviance-skill +0.078 > climatology; bin_level_verdict=pass) defined behind
    ADOPT_BIN_LEVEL_TIMING_GATE=False in _confidence_from_gates; served timing_gate = tr_pass OR (FLAG AND
    bin_level), so with the flag OFF it equals the event-level pass and confidence is UNCHANGED. Flag NOT
    flipped; adoption is a recorded supervisor decision (B.1).
- Study integrator (salmon_lag.py): ITEM 2 (UNGATED, APPLIED) additive, separately-labeled exploratory
  section; full-span scan + ladder-consumed keys untouched.
  - Pre-registered Jun-Sep window + +lag (run leads presence) fixed BEFORE scanning. In-sample (all years):
    best lag +20d, r=0.251, p=0.013 (matches RB). Held-out year = 2021 (richest, 9 summer presence-days),
    lag fixed from training years = +17d; out-of-sample r=0.390, p=0.027 -> BEATS the pre-registered null.
  - Verdict: FLAGGED-FOR-DECISION (flag_for_operator_decision=true); L3 status = WITHHELD. Per B.1 the
    held-out hit is surfaced for an operator/supervisor decision, NOT self-promoted. Risk: LOYO only 2/5
    single-year held-outs clear (2021, 2023), 5-9 presence-days/year, multiplicity -- the flag is genuine
    but fragile.
  - Optional (informational): summer-window daily counts r=0.221, p=0.009 (counts dead-end pooled but help
    within the conditioned window; did NOT feed verdict logic).
- W4 exit: tools/waves/run-gate.sh mlops-gate = ALL PASS; honesty guard served_confidence=0.0 l2_gate=fail
  OK; served fit_report.json confidence 0.0 (untouched). Tracked diffs: cross_station_consistency.py +193,
  salmon_lag.py +350, plus refreshed study report JSONs. NOTHING committed (no operator ask, B.10).
  level0/1/2_joint report churn is timestamp-only from the gate run -- restore before any commit.
- frontier_state in wave_shape.yml updated (L2 FAIL with bin-level gate OFF; L3 WITHHELD/flagged); W3 + W4
  marked done; top-level status W1-W2-W3-W4-done. Effective confidence remains 0.0.
- Next operator gates: (1) supervisor decision on ITEM 3 (flip ADOPT_BIN_LEVEL_TIMING_GATE -> would
  promote L2 timing) -- requires promotion/supervisor.py record; (2) supervisor decision on the L3
  summer-conditioned held-out flag; (3) the 3-node production acoustic_detections ingest (deploy-gated)
  for L2 sample size; (4) a surgical commit of the W4 deliverables on an explicit ask.
- 2b decision (carried from charter): the agents' untracked scratch drivers (modeling/studies/_ra_response_scratch.py,
  _rb_conditioning.py, l2_data_volume_power.py) are NOT committed -- one-off reproducibility scripts
  that would pollute the tracked study tree; the findings docs + report JSONs + the figure are the
  durable deliverables. They remain locally untracked.

## Open / awaiting operator

- W4 has RUN (both integrators returned; see the W4 EXECUTED entry above). Items 1+2 landed; mlops-gate
  green at served confidence 0.0. Two supervisor decisions are now waiting:
  - ITEM 3 (bin-level timing gate, written OFF as ADOPT_BIN_LEVEL_TIMING_GATE=False): adoption needs a
    recorded supervisor decision via promotion/supervisor.py; that is the only code path that moves
    effective_confidence off 0% for L2 timing.
  - L3 summer-conditioned held-out flag (2021 out-of-sample r=0.390, p=0.027): FLAGGED-FOR-DECISION,
    fragile (LOYO 2/5). Operator decides whether to pursue (more presence-years / live 2026 feed) or
    keep WITHHELD.
- Still data/deploy-bound: the 3-node production acoustic_detections ingest for L2 sample size; a surgical
  commit of the W4 deliverables on an explicit ask (restore level0/1/2_joint timestamp churn first).
- (historical) Decide which graduated items become a W4 build/integrate wave. The cheapest high-value UNGATED move
  is U1 (re-score cross-station consistency at coarser bins + partial pooling): it makes diel
  reproducible and lunar clear at current volume, no ingest needed. None promotes confidence by
  itself.
- Commit of the research findings is available on an explicit operator ask (surgical; decide whether
  to keep or drop the scratch drivers).
- (historical) Research wave launch was the prior gate; it has run.
- L3 honest state: the stock-aligned Fraser feed is now correct AND complete (2020-2026), and still
  does not earn k_salmon on daily binary presence (p=0.394). If pursued: try detection COUNTS rather
  than binary presence, condition on season, or accept L3 withheld as the honest state. None promotes
  confidence by itself.
- W3 remaining: gate-rerun (mlops-gate stays green/honest) and promotion-packet are moot while no
  gate passes; the binding L2 dependency is still the operator/deploy-gated 3-node production ingest.
- (superseded) earlier L3 note: the stock-aligned Fraser feed is now wired but does not earn k_salmon on daily binary
  presence. Options if pursued: use detection COUNTS (not binary presence) and/or restrict to the
  high-coverage seasons; wire the live 2026 Albion feed on a DFO-reachable host; or accept L3
  withheld as the honest state. None promotes confidence by itself.
- Wave 2 -> Wave 3 gate: Wave 3 as chartered (gate + L3 + promotion prep) has NO promotable gate, so
  there is no promotion packet to prepare. The remaining moves are data-bound and operator/deploy-gated,
  not a code wave: (a) land the 3-node production acoustic_detections ingest (Agent D's
  ingest_multistation.py, dry-run validated 1029/265/34) to give L2 cross-station the sample size it
  needs; (b) source a stock-aligned Fraser-summer Chinook feed for L3 (Albion is image-only; an
  alternative DFO/PSC machine-readable source is needed). Neither earns confidence by itself; each is a
  precondition.
- Optional now: a surgical commit of the Wave 1/2 deliverables (restore report timestamp churn first,
  stage only the intended files) on an explicit operator ask.
- The original Wave 1 -> Wave 2 recommendation block below is superseded (Wave 2 is complete).

### (superseded) Original Wave 1 -> Wave 2 recommendation
  scope is narrower than the original "wire effort + pass the gate": (1) land Agent A's effort wiring
  (correct regardless, fixes the key mismatch, no-op today); (2) land the burst-dedup / bin-level
  time-rescaling scoring change and report the L2 timing verdict honestly (likely withheld with the
  clustering reason); (3) land the DART parser patch to enable a real L3 lag scan; (4) treat the
  3-node production ingest as the data dependency for both L2 blockers (operator/deploy-gated). A
  passing L2 gate is NOT expected from Wave 2 integration alone on the current data.
- The original Wave 1 launch line is superseded by the above (Wave 1 is complete).
- M-L2 to a real pass: ingest the additional Orcasound nodes into the production acoustic_detections
  stream (the experiment used the cached index), tighten per-station effort/log E so time-rescaling
  passes, and lift cross-station kernel consistency. Multi-station already flips held-out skill
  positive, so this is the path off 0% (a passing gate + a recorded supervisor decision would then
  promote confidence; not done here).
- M-L3 needs a real Chinook run-timing feed: validate the Albion/DART parsers in
  `src/aws_backend/sources/salmon.py` (both wired, both fall through to climatology today).
- The harmonic integration lives in the local modeling pipeline (untracked, like fit_kernels.py
  and design.py); only `tide_harmonic.py` and the study reports are tracked. Reproduce with
  `ORCAST_STORAGE_BACKEND=aws ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads AWS_REGION=us-west-2 PYTHONPATH=. .venv-modeling/bin/python -m modeling.fit_kernels`.
- MLO scheduling/monitoring AWS infra is operator/deploy-gated.
- A confidence promotion still requires a passing gate + a recorded supervisor decision.
