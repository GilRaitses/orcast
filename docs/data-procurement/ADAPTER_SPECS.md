# ORCAST Data Procurement Adapter Specs

## Implementation Order

### P0: Integrity For Current Level 1-2 Claims

1. OrcaHello reviewed detector outcomes.
2. Station uptime / effort offset.
3. NOAA historical current predictions overlapping acoustic window.
4. NOAA/NDBC detectability covariates.
5. Shoreline/bathymetry spatial basics.
6. OBIS/iNaturalist validation tightening.

### P1: Level 3 Spatial/Prey And Stronger Validation

1. Fraser/Albion + DART salmon prey index.
2. AIS vessel/noise proxy.
3. Kelp/eelgrass/protected-area spatial covariates.
4. Orca Network / CWR research-request validation labels.

## Adapter Specs

### OrcaHello Reviewed Detector Outcomes

- File: extend `src/aws_backend/sources/orcahello_history.py`.
- Stream: `orcahello_reviewed_detector_outcomes`.
- Integrity label: `input_integrity`.
- Record:

```json
{
  "t": "ISO8601",
  "id": "detection id",
  "station": "hydrophone name/key",
  "latitude": 48.0,
  "longitude": -123.0,
  "confidence": 0.0,
  "reviewed": true,
  "found": "yes|no|unknown",
  "confirmed": true,
  "outcome": "confirmed|false_positive|unknown|unreviewed",
  "audio_uri": "https://...",
  "spectrogram_uri": "https://..."
}
```

- Fit integration:
  - Level 0 detector report: counts by outcome, false-positive rate, confirmed fraction, unknown fraction.
  - Use reviewed labels to separate detector QC from acoustic spike-train fitting.
- UI label:
  - `Detector QC`: live when reviewed outcome distribution is present.

### Station Uptime / Effort Offset

- Files: extend `src/aws_backend/sources/orcasound.py` or add `src/aws_backend/sources/uptime.py`.
- Stream: `station_uptime`.
- Integrity label: `effort_offset`.
- Source hierarchy:
  1. SeaStats `recordingCoverage` if station key mapping is confirmed.
  2. Orcanode Monitor event/status API if maintainers confirm access.
  3. S3 segment inventory fallback.
- Record:

```json
{
  "t": "ISO8601",
  "id": "station-hour-id",
  "station": "haro_strait",
  "source": "seastats|orcanode_monitor|s3_inventory",
  "up": 1,
  "status": "online|offline|partial|unknown",
  "coverage_fraction": 0.0,
  "node_name": "rpi_orcasound_lab"
}
```

- Fit integration:
  - `modeling/design.py` already consumes station uptime as exposure.
- UI label:
  - Replace `Effort assumed continuous` with `Effort offset active` when available.

### NOAA CO-OPS Current Predictions

- File: extend `src/aws_backend/sources/noaa.py`.
- Stream: `noaa_coops_current_predictions`.
- Integrity label: `kernel_identifiability`.
- Stations:
  - PUG1701 Deception Pass.
  - PUG1702 Rosario Strait.
  - PUG1703 San Juan Channel south entrance.
- Product:
  - `currents_predictions`, `interval=60`, `time_zone=gmt`, `units=english`, monthly chunks.
- Record:

```json
{
  "t": "ISO8601",
  "station": "PUG1702",
  "product": "currents_predictions",
  "velocity_major_knots": -1.17,
  "speed_knots": 1.17,
  "bin": "16",
  "depth_ft": 47.0,
  "mean_flood_dir_deg": 357,
  "mean_ebb_dir_deg": 190,
  "source_url": "https://api.tidesandcurrents.noaa.gov/..."
}
```

- Fit integration:
  - Tide phase can be computed against the actual acoustic window.
  - Only fit `k_tide` when overlap exists.
- UI label:
  - `Tide kernel withheld` becomes `Tide kernel fitted` when overlap and phase coverage pass.

### NOAA/NDBC Weather And Sea State

- Files: add `src/aws_backend/sources/ndbc.py`; optionally extend `noaa.py` for CO-OPS met.
- Streams:
  - `noaa_ndbc_stdmet`
  - `noaa_coops_met`
- Integrity label: `detectability_noise`.
- Stations:
  - P0: NDBC 46088, CO-OPS/NDBC Friday Harbor 9449880/FRDW1.
  - P1: Port Townsend 9444900/PTWW1, Smith Island SISW1.
