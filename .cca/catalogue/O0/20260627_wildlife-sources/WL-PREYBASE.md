# WL-PREYBASE: forage fish, pinnipeds, seabirds, productivity — labeled prey-base covariates

Lane: WL-PREYBASE (wildlife-source research waveset, O0). Model role: **prey-base context on the
Chinook prey term**, never the temporal-kernel heat. Each source is labeled explicitly as a
prey-base covariate, a competitor/predator, or an indicator. Integrity condition for every source
below is `prey_covariate` (these are ecological covariates on the Chinook prey base; none is an
effort covariate and none is `detectability_noise` — see honesty framing).

Research only. No ingest, no writes to any store, no commits. This file is the only output. No
prey-base ecosystem source is wired in the repo today (`grep src/aws_backend/sources/` for
herring/seal/sea lion/chlorophyll/upwelling/sand lance/eulachon/auklet/seabird/forage returns
nothing), so every source below is `already_wired: false`.

## Honesty framing (read first)

- **These are not `k_salmon`, and not the heat.** `k_salmon` (WL-PREY) is the Chinook run-timing /
  abundance term. The sources here sit *one trophic step removed* from that term. They contextualize
  *why* Chinook abundance varies, or compete for the same Chinook, or indicate ecosystem state. In
  `log lambda(x,t)` they would enter only as slow covariates that modulate the prey base feeding
  `k_salmon`, or as separate competitor/indicator regressors — never as the acoustic-estimated
  temporal kernels (`docs/methodology/FORECAST_KERNELS.md`, model form).
- **Forage fish are prey of *juvenile* Chinook, not of SRKW.** SRKW eat large adult Chinook
  (Ford & Ellis 2006; WL-PREY). Herring and sand lance feed *juvenile* Chinook in their first
  marine year (Duffy et al. 2010). So a herring/sand-lance signal is a **bottom-up covariate with a
  multi-year lag** (forage-fish year-class -> juvenile Chinook growth/survival -> 2-4 yr later as
  adult Chinook available to SRKW). The lag is long, stock-specific, and must be fit, not assumed.
  Do not treat a herring index as a within-season SRKW driver.
- **Pinnipeds are competitors/predators, not prey.** Harbor seals and sea lions consume Chinook
  (juvenile and adult), reducing the Chinook available to SRKW (Chasco et al. 2017). They enter as a
  negative competitor covariate on the prey base, at annual resolution. They are NOT SRKW prey and
  NOT an effort term.
- **Productivity and seabird-diet sources are indicators**, read as proxies for forage-fish /
  ecosystem state. Satellite chl-a and upwelling indices are bottom-up drivers of the whole system
  with the same multi-year lag to adult Chinook; rhinoceros auklet diet is a sentinel readout of
  forage-fish abundance, not a fish census itself.
- **Spatial mismatch is real.** Most of these series are basin- or coast-scale annual values, not
  San-Juan-summer daily signals. They cannot sharpen a temporal kernel; at best they shift the
  prey-base level across years. Label the area/resolution honestly per source.

## Ranked summary (most defensible prey-base covariates)

Ranked by defensibility as a covariate that legitimately informs the Chinook prey base for the SRKW
forecast, weighting (a) strength of the published trophic link, (b) data availability/cadence, and
(c) honest interpretability of the lag/area.

| Rank | Source | Labeled role | Availability | Cadence / lag | Priority |
|------|--------|--------------|--------------|---------------|----------|
| 1 | NOAA satellite chl-a (CoastWatch/ERDDAP) + CUTI/BEUTI upwelling indices | indicator (bottom-up productivity) | public_api | daily-monthly grids; multi-yr lag to adult Chinook | P1 |
| 2 | NOAA Marine Mammal Stock Assessment Reports (harbor seal, CA + Steller sea lion) | competitor / predator | public_download | annual; competes for current Chinook | P1 |
| 3 | DFO Pacific Herring spawn index / stock assessment (BC, Strait of Georgia) | prey-base covariate (juvenile Chinook forage) | public_download | annual spawn index; multi-yr lag | P1 |
| 4 | WDFW Puget Sound Pacific herring spawning-biomass surveys | prey-base covariate (juvenile Chinook forage) | public_download | annual; multi-yr lag | P2 |
| 5 | DFO harbour seal & Steller sea lion abundance (Olesiuk / CSAS) | competitor / predator (BC side) | public_download | periodic survey years; annual interp | P2 |
| 6 | Rhinoceros auklet colony + diet monitoring (Protection Island; Pearson/Hodum/Good) | indicator (forage-fish sentinel) | research_request_required | annual breeding-season diet | P2 |
| 7 | Pacific sand lance (Ammodytes personatus) abundance | prey-base covariate / indicator | not_found (no directed survey) | n/a — proxy only | P2 |
| 8 | Eulachon (Thaleichthys pacificus) spawning-stock biomass (DFO / CDFW) | indicator (forage-fish / productivity) | public_download | annual; weak direct Chinook link | P2 |

