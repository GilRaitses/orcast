# Summit verification — 2026-06-17 (Post-API-Truth ship)

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

## CloudFront (primary booth URL)

- URL: `https://d2gslju5drx74c.cloudfront.net/`
- Nav labels: **Recent sightings**, **Score grid**, **Reports**
- `/reports`: auto-generated report + **Download CSV** button verified in browser
- Bundle: `main.1923ee57740e9b00.js`

## orcast.org (Firebase custom domain)

- Deploy: **complete** 2026-06-17 (Firebase Hosting `orca-904de`)
- Fix applied: GitHub secret `FIREBASE_SERVICE_ACCOUNT_ORCA_904DE` updated to `orca-904de` service account (was wrong project)
- `last-modified`: 2026-06-17; bundle matches CloudFront (`main.1923ee57740e9b00.js`)
- `/reports`: HTTP 200

## CI (commit `106b708`)

| Workflow | Result |
|----------|--------|
| AWS Backend CI | pass |
| Angular Unit Tests | pass (35) |
| Cloudflare Deploy | pass (skip if no secrets) |
| Firebase Hosting | deploy step failed before secret fix; re-run after secret update |

## Offline demo

- `bash scripts/rebuild.sh --local-only` → demo/cache refreshed
- `bash scripts/demo-start.sh` → cache on `:8080`

## Booth recommendation

1. Primary QR: CloudFront landing or orcast.org (both current)
2. Demo flow: `/` → `/reports` → CSV → `/ml-predictions` (Score grid)
3. Honest line: recent sightings are historical; agent chat is report summary not LLM
4. Ingest POST is key-protected in production
