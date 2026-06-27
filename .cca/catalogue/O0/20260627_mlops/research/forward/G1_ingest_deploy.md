# G1 ingest-deploy grounding (grounds W6 / O1)

Agent G1, W5 forward-path grounding wave. Investigation-first: this doc only. No
deploy, no production write, no promotion, no commit. Authority above this doc:
`20260627_mlops-handoff/HANDOFF_CHARTER.md` section B; campaign:
`20260627_mlops/CAMPAIGN_CHARTER.md` / `CAMPAIGN_DISPATCH.md` (G1).

Reads this wave (dry-run only):
- `src/aws_backend/ingest_multistation.py` (the recipe; dry-run validated)
- `src/aws_backend/ingest_timeseries.py` (`ingest_acoustic_reviewed_outcomes`,
  `_put_grouped_by_station`, grouping by `record["station"]`)
- `src/aws_backend/timeseries.py` (`S3TimeSeriesStore`, dedupe key `(t, id)`,
  partition layout)
- `.cca/.../WIRING-ingest.md`, `research/L2_data_volume.md` (RE),
  `research/SYNTHESIS_L2_L3.md` (RF, C2), `modeling/studies/level2_multistation.py`
  and `modeling/studies/reports/level2_multistation.json`
- cached index `.cca/.../orcahello_index.cache.json` (1359 records, B.9)

Dry-run reproduced locally this wave (`python -m src.aws_backend.ingest_multistation`,
MemoryTimeSeriesStore, no production touch): orcasound_lab 1029, andrews_bay 296 raw
to 265 stored, north_san_juan_channel 34; total 1359 raw to 1328 stored.

SERVED store (B.4): bucket `198456344617-us-west-2-orcast-aws-backend-raw-payloads`,
region `us-west-2`. The config default `orcast-raw-payloads` is WRONG (the footgun
that cost a session); the env must override it.

---

## 0. What this deploy is, and what it is not

The ingest reads the cached OrcaHello reviewed-outcome index and writes those rows
into the production `acoustic_detections` store under three new station prefixes
(`orcasound_lab`, `andrews_bay`, `north_san_juan_channel`). `haro_strait` is already
in production and is intentionally excluded (`EXTRA_NODES` does not contain it), so
the existing single-station stream is never touched by this write.

Two facts must travel together, because they look contradictory and are not:

- Against the SERVED store as it stands today (only `haro_strait`, ~761 detections),
  this write adds 1328 net-new served detections. That is the lever: it converts the
  served fit from single-station to four-station.
- Against the analysis universe RE and the multistation experiment already consume
  (which already includes the cache), this write adds ZERO new observations. It moves
  the same cached rows into the store. So it cannot push skill or cross-station
  consistency BEYOND what the four-station experiment already measured.

Both are true at once because they measure net-new against different baselines
(served store vs the cache-inclusive analysis). RE's "0 observations" (C2) is about
the analysis universe; the campaign's "net-new served detections is the real lever"
is about the served store. Section 3 reconciles the numbers.

---

## 1. Production deploy runbook

Target stream: `acoustic_detections`. Target store: S3 `S3TimeSeriesStore` over
bucket B.4, region `us-west-2`. Source: `DEFAULT_CACHE_PATH`
(`orcahello_index.cache.json`). Entry point: `ingest_multistation_acoustic(store, dry_run=False)`.

### 1.1 Idempotency and dedup key (station + window)

The store's identity model has three nested levels, all in `timeseries.py`:

- station: partition directory `timeseries/acoustic_detections/{station}/`
  (`S3TimeSeriesStore._prefix`). `_put_grouped_by_station` groups incoming rows by
  `record["station"]` before writing, so each node lands in its own prefix.
- window: monthly partition file `{YYYY}/{MM}.ndjson` keyed off each record's
  parsed `t` (`S3TimeSeriesStore._key`, `put_series` buckets `by_month`).
- within-partition row identity: `(str(t), str(id))` (`_record_key`); on write the
  partition is read, merged by that key with incoming winning, re-sorted by `t`, and
  rewritten (`_merge_records`, `put_series` read-modify-write).

So the effective idempotency key is `(station, t, id)`. Re-running the ingest is
idempotent: a second run reads the existing partition, merges the identical rows by
`(t, id)`, and rewrites the same content. No duplication, no growth.