Bottom line: the **most defensible** prey-base covariates are the **ocean-productivity layer (1)**
and the **pinniped competitor layer (2)** — both have direct, named, mechanistic links to the
Chinook available to SRKW and are publicly accessible at usable cadence. The **forage-fish layer
(3-4, herring)** is well-grounded trophically but enters only as a lagged bottom-up term. The
**seabird/sand-lance/eulachon layer (6-8)** is indicator-grade: useful ecosystem context, weakest
as a direct Chinook covariate. None of these is the temporal-kernel heat.

---

## Sources

### 1. NOAA satellite chlorophyll-a + CUTI/BEUTI upwelling indices (ocean productivity)

```yaml
source: NOAA CoastWatch / ERDDAP satellite ocean-color chlorophyll-a (MODIS-Aqua, VIIRS) plus NOAA SWFSC-ERD Coastal Upwelling Transport Index (CUTI) and Biologically Effective Upwelling Transport Index (BEUTI)
purpose: Bottom-up ocean-productivity covariate for the Chinook prey base. Chl-a indexes primary production; CUTI/BEUTI index the nutrient supply that drives it. Both modulate forage availability for juvenile Chinook and therefore later adult-Chinook abundance available to SRKW.
availability: public_api
account_needed: none
license: U.S. Government / public domain (NOAA, NASA ocean color); CUTI/BEUTI free with acknowledgement of NOAA SWFSC Environmental Research Division. Cite Jacox et al. 2018 for the indices.
endpoint_or_access_path: |
  Chl-a (gridded, scriptable): NOAA CoastWatch ERDDAP, e.g. https://coastwatch.pfeg.noaa.gov/erddap/ (griddap datasets erdMH1chla* (MODIS-Aqua), nesdisVHNchla* (VIIRS)); GET CSV/NetCDF by lon/lat/time bbox.
  Upwelling indices: https://oceanview.pfeg.noaa.gov/products/upwelling/cuti and .../beuti ; data files + ERDDAP (erdCUTI, erdBEUTI), daily 1-degree, 31-47N, 1988-present.
  NWFSC "Ocean Ecosystem Indicators" (synthesis context): https://www.fisheries.noaa.gov/west-coast/science-data/ocean-ecosystem-indicators-pacific-salmon-marine-survival-northern
fields:
  - name: time
    meaning: Daily (upwelling) or 8-day/monthly composite (chl-a) timestamp.
  - name: chlorophyll
    meaning: Near-surface chlorophyll-a concentration (mg m^-3) — primary-production proxy.
  - name: latitude / longitude
    meaning: Grid cell (chl-a ~4 km; CUTI/BEUTI 1-degree latitudinal bands).
  - name: CUTI
    meaning: Vertical volume transport (upwelling/downwelling), m^2 s^-1 per m coastline.
  - name: BEUTI
    meaning: Vertical nitrate flux (mmol N m^-1 s^-1) — nutrient quality of upwelled water.
time_coverage: Chl-a MODIS-Aqua 2002-present, VIIRS 2012-present; CUTI/BEUTI 1988-present (daily).
spatial_coverage: Chl-a global gridded (subset Salish Sea / NE Pacific shelf); CUTI/BEUTI 31-47N US West Coast latitudinal bands (covers the WA/OR outer-coast SRKW winter range; Salish Sea interior is shelf-adjacent, use 45-48N bands as the coastal driver).
adapter_contract:
  stream_name: ocean_productivity_index
  record_shape: {t: ISO-date, region: string, chla: float|null, cuti: float|null, beuti: float|null, source: "noaa_coastwatch|noaa_erd"}
  cadence: chl-a 8-day/monthly; upwelling daily; pull on a scheduled job, cache aggressively
integrity_condition: prey_covariate
already_wired: false
risks:
  - INDICATOR, lagged and indirect. Productivity drives juvenile Chinook growth/survival; the effect on adult Chinook available to SRKW lags 2-4 years (ocean-entry year-class to returning adult). Misusing chl-a as a contemporaneous SRKW driver would be a category error.
  - Spatial mismatch: CUTI/BEUTI are outer-coast (eastern boundary upwelling) indices; the Salish Sea interior is estuarine, not wind-driven upwelling. They are most defensible for the SRKW outer-coast winter range and as the regional ocean state setting the Fraser/Columbia smolt-year, less so for in-Salish-Sea summer.
  - Chl-a in inland glacial-fjord waters is optically complex (CDOM/turbidity); coastal ocean-color retrievals carry error near shore — validate before quantitative use.
next_action: Prototype an ERDDAP pull of monthly chl-a over the Salish Sea + NE Pacific shelf and the 45-48N CUTI/BEUTI bands; define a lagged annual productivity covariate (smolt-year) distinct from any within-season term; document the lag as a fitted parameter, not an assumption.
decision_label: can_get_now
priority: P1
literature_grounding:
  citation: "Wells, B.K., J.A. Santora, I.D. Schroeder, N. Mantua, W.J. Sydeman, D.D. Huff, and J.C. Field. 2017. Marine ecosystem perspectives on Chinook salmon recruitment: a synthesis of empirical and modeling studies from a California upwelling system. Marine Ecology Progress Series 552:271-284. doi:10.3354/meps11757. (Upwelling-index methodology: Jacox, M.G., C.A. Edwards, E.L. Hazen, S.J. Bograd. 2018. Coastal upwelling revisited: Ekman, Bakun, and improved upwelling indices for the U.S. West Coast. JGR Oceans 123(10):7332-7350. doi:10.1029/2018JC014187.)"
  verified: true
  mechanism: "Early-season upwelling intensity and the associated bottom-up productivity (retention of euphausiid and juvenile-rockfish prey on the shelf) are positively related to juvenile Chinook growth and ocean survival, setting cohort strength and adult return rates. This grounds satellite chl-a and CUTI/BEUTI as lagged prey-base productivity covariates on later adult-Chinook availability."
```

