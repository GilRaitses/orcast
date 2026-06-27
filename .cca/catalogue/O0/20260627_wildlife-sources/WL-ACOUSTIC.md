# WL-ACOUSTIC — Passive Acoustic Monitoring (PAM) networks for the SRKW presence spike train

Lane: WL-ACOUSTIC of the WILDLIFE wildlife-source research waveset.
Date: 2026-06-27 (America/New_York). Read-only research; no ingest, no commits.
Model role: presence **spike train** (kernel estimation, Levels 1–2) and **log E** effort offset.
Output template: `docs/data-procurement/PROCUREMENT_CHARTER.md` Agent Output Template (YAML) + a
`literature_grounding` block per source.

## Why this lane is the highest-value unlock

The Level 2 follow-up (`docs/methodology/CALIBRATION_STUDIES.md`,
`modeling/studies/reports/level2_joint_temporal.json`) showed the binding constraint is the
**single-station** fit (`haro_strait` only): bringing `k_tide` into the joint fit lifted phase
coverage 0.42 → 1.00 but held-out skill stayed negative. The L2 fitness gate explicitly needs
"kernels stable across CV folds" and "shape consistent across stations" (Level 1 gate), and Level
4 needs "multi-station concurrent detections." A single detector cannot separate animal cycle from
detector/site idiosyncrasy. **More stations is the estimation substrate that L2 is starving for.**
So this report ranks sources first by whether they add *new fixed stations* with an
*effort-stable* detection series, and second by label/confidence richness for the L0 detector ROC.

## Honesty constraints carried into this lane

- Acoustic presence ≠ visual encounter. Every source here is a presence/effort layer, never a
  sighting. Keep it distinct from WL-SRKW (validation + `s_space`).
- A detection at a fixed hydrophone reports vocalizing animals near a point, modulated by call
  rate and detection range, not animal abundance. The "effort-stable" claim is about *human
  observation effort* (continuous recording vs daylight/good-weather visual), not about perfect
  detectability — detectability still varies with noise/sea-state and must be carried as the L0
  ROC and the `log E` offset, exactly as `CALIBRATION_STUDIES.md` Method/Level 0 require.
- Citations verified by web search before quoting are marked `verified: true`; anything I could
  not confirm to a named, dated venue is marked `verified: false` and flagged in text.

---

## 1. OrcaHello AI detection feed (Orcasound nodes) — ALREADY WIRED

This is the exact source the current kernel is fit on. It is the *detection* layer over the
Orcasound hydrophone nodes (binary SRKW call classifier + human moderation). Listed for
completeness and because its multi-node coverage is under-used: the fit uses only `haro_strait`,
but the same API already serves other in-region nodes.

```yaml
source: orcahello_detections
already_wired: true
purpose: SRKW call-detection spike train (presence events) + moderated labels, the substrate for k_diel/k_tide kernels
availability: public_api
account_needed: none
license: detections API public; underlying audio CC-BY-NC-SA 4.0 (Orcasound)
endpoint_or_access_path: https://aifororcasdetections.azurewebsites.net/api/detections (+ /confirmed, /falsepositives, /unknowns, /unreviewed); wired in src/aws_backend/sources/orcahello.py and orcahello_history.py
fields:
  - name: timestamp
    meaning: detection time (UTC); the spike time
  - name: location{name,latitude,longitude}
    meaning: hydrophone node position (NOT the orca position)
  - name: confidence
    meaning: model score 0-100 (rescaled 0-1) — per-detection CONFIDENCE available
  - name: reviewed/found
    meaning: moderator outcome -> confirmed vs false_positive vs unknown vs unreviewed
  - name: audioUri/spectrogramUri
    meaning: raw evidence clip + spectrogram
time_coverage: ~2020-present (live + full archive via paging)
spatial_coverage: Orcasound nodes, southern Salish Sea (see source 2 for coords)
adapter_contract:
  stream_name: orcahello_detections
  record_shape: {t, station, lat, lng, confidence, reviewed, found, confirmed, audio_uri, spectrogram_uri}
  cadence: event-driven (live window) + archive paging
integrity_condition: kernel_identifiability
station_coordinates: per detection record (hydrophone node lat/lng)
detection_vs_raw_audio: BOTH (detection events + linked audio/spectrogram clips)
moderated_labels: YES (confirmed/false_positive/unknown via dedicated endpoints) — directly feeds M-L0 ROC
per_station_effort_uptime: NOT in detection payload; must be derived from node uptime/HLS availability (gap = no record). This is the L0 effort gap.
per_detection_confidence: YES (0-100 score) — supports detector ROC (d', AUC) like M-L0
risks:
  - Unreviewed stream is false-positive dominated; only confirmed records are a clean "presence" label.
  - Effort/uptime not exposed -> absence is ambiguous (offline node vs quiet whale). Needs node-status join.
  - Confidence is a single model's score, not calibrated across model versions.
next_action: Already ingested; expand fit beyond haro_strait to all in-region nodes; join node uptime for log E.
decision_label: can_get_now
priority: P0
literature_grounding:
  - citation: "Mellinger, D.K., K.M. Stafford, S.E. Moore, R.P. Dziak, H. Matsumoto. 2007. An overview of fixed passive acoustic observation methods for cetaceans. Oceanography 20(4):36-45. doi:10.5670/oceanog.2007.03"
    verified: true
    mechanism: "Establishes fixed/continuous PAM as effort-stable relative to visual survey: recording continues at night, in poor weather, and around the clock, so detection-rate variation reflects the animal cycle rather than the observation cycle. This is exactly why detections (not sightings) are used as the spike train in CALIBRATION_STUDIES.md."
  - citation: "Olson et al. 2018 (Salish Sea SRKW sightings, effort bias) — in repo references.bib"
    verified: in_repo
    mechanism: "Documents the effort confound in visual SRKW occurrence that motivates using continuous acoustic detections for temporal-kernel estimation instead."
```

