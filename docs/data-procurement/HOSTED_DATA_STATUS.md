# Hosted Data Status

## S3 Hosting Target

`s3://198456344617-us-west-2-orcast-aws-backend-raw-payloads/`

Time-series layout:

`timeseries/{stream}/{station}/{YYYY}/{MM}.ndjson`

Set `ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads` when ingesting from a local shell.

## P0 Close-Out (2026-06-22)

### OrcaHello Reviewed Detector Outcomes

Stream: `orcahello_reviewed_detector_outcomes`

Adapter: dedicated v1.2 endpoints (`/confirmed`, `/falsepositives`, `/unknowns`, `/unreviewed`) via `OrcaHelloHistoryAdapter.fetch_reviewed_outcomes`.

Hosted summary:

- Stations: `haro_strait`, `orcasound_lab`, `north_san_juan_channel`, `andrews_bay`
- Records: `334`
- Span: `2020-09-28` to `2026-06-16`

Fit integration: `level0_detector_qc` now computes outcome counts, confirmed fraction, and false-positive rate in `modeling/fit_kernels.py`.

### OBIS Validation

Stream: `obis_verified/salish_sea`

Hosted summary:

- Records: `141`
- Fields: `license`, `citation`, `quality_grade`, `source_url`
- Span: `2020-07-12` to `2025-12-19`

### iNaturalist Validation

Stream: `inaturalist_verified/salish_sea`

Hosted summary:

- Records: `7`
- Fields: `license`, `citation`, `media_license`, `quality_grade`, `source_url`

### Spatial Grid Covariates (Per Forecast Cell)

Stream: `spatial_grid_covariates/san_juan_pilot`

Hosted summary:

- Records: `56` water grid cells at `0.05°` step
- Fields per cell: `cell_id`, `lat`, `lng`, `depth_m`, `nearest_shore_m`, `inside_land`

Provenance integration: `/api/provenance` now returns bathymetry/shoreline metadata via `spatial_enrichment.lookup_cell`.

### Prior P0 Streams (Still Hosted)

- `env_water_level`, `env_currents`, `noaa_ndbc_stdmet`, `shoreline_distance`
- `acoustic_detections`, `salmon_run_index`, `station_uptime`

## P1 Partial (2026-06-22)

| Stream | Status | Notes |
| --- | --- | --- |
| `ferry_effort_wa` | hosted metadata | WSDOT route snapshot XML (`1` record) |
| `ferry_effort_bc` | placeholder | BC route geometry still needs manual export |
| `protected_areas_ca` | placeholder | CPCAD export pending |
| `ais_vessel_traffic_erddap` | not hosted | PMEL ERDDAP dataset ID/query still needs correction |
| `habitat_bc_shorezone` | not hosted | BC ShoreZone REST query returned no features in pilot bbox |
| `protected_areas_us` | not hosted | NOAA MPA ArcGIS endpoint returned invalid URL |

## Next Actions

1. User lane (D): send research requests from Desktop `ORCAST Data Access Requests/` for Orca Network, CWR, Orcasound maintainers.
2. Fix AIS ERDDAP dataset ID or switch to Marine Cadastre bulk slice.
3. Pin BC ShoreZone / NOAA MPA working REST endpoints for clipped pilot pulls.
4. Re-run fit after P0 close-out so `fit_report.json` carries live `level0_detector_qc` and spatial metadata.
