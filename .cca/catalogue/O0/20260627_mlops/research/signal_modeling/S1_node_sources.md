# S1 -- in-region acoustic node source discovery + grounding

Agent: research subagent W9-S1, signal & modeling research campaign. Date: 2026-06-27
(America/New_York). Repo: `/Users/gilraitses/orcast`. This doc only; no other file edited,
no deploy, no production write, no fit, no promotion, no commit (B.1/B.6/B.10).

Authority above this doc: `20260627_mlops-handoff/HANDOFF_CHARTER.md` section B;
`20260627_mlops/SIGNAL_MODELING_CHARTER.md`; task = `SIGNAL_MODELING_DISPATCH.md` section S1.

## 0. Hydration + the bar I judge against

Read first, in order: HANDOFF_CHARTER B (B.1 honesty/promotion gate, B.2 effort-bias
covariate roles, B.3 withhold-over-fake, B.4 bucket footgun, B.9 OrcaHello flake + cache),
SIGNAL_MODELING_CHARTER, SIGNAL_MODELING_DISPATCH (S1), `research/forward/G1_ingest_deploy.md`
(W6 ingest pattern + the 0-net-new finding), `research/forward/G2_promotion_protocol.md`
(the +0.144 bar), `src/aws_backend/ingest_multistation.py` (`EXTRA_NODES`, the cached-index
ingest template), `modeling/studies/common.py` (`STATION_COORDS`),
`src/aws_backend/sources/orcahello_history.py` (`REVIEWED_OUTCOME_PATHS`, `_record_in_region`),
`src/aws_backend/geo_region.py` (`SAN_JUAN_BOUNDS`), and the cache itself
(`orcahello_index.cache.json`: 1359 records, keys `orcasound_lab` 1029 / `andrews_bay` 296 /
`north_san_juan_channel` 34; outcomes confirmed 895 / false_positive 363 / unreviewed 74 /
unknown 27).

The judging bar (G2, charter sec 4): a node graduates only if it would add genuinely NEW,
INDEPENDENT presence observation that could move SERVED held-out, fold-stable CV
mean-deviance-skill toward **+0.144** (the verified P0 0.6-crossing; ~1.85x the current +0.078
experiment). Never argue from in-sample fit. Effort-bias honesty (B.2): acoustic detections are
effort-stable temporal drivers with a `log E` offset; a hydrophone is a fixed position, not a
whale GPS fix; visual sightings are validation + `s_space` only.

### 0.1 The two facts that decide every verdict below

1. **The current cache is in-region-filtered.** The existing 4-station universe is haro_strait
   (served, ~761) + the 3 cached nodes. The cache was built by
   `fetch_reviewed_outcomes(in_region_only=True)`, and `_record_in_region` gates on
   `SAN_JUAN_BOUNDS` = **lat 48.40-48.70, lng -123.25 to -122.75** (the San Juan archipelago
   core). OrcaHello actually monitors **8** locations; the 4 southern ones were dropped by that
   box, which is the only reason the cache holds 3 extra nodes and not 7.
2. **The W6 contrast (the whole point of this campaign).** W6 added **0 net-new ANALYSIS
   observations** because it moved the SAME cached rows into the served store. By contrast, every
   node in this catalog is **absent from `orcahello_index.cache.json`**, so grounding it via a
   fresh reviewed-outcome fetch (a new cache build) adds genuinely new analysis observations --
   not a re-shelving of the existing cache. That is the lever W6 did not have.

The catch that travels with fact 1: the highest-yield directly-groundable nodes (the other
OrcaHello sites) sit **OUTSIDE** `SAN_JUAN_BOUNDS`. Grounding them is not just an ingest; it is a
deliberate **modeling-region expansion** decision (does SRKW presence at Admiralty Inlet / central
Puget Sound belong to the same modeled process as the San Juan core?). Flagged per node.

---

## 1. NODE CATALOG

Coordinates are the operator's published values (Orcasound `orcasite` feeds JSON +
`orcasound/orcahello` `source_guid_to_location`; SMRU/The Whale Museum; ONC/JASCO ECHO dataset
DOI 10.1038/s41597-025-05281-5). "In box?" = inside `SAN_JUAN_BOUNDS` (the current modeling
region gate). "In cache?" = present in `orcahello_index.cache.json` today.

