# Wave Set G4 — D1–D4 data wiring status

**Date:** 2026-06-23  
**Charter:** [DATA_WIRING.md](../methodology/DATA_WIRING.md)

## Summary

D1–D4 are **substantially implemented in code**; production ingest runs on schedule. G4 documents status and remaining gaps — not a full re-build.

| Wave | Status | Evidence |
|------|--------|----------|
| **D1** | **done** | `src/aws_backend/timeseries.py` (S3 + memory store); `covariates.py`; adapters: `orcahello_history`, `noaa`, `salmon`, `obis`, `inaturalist`; `tests/aws_backend/test_timeseries.py` |
| **D2** | **done** | `ingest_timeseries.py` orchestration; `POST /api/timeseries/backfill`, `/refresh`; EventBridge scheduled ingestion in CFN |
| **D3** | **partial** | Live OBIS + iNaturalist enabled on App Runner; OrcaHello history returns 403 intermittently (logged) |
| **D4** | **partial** | `sources/bathymetry.py` + spatial grid streams; full GEBCO clip L3 deferred |

## Stream coverage (ingest module)

Implemented streams in `ingest_timeseries.py`: acoustic_detections, env_water_level, env_currents, salmon_run_index, station_uptime, obis_verified, inaturalist_verified, spatial grid, shoreline, NDBC, AIS, habitat, protected areas, ferry effort.

## Definition-of-done gaps

1. Single `/api/data-status` freshness dashboard (route exists; verify post-deploy)
2. OrcaHello archive backfill blocked by upstream 403 — document as external dependency
3. Bathymetry L3 static asset not yet wired into kernel spatial term

## Gate

```bash
PYTHONPATH=src pytest tests/aws_backend/test_timeseries.py -q
curl -sf "$BACKEND/api/data-status"
```
