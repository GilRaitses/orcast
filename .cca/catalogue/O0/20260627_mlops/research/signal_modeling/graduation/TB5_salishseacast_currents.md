# TB5 -- SalishSeaCast subtidal currents + shear/convergence (the M3-B1 front covariate)

Agent: TB5, graduation waveset (Wave TB), forecast ML-ops. Date: 2026-06-27 (America/New_York).
Repo: `/Users/gilraitses/orcast`. Home: this doc only; no other file edited.
Authority: `20260627_mlops-handoff/HANDOFF_CHARTER.md` section B; `20260627_signal-modeling-launch-handoff/HANDOFF_CHARTER.md` section B (B.2 covariate-role honesty);
`GRADUATION_WAVESET_CHARTER.md` (sections 1, 3); `GRADUATION_DISPATCH.md` (RECALIBRATION FROM DE [BINDING] + the TB5 lane).
Scope: investigation + recipe spec + patch-spec only. No production write, no convergence-file edit,
no fetch-that-writes, no fit-that-writes, no deploy, no promotion, no commit. Effective confidence 0.0.

## 0. Rails + the bar this lane is judged against

- B.1 honesty / promotion gate. Nothing here promotes. A covariate earns confidence only later via a
  passing gate on SERVED data plus a recorded supervisor decision. Effective confidence stays 0.0.
- The bar (G2): served 4-station fit = held-out CV mean-deviance-skill +0.078 -> confidence 0.49
  (HOLD). Crossing 0.6 needs served skill ~+0.144 AND fold-stable (>=4/5 folds individually positive,
  across-fold lower bound >= +0.078, PIT calibrated, L1 null beaten). Judge by fold-stable held-out
  `block_cv` skill, never in-sample fit. Effective independent N is ~300 encounter onsets pooled.
- B.2 covariate-role honesty (load-bearing for this lane). Raw current speed is collinear with
  `k_tide`; it is NOT admissible as a kernel. Only the SUBTIDAL residual + shear/convergence/
  Okubo-Weiss is admissible, and only as an (b) effect-modifier estimated from effort-stable acoustic
  detections with the `log E` offset. The current series already in the repo feeds the harmonic
  `k_tide` phase ONLY (`fit_kernels.py` lines ~601-622); SalishSeaCast must NOT be laundered into a
  second tidal term, and a hydrophone detection is a fixed-position presence event, not a whale fix.
- DRIFT-GUARD (binding, GRADUATION_DISPATCH RECALIBRATION FROM DE). HF-radar currents are NO-GO
  in-region (radar shadow in the inland archipelago); SalishSeaCast is the only admissible in-region
  current source. The spatial-front leverage is damped until presence is spatially resolved, so this
  lane is CONDITIONAL on TB1/TB4 adding spatially separated nodes. This doc is honest about that.