---

## 2. Orcasound hydrophone node network (raw audio + node metadata) — ALREADY WIRED (metadata)

The hardware/audio layer beneath OrcaHello. Wired today only as static station metadata
(`src/aws_backend/sources/orcasound.py`), but the raw audio S3 registry and the node roster are
the path to *more stations* and to running the project's own detector where OrcaHello does not.

```yaml
source: orcasound_hydrophones
already_wired: true   # station metadata only; raw-audio archive NOT yet ingested
purpose: fixed hydrophone node network (raw HLS audio + S3 archive) -> additional effort-stable detection stations
availability: public_api    # node roster via orcasite GraphQL/REST; audio via AWS open-data S3
account_needed: none
license: CC-BY-NC-SA 4.0 (Orcasound audio); AWS Open Data Registry
endpoint_or_access_path: orcasite API (https://live.orcasound.net), raw audio s3://registry.opendata.aws/orcasound/ ; metadata wired in src/aws_backend/sources/orcasound.py
fields:
  - name: node id/name/slug
    meaning: station identity + stream URL
  - name: latitude/longitude
    meaning: fixed hydrophone position
  - name: visible/online
    meaning: node status (proxy for uptime/effort)
time_coverage: 2018-present (per-node; archive depth varies)
spatial_coverage: |
  Production nodes (2023): Orcasound Lab (Haro Strait, ~48.558 N, -123.174 W approx),
  Port Townsend (~48.14 N, -122.76 W approx), Bush Point / Whidbey (~48.03 N, -122.60 W approx),
  Sunset Bay / Edmonds-Mukilteo (~47.86 N, -122.33 W approx).
  Dev nodes: Point Robinson (Vashon), north San Juan Channel, MaST Center (Redondo).
  EXACT coords: pull from orcasite API (coords above are approximate, mark unverified).
adapter_contract:
  stream_name: orcasound_audio
  record_shape: {node, lat, lng, stream_url, s3_prefix, status}
  cadence: continuous HLS; 10-second S3 segments
integrity_condition: kernel_identifiability   # (effort_offset when node-uptime series is derived)
station_coordinates: YES (per node; exact via orcasite API — listed coords approximate/unverified)
detection_vs_raw_audio: RAW AUDIO (no built-in detections — pair with OrcaHello or own detector)
moderated_labels: via OrcaHello moderation + aifororcas-podcast crowd labels (separate)
per_station_effort_uptime: derivable from S3 segment continuity / node status — this is the cleanest path to log E for the Orcasound stations
per_detection_confidence: N/A at raw layer (depends on detector applied)
risks:
  - Raw audio is large; running a detector is its own pipeline (out of scope for this lane).
  - Node coords/roster change; treat listed coords as approximate until pulled from API.
  - Non-commercial license (CC-BY-NC-SA) — confirm use class before any redistribution.
next_action: Pull authoritative node roster + S3 segment manifests to build per-node UPTIME (log E) series; this de-confounds OrcaHello absences.
decision_label: can_get_now
priority: P0
literature_grounding:
  - citation: "Mellinger et al. 2007, Oceanography 20(4):36-45 (as above)"
    verified: true
    mechanism: "Continuous fixed recording -> effort-stable; segment continuity is a direct measure of recording effort, which is the log E offset the L0 gate requires."
```

