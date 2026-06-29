# TA3 graduate: AIS-derived effort/noise term in `log E`

Agent: TA3 deep subagent, graduation waveset (Wave TA, "extract from existing data: model + effort").
Date: 2026-06-27 (America/New_York). Repo: `/Users/gilraitses/orcast`. This findings doc is the ONLY
file written. No convergence-file edit, no served write, no fetch-that-writes, no deploy, no promotion,
no commit (B.1/B.5/B.6/B.10). Effective confidence stays 0.0.

Authority/hydration read in full first: `GRADUATION_DISPATCH.md` (Shared context, the binding
"RECALIBRATION FROM DE" block, "Fit safety", lane TA3); `GRADUATION_WAVESET_CHARTER.md` sections 1-2;
`20260627_mlops-handoff/HANDOFF_CHARTER.md` section B (esp. B.2 covariate-role honesty);
`SYNTHESIS_signal_modeling.md` + `research/signal_modeling/S2_covariate_sources.md` (rank 1, the
effort/exposure classing); `docs/methodology/FORECAST_KERNELS.md` (the effort-bias / `log E` principle);
`research/forward/G2_promotion_protocol.md` (the +0.144 bar, fold-stability definition).

## 0. The one binding rail this lane obeys (B.2, restated)

AIS vessel traffic / ambient noise is an **EFFORT / EXPOSURE** term. Vessel noise masks SRKW calls and
**lowers detection probability**, so it belongs in `log E`, NOT in a presence kernel. It must NOT be
laundered into presence. A secondary "vessels disturb whales" effect-modifier story exists in the
literature, but at our N it is confounded with detectability and would launder a detector artifact into
biology, so this lane classes it strictly as effort (S2 section 0.2 / 2 / rank 1; SYN A3). Everything
below keeps it as a multiplicative detectability factor on the existing exposure offset, with zero added
presence parameters.

## 1. Baseline (MEASURED) the AIS delta would be scored against

Reproduced the served 4-station experiment under the CURRENT code, in `.venv-modeling`, with
`ORCAST_STORAGE_BACKEND=aws ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads AWS_REGION=us-west-2`,
`fk._maybe_write_s3 = lambda: None`, `run_fit(write_outputs=False, make_figures=False)`. Same
mixed-provenance memory store as `modeling/studies/level2_multistation.py` (production `haro_strait`
stream + cached OrcaHello index for the other three nodes). No store/artifact written.

| Quantity | Measured value |
|---|---|
| Held-out CV mean-deviance-skill | **+0.0778** |
| Per-fold skills (5 time blocks) | [-0.0381, +0.0648, +0.1401, +0.0662, +0.1559] |
| Folds individually positive | **4/5** |
| Across-fold one-sided 95% lower bound (mean - t*SE) | **+0.0044** |
| Held-out NB PIT | calibrated (KS p = 0.364) |
| P0-map confidence | 0.49 (HOLD) |
| Covariates fit | diel, tide, lunar, season |
| Level-1 beats-null (modulation) | diel 0.52 yes; lunar 0.95 yes; season 0.92 yes; tide 0.386 **no** |
| Time-rescaling verdict | withheld (neither event nor encounter level passes) |
| `effort_assumed_continuous` | **True (log E is FLAT today)** |
| n detections / n station-bins | 2089 / 66899 |

Two facts here are load-bearing for this lane:

1. **`log E` is currently flat.** No `station_uptime` series binds any station's detection window
   (`level2_multistation` already records `effort_assumed_continuous=True`), so the exposure offset is a
   constant within each station and carries no temporal structure at all. An AIS detectability term would
   be the *first* real structure in `log E`. That is the headroom S2 rank 1 is pointing at.
2. **The baseline is fold-fragile.** Fold 1 is negative (-0.038) and the across-fold lower bound is only
   +0.0044, far under the +0.078 robustness floor G2 requires for promotion. So the honest target for an
   effort term is not just the mean: it is *fold stability* (does it lift the negative fold and tighten
   the lower bound) as much as the mean skill.

## 2. AIS delta: NOT-MEASURED (real fetch infeasible in this bounded environment)

