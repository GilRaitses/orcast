# Summit verification — 2026-06-18 (Wave 1 MapFoundation deploy)

## Backend (live)

- URL: `https://pjrftm3bkv.us-west-2.awsapprunner.com`
- API catalog: [docs/API.md](../API.md)
- Write auth: `ORCAST_API_KEY` set via CloudFormation; GitHub secret `ORCAST_API_KEY` configured

### Live curl checklist

| Check | Expected | Result |
|-------|----------|--------|
| `GET /health` | `healthy` or `degraded` with `sources` | **pass** — `healthy` |
| `GET /api/verified-sightings` count ≤ `/api/sightings` | filtered set | **pass** — verified=5, all=8 |
| `GET /api/predictions` | **410** with replacement hint | **pass** |
| `POST /api/reports/probability` + CSV | report + download | **pass** |
| `POST /api/sightings/ingest` without key | **401** | **pass** |
| `GET /api/realtime/events` | historical sightings, not live acoustics | **pass** |

```bash
BASE=https://pjrftm3bkv.us-west-2.awsapprunner.com
curl -s "$BASE/health" | jq .
curl -s -o /dev/null -w '%{http_code}\n' -X POST "$BASE/api/sightings/ingest?include_live=false"  # 401
curl -s -o /dev/null -w '%{http_code}\n' "$BASE/api/predictions"  # 410
```

## Unit tests

| Check | Result |
|-------|--------|
| Angular unit tests (37) | **pass** — 2026-06-18 |

```bash
cd orcast-angular && npm test -- --watch=false --browsers=ChromeHeadless
```

## UI copy (Wave 1 — 2026-06-18)

Reference: [docs/UI_COPY.md](../UI_COPY.md)

| Page | Check | Expected |
|------|-------|----------|
| `/` | Tagline | No `fusion`, `transparent`, `prototype` |
| `/` | Demo badges | `Live API` or `Demo only` |
| `/` | Demo card count | ≤ 4 live demo cards |
| `/` | Shore/kayak copy | "watching from the shore or going out kayaking" |
| `/reports` | CSV + live API | Works |
| `/ml-predictions` | Title | "Probability map" — no PINN/model selector |
| `/score-grid` | Redirect | → `/ml-predictions` |
| `/realtime` | Copy | No hydrophone detection / audio chrome |
| `/live-demo` | Copy | "Map demo" + `Demo only`; no fake % metrics |
| Nav | Links | Home, Reports (emphasized), Score grid |

Banned in visible UI: `fusion`, `transparent`, `PINN`, `ML Predictions` (product name), fake accuracy bars.

### Google Maps API key

Restrict by HTTP referrer in GCP console for production domains (`orcast.org`, `d2gslju5drx74c.cloudfront.net`, `localhost:4200`). Long-term: inject key via environment at build time.

**2026-06-18:** Maps load on all map routes. No `RefererNotAllowedMapError`, duplicate map init errors, or "For development purposes only" watermark observed in browser console on CloudFront.

## Readable instrumentation hero (2026-06-19)

Landing hero now synthesizes the real instrumented data instead of the synthetic forecast grid.

- **Typed events accessor** ([backend.service.ts]): `getMapEvents()` -> `MapEvent[]` from `/api/realtime/events`, classifying `orcahello` as acoustic, others visual.
- **Map layers** ([map.service.ts]): `addDetectionHeat` (deck.gl heat weighted by confidence x recency), `addTypedSightings` (visual dots vs acoustic rings, honest info windows), `addFeedConnectors` (sighting -> nearest station), online/offline station styling.
- **Landing** ([landing.component.ts]): composes the four layers via `forkJoin(getMapEvents, getHydrophoneData)`, recency factor `exp(-ageDays/540)` clamped; added a legend overlay; removed the synthetic grid from the hero (score grid still uses it).
- Deploy: `main.6732fac6aae7a048.js` (CloudFront + Firebase). Tests 65/65. Playwright landing spec passes (real tiles, no console errors).
- Verified live: heat blooms around real detection clusters, orange visual markers, legend present.

## Caveat fixes + ML integration (2026-06-19)

Addressed the remaining map caveats and researched orca ML integration.

### Shipped