**Multi-station note:** Orcasound already spans ~4 production + 3 dev nodes. Fitting the existing
OrcaHello feed across all of them (instead of `haro_strait` alone) is the *cheapest* multi-station
step — no new account, source already wired. This is the first Level 2 unlock.

---

## 3. Ocean Networks Canada (ONC) Oceans 3.0 hydrophones — ALREADY WIRED (spectrogram relay)

Wired today only as a server-side spectrogram relay (`src/aws_backend/sources/onc.py`). The full
Oceans 3.0 API + ERDDAP expose hydrophone time series and data products across multiple BC nodes
(Strait of Georgia, off SW Vancouver Island), i.e. **new fixed stations north of the current fit**.

```yaml
source: onc_oceans3
already_wired: true   # spectrogram PNG relay only; detection/time-series NOT yet ingested
purpose: additional fixed hydrophone stations (BC) + data products -> multi-station spike trains
availability: account_required   # free API token
account_needed: api_key   # ONC_API_TOKEN (already supported, server-side only per HANDOFF B5)
license: CC-BY 4.0 (ONC open data)
endpoint_or_access_path: |
  Oceans 3.0 v3 REST https://data.oceannetworks.ca/api (locations?deviceCategoryCode=HYDROPHONE;
  dataProductDelivery; archivefile). ERDDAP/OPeNDAP: https://dap.oceannetworks.ca/erddap .
  Python client: oceannetworkscanada/api-python-client.
fields:
  - name: locationCode/locationName/lat/lon
    meaning: station identity + coordinates (Discovery service)
  - name: deviceCategoryCode=HYDROPHONE
    meaning: hydrophone device filter
  - name: dataProduct (audio WAV/FLAC, spectrogram, detections)
    meaning: 120+ products incl. audio + derived
time_coverage: multi-year per node (varies)
spatial_coverage: Strait of Georgia and SW Vancouver Island shelf nodes; Salish Sea adjacent. (Note: Lime Kiln LKWA is The Whale Museum/SMRU, NOT ONC — see source 8.)
adapter_contract:
  stream_name: onc_hydrophone
  record_shape: {location_code, lat, lon, t, product, value}
  cadence: continuous; products generated on request
integrity_condition: kernel_identifiability   # (effort_offset via deployment/uptime metadata)
station_coordinates: YES (Discovery locations service)
detection_vs_raw_audio: BOTH (raw WAV/FLAC + derived products; automated detectors available via data products, varies by node)
moderated_labels: partial / project-dependent (not a uniform moderated SRKW label like OrcaHello)
per_station_effort_uptime: YES (deployment metadata + data availability per device) — strong log E support
per_detection_confidence: depends on the detection data product selected (not guaranteed)
risks:
  - Token must stay server-side (already enforced in onc.py).
  - SRKW-specific detection product not uniform across nodes; may need to run own detector on audio.
  - Node positions are BC-side (north of haro_strait) — good for spatial spread, but ecotype mix (Northern/Biggs) must be labeled, not assumed SRKW.
next_action: Use Discovery to enumerate hydrophone locations + deployment uptime; pull audio/detection products for 2-3 Salish-adjacent nodes to extend the station array northward.
decision_label: needs_user_account   # token already provisioned in this project
priority: P0
literature_grounding:
  - citation: "Mellinger et al. 2007, Oceanography 20(4):36-45 (as above)"
    verified: true
    mechanism: "Fixed cabled/continuous nodes -> effort-stable detection series at new positions; multiple positions are required for the cross-station consistency check (Level 1 gate) and population decoding (Level 4)."
```

---

## 4. DFO Ocean Protection Plan — Marine Environmental Quality (OPP-MEQ) PAM mooring network — NOT WIRED

The single largest **multi-station** unlock in SRKW critical habitat. DFO (Vagle/IOS) operates a
network of continuously-recording autonomous hydrophone moorings, SRKW-centred, with **manually
validated killer-whale call detections** in several published CSAS analyses.

