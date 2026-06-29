# S2 -- covariate signal source discovery

Agent: O0 orchestrator, writing S2 directly (the W9-S2 research subagent hit a resource limit
twice; the operator asked the orchestrator to produce this deliverable in its place). Date:
2026-06-27 (America/New_York). Repo: `/Users/gilraitses/orcast`. This doc only; no other file
edited, no deploy, no production write, no fit, no promotion, no commit (B.1/B.6/B.10). No
fetch-to-write was run; every source below is described from public provenance, not ingested.

Authority above this doc: `20260627_mlops-handoff/HANDOFF_CHARTER.md` section B;
`20260627_mlops/SIGNAL_MODELING_CHARTER.md`; task = `SIGNAL_MODELING_DISPATCH.md` section S2.

## 0. Hydration + the bar I judge against

Read first, in order: HANDOFF_CHARTER B (B.1 honesty/promotion gate, **B.2 effort-bias covariate
roles**, B.3 withhold-over-fake, B.9 EC2-for-DFO escape hatch), SIGNAL_MODELING_CHARTER,
SIGNAL_MODELING_DISPATCH (S2), `docs/methodology/FORECAST_KERNELS.md` (current covariates +
effort-bias), `modeling/tide_harmonic.py` (the in-repo harmonic example),
`research/forward/G3_l3_grounding.md` (Albion/Fraser prey context + the L3 WITHHELD state),
`research/forward/G2_promotion_protocol.md` (the +0.144 bar). I also read the S1 catalog already on
disk so S2 stays consistent with it.

The judging bar (G2, charter sec 4): a covariate graduates only if it could plausibly move SERVED
held-out, **fold-stable** CV mean-deviance-skill toward **+0.144** -- never in-sample fit, never
added parameters. The frontier is small-N (~2089 detections, 4 stations) and the confidence map
saturates fast, so a covariate that merely correlates in-sample is a dead-end.

### 0.1 The current covariate stack (what new signal must be independent OF)

From `FORECAST_KERNELS.md`, `log lambda` already carries: `s_space(x)` (habitat/bathymetry),
`k_tide` (tidal phase, harmonic), `k_diel` (24 h), `k_lunar` (29.5 d), `k_season` (annual),
`k_salmon` (Albion run index, currently L3-WITHHELD), and a `log E(x,t)` effort offset. A new
covariate only adds held-out skill if its **temporal variation is independent of those kernels**.
That single fact decides most verdicts below: SST, river discharge, salinity, and upwelling all
have a dominant **annual cycle** that `k_season` already absorbs, so only their **anomaly /
gradient / subtidal-residual** components are admissible new signal. Likewise raw current speed is
tidal, which `k_tide` already carries -- only the **subtidal / shear** residual is independent.

### 0.2 The three admissible roles under B.2 (the honesty spine of this doc)

Every signal is classed as exactly one of:
- **(a) effort / exposure term** -- it changes the *probability a present whale is detected* (or the
  monitored volume), and enters through `log E`, NOT the rate kernels. Vessel noise / ambient noise
  are the canonical case: they mask calls and lower detectability; treating them as presence drivers
  would launder a detector artifact into biology.
- **(b) effect-modifier covariate** -- it plausibly changes *true SRKW presence/foraging intensity*
  and enters as its own kernel `k_*`. It is fit against effort-stable acoustic detections with the
  `log E` offset, never against biased visual sightings.
- **(c) validation-only / `s_space`** -- it cannot be cleanly identified as either a temporal effort
  or temporal effect term at our N (static spatial, or presence-only/biased), so it informs the
  spatial habitat prior or the validation overlay, not the temporal gate.

The hard rule (B.2): acoustic detections stay the effort-stable temporal driver; a hydrophone is a
fixed position, not a whale GPS fix; nothing here is laundered into a whale fix.

---

## 1. COVARIATE SOURCE CATALOG

"Annual cycle?" flags whether the raw signal is dominated by a seasonal cycle that `k_season`
already carries (so only its anomaly is independent). "In region?" is the Salish Sea / Haro Strait /
San Juan core the 4 stations sit in (~48.4-48.8 N, -123.3 to -122.7 W).

### Group P -- physical oceanography (gridded model + satellite)

