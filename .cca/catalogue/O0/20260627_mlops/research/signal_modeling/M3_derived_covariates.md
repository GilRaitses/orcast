# M3 subtler derived covariates (the "more signal per observation" lever)

Agent: W10-M3 derived-covariate research agent, W10 of the signal & modeling research campaign.
Date: 2026-06-27 (America/New_York). Repo: `/Users/gilraitses/orcast`.
Home: `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/M3_derived_covariates.md` (this doc;
no other file edited).
Authority: `20260627_mlops-handoff/HANDOFF_CHARTER.md` section B (B.1 honesty, B.2 covariate-role
honesty, B.3 withhold-over-fake); `SIGNAL_MODELING_CHARTER.md`; `SIGNAL_MODELING_DISPATCH.md` (M3).
Scope: investigation + recipe spec only. No fit that writes, no deploy, no promotion, no commit.
Effective confidence stays 0.0.

## 0. Hydration (what I read)

- `HANDOFF_CHARTER.md` section B (B.1 promotion = passing gate on SERVED data + recorded supervisor
  decision; B.2 effort-bias / covariate-role; B.3 withhold-over-fake; B.4 bucket; B.6 local-only tree).
- `SIGNAL_MODELING_CHARTER.md` (the +0.144 lever; two ways to cross 0.6; anti-overfitting sec 4).
- `SIGNAL_MODELING_DISPATCH.md` (the M3 brief, followed exactly; the six required categories).
- `docs/methodology/FORECAST_KERNELS.md` (model form, current covariates, the effort-bias design).
- `modeling/tide_harmonic.py` (the committed M2/S2/N2/K1/O1 harmonic predictor + `phase`).
- `modeling/tide_phase.py` (`TidalPhase`, `HarmonicTidalPhase`; flood-onset anchor; `value_at`).
- `modeling/design.py` (the (station, time-bin) count table; `diel/lunar/season/tide` columns; the
  `log_exposure` effort offset; `phase_coverage`).
- `modeling/bases.py` (the truncated Fourier basis; `[cos_h, sin_h]` columns).
- `modeling/fit_kernels.py` (CYCLIC = diel/tide/lunar/season; NB2 + Poisson GLM at `n_harmonics=2`;
  tide drop-when-no-overlap; `season_extrapolated` coverage guard; 5-fold CV; time-rescaling).
- `modeling/studies/common.py` (`STATION_COORDS` for the four nodes; cached-index loaders).
- `modeling/studies/salmon_lag.py` (the pre-registered Jun-Sep lag scan; stock-alignment gate;
  climatology fallback => WITHHELD).
- `modeling/studies/level3_prey_space.py` (s_space precursor + the effort-confound warning).
- `src/aws_backend/sources/bathymetry.py` + `src/aws_backend/spatial_enrichment.py` (served depth is
  ETOPO1 1 arc-minute in `data/geo/san_juan_bathymetry.json`; `depth_at`, `nearest_shore_m`).
- `research/forward/G2_promotion_protocol.md` (the verified P0 confidence map; +0.144 = 0.60 crossing).
- `research/R2_bathymetry_soundings.md` (CUDEM is NCEI 1/9 arc-second (~3 m) topobathy, NAVD88,
  a MODELED interpolated surface; lives in the 3d-twin pipeline, NOT in the modeling tree).
- Checked for `research/signal_modeling/S2_covariate_sources.md`: NOT PRESENT at start. Every item
  below that needs an external feed carries an explicit S2 dependency flag (section 0.3).

## 0.1 The locked rails this doc obeys (restated)

- B.1 No promotion. Findings here are decision aids. A derived covariate earns confidence only later
  via a passing gate on SERVED data + a recorded supervisor decision. Effective confidence stays 0.0.
- B.2 Covariate-role honesty (load-bearing). Every covariate below is classed as exactly one of:
  (a) effort/exposure term (enters the `log E(x,t)` offset, never the heat); (b) effect-modifier
  covariate (enters a kernel / the intensity, estimated from effort-stable ACOUSTIC detections);
  (c) validation-only (informs `s_space` or the held-out validation set, built from VISUAL sightings
  which carry structured observer bias). Acoustic presence drives the temporal kernels with the
  `log E` offset; visual sightings stay validation + `s_space`. Nothing here is laundered into a
  whale GPS fix: a hydrophone detection is a fixed-position presence event, not a located animal.