- **Real coastline:** OSM `natural=coastline` (ODbL) for the archipelago → `data/geo/san_juan_land.geojson` (50 island polygons, 3,363 vertices) + regenerated `geo-region.data.ts`. Replaces hand-authored polygons. geo-region specs 16/16.
- **Backend truth pipeline:** new `src/aws_backend/geo_region.py` (loads the coastline mask); normalizers drop out-of-bounds + snap on-shore to water; `scoring.py` clamps hotspot centroids to water; `read.py` filters feeds to in-region server-side. Backend pytest 37/37.
- **OrcaHello fixed:** adapter repointed to the live API `https://aifororcasdetections.azurewebsites.net/api/detections` (top-level array, confidence 0-100, `location.*`). Live: `orcahello available=True, records=1, err=None`; health now **healthy**.
- **HeatmapLayer removal fix:** Google removed `HeatmapLayer` in Maps JS v3.65 (it threw on landing + ml-predictions). Replaced with a circle-density surface in `map.service.ts`; ml-predictions button no longer sticks on "Loading…". Frontend karma 64/64.
- **E2E + visual-regression suite:** Playwright suite under `orcast-angular/e2e/` (tile/marker/console-error assertions across routes, desktop + mobile); deleted 24 stale Cypress specs, kept 4.
- **ML research:** `docs/ml/ORCA_ML_INTEGRATION.md` (OrcaHello API + SRKW model, Orcasound open data, Pod.Cast/Watkins, Perch 2.0/Palmer 2025, OBIS/iNat/NOAA, DTAG) with ranked near-term integrations.

### Deploys

| Surface | Artifact | Result |
|---------|----------|--------|
| Frontend (CloudFront + Firebase) | `main.947bc52172d1b99a.js` | **pass** |
| Backend (App Runner via deploy.sh) | new image + Dockerfile copies coastline asset | **pass** (App Runner RUNNING; health healthy) |

### Live backend verification

| Check | Result |
|-------|--------|
| `/health` status | **healthy** (was degraded) |
| sources | obis_verified (8), orcahello (1), community (1) — all available, no errors |
| `/api/live-hydrophones` | 3 in-region stations only (out-of-region hidden) |

### Findings from the new suite (ACTION REQUIRED)

1. **HeatmapLayer v3.65 removal** — caught and fixed (above).
2. **Google Maps key rejected → demo-key quota exhausted.** The live site loads Maps with `GOOGLE_API_KEY_REDACTED`, but Google rejects it and falls back to the rate-limited demo key, which is now over quota (`Maps Demo Key limit reached ... project=293403666260`). Result: **map tiles currently do not render on production.** This is a GCP infra action, not code: verify the key's project (`orca-904de`) has Maps JavaScript API enabled, active billing, and HTTP-referrer allowlist including `https://orcast.org/*`, `https://d2gslju5drx74c.cloudfront.net/*`. Until fixed, maps will be blank/throttled for users.

## Maps build — landing hero + data truth (2026-06-19)

Geo-region water mask, data-truth fixes, and a coastline heatmap landing hero.

### Deploy

| Surface | Bundle | Result |
|---------|--------|--------|
| AWS CloudFront | `main.545106d976d8cdc5.js` | **pass** |
| Firebase (orcast.org) | `main.545106d976d8cdc5.js` | **pass** |

Unit tests: **58/58 pass** (10 new geo-region specs + data-truth specs).

### What changed

- New `geo-region.ts` + embedded San Juan land polygons: `inBounds`, `isOnLand`, `isInWater`, `snapToWater`, `distanceKm`.
- Data truth: sightings/feeds filtered to the archipelago bounds; on-shore points snapped to water; hotspot centroids clamped off land; heatmap masked to in-water cells with a floor; out-of-region hydrophones (MaST Center, Port Townsend, Bush Point, etc.) hidden; fabricated pod identity removed (`inferPod` deleted; no J/K/L/Transient/Offshore filters).
- Landing: coastline heatmap hero (archipelago framing, heatmap + in-region feeds + sighting markers), tap-water peek to reports/plan, tagline card + pilot banner, demoted CTAs, "Start here" 3-step path retained.

### Visual verification (orcast.org, 2026-06-19)

| Route | Result | Notes |
|-------|--------|-------|
| `/` | **pass** | Full archipelago map hero; sighting markers clustered in-region; tagline card + pilot banner; Start here path below |
| `/historical` | **pass** | Pod Types filters removed; Behaviors only; stats show Top behavior / Top location (no Top pod) |

## Path A — community submissions (moderation queue, 2026-06-19)