| Signal | Source / dataset id | Access / license | Spatial res | Temporal res / span | In region? | Annual cycle? |
|---|---|---|---|---|---|---|
| **Currents (u,v), 3D** | SalishSeaCast NEMO v21-11 (UBC MOAD) | ERDDAP griddap `ubcSSg3DPhysicsFields1hV21-11` / `ubcSSfDepthAvgdCurrents1h`; open (ERDDAP, Apache-like) | ~500 m | hourly; hindcast 2007+, near-real-time since 2024-01 | **YES** (Strait of Georgia + Juan de Fuca + Gulf/San Juan Islands) | tidal-dominated, not annual |
| **Salinity, temperature, SSH (3D)** | SalishSeaCast NEMO v21-11 | same ERDDAP server | ~500 m | hourly; 2007+ | **YES** | salinity/temp partly annual (freshet/season) |
| **SST (foundation)** | NASA JPL MUR L4 v4.1 (`jplMURSST41`) | NOAA CoastWatch ERDDAP + PO.DAAC; direct S3 `podaac-ops-cumulus-public/MUR-JPL-L4-GLOB-v4.1/` (us-west-2); Earthdata login for cloud | 0.01 deg (~1 km) | daily; 2002-06+ | YES (but ~1 km smooths narrow channels) | **strong annual** |
| **SST (higher-res, fronts)** | GHRSST L2P VIIRS (Suomi-NPP) | PO.DAAC / Earthdata; OPeNDAP | ~750 m, swath | per-overpass; 2012+ | YES (cloud-gappy) | strong annual |
| **Surface currents (radar)** | IOOS HFRNet (USWC) | NDBC THREDDS `dods.ndbc.noaa.gov/thredds/catalog/hfradar.html` (since 2025-06-30); open | 1-6 km | hourly | **partial -- open Juan de Fuca mouth only; the inland archipelago is radar-shadowed** | tidal |
| **Upwelling index** | NOAA CUTI / BEUTI (`erdCUTIdaily` / `erdBEUTIdaily`) | NOAA ERDDAP; open | 1 deg lat bins | daily; 1988+ | **NO -- coverage is 31-47 N; our region is ~48.5 N, OUT of the product** | strong annual |

### Group H -- hydrology / freshwater

| Signal | Source / dataset id | Access / license | Spatial | Temporal res / span | In region? | Annual cycle? |
|---|---|---|---|---|---|---|
| **Fraser River discharge at Hope** | ECCC Water Survey of Canada station **08MF005** | wateroffice.ec.gc.ca historical CSV + real-time web service (`realtime_ws`); R `tidyhydat`; Open Government Licence - Canada | point gauge (49.39 N, -121.45 W) | daily (sub-daily realtime); **1912-present** | upstream driver of the in-region Fraser plume | **strong annual** (freshet ~late May-Jun) |

Note on access host: 08MF005 is on `wateroffice.ec.gc.ca` (ECCC), which is a *different* host from
the DNS-blocked DFO FOS host `www-ops2.pac.dfo-mpo.gc.ca` (the Albion fishery, B.9). If wateroffice
is also blocked from the dev host/region at fetch time, route via the aimez EC2
`i-04a649f91274e9fce` exactly like the Albion recipe -- but this doc runs no fetch.

### Group A -- anthropogenic / detectability

| Signal | Source / dataset id | Access / license | Spatial | Temporal res / span | In region? | Annual cycle? |
|---|---|---|---|---|---|---|
| **AIS vessel traffic** | NOAA Marine Cadastre NAIS (USCG) | `marinecadastre.gov/accessais` (clip-and-ship CSV) + bulk GeoParquet/CSV 2009+; BOEM/NOAA/USCG, open | 1-min point tracks | continuous; 2009+ (US waters; BC side via Canadian AIS, not this feed) | YES (US side of the boundary) | weak (some summer recreational rise) |
| **Ambient noise** | derived from AIS proximity, or in-band hydrophone RMS, or ECHO/ONC noise products | AIS-derived: open; hydrophone band level: from our own OrcaHello/Orcasound audio; ECHO noise: partnership | varies | varies | YES | weak |

### Group B -- biological / prey (beyond Albion/DART)

| Signal | Source / dataset id | Access / license | Spatial | Temporal res / span | In region? | Annual cycle? |
|---|---|---|---|---|---|---|
| **Albion test fishery (Fraser Chinook CPUE)** | DFO FOS, already wired (`salmon.py`, `_load_albion_fos`) | DFO FOS via aimez EC2 (B.9); OGL-Canada | point index | daily, Apr-Oct; cached 2019-2026 | upstream run-timing proxy | **strong annual** |
| **Bonneville / Fraser counts (other stocks)** | WDFW / PSC / Columbia DART | public web/API | point counts | daily seasonal | adjacent stocks | strong annual |
| **Test-fishery alternatives (Whonnock, Cottonwood)** | DFO FOS sibling reports | same FOS host (EC2) | point | seasonal | Fraser stocks | strong annual |

### Group T -- terrain (static; already partly held)

| Signal | Source / dataset id | Access / license | Spatial | Temporal res | In region? |
|---|---|---|---|---|---|
| **Bathymetry / terrain** | CUDEM (NOAA NCEI) 1/9 arc-sec; held locally; modeling tree currently only wires ETOPO1 1-arc-min | NCEI, open | ~3 m (CUDEM) | static | YES |

