# TB1 -- Port Townsend + Bush Point (OrcaHello), widened region gate

Subagent TB1, graduation waveset (Wave TB, the +0.144 lever lane). Repo `/Users/gilraitses/orcast`.
Date 2026-06-27 (America/New_York). This doc only; no other file written, no production fetch-that-
writes, no ingest, no convergence-file edit, no deploy, no promotion, no commit (B.1/B.6/B.10).
Effective confidence stays 0.0.

DRIFT-GUARD (binding, from DE3 / RECALIBRATION FROM DE): the binding L3 lever for this lane is summer
**SRKW PRESENCE-DAYS**, NOT a prey feed. This report frames the deliverable as net-new SRKW
presence-days and judges them against the summer-conditioned served gate.

Authority above this doc: `20260627_signal-modeling-launch-handoff/HANDOFF_CHARTER.md` section B;
`GRADUATION_WAVESET_CHARTER.md` (sections 1, 3); `GRADUATION_DISPATCH.md` (TB1 lane + the RECALIBRATION
FROM DE block).

---

## 0. Headline (MEASURED, dry-run, lower bound)

A bounded read-only dry-run probe of the OrcaHello `confirmed` reviewed-outcome endpoint (full archive,
31 pages, end-of-archive reached -- see section 2) measured the following for the two out-of-box
Admiralty Inlet nodes, neither of which is in the current cache or the served 4-station universe:

| node | confirmed records | confirmed presence-days | span (UTC) |
|---|---:|---:|---|
| **Port Townsend** (`rpi_port_townsend`, 48.13569, -122.76045) | 95 | 13 | 2020-11-19 .. 2026-03-02 |
| **Bush Point** (`rpi_bush_point`, 48.03371, -122.6039) | 118 | 18 | 2020-11-19 .. 2024-11-02 |
| **PT ∪ BP (unique calendar days)** | 213 | **27** | 2020-11-19 .. 2026-03-02 |

**Net-new SRKW presence-days the current 4-station universe lacks: 25** (MEASURED, lower bound).
Robust across both baselines: PT∪BP has 27 unique confirmed presence-days; only 2 of those already
appear in the existing universe, whether the existing universe is taken as the **cache** (3 nodes,
92 confirmed-day union -> 25 net-new) or the **live archive** (4 nodes incl. haro_strait, 92
confirmed-day union -> 25 net-new). Same answer both ways.

**THE DECISION-CRITICAL CAVEAT (binding L3 lever): of those 25 net-new presence-days, 0 are in summer
(JJA).** Every PT/BP confirmed presence-day falls Oct-Mar (month histogram: Oct 5, Nov 12, Dec 5,
Jan 1, Feb 1, Mar 1). The served gate's load-bearing regime is **summer** presence-days (the existing
universe carries 14 summer confirmed-days; PT/BP add **zero**). So against the binding lever these nodes
add net-new **off-season** presence-days only. This materially tempers the S1 "GO" and is the single
most important finding of this lane (section 5).

Status of the count: **MEASURED but a LOWER BOUND.** The live `confirmed` endpoint under-reports deep
history relative to the cache (e.g. it returns Orcasound Lab = 95 records / 7 days, while the cache holds
orcasound_lab = 572 records / 82 confirmed-days), because the cache was built from a `reviewed_outcomes`
**+ `history`** merge, not the `confirmed` endpoint alone. So the true PT/BP confirmed presence-day count
may be modestly higher than 27. The **seasonal skew (no summer) is robust** regardless and is what drives
the verdict.

---

## 1. What this lane is (and the W6 contrast)

S1 (ranks 1-2) identified Port Townsend + Bush Point as the cheapest real "new observation" lever: same
OrcaHello adapter / reviewed-outcome endpoints / record schema as the served 4, the only change being the
station key/coords and a **widened region gate**. Unlike W6 -- which moved the SAME cached rows into the
served store and added **0 net-new analysis observations** -- PT and BP are **absent from
`orcahello_index.cache.json`** (they were dropped by `SAN_JUAN_BOUNDS`), so a fresh reviewed-outcome
fetch yields genuinely new analysis observations. This is the lever W6 did not have.

