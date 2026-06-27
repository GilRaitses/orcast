# WIRING-ingest: multi-station acoustic ingest (Agent D, Wave 1)

Location decision: this doc lives in the mlops waveset home
(`.cca/catalogue/O0/20260627_mlops/WIRING-ingest.md`), alongside the other Wave 1
wiring specs. The module it wires is `src/aws_backend/ingest_multistation.py`.

Scope: tell the backend integrator (Wave 2, sole editor of
`src/aws_backend/ingest_timeseries.py`) how to wire the multi-station nodes into
the production `acoustic_detections` stream, and how the deploy-gated production
run is invoked. Wave 1 is DRY-RUN ONLY; no production write happened.

## What the module provides

`src/aws_backend/ingest_multistation.py` (new, owned by Agent D; does not edit any
convergence file). It reuses, not redefines, the production grouping:

```python
from src.aws_backend.ingest_timeseries import ACOUSTIC, _put_grouped_by_station
```

Exported API:

- `build_acoustic_records(cache_path=DEFAULT_CACHE_PATH, stations=EXTRA_NODES, outcomes=None, confidence_cache_path=DEFAULT_CONFIDENCE_CACHE_PATH) -> list[dict]`
  Maps cached OrcaHello reviewed-outcome rows to `acoustic_detections` records,
  each keyed by `record["station"]` and shaped like the production OrcaHello
  acoustic record (`t`, `station`, `latitude`, `longitude`, `confidence`,
  `reviewed`, `found`, `confirmed`, plus `outcome` and `source`).
- `ingest_multistation_acoustic(store=None, cache_path=DEFAULT_CACHE_PATH, stations=EXTRA_NODES, outcomes=None, dry_run=True, confidence_cache_path=DEFAULT_CONFIDENCE_CACHE_PATH) -> dict`
  The callable the task asked for: takes a store + the cached index path, groups
  by station via `_put_grouped_by_station`, and **defaults to `dry_run=True`**.

Constants:
- `EXTRA_NODES` — the 3 in-region nodes missing from production and their coords
  (`orcasound_lab`, `north_san_juan_channel`, `andrews_bay`). `haro_strait` is
  intentionally excluded (already in production).
- `DEFAULT_CACHE_PATH` — `.cca/.../orcahello_index.cache.json` (charter B.9).
- `DEFAULT_CONFIDENCE_CACHE_PATH` — `orcahello_index.confidence.cache.json`, used
  only as an optional per-record confidence enrichment join on `(key, t)`.

### Dry-run vs production semantics

- `dry_run=True` (default): does NOT write the production store. It builds + groups
  records, then probes a throwaway `MemoryTimeSeriesStore` to measure the
  post-dedupe stored count, and returns both `raw_records_by_station` and
  `stored_records_by_station`. The store's dedupe key is `(t, id)` (see
  `timeseries._record_key` / `_merge_records`); the cache rows have no `id`, so
  rows sharing a timestamp collapse on write (this is why andrews_bay 296 raw
  becomes 265 stored).
- `dry_run=False`: operator/deploy-gated production path. Requires an explicit
  `store`; raises `ValueError` if `store is None`. Writes via
  `_put_grouped_by_station(store, ACOUSTIC, records)`.

## How to wire it into ingest_timeseries.py (Wave 2 integrator)

`ingest_timeseries.py` is a convergence file; Agent D did not edit it. The
integrator adds a thin wrapper that mirrors the existing `ingest_*` helpers and
delegates to the new module. Suggested addition (NOT applied this wave):

```python
# near the other imports in ingest_timeseries.py
from .ingest_multistation import ingest_multistation_acoustic

def ingest_acoustic_multistation_cached(
    store: Optional[Any] = None,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """Ingest the 3 extra in-region OrcaHello nodes into acoustic_detections
    from the cached reviewed-outcome index (charter B.9). Dry-run by default;
    the production write is operator/deploy-gated."""
    ts = _resolve_store(store)
    return ingest_multistation_acoustic(store=ts, dry_run=dry_run)
```

Notes for the integrator:
- This reuses `_put_grouped_by_station` and the `ACOUSTIC` constant already in
  `ingest_timeseries.py`; nothing in that file needs to change beyond adding the
  import + wrapper.
- Do NOT add this to `backfill_all` / `refresh_recent` as a default. Those run on
  the live `OrcaHelloHistoryAdapter`; the cached multi-station ingest is a
  one-shot backfill of historical reviewed outcomes, not a recurring refresh.
  Keep it a separately invoked, gated step.
- Provenance honesty: these records carry `source: "orcahello_index_cache"` and
  an `outcome` field; they are the reviewed-outcome cache, distinct from a live
  `fetch_history` pull. Keep that field so downstream can tell provenance apart.

## How the deploy-gated production run is invoked (Wave 2, operator gate)

The actual write to the production `acoustic_detections` store is operator/deploy
-gated (charter F, HANDOFF_CHARTER dispatch table). Once gated, run under `.venv`
with the AWS store env (charter B.4):

```bash
ORCAST_STORAGE_BACKEND=aws \
ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads \
AWS_REGION=us-west-2 PYTHONPATH=. \
.venv/bin/python -c "
from src.aws_backend.timeseries import build_timeseries_store
from src.aws_backend.config import settings
from src.aws_backend.ingest_multistation import ingest_multistation_acoustic
store = build_timeseries_store(settings)  # S3 store under the env above
print(ingest_multistation_acoustic(store=store, dry_run=False))
"
```

This writes `timeseries/acoustic_detections/{orcasound_lab,andrews_bay,north_san_juan_channel}/YYYY/MM.ndjson`
partitions next to the existing `haro_strait` partitions, deduping by `(t, id)`
against anything already present. Re-running is idempotent (merge-by-key).

Pre-write check (still dry-run, but against the real S3 store, to confirm no
collision with existing partitions) can be done by reading
`store.list_stations("acoustic_detections")` first; today that returns only
`haro_strait`.

## Dry-run result (measured this wave, `.venv`)

Command: `.venv/bin/python -m src.aws_backend.ingest_multistation`

| station | raw cache records | stored after `(t,id)` dedupe |
|---|---:|---:|
| orcasound_lab | 1029 | 1029 |
| andrews_bay | 296 | 265 |
| north_san_juan_channel | 34 | 34 |
| total | 1359 | 1328 |

`confirmed`-only variant (`outcomes=("confirmed",)`), for reference: orcasound_lab
572, andrews_bay 264, north_san_juan_channel 28.

## Risks / honesty

- The cache mixes review outcomes (confirmed / false_positive / unknown /
  unreviewed). The default ingest keeps all of them (matching the production
  `fetch_history` behavior, which stores all in-region detections and records the
  review state). If the temporal kernel should consume confirmed presence only,
  pass `outcomes=("confirmed",)` at wire time — that is a modeling decision, not
  an ingest one.
- `andrews_bay` loses 31 records to the `(t, id)` dedupe because the cache rows
  have no `id` and several share a timestamp. If true distinct detections share a
  timestamp, they collapse; the cache does not carry enough identity to tell them
  apart. Reported honestly as 296 raw -> 265 stored.
- Confidence is sparse for these 3 nodes: the plain cache has no `confidence`
  field for them, and the confidence cache only overlaps a handful of rows, so
  most multi-station records store `confidence: null`. Stated, not faked.
- This is the cached reviewed-outcome index, not a fresh live pull; it is the
  charter-blessed source (B.9) because the live history API 403s/SSL-EOFs on heavy
  paging. If a fresh live multi-station pull is later wanted, it must go through
  the reviewed-outcome endpoints, not `fetch_history`.
