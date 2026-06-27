# WL-SRKW: SRKW occurrence, photo-ID, census, and demographic sources

Lane: WL-SRKW (wildlife-source research waveset, O0)
Scope: Southern Resident Killer Whale (SRKW; *Orcinus orca*) visual occurrence,
photo-identification encounters, annual census, and demographic records.
Model role (locked): **external validation (held-out) and `s_space` habitat term ONLY.**
These are effort-confounded presence-only data; they must **never** feed the temporal-kernel
heat (`k_tide`, `k_diel`, `k_lunar`, `k_season`). That estimation substrate is the acoustic
network (WL-ACOUSTIC), where effort is stable.

Method: research only (web + repo). No ingest, no adapters, no account creation, no commits.
Confirmed-sighting definition used throughout: `cross_validation` status in {`verified`,
`likely`}; community-origin rows require moderator approval before they count.

---

## Ranked summary (top validation sources first)

Ranking is by validation utility = (structured/exportable) x (independent of our acoustic
estimation) x (SRKW-resolved, ideally individual/pod or behaviour labels) x (license clarity).

| Rank | Source | Role | Availability | Structured export? | Priority | Already wired |
|------|--------|------|--------------|--------------------|----------|---------------|
| 1 | Center for Whale Research (CWR) Orca Survey | external_validation (+ demographic) | public_scrape_required / research_request | Yes (per-encounter pages; community-tidied CSV exists) | P0 | no |
| 2 | The Whale Museum — Orca Master / Whale Hotline | external_validation + spatial_covariate | research_request (legacy public API likely defunct) | Partial (legacy `hotline.whalemuseum.org` API; quadrant layer via NOAA) | P0/P1 | no |
| 3 | Happywhale (photo-ID encounters) | external_validation | account_required (research export) | Yes (CC-BY-NC via OBIS-SEAMAP DOI; unofficial CLI) | P1 | no |
| 4 | OBIS-SEAMAP (Duke MGEL) | spatial_covariate + external_validation | public_download (some permission-required) | Yes (CSV / shapefile / WFS; per-dataset DOI) | P0/P1 | partial (overlaps wired OBIS backbone) |
| 5 | GBIF *Orcinus orca* occurrences | external_validation | public_api | Yes (async download API, DOI, DwC-A) | P0 | partial (overlaps wired OBIS backbone) |
| 6 | Acartia data cooperative | external_validation (community/moderated) | account_required (API key) | Yes (REST `/sightings/current` and `/trusted`) | P1 | no |
| 7 | BCCSN / Ocean Wise Sightings Network (WhaleReport) | external_validation | research_request (form) | Yes on request (DB subset) | P1 | no |
| 8 | Orca Network Whale Sighting Network | external_validation | research_request / via Acartia | No native bulk; flows to Acartia + TWM | P1/P2 | no (reachable via Acartia) |
| 9 | DFO/NOAA line-transect surveys (SWFSC ORCAWALE / CalCurCEAS) | spatial_covariate (effort-known) + external_validation | public_download (OBIS-SEAMAP) | Yes (CSV + effort tracks; CC0) | P2 | no |
| 10 | salishsea.io nightly Darwin Core Archive (aggregator) | external_validation | public_download | Yes (DwC-A + GeoParquet, sha256) | P2 | no |

Five-line takeaway:
1. **CWR Orca Survey** is the strongest structured validation source: dated, vessel-based,
   pod/ecotype-labelled encounters since 1976, plus the authoritative annual census; not open
   bulk, but per-encounter pages are exportable and a community-tidied CSV exists.
2. **Happywhale** is the best individual-resolved (photo-ID) cross-check and is already
   exportable as a CC-BY-NC dataset through its OBIS-SEAMAP DOI — ideal held-out validation.
3. **The Whale Museum Orca Master** is the dataset behind Olson et al. 2018 (the project's
   effort-bias anchor) and is the canonical `s_space` reference, but needs a research request.
4. **OBIS-SEAMAP + GBIF** give immediate, license-clear, DOI-citable occurrence backbones that
   partly overlap the already-wired `api.obis.org` backbone; use for breadth, not novelty.