The current cache holds only the 3 in-box extra nodes:

```
by key: {'orcasound_lab': 1029, 'north_san_juan_channel': 34, 'andrews_bay': 296}
```

PT and BP do not appear because `_record_in_region` (in `sources/orcahello_history.py`) gates on
`in_bounds` -> `SAN_JUAN_BOUNDS` = lat 48.40-48.70, lng -123.25..-122.75. PT (lat 48.136) and BP
(lat 48.034) are below the southern lat edge, so the cache build silently excluded them.

---

## 2. Dry-run method + provenance (what was actually run)

All probes were **read-only**: in-memory aggregation, printed summary, **nothing written, ingested,
deployed, or committed**. They are the dry-run the task asks for; the eventual fetch-that-writes is a
separate operator-gated step (section 7).

**Probe A -- reachability + schema (1 page).** `GET /api/detections/confirmed?Page=1&SortOrder=desc`
returned 50 records; location names are human-readable (`"Andrews Bay"`, `"Orcasound Lab"`) with embedded
`location.latitude/longitude` and per-record `id`, `confidence`, `found`, `reviewed`, `moderated`. The
endpoint is reachable from this host (no 403/SSL-EOF on light paging; B.9 flakiness is a heavy-paging
hazard).

**Probe B -- full confirmed archive (bounded, 31 pages of 100, asc, stop-on-empty/error, 0.12s
inter-page sleep, 20s per-request timeout).** Reached end-of-archive at page 32 (empty). Total confirmed
records archive-wide = 1549. Per-location confirmed counts/days/span (MEASURED this wave):

| location (live name) | confirmed rec | confirmed days | span |
|---|---:|---:|---|
| Haro Strait | 477 | 75 | 2020-09-30 .. 2025-09-22 |
| Sunset Bay | 401 | 49 | 2023-12-25 .. 2026-02-23 |
| Andrews Bay | 295 | 11 | 2026-02-06 .. 2026-06-16 |
| **Bush Point** | **118** | **18** | 2020-11-19 .. 2024-11-02 |
| **Port Townsend** | **95** | **13** | 2020-11-19 .. 2026-03-02 |
| Orcasound Lab | 95 | 7 | 2025-12-17 .. 2026-06-15 |
| Mast Center | 40 | 4 | 2025-12-15 .. 2026-01-13 |
| North San Juan Channel | 27 | 2 | 2026-03-13 .. 2026-03-29 |
| North SJC (alias) | 1 | 1 | 2025-04-16 |

**Probe C -- net-new overlap (bounded re-page + local cache join).** Computed PT∪BP confirmed
presence-day set minus the existing universe's confirmed presence-day set, against both the live archive
(existing 4-station union = 92 days) and the cache (3-node union = 92 days). Net-new = **25** both ways.
Summer (JJA) net-new = **0** both ways.

Endpoint: host `https://aifororcasdetections.azurewebsites.net`, path `/api/detections/confirmed`
(one of `REVIEWED_OUTCOME_PATHS`). License/provenance: Orcasound is an open project; the detection
archive is publicly queryable; audio under the AWS open-data registry (`registry.opendata.aws/orcasound/`).

**Data-quality flags surfaced by the probe (carry into any ingest):**
1. **Live `confirmed` under-reports vs cache** (Orcasound Lab 7 days live vs 82 days cached). The eventual
   fetch must reproduce the cache's `reviewed_outcomes + history` merge, not `confirmed` alone, or it will
   under-collect. => PT/BP counts here are a **lower bound**.
2. **Station-name aliasing**: `"North San Juan Channel"` and `"North SJC"` share coords (48.591294,
   -123.058779) but are two distinct location-name strings. A key-normalization map is required before
   keying records by station (section 6).