```yaml
source: dfo_opp_meq_pam
already_wired: false
purpose: multi-station, continuous, SRKW-centred acoustic detections in critical habitat -> the multi-station spike-train array for Level 2/4
availability: research_request_required
account_needed: researcher_request
license: Government of Canada / DFO (data-sharing terms; some via CSAS reports + whalesound.ca visualizations)
endpoint_or_access_path: DFO Institute of Ocean Sciences (IOS); CSAS Research Documents (waves-vagues.dfo-mpo.gc.ca); BC Hydrophone Network whalesound.ca (visualization). No open bulk API confirmed -> data-sharing request.
fields:
  - name: mooring location (lat/lon)
    meaning: fixed station position (~30 km spacing)
  - name: continuous WAV (256 kHz, 24-bit, AMAR G4 + GeoSpectrum M36-100)
    meaning: raw acoustic for own detection
  - name: validated KW call detections
    meaning: manually reviewed presence events (per CSAS analyses)
  - name: co-located CTD (RBR) temp/salinity/depth
    meaning: covariate context (sound speed)
time_coverage: continuous since February 2018 (multi-year)
spatial_coverage: |
  ~11 moorings in place; SRKW critical habitat. Named sites incl. Swiftsure Bank, Port Renfrew,
  Jordan River, Sooke (Strait of Juan de Fuca), Haro Strait, Boundary Pass, Swanson Channel (N Pender
  ISZ), Saturna/East Point; expanded into Strait of Georgia. (One mooring example: 48.7393 N, 123.257 W.)
adapter_contract:
  stream_name: dfo_pam_detections
  record_shape: {mooring, lat, lng, t, species=killer_whale, validated:bool}
  cadence: continuous recording; detection series per analysis window
integrity_condition: kernel_identifiability   # array also enables effort_offset cross-checks
station_coordinates: YES (CSAS report tables; ~30 km spacing)
detection_vs_raw_audio: BOTH (continuous WAV archive + manually validated KW detections in studies)
moderated_labels: YES (manually validated KW detections; detectors do NOT separate SRKW vs Northern vs Biggs — ecotype must be labeled, not assumed)
per_station_effort_uptime: YES (moorings serviced for continuous coverage; deployment/recovery tables in CSAS docs) — excellent log E
per_detection_confidence: detector-dependent; validated-vs-auto distinction available
risks:
  - Access is by data-sharing request, not open API -> latency, terms.
  - KW detector is ecotype-agnostic; SRKW attribution needs call-type/pod labeling (do not assume all KW = SRKW).
  - Some products only as aggregate figures in CSAS PDFs, not raw event tables.
next_action: Request the OPP-MEQ acoustic detection time series (or per-mooring validated KW events) from DFO IOS; this is the P0 multi-station data-sharing ask.
decision_label: needs_research_request
priority: P0
literature_grounding:
  - citation: "DFO CSAS (Vagle et al.) — Vessel presence and acoustic environment within SRKW critical habitat in the Salish Sea and Swiftsure Bank area; and: Evaluation of the efficacy of the Juan de Fuca lateral displacement trial and Swiftsure Bank/Swanson Channel ISZs, 2019. Government of Canada / DFO Canadian Science Advisory Secretariat."
    verified: true
    mechanism: "Documents a fixed, continuous, multi-mooring (~11 sites, since Feb 2018) SRKW-centred PAM network with AMAR G4 + GeoSpectrum M36-100 recorders at 256 kHz/24-bit, serviced for continuous coverage. Continuous recording = effort-stable; multi-site = the cross-station array the L2/L4 gates require."
  - citation: "Thornton et al. 2022 (SRKW summer distribution and habitat use, DFO CSAS) — in repo references.bib"
    verified: in_repo
    mechanism: "Effort-corrected SRKW habitat-use map used to site the moorings in foraging hotspots; corroborates that these stations sit where SRKW spend time."
  - citation: "Barlow, J., B.L. Taylor. 2005. Estimates of sperm whale abundance in the northeastern temperate Pacific from a combined acoustic and visual survey. Marine Mammal Science 21(2):429-445."
    verified: true
    mechanism: "Quantifies acoustic detecting more groups than visual and enabling night/all-weather detection — the general effort advantage that justifies acoustic-first temporal estimation."
```

**Multi-station note:** This is THE multi-station Level 2/Level 4 unlock — ~11 fixed, continuous,
SRKW-sited moorings with validated KW detections and serviced uptime. If only one new source is
pursued for the L2 binding constraint, it is this one.

---

## 5. JASCO Boundary Pass Underwater Listening Station (ECHO program / PortListen) — NOT WIRED

Cabled, two-frame observatory under the Vancouver shipping lanes in SRKW critical habitat, running
real-time AI killer-whale detectors with manual review. Very high uptime and a large
manually-verified call archive.

