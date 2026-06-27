# RC findings: time-of-day conditioning + temperature/SST feasibility

Agent: RC (L2/L3 push research waveset). Charter: `RESEARCH_CHARTER.md` (question Q3 + Q5).
Locked decisions: `HANDOFF_CHARTER.md` section B. Methodology: `docs/methodology/FORECAST_KERNELS.md`.
Investigation-first. No convergence-file edits; no production store/model write; no confidence
promotion; nothing committed. An honest "no gain" is a valid result (B.3).

Report JSON: `modeling/studies/reports/L3_diel_temperature.json`.
Scratch (read-only reuse of `salmon_lag.py` + `common.py`, deleted after): `/tmp/rc_research/diel_cond.py`.

---

## Part 1 - Time-of-day (diel) conditioning of the salmon-lag signal

### Method

The L3 salmon test correlates daily acoustic presence against the lagged Albion (Fraser-summer
Chinook) run index over +/-30 d, with a 1000-sample circular-shift permutation null. I conditioned
that test on the **fitted `k_diel` active window** and re-ran it, holding everything else identical:

- Active window = the local solar hours where the fitted diel kernel's log-rate contribution is
  positive (mean-centered), read from the local `data/models/fitted_kernels.json`
  (`repr_96cc7ce94f4a5ed6`): **phase 0.405-0.815, i.e. solar hour ~09:43 to ~19:34** (peak phase
  0.62 ~= 14:50). This matches the L1 diel PSTH (modulation 1.79, p=0.0005), whose high-count bins
  are the afternoon/evening hours.
- Each of the 1359 cached OrcaHello detections was assigned its diel phase
  (`common.diel_phase`, per-station longitude from `STATION_COORDS`) and classified active/inactive
  by the sign of the fitted kernel at that phase.
- Daily presence was rebuilt over the same full day span (2020-09-28..2026-06-16, 2088 days) for
  three subsets, and the lag scan + permutation null were re-run via the unmodified `salmon_lag.py`
  functions (`_build_run_index`, `_best_lag`, `_permutation_null`). Salmon source = Albion for every
  detection year (single source, stock-aligned).

### Measured numbers

| Scan | detections | days w/ presence | best lag | r | null mean\|r\| | p | beats null? |
|------|-----------:|-----------------:|---------:|------:|--------------:|------:|:-----------:|
| Full (unconditioned) | 1359 | 163 | +20 d | 0.0757 | 0.0809 | **0.394** | no |
| Active window only | 802 (59%) | 105 | +18 d | 0.0719 | 0.0716 | **0.326** | no |
| Inactive window only | 557 (41%) | 82 | -26 d | -0.0568 | 0.0678 | **0.402** | no |

The full scan exactly reproduces the committed `salmon_lag.json` (best lag +20 d, r 0.076, p 0.394),
confirming the harness is wired correctly.

### Result (honest)

**Conditioning on the diel-active window does not change the salmon-lag signal.** The best lag moves
trivially (+20 -> +18 d), the correlation barely moves (0.076 -> 0.072), and the p-value stays far
from significance (0.394 -> 0.326). The active-window correlation sits essentially on its own null
mean (0.072 vs 0.072). The inactive subset is, if anything, weaker.

This is the expected outcome and confirms the charter's prior (Q3): **time-of-day is irrelevant at
the daily/seasonal salmon timescale.** Diel structure is an intraday (L1/L2) phenomenon; the L3 test
relates *which days* have presence to *seasonal* run timing, and collapsing to daily presence
already integrates over the diel cycle. Selecting only afternoon/evening detections removes ~41% of
the data (lower power) without sharpening the seasonal alignment. There is no diel-conditioning route
to an L3 pass.

**Recommendation:** do NOT pursue diel conditioning for L3. It neither helps nor is the blocker. (The
L3 blocker is the absence of a daily-presence-vs-run-timing signal itself - see RA counts/GLM and RB
season/per-station conditioning for the response-variable and seasonal-restriction avenues.)

---

## Part 2 - Temperature / SST: source coverage + honest role + go/no-go

### What already exists (inspected)

- `src/aws_backend/sources/noaa.py` (`NoaaAdapter`): CO-OPS datagetter. `current_environment()`
  pulls `water_temperature` (latest) from Friday Harbor `9449880` and converts to degC. History
  helpers exist for `water_level` and `currents` (harmonic predictions for `PUG1701/2/3`); there is
  **no `water_temperature` history helper**, though the datagetter supports it (verified below).
- S3 store (`198456344617-us-west-2-orcast-aws-backend-raw-payloads`, us-west-2) `timeseries/`
  streams present: `acoustic_detections, env_currents, env_water_level, noaa_ndbc_stdmet,
  salmon_run_index, station_uptime, spatial_grid_covariates, obis_verified, inaturalist_verified,
  orcahello_reviewed_detector_outcomes, ferry_effort_wa, ferry_effort_bc, protected_areas_ca,
  shoreline_distance`. **There is no dedicated SST/water_temperature stream**; the only water
  temperature in the store is the `WTMP` column inside `noaa_ndbc_stdmet`.
- The fit currently ingests `noaa_ndbc_stdmet` station `46088` for **2026-05-08..2026-06-27 only
  (7215 records)**, and `fit_report.json` labels it `"detectability/noise metadata; not yet a
  fitted animal-behavior kernel"` - already consistent with B.2.