### Group A -- OrcaHello-monitored Orcasound nodes (same API + same W6 grounding as the current 4)

These are detected by the OrcaHello binary SRKW-call classifier and human-moderated, identical in
shape to the cached nodes. They are the cheapest to ground because the adapter, the
reviewed-outcome endpoints, and the record schema already exist; the only change is the station
key/coords and the region gate.

| node (OrcaHello key) | coords (lat, lng) | operator | in box? | in cache? | reviewed feed | span/cadence |
|---|---|---|---|---|---|---|
| **Port Townsend** (`rpi_port_townsend`) | 48.135743, -122.760614 | Orcasound + PT Marine Science Center | **NO** (lat<48.40) | no | OrcaHello reviewed-outcome (same as cache) | live since ~2020; continuous, gappy uptime |
| **Bush Point** (`rpi_bush_point`) | 48.0336664, -122.6040035 | Orca Network (Whidbey) | **NO** (lat<48.40) | no | OrcaHello reviewed-outcome | live 2018+; **intermittent** (storm/repair gaps, e.g. down 1/2026, 4/2025) |
| **Sunset Bay** (`rpi_sunset_bay`) | 47.86497, -122.33394 | Orca Conservancy (Edmonds) | **NO** | no | OrcaHello reviewed-outcome | live 2021+; single element, shallow |
| **Point Robinson** (`rpi_point_robinson`) | 47.388383, -122.37267 | Orcasound (Maury I.) | **NO** | no | OrcaHello reviewed-outcome | live; central Puget Sound |
| **MaST Center** (`rpi_mast_center`) | ~47.36, -122.32 (Des Moines) | Orcasound / Highline MaST | **NO** | no | OrcaHello reviewed-outcome | live; south-central Puget Sound |

Data access (all of Group A): host `https://aifororcasdetections.azurewebsites.net`, paths in
`REVIEWED_OUTCOME_PATHS` (`/api/detections/confirmed|falsepositives|unknowns|unreviewed`).
License: Orcasound is an open project (audio under open-data registry `registry.opendata.aws/orcasound/`,
CC-style); the detection archive is publicly queryable. Known flake (B.9): the history API 403s /
SSL-EOFs on heavy paging and `fetch_history` returns oldest-first -- so use the reviewed-outcome
endpoints + a cache build, exactly as the current 4 were sourced.

W6-style grounding plan (Group A, per node): (i) call `fetch_reviewed_outcomes` with the region
gate widened/removed for that station key, build a per-node `orcahello_index.<node>.cache.json`;
(ii) add the node to `EXTRA_NODES` / `STATION_COORDS` with the coords above; (iii) reuse
`build_acoustic_records` -> `_put_grouped_by_station` (keyed by `record["station"]`, monthly
`YYYY/MM.ndjson`, idempotency key `(station, t, id)`); (iv) provenance `source:
"orcahello_index_cache"` + `outcome`. Dedupe caveat inherited from W6: cache rows carry no `id`,
so same-timestamp rows collapse on `(t, None)` (reported, not silently dropped).

### Group B -- in-region but spatial duplicate (independent detector, same position)

| node | coords (lat, lng) | operator | in box? | in cache? | reviewed feed | span/cadence |
|---|---|---|---|---|---|---|
| **Lime Kiln Lighthouse** | 48.516, -123.152 | SMRU Consulting + The Whale Museum (SeaSound / Salish Sea Hydrophone Network) | **YES** | no | PAMGuard event logs (ECHO daily logs) 2016-2021; WRAS real-time alerts (Ocean Wise) since Jun-2024 | acoustic since 2012; summer/fall analyzed continuously |