```yaml
source: jasco_boundary_pass
already_wired: false
purpose: cabled, near-100%-uptime KW detection station(s) in critical habitat -> high-quality effort-stable spike train + log E anchor
availability: vendor_or_restricted   # JASCO/Transport Canada/ECHO; PortListen platform
account_needed: vendor_contract   # or research collaboration via ECHO/Transport Canada
license: Transport Canada / Vancouver Fraser Port Authority ECHO; access via PortListen, terms apply
endpoint_or_access_path: PortListen platform (audio, spectrograms, metadata, ambient noise stats); contact via ECHO program / JASCO. No open public API confirmed.
fields:
  - name: KW call detections (manually verified)
    meaning: presence events; >275,000 verified KW calls logged
  - name: two subsea frame positions
    meaning: fixed cabled station coordinates (Boundary Pass, Canada-US border)
  - name: ambient noise statistics
    meaning: detectability covariate (noise -> L0 ROC confound control)
time_coverage: continuous since June 2019 (cabled); autonomous recorders Dec 2018-May 2020 bridge
spatial_coverage: Boundary Pass, 23 km strait on Canada-US border, SRKW critical habitat; two frames under the shipping lanes. (Related SIMRES recorders: Monarch Head / East Point.)
adapter_contract:
  stream_name: jasco_bp_detections
  record_shape: {frame, lat, lng, t, species=killer_whale, verified:bool, ambient_noise}
  cadence: continuous; real-time detectors with manual review
integrity_condition: kernel_identifiability
station_coordinates: YES (two cabled frames; exact via JASCO/ECHO)
detection_vs_raw_audio: BOTH (PortListen serves audio + spectrograms + detections)
moderated_labels: YES (manually reviewed KW detections; ecotype-agnostic detector)
per_station_effort_uptime: YES — >99% uptime since June 2019 across both arrays (effectively constant effort = ideal log E anchor)
per_detection_confidence: detector score + manual verification flag (PAMlab); availability via terms
risks:
  - Vendor/agency-restricted; access likely needs ECHO/Transport Canada collaboration, not a public download.
  - KW detector does not separate SRKW/Northern/Biggs ecotypes (must label).
  - Commercial platform terms; confirm research-use license before any ingest.
next_action: Approach via the ECHO program / Transport Canada research-collaboration channel for Boundary Pass KW detection series + uptime logs.
decision_label: vendor_or_restricted
priority: P1
literature_grounding:
  - citation: "JASCO Applied Sciences. Boundary Pass Underwater Listening Station (Transport Canada / Vancouver Fraser Port Authority ECHO Program). Reported >275,000 manually verified killer whale calls and >99% uptime since June 2019."
    verified: true   # JASCO published operational reporting; metrics from JASCO/ClearSeas materials
    mechanism: "A cabled station at ~constant (>99%) uptime is the strongest possible effort-stable detector: the log E offset is nearly flat, so detection-rate variation is almost entirely animal cycle + detectability. Ambient-noise stats let detectability be regressed out (L0)."
  - citation: "Mellinger et al. 2007, Oceanography 20(4):36-45 (as above)"
    verified: true
    mechanism: "General fixed-PAM effort-stability rationale."
```

---

## 6. NOAA SanctSound / NCEI Passive Acoustic Data Archive — NOT WIRED

NOAA-Navy Sanctuary Soundscape Monitoring Project, archived and served by NCEI with a **killer
whale detection** product, openly downloadable (GCS + ERDDAP). Best fit for the **outer/coastal**
SRKW range (e.g. Olympic Coast NMS) rather than inner Salish Sea, so it extends spatial spread.