---

## 2. ADMISSIBLE ROLE (B.2) + COLLINEARITY

| Signal | B.2 role | Honest reason | Collinearity with existing kernels |
|---|---|---|---|
| SalishSeaCast **subtidal/residual currents + shear** | **(b) effect-modifier** | foraging tracks convergence/shear fronts; the *subtidal* residual is a real physical driver | raw current speed is **collinear with `k_tide`** -- admissible ONLY as the tide-band-removed residual / shear |
| SalishSeaCast **salinity (Fraser plume front)** | **(b) effect-modifier**, weak | plume fronts aggregate prey; front *position* can vary at sub-seasonal scale | **collinear with `k_season` and with Fraser discharge** (freshet); admissible only as front-gradient/anomaly |
| **SST front gradient** (MUR / VIIRS `|grad SST|`) | **(b) effect-modifier** | thermal fronts concentrate prey; the *gradient* carries sub-seasonal structure | raw SST **strongly collinear with `k_season`**; use gradient/anomaly, not absolute SST |
| **Fraser discharge anomaly** (08MF005) | **(b) effect-modifier** | drives plume extent + correlates with Fraser Chinook migration conditions; de-seasonalized anomaly is independent | raw discharge **strongly collinear with `k_season`** (and partly with `k_salmon`); admissible only as anomaly |
| **AIS vessel traffic / ambient noise** | **(a) effort / exposure** | vessel noise *masks SRKW calls and lowers detection probability*; it belongs in `log E`, not a presence kernel. (A secondary disturbance/effect-modifier story exists but is confounded with detectability at our N -- default to effort to avoid laundering, B.2.) | partly correlated with `k_diel`/`k_season` (daytime/summer traffic) -- must be entered as effort so it de-biases rather than competes |
| **CUTI / BEUTI upwelling** | -- | **out of product coverage (31-47 N)**; not sourceable for our region | n/a |
| **HF-radar surface currents** | (b) in principle | inland archipelago is radar-shadowed; SalishSeaCast supersedes in-region | tidal (as currents) |
| **Bathymetry/terrain (CUDEM)** | **(c) validation-only / `s_space`** | static spatial; cannot move the *temporal* CV gate; informs the habitat prior | collinear with depth + the 4-level station intercept |
| **Other prey counts (Bonneville/DART, sibling test fisheries)** | (b) effect-modifier, deferred | same role as `k_salmon`; but L3 is WITHHELD and the binding constraint is presence-days, not more prey series (G3) | collinear with Albion + `k_season` |

Cross-covariate collinearity worth stating once: SST, salinity, Fraser discharge, and upwelling
**all share the annual cycle**, so wiring more than one of their *raw* forms just re-expresses
`k_season`. Their anomaly/gradient/residual forms are only *weakly* mutually collinear and are where
any independent signal lives.

---

## 3. RANKED GO / NO-GO (expected independent, fold-stable held-out contribution)

Ordered by the campaign objective: move SERVED, fold-stable CV mean-deviance-skill toward +0.144
via genuinely independent signal, cheapest first.

1. **GO -- AIS-derived effort/noise term for `log E` (effort/exposure, B.2-a).** The highest-value,
   lowest-risk wire. It does not chase presence skill directly; it *de-biases the effort offset that
   every temporal kernel already depends on*. Better `log E` makes `k_diel`/`k_tide`/`k_season`
   cleaner and can raise held-out skill without adding a presence parameter -- exactly the
   "more signal per observation" lever that survives the anti-overfitting rule. Open Marine Cadastre
   feed, US side. Caveat: BC-side traffic needs Canadian AIS; partial coverage is still informative.

2. **GO (conditional) -- SST thermal-front gradient (effect-modifier, B.2-b).** Use `|grad SST|` /
   distance-to-front from MUR (or VIIRS for sharper fronts), NOT absolute SST (which `k_season`
   owns). Physically motivated (fronts concentrate prey), and the gradient has genuine sub-seasonal
   temporal variation. This is the S2 source M3's C1 depends on -- graduating it unlocks M3-C1.
   Conditional on the front signal surviving fold-stable held-out scoring, not in-sample fit.

3. **GO (conditional) -- SalishSeaCast subtidal currents + shear/convergence (effect-modifier,
   B.2-b).** Gridded, ~500 m, hourly, full in-region coverage -- the best current source (HF radar
   is shadowed inland). Admissible ONLY after removing the tidal band (raw currents = `k_tide`).
   The subtidal residual + shear/Okubo-Weiss is the source M3's B1 front term needs. Higher
   engineering effort (de-tiding, gridding to station footprints), so ranked below SST.