### 2. NOAA Marine Mammal Stock Assessment Reports — harbor seal, California sea lion, Steller sea lion (US)

```yaml
source: NOAA Fisheries Marine Mammal Stock Assessment Reports (SARs), Pacific region — Harbor seal (Washington inland-waters stock), California sea lion (US stock), Steller sea lion (Eastern DPS)
purpose: Competitor/predator covariate. These pinnipeds consume juvenile and adult Chinook in the Salish Sea and outer coast, reducing the Chinook available to SRKW. Their abundance enters as a negative term on the prey base.
availability: public_download
account_needed: none
license: U.S. Government work, public domain; cite the specific SAR year and stock.
endpoint_or_access_path: |
  SAR hub: https://www.fisheries.noaa.gov/national/marine-mammal-protection/marine-mammal-stock-assessment-reports
  Pacific SARs (annual PDFs) + the underlying abundance tables; population estimates (Nbest), trend, and Pbr per stock.
  Supporting WA haulout/abundance: WDFW marine mammal pages + Jeffries et al. survey series (Puget Sound aerial counts).
fields:
  - name: stock
    meaning: Named stock (e.g., harbor seal WA inland waters; CA sea lion US stock; Steller Eastern DPS).
  - name: year
    meaning: Assessment/survey year of the abundance estimate.
  - name: abundance_estimate
    meaning: Best population estimate (Nbest) and minimum population estimate (Nmin).
  - name: trend
    meaning: Population trend classification (increasing/stable) where given.
time_coverage: SARs published ~annually; underlying surveys span 1970s-present (WA inland harbor seal series from ~1978).
spatial_coverage: US stocks: WA inland waters (Puget Sound / Strait of Juan de Fuca / San Juans), US West Coast (CA sea lion), Eastern DPS Steller (CA-AK).
adapter_contract:
  stream_name: pinniped_abundance_annual
  record_shape: {species: string, stock: string, year: int, n_best: float, n_min: float, trend: string, source: "noaa_sar"}
  cadence: annual (one value per stock per assessment); manual/scheduled pull on SAR release
integrity_condition: prey_covariate
already_wired: false
risks:
  - COMPETITOR/PREDATOR, not prey and not effort. Sign in the model is negative on the Chinook prey base; mislabeling it as prey or as observation effort would corrupt the prey term.
  - Annual / multi-year survey resolution; the WA inland harbor seal stock has not been comprehensively re-surveyed in some recent years (Nbest may be dated). It carries between-year level, not within-season timing.
  - Total pinniped abundance is a coarse proxy for Chinook predation; the actual Chinook removed depends on diet fraction and bioenergetics (the Chasco et al. model), which vary by area/season — do not equate seal count with Chinook mortality without the diet weighting.
next_action: Extract harbor-seal (WA inland), CA sea lion, and Steller (Eastern DPS) Nbest time series from the SARs; pair with Chasco et al. per-capita Chinook-consumption coefficients to build an annual pinniped-predation covariate rather than using raw counts.
decision_label: can_get_now
priority: P1
literature_grounding:
  citation: "Chasco, B.E., I.C. Kaplan, A.C. Thomas, A. Acevedo-Gutierrez, D.P. Noren, M.J. Ford, M.B. Hanson, J.J. Scordino, S.J. Jeffries, K.N. Marshall, A.O. Shelton, C. Matkin, B.J. Burke, and E.J. Ward. 2017. Competing tradeoffs between increasing marine mammal predation and fisheries harvest of Chinook salmon. Scientific Reports 7:15439. doi:10.1038/s41598-017-14984-8."
  verified: true
  mechanism: "A spatio-temporal bioenergetics model showed that Chinook biomass consumed by pinnipeds and killer whales on the US/Canada West Coast rose from 6,100 to 15,200 metric tonnes (1975-2015); for Salish Sea Chinook the increase in predation greatly exceeds fishery harvest, so recovering pinnipeds may now limit Chinook available to SRKW more than fisheries do. This grounds pinniped abundance as a negative competitor covariate on the SRKW prey base."
```

### 3. DFO Pacific Herring spawn index / stock assessment (British Columbia, Strait of Georgia)