Known, accepted dedup loss: the cached rows for these three nodes carry no `id`
(only `t`, `key`, `outcome`), so `build_acoustic_records` sets `id = None` and the
key collapses to `(t, "None")`. Distinct detections that share a timestamp therefore
merge. This is exactly why andrews_bay is 296 raw to 265 stored (31 same-timestamp
collisions). The cache does not carry enough identity to separate them; this is
reported honestly, not silently dropped, and is stable across re-runs.

### 1.2 Backfill window and oldest-first handling

This ingest reads a finite cached list, not the live `fetch_history` pager, so the
oldest-first / heavy-paging hazard does NOT apply to this write. `fetch_history`
returns oldest-first (early pages are all Haro Strait) and the live history API 403s
/ SSL-EOFs on heavy paging (B.9); the recipe sidesteps both by consuming the cached
reviewed-outcome index that was already built from the reviewed-outcome endpoints.

Backfill window written = the full cache span per node (from the cache and RE):

| node | cache span | implied monthly partitions |
|---|---|---:|
| orcasound_lab | 2020-09-28 to 2026-06-15 (~5.7 yr) | ~70 `YYYY/MM.ndjson` |
| north_san_juan_channel | 2025-04-16 to 2026-03-29 (~0.95 yr) | ~12 |
| andrews_bay | 2026-02-06 to 2026-06-16 (~0.35 yr) | ~5 |

The oldest-first concern returns only if a future LIVE refresh is wired (see 1.4);
it is not part of the W6 one-shot backfill.

### 1.3 Partition and schema

Layout (matches the production single-station ingest exactly):

```
timeseries/acoustic_detections/orcasound_lab/2020/09.ndjson
timeseries/acoustic_detections/orcasound_lab/2020/10.ndjson
...
timeseries/acoustic_detections/north_san_juan_channel/2025/04.ndjson
timeseries/acoustic_detections/andrews_bay/2026/02.ndjson
```

NDJSON, one record per line, `application/x-ndjson`. Per-record schema emitted by
`build_acoustic_records` (mirrors the production OrcaHello acoustic record shape):
`t`, `id` (null for these nodes), `station`, `latitude`, `longitude`, `confidence`
(mostly null for these nodes; the confidence cache overlaps only a handful of rows),
`reviewed`, `found`, `confirmed`, `outcome`, `source: "orcahello_index_cache"`. The
`source` and `outcome` fields are provenance markers that let downstream tell these
cached reviewed-outcome rows apart from a live `fetch_history` pull; keep them.

Outcome policy (a modeling decision to record at gate time, not an ingest one):
default keeps all reviewed outcomes (confirmed / false_positive / unknown /
unreviewed), matching the production `fetch_history` behavior. The confirmed-only
variant (`outcomes=("confirmed",)`) yields orcasound_lab 572, andrews_bay 264,
north_san_juan_channel 28, which lowers N and makes the consistency bar harder, not
easier.

### 1.4 Rate-limit, 403 retry/backoff

This W6 write makes NO OrcaHello calls (it reads a local cache file), so there is no
OrcaHello rate-limit or 403 surface for the deploy itself. The only network surface
is S3 (`get_object` per partition to read existing content, `put_object` to write).
Use boto3 standard/adaptive retries (transient 5xx, throttling); the writes are tiny
and serial, so throttling is not expected.

The 403 / backoff guidance is reserved for any FUTURE live forward-refresh of these
nodes (not in W6): go through the reviewed-outcome endpoints (never `fetch_history`
for multi-station), cap pages, use exponential backoff with jitter, and fall back to
the cache on repeated 403/SSL-EOF. Do NOT add the cached ingest to `backfill_all` /
`refresh_recent` (per WIRING): those run the live adapter; this is a one-shot,
separately invoked, gated backfill.

Concurrency note: `put_series` is read-modify-write per partition and is NOT
safe under concurrent writers (last writer wins the whole partition). Run a single
ingest writer; ensure no `refresh_recent` job touches `acoustic_detections` for these
prefixes during the deploy window.

### 1.5 Cost estimate

