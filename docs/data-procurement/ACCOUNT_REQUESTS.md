# ORCAST Data Access Account and Request List

## No Account Needed

- OrcaHello public read endpoints for detections, confirmed detections, false positives, unknowns, and unreviewed candidates.
- NOAA CO-OPS datagetter for water levels, currents, current predictions, wind, pressure, and temperature.
- NOAA NDBC realtime and historical station files.
- NOAA Marine Cadastre AIS bulk downloads.
- NOAA PMEL ERDDAP AIS annual tables.
- NOAA CUSP shoreline.
- NOAA ETOPO1 / existing bathymetry asset.
- NOAA Marine Protected Areas Inventory.
- Canada CPCAD protected/conserved areas.
- WA DNR kelp canopy services.
- BC ShoreZone/CRIMS habitat layers.
- WSDOT and BC ferry route GIS services.
- OBIS API.
- iNaturalist API, for normal API-scale use.

## Likely Free Account / API Key

### Happywhale

Purpose: photo-ID encounter validation and individual whale histories.

Action for user:
1. Create/log into a Happywhale account.
2. Ask whether research/export/API access is available for Salish Sea `Orcinus orca` encounters.
3. Request fields: encounter id, date/time, approximate location, species/ecotype/pod/individual id if allowed, public encounter URL, media/license permissions.

### Acartia / External Community Alert Feeds

Purpose: public/community sighting validation feeds beyond ORCAST internal submissions.

Action for user:
1. Create an API account or request an access token if available.
2. Ask for current and trusted sighting endpoints, rate limits, and allowed retention.
3. Request fields: id, observed_at, lat/lng or generalized location, species, confidence/trusted flag, report URL.

## Research / Data Requests

### Orcasound / OrcaHello Maintainers

Purpose: confirm data license and station uptime/event history.

Ask:
- Is the public detections API data licensed for research download and derived statistics?
- May ORCAST retain reviewed outcome fields and audio/spectrogram URLs?
- Is there a stable public API for Orcanode Monitor event history or station uptime?
- Can station keys be mapped reliably between OrcaHello detection `location`, Orcasound feed `node_name`, and SeaStats station keys?

### Orca Network

Purpose: structured Salish Sea sightings as independent validation labels.

Ask:
- Is structured historical sighting export available for research?
- Can ORCAST use date/time, location, species/ecotype, count, behavior, confidence, and source URL?
- What citation and redistribution limits apply?

### Center for Whale Research

Purpose: high-confidence SRKW encounter validation.

Ask:
- Is a structured encounter export available for research use?
- Can ORCAST use encounter date/time, approximate location, pod/ecotype, encounter id, and public report URL?
- Are there restrictions on derived validation metrics or public display?

## Avoid Unless Needed

### Commercial AIS Vendors

NOAA Marine Cadastre and PMEL ERDDAP are enough for the first vessel/noise proxy. Vendor AIS is not needed unless public data coverage proves inadequate.

### Public Whale-Watch / Kayak Route Maps

Public route maps are usually copyrighted marketing or guide material. Do not scrape into GIS without permission. Use ferries, AIS, no-go zones, and access points as defensible effort proxies.
