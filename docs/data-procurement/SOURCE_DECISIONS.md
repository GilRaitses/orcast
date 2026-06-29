# ORCAST Source Procurement Decisions

## Can Get Now

| Source | Use | Priority | Next action |
| --- | --- | --- | --- |
| NOAA CO-OPS current predictions PUG1701/PUG1702/PUG1703 | Tide/current phase for 2020-2021 overlap | P0/P1 | Extend `NoaaAdapter` station list and metadata preservation. |
| NOAA NDBC 46088 | Weather/sea-state detectability | P0 | Add NDBC parser for stdmet/spec files. |
| NOAA CO-OPS Friday Harbor wind/met | In-domain wind/pressure detectability | P0 | Add CO-OPS met time-series ingestion. |
| NOAA CUSP shoreline | Distance-to-shore and land/water support | P0 | Clip to pilot region and compute nearest shore per grid cell. |
| Existing ETOPO1 bathymetry asset | Depth/channel covariate | P0 | Keep current adapter; derive slope/depth bins later. |
| OBIS | Independent occurrence validation | P0 | Preserve license/citation fields in adapter outputs. |
| iNaturalist | Photo-backed public validation | P0 | Tighten query to photo/licensed observations for validation use. |
| Columbia DART Bonneville Chinook | Salmon fallback / cross-check | P0 fallback | Pin generated CSV query link and parse daily counts. |
| Fraser/Albion Chinook | Best SRKW prey index | P0/P1 | Confirm PSC/DFO download schema; implement parser after link inspection. |
| NOAA PMEL ERDDAP AIS or Marine Cadastre bulk | Vessel/noise proxy | P1 | Prefer Marine Cadastre bulk if ERDDAP query remains brittle. |
| WSDOT / BC ferry routes | Observation effort proxy | P0/P1 | Add route-distance grid features. |
| WA DNR kelp + BC ShoreZone | Habitat covariates | P1 | Normalize U.S./Canada habitat layers. |
| NOAA/Canada protected areas | Spatial/regulatory context | P1 | Clip and compute inside/distance features. |

## Needs User Account

| Source | Why | Ask user to do |
| --- | --- | --- |
| Happywhale | Account/permission likely required for usable encounter export/API | Create account and request research/export access for Salish Sea `Orcinus orca` encounters. |
| Acartia / external community feeds | API token likely required | Create/request access token and endpoint docs. |

## Needs Research Request

| Source | Why | Ask/request |
| --- | --- | --- |
| Orcasound / OrcaHello maintainers | Need stable endpoint/license confirmation and station uptime mapping | Confirm stable reviewed-detections API, data license, station keys, station uptime/event-history API. |
| Orca Network | Public pages are not a structured reusable API | Request structured historical sightings export and reuse terms. |
| Center for Whale Research | Strong validation source, not open bulk data | Request structured encounter export/permission. |

## Vendor Or Restricted

| Source | Decision |
| --- | --- |
| Commercial AIS vendors | Avoid for now. NOAA Marine Cadastre/PMEL are sufficient for first vessel/noise proxy. |

## Not Worth It For First Pass

| Source | Reason |
| --- | --- |
| Public kayak/whale-watch route maps | Copyright/permission unclear and not stable GIS. |
| AccessAIS manual ordering | Useful for QA, but not stable enough as primary adapter; use bulk/ERDDAP AIS. |
| Fish Passage Center as primary salmon source | Use DART first; keep FPC as secondary validation only. |