4. **GO (conditional) -- Fraser discharge anomaly, 08MF005 (effect-modifier, B.2-b).** Cheapest
   feed here (daily CSV, 1912+, one gauge), physically tied to the Fraser plume and to Fraser
   Chinook migration. Admissible only de-seasonalized (raw discharge = `k_season`/freshet). Honest
   ceiling: it is a coarse single-point proxy and partly redundant with `k_salmon`; expect a small
   contribution, but it is nearly free to test.

5. **CONDITIONAL -- SalishSeaCast salinity (Fraser-plume front).** Real but doubly collinear (with
   `k_season` AND discharge); only the front-gradient/anomaly is independent, and it largely
   restates #3/#4. Wire only if #3 is already in and salinity adds a separable front signal.

6. **NO-GO (now) -- bathymetry/terrain (CUDEM).** Genuinely useful, but as `s_space`/validation
   (B.2-c), NOT a mover of the temporal CV gate the campaign is scored on (the 4 stations sit in one
   ~8x9 km cluster -- static spatial covariates cannot lift the temporal half). Matches M3's
   E-family verdict. GO only inside a separate `s_space` quality wave, not for +0.144.

7. **NO-GO -- CUTI/BEUTI upwelling index (B.3 withhold-over-fake).** The product stops at 47 N; our
   region (~48.5 N) is outside it. Do not substitute a hand-rolled Bakun index as if it were the
   validated product. If upwelling is ever wanted, it must be computed locally from in-region wind
   and reported as a new, unvalidated derived signal -- a separate decision, not this catalog.

8. **NO-GO -- HF-radar surface currents.** Inland San Juan/Gulf Island waters are radar-shadowed;
   SalishSeaCast (#3) supersedes it in-region. Revisit only for the open Juan de Fuca mouth if a
   station is ever grounded there.

9. **DEFER -- additional prey series (Bonneville/DART, sibling Fraser test fisheries).** Same role
   as `k_salmon`, but G3 establishes the binding L3 constraint is **summer acoustic presence-days,
   not more prey predictors**; L3 stays WITHHELD. More prey series cannot move that. Defer to the
   L3 re-test wave after S1 nodes add presence-days.

### The single cheapest high-value experiment this catalog implies

Wire the **AIS-derived effort/noise term into `log E`** (#1) and dry-run whether the cleaner effort
offset raises held-out, fold-stable CV-skill on the existing 4-station data -- no new presence
parameter, no new biology claim, just a less-biased exposure model. It is the one S2 item that can
help *without* new observation and without an overfitting-prone flexible kernel, so it is the safest
first test. The next tier (SST-front gradient #2, subtidal-current shear #3) are the sources that
*unlock M3's derived covariates* and should be sequenced with that wave. Everything here stays
investigation-first: nothing is fetched-to-write, deployed, promoted, or committed; the actual
feeds + wiring + refit are separate operator-gated waves.

---

## Return summary

- **Doc path:** `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/S2_covariate_sources.md`
- **Catalog:** physical-ocean (SalishSeaCast NEMO ~500 m hourly currents/salinity/temp/SSH; MUR &
  VIIRS SST; HFRNet radar; CUTI/BEUTI upwelling), hydrology (Fraser at Hope 08MF005), anthropogenic
  (Marine Cadastre AIS / derived ambient noise), prey (Albion already wired + sibling stocks), and
  static terrain (CUDEM). Provenance/access/license recorded per source; nothing ingested.
- **B.2 roles:** AIS/ambient-noise = **effort/exposure** (`log E`, the de-biasing lever); SST-front
  gradient, subtidal-current shear, Fraser-discharge anomaly, salinity-front = **effect-modifier**
  kernels (admissible only in anomaly/gradient/residual form); bathymetry/terrain =
  **validation-only / `s_space`**; CUTI/BEUTI = unsourceable in-region (withheld).
- **Collinearity:** SST, salinity, discharge, upwelling all share the annual cycle `k_season` owns,
  and raw currents share `k_tide` -- so only anomaly/gradient/subtidal-residual forms are
  independent new signal; that is the load-bearing constraint on every effect-modifier here.
- **Ranked go/no-go:** GO AIS effort/noise term (cheapest, de-biases the existing kernels); GO-cond
  SST-front gradient (unlocks M3-C1); GO-cond SalishSeaCast subtidal current shear (unlocks M3-B1);
  GO-cond Fraser-discharge anomaly (cheap, coarse); CONDITIONAL salinity front; NO-GO terrain (it is
  `s_space`, not the temporal gate); NO-GO CUTI/BEUTI (out of coverage, B.3); NO-GO HF radar
  (shadowed in-region); DEFER more prey series (L3 binds on presence-days, not predictors).
- Honesty rails held: nothing promotes (B.1); vessel noise classed as detectability/effort not
  laundered into presence (B.2); out-of-coverage upwelling reported as unsourceable rather than
  faked (B.3). No fetch-to-write, no deploy, no promotion, no commit.