```yaml
source: Fisheries and Oceans Canada (DFO) Pacific Herring (Clupea pallasii) spawn index and integrated stock assessment, by major stock area (Strait of Georgia is the SRKW-relevant area; also WCVI, PRD, CC, HG)
purpose: Prey-base covariate. Pacific herring is the dominant pelagic forage fish on which juvenile/sub-adult Chinook become piscivorous in the Salish Sea; the BC (Strait of Georgia) herring spawn index is a bottom-up indicator of the forage base that builds Chinook cohorts later available to SRKW.
availability: public_download
account_needed: none
license: Open Government Licence - Canada (DFO Open Data); attribution to DFO. Confirm per-dataset terms on the Open Data record.
endpoint_or_access_path: |
  DFO Pacific Herring program: https://www.pac.dfo-mpo.gc.ca/fm-gp/herring-hareng/index-eng.html
  Spawn index data + assessments (Open Data): https://open.canada.ca/data/en/dataset (search "Pacific Herring spawn index"); annual stock assessment Research Documents via CSAS (https://www.dfo-mpo.gc.ca/csas-sccs/).
  Herring spawn survey database (surface + dive/SOK spawn index by section/area).
fields:
  - name: year
    meaning: Spawn/assessment year.
  - name: stock_area
    meaning: DFO herring major stock area (Strait of Georgia = SoG is the SRKW-relevant unit).
  - name: spawn_index
    meaning: Spawn index (tonnes) — biomass proxy from spawn surveys; and modelled spawning-stock biomass.
  - name: section
    meaning: Sub-area / statistical section of the spawn (spatial detail within a stock area).
time_coverage: Spawn index series from 1951-present (one of the longer forage-fish series available); annual.
spatial_coverage: Coastal BC by major area; Strait of Georgia is the area overlapping the SRKW Salish Sea summer range.
adapter_contract:
  stream_name: forage_fish_index (herring, BC)
  record_shape: {year: int, stock_area: string, spawn_index_t: float, ssb_t: float|null, source: "dfo_herring"}
  cadence: annual; pull on assessment release
integrity_condition: prey_covariate
already_wired: false
risks:
  - Prey of JUVENILE Chinook, not of SRKW. The link to SRKW prey is bottom-up and lagged 2-4 years (forage year-class -> juvenile Chinook -> returning adult); enter as a lagged annual covariate, never a within-season term.
  - Spawn index measures the spawning component, not the summer pelagic forage field that juvenile Chinook actually feed on; it is a proxy for the standing forage stock, with its own measurement model.
  - Stock-area resolution is coarse relative to where juvenile Chinook of SRKW-relevant stocks rear; align SoG herring to Fraser-origin juvenile Chinook rearing rather than to SRKW presence directly.
next_action: Pull the SoG spawn-index series from DFO Open Data; define a lagged forage-base covariate feeding the Chinook prey term; document the lag as fitted.
decision_label: can_get_now
priority: P1
literature_grounding:
  citation: "Duffy, E.J., D.A. Beauchamp, R.M. Sweeting, R.J. Beamish, and J.S. Brennan. 2010. Ontogenetic diet shifts of juvenile Chinook salmon in nearshore and offshore habitats of Puget Sound. Transactions of the American Fisheries Society 139(3):803-823. doi:10.1577/T08-244.1."
  verified: true
  mechanism: "Juvenile Chinook salmon shift to piscivory as they grow, feeding predominantly on Pacific herring in offshore Puget Sound habitats; herring is the most abundant pelagic forage fish and its decline is flagged as reducing energy-rich prey for Chinook. This grounds the herring spawn index as a bottom-up prey-base covariate on Chinook cohort production."
```

### 4. WDFW Puget Sound Pacific herring spawning-biomass surveys (US Salish Sea)

```yaml
source: Washington Department of Fish & Wildlife (WDFW) Puget Sound Pacific herring (Clupea pallasii) stock assessment / spawning-biomass surveys, by stock (e.g., Cherry Point, Squaxin Pass, and ~20 Puget Sound sub-stocks)
purpose: Prey-base covariate (US side). Puget Sound herring spawning biomass indexes the inland forage base for juvenile Chinook on the US side, complementing the DFO SoG index; Cherry Point in particular is a long-tracked, severely declined stock.
availability: public_download
account_needed: none
license: WDFW public data; attribution to WDFW; some series via data.wa.gov under WA open-data terms. Confirm reuse terms for assessment-derived biomass estimates.
endpoint_or_access_path: |
  WDFW forage fish / herring: https://wdfw.wa.gov/species-habitats/species/clupea-pallasii (status reports) and Puget Sound herring stock status reports.
  Spawning-ground survey data via data.wa.gov; PSEMP (Puget Sound Ecosystem Monitoring Program) forage-fish vital sign for synthesized trends.
fields:
  - name: stock
    meaning: Named Puget Sound herring sub-stock (Cherry Point, Squaxin Pass, etc.).
  - name: year
    meaning: Survey year.
  - name: spawning_biomass
    meaning: Estimated spawning biomass (tons) from spawn-deposition / acoustic-trawl surveys.
  - name: status
    meaning: Stock status / trend classification.
time_coverage: Multi-decade per stock (Cherry Point series from ~1970s); annual.
spatial_coverage: Puget Sound and adjacent WA inland waters, by spawning sub-stock.
adapter_contract:
  stream_name: forage_fish_index (herring, Puget Sound)
  record_shape: {stock: string, year: int, spawning_biomass_t: float, status: string, source: "wdfw_herring"}
  cadence: annual; manual pull on status-report update
integrity_condition: prey_covariate
already_wired: false
risks:
  - Same bottom-up, lagged, juvenile-Chinook-prey caveat as source 3; not an SRKW within-season driver.
  - Puget Sound herring stocks are fragmented and some lack recent surveys; the US-side juvenile-Chinook stocks (Puget Sound) are a minority (~6-14%) of SRKW summer Chinook origin (Hanson et al. 2010, see WL-PREY), so this is a low-weight US complement to the SoG (Fraser-relevant) index.
  - No single documented bulk API; structured extraction via data.wa.gov or report digitization.
next_action: Decide whether the small Puget-Sound diet share justifies a separate US herring covariate; if yes, pull Cherry Point + aggregate Puget Sound biomass via data.wa.gov as a low-weight lagged forage term.
decision_label: can_get_now
priority: P2
literature_grounding:
  citation: "Duffy, E.J., D.A. Beauchamp, R.M. Sweeting, R.J. Beamish, and J.S. Brennan. 2010. Ontogenetic diet shifts of juvenile Chinook salmon in nearshore and offshore habitats of Puget Sound. Transactions of the American Fisheries Society 139(3):803-823. doi:10.1577/T08-244.1."
  verified: true
  mechanism: "In Puget Sound, juvenile Chinook became increasingly piscivorous (feeding mainly on Pacific herring) as they grew and moved offshore; recent herring declines may reduce the energy-rich prey supporting Chinook growth. Grounds Puget Sound herring biomass as a US-side bottom-up prey-base covariate."
```

