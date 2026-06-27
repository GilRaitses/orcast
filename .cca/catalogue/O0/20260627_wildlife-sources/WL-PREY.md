# WL-PREY: Chinook / salmonid prey index sources for `k_salmon`

Lane: WL-PREY (wildlife-source research waveset, O0). Model role: `k_salmon` prey covariate
in `log lambda(x,t)` (`docs/methodology/FORECAST_KERNELS.md` section "The kernels" / study 5).
Integrity condition for every source below: `prey_covariate`.

Research only. No ingest, no writes to any store, no commits. This file is the only output.

## Honesty framing (read first)

- The live `k_salmon` covariate today is a **climatology placeholder**, not a validated feed.
  `src/aws_backend/sources/salmon.py` defines a double-Gaussian day-of-year run-timing curve
  (`_climatology_series`) that is returned whenever the Albion and DART live fetchers fail. The
  module docstring states the Albion/DART endpoints and payload parsers are "best-effort and
  UNCONFIRMED." This is why M-L3 (the salmon lag scan) stays withheld: a climatology fallback is
  not an ecological covariate, it is a seasonal prior with zero between-year information.
- "Already wired" below means an adapter path exists in the repo, **not** that it returns
  validated data. The Albion and DART adapters are wired (`ingest_timeseries.py` ->
  `SalmonRunAdapter.fetch_run_index`) but run on unconfirmed parsers and silently fall through to
  climatology. Replacing the placeholder means confirming a real parse, not adding a new adapter.
- Lag structure is an open question for every prey source (FORECAST_KERNELS.md "Open decisions":
  "Salmon data source and license; lag structure"). An upriver/test-fishery count leads local SRKW
  presence in the San Juans by a stock- and gear-dependent lag; a coast-wide annual index has no
  within-season timing at all. Each source below notes its native timing and the lag question.
- Diet/GSI work (Hanson et al.) is included as a **stock-weighting and species-selectivity anchor**,
  not as a daily feed. It tells you *which* Chinook stocks to weight (Fraser-heavy in summer), which
  determines which run-timing series the `k_salmon` index should track.

## Ranked summary (top recommended Chinook index sources)

Ranked by directness as a *within-season run-timing* covariate for SRKW summer presence in the
Salish Sea, weighted by the GSI evidence that SRKW summer Chinook are ~80-90% Fraser-origin.

| Rank | Source | Role for `k_salmon` | Availability | Replaces placeholder? | Priority |
|------|--------|---------------------|--------------|-----------------------|----------|
| 1 | DFO Albion Chinook test fishery (Fraser, via PSC) | Daily Fraser Chinook run-timing CPUE — the most diet-relevant within-season signal | public_download (CSV/xlsx) + public_scrape | YES — directly replaces the Fraser leg of the placeholder | P0 |
| 2 | Pacific Salmon Commission Fraser Panel test fishing (Qualark/Mission/marine approaches) | Broader Fraser in-river timing + passage; backs/extends Albion | public_download + public_scrape | YES — corroborates/extends Fraser leg | P0/P1 |
| 3 | Columbia Basin Research DART (Bonneville adult passage) | Daily Columbia Chinook passage — secondary basin, scriptable API-style link | public_download (scriptable query link) | YES — directly replaces the Columbia leg of the placeholder | P0 |
| 4 | PSC Chinook Technical Committee (CTC) abundance indices | Coast-wide / AABM annual age-3+ abundance index — the index the SRKW literature uses | public_download (xlsx) + data request | Partial — adds real between-year level, not within-season timing | P1 |
| 5 | PFMC Ad Hoc SRKW Workgroup Chinook abundance index (NOF, age-3+, seasonal) | SRKW-purpose-built seasonal/area abundance index tied to SRKW demography | public_download (PDF + report tables) | Partial — seasonal-block level, needs digitizing | P1 |
| 6 | WDFW SCoRE / SaSI escapement (Puget Sound Chinook) | Puget Sound stock escapement — the 6-14% Puget-origin diet fraction; annual | public_scrape_required (+ data.wa.gov) | No (annual escapement, not run-timing) — context/weighting | P2 |
| 7 | Fish Passage Center adult dam counts (Columbia/Snake) | Independent cross-check on DART (same underlying counts) | public_download (query) | No — QA/redundancy for source 3 | P2 |
| 8 | Hanson et al. GSI diet record (stock composition) | Defines *which* stocks/season to weight; not a feed | research record / published tables | No — calibration anchor for the index weighting | P1 |