- Record:

```json
{
  "t": "ISO8601",
  "station": "46088",
  "latitude": 48.332,
  "longitude": -123.179,
  "wind_speed_m_s": 5.2,
  "wind_gust_m_s": 7.1,
  "wave_height_m": 0.8,
  "dominant_wave_period_s": 6.0,
  "pressure_hpa": 1013.2,
  "air_temp_c": 12.0,
  "water_temp_c": 9.4
}
```

- Fit integration:
  - First pass: detector/detectability covariate, not animal-behavior kernel.
  - Use to explain detector performance and visual effort quality.

### Shoreline Distance / Bathymetry

- Files:
  - keep `src/aws_backend/sources/bathymetry.py`
  - add `src/aws_backend/sources/shoreline.py`
- Streams:
  - `bathymetry`
  - `shoreline_distance`
- Integrity label: `spatial_covariate`.
- Record:

```json
{
  "cell_id": "grid-id",
  "lat": 48.5,
  "lng": -123.0,
  "depth_m": -120.0,
  "nearest_shore_m": 500.0,
  "inside_land": false
}
```

- Fit integration:
  - Future `s_space`.
  - For now, use as spatial integrity metadata in provenance.

### OBIS / iNaturalist Validation

- Files: extend `src/aws_backend/sources/obis.py`, `src/aws_backend/sources/inaturalist.py`.
- Streams:
  - `obis_verified`
  - `inaturalist_verified`
- Integrity label: `external_validation`.
- Add fields:
  - license
  - citation
  - quality grade
  - media/evidence license when present
- Fit integration:
  - Held-out validation, not temporal kernel training.

## P1 Adapter Specs

### Salmon / Prey Index

- File: fix/extend `src/aws_backend/sources/salmon.py`.
- Stream: `salmon_run_index`.
- Sources:
  - DART Bonneville public CSV as immediate fallback.
  - Fraser/Albion PSC/DFO report download once schema is pinned.
- Record:

```json
{
  "t": "YYYY-MM-DD",
  "fraser_index": 0.0,
  "columbia_index": 0.0,
  "run_index": 0.0,
  "source": "albion|dart|climatology_fallback",
  "source_url": "https://..."
}
```

- Fit integration:
  - Future `k_salmon`.
  - Do not treat climatology fallback as validated prey signal.

### AIS Vessel / Noise Proxy

- File: add `src/aws_backend/sources/ais.py`.
- Streams:
  - `ais_vessel_traffic_erddap`
  - `ais_vessel_traffic_bulk`
- Integrity label: `detectability_noise` / `effort_offset`.
- Record after aggregation:

```json
{
  "t": "ISO8601 time-bin start",
  "grid_cell_id": "grid-id",
  "vessel_count": 12,
  "vessel_minutes": 45.0,
  "large_vessel_presence": 1.0,
  "speed_weighted_presence": 3.2
}
```

- Fit integration:
  - Detector/noise proxy and observation-effort covariate.
  - Do not treat vessel traffic as habitat preference.

### Habitat / Protected Areas / Ferry Effort

- Files:
  - `src/aws_backend/sources/habitat.py`
  - `src/aws_backend/sources/ferries.py`
  - `src/aws_backend/sources/protected_areas.py`
- Streams:
  - `kelp_canopy_wa`
  - `habitat_bc_shorezone`
  - `protected_areas_us`
  - `protected_areas_ca`
  - `ferry_effort_wa`
  - `ferry_effort_bc`
- Integration:
  - `s_space` and observation-effort controls.
  - Keep ecological spatial covariates separate from effort proxies.

## Model Integration Labels

| Source group | Model role | UI integrity label |
| --- | --- | --- |
| OrcaHello reviewed labels | Level 0 detector QC | `Detector QC active` |
| Station uptime | exposure offset | `Effort offset active` |
| NOAA currents | tide kernel identifiability | `Tide covariate aligned` |
| NDBC/CO-OPS weather | detectability/noise | `Detectability conditions included` |
| Salmon | prey kernel | `Prey index active` |
| AIS/ferries/access | effort/noise proxy | `Vessel/observer effort proxy active` |
| Bathymetry/shoreline/habitat | spatial kernel | `Spatial covariates active` |
| OBIS/iNat/CWR/Orca Network | held-out validation | `External validation active` |