### 5. DFO harbour seal & Steller sea lion abundance (Olesiuk / CSAS, British Columbia)

```yaml
source: DFO Canadian Science Advisory Secretariat (CSAS) Pacific harbour seal (Phoca vitulina richardsi) and Steller sea lion (Eumetopias jubatus) abundance assessments (Olesiuk 2010; Olesiuk 2018) + DFO aerial haulout survey series
purpose: Competitor/predator covariate (Canadian Salish Sea). Strait of Georgia harbour seals grew ~10-fold (3,600 in 1973 to ~39,000 by mid-1990s) and consume salmonids; the BC-side pinniped abundance complements the US SARs for a basin-complete competitor term.
availability: public_download
account_needed: none
license: Open Government Licence - Canada; DFO CSAS Research Documents public; attribution to DFO.
endpoint_or_access_path: |
  Harbour seal: Olesiuk, P.F. 2010. An assessment of population trends and abundance of harbour seals (Phoca vitulina) in British Columbia. DFO CSAS Res. Doc. 2009/105 (waves-vagues.dfo-mpo.gc.ca).
  Steller: Olesiuk, P.F. 2018. Recent trends in abundance of Steller sea lions in BC. DFO CSAS Res. Doc. 2018/006.
  Updated SoG harbour seal survey: Majewski & Ellis (2022, 2014 aerial survey synthesis). CSAS portal: https://www.dfo-mpo.gc.ca/csas-sccs/
fields:
  - name: species
    meaning: Harbour seal or Steller sea lion.
  - name: region
    meaning: Stock/sub-area (Strait of Georgia is SRKW-relevant; coast-wide BC also reported).
  - name: year
    meaning: Survey year (surveys are periodic, not annual).
  - name: abundance_estimate
    meaning: Estimated abundance with CI (surface count x haulout correction factor ~1.63).
  - name: haulout_sites
    meaning: Number/location of identified haulout sites (~1,400 coast-wide for harbour seal).
time_coverage: Harbour seal surveys 1973-2008 (logistic model) + 2014 update; Steller trend to ~2017. Periodic survey years, interpolated for an annual covariate.
spatial_coverage: Coastal BC; Strait of Georgia is the SRKW Salish Sea overlap area.
adapter_contract:
  stream_name: pinniped_abundance_annual (BC)
  record_shape: {species: string, region: string, year: int, abundance: float, ci_low: float, ci_high: float, source: "dfo_csas"}
  cadence: per survey year; interpolate to annual for the covariate
integrity_condition: prey_covariate
already_wired: false
risks:
  - COMPETITOR/PREDATOR, negative sign, annual/periodic resolution — same labeling caveat as source 2.
  - BC harbour seal abundance has been roughly stable near carrying capacity since the mid-1990s, so it adds little between-year variation in recent years; its main value is the historical recovery trajectory and basin-complete coverage alongside the US stock.
  - Survey years are sparse; an annual covariate requires interpolation, which fabricates between-survey structure — flag the interpolation explicitly.
next_action: Combine SoG harbour seal (Olesiuk 2010 + Majewski & Ellis 2022) with the US WA-inland SAR into one basin Salish Sea pinniped index; mark interpolated years.
decision_label: can_get_now
priority: P2
literature_grounding:
  citation: "Olesiuk, P.F. 2010. An assessment of population trends and abundance of harbour seals (Phoca vitulina) in British Columbia. DFO Canadian Science Advisory Secretariat Research Document 2009/105. vi + 157 p. (mechanism via Chasco, B.E. et al. 2017, Scientific Reports 7:15439, doi:10.1038/s41598-017-14984-8.)"
  verified: true
  mechanism: "Olesiuk documents the ~10-fold recovery of Strait of Georgia harbour seals (3,600 in 1973 to ~39,000 by the mid-1990s, then stable), the abundance trajectory that Chasco et al. 2017 couple to bioenergetics to show pinniped Chinook consumption in the Salish Sea now exceeds fishery harvest. Grounds BC pinniped abundance as a competitor covariate on the SRKW Chinook prey base."
```