3. **Records carry `id`** on the live endpoint (unlike the current cache rows, which carry only
   `t/key/outcome`). A fresh PT/BP fetch should **retain `id`** so the store's `(station, t, id)` dedupe is
   precise -- this avoids the andrews_bay-style `(t, None)` collapse (W6 lost 31 rows that way).

---

## 3. Net-new presence-day estimate (the deliverable)

### 3.1 Three honest readings (state which you mean)

| reading | definition | value | note |
|---|---|---:|---|
| **net-new station-days** | PT days + BP days (new observation ROWS for modeling, any region overlap allowed) | **31** (13 + 18) | new per-station CV observations; what a per-station random-effect fit consumes |
| **net-new region presence-days** | PT∪BP calendar days NOT seen by any existing station | **25** | the binding "days the universe lacks" reading; MEASURED, lower bound |
| **net-new SUMMER region presence-days** | the subset of the above in JJA | **0** | the binding L3 lever; PT/BP add nothing here |

### 3.2 Net-new region presence-days, by season (MEASURED)

```
month:  Oct  Nov  Dec  Jan  Feb  Mar  | JJA(Jun-Aug)
count:   5    12    5    1    1    1   |     0
```

PT/BP net-new presence-days cluster in the fall chum-run window (Oct-Dec), which is ecologically
consistent with SRKW (notably J-pod) moving south through Admiralty Inlet into Puget Sound in fall --
i.e. these are plausibly genuine SRKW presence, but in the **off-season** for the model's summer gate.

### 3.3 Why the number is a lower bound, and the upper-bound method (NOT measured)

- The live `confirmed` endpoint under-collects deep history (flag 2.1). The cache-equivalent
  `reviewed_outcomes + history` merge would likely raise PT/BP confirmed days somewhat.
- An **all-reviewed** reading (confirmed + unknown, excluding false_positive) would give a presence-day
  **upper bound**; this lane did NOT page the `unknowns`/`unreviewed` endpoints (bounded-work + B.3
  withhold-over-fake: `confirmed` is the honest presence proxy). The operator probe in the runbook
  (section 7) can produce that upper band if wanted.
- Bound statement: **net-new region presence-days ∈ [25, ~40]**; net-new **summer** presence-days ≈ **0**
  (high confidence -- the seasonal mechanism, not the count precision, drives this).

### 3.4 Expected CV-skill effect (HONEST, not measured here)

No fit was run (TB lane = dry-run + runbook + estimate; the fit is a later single-editor, operator-gated
step). The honest expectation: 25-31 net-new presence-days is a **small** addition against ~300 effective
independent encounter onsets, and -- critically -- it lands **outside** the summer regime the gate scores.
So the expected contribution to **summer-conditioned** fold-stable CV mean-deviance-skill toward +0.144 is
**near zero to slightly negative** (added off-season heterogeneity can dilute the summer signal and worsen
cross-station consistency, already failing at 0.14-0.34). The nodes are better justified as **off-season
coverage / future-accumulation** than as a summer-+0.144 lever. Any GO must measure the marginal
fold-stable CV-skill through `block_cv` (write_outputs=False) before it is believed.

---

## 4. `log E` effort plan (encodes Bush Point's documented outages)

Acoustic detections are **effort-stable temporal drivers with a `log E` offset** (B.2): a hydrophone is a
fixed position, not a whale GPS fix, and a detection rate is only interpretable relative to monitored
time. PT and BP have very different uptime profiles, so their `log E` must be node-specific.

**Effort definition.** For node `s`, time-bin `b`: `E[s,b] = monitored_hours(s,b)` (the hours the node
was live AND the OrcaHello classifier was running), entered as `log E[s,b]` offset. A gap is **unknown
effort, withheld** -- NOT imputed as zero presence (B.3). A bin with `E=0` is dropped from the likelihood,
not scored as a confirmed absence.