### Data-availability spike (small, real probes; both feeds reachable LOCALLY - no EC2 needed)

| Source | Station / loc | Reachable locally | Coverage over acoustic window | Cadence | Valid |
|--------|---------------|:-----------------:|-------------------------------|---------|-------|
| NDBC historical stdmet `WTMP` | `46088` New Dungeness, E Strait of Juan de Fuca (~48.33N,123.17W; ~20-24 km S of Haro) | yes | full year-round 2020,2023,2025 verified (52k rows/yr, 10-min) | 10 min | 99% valid |
| CO-OPS `water_temperature` | `9449880` Friday Harbor (48.545N,123.013W; ~9 km E of Haro array) | yes | returns data for 2020-01 (winter), 2021-05, 2023-07, 2026-06 - full 2020-2026 | 6 min | live |
| CO-OPS `water_temperature` | `9443090` Neah Bay (strait mouth, ~120 km W) | yes | regional only (too far) | 6 min | live |

Notes: NOAA CO-OPS `9449880` returns *no* data for `date=latest` water_temperature (why the adapter
falls back to 12.0 degC) but **does** return a full historical series for explicit date ranges.
Neither feed is DNS-blocked here, so no aimez EC2 work was required and `/tmp` needs no cleanup beyond
the scratch dir.

**Coverage verdict: temperature is abundant and complete over the 2020-2026 Haro Strait window** from
two independent, locally reachable feeds within the array footprint (CO-OPS Friday Harbor ~9 km;
NDBC 46088 ~20-24 km). Availability is not a blocker.

### Honest role classification (per B.2)

The methodology is explicit: weather (wind/waves/temperature) and AIS enter as **detector-QC / effort
terms at Level 0, NOT as animal kernels**. Classifying the two candidate roles the charter names:

1. **Detectability / effort term at Level 0 (role b): defensible but weak and largely redundant.**
   Water temperature has only a small effect on sound speed / propagation; the dominant acoustic-QC
   covariates are ambient *noise* and *sea state* (`WSPD`, `WVHT`), which `noaa_ndbc_stdmet` already
   supplies and which the fit already carries as detectability metadata. Temperature would be a minor,
   collinear addition to the L0 detector-QC model - and the L0 detector already **PASSES** (ROC AUC
   0.879). So the role is legitimate but low-value.

2. **Prey/habitat effect modifier for `s_space`/`k_salmon` (role a): NOT defensible on this data.**
   Over the Salish Sea / Haro Strait for 2020-2026, SST is almost entirely a function of day-of-year;
   it is **collinear with `k_season`** (which the model already represents and which is currently
   *withheld* for phase coverage 0.75 and earned no skill). The prey pathway is already routed through
   `k_salmon` (run-timing index) and habitat through `s_space` (bathymetry/channel). A raw-SST animal
   kernel would double-count the seasonal cycle and is **not separately identifiable from `k_season`**
   on this detection set. SST is at best an indirect proxy for the same seasonal/prey signal the model
   already targets. Treating it as an animal kernel would violate B.2 without justification.

**Verdict: temperature/SST is primarily a Level-0 detectability/effort covariate, and is NOT a
defensible standalone animal kernel** without independent evidence that it adds skill *beyond season*
- evidence this data cannot provide (SST ~= f(season), and `k_season` itself is withheld/no-skill).

### Go / no-go on a temperature feasibility spike

- **Data availability: GREEN.** Both feeds are complete over 2020-2026 and reachable locally; wiring a
  `water_temperature` history pull (CO-OPS `9449880`) or extending the NDBC `46088` `WTMP` ingest is
  mechanically trivial.
- **As an animal kernel: NO-GO.** Forbidden by B.2 without justification; not identifiable from
  `k_season`; and it cannot move either binding constraint - L2 is bounded by detection burstiness +
  single-station sample size (temperature-independent), and L3 shows no daily-presence-vs-run-timing
  signal at all (Part 1; STEP_LOG W3), with SST *more* collinear with season than salmon is.
- **As an L0 detector-QC covariate: optional, low priority.** Cheap to add, but ambient noise / sea
  state already dominate L0 and the L0 gate already passes. Not worth a dedicated build wave.

**Bottom line: honest NO-GO on a temperature spike.** Coverage is excellent, but temperature has no
defensible animal-kernel role here and no path to moving L2 or L3. If anything is ever wired, it is a
minor L0 detectability term, not a `k_temp` animal kernel.

---

## Risks / caveats

- The diel-active window is taken from the single-station (`haro_strait`, 761-detection) fit's
  `k_diel`; the conditioning detections are the 1359-record multi-station cached index. The window is
  corroborated by the multi-station L1 PSTH, so the mismatch does not affect the conclusion, but a
  multi-station refit could shift the window by an hour or two (immaterial to the daily-scale result).
- The SST collinearity-with-season argument is qualitative (no SST-vs-season fit was run, per the
  "small spike only" scope). It is the standard oceanographic expectation for this region and is
  consistent with `k_season` already being the model's seasonal term; a formal variance-partition is
  the only thing that could overturn the NO-GO, and B.2 puts the burden of proof there.
- No production store or model artifact was written; `fit_report.json` is untouched; the experiment
  reused `salmon_lag.py` read-only and ran the salmon source off the local Albion cache (no network
  fit). The only new tracked artifact is this doc + the report JSON.