Real community sighting pipeline shipped. Public submit lands in a pending queue;
admin approves; approved entries feed the existing pipeline as a low-reliability
`community` source (cross-validation keeps them tentative).

### Backend deploy

- CloudFormation `orcast-aws-backend` updated to **UPDATE_COMPLETE** (new `CommunitySubmissionsTable`, IAM ARN, `ORCAST_COMMUNITY_TABLE` env). App Runner image `5c0c0c1` pushed to ECR.
- Existing `ORCAST_API_KEY` preserved (recovered from the running service; not overwritten).

### Endpoint smoke (live, `pjrftm3bkv.us-west-2.awsapprunner.com`)

| Check | Expected | Result |
|-------|----------|--------|
| `POST /api/community/sightings` (no key) | 201 pending | **pass** |
| `GET /api/community/submissions` (no key) | 401 | **pass** |
| `GET /api/community/submissions` (key) | 200 | **pass** |
| approve + `ingest` + `/api/realtime/events` | `source:"community"` present | **pass** |

### Tests

- Backend pytest: **24 passed** (7 new community tests).
- Frontend karma: **43 passed**.

### Frontend deploy + verify

- Bundle `main.df446101c3a6464d.js` on CloudFront + orcast.org.
- `/contribute`: rewired to POST the live endpoint, moderation note, "Your name" field, click-to-pin location map, local cache fallback. Verified live.

## Phase 5 — field-pilot UI (2026-06-19)

Prototype field tools added on the shared shells. Honest scope: local-only shore
form, report-API-backed trip planner, crowd-tag placeholder.

### Deploy

| Surface | Bundle | Result |
|---------|--------|--------|
| AWS CloudFront | `main.baf001c3db35d6d4.js` | **pass** |
| Firebase (orcast.org) | `main.baf001c3db35d6d4.js` | **pass** — hashes match |

Unit tests: **42/42 pass** (5 new `PilotSubmissionService` specs).

### What changed

- New `/plan` (`TripPlannerComponent`): island picker → top-3 hotspots from the live report API, filtered within ~12 km of the island centroid, shown as cards + markers on a satellite map. Honest caption, no faked day-part precision.
- New `/contribute` (`ContributeComponent`) + `PilotSubmissionService`: shore sighting form persisted to `localStorage` (`orcast_pilot_sightings`), "Queued for the August pilot" success state, queued list + Clear all. Clearly labeled prototype, device-only.
- `/realtime`: disabled "Tag this clip (coming August)" crowd-tag placeholder + note in the Stations panel.
- Nav: added "Plan" link. Landing: "Field tools (preview)" cards link `/plan` and `/contribute`.
- `docs/UI_COPY.md`: Phase 5 approved phrases added.

### Visual verification (orcast.org, 2026-06-19)

| Route | Result | Notes |
|-------|--------|-------|
| `/plan` | **pass** | San Juan → Salmon Bank 60%, Spieden 58%, Lime Kiln 56%; markers + fitBounds on satellite map; "Plan" nav active |
| `/contribute` | **pass** | Submitted Lime Kiln Point → success state + queued list entry; Clear all empties list |
| `/realtime` | **pass** | Stations panel shows disabled "Tag this clip (coming August)" + August-pilot note |

## UI redesign wave (2026-06-19)

Design-system foundation + map/story surfaces rebuilt on shared shells.

### Deploy

| Surface | Bundle | CSS | Result |
|---------|--------|-----|--------|
| AWS CloudFront | `main.f078754bf9b14ae8.js` | `styles.9c5417cb70c3d51f.css` | **pass** |
| Firebase (orcast.org) | `main.f078754bf9b14ae8.js` | `styles.9c5417cb70c3d51f.css` | **pass** — hashes match |

Unit tests: **37/37 pass**.

### What changed

- Design tokens + utility classes centralized in `src/styles.scss` (CSS variables, `.btn`, `.card`, `.badge`, `.pilot-banner`).
- Shared shells: `AppShellComponent` (nav + footer), `MapShellComponent` (full-viewport map + slotted panels), `CollapsiblePanelComponent`.
- `/reports` rebuilt as list + map split view; hotspots plotted as markers (`MapService.addReportHotspots`/`fitBounds`); internal IDs/`model_version`/reason codes moved to a collapsed "Report details" accordion.
- `/historical`, `/realtime`, `/ml-predictions` adopted `MapShell` + `CollapsiblePanel`.
- Landing rebuilt with `AppShell`, single primary CTA (`See this week's map`), always-on pilot banner, 3-step guided path.
- Partners aligned to `AppShell` + shared cards.
- Fixed projected `[map]` slot CSS so satellite tiles render (was black void on shell pages).