**Bush Point outage encoding (documented + data-derived).**
- Documented (S1): BP is intermittent (storm/repair gaps; down ~Jan-2026, ~Apr-2025; live 2018+).
- Data-derived corroboration this wave: BP's confirmed detections **stop at 2024-11-02** with nothing
  after, consistent with an extended 2025-2026 outage. Its confirmed presence clusters in three
  fall windows (2020, 2021-22, 2024); 2023 has a single day. These gaps must be effort, not absence.
- Effort source ladder (best -> fallback), per month:
  1. **Operator uptime telemetry** -- Orca Network / Orcasound node-status logs and the Orcasound
     `orcasite` feed `online`/`offline` history (preferred; true monitored hours).
  2. **OrcaHello liveness proxy** -- months with ANY OrcaHello record at the node (incl.
     false_positive/unreviewed, which only exist when the classifier was running) mark the node "live";
     months with none are **candidate outages** flagged for withholding, NOT scored as absence.
  3. **Coarse default** -- where neither is available, set `E` to the median live-month hours and
     **flag the bin as effort-uncertain** (sensitivity-test it in/out of the fit).
- **PT** is comparatively continuous (confirmed days span 2020-2026 with regular fall recurrence); a
  simpler near-constant `log E` with the same liveness-proxy gap handling suffices.

**Honesty rail.** Because BP's rate is computed over real (gappy) uptime, its per-bin detection rate must
not be inflated by treating outage months as zero-presence months. The W6 effort discipline applies, and
it is **harder here** (S1 sec 2): get BP's `log E` wrong and its presence rate is overstated.

---

## 5. REGION-EXPANSION DECISION MEMO (for the operator)

**The decision.** Grounding PT + BP is not just an ingest; it is a deliberate **modeling-region
expansion** from the San Juan core to Admiralty Inlet. The operator must decide whether SRKW presence at
Admiralty Inlet belongs to the **same modeled temporal process** as the San Juan core.

**What you gain (MEASURED):** 25 net-new region presence-days (31 station-days), all Oct-Mar, from a
real SRKW transit corridor, via the cheapest grounding path (existing adapter + a region-gate widen).

**What you do NOT gain (MEASURED):** any net-new **summer** presence-days. Against the binding L3 lever
(summer presence-days), PT + BP contribute **0**. The +0.144 bar is judged on the summer-conditioned
served gate; these nodes do not feed it.

**Three risks the operator weighs:**