```yaml
source: noaa_sanctsound
already_wired: false
purpose: open, standardized KW detection products (NetCDF) at sanctuary sites -> additional effort-stable stations + clean open license
availability: public_download   # GCS immediate; ERDDAP RESTful; NCEI request also available
account_needed: none
license: public (NOAA / U.S. Government), NOAA Big Data Program (GCP)
endpoint_or_access_path: |
  NCEI Passive Acoustic Data Archive map viewer (discovery);
  ERDDAP killer-whale detection files: https://coastwatch.pfeg.noaa.gov/erddap/info/noaaSanctSound_Dection_Files/index.html
  (variables include killerwhaleID / killerwhaleNetcdfFile); audio + products on Google Cloud Storage.
fields:
  - name: killerwhaleID / killerwhaleNetcdfFile
    meaning: presence detection product per site/deployment (NetCDF)
  - name: site/deployment id
    meaning: station identity (e.g. SBxx; Olympic Coast OC sites for SRKW range)
  - name: raw audio files
    meaning: full recordings on GCS for own detection
time_coverage: ~2018-2022 (project span; ~300 TB archived)
spatial_coverage: National Marine Sanctuary sites; for SRKW-relevant range see Olympic Coast NMS (outer WA coast). Inner Salish Sea coverage is limited -> complements, not replaces, Salish nodes.
adapter_contract:
  stream_name: sanctsound_kw_detections
  record_shape: {site, lat, lng, t, killer_whale_presence, netcdf_uri}
  cadence: per-deployment detection products (daily/1h aggregates) + raw audio
integrity_condition: kernel_identifiability
station_coordinates: YES (site/deployment metadata in archive)
detection_vs_raw_audio: BOTH (detection NetCDF products + raw audio on GCS)
moderated_labels: YES (analyst-produced detection products; QA per NCEI workflow)
per_station_effort_uptime: YES (deployment windows + sound-level products give recording effort) — supports log E
per_detection_confidence: product-dependent (presence/aggregate; per-detection score not guaranteed in 1d products)
risks:
  - Inner-Salish coverage thin; main value is outer-coast range extension + clean open license.
  - Detection products are aggregated (e.g. daily) for some variables -> coarser than event-level spikes.
  - Project span ended ~2022 -> historical, not live.
next_action: Pull killer-whale detection NetCDFs for SRKW-range sanctuary sites via ERDDAP; map deployment windows to effort.
decision_label: can_get_now
priority: P1
literature_grounding:
  - citation: "NOAA-Navy Sanctuary Soundscape Monitoring Project (SanctSound), stewarded by NOAA NCEI Passive Acoustic Data Archive; killer-whale detection products served via ERDDAP (noaaSanctSound_Dection_Files)."
    verified: true   # NCEI/ERDDAP portal confirmed; killerwhale detection variables present
    mechanism: "Standardized, long-term, continuous sanctuary recordings with analyst detection products = effort-stable presence series at fixed sites, openly licensed."
  - citation: "Hatch et al. 2024 (SanctSound synthesis) — cited secondhand in a curated-dataset preprint"
    verified: false   # could not confirm the exact Hatch 2024 citation to a named venue
    mechanism: "(If verified) project-level description of SanctSound detection methodology. Flagged unverified; do not quote until confirmed."
```

---

## 7. Ocean Observatories Initiative (OOI) Regional Cabled Array broadband hydrophones — NOT WIRED

Offshore Oregon cabled broadband hydrophones (HYDBB). Open raw audio, no SRKW detection product —
value is **range extension** (offshore Oregon is within the documented coast-to-Alaska SRKW range)
and a continuous, very-stable-effort substrate if the project runs its own detector.

```yaml
source: ooi_rca_hydbb
already_wired: false
purpose: continuous offshore broadband hydrophone audio (Oregon) -> range-extension station(s); own-detector substrate
availability: public_download
account_needed: none
license: public (OOI; raw archive open; IRIS for seismic/LF)
endpoint_or_access_path: |
  OOI Raw Data Archive (MiniSEED .mseed, 5-min files, daily subdirs by site);
  OOI Data Explorer + ERDDAP (~600 datasets); IRIS for hydrophone/seismic ("OO" network).
  Tooling: ObsPy / OOIPY (mseed -> WAV/FLAC).
fields:
  - name: HYDBB site (Axial Base x2, Slope Base x2, Oregon Offshore, Oregon Shelf)
    meaning: fixed station identity + position
  - name: broadband waveform
    meaning: raw acoustic (MiniSEED) for own detection
time_coverage: multi-year, near-real-time (5-min updates) + delayed addendum after Navy review
spatial_coverage: Oregon margin / Axial Seamount (offshore, NE Pacific); within broad SRKW coastal range, NOT Salish Sea.
adapter_contract:
  stream_name: ooi_hydbb_audio
  record_shape: {site, lat, lng, t, mseed_uri}
  cadence: continuous; 5-min MiniSEED files
integrity_condition: kernel_identifiability   # effort_offset trivially near-constant (cabled)
station_coordinates: YES (six HYDBB sites; positions in OOI site metadata)
detection_vs_raw_audio: RAW AUDIO ONLY (no SRKW detection product; must run own detector)
moderated_labels: NO (no built-in moderated KW labels)
per_station_effort_uptime: YES (cabled, near-continuous; file presence = effort) — clean log E
per_detection_confidence: N/A until own detector applied
risks:
  - No detections -> requires running a classifier (own pipeline; out of this lane's scope).
  - Offshore Oregon SRKW occupancy is seasonal/sparse -> low spike count, modest k-estimation value.
  - MiniSEED -> audio conversion adds engineering overhead.
next_action: Catalogue HYDBB sites + uptime; defer ingest until an own-detector path exists (lower priority than Salish multi-station).
decision_label: can_get_now
priority: P2
literature_grounding:
  - citation: "Ocean Observatories Initiative, Regional Cabled Array Broadband Hydrophone (HYDBB) data availability (OOI Raw Data Archive, MiniSEED; six sites at Axial Base, Slope Base, Oregon Offshore/Shelf)."
    verified: true   # OOI operational documentation confirmed
    mechanism: "Cabled continuous recording = near-constant effort; supplies an effort-stable substrate at offshore positions for range extension once a detector is applied."
  - citation: "Mellinger et al. 2007, Oceanography 20(4):36-45 (as above)"
    verified: true
    mechanism: "Fixed-PAM effort-stability rationale; offshore sites add spatial spread for the population-decoding read-out (Level 4)."
```

