# OS1 findings: open detection-range effort/detectability `log E` spec

Agent: OS1 background subagent, Open-Science Integration (OS) waveset, O0 forecast ML-ops lane.
Date: 2026-06-27 (America/New_York). Repo: `/Users/gilraitses/orcast`. This findings doc is the ONLY
file written (plus one STEP_LOG line). READ-ONLY research plus bounded reachability probes; no
convergence-file edit (`modeling/**`, `src/aws_backend/**`), no served/S3 write, no fetch-that-writes,
no ingest, no deploy, no promotion, no commit, no `git add`. Effective confidence stays 0.0; this
RECOMMENDS and SPECs only.

Hydration read in full first: `WAVESET_CHARTER.md` (sections 0-4), `OS_DISPATCH.md` (hard rails, OS1
source pointers), `TB4_PRESENCE_DAY_COUNT.md` (the effort denominator left NOT-MEASURED), the
`TA2_TA3_BASELINE_VERDICT.md` (TA3 AIS wire landed as a no-op on the same flat `log E`), and the repo
anchors `modeling/effort.py`, `modeling/design.py` (`build_design`), `modeling/ais_noise.py`,
`research/signal_modeling/graduation/TA3_ais_effort.md`.

## 0. The gap this lane closes, and the one binding rail

TB4 (`TB4_PRESENCE_DAY_COUNT.md` section "Verdict") discharged the SRKW presence count (6 net-new
JJA-2016 days at Strait of Georgia ULS) but left condition #2, "reconstruct effort honestly", STILL
NOT-MEASURED: per B.2, presence-only counts without an effort denominator bias the rate, so no CV-skill
credit is claimed. TA3 (`TA2_TA3_BASELINE_VERDICT.md`, the "TA3 AIS effort NOT-MEASURED" section) landed the AIS
detectability factor as an exact no-op because `log E` is still flat (`effort_assumed_continuous=True`,
no binding uptime). Both gaps are the same hole: the conditional intensity
`log lambda = b0 + a_station + sum_j kernel_j(phase_j(t)) + log E(station, t)` (`modeling/effort.py`
docstring) has a `log E` that carries no real per-(station, day) detectability structure.

Binding rail (B.2, same as TA3 section 0): acoustic detectability is an EFFORT / EXPOSURE term, never a
presence kernel. Ambient noise and propagation conditions change how far a hydrophone can hear a calling
whale, which changes expected detections at fixed true presence, so a detection-range-derived term
belongs in `log E` as a multiplicative offset with ZERO added presence parameters. It must not be
laundered into presence. Everything below keeps it as a fixed multiplicative detectability factor on the
existing exposure offset, exactly like the TA3 `D_ais`.

## 1. OSF repository `osf.io/6ctjq` (MEASURED, read-only probe)

The OSF link published in the paper's Data Availability statement is a view-only anonymous link:
`https://osf.io/6ctjq/?view_only=f4e6e83b9eab427bb530a74638ba3e52` (token transcribed from the PLOS
full text, which is CC-BY 4.0). Probed read-only via the OSF API v2 with that view_only token; nothing
downloaded into the repo store and no zip extracted (bounded probe only).

Reachability (MEASURED 2026-06-27 from this host):

| Probe | Result |
|---|---|
| `GET api.osf.io/v2/nodes/6ctjq/` (no token) | HTTP 401 "Authentication credentials were not provided" |
| `GET api.osf.io/v2/guids/6ctjq/` | HTTP 302 -> `nodes/6ctjq/` (the guid is a project node) |
| `GET .../nodes/6ctjq/?view_only=<token>` | HTTP 200 |
| `GET .../files/osfstorage/?view_only=<token>` | HTTP 200, 2 folders |

Node metadata (MEASURED): title "Modeling the detection range of pulsed calls from resident killer
whale in nearshore waters of British Columbia, Canada"; description "This repository contains the sound
pressure level, and acoustic propagation loss files used for estimating the detection range of killer
whale pulsed calls in nearshore waters of British Columbia, Canada"; category `project`;
`public: false`; `registration: false`; `access_requests_enabled: true`; storage region `ca-1`
(Canada); created 2024-12-29, last modified 2024-12-31.

Files (MEASURED, osfstorage root, 2 folders, 2 files):

| Path | Kind | Size |
|---|---|---|
| `SPL files/SPL_files.zip` | file | 42,806,989 bytes (~42.8 MB) |
| `Propagation loss coefficients/PL_coeffs.zip` | file | 242,482 bytes (~242 KB) |