Hydration (read in full): GRADUATION_DISPATCH.md, GRADUATION_WAVESET_CHARTER.md, both HANDOFF_CHARTER
section B docs, SYNTHESIS_signal_modeling.md, S2_covariate_sources.md (rank 3 + section 2 collinearity),
M3_derived_covariates.md (category B / B1), FORECAST_KERNELS.md, and the relevant code:
`modeling/design.py` (the design table builder), `modeling/fit_kernels.py` (CYCLIC set, `fit_glm`,
`_station_intensity_fn`, `block_cv`, `write_outputs`, `_maybe_write_s3`), `modeling/tide_harmonic.py`
(the in-repo least-squares harmonic predictor I reuse for de-tiding), `modeling/studies/common.py`
(`STATION_COORDS`), and DE1/DE2 registers (currents rows #9/#10 and L6/G6).

## 1. Source provenance + license

Provenance below is from S2 (the W9-S2 covariate catalog, Group P); NOT independently re-fetched here.
No griddap query was run. Numbers I could not verify without a fetch are marked NOT-MEASURED.

| Field | Value |
|---|---|
| Model | SalishSeaCast NEMO v21-11, UBC Mesoscale Ocean and Atmospheric Dynamics (MOAD) group |
| Access | ERDDAP griddap (UBC/MOAD ERDDAP server) |
| Primary dataset (3D, depth-resolved u,v) | `ubcSSg3DPhysicsFields1hV21-11` |
| Alternate dataset (depth-averaged currents) | `ubcSSfDepthAvgdCurrents1h` |
| Grid resolution | ~500 m (NEMO Salish Sea grid) |
| Temporal resolution | hourly |
| Span | hindcast 2007+; near-real-time since 2024-01 (per S2) |
| In region? | YES (Strait of Georgia + Juan de Fuca + Gulf/San Juan Islands; covers all 4 stations) |
| License | open (ERDDAP, Apache-like per S2); UBC/MOAD attribution expected. CONFIRM exact license + citation text at fetch time (NOT-MEASURED here). |
| Grid orientation caveat | NEMO velocities are on a staggered (Arakawa-C-like) curvilinear grid with grid-relative u,v; ERDDAP griddap commonly serves regridded geographic u,v, but the staggering / rotation MUST be confirmed before computing spatial derivatives (NOT-MEASURED). |
| Reachability caveat | UBC/MOAD ERDDAP reachability from the dev host/region is NOT-MEASURED; if blocked, route via the aimez EC2 `i-04a649f91274e9fce` (B.9), exactly like the DFO recipe. No fetch was run. |

Why SalishSeaCast and not HF radar (restated, binding): the inland San Juan / Gulf Island channels are
radar-shadowed (S2 section 3 #8; DE1 row #10), so HFRNet/HF radar is NO-GO in-region. SalishSeaCast is
a gridded model field with full in-region coverage and is the only admissible current source here. It
is a MODELED field, not observed current; honest as a covariate, not presented as measurement.

## 2. The de-tided residual + shear/convergence recipe

The deliverable of this section is a deterministic offline construction (no fit, no write) that turns
the raw hourly velocity field into the admissible covariates. Five steps.

### 2.1 Pull the surface velocity field (offline, dry-run only)

- Query `ubcSSg3DPhysicsFields1hV21-11` for the top model level (surface) over the station-cluster
  bounding box (~48.4-48.8 N, -123.3 to -122.7 W; the SAN_JUAN core plus a halo wide enough to compute
  derivatives at the edge cells) and the acoustic detection window (the served fit's data window).
  Variables: eastward `u` and northward `v` (confirm exact var names at fetch; NOT-MEASURED). Use
  `ubcSSfDepthAvgdCurrents1h` (depth-averaged) as the lighter alternate if the 3D field is too heavy or
  if surface-only is judged unrepresentative of the foraging layer; record which one was used.
- Keep the query BOUNDED: one box, one surface level, hourly, the acoustic window only. This avoids the
  resource-exhaustion failure mode. The full 3D archive is large; do not pull it.
- This is a DRY-RUN spec. No fetch-that-writes; if executed it writes only to an isolated scratch dir,
  never `data/models/` or any served artifact.

### 2.2 Remove the tidal band (the admissibility step)

Raw `u(x,y,t), v(x,y,t)` are tidal-band dominated and collinear with `k_tide`. Two admissible de-tiding
methods; the recipe specifies the harmonic method as primary (reuses in-repo machinery) and the
low-pass filter as the cross-check.

(a) Harmonic subtraction (primary; reuses `modeling/tide_harmonic.py`). For each grid cell and each
   velocity component, fit `HarmonicTide` (fixed constituents M2/S2/N2/K1/O1 + mean) by least squares
   to the hourly series, then form the residual `u_sub = u - HarmonicTide.predict(t)` (same for `v`).
   The fitted harmonic is the tidal band; the residual is the subtidal flow. Record per-cell
   `reconstruction_r2`; a high R^2 (tide explains most variance) is expected and is the evidence the
   residual is genuinely subtidal. This reuses code already trusted for `k_tide`, so the de-tiding is
   consistent with how the model already defines the tidal band.
   - Honest limit: 5 constituents capture the dominant semidiurnal/diurnal band but not the full
     spring-neap envelope or shallow-water overtides (M4/M6). Residual leakage of the fortnightly beat
     is possible and is itself collinear with `k_lunar`; flag it (see 2.5).

(b) Low-pass / tidal filter (cross-check). Apply a Godin filter (24h-24h-25h moving average) or a
   33-hour Lanczos low-pass to `u, v` per cell; the low-pass output is the subtidal flow, the
   complement is the tidal band. Compare `u_sub` from (a) vs (b); they should agree to within the
   overtide/residual band. Disagreement flags constituent mis-fit. Use (b) as the reported residual if
   the harmonic R^2 is poor at a cell (mirrors the `fit_kernels` policy of refusing a bad harmonic fit
   and falling back).

The output of 2.2 is the subtidal velocity field `(u_sub, v_sub)(x,y,t)` on the ~500 m grid.

### 2.3 Compute shear / convergence / Okubo-Weiss from the subtidal field

On the de-tided field, compute the horizontal velocity-gradient tensor by centered finite differences
on the grid (respect the ~500 m spacing in metres; confirm grid geometry / any rotation first, 2.1):

- Convergence: `C = -(du_sub/dx + dv_sub/dy)` (positive C = convergent / frontogenetic).
- Normal strain: `S_n = du_sub/dx - dv_sub/dy`; shear strain: `S_s = dv_sub/dx + du_sub/dy`.
- Total strain rate: `S = sqrt(S_n^2 + S_s^2)`.
- Relative vorticity: `omega = dv_sub/dx - du_sub/dy`.
- Okubo-Weiss: `W = S^2 - omega^2` (W > 0 strain/front-dominated; W < 0 eddy-core-dominated).

These separate frontal/strain cells (where prey concentrates) from rotation-dominated cells. Convergence
`C` is the physically primary "front" variable per M3-B1; `S` and `W` are the discriminants. All are
computed on the SUBTIDAL field, so they carry the subtidal frontal structure, not the tidal pulse.

### 2.4 Sample at the station footprints

- For each station in `STATION_COORDS` (`modeling/studies/common.py`): orcasound_lab (48.558, -123.174),
  andrews_bay (48.550, -123.167), north_san_juan_channel (48.591, -123.059), haro_strait
  (48.516, -123.152), bilinearly interpolate `C, S, W` (and `|u_sub|`) from the grid to the station
  coordinate at each hourly step. Optionally average over a small footprint radius (e.g. the nearest
  few cells, ~1-2 km) to represent the acoustic detection volume rather than a single point; record the
  radius used.
- Reduce to the design bin width (`bin_hours`, default 1.0, so it is already hourly): align each
  station-bin centre `t` (the `t` column `build_design` emits) to the field timestamp and attach the
  sampled `C, S, W` as new design columns (e.g. `subtidal_conv`, `subtidal_strain`, `okubo_weiss`).
- Standardize each column (mean-zero, unit-variance over the fit window) so it enters as a clean
  aperiodic covariate; record the scaling so serving can reproduce it.

### 2.5 Admissibility / collinearity guard (the load-bearing check)

Before any scoring, verify the residual is actually independent of the existing kernels, because a
mis-de-tided column would just re-express `k_tide`/`k_lunar` and the CV would (correctly) refuse it:

- Regress each candidate column (`subtidal_conv` etc.) on the existing design columns
  (`k_tide` Fourier columns, `k_lunar`, `k_diel`, `k_season`) and report R^2. A high R^2 means the
  "subtidal" residual still carries tidal/fortnightly leakage and is NOT admissible; withhold it
  (B.3) rather than fit a laundered tide term. NOT-MEASURED here (needs the fetch + de-tide run).
- Report the residual fraction of variance the subtidal field carries vs the raw field per cell; a
  vanishingly small subtidal fraction at the station cells would itself be a NO-GO (nothing
  independent to add). NOT-MEASURED.

## 3. B.2 role + collinearity (honest classing)

| Covariate | B.2 role | Honest reason | Collinearity |
|---|---|---|---|
| `subtidal_conv` (-div u_sub) | (b) effect-modifier | subtidal convergence fronts concentrate prey; documented SRKW foraging cue (M3-B1) | TEMPORAL part at a fixed station is still partly tidally driven; de-tiding removes the dominant band but the SPATIAL signal (how convergence differs across cells) is where independence lives, and that is exactly what 4 clustered point sensors cannot resolve |
| `subtidal_strain` (S) | (b) effect-modifier | strain-rate discriminates frontal vs eddy cells | with `subtidal_conv` and `okubo_weiss` (all derived from the same gradient tensor) |
| `okubo_weiss` (W) | (b) effect-modifier | separates front/strain from eddy cores | with the two above |
| raw `|u|` current speed | NOT admissible as a kernel | collinear with `k_tide` (S2 section 2) | high with `k_tide`; excluded by B.2 |

The single load-bearing collinearity (M3 section 0.2, B1 verdict): the independent leverage of a front
covariate is SPATIAL (the front is somewhere; presence is higher near it). The 4 served stations sit in
one ~8 x 9 km cluster, so the field is nearly constant across them and the spatial dimension that would
make fronts pay off is not observed. What remains is the temporal evolution of front strength near the
cluster, which is weak and partly tidal. This is why M3 rates B1 NEAR ZERO at current N and SYN places
B5 as conditional.

## 4. Conditional-payoff assessment (HONEST; depends on more nodes)

The payoff of this covariate is gated on the data GEOMETRY, not on the recipe. The recipe above is
sound and bounded; the question is whether it can move the fold-stable held-out CV-skill toward +0.144.

- At the CURRENT 4-clustered-station geometry: expected marginal fold-stable held-out contribution is
  NEAR ZERO, plausibly negative once the column competes with `k_tide`/`k_lunar` in CV (a residual that
  still leaks tidal/fortnightly variance is the failure mode). M3-B1 verdict: "NEAR ZERO at current
  data ... the spatial leverage that would make fronts pay off does not exist with 4 clustered point
  sensors." This lane does NOT claim a skill number; any number would be fabricated. NOT-MEASURED.
- The leverage UNLOCKS only when presence is spatially resolved, i.e. when TB1 (Port Townsend + Bush
  Point, Admiralty Inlet corridor) and/or TB4 (ONC/JASCO Boundary Pass) add stations that are
  GEOGRAPHICALLY SEPARATED from the San Juan cluster and from each other. With separated nodes, the
  convergence field DOES vary across stations, and a front covariate can express "this node is near a
  subtidal front today, that one is not" -- the spatial contrast the cluster cannot show. So the
  conditional payoff is: damped/near-zero now; becomes testable (and potentially small-positive) once
  TB1/TB4 nodes land and are spatially separated.
- Even conditional on more nodes, the honest expected band is SMALL. Subtidal fronts are a second-order
  cue relative to the new presence-days themselves (B1) and the prey/SST signals (B2/B3); B5 "pairs
  with more nodes" (SYN Tier B) as a refinement, not a primary +0.144 lever. Do not sequence B5 ahead
  of the node grounding it depends on.
- Engineering cost is real and higher than the in-repo covariates: a new ERDDAP adapter, the de-tide
  step per cell, the gradient computation, footprint sampling, and the collinearity guard. The cost is
  justified ONLY after the nodes that give it spatial leverage exist.

## 5. GO / NO-GO

NO-GO at current N (4 clustered stations). The recipe is correct and the source is the right one, but
the spatial leverage that would make subtidal fronts pay off does not exist at the current geometry,
and the temporal residue is collinear with tide/lunar. Scoring it now would, at best, measure ~0 and at
worst launder leaked tidal variance.

CONDITIONAL GO, deferred: revisit as a refinement covariate AFTER TB1 and/or TB4 add spatially
separated nodes, AND only after the de-tided residual passes the 2.5 admissibility/collinearity guard,
AND only if it shows fold-stable marginal held-out skill in `block_cv` against a baseline that already
includes `k_tide`/`k_lunar` (so a gain is not just leaked tide). Sequence STRICTLY after B1/B4 per SYN.

This matches S2 rank 3 (GO-conditional, ranked below SST for engineering effort) and M3-B1 (NO-GO at
our N, spatial-geometry-blocked, S2-feed-gated) without contradiction.

## 6. PATCH-SPEC (for the later single-editor, operator-gated integrate)

Do NOT apply now. This is the spec for the separate single-editor integrate step. It is gated behind
TB1/TB4 node grounding (section 4); integrating it before then wires a covariate that cannot pay off.

Files the integrate would touch (all convergence files; single-editor only):

1. NEW `src/aws_backend/sources/salishseacast.py` (new source adapter, mirrors the existing source
   pattern): an ERDDAP griddap client that pulls `ubcSSg3DPhysicsFields1hV21-11` (surface) or
   `ubcSSfDepthAvgdCurrents1h` over the station bbox + window, returns hourly `(u, v)` grids. Pure read;
   no write to the served store. Register it so DE2's "block in source registry if added later" note
   (G12) is satisfied with an explicit, documented entry rather than a silent dead-end-adjacent feed.

2. NEW `modeling/subtidal_currents.py` (offline derive module, local-only modeling tree per B.7):
   implements 2.2 (harmonic de-tide via `tide_harmonic.HarmonicTide` + Godin/Lanczos cross-check),
   2.3 (gradient tensor -> `C, S, W`), 2.4 (footprint sampling to station-hour), 2.5 (collinearity
   guard). Returns a per-(station, t) frame of `subtidal_conv, subtidal_strain, okubo_weiss`.

3. `modeling/design.py` `build_design`: add optional `subtidal_by_station` input (default None ->
   strict no-op, columns NaN/absent, exactly like the `tide_phase=None` pattern) and emit the three
   standardized columns alongside the existing `diel/tide/lunar/season`. Must remain a no-op when the
   feed is absent so the current served fit is unchanged.

4. `modeling/fit_kernels.py`: the subtidal columns are APERIODIC (not cyclic), so they do NOT join
   `CYCLIC = ("diel","tide","lunar","season")` and must NOT be added as a Fourier kernel. Enter them
   as aperiodic linear/smooth terms in `fit_glm` (the same class as `k_salmon`/`s_space`, i.e. handled
   outside the cyclic Fourier path), include them in `_select_covariates` with a coverage/finite guard,
   and ensure `_station_intensity_fn` adds the corresponding term to `log_rate` ONLY when the column is
   present. Keep raw `|u|` OUT entirely (B.2). Preserve `write_outputs=False` / `_maybe_write_s3 =
   lambda: None` discipline for any prototype fit; never touch `data/models/fit_report.json`.

5. Scoring: a study module (analogous to `modeling/studies/salmon_lag.py`) that runs the 2.5
   collinearity guard, then `block_cv` with the subtidal columns added to the existing covariate set,
   and reports per-fold held-out CV mean-deviance-skill + across-fold lower bound + PIT + the MARGINAL
   skill vs a baseline WITHOUT the subtidal columns. WITHHELD (no `k`-credit) unless it shows
   fold-stable marginal skill against that baseline. Writes only to `modeling/studies/reports/`.

6. Honesty/disclosure: the served fit report must disclose subtidal-current columns as a MODELED
   (SalishSeaCast) covariate, not observed current, and as effect-modifier (not a second tide term).

Integration order (binding): TB1/TB4 node grounding -> re-fit baseline with new nodes -> THEN add the
subtidal columns and read their MARGINAL fold-stable skill. Never integrate B5 before the nodes.

### 6.1 DE drift note (carry forward to the integrate)

This patch-spec's documentation touches text DE flagged. Append, at integrate time:

- DE1 row #9 (`wave_shape.yml` `signal_modeling_research.objectives.M3_derived`, ~L314): when this
  covariate is recorded there, append "subtidal currents = SalishSeaCast residual only; HF radar
  shadowed/NO-GO in-region (S2 section 3 #8)." (Supersession caveat, DE1 register.)
- DE1 row #10 (`M3_derived_covariates.md` section 0.3, ~L95-96): strike HF radar as a peer current
  candidate; "SalishSeaCast only; HF radar NO-GO in-region."
- DE2 row L6 (`fit_kernels.py:601-622`): preserve the established fact that NOAA currents enter as the
  `k_tide` PHASE driver only; the SalishSeaCast subtidal field is a SEPARATE effect-modifier column and
  must not be merged into or mistaken for the tidal term. (Confirms the dead-end is not revived.)

## 7. Return summary

- Doc path: `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/graduation/TB5_salishseacast_currents.md`.
- Recipe: pull SalishSeaCast NEMO v21-11 surface velocity (ERDDAP griddap
  `ubcSSg3DPhysicsFields1hV21-11` / `ubcSSfDepthAvgdCurrents1h`, ~500 m hourly, in-region); remove the
  tidal band by harmonic subtraction (reusing `modeling/tide_harmonic.py`) with a Godin/Lanczos
  low-pass cross-check; compute convergence `-div u_sub`, strain rate, and Okubo-Weiss on the subtidal
  field; bilinearly sample to the four station footprints; standardize; and run a collinearity guard
  before any scoring.
- Provenance/license: SalishSeaCast NEMO v21-11 (UBC/MOAD), ERDDAP griddap, ~500 m, hourly, 2007+ /
  near-real-time since 2024-01, in-region YES, open license (Apache-like per S2; exact citation/license
  + grid rotation + reachability CONFIRM at fetch, NOT-MEASURED). HF radar NO-GO in-region (shadow).
- B.2 role: subtidal residual + shear/convergence/Okubo-Weiss = (b) effect-modifier; raw current speed
  NOT admissible (collinear with `k_tide`); never laundered into a whale fix or a second tide term.
- Conditional-payoff verdict: DAMPED / NEAR ZERO (plausibly negative) at the current 4-clustered-station
  geometry; the spatial-front leverage is unobservable until TB1/TB4 add spatially separated nodes.
  Even then the honest expected band is SMALL (a refinement, not a primary +0.144 lever). No skill
  number is claimed (NOT-MEASURED; claiming one would be fabrication).
- GO/NO-GO: NO-GO at current N; CONDITIONAL GO deferred behind TB1/TB4 node grounding + the
  admissibility/collinearity guard + fold-stable marginal held-out skill vs a `k_tide`/`k_lunar`
  baseline.
- PATCH-SPEC delivered (section 6) for the later single-editor integrate, with a DE drift note (6.1).
- Confirmation: nothing deployed, fetched-to-write, ingested, promoted, or committed; no convergence
  file edited; no fit run; only this one doc written. Effective confidence stays 0.0.