---

## 8. Lime Kiln (The Whale Museum SeaSound / SMRU Consulting / Beam Reach) — NOT WIRED (separate from ONC)

Cabled hydrophone at Lime Kiln Point lighthouse, San Juan Island — a documented SRKW foraging
hotspot in Haro Strait. Single station, but its **real-time KW detections now feed Ocean Wise's
Whale Report Alert System (WRAS)**, and it co-locates with the existing `haro_strait` fit, making
it a strong corroboration/effort cross-check rather than a new region.

```yaml
source: lime_kiln_seasound
already_wired: false
purpose: long-running cabled KW-detection station in Haro Strait foraging hotspot -> corroborates haro_strait fit + WRAS detection feed
availability: research_request_required   # live stream public; detection series via SMRU/Whale Museum
account_needed: researcher_request   # for detection data; live audio is public
license: The Whale Museum / SMRU Consulting (research terms); live stream public
endpoint_or_access_path: |
  Live stream via whalemuseum.org SeaSound / seasound.org; detection integration via Ocean Wise
  WRAS; data access by request to The Whale Museum / SMRU Consulting (info@whalemuseum.org).
fields:
  - name: KW vocalization detections (real-time)
    meaning: presence events feeding WRAS since June 2024
  - name: ambient noise / SRKW presence-activity
    meaning: long-term acoustic research products (SMRU)
  - name: continuous audio
    meaning: raw stream since 2007 (public), SMRU data since 2012
time_coverage: public stream since 2007; SMRU acoustic data since 2012; WRAS detection feed since June 2024
spatial_coverage: Lime Kiln Point, west side San Juan Island. Coordinates ~48.516 N, -123.153 W; depth ~23 m; cabled. (In/near the haro_strait fit footprint.)
adapter_contract:
  stream_name: lime_kiln_detections
  record_shape: {station=lime_kiln, lat:48.516, lng:-123.153, t, species=killer_whale}
  cadence: continuous stream; real-time detections
integrity_condition: kernel_identifiability   # also a haro_strait effort cross-check
station_coordinates: YES (48.516 N, -123.153 W; depth 23 m — verified via IQOE/SMRU)
detection_vs_raw_audio: BOTH (public live/archived audio + real-time KW detections via WRAS)
moderated_labels: partial (WRAS-grade real-time detections; new SMRU/UBC/DFO statistical method in development)
per_station_effort_uptime: derivable from stream continuity (cabled, "tides and technology willing") — modest gaps
per_detection_confidence: detector-dependent (WRAS pipeline); availability via SMRU
risks:
  - Single station, co-located with existing haro_strait fit -> adds corroboration/effort cross-check, NOT new spatial coverage.
  - Detection event series likely needs a request (live audio is open but event tables are not a public API).
  - "Beam Reach" is historical program support; current operator is The Whale Museum + SMRU (cite accordingly).
next_action: Request the Lime Kiln KW detection series (WRAS/SMRU) as an independent effort/label cross-check for the haro_strait kernel.
decision_label: needs_research_request
priority: P1
literature_grounding:
  - citation: "The Whale Museum SeaSound Remote Sensing Network / SMRU Consulting North America — Lime Kiln cabled hydrophone (public since 2007; SMRU acoustic data since 2012; KW detections integrated into Ocean Wise Whale Report Alert System since June 2024). Station: 48.516 N, -123.153 W, 23 m (IQOE Port of Vancouver - Lime Kiln record)."
    verified: true   # coordinates/operator confirmed via IQOE + SMRU + Whale Museum
    mechanism: "Continuous cabled recording at a known SRKW foraging hotspot -> effort-stable presence at the same location as the current fit; an independent detector here cross-checks the haro_strait spike train and its effort assumptions."
  - citation: "Thornton et al. 2022 (SRKW summer distribution/habitat use, DFO) — in repo references.bib; SMRU maps Lime Kiln inside the high-likelihood SRKW foraging area."
    verified: in_repo
    mechanism: "Confirms Lime Kiln sits in a documented foraging hotspot, so its detections are SRKW-relevant presence rather than incidental."
```