1. **Out-of-box heterogeneity / cross-station consistency (the load-bearing risk).** Admiralty Inlet is a
   different passage regime (fall chum transit) than the San Juan summer foraging core. The cross-station
   kernel consistency is already failing (0.14-0.34). Adding two off-season-dominated nodes can **lift raw
   CV observation count while WORSENING consistency** -- and the seasonal mismatch (their mass is Oct-Dec,
   the core's is summer) makes a single shared `k_season` kernel actively wrong across the pooled set.
   Consistency is not a confidence-map input but it is the L2 quality blocker the campaign tracks. Likely
   net effect on the **summer** gate: neutral-to-negative.

2. **Bigg's-confound caveat.** The model targets SRKW presence; OrcaHello's classifier is an SRKW-call
   detector, but Admiralty Inlet hosts Bigg's/transient killer whales year-round, and a moderator
   "confirmed" marks a confirmed **killer-whale call**, not a confirmed **ecotype**. The Oct-Dec timing of
   PT/BP confirmations aligns with known SRKW (J-pod) fall chum foraging in Puget Sound, which supports
   (but does not prove) SRKW origin. Mitigation if grounded: prefer pod-ID'd / annotated subsets where
   available; treat raw PT/BP confirmed counts as **killer-whale presence**, with SRKW-ecotype a stated
   assumption, not a measurement. This is exactly the southern-node confound S1 flagged for Sunset
   Bay/Point Robinson/MaST, present here in milder form.

3. **Detector + species + region coupling vs. independence.** PT/BP are independent **locations** and
   **new SRKW days**, but they share the **same operator + same detector (OrcaHello)** as the served 4, so
   they are not detector-independent corroboration the way ONC/Boundary Pass (TB4) would be. Their value
   is geographic coverage, not method triangulation.

**Operator decision points (each a gate):**
- **D1 -- Region scope.** Expand the modeling region to Admiralty Inlet (PT + BP), yes/no? If yes, prefer
  the **two-box** gate (keep `SAN_JUAN_BOUNDS` unchanged; add a separate Admiralty box) so the San Juan
  core gate is untouched (section 6.1).
- **D2 -- Seasonal framing.** Given 0 net-new summer presence-days, do you ground PT/BP as (a) an
  **off-season coverage / forward-accumulation** add (honest, does not claim a +0.144 lever), or (b)
  defer until the model carries a season/regime split or per-station random effect that can use off-season
  mass without polluting the summer kernels? **Recommendation: (a) ground as coverage, do NOT credit on
  the summer gate**, OR defer per D4.
- **D3 -- Species handling.** Accept killer-whale-presence (Bigg's-confound stated) or restrict to
  pod-ID'd SRKW subsets (lower N, cleaner)?
- **D4 -- Sequencing.** Recommended: ground only after (or alongside) a model change that can exploit
  off-season / multi-region mass (TA2 per-station random effect / presence-hurdle reframe); grounding into
  today's single summer-conditioned process risks worsening consistency for ~0 summer gain.

**TB1 verdict.** **CONDITIONAL GO as off-season coverage / forward-accumulation; NO-GO as a summer
+0.144 lever on today's model.** The cheapest-grounding claim holds; the new-observation claim holds (25
net-new days, not a W6 re-shelving); but the *binding* summer-presence-day lever is not moved. The S1
"GO Port Townsend / GO Bush Point" ranking stands only under the off-season-coverage framing -- this lane
adds the measured seasonal caveat S1 did not have. Honest expected effect on the summer-conditioned
+0.144 bar: ~0 to slightly negative. Recommend D4 (sequence behind a model change) over an immediate
ground-into-summer-gate.

---

## 6. Per-node cache index + region-gate plan (dry-run design)

### 6.1 Widened region gate (two-box, recommended)

Keep `SAN_JUAN_BOUNDS` exactly as is (do not perturb the served core gate). Add a disjoint Admiralty
Inlet box and OR the two. Proposed box, chosen to capture PT + BP and **exclude** the Bigg's-dominated
southern Puget Sound sites (Sunset Bay 47.865, Point Robinson 47.39, MaST 47.35 all fall below
`min_lat=48.00`):

```python
# proposed addition to src/aws_backend/geo_region.py (PATCH-SPEC, not applied)
ADMIRALTY_INLET_BOUNDS = RegionBounds(
    min_lat=48.00, max_lat=48.20, min_lng=-122.85, max_lng=-122.55
)
# PT (48.13569, -122.76045) in-box; BP (48.03371, -122.6039) in-box;
# Sunset Bay / Point Robinson / MaST excluded (lat < 48.00).
```

Region gate becomes `in_bounds(lat,lng) or _in_admiralty(lat,lng)` (a new helper), or an explicit
`MODELING_REGIONS = [SAN_JUAN_BOUNDS, ADMIRALTY_INLET_BOUNDS]` list the gate iterates. The single-box
alternative (floor `SAN_JUAN_BOUNDS.min_lat` to 48.00, raise `max_lng` to -122.55) is simpler but mutates
the served core gate and pulls in a wider eastern strip; the two-box approach is preferred for blast-radius
control. **This change is operator-gated (D1); not applied here.**

### 6.2 Per-node cache indexes (mirrors the W6 cache pattern)

Build one cache file per node, exactly as `orcahello_index.cache.json` was built, but with the gate
widened for that node's coords:

```
.cca/catalogue/O0/.../orcahello_index.port_townsend.cache.json
.cca/catalogue/O0/.../orcahello_index.bush_point.cache.json
```

Each via `OrcaHelloHistoryAdapter.fetch_reviewed_outcomes(in_region_only=True)` with the widened gate
(so only PT/BP-region records are kept), merged with a `history` pass as the original cache was (to
overcome the `confirmed`-endpoint under-collection, flag 2.1). Retain `id` per record (flag 2.3). Record
schema per row: `{t, id, key, outcome, latitude, longitude, confidence}` -- richer than the current
3-node cache, which only stored `{t, key, outcome}`.

Per-node index keys, normalized (flag 2.2): map live location-name strings to station keys:
`{"Port Townsend": "port_townsend", "Bush Point": "bush_point",
"North San Juan Channel": "north_san_juan_channel", "North SJC": "north_san_juan_channel"}`.

---

## 7. Runbook

### 7.1 Dry-run (reproduce this lane's estimate -- safe, read-only, no write)

1. Reachability + schema: `GET /api/detections/confirmed?Page=1&SortOrder=desc&RecordsPerPage=100`;
   confirm location names + embedded coords + `id`.
2. Bounded full-archive page (asc, stop-on-empty/error, inter-page sleep, per-request timeout) of the
   `confirmed` endpoint; aggregate per-location confirmed records, distinct presence-days (UTC date), and
   span. Cap pages (60 is ample; the archive ended at 31 this wave).
3. (Optional upper band) repeat for `/unknowns` and `/unreviewed` to bound presence-days above; keep
   `confirmed` as the honest headline (B.3).
4. Net-new join: PT∪BP confirmed-day set minus the existing universe's confirmed-day set (cache 3-node
   union and/or live 4-node union). Report total + **summer (JJA)** net-new separately.
