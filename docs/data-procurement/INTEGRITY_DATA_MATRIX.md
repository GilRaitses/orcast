# ORCAST Integrity Data Matrix

## Summary

Most missing integrity data can be sourced without vendors. The highest-friction items are not commercial data; they are permission/relationship datasets: Orca Network, Center for Whale Research, Happywhale, and possibly Orcasound station-event history if public API access is insufficient.

## Priority Matrix

| Domain | Source | Integrity condition | Availability | Decision | Priority | Adapter effort | Scientific value |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Acoustic labels | OrcaHello confirmed / false positive / unknown / unreviewed endpoints | input integrity | `public_api` | `can_get_now` | P0 | medium | high |
| Station uptime | SeaStats / Orcanode Monitor / Orcasound S3 inventory | effort offset | `public_api` with possible gaps | `can_get_now` plus possible maintainer confirmation | P0 | medium-high | high |
| Historical current predictions | NOAA CO-OPS `currents_predictions` PUG17xx stations | kernel identifiability | `public_api` | `can_get_now` | P0/P1 | low-medium | high |
| Salmon prey | Columbia DART Bonneville Chinook | prey covariate | `public_api` | `can_get_now` | P0 fallback | medium | medium |
| Salmon prey | Fraser/Albion Chinook CPUE | prey covariate | `public_download` / `public_scrape_required` | `can_get_now` after schema confirmation | P0/P1 | medium-high | high |
| Weather / sea state | NDBC 46088 and CO-OPS Friday Harbor | detectability/noise | `public_download` / `public_api` | `can_get_now` | P0 | medium | high |
| AIS vessel traffic | NOAA PMEL ERDDAP AIS / Marine Cadastre bulk | detectability/noise | `public_api` / `public_download` | `can_get_now` | P1 | medium-high | high |
| Shoreline distance | NOAA CUSP shoreline | spatial covariate | `public_api` | `can_get_now` | P0 | medium | high |
| Bathymetry | Existing ETOPO1 local asset | spatial covariate | already present | `can_get_now` | P0 | low | high |
| Protected areas | NOAA MPA + Canada CPCAD | spatial covariate | `public_download` | `can_get_now` | P1 | medium | medium |
| Kelp/eelgrass/habitat | WA DNR kelp + BC ShoreZone/CRIMS | spatial covariate | `public_api` | `can_get_now` | P1 | medium-high | medium |
| Ferry routes | WSDOT + BC coastal ferry routes | effort offset | `public_api` | `can_get_now` | P0/P1 | medium | medium |
| Access points | WA Ecology/WDFW boat ramps, Cascadia Marine Trail | effort offset | `public_api` / `public_download` | `can_get_now` | P2 | low-medium | low-medium |
| External validation | OBIS | external validation | `public_api` | `can_get_now` | P0 | already present, minor improvements | high |
| External validation | iNaturalist | external validation | `public_api` | `can_get_now` | P0 | already present, minor improvements | medium-high |
| External validation | Orca Network | external validation | `public_scrape_required` / request | `needs_research_request` | P1 | medium after permission | high |
| External validation | Center for Whale Research | external validation | public pages plus request | `needs_research_request` | P1 | medium after permission | very high |
| External validation | Happywhale | external validation | account/restricted | `needs_user_account` | P2 | medium after permission | medium |
| Community validation | Acartia / Whale Museum feeds | external validation | `account_required` / docs request | `needs_user_account` | P1 | medium | medium-high |

## P0 Procurement Queue

1. OrcaHello reviewed outcome endpoints.
2. Station uptime/effort from SeaStats, Orcanode Monitor, or S3 inventory.
3. NOAA CO-OPS current predictions for San Juan current stations overlapping 2020-2021 acoustic detections.
4. NDBC/CO-OPS weather and sea-state detectability covariates.
5. Shoreline distance and bathymetry spatial covariates.
6. OBIS and iNaturalist validation feeds, with license/citation preservation.

## P1 Procurement Queue

1. Fraser/Albion Chinook CPUE and DART Bonneville fallback.
2. AIS vessel traffic from NOAA ERDDAP or Marine Cadastre.
3. Kelp/eelgrass and protected-area covariates.
4. Orca Network and Center for Whale Research structured validation access.
5. External community report APIs if account/key access is granted.

## P2 / Avoid For Now

- Public kayak/whale-watch route maps: useful context, but no stable GIS/license. Use ferry, AIS, and access points instead.
- AccessAIS manual ordering: useful for ad hoc QA, but not a primary adapter.
- Full Happywhale integration: useful later for individual ID validation, but account/terms make it non-blocking.