Per the dispatch ("If the AIS fetch or fit is infeasible, deliver the sourcing recipe + construction +
expected band and mark numbers NOT-MEASURED; do not fabricate"), the measured skill delta from a cleaner
`log E` is **NOT-MEASURED**. The reasons are concrete, not hand-waved:

- **Network blocked here.** The in-repo PMEL/CoastWatch ERDDAP path used by `src/aws_backend/sources/ais.py`
  (`https://coastwatch.pfeg.noaa.gov/erddap/tabledap/AIS2023_WestCoast.csv`) returns
  `curl: (35) Recv failure: Connection reset by peer` from this host. Probed directly; not reachable.
- **AccessAIS clip-and-ship is asynchronous.** `marinecadastre.gov/accessais` is an order-and-deliver
  workflow (area + date range -> queued job -> emailed download link), not a synchronous API, so it cannot
  complete inside a bounded subagent turn.
- **Bulk is multi-GB and multi-year.** The detection windows span **2020-09-28 -> 2021-05-09**
  (`haro_strait`) and out to **2026-06-16** for the cached Orcasound nodes. Covering all 66,899
  station-bins needs AIS for the cluster across ~2020-2026. The Marine Cadastre annual zipped CSV / GeoParquet
  products are tens-to-hundreds of MB per zone per day; multi-year over the region is far past the
  "keep work bounded to avoid resource exhaustion" rail.
- **Recent-year publication lag.** Marine Cadastre annual AIS products typically lag ~1 year, so the
  2025-2026 tail of the multi-station detection window likely has **no published AIS yet** (the in-repo
  adapter only references `AIS2023_WestCoast`). That part of the offset would be unavoidably missing.

Fabricating an AIS index and reporting a "delta" off it would violate B.3 (withhold over fake) and the
dispatch's "do not fabricate". So the delta is withheld with the construction + an honest expected band
below, exactly as the lane permits.

## 3. Source + provenance + license

Primary source (per dispatch): **NOAA Marine Cadastre AIS** (US NAIS, collected by the U.S. Coast Guard;
distributed by NOAA Office for Coastal Management / BOEM).

| Aspect | Detail |
|---|---|
| Access A (clip-and-ship) | `marinecadastre.gov/accessais`: draw the San Juan bbox (`SAN_JUAN_BOUNDS` = 48.40-48.70 N, -123.25 to -122.75 W; widen to ~48.35-48.85 N, -123.45 to -122.55 W to capture the Haro Strait lane and approach geometry), pick the date range, receive decimated (1-min) point CSV by email. |
| Access B (bulk) | Annual zipped CSV historically at `coast.noaa.gov/htdata/CMSP/AISDataHandler/<year>/`; cloud-native **GeoParquet** on the AWS Registry of Open Data / Marine Cadastre cloud bucket (partitioned by date), readable with pyarrow/duckdb with a pushed-down bbox+time predicate. Preferred for batch. |
| Access C (in-repo, lightweight) | `src/aws_backend/sources/ais.py` already wraps the PMEL/CoastWatch ERDDAP `AIS<year>_WestCoast` tabledap with a `SAN_JUAN_BOUNDS` filter; good for bounded windows, but only `AIS2023` is wired and the endpoint was unreachable from this host. |
| Fields | MMSI, BaseDateTime, LAT, LON, SOG (speed-over-ground), COG, Heading, VesselName, IMO, CallSign, VesselType, Status, Length, Width, Draft, Cargo. |
| Cadence / span | ~1-min decimated positions; 2009 -> present; US waters. |
| License | U.S. Government work, **public domain / open** (no use restriction). Cite "NOAA Office for Coastal Management / BOEM / USCG, Marine Cadastre AIS." |

### The BC-side coverage gap (must be documented on the index)

The dominant masking source for these four stations is the **Haro Strait commercial shipping lane**, which
runs along the Canada/US international boundary, 2-5 km off the west San Juan shore where `haro_strait`,
`orcasound_lab`, and `andrews_bay` sit. Marine Cadastre carries **US-side NAIS only**. Coverage near the
boundary is partial-but-useful (US terrestrial receivers on the San Juans pick up most VHF-range
boundary traffic, ~40-60 km), but vessels purely in Canadian waters (Strait of Georgia / Vancouver
approaches) are under-represented. Net effect: the proximity-noise index is a **lower bound** on true
masking, biased toward US-side completeness. Closing the gap needs a Canadian AIS source (Spire / former
exactEarth commercial, ONC/MEOPAR, or CCG), which is out of scope for this open feed and flagged for the
operator. The index spec below carries a `coverage = "us_side_partial"` flag so the bias is never hidden.

## 4. Per-station, per-time-bin proximity-noise index (construction)

Two construction variants, both producing a per-(station, hour-bin) detectability fraction
`D_ais(s, b) in (0, 1]` (1 = no masking, smaller = more masking). Variant A is the recommended default
(fewer unvalidated assumptions); variant B is the richer acoustic model if a calibrated source level is
wanted later.

**Inputs.** AIS point reports `{MMSI, t, lat, lon, SOG, Length, VesselType}` clipped to the widened bbox
and the detection span. Station coordinates (from `modeling/studies/common.py` `STATION_COORDS`):
`haro_strait` (48.516, -123.152), `orcasound_lab` (48.5583, -123.1736), `andrews_bay` (48.5500, -123.1666),
`north_san_juan_channel` (48.5913, -123.0588).

### Variant A: distance-weighted vessel-proximity index (default)

1. For each AIS report of vessel v at time t, compute great-circle range `r(v, s, t)` to station s
   (haversine; floor at `r0 = 0.2 km` to avoid a singularity).
2. Optional per-vessel weight `m_v` for masking potential: `m_v = (SOG/SOG0) * (Length/L0)` clipped to
   `[0.25, 4]` (faster, larger vessels are louder); set `m_v = 1` if attributes missing. Default off
   (set all `m_v = 1`) until validated, so the index is a pure proximity-presence proxy.
3. Per-bin proximity load: `I(s, b) = sum over reports in bin b of  m_v / max(r(v,s,t), r0)^2`
   (inverse-square is the conservative spherical-spreading proxy; a `1/r^1.5` cylindrical-channel variant
   is reported as a sensitivity).
4. Map load to detectability: `D_ais(s, b) = exp(-kappa * I_norm(s, b))`, where `I_norm` is `I` scaled by
   its own region-wide 95th percentile and `kappa` is a single non-negative masking scalar. `kappa = 0`
   recovers the flat baseline (exact no-op); a sweep over `kappa in {0.25, 0.5, 1.0, 2.0}` is the
   sensitivity grid. This adds **no fitted parameter** to the GLM (`kappa` is a fixed offset knob chosen by
   the construction, not estimated against the response).

### Variant B: source-level + transmission-loss received-noise model (richer)

1. Per-vessel monopole source level `SL_v` (dB re 1 uPa @ 1 m) from a speed/length regression (ECHO /
   MacGillivray-style: `SL = a + b*log10(SOG) + c*log10(Length)`).
2. Transmission loss to station s: `TL = n*log10(max(r, r0)*1000)` with `n in [15, 18]` (shallow-channel,
   between cylindrical and spherical); `RL_v,s(t) = SL_v - TL`.
3. Sum in the intensity (linear) domain over in-range vessels:
   `RL_band(s, b) = 10*log10( sum_v 10^(RL_v,s/10) )`, aggregated over the bin (energy mean).
4. Detectability from noise: `D_ais(s, b) = clip(1 - (RL_band - N0)/(N1 - N0), Dmin, 1)`, calibrating
   `N0` (ambient floor) and `N1` (full-masking level) from the empirical RL distribution (e.g. 10th and
   95th percentiles) since the OrcaHello detector's per-dB threshold is not published; the slope is a
   disclosed assumption.

Both variants share `coverage = "us_side_partial"` and `Dmin = 1e-2` (floor so `log D_ais` stays finite).

## 5. How it enters `log E` (the exact mechanism, no presence parameter)

The design already builds `exposure(s, b) = bin_hours * E_frac(s, b)` and the GLM uses `log(exposure)` as
a fixed offset (`modeling/design.py`; `modeling/effort.py`). The AIS term multiplies the existing exposure
by the detectability factor:

```
E_eff(s, b) = bin_hours * E_uptime_frac(s, b) * D_ais(s, b)
log E_eff   = log(bin_hours) + log(E_uptime_frac) + log(D_ais)
```

Equivalently, add `log D_ais(s, b)` to the GLM offset. It is a **fixed offset**, so it cannot overfit the
response: it adds zero degrees of freedom. The same `log D_ais` must also be added on the integration grid
inside `_station_intensity_fn` (`modeling/fit_kernels.py`), so the time-rescaling GOF integrates the same
effort-corrected intensity (the existing `station_log_effort` call is the hook).

## 6. Expected skill band + whether `k_diel` / `k_season` get cleaner (reasoned, NOT measured)

This is the honest analysis behind the NOT-MEASURED delta; it is reasoning about the model form and the
data geometry, with no fabricated numbers.

- **Decompose the AIS term into a cyclic part and an episodic part.** Vessel noise has (i) a cyclic
  component (more daytime + summer traffic, partly correlated with `k_diel` / `k_season`) and (ii) an
  episodic component (individual ship passages, not captured by any cyclic kernel).
- **The cyclic part de-biases, it does not add held-out skill.** A flexible cyclic kernel can already
  absorb daytime/seasonal detectability structure as a fitted coefficient. Moving that structure into a
  *fixed* offset re-attributes it (the `k_diel` / `k_season` curves shift toward true presence and away
  from the detectability confound, i.e. they get **cleaner / closer to unbiased**), but it does not
  improve out-of-sample deviance because the free kernel was already fitting it. It can even slightly
  *reduce* skill if the fixed offset is a worse fit to that structure than the free coefficient was.
- **Only the episodic part can raise held-out CV-skill**, and only if those ship-passage maskings line up
  with genuine drops in detection counts the kernels cannot otherwise explain. Given the bursty,
  detector-chatter nature of the stream (effective independent N ~300 onsets; Hawkes branching 0.79-0.96),
  the episodic masking that survives binning to 1 h is modest.
- **Per-station leverage is weak.** The four stations sit in one ~8x9 km cluster, all facing the same
  Haro Strait lane, so `D_ais` is nearly a single shared regional series; it cannot differentiate stations
  much, which limits how much new per-station structure it injects.
- **The BC-side gap shrinks it further** (the index is a lower bound on masking).

**Expected band (honest, NOT-MEASURED):** mean held-out CV mean-deviance-skill change in roughly
**-0.01 to +0.03**, most likely **near-zero-to-slightly-positive**, with the *primary deliverable being
cleaner `k_diel` and `k_season` curves (de-confounding) rather than a skill jump*. The most valuable
plausible outcome is improved **fold stability** (lifting the negative fold 1 and tightening the +0.0044
lower bound) rather than a higher mean. It **cannot reach +0.144 alone** and is not a promotion lever; per
SYN it is the "more signal per observation" / clean-the-baseline lever that must precede judging any new
effect-modifier covariate (B2 SST front, B3 Albion anomaly), so those covariates are read against a
correctly-specified offset rather than a mis-specified flat one.

## 7. GO / NO-GO

**GO (conditional, build-gated) on the WIRING as a de-biasing effort offset; NO-GO on any skill credit
until measured.**

- GO rationale: the role classing is correct and safe (B.2 effort/exposure, fixed offset, zero presence
  parameters, `kappa = 0` is an exact no-op), `log E` is currently flat so there is real headroom, and S2
  rank 1 / SYN A3 both rank it the highest-value, lowest-risk effort wire. It should be built and measured
  in a separate operator-gated step, sequenced before B2/B3 so those covariates are judged against a clean
  baseline.
- NO-GO component: the skill delta is **NOT-MEASURED** (real AIS infeasible here), and the reasoned band
  is small and most likely sub-skill (de-biasing, not a jump). No confidence is earned; effective
  confidence stays 0.0. Judge the eventual build by **fold-stable held-out CV-skill** (>= 4/5 folds, across-
  fold lower bound, PIT), never in-sample fit, and accept it as a graduate only if it at least does not
  *degrade* fold stability while making the kernel curves cleaner.

## 8. PATCH-SPEC (for the later single-editor, operator-gated integrate)

Not applied here (no convergence-file edit). Files and surfaces the integrator touches:

1. **New source-level AIS index (do not fabricate the data).** Upgrade `src/aws_backend/sources/ais.py`
   from a presence-count proxy to the per-station proximity index of section 4 (variant A default), and
   parametrize the year so `AIS<year>_WestCoast` (or the bulk GeoParquet) covers the full detection span,
   not just 2023. Ingest it into a new per-station stream (e.g. `env_vessel_noise`, keyed by acoustic
   station, not the existing single `ais_vessel_traffic_erddap` "salish_sea" cell), via the existing
   `ingest_p1_sources` path in `src/aws_backend/ingest_timeseries.py`. The ingest is a SEPARATE
   operator-/deploy-gated step (no fetch-that-writes in this wave).
2. **`modeling/ais_noise.py` (new, pure, side-effect-free, mirrors `modeling/effort.py`).** Reads the
   `env_vessel_noise` index and returns `D_ais(s, b) in (Dmin, 1]` and `log D_ais` on a grid, with `kappa`
   (variant A) / `N0,N1,Dmin` (variant B) as inputs and `kappa = 0` => `D = 1` exact no-op. Carries the
   `coverage = "us_side_partial"` flag and refuses to fabricate where AIS is absent (returns `D = 1` and
   a `missing_ais=True` note rather than inventing masking, B.2/B.3).
3. **`modeling/design.py` `build_design`.** Add an optional `noise_by_station` argument; when present,
   `exposure *= D_ais(s, center)` before `log_exposure`. Default `None` => unchanged behaviour.
4. **`modeling/effort.py`.** Thread an optional detectability factor through `exposure_for_bins` /
   `station_log_effort` (multiply `E_frac` by `D_ais`), keeping all current signatures default-compatible
   (no factor => identical output).
5. **`modeling/fit_kernels.py` `_station_intensity_fn`.** Add `log D_ais(s, t)` on the integration grid
   alongside the existing `station_log_effort` term, so time-rescaling integrates the effort-corrected
   intensity. No change to any kernel, to `_confidence_from_gates`, or to the served gate logic.
6. **Score it** through `modeling/validation/crossval.py` `block_cv` (`write_outputs=False`,
   `.venv-modeling`, the B.5 env, `fk._maybe_write_s3 = lambda: None`), reporting per-fold skills, the
   across-fold lower bound, PIT, and the `k_diel` / `k_season` curve change vs the section-1 baseline,
   across the `kappa` sweep. Promotion remains a separate B.1 supervisor decision on SERVED data.

**DE drift note:** none required. This patch touches code (`fit_kernels.py`, `effort.py`, `design.py`,
new `ais_noise.py`/`ais.py`), not the DE-flagged prose docs (`M2_nonlinear_physics.md`, `wave_shape.yml`
objectives, `ORCHESTRATOR_NOTES.md`, wildlife register). The source doc S2 already classes AIS correctly
as effort/exposure (no stale GO to supersede), and the RECALIBRATION-FROM-DE block does not flag AIS.

## 9. Return summary

- **Doc path:** `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/graduation/TA3_ais_effort.md`.
- **Baseline (MEASURED):** 4-station experiment CV mean-deviance-skill +0.0778, folds
  [-0.0381, +0.0648, +0.1401, +0.0662, +0.1559] (4/5 positive, lower bound +0.0044), PIT calibrated
  (p=0.364), confidence 0.49, **`log E` flat today** (`effort_assumed_continuous=True`).
- **AIS delta:** **NOT-MEASURED.** Real Marine Cadastre fetch infeasible in this bounded environment
  (ERDDAP connection reset from this host; AccessAIS is async; bulk is multi-GB / multi-year over a
  2020-2026 span; recent years likely unpublished). Not fabricated (B.3).
- **B.2 role:** effort/exposure, a multiplicative detectability factor on the existing exposure offset;
  zero added presence parameters; NOT laundered into presence.
- **Sourcing + index + wiring:** delivered (section 3-5), with the **BC-side US-only coverage gap**
  documented as a lower-bound bias on masking.
- **Expected band (reasoned, NOT-MEASURED):** ~ -0.01 to +0.03 on mean CV-skill, most likely near-zero;
  primary value is **cleaner `k_diel`/`k_season` (de-confounding) + better fold stability**, not a skill
  jump; cannot reach +0.144 alone.
- **GO/NO-GO:** **GO (conditional, build-gated)** on the de-biasing effort wire as the clean-the-baseline
  step before judging B2/B3; **NO-GO** on any skill credit until measured by fold-stable held-out CV.
- **PATCH-SPEC:** section 8 (for the later single-editor, operator-gated integrate). No DE drift note
  required.
- **Confirmation:** nothing deployed, fetched-to-write, promoted, or committed; no served artifact or
  store written; no convergence file edited; mlops-gate untouched. Effective confidence 0.0.
