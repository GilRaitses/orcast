# TB2 -- SST-front gradient covariate (sourcing + recipe + dry-run probe + patch-spec)

Agent: TB2 subagent, graduation waveset (Tier B). Date: 2026-06-27 (America/New_York). Repo:
`/Users/gilraitses/orcast`. This doc only; no other file edited, no deploy, no production write, no
fit that writes a served artifact, no promotion, no commit. Effective confidence stays 0.0.

Authority: `20260627_signal-modeling-launch-handoff/HANDOFF_CHARTER.md` section B (B.2 covariate-role
honesty is load-bearing here); `GRADUATION_DISPATCH.md` (TB2 lane + the RECALIBRATION-FROM-DE binding
preamble + B.2 RAIL); `GRADUATION_WAVESET_CHARTER.md` sections 1, 3; `SYNTHESIS_signal_modeling.md`
(B2 row); `research/signal_modeling/S2_covariate_sources.md` (rank 2); `M3_derived_covariates.md`
(C1); `docs/methodology/FORECAST_KERNELS.md`; `research/forward/G2_promotion_protocol.md` (+0.144 bar).

## 0. The binding rails this lane obeys (restated)

- **B.2 RAIL (binding, from the dispatch).** Absolute SST is seasonal and collinear with `k_season`;
  it is NOT admissible. Only the **gradient** `|grad SST|` / **distance-to-front** is the independent
  signal, and it enters as an **effect-modifier** orthogonalized vs `k_season`. Terrain stays
  `s_space`-only and is not touched by this lane (do not drift it onto the temporal gate).
- **Judge by held-out, fold-stable CV mean-deviance-skill toward +0.144, never in-sample fit** (G2;
  `block_cv` in `modeling/validation/crossval.py`). The effective independent N is ~300 encounter
  onsets pooled (not 2089), so a flexible covariate that only correlates in-sample is a dead-end.
- **No served write / no convergence-file edit / no commit.** `modeling/fit_kernels.py`,
  `modeling/design.py`, `modeling/estimator.py`, and `src/aws_backend/sources/*` are convergence files
  edited by a later single-editor integrate step; this lane delivers a PATCH-SPEC, not an edit.
