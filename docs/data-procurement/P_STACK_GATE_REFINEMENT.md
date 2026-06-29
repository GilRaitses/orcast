# ORCAST P-Stack Gate Refinement

## P0 Gate: Current Level 1-2 Integrity

The P0 gate is limited to the data needed to make current acoustic temporal claims defensible. Salmon, ferries, AIS, and habitat are valuable, but they should not block this gate.

## P0 Final Adapter Order

1. OrcaHello reviewed detector outcomes.
2. Station uptime / effort offset.
3. NOAA CO-OPS historical current predictions.
4. NOAA/NDBC detectability covariates.
5. Shoreline distance + bathymetry basics.
6. OBIS + iNaturalist validation tightening.

## P0 Pass Conditions

| Source | Pass condition |
| --- | --- |
| OrcaHello reviewed outcomes | Confirmed/false-positive/unknown/unreviewed outcomes are available across the acoustic window, with per-station outcome counts and detector QC metrics. |
| Station uptime | Every modeled station has station-hour `coverage_fraction`, `up`, `status`, and provenance across the acoustic detection window. |
| NOAA currents | PUG1701/PUG1702/PUG1703 predictions cover the acoustic window and preserve bin/depth/flood/ebb metadata. |
| Weather / sea state | NDBC/CO-OPS records are aligned to acoustic windows as detectability/noise covariates. |
| Shoreline + bathymetry | Every forecast cell has `depth_m`, `nearest_shore_m`, `inside_land`, and source metadata. |
| OBIS + iNaturalist | Validation records preserve quality, evidence URL/media, license/citation, timestamp, and spatial provenance. |

## P1 Gate: Level 3 Prey / Spatial / Stronger Validation

P1 should start after P0 adapters are underway.

Priority order:

1. Fraser/Albion Chinook CPUE schema plus DART Bonneville fallback.
2. NOAA Marine Cadastre AIS bulk vessel/noise proxy.
3. WA DNR kelp, BC ShoreZone/CRIMS, NOAA MPA, Canada CPCAD.
4. WSDOT and BC ferry routes as effort proxies.
5. Orca Network and Center for Whale Research research requests.
6. Acartia/community-feed token if available.

## P1 Pass Conditions

| Source | Pass condition |
| --- | --- |
| Salmon prey | Non-climatology salmon index with source URL, schema, date coverage, and lag-scan support. |
| AIS / vessel proxy | Aggregated cell/time-bin vessel features exist; raw tracks are not directly modeled. |
| Habitat layers | Spatial features are clipped to the forecast grid and kept separate from effort proxies. |
| External validation | Permissioned or public labels are held out from fitting and carry reuse/citation rules. |

## P2 / Deferred

Defer:

- Happywhale, until account/export permission is clear.
- Public access points, until ferry/AIS/station effort residual gaps justify them.
- Fish Passage Center, as salmon-source sensitivity check only.

Reject for first pass:

- Public kayak/whale-watch route maps as ingested GIS.
- AccessAIS as a primary adapter.
- Commercial AIS vendors.

## Gate Refinement Rule

Do not promote a source to implementation just because it is interesting. It must satisfy one named integrity condition and have a defensible access/license path.