Mapping to the method (section 2): `PL_coeffs.zip` holds the fitted propagation-loss coefficients
`A(f, z)` and `n(f, z)` of Eq 2 (the load-bearing, small, reusable artifact: ~242 KB). `SPL_files.zip`
holds the sound-pressure-level files: the in situ ambient SPL per site and the call source-level SPL
spectra (the larger ~42.8 MB artifact). The two zips were NOT extracted here; their internal per-site
file layout is therefore NOT-MEASURED (a later operator-gated extract characterizes the exact site keys,
frequency-band grid, and depth grid inside).

License (MEASURED): the OSF node carries NO explicit license (`node_license: None`, no `license`
relationship; `tags: []`, `subjects: []`). The PLOS article text is CC-BY 4.0, but the OSF data files
are not separately license-tagged. OPERATOR GATE: confirm reuse terms before any ingest. The node is
private with `access_requests_enabled: true`, shared via the published anonymous view-only link;
read access is granted by that token but redistribution / derivative-use terms for the coefficient files
are unstated. Treat as "open to read via the published token, license-unconfirmed for reuse" until the
operator confirms (request access on OSF or contact the corresponding authors, Mouy / Austin / Yurk).

Provenance: JASCO Applied Sciences + Fisheries and Oceans Canada (DFO). Coefficients computed with
JASCO's Marine Operations Noise Model (MONM).

## 2. The PLOS One 2025 method (MEASURED from the full text)

Mouy, Austin, Wladichuk, Yurk (2025), "Modeling the detection range of pulsed calls from resident killer
whale in nearshore waters of British Columbia, Canada", PLOS One, DOI `10.1371/journal.pone.0331942`
(published 2025-09-26; CC-BY 4.0; full text retrieved and read). It supersedes the authors' earlier
conference version (JASA `10.1121/10.0008304`).

How a station + ambient condition maps to a call detection probability vs distance:

1. Received level. A call is detectable at range `R` when its received level exceeds the ambient noise
   by at least a detector threshold, in the same 300 Hz band. Eq 1: `RL = SL - PL`, with `SL` the
   source level (dB re 1 uPa^2 m^2) and `PL` the propagation loss (dB re 1 m^2).
2. Propagation loss model. Eq 2: `PL(f, z, R) = A(f, z) - n(f, z) * log10(R)`, for frequency `f` (Hz),
   source depth `z` (m), range `R` (m). `A` and `n` are the fitted per-site, per-band, per-depth
   coefficients (`n` is the geometric-spreading term). These are exactly the `PL_coeffs.zip` contents.
   `PL` was modeled with MONM (parabolic-equation + ray-trace) along multiple azimuthal transects per
   site, over a geoacoustic profile, sound-speed profile, and bathymetry, then fit to Eq 2.
3. Detection condition. A call is detected at range `R` if `RL - NL >= DT`, i.e.
   `SL - PL(f, z, R) - NL >= DT`, where `NL` is the in situ ambient level in that 300 Hz band and `DT`
   is the signal-processing detection threshold of the AUTOMATED detector (explicitly not a human
   listening threshold). The maximum detection range is the largest `R` satisfying this.
4. Per 300 Hz band, then combined. Analysis is run independently across consecutive 300 Hz bands from
   1 kHz upward (the smallest bandwidth assumed necessary for an automated detector); the final maximum
   detection range is the band-combined result. Source-level spectral distribution per band: slope
   -0.66 dB per 300 Hz band for SRKW, -0.27 dB for NRKW (from 35 and 14 high-SNR calls).
5. Monte Carlo over source level and caller depth. For each ambient sample, the max detection range is
   computed 10,000 times, drawing 100 normally distributed source-level values (Holt et al. for SRKW,
   Wladichuk et al. for NRKW) and caller depths from a log-logistic dive-depth model. Each iteration
   yields a detection probability at each range; the distribution is summarized by percentiles 25/50/75.
6. Ambient time series -> per-site detection-probability-vs-range. Ambient SPL is processed per minute
   (PAMlab). The detection-probability curve at a site is the fraction of 1-minute ambient samples whose
   max detection range equals or exceeds a given range, divided by the total number of 1-minute samples.
   This bakes the site's ambient distribution (and therefore its season) into a probability-of-detection
   vs distance curve `p_det(R | site, season, ecotype)`.