Note: Lime Kiln's coords are **essentially identical** to the `haro_strait` STATION_COORDS
(48.516, -123.152). It is the canonical Haro Strait foraging-hotspot listening station. So it is a
**different detector at the same place** as our existing haro_strait node -- it does not add a new
location. Access is NOT an open API: ECHO daily event logs come via SMRU/VFPA (request/agreement);
WRAS alerts via Ocean Wise. License/sharing terms would need a partnership. Detection method is
PAMGuard whistle + click detectors reviewed in Viewer Mode (a different, click-capable detector
than OrcaHello's call classifier), with night coverage and a longer history.

Grounding plan (Group B): would require a data-sharing agreement, then mapping PAMGuard/ECHO daily
"SRKW present" event logs to `acoustic_detections` records keyed `station: "lime_kiln"` (or fused
into haro_strait). Honest classing: because it co-locates with haro_strait, treat it as a
**detector-fusion / validation** enrichment of haro_strait (it can fill days OrcaHello missed --
night, clicks-only, pre-2020), NOT as a new station for cross-station structure.

### Group C -- BC / Boundary Pass / Strait of Georgia (ONC + JASCO/VFPA ECHO)

| node | coords (lat, lng) | operator | in box? | in cache? | reviewed feed | span/cadence |
|---|---|---|---|---|---|---|
| **Strait of Georgia ULS / Boundary Pass** | ~48.78, -123.05 (170 m, NB shipping lane) | VFPA + JASCO + ONC (VENUS) | **NO** (lat>48.70, BC) | no | **published annotated orca dataset** (Sci. Data 2025, DOI 10.1038/s41597-025-05281-5); raw via ONC Oceans 3.0 | ULS 2015-09 to 2018-03; AMAR Boundary Pass 2018-2019 |
| **Boundary Pass WRAS station** | ~48.72, -123.0 | Transport Canada + JASCO + VFPA | **NO** (BC) | no | WRAS real-time alerts (Ocean Wise) since Apr-2024 | near-real-time, live |

Data access (Group C): ONC **Oceans 3.0 API** (`oceannetworkscanada.github.io/api-python-client`,
free account + API token; Python `onc` client; discovery -> deviceCategory `Hydrophone` ->
data products). The published annotated dataset is a DOI-citable, reviewed/bounding-boxed orca
detection corpus (independent of OrcaHello, expert-annotated). The WRAS feed is not an open API.
Boundary Pass is a genuine SRKW corridor (northbound shipping lane), so detections are real
SRKW presence, independent operator + location.

Grounding plan (Group C): for the published dataset, parse the annotation tables to per-day
"orca present" events at the ULS/Boundary Pass position, map to `acoustic_detections`
(`station: "boundary_pass"`, provenance `source: "onc_jasco_echo_2025"`), and -- critically --
attach the deployment duty cycle as **effort** for the `log E` offset (170 m bottom-mounted, duty
cycled, not a continuous surface node). For the live ONC feed, a future probe would go through ONC
Oceans 3.0 (NOT the DFO FOS host, which local DNS blocks; if any in-region probe were needed it
would route via aimez EC2 `i-04a649f91274e9fce`, but this doc runs NO fetch that writes). Either
way it needs **our own presence-day extraction** (or the published annotations), not a turnkey
reviewed feed like OrcaHello.

### Group D -- BC Gulf Islands community streams (live audio, no reviewed-detection feed)

| node | coords (lat, lng) | operator | in box? | reviewed feed |
|---|---|---|---|---|
| **Monarch Head / East Point** (Boundary Pass) | ~48.78, -123.04 | SIMRES | **NO** (BC) | none documented (live stream only) |
| **Pender Island** (Swanson Channel) | ~48.77, -123.28 | Raincoast | **NO** (BC) | none documented (live stream only) |

Access: live public streams; no published API or reviewed-detection log. Grounding would require
building/running our own detector on their audio -- high effort, no effort-stable reviewed feed,
out-of-box.

### Group E -- out of scope (recorded for completeness)

- **Skunk Bay (Hansville)**: weather/skycam, not an orca-detection feed. NO.
- **Salish Sea Hydrophone Network historic sites (Neah Bay, Seattle)**: referenced historically
  by The Whale Museum but not active reviewed feeds today. NO.

---

## 2. INDEPENDENT vs DUPLICATE verdict (does it add new whale-presence days?)

The decisive test (vs the W6 0-net-new): is the node ABSENT from the current cache/analysis
universe, and does it observe presence the existing 4 stations cannot?

| node | in cache today? | new location? | independent presence days? | verdict |
|---|---|---|---|---|
| Port Townsend | no | yes (Admiralty Inlet approach) | yes -- SRKW transits PT/Admiralty independent of San Juan core | **INDEPENDENT** (new obs, out-of-box) |
| Bush Point | no | yes (Admiralty Inlet) | yes -- SRKW pass ~monthly; distinct from San Juan | **INDEPENDENT** (new obs, out-of-box, gappy effort) |
| Sunset Bay | no | yes (Possession/Puget) | partly -- more Bigg's/humpback, lower SRKW rate | **INDEPENDENT but low-SRKW-yield** |
| Point Robinson | no | yes (central Puget) | weak -- SRKW rare, Bigg's-dominated | **INDEPENDENT but marginal for SRKW** |
| MaST Center | no | yes (south-central Puget) | weak -- SRKW rare, Bigg's-dominated | **INDEPENDENT but marginal for SRKW** |
| Lime Kiln | no | **no** (= haro_strait position) | partly -- only on days haro_strait OrcaHello missed (night/clicks/pre-2020) | **DUPLICATE location / partially time-independent detector** |
| Strait of Georgia / Boundary Pass (ONC/JASCO) | no | yes (Boundary Pass corridor) | yes -- real SRKW corridor, independent operator + annotations | **INDEPENDENT** (out-of-box, historical, needs extraction) |
| Boundary Pass WRAS | no | yes | yes, live | **INDEPENDENT** but no open API |
| SIMRES / Raincoast (BC) | no | yes | unknown -- no reviewed feed to measure | **INDEPENDENT in principle, ungroundable now** |
| Skunk Bay / SSHN historic | no | n/a | no | **NO** |

Honesty caveats that bound the "independent" wins:
- **Species mismatch toward the south.** The model targets SRKW presence; OrcaHello's classifier is
  an SRKW-call detector, but the southern Puget Sound sites (Point Robinson, MaST, Sunset Bay) are
  Bigg's/transient-dominated, and Bigg's are frequently silent or call differently -- so raw
  detection counts there are NOT clean SRKW presence-days. Confirmed-outcome filtering and pod ID
  help but lower N.
- **Out-of-box heterogeneity.** Admiralty Inlet and Puget Sound are different passage regimes than
  the San Juan core. They add independent CV observations (good for the skill component) but can
  WORSEN cross-station kernel consistency (already failing at 0.14-0.34). Consistency is not a
  confidence-map input, but it is an L2 quality blocker the campaign tracks -- so a southern node
  could lift CV-skill while hurting consistency. State this on any graduation.
- **Effort/`log E` is non-trivial for the new nodes.** Bush Point has documented multi-month
  outages; bottom-mounted ONC/JASCO nodes are duty-cycled at depth. Their `log E` offset must
  encode real uptime, or their rates are biased. This is the W6 effort discipline, harder here.

---

## 3. Ranked GO / NO-GO (expected new independent SRKW-presence observation per unit effort)

Ranked by the campaign objective: move SERVED, fold-stable CV mean-deviance-skill toward +0.144
via genuinely new observation, cheapest first. Effort is measured against the existing W6 path
(same adapter + reviewed-outcome endpoints + cache build = lowest effort).

1. **GO -- Port Townsend (OrcaHello).** Cheapest real lever. Same adapter/feed/schema as the
   current 4; only a region-gate widen + station coords. Admiralty Inlet is a true SRKW transit
   point, so it adds independent SRKW presence-days that are NOT in the cache (unlike W6).
   Dependency: an explicit region-expansion decision (it is out-of-box). Data type: **new
   observation**. Role: effort-stable temporal driver with `log E` (B.2).
2. **GO -- Bush Point (OrcaHello).** Same near-zero-marginal grounding; SRKW pass Admiralty Inlet
   ~monthly. Independent. Caveat: intermittent uptime -- its `log E` must encode the documented
   outage windows or its rate is overstated.
3. **GO (conditional) -- Strait of Georgia / Boundary Pass (ONC + JASCO/VFPA ECHO).** Highest
   *independence quality* (independent operator, independent detector, expert-annotated published
   dataset, real SRKW corridor), but higher effort: out-of-box, historical (2015-2019), and needs
   our own presence-day extraction from the DOI annotations + a duty-cycle effort model. Worth it
   as the strongest *independent corroboration* node, after the cheap OrcaHello adds. Data type:
   **new observation**.
4. **CONDITIONAL -- Lime Kiln (SMRU/Whale Museum) as haro_strait detector-fusion.** Not a new
   location (co-located with haro_strait), so NO-GO as a "new node." But it is a different detector
   (PAMGuard clicks + night + 2012/2016+ history) that can add haro_strait presence-days OrcaHello
   missed -- a validation + gap-fill enrichment. GO only if a data-sharing agreement is cheap;
   otherwise defer. Data type: partially new observation (time), not new location.
5. **NO-GO (now) -- Sunset Bay, Point Robinson, MaST Center (OrcaHello).** Groundable just as
   cheaply, but Bigg's-dominated / low-SRKW sites: expected new *SRKW* presence-days are small and
   the raw counts are confounded by transient detections, while adding the most cross-station
   heterogeneity risk. Reconsider only if the model adds a species/ecotype split or a station
   random effect.
6. **NO-GO -- Boundary Pass WRAS live feed.** Independent and live, but no open API; access is an
   alerting integration, not a queryable archive. Revisit only via a partnership.
7. **NO-GO -- SIMRES Monarch Head, Raincoast Pender (BC Gulf Islands).** Live audio only, no
   reviewed-detection feed; grounding means building our own detector. Out-of-box, high effort,
   no effort-stable reviewed signal. (B.3 withhold-over-fake: report as ungroundable now.)
8. **NO-GO -- Skunk Bay, defunct SSHN historic sites.** No usable orca-detection feed.

### The single cheapest high-value experiment this catalog implies

Re-fetch OrcaHello reviewed-outcomes for **Port Townsend + Bush Point** with the region gate
widened to include Admiralty Inlet, build the new caches, and (dry-run) score whether the two
nodes add net-new SRKW presence-days the current 4-station universe lacks. This is the exact W6
mechanic but, unlike W6, against stations **not already in the cache** -- so it is the first thing
that can add *new analysis observations* rather than re-shelving them. It directly tests whether
served, fold-stable CV-skill can move toward +0.144 from new observation. Everything here stays
investigation-first: nothing is fetched-to-write, deployed, promoted, or committed; the actual
fetch + ingest + refit are separate operator-gated waves.

---

## Return summary

- **Doc path:** `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/S1_node_sources.md`
- **Node catalog:** OrcaHello monitors 8 sites; beyond the current 4 (haro_strait, orcasound_lab,
  andrews_bay, north_san_juan_channel) the additional OrcaHello nodes are **Port Townsend, Bush
  Point, Sunset Bay, Point Robinson, MaST Center** -- all groundable via the identical W6 reviewed-
  outcome path but all **outside** `SAN_JUAN_BOUNDS`, so grounding them is a region-expansion
  decision. **Lime Kiln** (SMRU/Whale Museum) is in-box but co-located with haro_strait. **ONC /
  JASCO Strait of Georgia & Boundary Pass** (ECHO; published annotated dataset DOI
  10.1038/s41597-025-05281-5; Oceans 3.0 API) is an independent BC corridor node, historical.
  **SIMRES/Raincoast** BC streams have no reviewed-detection feed.
- **Independent vs duplicate:** unlike W6 (0 net-new, re-shelved cache rows), **none of these nodes
  are in the existing cache**, so each adds genuinely new analysis observation when fetched fresh.
  INDEPENDENT (new location + new SRKW days): Port Townsend, Bush Point, ONC/Boundary Pass.
  INDEPENDENT but low-SRKW-yield / Bigg's-confounded: Sunset Bay, Point Robinson, MaST Center.
  DUPLICATE location (haro_strait), only partially time-independent: Lime Kiln. Ungroundable now:
  SIMRES/Raincoast, WRAS live, Skunk Bay.
- **Ranked go/no-go:** GO Port Townsend (cheapest, same feed, new SRKW corridor); GO Bush Point
  (same feed, gappy effort); GO-conditional ONC/Boundary Pass (best independence, higher effort,
  needs extraction); CONDITIONAL Lime Kiln (haro_strait detector-fusion/validation, not a new
  node); NO-GO-now Sunset Bay/Point Robinson/MaST (Bigg's-confounded, heterogeneity risk); NO-GO
  WRAS/SIMRES/Raincoast/Skunk Bay (no open reviewed feed). Cheapest high-value experiment:
  re-fetch + dry-run Port Townsend + Bush Point with a widened region gate to measure net-new SRKW
  presence-days, the first move that adds new observation rather than re-shelving the cache.
- Honesty rails held: nothing promotes (B.1); acoustic = effort-stable temporal driver with
  `log E`, hydrophone = fixed position not a whale fix (B.2); ungroundable feeds reported as such
  (B.3). No fetch-to-write, no deploy, no promotion, no commit.