### Visual verification (orcast.org, 2026-06-19)

| Route | Result | Notes |
|-------|--------|-------|
| `/reports` | **pass** | Split view; 8 hotspot cards (name + chance % + sightings); markers on satellite map; no internal IDs in default view |
| `/historical` | **pass** | Full satellite map; 5 markers; collapsible Pod types/Behaviors; inline stats; bottom-right legend |
| `/realtime` | **pass** | Full satellite map; orange sighting markers + cyan hydrophone stations coexist; Stations panel collapsed; confidence-labeled list |
| `/ml-predictions` | **pass** | Full satellite map; 54 grid points, max probability 8.7% (5% default threshold); "Score grid" nav active |
| `/` | **pass** | Shared nav + footer; pilot banner; guided path |

### Phase 4 — route quarantine (2026-06-19, bundle `main.40a48d366eddd066.js`)

Legacy demo/agent routes carrying old ORCAST/multi-agent/PINN copy are no longer
linked from nav, landing, or footer. Direct hits now redirect to live pages
(`app.routes.ts`):

| Old route | Redirects to | Verified |
|-----------|--------------|----------|
| `/agent-spatial-demo` | `/reports` | **pass** |
| `/agent-demo` | `/reports` | — |
| `/main-map` | `/historical` | **pass** |
| `/dashboard` | `/reports` | — |
| `/automated-demo` | `/` (landing) | — |
| `/live-demo` | kept (footer "Map demo", `Demo only`); trimmed duplicate disclaimer | — |

## Deploy (2026-06-18)

| Surface | Script | Configuration | Result |
|---------|--------|---------------|--------|
| AWS CloudFront | `tools/deployment/aws/deploy-frontend.sh` | `--configuration=aws` | **pass** |
| Firebase (orcast.org) | `tools/deployment/firebase/deploy.sh` | `--configuration=firebase` | **pass** |

### Bundle hash

- Built: `main.db7787d11bd719e6.js`
- CloudFront HTML: `main.db7787d11bd719e6.js` — **match**
- orcast.org HTML: `main.db7787d11bd719e6.js` — **match**

## CloudFront (primary booth URL)

- URL: `https://d2gslju5drx74c.cloudfront.net/`
- Nav labels: **Home**, **Reports**, **Historical sightings**, **Recent sightings**, **Score grid**
- Bundle: `main.db7787d11bd719e6.js` (Wave 1 deploy 2026-06-18)

### Visual verification — CloudFront (2026-06-18)

| Route | Check | Result | Notes |
|-------|-------|--------|-------|
| `/` | Landing | **pass** | 4 live demo cards (all `Live API`); shore/kayak copy present; no degraded backend badge |
| `/reports` | Probability report | **pass** | h1 "Probability report"; auto-generated report with 8 hotspots; Download CSV visible |
| `/historical` | Map tiles + markers | **pass** | Satellite tiles loaded; 5 verified sightings; blue markers on map |
| `/realtime` | Sightings + hydrophones | **pass** | 8 sightings in list with red map markers; 9 hydrophone stations listed |
| `/ml-predictions` | Grid points | **pass** | Grid points: 54; max probability 8.6%; map tiles visible |

## orcast.org (Firebase custom domain)

- Deploy: **complete** 2026-06-18 (Firebase Hosting `orca-904de`)
- Bundle matches CloudFront: `main.db7787d11bd719e6.js`
- `/reports`: HTTP 200

## CI (commit `106b708`)

| Workflow | Result |
|----------|--------|
| AWS Backend CI | pass |
| Angular Unit Tests | pass (37) |
| Cloudflare Deploy | pass (skip if no secrets) |
| Firebase Hosting | deploy step failed before secret fix; re-run after secret update |

## Offline demo

- `bash scripts/rebuild.sh --local-only` → demo/cache refreshed
- `bash scripts/demo-start.sh` → cache on `:8080`

## Booth recommendation

1. Primary QR: CloudFront landing or orcast.org (both current, same bundle)
2. Demo flow: `/` → `/reports` → CSV → `/ml-predictions` (Score grid)
3. Honest line: recent sightings are historical; agent chat is report summary not LLM
4. Ingest POST is key-protected in production