Scope of the published sites (MEASURED): 8 DFO PAM locations (e.g. Swiftsure Bank, Port Renfrew, Mouat
Point, Sheringham Point), recorded on cabled icListenHF (OceanSonics) and AMAR (GeoSpectrum M36) units.
Published medians (Table 3): SRKW 50% on-axis detection range from 650 m (winter, Swiftsure Bank, the
noisiest) to 7.9 km (summer); 10% on-axis range 1.5-25 km in winter, 4.2-37.5 km in summer (site
dependent). Maximum detection ranges are generally GREATER in summer than winter, because winter ambient
noise is higher (weather). This summer-greater-than-winter direction is directly relevant to the JJA
presence focus of TB4/OS2: summer detectability is the favorable, larger-area regime.

From detection-probability-vs-range to an effective detection area / `log E` term:

- Effective detection area. Integrating the radial detection probability over the plane gives the
  effective detection area `A_eff(s, cond) = integral_0^inf p_det(R | s, cond) * 2*pi*R dR` (the standard
  passive-acoustic-density-estimation "effective detection radius/area"; the paper states it is built to
  "provide needed inputs for passive acoustic density estimation models"). High ambient (winter, noisy)
  shrinks `p_det(R)` and therefore `A_eff`; low ambient (summer, quiet) grows it.
- Detectability factor. Normalize to a per-station reference to get a unitless multiplier
  `D_det(s, d) = A_eff(s, cond(d)) / A_eff_ref(s)` in `(0, 1]`, where `A_eff_ref(s)` is the station's
  best-case (quietest) effective area. `D_det = 1` at the station's most detectable condition; `D_det < 1`
  as ambient rises. This is the per-(station, day) detectability term: it scales the exposure offset by
  how much ocean the sensor could actually hear that day, with no presence parameter.

## 3. How it composes with the existing exposure path

The existing chain (`modeling/design.py` `build_design`, lines ~183-197, plus `modeling/effort.py`):

```
E(s, b)      = bin_hours * E_uptime_frac(s, b) * D_ais(s, b)        # today, D_ais defaults to 1 (no-op)
log_exposure = log(E(s, b))                                          # the GLM offset
```

`exposure_for_bins` supplies `bin_hours * E_uptime_frac` (uptime from the `station_uptime` stream, with
the rpi_*<->acoustic key bridge); `build_design` multiplies in `D_ais` only when `noise_by_station` and
`ais_kappa > 0` (TA3). The open detection-range term attaches as a THIRD multiplicative factor on the
same offset (B.2 role, identical to `D_ais`):

```
E(s, b)      = bin_hours * E_uptime_frac(s, b) * D_ais(s, b) * D_det(s, day(b))
log_exposure = log(bin_hours) + log E_uptime_frac + log D_ais + log D_det
```

and the same `log D_det(s, t)` is added on the integration grid inside
`modeling/fit_kernels.py` `_station_intensity_fn` (where `station_log_effort` and the TA3 `log D_ais`
already attach), so the time-rescaling GOF integrates the same effort-corrected intensity. `D_det` is a
fixed offset: zero added degrees of freedom, cannot overfit the response.

Relationship to the three effort factors (they multiply, they do not substitute):

- `E_uptime_frac` (ONC Oceans 3.0 uptime/duty mask): "was the hydrophone recording", a 0/1 or duty
  fraction. Answers sensor on/off.
- `D_ais` (TA3, Marine Cadastre AIS): episodic vessel-noise masking, a fast (sub-daily) ambient term.
- `D_det` (this lane, OSF/PLOS): the propagation-plus-ambient detection-area scaling, "given the sensor
  is up and given the ambient, how much ocean could it hear". A per-(station, day) (or per-season) term.

Daily granularity is the natural and honest resolution for `D_det`: the published product is a
per-site, per-season detection-probability curve, and a per-(station, day) ambient summary is the finest
the open ambient series supports without fabricating sub-daily structure. `D_ais` carries the sub-daily
masking; `D_det` carries the slow ambient/propagation envelope. They are complementary, not double
counts (AIS vessel passages are one component of ambient; the PLOS ambient series is total measured
ambient at the DFO sites, so an operator combining both must avoid double-attributing the vessel
component, e.g. use `D_det` for the non-vessel propagation/weather envelope and `D_ais` for the
served-station vessel passages, or use `D_det` alone where AIS is absent).

ONC Oceans 3.0 uptime mask reachability (MEASURED 2026-06-27): the search UI
`https://data.oceannetworks.ca/SearchHydrophoneData` returns HTTP 200 (page reachable), but the
programmatic data-availability API (`https://data.oceannetworks.ca/api/locations`) returns HTTP 401
errorCode 128 "Either token or appToken must be specified". So the uptime/duty time series itself is
TOKEN-GATED and NOT-MEASURED here (OPERATOR GATE: ONC Oceans 3.0 token). This matches the TB4 verdict's
"ULS ONC-uptime mask requires an ONC Oceans 3.0 account/token".