5. NEVER call a store write in the dry-run. Aggregation is in-memory; output is a printed summary only.

### 7.2 Eventual operator-gated fetch + ingest (NOT run here; separate gated step)

1. **Gate D1** approved (region expansion). Apply the two-box gate patch (section 6.1, single-editor
   integrate of `geo_region.py`).
2. Build per-node caches (section 6.2) via the widened `fetch_reviewed_outcomes` + `history` merge; retain
   `id`. This is a fetch-to-cache, not a fetch-to-served-store; still gated.
3. Extend `EXTRA_NODES` / `STATION_COORDS` and add a per-node `cache_path` argument to
   `build_acoustic_records` (section 8). Dry-run `ingest_multistation_acoustic(dry_run=True)` and confirm
   per-station raw vs `(station,t,id)`-deduped counts.
4. **Gate W6-equivalent** (operator deploy approval) -> `ingest_multistation_acoustic(store, dry_run=False)`
   with env `ORCAST_STORAGE_BACKEND=aws
   ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads AWS_REGION=us-west-2`
   (B.5 footgun). Single writer only (read-modify-write partitions are not concurrency-safe).
5. Observability: pre-write `list_stations("acoustic_detections")` must NOT already contain
   `port_townsend`/`bush_point`; post-write assert per-node counts == dry-run; provenance audit
   (`source == "orcahello_index_cache"`); haro_strait untouched.
6. Rollback: delete only the two new station prefixes
   (`timeseries/acoustic_detections/port_townsend/`, `.../bush_point/`); never touch existing prefixes.
7. **Refit** (separate single-editor, write_outputs=False): measure marginal **summer-conditioned**
   fold-stable CV mean-deviance-skill via `block_cv`. Do NOT promote (B.1); confidence stays 0.0 until a
   passing gate on served data + a recorded supervisor decision.

### 7.3 In-region escape hatch