- **DE drift-guard.** Per the RECALIBRATION-FROM-DE preamble, a stale "GO" in a source doc does not
  override the SYN/DE verdicts. M3-C1 reads as a *conditional* GO (S2-gated, season-orthogonalized);
  this lane preserves that conditionality and adds the role-honesty caveat (DE1 rows #6-10): SST is
  admissible ONLY as the de-seasonalized gradient, never as absolute SST laundered into presence.

## 1. SOURCING

### 1.1 Primary product -- MUR SST (recommended)

| Field | Value |
|---|---|
| Dataset | GHRSST Level 4 **MUR** (Multi-scale Ultra-high Resolution) v4.1, `jplMURSST41` |
| Producer | NASA JPL PO.DAAC (foundation SST, gap-free L4 analysis) |
| Resolution | 0.01 deg (~1 km); daily; 2002-06-01 -> present |
| Variable | `analysed_sst` (Kelvin on PO.DAAC native; degree_C on the CoastWatch ERDDAP mirrors) |
| Access A (ERDDAP) | CoastWatch / PFEG ERDDAP griddap: `https://coastwatch.pfeg.noaa.gov/erddap/griddap/jplMURSST41.{csv,nc}` (and `upwell.pfeg.noaa.gov`) -- subset `[time][latitude][longitude]` |
| Access B (cloud) | PO.DAAC S3 `podaac-ops-cumulus-public/MUR-JPL-L4-GLOB-v4.1/` (us-west-2), Earthdata login (per S2) |
| License | NASA/JPL open data; free use + redistribution (cite GHRSST + JPL MUR DOI 10.5067/GHGMR-4FJ04) |

### 1.2 Secondary product -- VIIRS L2P (sharper fronts, per the dispatch)

| Field | Value |
|---|---|
| Dataset | GHRSST **L2P VIIRS** (Suomi-NPP / NOAA-20), ~750 m swath, per-overpass, 2012+ |
| Access | PO.DAAC / Earthdata; OPeNDAP |
| Use | L4 MUR smooths narrow Haro Strait / Boundary Pass channels; VIIRS L2P resolves sharper thermal
  fronts but is cloud-gappy (composite/gap-fill needed). Use MUR as the daily backbone and VIIRS as a
  sharper-front overlay where cloud-free. License: GHRSST open. |

### 1.3 Reachability finding from THIS environment (measured, honest)

A bounded read-only probe was run (no write, no fit). Findings:

- The canonical global `jplMURSST41` ERDDAP hosts (`coastwatch.pfeg.noaa.gov`, `upwell.pfeg.noaa.gov`)
  and PO.DAAC reset the TLS connection from this sandbox (`curl (35) Recv failure: Connection reset`,
  HTTP 000), while generic outbound works (`example.com` -> 200). So MUR-via-PFEG is **NOT reachable
  here**; in a production fetch use the aimez EC2 escape hatch (B.9) or PO.DAAC S3 in us-west-2.
- The NOAA CoastWatch ERDDAP (`coastwatch.noaa.gov/erddap`) IS reachable. It carries a MUR **East
  Coast EEZ** clip (`noaacwecnMURdaily`, wrong region for the Salish Sea, ends 2022) and the global
  **Geo-polar Blended 5 km** SST (`noaacwBLENDEDsstDNDaily`, `analysed_sst`, 2019-07-22 ->
  2026-06-25, GHRSST open license), which DOES cover the cluster. The blended 5 km was used below as a
  **coarse cross-check only** -- it is NOT the recommended product (5 km cannot resolve the
  sub-kilometre channel fronts MUR 1 km / VIIRS 750 m would; it under-states front strength).
- Multi-day griddap subsets on the blended dataset hit the server's ~60 s gateway timeout (HTTP 502
  after 60 s); only single-day slices returned reliably. So a full multi-year near-cluster gradient
  time series was NOT obtained here. This is a probe limitation, not a property of the covariate.

## 2. CONSTRUCTION RECIPE (|grad SST| + distance-to-front, orthogonalized vs k_season)

Station cluster (from `modeling/studies/common.py STATION_COORDS`): orcasound_lab (48.558, -123.174),
andrews_bay (48.550, -123.167), north_san_juan_channel (48.591, -123.059), haro_strait (48.516,
-123.152) -- an ~8x9 km box. Use a working bbox with a halo for the gradient stencil, e.g. lat
[48.40, 48.70], lon [-123.35, -122.90].

1. **Fetch** daily `analysed_sst` over the bbox for the full acoustic span (MUR 1 km; VIIRS where
   cloud-free). Convert to degC. Cache locally (B.7 local-only; do not write the served store).
2. **Gradient field.** Per day, compute the horizontal gradient magnitude on the SST raster:
   `|grad SST|(x,y) = sqrt((dT/dx)^2 + (dT/dy)^2)`, with `dx = dlon * 111000 * cos(lat)`,
   `dy = dlat * 111000` (metres), central differences interior, one-sided at edges. Units degC/km.
3. **Front mask + distance-to-front.** Define a front mask `|grad SST| >= q` (q = a fixed percentile,
   e.g. the 90th percentile of the in-region climatological gradient, frozen out-of-sample). For each
   station/day compute (a) `front_strength` = mean `|grad SST|` in a small radius (e.g. <=5 km) around
   the station, and (b) `dist_to_front` = great-circle distance from the station to the nearest masked
   front cell. Optionally lag a few days for a prey-response delay (pre-register the lag like
   `salmon_lag.py`, selected out-of-sample on training folds only).
4. **Per-(station, day) covariate** keyed by the bin-centre date, broadcast to the hourly bins of that
   day (the front evolves on a daily, not hourly, timescale).