### 6. Rhinoceros auklet colony & diet monitoring (Protection Island; Pearson / Hodum / Good)

```yaml
source: Rhinoceros auklet (Cerorhinca monocerata) breeding-colony and chick-provisioning diet monitoring, Salish Sea (Protection Island NWR) and outer WA coast (Destruction, Tatoosh) — USFWS / WDFW / University of Puget Sound (Pearson, Hodum) + NOAA (Good)
purpose: Indicator (forage-fish sentinel). Auklets are central-place piscivores that carry identifiable bill-loads of forage fish to chicks; their diet composition is a low-cost readout of Pacific sand lance and Pacific herring abundance/recruitment in the Salish Sea — the same forage base that feeds juvenile Chinook.
availability: research_request_required
account_needed: researcher_request
license: Mixed — published papers (publisher terms); raw colony diet/burrow data held by WDFW/USFWS/UPS researchers; contact required for time series. Cite Good et al. 2014 and WDFW colony reports.
endpoint_or_access_path: |
  Published: Good et al. 2014 (Mar. Pollut. Bull.); WDFW Protection Island burrow-count progress reports (wdfw.wa.gov/sites/default/files/publications/).
  Raw diet/colony series: request from WDFW (S.F. Pearson) / University of Puget Sound (P. Hodum) / USFWS Washington Maritime NWR Complex.
  At-sea complement: PSEMP marine bird vital sign; WDFW Puget Sound Seabird Survey; BC Coastal Waterbird Survey (Birds Canada).
fields:
  - name: colony / year
    meaning: Breeding colony (Protection Island = Salish Sea) and season-year.
  - name: prey_species_composition
    meaning: Fraction of bill-load by species (sand lance, herring, anchovy, smelt, salmonid).
  - name: bill_load_mass / energy
    meaning: Mean prey load mass and caloric content delivered to chicks.
  - name: burrow_count / occupancy
    meaning: Colony size proxy (burrow density, occupancy) from monitoring.
time_coverage: Diet sampling at Protection Island across multiple breeding seasons (2000s-present, intermittent); not a continuous public series.
spatial_coverage: Protection Island (eastern Strait of Juan de Fuca, Salish Sea) and outer-coast colonies; foraging range tens of km around colony.
adapter_contract:
  stream_name: forage_fish_indicator (seabird diet)
  record_shape: {colony: string, year: int, prey_species: string, fraction: float, source: "rhau_diet"}
  cadence: annual breeding-season; manual on data release/request
integrity_condition: prey_covariate
already_wired: false
risks:
  - INDICATOR, not a fish census. Auklet diet reflects what is locally available within foraging range during one season; it is a relative, behaviorally filtered signal, not absolute forage-fish biomass.
  - Several years' data are unpublished (Pearson et al. unpubl.) and require a researcher request; cadence is irregular.
  - Two trophic steps from SRKW prey (forage fish -> juvenile Chinook -> adult Chinook), so it is supporting context for the forage-base covariates (3-4, 7), not a standalone Chinook signal.
next_action: Request the Protection Island sand-lance/herring diet fraction time series from WDFW/UPS as a corroborating index for the herring/sand-lance covariates; do not treat as primary.
decision_label: needs_research_request
priority: P2
literature_grounding:
  citation: "Good, T.P., S.F. Pearson, P. Hodum, D. Boyd, B.F. Anulacion, and G.M. Ylitalo. 2014. Persistent organic pollutants in forage fish prey of rhinoceros auklets breeding in Puget Sound and the northern California Current. Marine Pollution Bulletin 86(1-2):367-378. doi:10.1016/j.marpolbul.2014.06.042."
  verified: true
  mechanism: "Rhinoceros auklets breeding on Protection Island (Salish Sea) provisioned chicks with a diet ~76% Pacific sand lance and ~16% Pacific herring by weight, demonstrating that auklet bill-load composition is a direct readout of local forage-fish (sand lance/herring) availability. Grounds auklet diet monitoring as a forage-fish indicator for the Chinook prey base."
```

### 7. Pacific sand lance (Ammodytes personatus) abundance