## 4. MEASURED vs NOT-MEASURED, and the operator gate each needs

MEASURED here:

- The full method (Eq 1-2, per-300 Hz-band detection condition, Monte Carlo over source level and depth,
  per-minute-ambient detection-probability-vs-range, effective-detection-area framing). DOI
  `10.1371/journal.pone.0331942`.
- The OSF repository exists and is read-reachable via the published view-only token; it contains exactly
  `PL_coeffs.zip` (~242 KB, the `A`/`n` Eq-2 coefficients) and `SPL_files.zip` (~42.8 MB, ambient + call
  source-level SPL). Region ca-1, created 2024-12-29.
- Published per-site summer/winter median detection ranges (Table 3) and the source-level spectral slopes
  (-0.66 / -0.27 dB per 300 Hz band).
- Reachability of the OSF API (200 with token), the ONC UI (200), and the ONC API (401 token-gated).

NOT-MEASURED here (with the gate each needs):

- The OSF data-file LICENSE for reuse. Node has no license tag. GATE: operator confirms reuse terms
  (OSF "request access" / contact authors) before any ingest. Read-only inspection via the published
  token is permitted; redistribution/derivative terms are unstated.
- The internal layout of the two zips (exact per-site file names, band grid, depth grid, ambient time
  span). GATE: operator-gated extract of `PL_coeffs.zip` / `SPL_files.zip` to scratch (not done here;
  bounded probe only).
- Per-station ambient time series for the SERVED nodes (Orcasound Lab, Haro Strait, North San Juan
  Channel, Andrews Bay). The PLOS study modeled 8 DFO sites, NOT the served Orcasound stations, so
  `D_det` for our stations needs either (a) ambient at the served sites, or (b) a defensible
  geoacoustic-class + ambient transfer from the nearest published site. Mouat Point (Pender Island, near
  Boundary Pass and the north San Juan cluster) is the closest published site to the served stations and
  to the TB4 Boundary Pass node, so it is the most transferable. GATE: ONC Oceans 3.0 token (ambient SPL
  + uptime), or a DFO/JASCO ambient series, plus an operator decision to accept the geoacoustic-class
  transfer.
- The detector threshold `DT`. The PLOS `DT` is for the DFO automated detector; the served pipeline uses
  the OrcaHello detector, whose per-dB `DT` is not published. GATE: re-derive or bound `DT` for the
  served detector (same open problem TA3 flagged for `N0`/`N1`); until then `D_det` is shape-correct but
  its absolute normalization is ESTIMATED.
- The CV-skill delta of attaching `D_det`. NOT-MEASURED (no fit run; depends on all of the above). Per
  B.2 and the TA3 precedent, the expected primary value is a CLEANER, de-biased `k_season`/`k_diel`
  (moving the summer-detectability confound out of the kernels and into a fixed offset) and better fold
  stability, not necessarily a mean-skill jump. Judge any eventual build by fold-stable held-out CV
  mean-deviance-skill toward +0.144, never in-sample fit.

## 5. PATCH-SPEC (for the later single-editor, operator-gated integrate; NO code edited here)

Not applied in this run. Files and surfaces a later single editor would touch, with a byte-identical
no-op default, mirroring the landed TA3 pattern:

1. New pure module `modeling/detection_range.py` (mirrors `modeling/ais_noise.py`, side-effect-free,
   numpy + stdlib). Public API:
   - `detectability_factor(detrange_index, station, times, *, kappa_det=1.0, min_d=DEFAULT_MIN_D)`
     returning `D_det in [min_d, 1]`. Default no-op: empty/missing index or unknown station returns
     all-ones (EXACT no-op), so wiring is byte-identical until an operator supplies an index. NEVER
     fabricates ambient: missing -> `D_det = 1` plus a `missing_detrange=True` note (B.2/B.3).
   - `log_detectability(...)` returning `log D_det`, 0.0 when inactive.
   - The index is `{station: (times_hours, A_eff_norm)}` where `A_eff_norm` is the per-(station, day)
     effective-detection-area scaling in `(0, 1]` built from the OSF `A`/`n` coefficients plus the
     site/season ambient series (the construction of section 2). Carries a `coverage`/`transfer` flag
     recording whether the station used its own ambient or a geoacoustic-class transfer (e.g.
     `transfer="mouat_point_geoclass"`), so the assumption is never hidden.