- B.3 Withhold over fake. Where a covariate cannot be honestly identified at our N or its source is a
  placeholder, the recipe says WITHHELD with the reason rather than reporting a fabricated kernel.
- Anti-overfitting (charter sec 4). Each item is judged by EXPECTED out-of-sample, fold-stable CV
  mean-deviance-skill toward the +0.144 bar, never by in-sample fit or added parameters.

## 0.2 The model the covariates plug into, and the df budget (grounding the skill claims)

The served fit is a negative-binomial (NB2) log-linear point-process GLM on a (station, time-bin)
count table (`design.build_design`, `fit_kernels.fit_glm`). For each station-hour bin it carries the
detection count `y`, the `log_exposure` effort offset, and the cyclic phases `diel`, `tide`, `lunar`,
`season`. Each cyclic kernel is a truncated Fourier series at `n_harmonics=2` (four coefficients per
kernel: `cos_1, sin_1, cos_2, sin_2`; `bases.fourier_columns`), mean-zero over the cycle so `b0`
owns the level. The estimated intensity is

```
log lambda = b0 + k_diel(phase) + k_tide(phase) + k_lunar(phase) + k_season(phase)
                + (k_salmon, s_space when admitted) + log E
```

Three numbers bound what any new covariate can honestly buy:

1. N ~ 2089 detections across 4 stations, and the train is BURSTY (G2 / handoff: 63 to 91% of
   detections fall within 6 min of the prior). Effective independent N is well below 2089, plausibly
   a few hundred, so the usable degrees-of-freedom budget is small. Every added Fourier block (4
   coefs) or interaction tensor spends scarce df and is the first thing the 5-fold CV punishes.
2. The four stations are SPATIALLY CLUSTERED. `STATION_COORDS`: orcasound_lab (48.558, -123.174),
   andrews_bay (48.550, -123.167), north_san_juan_channel (48.591, -123.059), haro_strait
   (48.516, -123.152), i.e. all inside an ~8 by ~9 km box in west San Juan / Haro Strait. Any
   STATIC spatial covariate is nearly constant across the four points, so it cannot move the
   temporal CV-skill the gate measures; it collapses into a near-constant absorbed by `b0` or, at
   most, a 4-point station fixed effect (3 df, saturated, no held-out gain).
3. The gate the +0.144 bar lives on (G2) scores the held-out CV mean-deviance-skill of the ACOUSTIC
   temporal fit, plus PIT and a Level-1 null. It does NOT score the spatial `s_space` surface and it
   does NOT read visual sightings. So a covariate only moves the bar if it adds independent TEMPORAL
   structure to the effort-stable acoustic intensity. This is the single most important filter below.

## 0.3 S2 dependency status

`research/signal_modeling/S2_covariate_sources.md` (sibling W9-S2) does NOT exist at the time of
writing. For every derived covariate that needs an external feed I (a) assume a reasonable candidate
source from `FORECAST_KERNELS.md` and the dispatch's own list, and (b) flag the S2 dependency
explicitly so the synthesis can bind the real source/provenance/license/cadence once S2 lands.
Assumed candidate sources, pending S2 confirmation:

- Tidal currents: NOAA CO-OPS current predictions (the `env_currents` stream already feeds the
  harmonic tide). In-repo today; no S2 dependency for the tidal-nonlinearity items.