Data volume is trivial: 1328 records times roughly 250 to 350 bytes per NDJSON line
is on the order of 400 KB total across roughly 90 monthly partition objects
(orcasound_lab ~70 + nsj ~12 + andrews_bay ~5). S3 request count for a clean first
write is about one `get_object` (mostly `NoSuchKey`) plus one `put_object` per
partition, so on the order of ~90 GET + ~90 PUT, i.e. ~180 requests. At us-west-2
list/read/write pricing this is a fraction of one US cent for requests and effectively
zero for storage. There is no compute cost (no fit runs during the write). The real
cost is operator review time and the gate, not AWS spend.

### 1.6 Observability

Capture before, during, and after:

- Pre-write: `store.list_stations("acoustic_detections")` should return exactly
  `["haro_strait"]`. Record it (this is also the rollback target). If any of the
  three nodes already appear, STOP and reconcile (collision with a prior partial
  write).
- The write returns a summary with `raw_records_by_station`,
  `stored_records_by_station`, `total_stored`; assert it equals the dry-run:
  orcasound_lab 1029, andrews_bay 265, north_san_juan_channel 34, total 1328.
- Post-write per-station verification: re-read each node via
  `get_series("acoustic_detections", node, wide0, wide1)` and assert the count equals
  the stored count above. Confirm `list_stations` is now
  `[andrews_bay, haro_strait, north_san_juan_channel, orcasound_lab]`.
- Gaps: per node, compare the set of written `YYYY/MM` partitions against the
  expected span in 1.2 (orcasound_lab should be near-continuous 2020-09 to 2026-06;
  the sparse nodes have legitimately short spans). Sparse months are expected for the
  low-rate nodes and are not an error; a missing month inside orcasound_lab's dense
  span is. `timeseries_status` / `_stream_status` gives `first_t` / `last_t` per
  stream for a quick span check.
- Provenance audit: spot-read a few rows and confirm `source == "orcahello_index_cache"`
  and `haro_strait` rows are untouched (no `source` rewrite).

### 1.7 ROLLBACK procedure

Rollback is clean because the write only ADDS three brand-new station prefixes and
never mutates `haro_strait`:

1. Confirm the pre-write target recorded in 1.6 was `["haro_strait"]` (the three new
   prefixes did not previously exist).
2. Delete the three added prefixes and nothing else:
   `timeseries/acoustic_detections/orcasound_lab/`,
   `timeseries/acoustic_detections/andrews_bay/`,
   `timeseries/acoustic_detections/north_san_juan_channel/`
   (enumerate keys via the `list_objects_v2` paginator already in
   `_list_partition_keys`, then delete those keys). NEVER touch
   `timeseries/acoustic_detections/haro_strait/`.
3. Verify `list_stations("acoustic_detections")` is back to `["haro_strait"]`.
4. If bucket versioning is enabled, prefer restoring to the recorded pre-write state
   over hard delete; if not, the prefix delete is sufficient because the data is
   net-new (nothing pre-existing to restore).

Effect of rollback on modeling: the served fit reverts to single-station
`haro_strait` and its held-out CV mean-deviance-skill returns to the -0.047 baseline.
No model artifact is written by the ingest itself, so there is nothing else to undo.

---

## 2. Pre-deploy gate checklist (must all be true before the operator approves the write)

- [ ] Env verified: `ORCAST_STORAGE_BACKEND=aws`,
  `ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads`,
  `AWS_REGION=us-west-2` (B.4 footgun: the config default bucket is wrong).
- [ ] Pre-write read confirms `store.list_stations("acoustic_detections") == ["haro_strait"]`
  (the three target prefixes are absent, so no collision; this value is recorded as
  the rollback target).
- [ ] Dry-run reproduced on the deploy host and matches this doc: orcasound_lab 1029,
  andrews_bay 265, north_san_juan_channel 34, total_stored 1328.
- [ ] Outcome policy decided and recorded: all-outcomes (default) vs confirmed-only
  (572/264/28). Default is recommended to mirror production `fetch_history`.
- [ ] Single writer guaranteed: no `refresh_recent` / `backfill_all` job writing
  `acoustic_detections` during the deploy window (read-modify-write is not
  concurrency-safe).
- [ ] Rollback prerequisites in hand: bucket versioning status known; pre-write
  station list recorded; the prefix-delete plan (1.7) reviewed; haro_strait
  explicitly out of scope.