2. `modeling/design.py` `build_design`. Add an optional `detrange_by_station` argument (mirroring
   `noise_by_station`); when present, `exposure_bins = exposure_bins * detectability_factor(...)` right
   after the existing TA3 `D_ais` multiply (lines ~194-197). Default `None` -> unchanged, byte-identical.
3. `modeling/effort.py`. Optional: thread the detectability factor through `exposure_for_bins` /
   `station_log_effort` for the intensity-grid path, keeping all current signatures default-compatible
   (no factor -> identical output), so the time-rescaling intensity and the design share one definition.
4. `modeling/fit_kernels.py` `_station_intensity_fn`. Add `log D_det(s, t)` on the integration grid
   alongside the existing `station_log_effort` and TA3 `log D_ais` terms. No change to any kernel, to
   `_confidence_from_gates`, or to the served gate logic.
5. Score it through `modeling/validation/crossval.py` `block_cv` (`.venv-modeling`, `write_outputs=False`,
   `fk._maybe_write_s3 = lambda: None`), reporting per-fold skills, across-fold lower bound, PIT, and the
   `k_season`/`k_diel` curve change vs the clean baseline. Promotion remains a separate B.1 supervisor
   decision on SERVED data.

The data prep (extract `PL_coeffs.zip`, build per-(station, day) `A_eff_norm` from coefficients + ONC
ambient) is a SEPARATE operator-/deploy-gated step (no fetch-that-writes, no ingest in this wave), and is
gated on the OSF license confirmation and the ONC token above.

## 6. DE drift note

None required. This doc touches code surfaces (`design.py`, `effort.py`, `fit_kernels.py`, a new
`detection_range.py`) and introduces a spec; it does not edit any DE-flagged prose doc
(`M2_nonlinear_physics.md`, `wave_shape.yml` objectives, `ORCHESTRATOR_NOTES.md`, the wildlife register).
The classing here is consistent with `research/signal_modeling/S2_covariate_sources.md` and the TA3
graduate, which already class detectability/ambient as effort/exposure (B.2); there is no stale GO to
supersede and the RECALIBRATION-FROM-DE block does not flag detection range.

## 7. Return summary

- Doc path: `.cca/catalogue/O0/20260627_open-science-integration/OS1_effort_detectability.md`.
- B.2 role: effort/exposure. A per-(station, day) detection-area scaling `D_det` as a fixed multiplicative
  factor on the existing `log E` offset (third factor after uptime and `D_ais`); zero added presence
  parameters; not laundered into presence.
- Sources (MEASURED): OSF `6ctjq` read-reachable via the published view-only token, holds `PL_coeffs.zip`
  (~242 KB, Eq-2 `A`/`n`) and `SPL_files.zip` (~42.8 MB, ambient + source-level SPL); method fully
  characterized from PLOS One DOI `10.1371/journal.pone.0331942`. ONC UI reachable, ONC API token-gated.
- NOT-MEASURED: OSF data license (node untagged), zip internals, served-station ambient series, served
  detector `DT`, and the CV-skill delta. Each gate named in section 4.
- GO/NO-GO: GO (spec/build-gated) on the `D_det` detectability WIRE as a de-biasing effort offset on
  `log E` (it closes the structural form of the TB4/TA3 NOT-MEASURED denominator with a reusable,
  open-sourced, zero-presence-parameter spec); NO-GO on any skill credit or ingest until the OSF license
  is confirmed, an ONC-token (or transferred) ambient series lands, and a fold-stable held-out CV-skill
  is measured. Effective confidence stays 0.0.
- Single highest-value next action: confirm the OSF data-file reuse license (request access / contact the
  authors), since the small, load-bearing `PL_coeffs.zip` (~242 KB) is the reusable artifact and
  everything downstream is gated on its license.
- Operator gates hit: (1) OSF license unconfirmed (node carries no license tag); (2) ONC Oceans 3.0 token
  required for the ambient/uptime series (API 401); (3) served-station ambient + served-detector `DT` not
  open (geoacoustic-class transfer from Mouat Point is the proposed bridge, operator-accepted).
- Confirmation: nothing edited in `modeling/**` or `src/aws_backend/**`, nothing fetched-to-write,
  ingested, deployed, promoted, or committed; no served artifact or store written; OSF/PLOS/ONC accessed
  read-only; mlops-gate untouched; effective confidence 0.0.