5. Everything here is **effort-confounded** (Olson et al. 2018): use for held-out validation and
   the static `s_space` habitat prior only; the line-transect surveys (#9) are the one
   effort-*known* visual source and are the cleanest for an effort-corrected `s_space`, but their
   coverage is the outer coast, not the Salish Sea interior.

---

## Literature anchors (verified before quoting)

- **Olson, J.K., Wood, J., Osborne, R.W., Barrett-Lennard, L., Larson, S. 2018.** "Sightings of
  southern resident killer whales in the Salish Sea 1976−2014: the importance of a long-term
  opportunistic dataset." *Endangered Species Research* 37:105−118. doi:10.3354/esr00918.
  Open Access (CC-BY). **VERIFIED** (publisher PDF int-res.com; DOI; author list read from the
  paper masthead — note the PMC reference list for the 2023 follow-up drops Wood, but the paper
  itself lists five authors). Mechanism for this lane: the Orca Master dataset (82,447 SRKW
  sightings 1976−2014) is opportunistic/presence-only; the authors explicitly correct for
  observer effort (cost-distance from whale-watch ports and population centres) before estimating
  density, and state effort roughly tripled after 1995 from added sources, not from more whales.
  This is the direct, named justification that visual sightings are effort-confounded and belong
  in validation / `s_space`, never in the temporal kernels.
- **Thornton, S.J., Toews, S., Stredulinsky, E., Gavrilchuk, K., Konrad, C., Burnham, R.,
  Noren, D.P., Holt, M.M., Vagle, S. 2022.** "Southern Resident Killer Whale (*Orcinus orca*)
  summer distribution and habitat use in the southern Salish Sea and the Swiftsure Bank area
  (2009 to 2020)." *DFO Can. Sci. Advis. Sec. Res. Doc.* 2022/037. v + 56 p. ISBN 9780660449814.
  **VERIFIED** (DFO WAVES library PDF; Government of Canada Publications catalogue Fs70-5/2022-037E).
  Mechanism for this lane: builds an effort-corrected probability-of-occurrence surface (handling
  preferential sampling bias) and identifies high-use SRKW habitat — Swiftsure Bank, eastern
  Haro Strait, Swanson Channel, Boundary Pass, near the Fraser River, May−October — with foraging
  hotspots at Swiftsure Bank and Haro Strait. This is the named basis for the `s_space` habitat
  prior and for using acoustic detections to corroborate (not replace) sightings.

Both anchors agree on the design split this lane enforces: opportunistic SRKW sightings are
spatially/temporally biased by effort and must be effort-corrected before they inform habitat,
and used as referee (held-out validation) rather than as the temporal signal itself.

---

## Per-source records (procurement template + literature_grounding)

### 1. Center for Whale Research — Orca Survey (encounters + annual census)

```yaml
source: Center for Whale Research (CWR) Orca Survey
purpose: >
  Held-out validation of forecast encounters and a high-quality s_space prior. CWR runs the
  long-term photo-ID survey and the authoritative annual SRKW census (population count, births,
  deaths) since 1976. Per-encounter records carry date, begin/end time, location, pods/ecotype,
  observers, and a narrative summary - i.e. confirmed, individually/pod-resolved presence.
availability: public_scrape_required
account_needed: researcher_request
license: >
  All photos and data belong to CWR (501c3). No open bulk license; encounter pages are public.
  Community-tidied mirror (jadeynryan/orcas, rfordatascience tidytuesday 2024-10-15) reuses
  scraped data with CWR attribution. Treat as permission/attribution-required.
endpoint_or_access_path: >
  https://www.whaleresearch.com/encounters (one HTML page per encounter, e.g.
  https://www.whaleresearch.com/2023-66); census narrative at /orcasurvey. Community CSV:
  https://raw.githubusercontent.com/jadeynryan/orcas/refs/heads/master/data-raw/cwr_tidy.csv
  (2017-2024). For full/authoritative export: research request to CWR.
fields:
  - name: date / encounter_number
    meaning: encounter day and within-year sequence id
  - name: begin_time / end_time / duration
    meaning: encounter start/end and length (minutes)
  - name: begin_latitude / begin_longitude / end_latitude / end_longitude
    meaning: encounter start and end coordinates
  - name: pods_or_ecotype / ids
    meaning: pod (J/K/L) or ecotype label; individual IDs encountered
  - name: location / vessel / observers / encounter_summary
    meaning: place name, research vessel, observers, narrative
  - name: nmfs_permit
    meaning: permit under which photos taken
time_coverage: "Encounters web-exportable 2017-present; census/demographics 1976-present (annual)"
spatial_coverage: "Salish Sea / SRKW critical habitat; vessel-based, concentrated in summer core areas"
adapter_contract:
  stream_name: cwr_encounters
  record_shape:
    t: ISO8601
    id: "cwr:{year}-{encounter_number}"
    latitude: float
    longitude: float
    pods_or_ecotype: string
    ids: list[string]
    behavior: string|null
    cross_validation: verified
    source_url: string
    license: "CWR - attribution/permission required"
  cadence: "event-based; census annual"
integrity_condition: external_validation
risks:
  - "Effort-confounded: vessel-based survey concentrates on known summer core areas and daytime; never use for temporal kernels."
  - "No open bulk license; scraping is fragile (one page per encounter) and the tidied CSV is admittedly imperfect (typos, missing values)."
  - "Census is a population-level demographic series, not a spatial occurrence stream - keep the two uses distinct."
next_action: "Request structured encounter + census export and reuse terms from CWR; until then treat community CSV as provisional, attribution-required."
decision_label: needs_research_request
priority: P0
already_wired: false
literature_grounding:
  - citation: "Olson, J.K., Wood, J., Osborne, R.W., Barrett-Lennard, L., Larson, S. 2018. Endangered Species Research 37:105-118. doi:10.3354/esr00918. VERIFIED."
    mechanism: "Names CWR (Ken Balcomb) as a primary reliable contributor to the Orca Master sightings record and uses the SRKW census for population context; the same effort-bias caveat applies, so CWR encounters are validation/s_space, not temporal signal."
  - citation: "Thornton et al. 2022, DFO CSAS Res. Doc. 2022/037. VERIFIED."
    mechanism: "Effort-corrected SRKW summer habitat surface against which CWR encounters can be scored (held-out) and which justifies the s_space prior."
```

### 2. The Whale Museum — Orca Master / Whale Hotline

```yaml
source: The Whale Museum (TWM) - Orca Master dataset / Whale Hotline
purpose: >
  The canonical long-term SRKW sightings database (the dataset analysed in Olson et al. 2018,
  82,447 sightings 1976-2014) and the project's reference s_space source. Year-round, multi-source
  compilation with documented confirmation workflow (report -> confirm -> publish).
availability: research_request_required
account_needed: researcher_request
license: >
  TWM-owned; attribution/citation required; data submitted annually to NOAA for the SRKW Recovery
  Plan. Legacy public API documentation required full acknowledgment of TWM as source.
endpoint_or_access_path: >
  Research request: research@whalemuseum.org (Database Manager/GIS). Legacy public API
  http://hotline.whalemuseum.org/api/sightings?species=orca is documented historically but
  multiple 2023+ reports indicate it is no longer reliably active (FLAG - verify liveness before
  relying). Aggregated quadrant layer (effort summary, not point data) via NOAA InPort item 72522
  ("TWM quadrant sightings by month 1999-2022") and the NOAA SRKW Sightings dashboard.
fields:
  - name: sighting date / time
    meaning: confirmed sighting timestamp
  - name: latitude / longitude (or quadrant)
    meaning: point location, or 1-of-445 quadrant in the aggregated NOAA layer
  - name: source_class
    meaning: one of 5 tracked classes (public archive, whale-watch pager, Lime Kiln/Otis, Soundwatch, SPOT GPS)
  - name: reliability_flag
    meaning: "'public source' vs 'reliable' (observer known to TWM)"
  - name: pod / species
    meaning: SRKW pod (J/K/L) or species code
time_coverage: "1976-present (anecdotal records back to 1948); aggregated NOAA layer 1999-2022"
spatial_coverage: "Salish Sea (WA inland waters + southern BC)"
adapter_contract:
  stream_name: twm_orca_master
  record_shape:
    t: ISO8601
    id: "twm:{id}"
    latitude: float
    longitude: float
    pod: string|null
    source_class: string
    cross_validation: "verified|likely (map TWM 'reliable' -> verified, 'public consensus' -> likely)"
    license: "TWM - attribution required"
  cadence: "event-based (historical); quadrant layer monthly"
integrity_condition: external_validation
risks:
  - "Strongly effort-confounded: Olson et al. 2018 show ~3x sightings increase after 1995 driven by added sources/effort, not abundance - never temporal kernels."
  - "Legacy public API appears defunct; do not assume programmatic access without confirming."
  - "Point data is research-request gated; the openly available NOAA layer is effort-aggregated by quadrant/month (coarse, presence summary)."
  - "Overlaps Orca Network and BCCSN as upstream feeders - dedupe to avoid double-counting in validation."
next_action: "Email research@whalemuseum.org for structured Orca Master export + reuse terms; separately test whether hotline.whalemuseum.org API responds; otherwise use NOAA quadrant layer for coarse s_space."
decision_label: needs_research_request
priority: P0
already_wired: false
literature_grounding:
  - citation: "Olson, J.K., Wood, J., Osborne, R.W., Barrett-Lennard, L., Larson, S. 2018. Endangered Species Research 37:105-118. doi:10.3354/esr00918. VERIFIED."
    mechanism: "This IS the Orca Master dataset paper: it documents the 5 source classes, the confirmation rule (2 public or 1 reliable report), the effort-correction (cost-distance from ports/population centres), and the hot spots (Haro Strait, Boundary Pass/Swanson Channel, Puget Sound proper). Directly grounds both the effort-bias caveat and the s_space habitat structure."
  - citation: "Thornton et al. 2022, DFO CSAS Res. Doc. 2022/037. VERIFIED."
    mechanism: "Independent effort-corrected habitat surface corroborating the Orca Master hot spots; basis for treating TWM as an s_space reference."
```

### 3. Happywhale (photo-ID encounters)

```yaml
source: Happywhale
purpose: >
  Individual-resolved (photo-ID) killer whale encounters - the best independent cross-check for
  identity and date/location of a confirmed animal. Photo-backed, so quality is high and
  verifiable; complements CWR/TWM with a different observer pool.
availability: account_required
account_needed: free_account
license: >
  Happywhale-published OBIS-SEAMAP dataset (ID 1718, "Happywhale - Killer whale in North Pacific
  Ocean", DOI 10.82144/1131e581) is CC-BY-NC; shared with GBIF and OBIS. Direct site/API export
  for research typically needs an account and collaboration; an unofficial community CLI exists.
endpoint_or_access_path: >
  Structured + licensed path: OBIS-SEAMAP dataset 1718 (CSV / File Geodatabase download), also via
  GBIF/OBIS. Site: https://happywhale.com (account). Unofficial CLI (open-oceans/happywhale):
  `happywhale search --export out.csv --species "Killer Whale" --geom region.geojson` - undocumented
  endpoints, may break; do not depend on it for production.
fields:
  - name: individual_id / animal name
    meaning: Happywhale-assigned individual identity (photo-ID matched)
  - name: scientific_name / vernacular_name / taxon_rank
    meaning: species identification
  - name: decimal_latitude / decimal_longitude / coordinate_precision
    meaning: encounter location (WGS84)
  - name: date
    meaning: encounter date (dataset spans 1990-06-06 to 2026-06-10)
  - name: license / rights_holder / external_resource
    meaning: per-photo license, rights holder, image link
time_coverage: "1990-present (North Pacific KW dataset updated 2026-06)"
spatial_coverage: "North Pacific (global project); filter to Salish Sea / San Juan bbox"
adapter_contract:
  stream_name: happywhale_encounters
  record_shape:
    t: ISO8601
    id: "happywhale:{encounter_id}"
    individual_id: string
    latitude: float
    longitude: float
    cross_validation: verified
    license: "CC-BY-NC"
    media_url: string
  cadence: "event-based"
integrity_condition: external_validation
risks:
  - "Effort-confounded: photo-ID submissions cluster on accessible, well-photographed encounters (whale-watch, summer, daytime) - validation/s_space only."
  - "Ecotype mixing: North Pacific KW dataset includes Bigg's/transient and resident; must filter to SRKW (pod/individual ID) for SRKW-specific validation."
  - "Unofficial CLI hits undocumented endpoints (may change/break); prefer the CC-BY-NC OBIS-SEAMAP DOI path."
  - "CC-BY-NC restricts commercial reuse - check ORCAST's distribution terms."
next_action: "Create a Happywhale account and request research/export access for Salish Sea Orcinus orca; in parallel pull the CC-BY-NC OBIS-SEAMAP dataset 1718 as the citable backbone."
decision_label: needs_user_account
priority: P1
already_wired: false
literature_grounding:
  - citation: "Olson, J.K., Wood, J., Osborne, R.W., Barrett-Lennard, L., Larson, S. 2018. Endangered Species Research 37:105-118. doi:10.3354/esr00918. VERIFIED."
    mechanism: "Establishes that photo-ID / opportunistic citizen records are valuable but effort-biased, so photo-ID encounters are held-out validation, not temporal estimation input."
  - citation: "Thornton et al. 2022, DFO CSAS Res. Doc. 2022/037. VERIFIED."
    mechanism: "Effort-corrected habitat surface for scoring whether photo-ID encounter locations fall in modelled high-use s_space cells."
```

### 4. OBIS-SEAMAP (Duke Marine Geospatial Ecology Lab)

```yaml
source: OBIS-SEAMAP (seamap.env.duke.edu)
purpose: >
  Curated marine-mammal occurrence portal aggregating many SRKW-relevant datasets (photo-ID,
  line-transect, opportunistic) with per-dataset DOIs and explicit licenses. Strong for breadth of
  held-out validation and for assembling an s_space occurrence layer with provenance.
availability: public_download
account_needed: none
license: >
  Per-dataset: Public domain, CC-BY, CC-BY-NC, or "permission required". Minimum attributes
  (lat/lon, datetime, species, group size) downloadable for CC datasets without account; full
  attributes or permission-required datasets need contributor approval. Attribution to contributor
  + OBIS-SEAMAP required.
endpoint_or_access_path: >
  Species profile https://seamap.env.duke.edu/species/143025 (Orcinus orca); Advanced Search ->
  download wizard (CSV / ESRI shapefile / File Geodatabase / KML / OGC WFS-WMS). Per-dataset page
  https://seamap.env.duke.edu/dataset/{id}. datasets_and_citations.csv ships in each download zip.
fields:
  - name: decimal_latitude / decimal_longitude / coordinate_precision
    meaning: sighting location (WGS84)
  - name: datetime
    meaning: sighting date/time
  - name: scientific_name / taxon_rank / individual_count
    meaning: species id and group size (minimum attribute set)
  - name: dataset_id / DOI / sharing_policy / rights_holder
    meaning: provenance, citation DOI, license, contributor
time_coverage: "Dataset-dependent (e.g. Happywhale 1990-2026; ORCAWALE 1996/2001/2008)"
spatial_coverage: "Global; filter to Salish Sea / San Juan bbox"
adapter_contract:
  stream_name: obis_seamap_occurrence
  record_shape:
    t: ISO8601
    id: "obis_seamap:{dataset_id}:{record}"
    latitude: float
    longitude: float
    individual_count: int|null
    cross_validation: "verified|likely (per dataset data-type: photo-ID/survey -> verified)"
    license: string
    dataset_doi: string
  cadence: "static snapshots; portal updated continuously"
integrity_condition: spatial_covariate
risks:
  - "Mixed effort regimes within the portal: opportunistic datasets are effort-confounded; label per-dataset effort before any s_space weighting."
  - "Permission-required datasets appear on maps but are excluded from downloads - do not assume completeness."
  - "Overlaps the already-wired api.obis.org backbone and GBIF; dedupe by occurrenceID/DOI."
  - "CC-BY-NC subsets restrict commercial reuse."
next_action: "Pull Orcinus orca records for the San Juan bbox from CC-licensed datasets via the download wizard; record DOIs; request permission-required datasets only if needed."
decision_label: can_get_now
priority: P0
already_wired: partial  # overlaps the wired api.obis.org backbone (src/aws_backend/sources/obis.py); OBIS-SEAMAP portal endpoint itself is not wired
literature_grounding:
  - citation: "Thornton et al. 2022, DFO CSAS Res. Doc. 2022/037. VERIFIED."
    mechanism: "Uses effort-corrected occurrence (incl. survey + sightings) to define SRKW habitat; OBIS-SEAMAP is the multi-dataset occurrence substrate for building that s_space layer with provenance."
  - citation: "Olson, J.K., Wood, J., Osborne, R.W., Barrett-Lennard, L., Larson, S. 2018. Endangered Species Research 37:105-118. doi:10.3354/esr00918. VERIFIED."
    mechanism: "Effort-bias caveat for the opportunistic datasets aggregated in the portal; keeps them in validation/s_space roles."
```

### 5. GBIF — *Orcinus orca* occurrences

```yaml
source: GBIF (Global Biodiversity Information Facility)
purpose: >
  License-clear, DOI-citable occurrence backbone for Orcinus orca; aggregates iNaturalist, OBIS,
  museum and survey records. Use as broad held-out validation and a reproducible snapshot for
  s_space (each download is a single citable DOI).
availability: public_api
account_needed: free_account
license: >
  Per-record license, filterable: CC0_1_0, CC_BY_4_0, CC_BY_NC_4_0. Download DOI must be cited
  (GBIF data user agreement). Free account (username/password) required to request a download.
endpoint_or_access_path: >
  Async download: POST https://api.gbif.org/v1/occurrence/download/request (JSON predicate with
  taxonKey for Orcinus orca + geometry + license filter), poll the download key until SUCCEEDED,
  then fetch the DwC-A / SIMPLE_CSV zip + DOI. Synchronous search (<=100k):
  https://api.gbif.org/v1/occurrence/search. R/Python: rgbif occ_download(), pygbif.
fields:
  - name: decimalLatitude / decimalLongitude / coordinateUncertaintyInMeters
    meaning: occurrence location and uncertainty
  - name: eventDate
    meaning: observation date/time
  - name: basisOfRecord
    meaning: HumanObservation / MachineObservation / PreservedSpecimen
  - name: license / datasetKey / occurrenceID
    meaning: per-record license, source dataset, stable id
  - name: identificationVerificationStatus / occurrenceStatus
    meaning: verification flags where provided
time_coverage: "Multi-decadal, dataset-dependent"
spatial_coverage: "Global; filter to San Juan bbox via geometry predicate"
adapter_contract:
  stream_name: gbif_occurrence
  record_shape:
    t: ISO8601
    id: "gbif:{occurrenceID}"
    latitude: float
    longitude: float
    basis_of_record: string
    cross_validation: "verified|likely (map research-grade/specimen -> verified)"
    license: string
    download_doi: string
  cadence: "static download snapshots (DOI per pull)"
integrity_condition: external_validation
risks:
  - "Effort-confounded: dominated by HumanObservation (iNaturalist etc.) clustered on accessible/daytime/summer effort - validation/s_space only."
  - "Heavy overlap with the wired api.obis.org backbone and iNaturalist (already wired) - dedupe by occurrenceID/datasetKey to avoid leakage between train and held-out sets."
  - "Coordinate uncertainty and date precision vary; filter on coordinateUncertaintyInMeters and eventDate precision."
next_action: "Create a free GBIF account; submit a taxonKey + San Juan geometry + license predicate download; pin the DOI as the validation snapshot; dedupe against wired OBIS/iNaturalist."
decision_label: needs_user_account
priority: P0
already_wired: partial  # overlaps wired OBIS/iNaturalist; the GBIF download API itself is not wired
literature_grounding:
  - citation: "Olson, J.K., Wood, J., Osborne, R.W., Barrett-Lennard, L., Larson, S. 2018. Endangered Species Research 37:105-118. doi:10.3354/esr00918. VERIFIED."
    mechanism: "Opportunistic presence-only records are effort-biased; GBIF aggregates exactly such records, so its role is held-out validation, not temporal estimation."
  - citation: "Thornton et al. 2022, DFO CSAS Res. Doc. 2022/037. VERIFIED."
    mechanism: "Effort-corrected SRKW habitat surface for scoring GBIF occurrence locations against modelled s_space."
```

### 6. Acartia data cooperative

```yaml
source: Acartia (acartia.io) - decentralized Salish Sea marine-animal sightings cooperative
purpose: >
  Real-time + archived community sightings across the SRKW range (CA to AK), aggregating Orca
  Network (Facebook/Conserve.io) and other feeds. Useful for near-real-time validation overlay and
  community corroboration of acoustic detections.
availability: account_required
account_needed: api_key
license: >
  Creative Commons (per Acartia community guidelines/attribution; confirm exact CC variant at
  registration). API key required.
endpoint_or_access_path: >
  GET https://acartia.io/api/v1/sightings/current ; GET .../sightings/trusted ;
  GET .../sightings/{id} ; POST .../sightings (contribute). access_token parameter required.
  Register at https://acartia.io/.
fields:
  - name: latitude / longitude
    meaning: sighting location
  - name: created / type
    meaning: timestamp; sighting type (visual/acoustic)
  - name: trusted
    meaning: cooperative trust flag (use /trusted endpoint as the moderated subset)
  - name: data_source_id / entry_id
    meaning: upstream feed and record id (for dedupe)
time_coverage: "2020-present (prototype Phase 1 2020-22; ongoing)"
spatial_coverage: "Northern CA to northern BC; filter to San Juan bbox"
adapter_contract:
  stream_name: acartia_sightings
  record_shape:
    t: ISO8601
    id: "acartia:{entry_id}"
    latitude: float
    longitude: float
    type: string
    cross_validation: "likely (only the /trusted, moderator-approved subset counts as confirmed for community-origin rows)"
    license: "CC (confirm variant)"
  cadence: "real-time + archive"
integrity_condition: external_validation
risks:
  - "Community-origin: per the project rule, only moderator-approved (/trusted) rows count as confirmed; map the rest to unconfirmed."
  - "Strongly effort-confounded (social-media-driven; effort grew with platform adoption) - validation/social overlay only, never temporal kernels."
  - "Mixes visual and acoustic types and re-broadcasts Orca Network/Conserve - dedupe against Orca Network and the wired community queue."
  - "API endpoints are community-maintained (web3 prototype); confirm stability and CC variant."
next_action: "Register for an Acartia API key; pull the /trusted subset for the San Juan bbox as moderated community validation; dedupe vs Orca Network."
decision_label: needs_user_account
priority: P1
already_wired: false
literature_grounding:
  - citation: "Olson, J.K., Wood, J., Osborne, R.W., Barrett-Lennard, L., Larson, S. 2018. Endangered Species Research 37:105-118. doi:10.3354/esr00918. VERIFIED."
    mechanism: "Directly characterises opportunistic community SRKW sightings (e.g. Orca Network postings) as effort-biased; the same caveat fixes Acartia in the validation/social role."
  - citation: "Thornton et al. 2022, DFO CSAS Res. Doc. 2022/037. VERIFIED."
    mechanism: "Provides the effort-corrected habitat baseline against which near-real-time community sightings are scored, rather than fitted."
```

### 7. BCCSN / Ocean Wise Sightings Network (WhaleReport)

```yaml
source: BC Cetacean Sightings Network (BCCSN) / Ocean Wise Sightings Network (OWSN), WhaleReport
purpose: >
  22+ year curated cetacean sightings database for BC + WA waters (primary occurrence source for BC
  waters), feeding the WhaleReport Alert System. Held-out validation, especially for the Canadian/
  northern side of the Salish Sea where US sources thin out.
availability: research_request_required
account_needed: researcher_request
license: >
  Ocean Wise-owned; quality-checked. Data subsets released for academic/conservation use via a data
  request form; sensitive/personal fields withheld.
endpoint_or_access_path: >
  Data request: sightings@ocean.org (complete the OWSN data request form). Public reporting via the
  WhaleReport app; WRAS alert access restricted to commercial mariners (not a data source).
fields:
  - name: latitude / longitude
    meaning: sighting location
  - name: datetime
    meaning: sighting date/time
  - name: species / count
    meaning: cetacean species (incl. SRKW) and group size
  - name: quality_flag
    meaning: Ocean Wise staff quality-check status
time_coverage: "~2000-present (BCCSN since ~2002; opportunistic records back to 1975 via partners)"
spatial_coverage: "British Columbia + Washington State (Salish Sea, esp. Canadian waters)"
adapter_contract:
  stream_name: owsn_bccsn_sightings
  record_shape:
    t: ISO8601
    id: "owsn:{id}"
    latitude: float
    longitude: float
    species: string
    cross_validation: "verified|likely (Ocean Wise quality-check)"
    license: "Ocean Wise - request terms"
  cadence: "event-based (on request as subset)"
integrity_condition: external_validation
risks:
  - "Effort-confounded opportunistic citizen-science (effort grew with WhaleReport adoption; >20k alerts) - validation/s_space only."
  - "Research-request gated; release is a subset with terms, not bulk."
  - "Overlaps TWM Orca Master (TWM ingests BCCSN 1975-2022) and Acartia - dedupe carefully."
next_action: "Email sightings@ocean.org and complete the OWSN data request form for SRKW (Orcinus orca) sightings in the Salish Sea; clarify reuse terms."
decision_label: needs_research_request
priority: P1
already_wired: false
literature_grounding:
  - citation: "Thornton et al. 2022, DFO CSAS Res. Doc. 2022/037. VERIFIED."
    mechanism: "A DFO/Canada-context effort-corrected SRKW habitat study; BCCSN/OWSN is the Canadian-waters occurrence stream that complements it for the northern Salish Sea s_space."
  - citation: "Olson, J.K., Wood, J., Osborne, R.W., Barrett-Lennard, L., Larson, S. 2018. Endangered Species Research 37:105-118. doi:10.3354/esr00918. VERIFIED."
    mechanism: "Names BCCSN/Ocean Wise (Coastal Ocean Research Institute) as a contributing opportunistic source to Orca Master; same effort-bias caveat -> validation role."
```

### 8. Orca Network Whale Sighting Network

```yaml
source: Orca Network Whale Sighting Network
purpose: >
  High-volume, staff-vetted Salish Sea sightings (Facebook community, website, calls, email).
  Dominant near-real-time WA feed (>75% of WA WRAS sightings in Apr 2024 came via Orca Network).
  Validation/social overlay; also an s_space contributor after effort correction.
availability: research_request_required
account_needed: researcher_request
license: >
  Orca Network-owned, vetted records shared with researchers/partners; no open bulk-export license.
  Re-broadcast into Acartia under that cooperative's CC license.
endpoint_or_access_path: >
  No native structured bulk API. Practical programmatic path: Acartia (Orca Network feeds in via
  Conserve.io/Acartia). Direct historical export: request to Orca Network (info via
  orcanetwork.org). Public artifacts: monthly summaries, sightings archives (since Apr 2001),
  annual PDF reports.
fields:
  - name: date/time
    meaning: vetted sighting timestamp
  - name: location (descriptive / coordinates)
    meaning: sighting place (often descriptive; geocoding needed)
  - name: species / pod
    meaning: species and (when known) SRKW pod
  - name: vetting_status
    meaning: staff/expert cross-check outcome
time_coverage: "2001-present (archives); real-time ongoing"
spatial_coverage: "Salish Sea / Puget Sound (WA-centric)"
adapter_contract:
  stream_name: orca_network_sightings
  record_shape:
    t: ISO8601
    id: "orcanet:{id}"
    latitude: float
    longitude: float
    pod: string|null
    cross_validation: "likely (staff-vetted); community-origin -> requires moderator approval to count"
    license: "Orca Network / via Acartia CC"
  cadence: "real-time + archive"
integrity_condition: external_validation
risks:
  - "Effort-confounded social-media-driven reporting (Olson et al. 2018 explicitly cite Orca Network email postings as an Orca Master source) - validation/social only."
  - "No native structured export; descriptive locations need geocoding; cleanest access is indirect via Acartia."
  - "Heavy overlap with Acartia, TWM, BCCSN - dedupe to prevent validation leakage."
next_action: "Prefer pulling Orca Network records through the Acartia /trusted endpoint (moderated); for full historical export, request structured data + reuse terms from Orca Network."
decision_label: needs_research_request
priority: P1
already_wired: false
literature_grounding:
  - citation: "Olson, J.K., Wood, J., Osborne, R.W., Barrett-Lennard, L., Larson, S. 2018. Endangered Species Research 37:105-118. doi:10.3354/esr00918. VERIFIED."
    mechanism: "Lists Orca Network email postings among the 5 Orca Master source classes and as opportunistic/effort-biased; fixes Orca Network in validation/social, never temporal kernels."
  - citation: "Thornton et al. 2022, DFO CSAS Res. Doc. 2022/037. VERIFIED."
    mechanism: "Effort-corrected habitat baseline for scoring Orca Network sightings against modelled s_space."
```

### 9. DFO/NOAA line-transect surveys (SWFSC ORCAWALE / CalCurCEAS)

```yaml
source: NOAA SWFSC line-transect cetacean surveys (ORCAWALE 1996/2001/2008, CalCurCEAS, etc.)
purpose: >
  The one visual SRKW-relevant source with KNOWN, recorded effort (line-transect tracks), so it is
  the cleanest input for an effort-corrected s_space and for design-based validation - the effort
  offset is measured, not inferred. Cetacean sightings + on-effort track segments.
availability: public_download
account_needed: none
license: >
  CC0 (no rights reserved) for the SWFSC OBIS-SEAMAP datasets observed (e.g. ORCAWALE 2008 ID 1065,
  2001 ID 1047). Shared with GBIF and OBIS.
endpoint_or_access_path: >
  OBIS-SEAMAP SWFSC contributor page; per-cruise dataset pages e.g.
  https://seamap.env.duke.edu/dataset/1065/html (ORCAWALE 2008, DOI 10.82144/3424d523),
  /dataset/1047 (ORCAWALE 2001). NOAA Fisheries: "Ship-based Cetacean and Ecosystem Assessment
  Surveys in the California Current" landing page links the downloads. Effort tracks downloadable.
fields:
  - name: event
    meaning: "S = marine mammal sighting (t/p = turtle/pinniped)"
  - name: datetime / lat / lon
    meaning: sighting time and vessel position
  - name: cruise / sightno
    meaning: SWFSC cruise number and within-cruise sighting id
  - name: species/stock
    meaning: identified cetacean species/stock
  - name: effort track (separate layer)
    meaning: daily/intra-daily on-effort transect start/end - the effort offset
time_coverage: "1991-present, summer/fall cruises (ORCAWALE 1996, 2001, 2008; CalCurCEAS 2014; ...)"
spatial_coverage: "US West Coast out to ~300 nm (US-Canada to US-Mexico); incl. WA outer coast"
adapter_contract:
  stream_name: swfsc_line_transect
  record_shape:
    t: ISO8601
    id: "swfsc:{cruise}:{sightno}"
    latitude: float
    longitude: float
    species_stock: string
    on_effort: bool
    cross_validation: verified
    license: "CC0"
    effort_track_ref: string
  cadence: "periodic survey snapshots"
integrity_condition: spatial_covariate
risks:
  - "COVERAGE CAVEAT: ORCAWALE/CalCurCEAS transects are the outer continental shelf/offshore, NOT the Salish Sea interior where SRKW concentrate in summer; SRKW detections on these lines are sparse. Best for offshore/winter context, not the San Juan pilot bbox."
  - "Even with known effort, this is a design-based survey: use the effort track properly (it is a true offset, unlike the opportunistic sources)."
  - "Summer/fall, daytime, large-vessel - still a defined detection function, but not 24/7."
next_action: "Download the SWFSC OBIS-SEAMAP cruises (CC0) with their effort tracks; clip to a wider Salish Sea+approaches region; use as the effort-known anchor for s_space and as design-based validation, noting the offshore coverage limit."
decision_label: can_get_now
priority: P2
already_wired: false
literature_grounding:
  - citation: "Thornton et al. 2022, DFO CSAS Res. Doc. 2022/037. VERIFIED."
    mechanism: "Combines survey + sightings with effort correction for SRKW habitat; line-transect surveys with measured effort are the methodological ideal this lane points to for an honest s_space and effort offset."
  - citation: "Olson, J.K., Wood, J., Osborne, R.W., Barrett-Lennard, L., Larson, S. 2018. Endangered Species Research 37:105-118. doi:10.3354/esr00918. VERIFIED."
    mechanism: "Contrasts opportunistic (effort-biased) data with systematic surveys; line-transect data is the systematic counterpart whose known effort the opportunistic sources lack."
```

### 10. salishsea.io nightly Darwin Core Archive (aggregator) [bonus]

```yaml
source: salishsea.io (2025 project) - nightly Darwin Core Archive
purpose: >
  Regional aggregator publishing a nightly DwC-A (with GeoParquet sidecar + sha256 checksums)
  cross-referencing iNaturalist, Conserve/Orca Network, and Happywhale for Salish Sea cetaceans.
  Convenient single, provenance-tracked snapshot for held-out validation.
availability: public_download
account_needed: none
license: >
  Per-record provenance preserved (providers, collections, contributors); upstream licenses apply
  (iNaturalist/Happywhale CC variants). Confirm aggregate reuse terms in docs/data-provenance.md.
endpoint_or_access_path: >
  https://salishsea.io/dwca/ (nightly DwC-A + GeoParquet + checksums).
fields:
  - name: decimalLatitude / decimalLongitude
    meaning: occurrence location
  - name: eventDate
    meaning: observation date
  - name: scientificName
    meaning: species id
  - name: provenance fields
    meaning: provider/collection/contributor attribution (see docs/data-provenance.md)
time_coverage: "Aggregated upstream coverage; project started 2025"
spatial_coverage: "Salish Sea"
adapter_contract:
  stream_name: salishsea_io_dwca
  record_shape:
    t: ISO8601
    id: "salishsea_io:{occurrenceID}"
    latitude: float
    longitude: float
    cross_validation: "verified|likely (inherit from upstream provider)"
    license: "inherit upstream"
    provider: string
  cadence: "nightly snapshot"
integrity_condition: external_validation
risks:
  - "Aggregator: 100% overlap with iNaturalist (already wired), Happywhale, Orca Network/Conserve - cannot be treated as independent; dedupe by occurrenceID/provider before validation."
  - "New (2025) project; confirm stability and aggregate license."
  - "Effort-confounded upstream - validation only."
next_action: "Evaluate the nightly DwC-A as a convenience snapshot only; do not use as an independent validation set given upstream overlap."
decision_label: not_worth_it  # convenient but fully derivative of already-covered sources
priority: P2
already_wired: false
literature_grounding:
  - citation: "Olson, J.K., Wood, J., Osborne, R.W., Barrett-Lennard, L., Larson, S. 2018. Endangered Species Research 37:105-118. doi:10.3354/esr00918. VERIFIED."
    mechanism: "Aggregated opportunistic occurrence inherits the effort bias of its sources; validation role only."
```

---

## Already-wired sources (for reference; not new this lane)

Per the charter exit bar, sources already implemented in `src/aws_backend/sources/`:

```yaml
- source: OBIS (api.obis.org occurrence backbone)
  adapter: src/aws_backend/sources/obis.py (LiveObisAdapter) + local_obis.py (seed)
  source_name: obis_verified
  role: external_validation  # has fetch_validation_records(); quality_grade=verified
  already_wired: true
  note: "Distinct from the OBIS-SEAMAP portal (#4) and GBIF (#5), which it partly aggregates; dedupe new pulls against this."
- source: iNaturalist
  adapter: src/aws_backend/sources/inaturalist.py (INaturalistAdapter)
  source_name: inaturalist
  role: external_validation  # photo-backed; research-grade -> higher reliability
  already_wired: true
  note: "Also flows into GBIF (#5) and salishsea.io (#10) - dedupe to avoid validation leakage."
- source: Community submissions (moderation queue)
  adapter: src/aws_backend/sources/community.py (CommunitySubmissionAdapter)
  source_name: community
  role: external_validation (social/citizen-science)
  already_wired: true
  note: "Only status=approved (moderator-approved) rows are emitted - matches the project rule that community rows require moderator approval to count as confirmed."
```

---

## Honesty notes (apply to every source above)

- **Effort bias (Olson et al. 2018):** every opportunistic source here (CWR, TWM, Happywhale,
  OBIS-SEAMAP opportunistic subsets, GBIF, Acartia, BCCSN/OWSN, Orca Network, salishsea.io) is
  presence-only with structured observer-effort bias (more observers near whale-watch ports,
  ferry routes, in daylight, in summer; Olson et al. show ~3x sightings growth after 1995 from
  added effort, not abundance). They are **held-out validation and `s_space` only**; they must not
  estimate `k_tide`, `k_diel`, `k_lunar`, or `k_season`.
- **The one effort-known exception** is the line-transect surveys (#9): effort is measured as the
  transect track, so it is the cleanest s_space/effort-offset input - but its coverage is the
  outer coast, not the San Juan pilot interior, so it corroborates rather than replaces the
  inland opportunistic record.
- **Independence for validation:** these sources heavily cross-feed (TWM ingests Orca Network +
  BCCSN; Acartia re-broadcasts Orca Network; GBIF + salishsea.io aggregate iNaturalist + OBIS +
  Happywhale; the wired `obis_verified` overlaps OBIS-SEAMAP + GBIF). Dedupe by occurrenceID /
  DOI / provider before any held-out scoring, or the "held-out" set leaks into training.
- **Confirmed-sighting rule:** count a row as confirmed only when `cross_validation` is
  `verified` or `likely`; community-origin rows (Acartia non-`/trusted`, Orca Network unvetted,
  the `community` queue) require moderator approval first.
- **Research only:** nothing here was ingested; no adapters were written, no accounts created, no
  data pulled, no git actions taken. Account/research-request actions are listed as `next_action`
  for the user, not performed.