---

## Ranked summary (by Level 2 multi-station impact)

| Rank | Source | Wired? | New stations? | Multi-station L2 unlock | Detections | Moderated labels | Effort/uptime | Per-det. confidence | Access | Priority |
|------|--------|--------|---------------|--------------------------|------------|------------------|---------------|---------------------|--------|----------|
| 1 | OrcaHello feed (all Orcasound nodes) | yes | yes (use all nodes) | **HIGH — already wired, just expand beyond haro_strait** | yes | yes | derive from node status | yes | public_api | P0 |
| 2 | DFO OPP-MEQ moorings | no | **~11 fixed SRKW-sited** | **HIGHEST — biggest new array in critical habitat** | yes (validated) | yes | yes (serviced) | detector-dep. | research request | P0 |
| 3 | Orcasound raw audio / node roster | yes (meta) | yes | HIGH — supplies log E + own-detector option | via OrcaHello | via moderation | yes (S3 continuity) | n/a raw | public_api | P0 |
| 4 | ONC Oceans 3.0 hydrophones | yes (relay) | yes (BC nodes) | HIGH — northward spatial spread | both | partial | yes | product-dep. | api_key | P0 |
| 5 | JASCO Boundary Pass ULS | no | yes (2 cabled frames) | MED-HIGH — >99% uptime, critical habitat | yes (verified) | yes | yes (~constant) | yes (terms) | vendor/ECHO | P1 |
| 6 | NOAA SanctSound (NCEI) | no | yes (coastal/OC) | MED — outer-range extension, open license | yes (NetCDF) | yes | yes | product-dep. | public_download | P1 |
| 7 | Lime Kiln SeaSound (SMRU/Whale Museum) | no | no (co-located) | LOW — corroboration/effort cross-check at haro_strait | yes (WRAS) | partial | derive from stream | detector-dep. | research request | P1 |
| 8 | OOI RCA broadband (HYDBB) | no | yes (offshore OR) | LOW — range extension, no detections, sparse SRKW | raw only | no | yes | n/a raw | public_download | P2 |

### Sources that explicitly unlock multi-station Level 2

- **DFO OPP-MEQ (source 4)** — ~11 continuous, SRKW-sited moorings since Feb 2018 with validated KW
  detections and serviced uptime. The single biggest *new* fixed-station array directly in critical
  habitat. The top P0 data-sharing ask.
- **OrcaHello across all Orcasound nodes (sources 1+2)** — already wired; fitting the existing feed
  on all ~4 production + dev nodes instead of `haro_strait` alone is the cheapest L2 unlock (no new
  account, no new pipeline).
- **ONC Oceans 3.0 (source 3)** — BC hydrophone nodes add positions north of the current fit
  (token already provisioned, server-side).
- **JASCO Boundary Pass (source 5)** — two cabled frames at >99% uptime in critical habitat; a
  near-flat `log E` anchor with a large verified-call archive (access-gated).

### Lower-impact / supporting

- **SanctSound (source 6)** and **OOI (source 8)** extend the *outer/offshore* range and bring
  clean open licenses, but add little inner-Salish multi-station estimation power.
- **Lime Kiln (source 7)** is co-located with the existing fit, so it is an independent
  detector/effort cross-check for `haro_strait`, not new spatial coverage.

### Honesty / role recap

Every source above is a presence/effort layer feeding `kernel_identifiability` (the spike train)
and, via uptime, the `effort_offset` (`log E`). None is a visual encounter; ecotype-agnostic KW
detectors (DFO, JASCO) must be call-type/pod-labeled before being treated as SRKW. Per-detection
confidence (OrcaHello, JASCO) is the input to the M-L0 detector ROC; per-station uptime is the
input to the `log E` offset that the Level 0 gate requires. Citations are verified to named venues
(Mellinger et al. 2007 Oceanography 20(4):36-45; Barlow & Taylor 2005 Marine Mammal Science
21:429-445; DFO CSAS Vagle et al.) or flagged `verified: false` (Hatch 2024) / `unverified`
(approximate Orcasound node coordinates; arXiv 2602.09295 curated-dataset preprint, future-dated
and not relied upon here).