OrcaHello (Azure) is reachable from this host on light paging; it is NOT the DNS-blocked DFO FOS host, so
the EC2 `i-04a649f91274e9fce` is not required for these probes. Use the EC2 only if heavy paging triggers
the B.9 403/SSL-EOF flake during the full per-node cache build.

---

## 8. PATCH-SPEC stub (for the later single-editor integrate -- NOT applied)

**Scope:** `src/aws_backend/geo_region.py`, `src/aws_backend/ingest_multistation.py`,
`modeling/studies/common.py` (`STATION_COORDS`). No edit is applied by this lane; this is the spec.

1. `geo_region.py`: add `ADMIRALTY_INLET_BOUNDS` (section 6.1) and a region-set gate
   (`MODELING_REGIONS = [SAN_JUAN_BOUNDS, ADMIRALTY_INLET_BOUNDS]`; `in_bounds` iterates the list, OR a
   dedicated `in_modeling_region(lat,lng)` so the served map gate and the modeling gate can diverge if
   the operator wants the map unchanged). Gated on D1.
2. `ingest_multistation.py`:
   - extend `EXTRA_NODES` with
     `"port_townsend": (48.13569, -122.76045)`, `"bush_point": (48.03371, -122.6039)`;
   - add an optional per-node `cache_path` (the new `orcahello_index.<node>.cache.json`) so
     `build_acoustic_records` can read the PT/BP caches alongside the existing 3-node cache;
   - add a station-name->key normalization map (flag 2.2) at record-build time;
   - retain `id` from the richer PT/BP cache rows so dedupe is `(station, t, id)`, not `(t, None)`.
3. `modeling/studies/common.py`: add PT/BP to `STATION_COORDS` with the coords above.
4. Effort: wire the node-specific `log E` (section 4) -- BP must carry its outage-derived monitored-hours
   offset; do not let BP outage months read as zero-presence.

**DE drift note (per RECALIBRATION FROM DE):** this patch-spec frames PT/BP as net-new **presence-days**
(per DE3 row #10, presence is the binding L3 lever, not a prey feed) and explicitly records that the
net-new is **off-season** (0 summer days), so the integrate step lands the supersession caveat: do NOT
let any doc reframe these nodes as a summer-gate +0.144 lever. If the integrate touches a DE1/DE3-flagged
doc (e.g. a wildlife/objectives register that still reads "more nodes -> summer skill"), append the DE3
row #10 pointer.

---

## 9. Return summary

- **Doc path:** `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/graduation/TB1_port_townsend_bush_point.md`
- **Net-new presence-day estimate (MEASURED, dry-run, lower bound):** Port Townsend 13 + Bush Point 18 =
  **31 net-new station presence-days**; **25 net-new region presence-days** the current 4-station universe
  lacks (robust vs both cache and live baselines). **0 of these are summer (JJA)** -- the binding L3 lever
  is summer presence-days, and PT/BP add none. Lower bound: the live `confirmed` endpoint under-collects
  deep history (cache merge would raise the count; seasonal skew is robust). Bound: region net-new
  ∈ [25, ~40]; summer net-new ≈ 0.
- **Verdict:** CONDITIONAL GO as off-season coverage / forward-accumulation; **NO-GO as a summer +0.144
  lever on today's model**. Cheapest-grounding + genuinely-new-observation claims hold; the summer gate is
  not moved; consistency risk is real.
- **Operator decision points:** D1 region scope (two-box gate recommended); D2 seasonal framing (ground as
  coverage, do not credit summer gate -- or defer); D3 species handling (killer-whale-presence with
  Bigg's-confound stated vs pod-ID'd SRKW subset); D4 sequencing (recommend grounding behind a model
  change that uses off-season/multi-region mass, e.g. TA2).
- **Confirmation:** nothing was fetched-to-write, ingested, deployed, promoted, or committed. All probes
  were read-only in-memory aggregations against a public open-data endpoint; no convergence file edited;
  only this one findings doc written. **Effective confidence 0.0.**