- 2D surface currents (for shear/strain/convergence): SalishSeaCast ROMS NEMO surface velocity ONLY.
  HF radar is NO-GO in-region (the inland San Juan/Gulf Island channels are radar-shadowed -- S2
  section 3 #8); SalishSeaCast supersedes it. NOT in repo. S2-DEPENDENT.
- SST / thermal fronts: NOAA/NASA MUR SST (1 km daily) or VIIRS. NOT in repo. S2-DEPENDENT.
- Salmon run timing: DFO Albion Fraser test fishery (stock-aligned) per `salmon.py`. The adapter is
  wired but falls through to climatology, so a REAL Albion feed is the dependency (feed/S2).
- Bathymetry terrain: NCEI CUDEM 1/9 arc-second topobathy. Present in the 3d-twin infra
  (`research/R2_bathymetry_soundings.md`), NOT in the modeling tree; the modeling `s_space` depth is
  the coarse ETOPO1 1 arc-minute asset. Wiring CUDEM into modeling is a build dependency, not strictly
  S2, but flagged.

## 1. The derived covariates

Each item below states: the COMPUTATION RECIPE (from which existing/sourceable signal); the PHYSICAL
RATIONALE for why it should track SRKW presence; its ADMISSIBLE ROLE under B.2; COLLINEARITY with
existing covariates; the EXPECTED held-out-skill contribution (an honest Delta-skill band relative to
the +0.078 served experiment and the +0.144 bar); and any S2/feed dependency.

### Category A. Tidal-phase nonlinearities + slack / max-flow timing

Baseline: `k_tide` is already a 2-harmonic Fourier kernel on a tidal phase in [0,1) anchored at
flood-current onset (`HarmonicTidalPhase`, M2-derived phase from the `env_currents` harmonic fit).
Two harmonics already bend the kernel away from a pure sinusoid, so any "nonlinearity" feature that
is a deterministic function of the SAME single-cycle phase is largely redundant with the existing
columns. The genuinely new content is (i) the spring-neap amplitude envelope (cross-cycle), and (ii)
rectified distance-to-slack / distance-to-max-flow, which folds the phase in a way two raw harmonics
approximate but do not exactly represent.

**A1. Distance-to-slack and distance-to-max-flow (rectified tidal timing).**
- Recipe: from the fitted `HarmonicTide` reconstruction `V(t)` (in-repo, `tide_harmonic.predict`),
  detect slack times as zero-crossings of `V` (already computed as onsets) and max-flow times as
  local extrema of `|V|`. For each bin center `t`, compute `d_slack(t) = min|t - t_slack|` and
  `d_maxflow(t) = min|t - t_maxflow|`, each normalized by the local half-period. Enter as 1 to 2
  smooth columns (or a small Fourier block on the folded phase).
- Rationale: SRKW foraging in Haro Strait is reported to track current state (flood/ebb transitions
  and reduced-flow slack windows where prey concentrate against bathymetry). A rectified "time from
  slack" captures a symmetric peak that a phase-origin kernel splits across the [0,1) seam.
- B.2 role: (b) effect-modifier, estimated from acoustic detections with the `log E` offset. The
  current series is a harmonic PREDICTION, not a measured flow, which is honest as a covariate (it is
  not presented as observed current and not used to locate an animal).
- Collinearity: HIGH with `k_tide` (same phase variable, folded). Net-new information is only the
  part of a slack-centered response that two harmonics cannot already fit. Flag: fit A1 jointly with
  `k_tide` and report the marginal CV-skill, not A1 alone.
- Expected held-out skill: SMALL. Realistic Delta-skill band roughly -0.01 to +0.03. It is cheap and
  in-repo, so worth a bounded test, but it will not by itself close +0.078 -> +0.144.
- S2/feed dependency: none (uses the existing harmonic tide). 

**A2. Tidal current speed magnitude |V(t)| (flow strength, with spring-neap envelope).**
- Recipe: `|V(t)|` from the same harmonic reconstruction, sampled at each bin center; optionally a
  low-pass envelope to expose the M2/S2-beat spring-neap modulation (~14.77 d). Enter as one smooth
  column.
- Rationale: prey transport and acoustic detectability both scale with flow strength; strong springs
  vs weak neaps change foraging windows. The within-cycle part is phase; the across-cycle envelope is
  the new content.
- B.2 role: (b) effect-modifier from acoustic detections + `log E`.
- Collinearity: within-cycle |V| is HIGH with `k_tide`; the spring-neap envelope is HIGH with
  `k_lunar` (the fortnightly tidal beat is phase-locked to the synodic month). So A2 mostly re-expresses
  tide+lunar already in the model. Flag the lunar collinearity explicitly.
- Expected held-out skill: SMALL and at RISK of being negative once it competes with lunar in CV.
  Band roughly -0.02 to +0.02.
- S2/feed dependency: none.

**A3. Raise `k_tide` harmonics (not a new covariate, the honest cheaper alternative).**
- Recipe: change `n_harmonics` for the tide kernel from 2 to 3 (one extra `cos_3, sin_3` block) and
  re-score under CV. This is the lowest-cost way to add tidal nonlinearity without a new feature.
- Rationale: if the tidal response is genuinely peaked/asymmetric, a third harmonic captures it with
  2 extra df instead of importing a correlated feature.
- B.2 role: (b) effect-modifier (the existing kernel, richer).
- Collinearity: by construction orthogonal Fourier terms, but spends df the small-N CV may not
  support; `k_tide` is already FLAGGED not-yet-reliable (G2: split-half unstable, orcasound -0.486).
- Expected held-out skill: SMALL, likely <= 0 given the tide kernel's existing instability. Useful
  mainly as the control that tells you A1/A2 are not buying anything two more harmonics would.
- S2/feed dependency: none.

Category A honest verdict: tide is already in the model and already FLAGGED unreliable cross-station;
the derived tidal features are dominated by the existing phase kernel and (for the envelope) by lunar.
Treat A1 as the one bounded prototype; A2/A3 as controls.

### Category B. Current shear / strain + convergence (fronts)

**B1. Convergence (-div u), horizontal strain rate, Okubo-Weiss at the station/cell.**
- Recipe: from a 2D surface-velocity field `u(x,y,t)` compute the spatial derivatives:
  convergence `-(du/dx + dv/dy)`, strain rate `sqrt((du/dx-dv/dy)^2 + (dv/dx+du/dy)^2)`, and the
  Okubo-Weiss parameter (strain^2 - vorticity^2) to separate frontal/strain-dominated cells from
  eddy cores. Sample the field at each station coordinate and bin center; enter the front strength as
  a smooth covariate.
- Rationale: tidal convergence fronts in Haro Strait / Boundary Pass concentrate prey and are a
  documented SRKW foraging cue. Convergence is physically the right "front" variable.
- B.2 role: (b) effect-modifier from acoustic detections + `log E`, IF a field exists.
- Collinearity: the TEMPORAL part of convergence at a fixed station is tidally driven, so it is HIGH
  with `k_tide`. The SPATIAL part (how convergence differs across cells) is where the independent
  signal lives, and that is exactly the dimension our 4 clustered fixed stations cannot resolve
  (section 0.2 point 2).
- Expected held-out skill: NEAR ZERO at current data. The spatial leverage that would make fronts
  pay off does not exist with 4 clustered point sensors; the temporal residue is collinear with tide.
- S2/feed dependency: YES, strong. Needs a gridded surface-current field (SalishSeaCast ROMS NEMO, or
  HF radar with limited Haro coverage). FLAG S2. Even with the feed, the data geometry blocks payoff
  until presence is resolved spatially (an S1 node-density question, not an M3 one).

Category B honest verdict: physically the most appealing "front" mechanism, but it is a SPATIAL
covariate measured at points that do not vary spatially, behind an S2-dependent feed. NO-GO at our N.

### Category C. Thermal-front proximity

**C1. SST-front strength |grad SST| and distance-to-front near each station.**
- Recipe: from a gridded SST product (assume MUR SST 1 km daily, pending S2) compute the horizontal
  gradient magnitude `|grad SST|` per cell-day; define a front mask by a gradient threshold; for each
  station/day compute local front strength and distance to the nearest front. Enter front strength as
  a slow (daily) effect-modifier; optionally lag it a few days for prey response.
- Rationale: thermal fronts aggregate forage fish and thus Chinook and thus SRKW; front PROXIMITY is
  a cleaner aggregator cue than absolute SST.
- B.2 role: (b) effect-modifier from acoustic detections + `log E`.
- Collinearity: absolute SST is HIGH with `k_season` (both track the annual cycle), so use the
  GRADIENT (front), which is far less seasonal than the mean. Residual collinearity with season is
  moderate (fronts have a seasonal climatology). Flag: orthogonalize against `k_season` and report the
  marginal skill.
- Expected held-out skill: SMALL-to-MODERATE and the most promising of the S2-sourced items, because
  the front gradient is a genuinely independent physical driver (not a deterministic function of an
  existing covariate). But the same 4-clustered-station geometry damps the spatial part; what remains
  is the temporal evolution of front strength near the cluster. Band roughly 0.00 to +0.05, IF a real
  SST feed lands and the front signal is not absorbed by season.
- S2/feed dependency: YES. Needs MUR SST (or equivalent). FLAG S2.

Category C honest verdict: the strongest of the field-sourced derived covariates because front
gradient carries information independent of tide/diel/lunar/season; conditional GO once S2 confirms a
real SST feed, with the seasonal-orthogonalization caveat.

### Category D. Prey-lag interaction terms

Baseline: `k_salmon` is currently a CLIMATOLOGY placeholder and L3 is WITHHELD (`salmon_lag.py`):
credit requires BOTH a real feed AND stock alignment (Fraser-summer Chinook via Albion; DART is real
but stock-mismatched). The pre-registered Jun-Sep scan already exists; these items extend it.

**D1. Lagged stock-aligned run index, run_index(t - L*).**
- Recipe: take the REAL Albion Fraser run-timing index; apply the pre-registered non-negative lag
  `L*` selected out-of-sample on training years (the `salmon_lag.py` machinery already does this lag
  selection); enter `run_index(t - L*)` as a slow effect-modifier (`k_salmon`).
- Rationale: well-supported in literature: SRKW core-summer presence tracks the Fraser Chinook run,
  which LEADS presence by days. This is the strongest non-tidal biological driver in the design.
- B.2 role: (b) effect-modifier from acoustic detections + `log E`.
- Collinearity: MODERATE-HIGH with `k_season` (the run is itself seasonal). The independent content
  is the YEAR-TO-YEAR and within-season run anomaly relative to the seasonal climatology, so enter
  the run ANOMALY (run minus its day-of-year climatology) to break the collinearity with season.
- Expected held-out skill: potentially the HIGHEST of any item here (this is the campaign's "more
  independent observation" overlapping with "more signal"), but UNVALIDATED today and gated on the
  feed. With a real Albion feed and the anomaly construction, a plausible band is +0.02 to +0.08; with
  the climatology placeholder it is WITHHELD (B.3), contributing 0 and not creditable.
- S2/feed dependency: YES, decisive. Needs a real, stock-aligned Albion feed. FLAG feed/S2.

**D2. Prey x tide interaction (run anomaly x flood/slack timing).**
- Recipe: product of the run anomaly (D1) with the rectified tidal-timing feature (A1), entered as a
  single interaction column.
- Rationale: prey is delivered/concentrated on particular current states, so the prey effect may be
  expressed mainly during favorable tidal windows.
- B.2 role: (b) effect-modifier from acoustic detections + `log E`.
- Collinearity: it is a product of two already-present effects; main-effect collinearity is handled
  by including both mains. Interaction tensors spend df fast at small N.
- Expected held-out skill: SMALL and overfitting-prone; only worth testing AFTER D1 main effect is
  validated on a real feed. Band -0.02 to +0.02 standalone.
- S2/feed dependency: YES (inherits D1's feed dependency).

**D3. Prey x space interaction (run anomaly x channel proximity).**
- Recipe: product of the run anomaly with a static channel-proximity terrain feature (E3). Spatial.
- B.2 role: the spatial factor is `s_space` (validation-class), so this interaction is creditable
  only on the temporal acoustic side through the run anomaly; the spatial factor cannot be validated
  on acoustic at 4 clustered stations. Treat as (c) validation-only / s_space-side until presence is
  spatially resolved.
- Collinearity / leverage: blocked by the 4-clustered-station geometry (section 0.2).
- Expected held-out skill: ~0 on the acoustic gate. S2/feed dependency: YES.

Category D honest verdict: D1 (lagged stock-aligned run ANOMALY) is the single highest-value derived
covariate, but it is feed-gated and currently WITHHELD; D2/D3 are second-order and overfitting-prone.

### Category E. Bathymetry-derived terrain features (from the CUDEM grid)

Source note: the CUDEM 1/9 arc-second (~3 m) topobathy is a MODELED, interpolated NAVD88 surface
(`research/R2_bathymetry_soundings.md`). The modeling tree's `s_space` currently uses only the COARSE
ETOPO1 1 arc-minute (~1.8 km) depth grid (`san_juan_bathymetry.json`), which is too coarse to resolve
slope/channel structure; CUDEM lives in the 3d-twin pipeline and would have to be wired into modeling.

**E1. Seabed slope |grad depth|.** Recipe: finite-difference gradient of the CUDEM depth raster per
cell; magnitude is the slope. **E2. Aspect** (slope azimuth, optionally projected onto the local
tidal-current axis). **E3. Channel proximity / thalweg distance**: extract the deep-channel axis (the
Haro Strait / Boundary Pass thalweg) from CUDEM and compute each cell's distance to it.
**E4. Bathymetric Position Index (BPI)** (cell depth minus annulus-mean depth: ridges vs canyons) and
**E5. rugosity / terrain roughness** (local depth variance).
- Rationale: SRKW travel and forage along deep channels and steep drop-offs where prey concentrate;
  slope, channel proximity and BPI are standard cetacean-habitat terrain covariates.
- B.2 role: (c) VALIDATION-ONLY / `s_space`. These are STATIC spatial covariates. Under the
  effort-bias design they inform the spatial habitat surface `s_space`, which is validated against
  held-out VISUAL sightings (effort-confounded), NOT the effort-stable acoustic temporal kernels.
  They must not be entered as temporal effect-modifiers.
- Collinearity: with `depth` (already in `s_space`) and with each other (slope, BPI, rugosity are
  correlated); and, on the acoustic side, with a STATION FIXED EFFECT (each terrain feature is one
  near-constant value per clustered station, so across 4 stations it is collinear with a 4-level
  station intercept).
- Expected held-out skill ON THE GATE: ~0. The G2 gate scores the acoustic temporal CV-skill, and
  static terrain at 4 clustered points adds no temporal information and no resolvable spatial
  information. Terrain features improve the `s_space` surface QUALITY (a real product win) but do not
  move the +0.144 served acoustic bar.
- S2/feed dependency: not S2 per se; a build dependency to wire CUDEM into the modeling tree (today
  only ETOPO1 1 arc-min is wired). FLAG the wiring + the resolution gap.

Category E honest verdict: GO for `s_space` quality (slope, channel-proximity, BPI from CUDEM), NO-GO
as a lever on the served acoustic CV-skill bar. State the role split honestly; do not let a terrain
feature masquerade as temporal skill.

### Category F. Spatiotemporal interaction terms

**F1. lunar x diel (nocturnal-illumination interaction).**
- Recipe: enter `moon_illumination(t) * night_weight(diel)` where `night_weight` is a smooth
  day/night indicator from the diel phase and `moon_illumination` is the existing lunar phase mapped
  to fractional illumination. One interaction column.
- Rationale: moonlight only matters at night; if nocturnal foraging (echolocation in darkness) is
  illumination-sensitive, the lunar effect should be expressed at night and absent by day. This is
  the physically cleanest interaction and could DE-ALIAS lunar from season (a known confound).
- B.2 role: (b) effect-modifier from acoustic detections + `log E`.
- Collinearity: with `k_lunar` and `k_diel` mains (include both); the interaction itself is the new
  content. Modest df cost (1 to 2 columns).
- Expected held-out skill: SMALL but the best-motivated interaction. Band -0.01 to +0.03. Cheap and
  in-repo (lunar + diel already computed in `design.py`).
- S2/feed dependency: none.

**F2. tide x diel (nocturnal-tidal foraging).** Recipe: product of the rectified tidal-timing feature
(A1) with the night weight. Rationale: tidal foraging may be stronger at night. B.2: (b)
effect-modifier. Collinearity: the joint additive fit already separates tide and diel; the
interaction is new but tensor df is costly. Expected skill: SMALL, overfitting-prone (band -0.02 to
+0.02). No S2 dependency.

**F3. diel x season (seasonal change in the diurnal pattern).** Recipe: tensor of the diel and season
Fourier blocks (or diel main scaled by a season-amplitude term). Rationale: daylight length and the
diel foraging pattern co-vary seasonally. B.2: (b). Collinearity: with both mains; full tensor is
many df. Expected skill: SMALL and HIGH overfitting risk at our N; the season kernel is itself often
`season_extrapolated`/withheld for coverage, which compounds the risk. Band -0.03 to +0.01.

**F4. station x tide (per-station tidal kernel).** Recipe: interact the tide kernel with the station
factor (random or fixed slopes). Rationale: the cross-station consistency study found tide
HETEROGENEOUS across stations (G2: split-half 0.159 haro, -0.486 orcasound), suggesting a per-station
response. B.2: (b). Collinearity: with the station effect and `k_tide`. Expected skill: as a FIXED
interaction it overfits hard (4 stations x tide harmonics on bursty small-N) and is NO-GO; the honest
route is a PARTIAL-POOLED (hierarchical) station random effect, which is M1's territory, not a derived
covariate. DEFER to M1.

Category F honest verdict: F1 (lunar x diel illumination) is the one cheap, physically-clean
interaction worth a bounded test; F2/F3 are second-order and overfitting-prone; F4 is a
partial-pooling modeling choice (defer to M1), not an M3 feature.

## 2. Collinearity summary

| Derived covariate | Chief collinearity | Independent content that survives | Net leverage |
|---|---|---|---|
| A1 distance-to-slack/max-flow | `k_tide` (same phase, folded) | slack-centered peak past 2 harmonics | small |
| A2 |V| flow strength + envelope | `k_tide` (within-cycle), `k_lunar` (spring-neap) | little | very small |
| A3 raise k_tide to 3 harmonics | orthogonal but spends df; tide already flagged | tidal peak asymmetry | small, control |
| B1 convergence/strain/Okubo-Weiss | `k_tide` (temporal part) | spatial fronts (unresolvable at 4 pts) | ~0 at our N |
| C1 SST-front |grad SST| | `k_season` (mean SST); use gradient | front gradient is genuinely independent | small-to-moderate |
| D1 lagged run ANOMALY | `k_season` (run is seasonal); use anomaly | year/within-season run anomaly | potentially highest (feed-gated) |
| D2 prey x tide | A1 + D1 mains | favorable-window prey effect | small |
| D3 prey x space | s_space side blocked at 4 pts | none on the acoustic gate | ~0 |
| E1-E5 terrain (slope/aspect/channel/BPI/rugosity) | depth + station fixed effect | s_space habitat structure only | ~0 on gate; GO for s_space |
| F1 lunar x diel | `k_lunar`, `k_diel` mains | nocturnal illumination effect; de-aliases lunar | small, clean |
| F2 tide x diel | tide+diel mains | nocturnal tidal foraging | small |
| F3 diel x season | both mains; season often withheld | seasonal diel shift | small, high risk |
| F4 station x tide | station effect + k_tide | per-station tidal heterogeneity | overfits as fixed; defer to M1 |

The structural theme: most "derived" features are deterministic functions of covariates already in
the additive model, so they re-express existing columns and the 5-fold CV will not credit them. Only
three carry information independent of the current covariate set: D1 (a real run ANOMALY, feed-gated),
C1 (an SST front gradient, S2-gated), and F1 (a lunar x diel illumination interaction, in-repo). The
spatial families (B, E, D3) are blocked not by a missing recipe but by the 4-clustered-station data
geometry, which is an S1 node-density problem, not an M3 feature problem.

## 3. Ranked GO / NO-GO for prototyping

Ranked by EXPECTED held-out, fold-stable CV-skill contribution toward +0.144, with cost and the B.2
role. Nothing here promotes; each "GO" is a prototype recommendation for the synthesis to sequence,
scored later on SERVED data under the G2 gate.

1. GO (conditional on a real feed; highest potential) -- D1 lagged stock-aligned run ANOMALY
   (effect-modifier). Construct the run as an anomaly vs its day-of-year climatology to break the
   season collinearity, use the pre-registered out-of-sample lag, fit jointly with `k_season`.
   BLOCKER: needs a real Albion (Fraser-summer Chinook) feed; on the climatology placeholder it is
   WITHHELD (B.3) and contributes 0. Feed/S2 dependency. This is the same lever the campaign already
   names for L3, so M3's recommendation is to prioritize grounding the feed over engineering more
   transforms of existing covariates.
2. GO (conditional on S2 SST feed; best of the field-sourced items) -- C1 SST-front strength
   |grad SST| (effect-modifier), orthogonalized against `k_season`. Genuinely independent physical
   driver; damped by the station geometry but the temporal front evolution near the cluster is usable.
   S2 dependency: MUR SST (or equivalent).
3. GO (cheap, in-repo, bounded) -- F1 lunar x diel nocturnal-illumination interaction
   (effect-modifier). Physically clean, low df cost, can de-alias lunar from season. No dependency.
4. GO (cheap, in-repo, bounded; treat as a pair with its control) -- A1 distance-to-slack/max-flow
   (effect-modifier), reported jointly with `k_tide` and against the A3 "+1 harmonic" control so the
   marginal skill is honest. No dependency. Low expected gain; run only because it is nearly free.
5. GO for s_space quality, NO-GO on the gate -- E1/E3/E4 terrain (slope, channel proximity, BPI) from
   CUDEM (VALIDATION-ONLY / s_space). Improves the spatial habitat product but does not move the
   served acoustic CV-skill bar; do not credit it there. Build dependency: wire CUDEM into modeling
   (today only ETOPO1 1 arc-min).
6. NO-GO at current data -- A2 |V| flow-strength envelope (collinear with tide + lunar) and F2/F3
   interactions (tide x diel, diel x season): overfitting-prone, little independent content; revisit
   only if N grows or after the GO items.
7. NO-GO at current data -- B1 convergence/strain/Okubo-Weiss fronts and D3 prey x space: the
   spatial leverage that would justify them does not exist at 4 clustered fixed stations, and they sit
   behind an S2-gated gridded-current feed. This is an S1 (node density) blocker, not an M3 recipe gap.
8. DEFER to M1 -- F4 station x tide: the honest treatment is a partial-pooled (hierarchical) station
   random effect, which is M1's sparse-data modeling territory, not a derived covariate.

## 4. Honest bottom line

The +0.078 -> +0.144 gap is unlikely to be closed by transforming covariates the additive NB2 model
already carries: A-family, F2/F3, and the temporal part of B are collinear by construction, and E/B/D3
are spatial covariates measured at four clustered points that cannot resolve space. The genuinely
independent signal lives in (D1) a REAL stock-aligned salmon run anomaly and (C1) an SST-front
gradient, both source-gated, plus a small, clean, in-repo (F1) lunar x diel interaction. The most
honest M3 recommendation to the synthesis is therefore: prioritize SOURCING the real Albion feed and
an SST product (an S2/S1 dependency) over engineering further deterministic transforms of the existing
covariates, and run F1 and A1 as the cheap in-repo bounded prototypes that test whether any squeezed
nonlinearity survives the 5-fold CV. Everything stays WITHHELD until scored on SERVED data under the
G2 gate with a recorded supervisor decision (B.1).

## Return summary

- Doc path: `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/M3_derived_covariates.md`.
- Derived-covariate list with recipes: A1 distance-to-slack/max-flow; A2 |V| flow strength +
  spring-neap envelope; A3 raise k_tide harmonics (control); B1 convergence/strain/Okubo-Weiss fronts;
  C1 SST-front |grad SST|; D1 lagged stock-aligned run ANOMALY; D2 prey x tide; D3 prey x space;
  E1-E5 CUDEM terrain (slope/aspect/channel/BPI/rugosity); F1 lunar x diel; F2 tide x diel;
  F3 diel x season; F4 station x tide. Recipes are in section 1.
- Per-item B.2 role + collinearity: A1/A2/A3/C1/D1/D2/F1/F2/F3/F4 are (b) effect-modifiers estimated
  from effort-stable ACOUSTIC detections with the `log E` offset; E1-E5 and D3 are (c) validation-only
  / `s_space` (static spatial, validated on visual, not the temporal gate). Collinearity matrix in
  section 2: A1/A2/A3 with `k_tide` (A2 also with `k_lunar` via spring-neap); C1 and D1 with
  `k_season` (use the gradient / the anomaly to break it); B1 temporal with `k_tide`; E1-E5 with depth
  and a 4-level station intercept; F1/F2/F3 with their mains.
- S2 / feed dependencies flagged (S2 doc absent at start): C1 needs an SST feed (MUR/VIIRS);
  B1/D3 need a gridded surface-current field (SalishSeaCast ROMS / HF radar); D1/D2/D3 need a REAL
  stock-aligned Albion feed (climatology => WITHHELD); E-family needs CUDEM wired into the modeling
  tree (today only ETOPO1 1 arc-min). A-family and F1/F2/F3 use only in-repo signals.
- Ranked go/no-go (section 3): (1) GO conditional D1 run anomaly [feed-gated, highest potential];
  (2) GO conditional C1 SST front [S2-gated]; (3) GO cheap F1 lunar x diel; (4) GO cheap A1
  slack/max-flow with the A3 control; (5) GO for s_space only / NO-GO on the gate E terrain;
  (6) NO-GO A2, F2, F3; (7) NO-GO B1, D3 [4-clustered-station geometry + S2 feed]; (8) DEFER F4 to M1.
- No fit run, no production/model-bucket write, no promotion, nothing committed. Effective confidence
  stays 0.0.