```yaml
source: Pacific sand lance (Ammodytes personatus) abundance/distribution — no dedicated agency stock-assessment survey; inferred from forage-fish spawning-habitat surveys (WDFW surf-smelt/sand-lance spawning beaches), research trawls, and seabird-diet proxy
purpose: Prey-base covariate / indicator. Sand lance is, with herring, a primary lipid-rich forage fish for juvenile Chinook and the dominant prey of Salish Sea rhinoceros auklets; a sand-lance index would be a bottom-up covariate on the Chinook forage base. Honest status: there is no directed sand-lance abundance time series to ingest.
availability: not_found
account_needed: researcher_request
license: n/a for a direct series; component sources (WDFW spawning-beach data on data.wa.gov; research datasets) carry their own terms.
endpoint_or_access_path: |
  Closest proxies: WDFW forage-fish spawning-beach surveys (surf smelt + sand lance documented spawning habitat) https://wdfw.wa.gov/species-habitats/species/ammodytes-personatus ; data.wa.gov forage-fish spawning datasets.
  Indirect index: rhinoceros auklet diet (source 6); research trawl catches (e.g., NWFSC / DFO juvenile-salmon trawl bycatch).
  No NOAA/DFO directed sand-lance stock assessment exists (forage-fish management gap).
fields:
  - name: site / year
    meaning: Spawning beach or survey location and year (presence/spawning habitat, not abundance).
  - name: presence / spawning_index
    meaning: Documented spawning (presence) or relative occurrence — NOT a biomass time series.
time_coverage: Spawning-habitat documentation accrues over time; no continuous abundance series.
spatial_coverage: Puget Sound / Salish Sea beaches (spawning habitat); pelagic distribution unmeasured at stock scale.
adapter_contract:
  stream_name: forage_fish_index (sand lance) — NOT AVAILABLE as a quantitative series
  record_shape: {site: string, year: int, spawning_present: bool, source: "wdfw_forage_fish"}
  cadence: irregular; presence-type data only
integrity_condition: prey_covariate
already_wired: false
risks:
  - NOT FOUND as a directed abundance series — the single biggest forage-fish data gap. Treating spawning-beach presence as an abundance covariate would over-claim.
  - Best available signal is the auklet-diet proxy (source 6), which is itself an indicator. Keep sand lance as supporting context, not an independent covariate, until a real survey exists.
  - Taxonomy note: NE Pacific sand lance reclassified Ammodytes hexapterus -> A. personatus; reconcile names across older sources.
next_action: Do not build a sand-lance adapter; carry sand lance via the auklet-diet indicator (source 6) and WDFW spawning-habitat presence as qualitative context. Flag the missing directed survey as an ecosystem-monitoring gap.
decision_label: not_worth_it
priority: P2
literature_grounding:
  citation: "Good, T.P., S.F. Pearson, P. Hodum, D. Boyd, B.F. Anulacion, and G.M. Ylitalo. 2014. Persistent organic pollutants in forage fish prey of rhinoceros auklets breeding in Puget Sound and the northern California Current. Marine Pollution Bulletin 86(1-2):367-378. doi:10.1016/j.marpolbul.2014.06.042. (Chinook-prey link: Duffy et al. 2010, TAFS 139:803-823, doi:10.1577/T08-244.1.)"
  verified: true
  mechanism: "Sand lance is the dominant Salish Sea rhinoceros auklet prey (~76% at Protection Island; Good et al. 2014) and a key lipid-rich forage fish in the Puget Sound food web alongside herring (Duffy et al. 2010), making it part of the juvenile-Chinook forage base — but the absence of a directed abundance survey limits it to indicator/context status."
```

### 8. Eulachon (Thaleichthys pacificus) spawning-stock biomass (DFO Fraser/Columbia; CDFW)

```yaml
source: Eulachon (Thaleichthys pacificus) spawning-stock biomass / run indices — DFO Fraser River eulachon assessment, Columbia River (WDFW/ODFW) eulachon, southern-DPS monitoring under the ESA listing
purpose: Indicator (forage-fish / ocean-productivity state). Eulachon is a high-lipid anadromous smelt and an ecosystem forage-fish indicator; its abundance covaries with ocean/productivity conditions. Honest status: its direct trophic link to Chinook (or to SRKW prey) is weak, so it is an ecosystem indicator, not a Chinook prey-base covariate.
availability: public_download
account_needed: none
license: DFO Open Government Licence; US data WDFW/ODFW public + NOAA status reviews (public domain). Attribution per source.
endpoint_or_access_path: |
  NOAA southern-DPS status reviews (Gustafson et al. 2010 NMFS-NWFSC-105; 2016 update): https://repository.library.noaa.gov/ and fisheries.noaa.gov.
  DFO Fraser eulachon assessment via CSAS Research Documents; Columbia River spawning-stock biomass (ODFW/WDFW eulachon reports).
fields:
  - name: river / year
    meaning: Spawning river (Fraser, Columbia) and year.
  - name: spawning_stock_biomass
    meaning: Estimated eulachon spawning-stock biomass / run size index.
  - name: trend / status
    meaning: ESA southern-DPS status (listed threatened 2010) and trend.
time_coverage: Columbia spawning-stock biomass series multi-decade; Fraser indices multi-year; annual.
spatial_coverage: Fraser River and Columbia River (and other southern-DPS rivers); spawning runs, late winter/spring.
adapter_contract:
  stream_name: forage_fish_indicator (eulachon)
  record_shape: {river: string, year: int, ssb_t: float, status: string, source: "dfo_eulachon|noaa_eulachon"}
  cadence: annual; pull on assessment release
integrity_condition: prey_covariate
already_wired: false
risks:
  - WEAKEST direct Chinook link of the set. Eulachon are prey for many predators (pinnipeds, sturgeon, seabirds, some groundfish) but are not an established primary prey of juvenile Chinook; treat strictly as an ecosystem/productivity indicator, not a Chinook prey-base covariate. Over-claiming a Chinook link here would violate the honesty constraint.
  - Listed (threatened) southern DPS; runs are depressed and variable, so the signal is dominated by decline/recovery dynamics that may not track Chinook.
  - Different rivers/agencies use different units (SSB tonnes vs run index); normalize before any fusion.
next_action: Carry eulachon only as a low-weight ecosystem-state indicator (alongside chl-a/upwelling), explicitly NOT as a Chinook prey-base term; revisit only if a specific eulachon-Chinook or eulachon-SRKW link is established in the literature.
decision_label: not_worth_it
priority: P2
literature_grounding:
  citation: "Gustafson, R.G., M.J. Ford, D.J. Teel, and J.S. Drake. 2010. Status review of eulachon (Thaleichthys pacificus) in Washington, Oregon, and California. NOAA Technical Memorandum NMFS-NWFSC-105. 360 p. (southern DPS listed threatened, 75 FR 13012, 18 Mar 2010.)"
  verified: true
  mechanism: "Gustafson et al. document eulachon as a high-lipid forage fish whose southern-DPS decline is driven substantially by ocean/climate conditions; this supports eulachon as an ecosystem-productivity/forage-fish indicator. The review does NOT establish eulachon as Chinook prey, which is why it is labeled indicator, not prey-base covariate, here."
```

