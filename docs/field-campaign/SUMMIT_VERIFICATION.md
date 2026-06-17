# Summit verification — 2026-06-17 (API Truth repair)

## Backend (live)

- URL: `https://pjrftm3bkv.us-west-2.awsapprunner.com`
- Deploy: **complete** (image `85c0119`, router split + API truth fixes)
- API catalog: [docs/API.md](../API.md)

### Live curl checklist (post-deploy)

| Check | Expected | Result |
|-------|----------|--------|
| `GET /health` | `healthy` or `degraded` with `sources` array | **pass** — `healthy`, `sources: []` (no ingestion run on cold start) |
| `GET /api/verified-sightings` count ≤ `/api/sightings` | filtered set | **pass** — verified=5, all=8 |
| `GET /api/predictions` | **410** with replacement hint | **pass** — 410, `replacement: /api/reports/probability` |
| `POST /api/reports/probability` + CSV | report + download | **pass** (smoke test) |
| `POST /api/sightings/ingest` without key | **401** when `ORCAST_API_KEY` set | **pending** — ApiKey CFN param empty (open POST for now) |
| `GET /api/realtime/events` | `event_type: sighting`, no fake hydrophone keys | **pass** — `data_freshness: historical`, `stream_active: false` |

```bash
BASE=https://pjrftm3bkv.us-west-2.awsapprunner.com
curl -s "$BASE/health" | jq .
curl -s "$BASE/api/predictions" -w '\n%{http_code}\n'
curl -s "$BASE/api/verified-sightings" | jq '.total_count'
```

## CloudFront (primary booth URL)

- URL: `https://d2gslju5drx74c.cloudfront.net/`
- Deploy: **complete** (2026-06-17 — honest UI labels: Score grid, Recent sightings)
- Demo routes: `/`, `/reports`, `/partners`, `/historical`, `/ml-predictions`, `/realtime`
- `/reports`: generate report → CSV download (Cypress + manual)

## orcast.org (Firebase custom domain)

- Status: **stale July 2025 shell** until Firebase deploy
- Manual: `firebase login && bash tools/deployment/firebase/deploy.sh`

## Offline demo

- `bash scripts/rebuild.sh --local-only` → demo/cache refreshed **2026-06-17**
- `bash scripts/demo-start.sh` → cache on `:8080`

## Booth recommendation

1. Primary QR: CloudFront landing
2. Demo flow: `/` → `/reports` → CSV download → `/ml-predictions` (Score grid)
3. Honest line: recent sightings are historical; agent chat is report summary not LLM
4. Set `ORCAST_API_KEY` on App Runner before exposing ingest POST publicly