- [ ] This is a one-shot backfill only; it is NOT wired into `backfill_all` /
  `refresh_recent`.
- [ ] No confidence promotion is bundled with this deploy. The write does not run a
  fit and does not call `promotion/supervisor.py`. Served `effective_confidence`
  stays 0.0; promotion is W7, separate, supervisor-gated (B.1).
- [ ] `mlops-gate` is green before the deploy and the deploy changes no tracked model
  artifact (B.6/B.8).
- [ ] Operator deploy approval recorded (W6 gate; B.1 / campaign sec 6).

---

## 3. Net-new-detection estimate (the served CV-skill lever)

Dry-run, this wave (stored = after `(t, id)` dedupe):

| node | raw cache | stored | already in SERVED store today | net-new to SERVED store |
|---|---:|---:|---:|---:|
| orcasound_lab | 1029 | 1029 | 0 | +1029 |
| andrews_bay | 296 | 265 | 0 | +265 |
| north_san_juan_channel | 34 | 34 | 0 | +34 |
| (haro_strait, already served) | n/a | n/a | ~761 | 0 (untouched) |
| total added | 1359 | 1328 | ~761 | +1328 |

Two net-new readings, reconciled (this is the crux RE and the campaign each pin
from a different baseline):

- Net-new to the SERVED store: +1328 (1029 / 265 / 34). The served store holds only
  `haro_strait` today, so every one of these rows is new TO THE STORE and TO THE
  SERVED FIT, which has only ever seen `haro_strait`. This is the lever.
- Net-new to the analysis universe / fresh observations: 0. These are the identical
  cached rows the multistation experiment and RE's power analysis already consume.
  The ingest fetches nothing beyond the cache (the live API 403s), so it cannot move
  any metric BEYOND the already-measured four-station value.

Expected served fit after the ingest = the four-station experiment, exactly, because
the served store then contains the same four stations the experiment combined in
memory (`level2_multistation.py`: production `haro_strait` from S3 + the three cached
nodes). Measured experiment values (`level2_multistation.json`):

- n_detections 2089 (761 haro_strait + 1328 added), 4 acoustic stations.
- held-out CV mean-deviance-skill +0.07779744, 4/5 folds passing, vs the
  single-station served baseline -0.04730031.
- internal gate score `confidence_unpromoted` 0.5 (NOT a promotion).
- cross-station still NOT consistent (`can_clear_0p5_bar_honestly: false`): diel/tide
  noise-artifact, season coverage-confounded, lunar genuine-heterogeneity; and
  time-rescaling WITHHELD (event-level KS p=0.0, encounter-level p~7.5e-22).

Per-node contribution to the skill lever (assumptions stated):

- orcasound_lab (+1029) is the load-bearing node: it is the single largest mass, more
  than `haro_strait` itself, and carries the densest, longest span (2020 to 2026). It
  is what flips the served fit from single-station to a real multi-station fit and
  drives most of the +0.078.
- andrews_bay (+265) is a modest, mostly-recent (4-month span) add; it contributes
  some independent station signal but its short span makes its long-run rate
  uncertain (RE: the ~835/yr implied rate is a short-window overestimate).
- north_san_juan_channel (+34) is negligible for CV-skill (too sparse to fit a stable
  per-station curve); its value is completing the four-station cross-station test, not
  moving skill.

Is +1328 enough to push served CV-skill toward the +0.078 the four-station
experiment shows? Yes, for the CV-skill COMPONENT specifically: landing all three
nodes reproduces the experiment's configuration, so the served held-out CV skill
should land at approximately +0.078 (4/5 folds), turning the served single-station
-0.047 positive. Assumptions: same cache, same harmonic-tide currents + uptime from
S3, same `bin_hours=1.0` joint fit, `write_outputs=False` so no artifact side-effect
(B.5). Caveats that keep this honest:

- It reproduces the experiment value; it does not exceed it (0 new observations).
- Positive served CV-skill is necessary but NOT sufficient for L2: the FULL gate also
  needs cross-station consistency (unmet) and the timing gate (withheld event-level;
  the bin-level redefinition is a separate operator-gated change, G1/RD). So even with
  served CV-skill at +0.078, the multistation gate stays FAIL today and promotion
  requires G2's fold-stable "robustly positive" definition plus a recorded supervisor
  decision (W7).