Bottom line: **sources 1, 2, and 3 are the ones that directly replace the `salmon.py`
climatology placeholder** (Albion+PSC for the Fraser leg, DART for the Columbia leg). Sources 4
and 5 add a real between-year abundance level (the literature's actual SRKW driver) but at annual
or seasonal-block resolution, so they complement rather than replace the daily timing curve.
Sources 6-8 are weighting/QA/context.

---

## Sources

### 1. DFO Albion Chinook test fishery (Fraser River)

```yaml
source: DFO Albion Chinook test fishery (Fraser River), distributed via Pacific Salmon Commission
purpose: Daily within-season Chinook run-timing index for the Fraser River, the dominant origin of SRKW summer Chinook prey; primary k_salmon timing signal.
availability: public_download
account_needed: none
license: Government of Canada / DFO + PSC data; open for use with attribution to DFO and PSC (confirm exact reuse terms on PSC test-fishing page before bulk ingest).
endpoint_or_access_path: |
  PSC test fishing hub: https://www.psc.org/publications/fraser-panel-in-season-information/test-fishing-results/
  - "All Test Fishing Summary" year-to-date spreadsheet (downloadable .xlsx/.csv of daily catches).
  - Daily Test Fishing Calendar (per-day reports) and per-fishery year-to-date pages.
  - Test Fishing Archive: per-year pages back to 2000.
  DFO program page (referenced by salmon.py): https://www.pac.dfo-mpo.gc.ca/fm-gp/fraser/index-eng.html
  DFO Fishery Notices (FN bulletins) carry in-season Albion CPUE narrative.
fields:
  - name: date
    meaning: Calendar date of the test set (daily during the run season).
  - name: cpue / catch
    meaning: Chinook catch-per-unit-effort (catch per set or per standardized gillnet drift) at Albion.
  - name: fishery / location
    meaning: Test fishery site (Albion gillnet on the lower Fraser; PSC also lists Qualark, Mission, marine-approach sites).
  - name: species / run
    meaning: Species (Chinook) and, where applicable, run/stock-group attribution.
time_coverage: Seasonal, roughly spring through fall; annual archives back to ~2000. Daily resolution within season.
spatial_coverage: Lower Fraser River at Albion (point/in-river); represents Fraser aggregate run passing the lower river.
adapter_contract:
  stream_name: salmon_run_index (fraser leg)
  record_shape: {t: ISO-date, fraser_index: float[0-1], columbia_index: float|null, run_index: float[0-1], source: "albion", source_url: string}
  cadence: daily during run season; annual backfill from archive pages
integrity_condition: prey_covariate
already_wired: true
risks:
  - Already wired in salmon.py but on an UNCONFIRMED parser; the live _fetch_fraser path expects a JSON payload the site does not serve (it publishes HTML tables / xlsx), so it currently fails and falls back to climatology. Replacing the placeholder requires confirming the real download (xlsx/CSV) schema and per-year archive URLs, not adding a new adapter.
  - Test-fishery CPUE is an effort-standardized index, not absolute abundance; gear/protocol changes between years affect comparability.
  - Lag structure: Albion is in-river at the lower Fraser; SRKW intercept Fraser Chinook in the marine approaches (Juan de Fuca / San Juans) BEFORE the lower-river passage, so Albion likely LAGS local SRKW presence. Marine-approach test fisheries (Area 20/Area 12, listed on PSC page) are better-timed to SRKW interception. Lag must be fit (negative or positive) in the M-L3 scan, not assumed.
next_action: Inspect the PSC "All Test Fishing Summary" xlsx and per-year archive HTML to fix the real daily schema; decide Albion (in-river) vs Area 20/12 (marine approach) as the timing anchor; confirm PSC/DFO reuse terms.
decision_label: can_get_now
priority: P0
literature_grounding:
  citation: "Hanson, M.B., R.W. Baird, J.K.B. Ford, et al. 2010. Species and stock identification of prey consumed by endangered southern resident killer whales in their summer range. Endangered Species Research 11:69-82. doi:10.3354/esr00263."
  verified: true
  mechanism: "Of Chinook prey sampled in the SRKW summer range, 80-90% were inferred to originate from the Fraser River (only 6-14% Puget Sound), with Upper/Middle Fraser, South Thompson, and Lower Fraser stocks sequentially important through the summer. This is the empirical basis for making a Fraser run-timing series the primary k_salmon signal."
```

### 2. Pacific Salmon Commission — Fraser River Panel test fishing (Qualark / Mission / marine approaches)

```yaml
source: Pacific Salmon Commission, Fraser River Panel in-season test fishing program (Qualark gillnet, Mission hydroacoustic passage, Area 20/Area 12 marine-approach test fisheries)
purpose: Broader, multi-site Fraser run-timing and passage estimate that corroborates and extends the single Albion station; the marine-approach sites are timed closer to SRKW interception.
availability: public_download
account_needed: none
license: PSC data; attribution to PSC (and DFO for jointly operated fisheries) required; confirm exact reuse terms on the test-fishing page.
endpoint_or_access_path: |
  https://www.psc.org/publications/fraser-panel-in-season-information/test-fishing-results/
  - Daily Test Fishing Results (yesterday's catch across all active test fisheries).
  - Per-fishery year-to-date pages: Qualark Gillnet, Brownsville Bar, Area 20 Gillnet/Seine (San Juan), Area 12 Gillnet/Seine, Whonnock, U.S. Area 7 Reef Net.
  - "Test fishing data along with Mission passage data" in-season application.
  - Archive pages per year (2000-present).
fields:
  - name: date
    meaning: Daily test set date.
  - name: fishery_site
    meaning: Test fishery location (in-river vs marine approach).
  - name: cpue / catch / passage
    meaning: Chinook catch or, for Mission, hydroacoustic in-river passage estimate.
  - name: species
    meaning: Species split (Chinook focus; sockeye/chum also reported).
time_coverage: Seasonal in-season (typically summer Fraser Panel window), annual archives 2000-present, daily resolution.
spatial_coverage: Fraser River in-river (Qualark, Mission) and marine approaches off southern Vancouver Island / San Juan area (Area 20, Area 12, Area 7).
adapter_contract:
  stream_name: salmon_run_index (fraser corroboration / marine-approach leg)
  record_shape: {t: ISO-date, site: string, fraser_index: float[0-1], run_index: float[0-1], source: "psc_fraser_panel", source_url: string}
  cadence: daily during in-season; annual archive backfill
integrity_condition: prey_covariate
already_wired: false
risks:
  - No stable documented API; data is HTML tables + downloadable spreadsheets that vary by year (scrape/parse required).
  - Fraser Panel test fishing is focused on the sockeye/pink management window in some years; Chinook coverage and timing vary — verify Chinook is reported per-site per-year.
  - Mission is a passage (abundance-through-a-point) estimate, not CPUE; do not mix units with Albion CPUE without normalizing (the salmon.py min-max-within-season normalization partly handles this but cross-site fusion needs care).
  - Lag structure: marine-approach sites (Area 20/12) intercept Chinook nearer the SRKW foraging window, so they are better timing anchors than lower-river sites; quantify lag per site in M-L3.
next_action: Catalogue which sites report Chinook per year and in what units; prototype a parser against one archive year (e.g., 2023) for Area 20 + Qualark; compare timing to Albion.
decision_label: can_get_now
priority: P1
literature_grounding:
  citation: "Ford, J.K.B. and G.M. Ellis. 2006. Selective foraging by fish-eating killer whales Orcinus orca in British Columbia. Marine Ecology Progress Series 316:185-199. doi:10.3354/meps316185."
  verified: true
  mechanism: "Resident killer whale groups across the study area foraged selectively for Chinook (largest, highest-lipid, year-round-available salmonid) over far more abundant sockeye/pink; selectivity influences seasonal movements. This justifies tracking Chinook-specific run timing (not total salmon) and weighting marine-approach interception timing for k_salmon."
```

### 3. Columbia Basin Research — DART adult passage, Bonneville Dam (Chinook)

```yaml
source: Columbia Basin Research (University of Washington) DART - Adult Passage Counts Daily, Bonneville Dam (BON), Chinook
purpose: Secondary-basin daily Chinook run-timing/abundance signal (Columbia), used as the columbia_index leg and as a cross-check on the Fraser signal.
availability: public_download
account_needed: none
license: DART data is publicly accessible; CBR requests acknowledgement of Columbia River DART and underlying source (Fish Passage Center / USACE) in publications. Confirm citation text before publishing derived products.
endpoint_or_access_path: |
  Query UI: https://www.cbr.washington.edu/dart/query/adult_daily
  Scriptable: set Project=BON-Bonneville, Species=Chinook, Year, optional Chinook Run (Spring/Summer/Fall), check "Generate Query Result Link Only" -> yields a direct CSV query URL usable from scripts (this is DART's API-style access).
  Overview confirms: daily loads ~05:30-08:30 daily; data span 1879-present; primary source Fish Passage Center; CSV/spreadsheet output + scriptable link.
fields:
  - name: date
    meaning: Count date (daily visual adult ladder counts).
  - name: chinook (count)
    meaning: Adult Chinook passage count at Bonneville fish ladders; optionally split by run (spring/summer/fall).
  - name: project
    meaning: Dam code (BON for Bonneville; McNary, Lower Granite, etc. also available).
time_coverage: Bonneville adult counts from 1938 (DART overall 1879-present); daily resolution; updated daily in-season.
spatial_coverage: Bonneville Dam, lower Columbia River (single passage point integrating the upriver Columbia/Snake Chinook run).
adapter_contract:
  stream_name: salmon_run_index (columbia leg)
  record_shape: {t: ISO-date, fraser_index: null, columbia_index: float[0-1], run_index: float[0-1], source: "dart", source_url: string}
  cadence: daily; annual backfill via per-year query links
integrity_condition: prey_covariate
already_wired: true
risks:
  - Already wired in salmon.py (_fetch_columbia) but with UNCONFIRMED params; the code requests outputFormat=csvSingle then calls response.json(), a mismatch (CSV vs JSON), so the live path fails and falls back to climatology. Replacing the placeholder requires switching to the real "Generate Query Result Link Only" CSV endpoint and parsing CSV, plus pinning the per-year query string.
  - Columbia Chinook are a SECONDARY diet source for SRKW summer presence (GSI: ~6.5% Fraser vs 53.6% Columbia in OUTER-COAST winter/spring samples, but Fraser dominant in the Salish Sea summer range). Bonneville passage is most relevant to SRKW outer-coast winter/spring occurrence, not San Juan summer presence — label the role and lag accordingly.
  - Visual ladder counts have begin/end count dates that vary by year; off-season gaps are real zeros vs not-counted — handle explicitly.
next_action: Replace the JSON assumption with the DART CSV scriptable link; pin BON+Chinook per-year URL; decide whether Columbia feeds an outer-coast/winter k_salmon term distinct from the Salish-Sea-summer Fraser term.
decision_label: can_get_now
priority: P0
literature_grounding:
  citation: "Hanson, M.B., C.K. Emmons, M.J. Ford, et al. 2021. Endangered predators and endangered prey: Seasonal diet of Southern Resident killer whales. PLOS ONE 16(3):e0247031. doi:10.1371/journal.pone.0247031."
  verified: true
  mechanism: "In outer-coast (WA/OR/CA) winter-spring samples, Columbia River Chinook were the single largest stock group (53.6%) of identifiable Chinook prey, vs Central Valley 19.0%, Puget Sound 14.2%, Fraser 6.5%. This grounds the Columbia/Bonneville signal as the prey index for SRKW outer-coast/non-summer occurrence, distinct from the summer Fraser signal."
```

### 4. Pacific Salmon Commission — Chinook Technical Committee (CTC) abundance indices

```yaml
source: Pacific Salmon Commission, Chinook Technical Committee (CTC) Exploitation Rate Analysis / abundance indices (TCCHINOOK series + CTC Data Sets)
purpose: Coast-wide / aggregate-abundance-based-management (AABM) annual age-3+ Chinook abundance indices — the actual abundance index the SRKW survival literature correlates against (Ford et al. 2010, Ward et al. 2009). Provides real between-year level for k_salmon.
availability: public_download
account_needed: none
license: CTC data; "the CTC must be acknowledged in any presentations or publications"; some data only via data-request form to the Salmon Coordinator. Confirm per-dataset terms.
endpoint_or_access_path: |
  Reports hub: https://www.psc.org/publications/technical-reports/technical-committee-reports/chinook/
  Data sets (xlsx): https://www.psc.org/publications/technical-reports/technical-committee-reports/chinook/ctc-data-sets/
    - e.g. "TCCHINOOK (23)-04 Abundance indices stock composition for AABM fisheries" (.xlsx + visualization app).
  Memos/summary reports: annual Model Calibration memo (by April 1) + Commissioner Summary Report (catch/escapement, ERA, abundance projections).
fields:
  - name: year
    meaning: Brood/return year of the abundance index.
  - name: aabm_abundance_index
    meaning: Aggregate abundance index for AABM fisheries (SEAK, NBC, WCVI) — the PSC "Chinook abundance index" form used in SRKW analyses.
  - name: stock_composition
    meaning: Stock-group composition contributing to each AABM index.
  - name: escapement / exploitation_rate
    meaning: Catch, escapement, and exploitation-rate indicators per stock.
time_coverage: Annual; long historical series (calibration model spans decades; reports back through 1990s-2000s).
spatial_coverage: Coast-wide PSC Treaty area, resolved to AABM fishery regions (Southeast Alaska, Northern BC, West Coast Vancouver Island) and indicator stocks.
adapter_contract:
  stream_name: salmon_abundance_index_annual
  record_shape: {year: int, region: string, abundance_index: float, stock_group: string, source: "psc_ctc"}
  cadence: annual (one value per year per region/stock); manual/scheduled pull on report release
integrity_condition: prey_covariate
already_wired: false
risks:
  - Annual resolution only — gives between-year prey level, NOT within-season run timing. It complements (does not replace) the daily Albion/DART timing curve; in the model it would enter as a slowly varying yearly scalar on k_salmon, not the daily shape.
  - Some datasets require a data-request form; published xlsx coverage varies by report year.
  - The WCVI AABM index is the specific index Ward et al. 2009 used as the SRKW prey proxy; pin the exact index column to match the literature rather than a generic "abundance index."
next_action: Pull the latest TCCHINOOK AABM abundance-indices xlsx; identify the WCVI/coast-wide column matching the SRKW literature; define an annual scalar covariate distinct from the daily timing series.
decision_label: can_get_now
priority: P1
literature_grounding:
  citation: "Ford, J.K.B., G.M. Ellis, P.F. Olesiuk, and K.C. Balcomb. 2010. Linking killer whale survival and prey abundance: food limitation in the oceans' apex predator? Biology Letters 6(1):139-142. doi:10.1098/rsbl.2009.0468."
  verified: true
  mechanism: "Across 25 years, resident killer whale population trends were driven by survival, and survival was strongly correlated with coast-wide Chinook abundance (the PSC-type abundance index), to the degree that Chinook is a limiting factor. This is the canonical evidence that an annual Chinook abundance index belongs in the SRKW prey term."
```

### 5. PFMC Ad Hoc SRKW Workgroup — Chinook abundance index (North of Cape Falcon, age-3+, seasonal)

```yaml
source: Pacific Fishery Management Council, Ad Hoc Southern Resident Killer Whale Workgroup, Report 1 (2020) — annual indices of adult (age-3+) Chinook abundance by ocean area and seasonal breakpoints
purpose: SRKW-purpose-built Chinook abundance index, constructed specifically to relate Chinook abundance (especially North of Cape Falcon, NOF) to SRKW demographic rates; the closest published index to the exact covariate k_salmon wants.
availability: public_download
account_needed: none
license: U.S. Government work (PFMC/NOAA), public domain; cite PFMC SRKW Workgroup Report. Underlying model inputs (FRAM/CTC) carry their own attribution.
endpoint_or_access_path: |
  SRKW Workgroup Report 1 (PDF): https://www.pcouncil.org/documents/2020/02/e-3-a-srkw-workgroup-report-1-electronic-only.pdf/
  NOAA event hub (supporting docs, NMFS-NWFSC-123): https://www.fisheries.noaa.gov/event/ad-hoc-southern-resident-killer-whale-workgroup
  Amendment 21 EA (abundance threshold context): https://repository.library.noaa.gov/view/noaa/32082/noaa_32082_DS1.pdf
fields:
  - name: year
    meaning: Year of the abundance index.
  - name: ocean_area
    meaning: Spatial stratum (notably North of Cape Falcon vs South of Cape Falcon).
  - name: season_block
    meaning: One of three seasonal breakpoints used to build the index (within-year seasonality at coarse resolution).
  - name: age3plus_abundance_index
    meaning: Index of adult (age-3+) Chinook abundance available to SRKW in that area/season.
time_coverage: Annual with 3 seasonal blocks; multi-decade reconstruction in the report.
spatial_coverage: PFMC ocean areas off WA/OR/CA, partitioned at Cape Falcon (NOF most relevant to SRKW).
adapter_contract:
  stream_name: salmon_abundance_index_srkw
  record_shape: {year: int, area: string, season: string, abundance_index: float, source: "pfmc_srkw_wg"}
  cadence: annual x 3 seasonal blocks; one-time digitize from report tables, refresh if updated
integrity_condition: prey_covariate
already_wired: false
risks:
  - Published primarily as a report with tables/figures, not a maintained data API; values likely need digitizing from the PDF/appendix (verify whether an accompanying data file exists before assuming).
  - Resolution is annual x 3 seasons, not daily — same caveat as source 4: a level/seasonal-block covariate, not the daily timing shape.
  - NOF index is built for the SRKW *coast-wide/ocean* relationship; its overlap with the Salish-Sea-summer San Juan foraging window is partial — keep the area label explicit and do not silently equate NOF ocean abundance with in-Salish-Sea availability.
next_action: Extract the age-3+ NOF abundance index table from Workgroup Report 1; check for a released data appendix; align its seasonal blocks to the model's k_season/k_salmon time axis.
decision_label: can_get_now
priority: P1
literature_grounding:
  citation: "Ward, E.J., E.E. Holmes, and K.C. Balcomb. 2009. Quantifying the effects of prey abundance on killer whale reproduction. Journal of Applied Ecology 46(3):632-640. doi:10.1111/j.1365-2664.2009.01647.x."
  verified: true
  mechanism: "SRKW fecundity is highly correlated with Chinook abundance: the probability of a female calving was ~50% higher following high-salmon years than low-salmon years, using PSC/PFMC Chinook abundance indices (notably the WCVI index) as the prey proxy. Establishes that a purpose-built SRKW Chinook abundance index is a defensible prey covariate."
```

### 6. WDFW SCoRE / SaSI — Puget Sound Chinook escapement

```yaml
source: Washington Department of Fish & Wildlife - Salmon Conservation and Reporting Engine (SCoRE) + Salmonid Stock Inventory (SaSI); supporting Fish Traps & Surveys (FTS) on data.wa.gov
purpose: Puget Sound Chinook stock escapement (annual) — the ~6-14% Puget-Sound-origin fraction of SRKW summer Chinook diet; a U.S.-side stock-level context/weighting layer.
availability: public_scrape_required
account_needed: none
license: WDFW public data; attribution to WDFW; FTS raw survey data via data.wa.gov under WA open-data terms. Confirm reuse terms for SCoRE-derived escapement estimates.
endpoint_or_access_path: |
  SCoRE: https://fortress.wa.gov/dfw/score/score/index.jsp (Chinook Data by region; escapement estimates).
  Species pages: https://fortress.wa.gov/dfw/score/score/species/species.jsp
  FTS raw spawning-survey data: https://wdfw.wa.gov/fishing/management/fts-data -> data.wa.gov.
  SalmonScape interactive maps for distribution/status (GIS layers downloadable).
fields:
  - name: stock / population
    meaning: Named Puget Sound Chinook population (e.g., Skagit, Snohomish, mid-Sound).
  - name: year
    meaning: Return/spawning year.
  - name: escapement
    meaning: Spawning escapement estimate (and/or redd counts in FTS).
  - name: status
    meaning: SaSI stock status classification (healthy/depressed/critical/etc.).
time_coverage: Annual; multi-decade where surveys exist.
spatial_coverage: Puget Sound and Washington watersheds (in-river spawning grounds), not marine foraging areas.
adapter_contract:
  stream_name: salmon_escapement_annual_ps
  record_shape: {stock: string, year: int, escapement: float, status: string, source: "wdfw_score"}
  cadence: annual; manual pull on data update
integrity_condition: prey_covariate
already_wired: false
risks:
  - Escapement is a terminal/post-season annual count (fish that survived to spawn) — it is NOT run-timing and NOT marine availability; it would enter only as a coarse annual context/weighting term, never the daily k_salmon shape.
  - SCoRE is a web application without a documented bulk API; structured extraction likely requires scraping or the data.wa.gov FTS export.
  - Puget Sound is a minority (~6-14%) of SRKW summer Chinook origin — low weight relative to Fraser.
next_action: Decide whether Puget Sound escapement is worth a coarse weighting term at all given its small diet share; if yes, pull Chinook escapement via data.wa.gov FTS rather than scraping SCoRE.
decision_label: can_get_now
priority: P2
literature_grounding:
  citation: "Hanson, M.B., R.W. Baird, J.K.B. Ford, et al. 2010. Species and stock identification of prey consumed by endangered southern resident killer whales in their summer range. Endangered Species Research 11:69-82. doi:10.3354/esr00263."
  verified: true
  mechanism: "Only 6-14% of summer-range SRKW Chinook prey were inferred to originate from Puget Sound rivers (vs 80-90% Fraser). This bounds Puget Sound escapement as a small-weight stock context layer, not a primary k_salmon driver."
```

### 7. Fish Passage Center — adult salmon dam counts (Columbia/Snake)

```yaml
source: Fish Passage Center (FPC) - Adult Salmon Dam Counts (Columbia and Snake River dams)
purpose: Independent cross-check / QA on the DART Bonneville Chinook counts (DART's primary adult-count source IS the FPC), giving a second access path to the same underlying counts.
availability: public_download
account_needed: none
license: FPC public data; acknowledge Fish Passage Center. Confirm reuse terms before bulk ingest.
endpoint_or_access_path: |
  Adult dam count data query: https://www.fpc.org/webapps/adultsalmon/Q_adultcounts_dataquery.php
  Adult passage hub: https://www.fpc.org/adults/Q_adults_passagedata.php (queries, metadata, RSS feed of daily counts).
  Select site (e.g., Bonneville), species=Chinook (+ Chinook Race), daily counts, start date.
fields:
  - name: date
    meaning: Daily count date.
  - name: chinook (count)
    meaning: Adult Chinook ladder count; can split by race (spring/summer/fall).
  - name: site
    meaning: Dam/reporting site (Bonneville and others, with per-site begin/end count dates).
time_coverage: Daily, multi-decade (per-site begin years vary; metadata file lists coverage).
spatial_coverage: Columbia/Snake mainstem dams (Bonneville most relevant), same passage points as DART.
adapter_contract:
  stream_name: salmon_run_index (columbia QA leg)
  record_shape: {t: ISO-date, columbia_index: float[0-1], run_index: float[0-1], source: "fpc", source_url: string}
  cadence: daily; RSS feed available for current counts
integrity_condition: prey_covariate
already_wired: false
risks:
  - Largely redundant with DART (DART sources its adult counts from FPC); value is QA/redundancy and an alternate parse path, not new information. SOURCE_DECISIONS.md explicitly says "Use DART first; keep FPC as secondary validation only."
  - Query interface is form-driven HTML; the RSS feed is the cleanest machine-readable surface for current counts; historical pulls need the data-query form.
  - Same off-season begin/end-count-date caveat as DART.
next_action: Use only as a validation cross-check against DART for the Bonneville Chinook leg; do not build a primary adapter here.
decision_label: not_worth_it
priority: P2
literature_grounding:
  citation: "Hanson, M.B., C.K. Emmons, M.J. Ford, et al. 2021. Endangered predators and endangered prey: Seasonal diet of Southern Resident killer whales. PLOS ONE 16(3):e0247031. doi:10.1371/journal.pone.0247031."
  verified: true
  mechanism: "Columbia River Chinook were the dominant identifiable stock group (53.6%) in outer-coast winter/spring SRKW diet, so Columbia adult passage counts (whether via DART or FPC) are a legitimate prey signal for the non-summer/outer-coast occurrence component — FPC just provides a redundant access path to the same counts."
```

### 8. Hanson et al. SRKW diet genetic-stock-ID record (stock-weighting anchor)

```yaml
source: SRKW diet / genetic-stock-identification record (Hanson et al. 2010 ESR; Hanson et al. 2021 PLOS ONE) - prey species and Chinook stock composition by season/area
purpose: NOT a daily feed. Defines WHICH Chinook stocks and seasons the k_salmon index should weight (Fraser-dominant in the Salish Sea summer; Columbia/Central Valley/Puget Sound in outer-coast winter/spring), and confirms Chinook (not total salmon) as the prey to track.
availability: public_download
account_needed: none
license: Published open-access / publisher terms (ESR int-res.com; PLOS ONE CC-BY). Underlying sample data may require contacting NWFSC/Cascadia Research.
endpoint_or_access_path: |
  Hanson 2010 ESR PDF: https://www.int-res.com/articles/esr2010/11/n011p069.pdf
  Hanson 2021 PLOS ONE: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0247031
  Cascadia Research listing: https://cascadiaresearch.org/publications/species-and-stock-identification-prey-consumed-endangered-southern-resident-killer/
fields:
  - name: region / season
    meaning: Sampling region (San Juans, W. Strait of Juan de Fuca, outer coast) and season.
  - name: prey_species_fraction
    meaning: Fraction of prey that is Chinook vs other species (Chinook dominant).
  - name: chinook_stock_composition
    meaning: GSI-inferred stock-group percentages (Fraser sub-stocks, Columbia, Puget Sound, Central Valley).
time_coverage: 2004-2008 (2010 paper) extended through later years (2021 paper); not a live time series.
spatial_coverage: SRKW summer range (San Juans / W. Juan de Fuca) and outer-coast WA/OR/CA winter range.
adapter_contract:
  stream_name: prey_stock_weights (static calibration, not a stream)
  record_shape: {region: string, season: string, stock_group: string, fraction: float, se: float, source: "hanson_gsi"}
  cadence: static (published tables); update on new diet publications
integrity_condition: prey_covariate
already_wired: false
risks:
  - This is a calibration/weighting anchor, not a time-varying covariate; misusing it as a feed would be a category error.
  - Sample sizes per stock-group are modest; SEs matter when setting weights.
next_action: Encode the season/area Chinook stock-composition weights as fixed coefficients that decide how Albion/PSC (Fraser) vs DART (Columbia) feed into k_salmon by season; do not ingest as a series.
decision_label: can_get_now
priority: P1
literature_grounding:
  citation: "Hanson, M.B., R.W. Baird, J.K.B. Ford, et al. 2010. Species and stock identification of prey consumed by endangered southern resident killer whales in their summer range. Endangered Species Research 11:69-82. doi:10.3354/esr00263. (extended by Hanson et al. 2021, PLOS ONE 16(3):e0247031, doi:10.1371/journal.pone.0247031.)"
  verified: true
  mechanism: "Direct prey sampling + GSI established Chinook as the overwhelmingly dominant SRKW prey and quantified stock origin by season/area (summer San Juans 80-90% Fraser; outer-coast winter/spring Columbia 53.6%). This is the empirical key that maps each candidate run-timing feed to the correct season/area weight in k_salmon."
```

---

## Verified citation ledger

All citations below were verified by web search against the publisher/primary record during this
research pass (2026-06-27). None are unverified; none are invented.

| Citation | Venue / DOI | Verified | Used for |
|----------|-------------|----------|----------|
| Ford, Ellis, Olesiuk & Balcomb 2010 | Biology Letters 6(1):139-142, doi:10.1098/rsbl.2009.0468 | yes | SRKW survival tracks coast-wide Chinook abundance (sources 1, 4) |
| Ford & Ellis 2006 | Mar. Ecol. Prog. Ser. 316:185-199, doi:10.3354/meps316185 | yes | Strong SRKW selectivity for Chinook over other salmonids (source 2) |
| Hanson et al. 2010 | Endangered Species Research 11:69-82, doi:10.3354/esr00263 | yes | Summer-range GSI: 80-90% Fraser-origin Chinook (sources 1, 6, 8) |
| Hanson et al. 2021 | PLOS ONE 16(3):e0247031, doi:10.1371/journal.pone.0247031 | yes | Seasonal/outer-coast diet: Columbia 53.6% in winter/spring (sources 3, 7, 8) |
| Ward, Holmes & Balcomb 2009 | J. Appl. Ecol. 46(3):632-640, doi:10.1111/j.1365-2664.2009.01647.x | yes | SRKW fecundity ~50% higher in high-Chinook years (source 5) |
| PFMC Ad Hoc SRKW Workgroup 2020 | PFMC Report 1 (Sept 2020, Agenda E.3.a / H.3.a) | yes (PFMC doc) | Age-3+ NOF Chinook abundance index linked to SRKW demography (source 5) |
| PSC Chinook Technical Committee | TCCHINOOK series + CTC Data Sets (psc.org) | yes (PSC site) | Coast-wide/AABM annual Chinook abundance index (source 4) |

Supporting (not quoted as a mechanism but confirms the management threshold): DFO CSAS Science
Advisory Report (2009/2011) found the PSC Chinook abundance index correlates with resident killer
whale survival and that an index value above ~1.1 is associated with population growth. Treat as
corroborating context, verified against the DFO waves-vagues record.

## Exit-bar check (this lane)

- Distinct sources: 8 (>= 6 required).
- Each has availability, access path, license, fields, coverage, k_salmon relevance, and a verified
  citation with mechanism: yes.
- Sources that directly replace the salmon.py climatology placeholder, flagged: #1 Albion (Fraser
  leg), #2 PSC Fraser Panel (Fraser corroboration/marine-approach), #3 DART Bonneville (Columbia
  leg). #1 and #3 are already wired in the repo but on unconfirmed parsers and currently fall
  through to climatology, so "wired" != "validated."
- Lag-structure question noted per source where relevant (Albion in-river lags marine interception;
  marine-approach Area 20/12 better-timed; Columbia relevant to outer-coast/winter, not San Juan
  summer; annual indices carry no within-season timing).
