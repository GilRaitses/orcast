# ORCAST AWS Backend API

Single source of truth for the live AWS App Runner backend. Base URL (production):

```
https://pjrftm3bkv.us-west-2.awsapprunner.com
```

Run `bash scripts/inject-backend-url.sh` before frontend builds so Angular picks up the current URL from `infra/aws/state/deployment-manifest.json`.

Historical Cloudflare Worker routes (`/api/predictions`, etc.) are **not** implemented on the AWS backend except as 410 Gone stubs. See [Deprecated](#deprecated-410-gone).

---

## Supported

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | none | Service metadata |
| GET | `/health` | none | Health with source breakdown; `status` is `healthy` or `degraded` |
| GET | `/api/status` | none | API version, enabled sources, live endpoint list, deprecated routes |
| GET | `/api/sightings` | none | All normalized sightings (includes tentative/rejected) |
| GET | `/api/verified-sightings` | none | Sightings with `validation_status` in `{verified, likely}` by default; optional `?min_status=verified` |
| POST | `/api/sightings/ingest` | `X-ORCAST-Key` when `ORCAST_API_KEY` set | Run ingestion adapters; `?include_live=true` |
| GET | `/api/live-hydrophones` | none | Static Orcasound catalog (`source: static_catalog`, no live stream checks) |
| GET | `/api/realtime/events` | none | Recent **sightings** as events (`event_type: sighting`, `data_freshness: historical`) |
| GET | `/api/environmental` | none | NOAA environmental snapshot |
| GET | `/api/hotspots` | none | Ranked hotspot clusters |
| POST | `/api/hotspots/recompute` | `X-ORCAST-Key` when key set | Regenerate hotspots from stored sightings |
| POST | `/forecast/quick` | none | Point probability at lat/lng |
| POST | `/forecast/spatial` | none | Probability grid; `hours` scales horizon weighting |
| GET | `/forecast/current` | none | Default San Juan Islands point forecast |
| GET | `/forecast/status` | none | Model id `aws-deterministic-hotspot-v1` |
| POST | `/api/reports/probability` | none | Generate ranked hotspot report JSON |
| GET | `/api/reports/{report_id}` | none | Fetch stored report |
| GET | `/api/reports/{report_id}.csv` | none | CSV export |

### Examples

```bash
BASE=https://pjrftm3bkv.us-west-2.awsapprunner.com

curl -s "$BASE/health" | jq .
curl -s "$BASE/api/verified-sightings" | jq '.total_count'
curl -s -X POST "$BASE/api/reports/probability" \
  -H 'Content-Type: application/json' \
  -d '{"region":"san_juan_islands","min_confidence":0,"report_format":"json"}' | jq '.report.report_id'
curl -s -X POST "$BASE/forecast/spatial" \
  -H 'Content-Type: application/json' \
  -d '{"lat":48.5465,"lng":-123.0307,"radius_km":12,"grid_resolution":0.04,"hours":24}' | jq '.total_points'
```

### Write auth (production)

When `ORCAST_API_KEY` is configured on App Runner, POST ingest/recompute require:

```
X-ORCAST-Key: <shared secret>
```

Local dev with no key set allows open POST access.

**Production setup:** generate a key, store in GitHub secret `ORCAST_API_KEY`, then run:

```bash
export ORCAST_API_KEY='your-secret'
gh secret set ORCAST_API_KEY --body "$ORCAST_API_KEY"
bash tools/deployment/aws/set-api-key.sh
```

Lambda schedulers receive the same key via CloudFormation and send `X-ORCAST-Key` on scheduled ingest/recompute.

---

## Deprecated (410 Gone)

These paths return **410** with JSON `{"deprecated": true, "replacement": "..."}`:

| Path | Replacement |
|------|-------------|
| `GET /api/predictions` | `/api/reports/probability` |
| `GET /api/behavioral-analysis` | `/api/reports/probability` |
| `GET /api/dtag-data` | `/api/sightings` |

```bash
curl -s -o /dev/null -w '%{http_code}\n' "$BASE/api/predictions"
# 410
```

Legacy references remain in `archive/` for historical context only.

---

## Not implemented (do not document as live)

The following appear in old Cloudflare/Firebase docs but are **not** on the AWS backend:

- `GET /api/real-time-data`
- `GET /api/feeding-zones`
- `GET /api/ml-predictions`
- `GET /api/recent-sightings`
- `GET /api/environmental-data`
- `GET /api/hydrophone-data`

Use the supported endpoints above instead.

---

## Frontend mapping

| UI route | Backend truth |
|----------|---------------|
| `/reports` | `POST /api/reports/probability` |
| `/historical` | `GET /api/verified-sightings` |
| `/ml-predictions` | `POST /forecast/spatial` (spatial score grid, not ML) |
| `/realtime` | `GET /api/realtime/events` + static hydrophone catalog |

Agent chat in the UI calls `queryAgent()` which regenerates a probability report summary — **not** an LLM.