- The +0.078 is 4/5 folds; G2 must decide whether 4/5 with this margin clears a
  fold-stability bar before any promotion. That sign-off is G2's, not G1's.

---

## 4. Go / no-go for W6

GO to deploy the plumbing, gated on operator deploy approval (W6 gate). The write is
safe, reversible, near-zero cost, idempotent, and leaves `haro_strait` untouched; it
is the correct precondition for both L2 blockers and for forward accumulation, and it
makes the served fit equal the four-station experiment (served CV-skill ~ +0.078,
4/5 folds).

Explicitly NOT a confidence change: the deploy promotes nothing (served
`effective_confidence` stays 0.0), does not by itself clear cross-station consistency
or the timing gate, and adds zero observations beyond the cache. W7 promotion remains
separately supervisor-gated on G2's robust-skill definition.

Residual risks:

1. Mistaking plumbing for a fix (RF C2, highest narrative risk). The ingest must be
   communicated as forward-accumulation plumbing, not a cross-station consistency fix;
   on today's data the 0.5 bar stays unmet (`can_clear_0p5_bar_honestly: false`).
2. Confidence-cliff. A naive `_confidence_from_gates` could jump confidence to 1.0 on
   positive skill; the P0 confidence-cliff fix mitigates and, regardless, promotion is
   separately gated (W7), so no automatic promotion can ride this deploy. Verify P0 is
   in place and that the deploy runs no fit.
3. andrews_bay `(t, id)` collapse (296 to 265): same-timestamp rows merge because the
   cache has no `id`. Accepted and reported; stable across re-runs.
4. Provenance mixing: served `acoustic_detections` becomes part live `haro_strait`
   stream, part cached reviewed-outcome rows (`source: "orcahello_index_cache"`).
   Keep the `source`/`outcome` fields so downstream can distinguish.
5. Sparse/null confidence on the new nodes (the plain cache has no confidence for
   them); fine for presence-timing kernels but note it for any confidence-weighted
   downstream use.
6. Concurrency on read-modify-write partitions; enforce a single writer during deploy.
7. tide instability is unaffected by the ingest (RE: negative split-half at 8/12 bins);
   do not expect the added data to make tide reliable.

---

## Return summary

- Doc path: `.cca/catalogue/O0/20260627_mlops/research/forward/G1_ingest_deploy.md`
- Runbook summary: one-shot, operator-gated write of the cached reviewed-outcome
  rows for `orcasound_lab` / `andrews_bay` / `north_san_juan_channel` into the SERVED
  `acoustic_detections` store (bucket B.4, us-west-2) via
  `ingest_multistation_acoustic(store, dry_run=False)`. Idempotency key `(station, t, id)`
  with monthly `YYYY/MM.ndjson` partitions; merge-by-key, re-runnable. Reads the
  cache (no `fetch_history`), so no oldest-first / 403 surface for the deploy; only S3
  GET/PUT, ~180 requests, fractions of a cent. Observability: pre-write
  `list_stations == [haro_strait]`, assert stored counts 1029/265/34 (total 1328),
  per-node span/gap check, provenance audit. Rollback: delete only the three new
  station prefixes (haro_strait never touched), reverting the served fit to -0.047.
- Net-new estimate: +1328 served detections (orcasound_lab +1029, andrews_bay +265,
  north_san_juan_channel +34) net-new TO THE SERVED STORE, but 0 net-new observations
  to the analysis universe (same cached rows the experiment already used). This
  reproduces the four-station experiment: served CV skill goes from -0.047 to
  approximately +0.078 (4/5 folds). orcasound_lab is the load-bearing node; nsj (34)
  is negligible for skill. Enough to move the served CV-skill COMPONENT to +0.078, but
  not enough on its own to pass L2 (cross-station consistency unmet, timing gate
  withheld) and not a promotion.
- Go/no-go: GO to deploy (gated on operator approval); it is safe, reversible, and the
  correct precondition for W7. NO-GO on treating it as a consistency fix or a
  confidence change. Top residual risk: communicating plumbing as a fix (RF C2).
