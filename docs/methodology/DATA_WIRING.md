# Data wiring: the prerequisite layer

**Waves registry:** [WAVES_REGISTRY.md](../devpost/WAVES_REGISTRY.md) (canonical IDs D1–D4).

Gate principle: nothing in the forecast program (covariate library, PSTH, kernel fitting, forecast surface, instrument-panel UX) starts until every data source below is ingested, stored, scheduled, and validated. This doc is the definition of "all data wired" and the build waves to get there. Methodology context: [FORECAST_KERNELS.md](FORECAST_KERNELS.md), [CALIBRATION_STUDIES.md](CALIBRATION_STUDIES.md).

## Locked defaults

- Time-series history: **S3 partitioned NDJSON** under a `timeseries/<stream>/<station>/<yyyy>/<mm>.ndjson` layout (reuse the existing raw bucket prefix for now; a dedicated bucket later). The existing DynamoDB tables keep serving "latest"/entity reads. Parquet is a later optimization.
- Salmon: **Albion Chinook test fishery** (Fraser run, most SRKW-relevant) as primary; **DART** (Bonneville/Columbia) secondary.
- Bathymetry: **GEBCO/NOAA** grid clipped to the archipelago, deferred to the spatial term (L3), not in the first waves.

## Inventory and target state

| # | Stream | Source | Target | Schedule |
|---|--------|--------|--------|----------|
| 1 | acoustic_detections | OrcaHello API (history + ongoing) | S3 history + latest cache | backfill once, then hourly |
| 2 | visual_sightings | OBIS API (live, not seed) | sightings store | daily |
| 3 | visual_sightings | iNaturalist (enable) | sightings store | daily |
| 4 | community | submissions (wired) | existing | live |
| 5 | env_water_level | NOAA CO-OPS historical + latest | S3 series + latest | backfill, then hourly |
| 6 | env_currents | NOAA currents station(s) | S3 series + latest | backfill, then hourly |
| 7 | covariate_diel_solar | computed (ephemeris) | on-demand (no store) | n/a |
| 8 | covariate_lunar | computed (ephemeris) | on-demand (no store) | n/a |
| 9 | salmon_run_index | Albion + DART | S3 series | daily/seasonal |
| 10 | bathymetry | GEBCO/NOAA (L3) | static asset | one-time |
| 11 | water_mask | data/geo (done) | shipped | done |
| 12 | station_uptime | hydrophone status polling | S3 series | hourly |
| 13 | visual_effort | proxy model (later) | derived | n/a |

## Storage contract (shared)

A `TimeSeriesStore` abstraction (S3 + in-memory for tests):

```
put_series(stream: str, station: str, records: list[dict]) -> int   # records carry an ISO 't'
get_series(stream: str, station: str, start: datetime, end: datetime) -> list[dict]
list_stations(stream: str) -> list[str]
```

Backed by S3 NDJSON (append/merge per month partition); MemoryStore mirror for local/tests. All adapters write through this; the offline fitting reads through it.

## Build waves (all gate the modeling work)

### D1 — independent fetchers + compute + storage (no deploy, code + tests)
- `timeseries.py` - the TimeSeriesStore (S3 NDJSON + memory) + tests.
- `covariates.py` - pure compute: solar (sunrise/sunset, daylight, solar elevation), diel hour-angle, lunar phase/illumination from (timestamp, lat, lng). No deps beyond stdlib math; tests against known dates.
- `sources/orcahello_history.py` - paged pull of the full OrcaHello archive (in-region + all), normalized to acoustic-detection records (timestamp, station, lat, lng, confidence, reviewed/found labels). Tests with a mocked paged payload.
- `sources/noaa.py` (extend) - historical date-range pull for water level + add a currents station; return series. Tests with mocked NOAA JSON.
- `sources/salmon.py` - Albion + DART run-timing index adapter; return a daily index series. Tests with mocked source payload.

### D2 — ingest orchestration + backfill + schedule + deploy
- An ingest orchestrator that pulls each adapter and writes via TimeSeriesStore; a one-time backfill entrypoint; wire into the scheduled ingestion; infra for any new bucket/prefix; deploy. Backfill the OrcaHello + NOAA history.

### D3 — real sightings + effort
- Replace OBIS local seed with the live OBIS API; enable iNaturalist; start station-uptime logging.

### D4 — spatial inputs (for L3)
- Bathymetry static layer (GEBCO/NOAA clip).

## Definition of done ("all data wired")

- Every stream 1-9 and 12 ingests on schedule and backfills its available history into the store.
- `get_series` returns coherent, in-region, deduplicated, timestamped data for each stream.
- A single status view reports per-stream freshness, record counts, and coverage span.
- Covariate compute returns correct solar/lunar/diel values (validated against reference dates).
- Only then does the forecast/kernel program (PSTH, fitting, surface, instrument-panel UX) begin.

## Out of scope here
- Any kernel fitting, PSTH, forecast rendering, or UX. Those are gated on this being complete.