5. **Orthogonalize vs `k_season` (load-bearing, B.2 RAIL).** Absolute SST is `k_season`; the residual
   gradient is the independent signal. Inside CV, **on the training fold only**, regress the front
   covariate on the season Fourier basis (the same 2-harmonic columns `season__{cos,sin}_{1,2}` the
   model uses) and carry forward the **residual** to both train and test (apply the train-estimated
   season fit to the test fold's covariate). This guarantees the credited skill is the
   season-orthogonal part and is leakage-safe. Standardize the residual (train mean/sd) before entry.
6. **Enter as an APERIODIC effect-modifier** (a single standardized linear column, or a low-order
   natural-spline with <=2 df), NOT a Fourier kernel, fit jointly with the existing kernels + `log E`.

Honest collinearity note (M3 C1 / S2): even after season-orthogonalization a moderate seasonal
front climatology remains, and the 4-clustered-station geometry damps the SPATIAL leverage of fronts
(all four stations see nearly the same cell), so what is actually credited is the **temporal
evolution of front strength near the cluster**, not a spatial front map.

## 3. DRY-RUN / MEASURED PROBE

### 3.1 What was measured (real, bounded, blended-5km cross-check)

Single-day `analysed_sst` slices over the cluster halo bbox (5 km blended), `|grad SST|` computed per
day with the section-2 stencil:

| date | n grad cells | mean \|grad SST\| (degC/km) | max \|grad SST\| | mean SST (degC) |
|---|---:|---:|---:|---:|
| 2023-07-15 | 24 | 0.0129 | 0.0271 | 11.53 |
| 2023-07-22 | 24 | 0.0314 | 0.0622 | 12.17 |
| 2023-08-15 | 24 | 0.0308 | 0.0589 | 14.17 |
| 2024-07-15 | 24 | 0.0735 | 0.1227 | 14.33 |

Across these 4 summer days: mean `|grad SST|` ~0.037 degC/km, **day-to-day CV ~0.60**. Two qualitative
reads relevant to the GO decision:
- The gradient varies substantially day-to-day (>5x between the weakest and strongest of these days).
- The gradient is **partly decoupled from the absolute SST level**: 2023-07-22 (SST 12.2) and
  2023-08-15 (SST 14.2) have near-identical gradients (~0.031), while 2024-07-15 (SST 14.3) has the
  highest gradient (0.074). So the front strength is not a simple monotone function of the seasonal
  SST level -- consistent with `|grad SST|` carrying sub-seasonal content distinct from `k_season`.

These four numbers are MEASURED. They are a sourcing-plausibility confirmation only: n=4 days, a single
box, 5 km blended (front strength UNDER-stated vs MUR 1 km), and **no formal season-orthogonalization
or held-out scoring**. They do NOT establish the gated quantity.

### 3.2 What is NOT-MEASURED (and why)

- **Incremental fold-stable CV-skill of the front covariate: NOT-MEASURED.** A real dry-run of the
  gated quantity requires, simultaneously: (a) the served 4-station acoustic store via S3 (B.5 env),
  (b) a multi-year MUR/VIIRS near-cluster gradient series (the canonical MUR hosts reset here; the
  blended multi-day pulls 502-timeout), and (c) estimator support for an **aperiodic** covariate plus
  the per-fold season-orthogonalization -- none of which exist in the current code
  (`modeling/estimator.py _build_features` builds Fourier columns ONLY; `CYCLIC` is the only covariate
  family). Building all three is a production-adjacent integrate, out of this lane's bounded,
  no-convergence-edit scope. It is delivered as the PATCH-SPEC (section 5), to be measured by the
  later single-editor integrate.
- Per-day multi-year series, season-orthogonal residual variance fraction, distance-to-front
  distribution near the cluster: NOT-MEASURED (probe blocked as in 1.3 / 3.2a).

### 3.3 Expected-skill band (from M3-C1 + S2, reconciled)

M3-C1 expected held-out band: **0.00 to +0.05** marginal CV mean-deviance-skill, IF a real SST feed
lands and the front is not absorbed by season. S2 ranks it #2 (GO-conditional). Reconciled honest
expectation for THIS lane: a **small, genuinely-independent** contribution centred near **+0.01 to
+0.03**, plausibly up to **+0.05** with MUR 1 km / VIIRS fronts (sharper than the 5 km cross-check
above) and a well-chosen lag; **plausibly ~0 (or negative in CV)** if the 4-clustered-station geometry
leaves only a season-collinear residual. On its own this does NOT close the +0.078 -> +0.144 gap; it
is one independent covariate that must be stacked with the Tier-A clean-up (A2/A3) and the other
Tier-B observation levers (B1 nodes), and judged on the fold-stable held-out number, never in-sample.

## 4. GO / NO-GO

**GO -- CONDITIONAL (prototype-and-measure), confidence-neutral.** Source MUR `jplMURSST41` (VIIRS L2P
for sharper fronts), build `|grad SST|` + distance-to-front per (station, day), orthogonalize vs
`k_season`, and measure the **marginal, fold-stable** held-out CV-skill via `block_cv`
(`write_outputs=False`). It is a genuinely independent physical driver (the strongest field-sourced
covariate after AIS effort), the measured probe shows real, season-decoupled day-to-day variability,
and the construction has a clean B.2 role. The GO is conditional on:
1. the season-orthogonalized front surviving fold-stable held-out scoring (>=4/5 folds positive,
   across-fold lower bound >= +0.078 only matters at the +0.144 promotion stage; here the bar is
   simply a positive, fold-stable MARGINAL skill vs the A2/A3-cleaned baseline), NOT in-sample fit;
2. sourcing MUR/VIIRS (not the 5 km blended cross-check) for real front sharpness;
3. entry as the de-seasonalized gradient effect-modifier ONLY (absolute SST stays out, B.2 RAIL).

**NO-GO if** the season-orthogonal residual collapses to ~0 independent variance in CV (the front is
just re-expressing `k_season` / the cluster geometry damps it). Nothing here promotes; effective
confidence stays 0.0; any confidence change is a later passing gate on SERVED data + a recorded
supervisor decision (B.1).

## 5. PATCH-SPEC (for the later single-editor, operator-gated integrate)

No file below is edited by this lane. Each is a convergence file; this is the spec for the single
editor.

**P1 -- new source `src/aws_backend/sources/sst_front.py` (or `modeling/sst_front.py`, local-only).**
- `fetch_mur_sst(bbox, start, end) -> daily SST rasters` from `jplMURSST41` ERDDAP griddap
  (`analysed_sst`), VIIRS L2P optional overlay. Cache to a local parquet/json (B.7; NOT the served
  store). Route via aimez EC2 (B.9) if the dev host cannot reach the PFEG/PO.DAAC hosts (see 1.3).
- `front_covariate(rasters, station_coords, lag_days=0) -> Dict[(station, date) -> {front_strength,
  dist_to_front}]` implementing the section-2 stencil, mask, and station sampling.
- Provenance/license recorded in the cache header (GHRSST + JPL MUR DOI 10.5067/GHGMR-4FJ04).

**P2 -- `modeling/design.py build_design`.** Add an optional `sst_front_by_station_day` arg; in the
per-bin row loop add `"sst_front": float(value_for(station, date_of(center)))` (NaN when missing, so
it is handled exactly like the `tide` NaN path). Daily value broadcast to that day's hourly bins.

**P3 -- `modeling/estimator.py` (the load-bearing change: aperiodic covariate support).**
- Introduce `LINEAR_COVARIATES = ("sst_front",)`. In `_build_features`, for a name in
  `LINEAR_COVARIATES` add a SINGLE standardized linear column `f"{name}__lin"` (or a <=2-df natural
  spline) INSTEAD of Fourier columns; leave the existing cyclic path unchanged.
- In `fit_glm`, include `sst_front` in `usable_covariates` only when finite; reconstruct it as a
  linear coefficient (not a `KernelFit` Fourier curve) in the `FittedModel`.
- **Per-fold season-orthogonalization (leakage-safe):** before fitting, on the TRAIN frame regress
  `sst_front` on the season Fourier columns, subtract the fitted seasonal component from BOTH train
  and test `sst_front` (apply the train coefficients to test), then standardize by train mean/sd.
  Implement this inside `make_fit_predict` / a wrapper so `block_cv` credits only the season-orthogonal
  residual. (Equivalent: residualize once globally is NOT acceptable -- it leaks; do it per fold.)

**P4 -- scoring (no convergence edit; an isolated scratch driver).** Score the marginal skill in
`.venv-modeling` with `ORCAST_STORAGE_BACKEND=aws
ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads AWS_REGION=us-west-2`,
`fit_kernels._maybe_write_s3 = lambda: None`, `write_outputs=False`: run `block_cv` for the baseline
covariate set and for baseline+`sst_front` on the SAME 5 folds; report per-fold deviance skill, the
mean, the across-fold lower bound, and the MARGINAL (with - without). Never write
`data/models/fit_report.json` or any served artifact.

**P5 -- confidence/gate: unchanged.** `_confidence_from_gates` and the supervisor rule are not
touched. The covariate is judged purely by the fold-stable held-out marginal CV-skill vs +0.144;
effective confidence stays 0.0 until a passing gate on SERVED data + a recorded supervisor decision.

**DE drift note (per the RECALIBRATION-FROM-DE preamble).** This patch-spec keeps M3-C1 as a
CONDITIONAL GO and enforces the B.2 role-honesty caveat flagged in `DE1_text_drift.md` rows #6-10 /
S2 section 2: SST is admissible ONLY as the season-orthogonalized `|grad SST|` effect-modifier;
absolute SST must never enter (it would launder `k_season` into presence), and terrain stays
`s_space`-only. The single editor should land this caveat alongside the change.

## 6. RETURN SUMMARY

- **Doc path:** `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/graduation/TB2_sst_front.md`.
- **Sourcing:** MUR `jplMURSST41` (1 km daily, NASA JPL PO.DAAC; ERDDAP griddap or PO.DAAC S3
  us-west-2; GHRSST open) as the backbone + VIIRS L2P (~750 m) for sharper fronts. Provenance/license
  recorded. From this sandbox the canonical MUR/PFEG/PO.DAAC hosts reset (use EC2/S3 in production);
  the NOAA CoastWatch global blended 5 km SST was reachable and used as a coarse cross-check only.
- **Construction:** `|grad SST|` + front mask + distance-to-front per (station, day), broadcast to
  hourly bins, **season-orthogonalized per fold** (B.2 RAIL), entered as an aperiodic linear
  effect-modifier with `log E`.
- **Measured (probe):** 4 summer days near the cluster, mean `|grad SST|` 0.013-0.074 degC/km
  (5 km blended), day-to-day CV ~0.60, gradient partly decoupled from the absolute SST level ->
  qualitative support that the front carries sub-seasonal, season-independent content.
- **NOT-MEASURED:** the incremental fold-stable CV-skill (requires S3 served store + multi-year
  MUR/VIIRS series + estimator aperiodic-covariate support; all out of bounded no-convergence-edit
  scope). **Expected band:** marginal CV-skill ~ **+0.01 to +0.03**, up to +0.05 with MUR/VIIRS
  fronts, plausibly ~0/negative if season-collinear or geometry-damped. Not a stand-alone +0.144 lever.
- **GO/NO-GO:** **GO -- CONDITIONAL** (prototype-and-measure, confidence-neutral); NO-GO if the
  season-orthogonal residual collapses in CV.
- **PATCH-SPEC:** new SST-front source (P1), `build_design` join (P2), `estimator.py` aperiodic
  covariate + per-fold season-orthogonalization (P3), isolated `write_outputs=False` scoring driver
  (P4), gate unchanged (P5), with the DE role-honesty drift note.
- **Confirmation:** nothing was deployed, fetched-to-write, ingested, promoted, or committed; no
  convergence file edited; only this one doc written; mlops-gate untouched. **Effective confidence
  0.0.**