---

## Verified citation ledger

All citations below were verified by web search against the publisher / primary record during this
research pass (2026-06-27). None are unverified; none are invented.

| Citation | Venue / DOI | Verified | Used for (role) |
|----------|-------------|----------|-----------------|
| Chasco et al. 2017 | Scientific Reports 7:15439, doi:10.1038/s41598-017-14984-8 | yes | Pinniped predation reducing Chinook available to SRKW (sources 2, 5 — competitor) |
| Duffy, Beauchamp, Sweeting, Beamish & Brennan 2010 | Trans. Am. Fish. Soc. 139(3):803-823, doi:10.1577/T08-244.1 | yes | Juvenile Chinook become piscivorous on Pacific herring (sources 3, 4, 7 — prey-base) |
| Good, Pearson, Hodum, Boyd, Anulacion & Ylitalo 2014 | Marine Pollution Bulletin 86(1-2):367-378, doi:10.1016/j.marpolbul.2014.06.042 | yes | Auklet diet = sand lance/herring readout (sources 6, 7 — indicator) |
| Wells, Santora, Schroeder, Mantua, Sydeman, Huff & Field 2017 | Mar. Ecol. Prog. Ser. 552:271-284, doi:10.3354/meps11757 | yes | Upwelling/productivity drives Chinook growth/recruitment (source 1 — indicator) |
| Jacox, Edwards, Hazen & Bograd 2018 | JGR Oceans 123(10):7332-7350, doi:10.1029/2018JC014187 | yes | CUTI/BEUTI upwelling-index methodology (source 1) |
| Olesiuk 2010 | DFO CSAS Res. Doc. 2009/105 | yes (DFO waves-vagues) | BC harbour seal abundance trajectory (source 5 — competitor) |
| Gustafson, Ford, Teel & Drake 2010 | NOAA Tech. Memo. NMFS-NWFSC-105 | yes (NOAA repository) | Eulachon forage-fish status (source 8 — indicator) |

Supporting (verified in WL-PREY, reused for the forage-fish relevance): Ford, J.K.B. & G.M. Ellis
2006, Mar. Ecol. Prog. Ser. 316:185-199, doi:10.3354/meps316185 — SRKW select large adult Chinook,
establishing that forage fish act on Chinook (juveniles) bottom-up rather than being SRKW prey.
Hanson et al. 2010 (ESR 11:69-82) — Puget Sound is only 6-14% of summer SRKW Chinook origin,
bounding the US-side herring (source 4) weight.

## Exit-bar check (this lane)

- Distinct sources: 8 (>= 6 required), spanning all required categories: herring (DFO SoG #3 +
  WDFW Puget Sound #4), eulachon (#8), Pacific sand lance (#7), pinnipeds — harbor seal + Steller +
  California sea lion (NOAA SARs #2, DFO/Olesiuk #5), seabird colony + at-sea diet indicator
  (rhinoceros auklet #6), and ocean productivity — satellite chl-a + upwelling indices (#1).
- Each source has availability, account_needed, license, endpoint/access path, fields, time and
  spatial coverage, an explicit labeled role, a trophic mechanism, and a verified citation: yes.
- Roles labeled honestly: prey-base covariate (#3, #4, #7), competitor/predator (#2, #5),
  indicator (#1, #6, #8). None is the temporal-kernel heat; none is an effort covariate; integrity
  condition is `prey_covariate` for all (ecological covariates on the Chinook prey base).
- Lag/area honesty noted per source: forage fish and productivity act on *juvenile* Chinook with a
  2-4 year lag to adult Chinook available to SRKW; pinnipeds are a negative competitor at annual
  resolution; most series are basin/coast-scale, not San-Juan-summer daily signals.
- Already wired: none (`already_wired: false` for all) — no prey-base ecosystem source exists in
  `src/aws_backend/sources/`.
- Citations: 7 distinct, all verified against publisher/primary records; 0 unverified; 0 invented.
