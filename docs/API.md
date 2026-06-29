# ORCAST AWS Backend API

Single source of truth for the live AWS App Runner backend. Base URL (production):

```
https://pjrftm3bkv.us-west-2.awsapprunner.com
```

Run `bash scripts/inject-backend-url.sh` before frontend builds so Angular picks up the current URL from `infra/aws/state/deployment-manifest.json`.

Historical Cloudflare Worker routes (`/api/predictions`, etc.) are **not** implemented on the AWS backend except as 410 Gone stubs. See [Deprecated](#deprecated-410-gone).

Truth labels follow [workflow-truth-table.md](devpost/workflow-truth-table.md). Casting contract: [MANAGED_AGENTS_CONTRACT.md](devpost/casting/MANAGED_AGENTS_CONTRACT.md). Partner agents: [API_AGENTS.md](devpost/API_AGENTS.md).

---

## Vercel proxy (H0 web)

The hackathon web app at https://orcast-h0.vercel.app routes browser traffic through `web/app/api/be/[...path]/route.ts`:

- **Public GET** allow-list (gates, provenance, explore status, interactions status, sightings, …)
- **Public POST** for explore sessions/turn, interactions, sighting-assist (rate-limited per IP)
- **Governance writes** (decision records, promotion, community moderation) require WorkOS session on Vercel; the proxy injects `X-ORCAST-Key` and reviewer identity headers
- Direct App Runner calls with only `X-ORCAST-Key` are **not** sufficient for governance writes in production

---

## Supported — read & forecast

| Method | Path | Auth | Truth | Description |
|--------|------|------|-------|-------------|
| GET | `/` | none | live | Service metadata |
| GET | `/health` | none | live | Health with source breakdown |
| GET | `/api/status` | none | live | API version, enabled sources, deprecated routes |
| GET | `/api/sightings` | none | live | All normalized sightings |
| GET | `/api/verified-sightings` | none | live | Filtered by validation status |
| GET | `/api/live-hydrophones` | none | live | Static Orcasound catalog (no live stream checks) |
| GET | `/api/realtime/events` | none | partially live | Recent sightings as events (`data_freshness: historical`) |
| GET | `/api/environmental` | none | live | NOAA environmental snapshot |
| GET | `/api/hotspots` | none | live | Ranked hotspot clusters |
| GET | `/api/data-status` | none | partially live | Stream freshness / backfill status |
| POST | `/forecast/quick` | none | live | Point probability at lat/lng |
| POST | `/forecast/spatial` | none | live | Probability grid |
| GET | `/forecast/current` | none | live | Default San Juan Islands point forecast |
| GET | `/forecast/status` | none | live | Model id metadata |
| GET | `/api/reports/{report_id}` | none | live | Fetch stored report |
| GET | `/api/reports/{report_id}.csv` | none | live | CSV export |

## Supported — writes (keyed when `ORCAST_API_KEY` set)

| Method | Path | Auth | Truth | Description |
|--------|------|------|-------|-------------|
| POST | `/api/sightings/ingest` | `X-ORCAST-Key` | live | Run ingestion adapters |
| POST | `/api/hotspots/recompute` | `X-ORCAST-Key` | live | Regenerate hotspots |
| POST | `/api/reports/probability` | `X-ORCAST-Key` | live | Generate ranked hotspot report JSON |
| POST | `/api/timeseries/backfill` | `X-ORCAST-Key` | partially live | Async backfill job |
| POST | `/api/timeseries/refresh` | `X-ORCAST-Key` | partially live | Refresh time-series cache |

When `ORCAST_API_KEY` is **not** configured on App Runner, keyed routes return **503** (not open POST).

## Kernel & traceability

| Method | Path | Auth | Truth | Description |
|--------|------|------|-------|-------------|
| GET | `/api/gates` | none | live | Fitness gates, confidence, promotion state; CV includes `display_status` (IC4) |
| GET | `/api/provenance` | none | live | Cell kernel contributions + nearby evidence |

## Governance & promotion

| Method | Path | Auth | Truth | Description |
|--------|------|------|-------|-------------|
| GET | `/api/decision-records` | `X-ORCAST-Key` + trusted proxy for prod writes | live | Human promotion audit log |
| POST | `/api/decision-records` | keyed + WorkOS via Vercel proxy | live | Record promote / hold / reject |
| POST | `/api/promotion/draft` | `X-ORCAST-Key` | partially live | Supervisor draft |
| POST | `/api/promotion/apply` | keyed + trusted proxy | partially live | Apply promotion marker |
| POST | `/api/orchestrator/run` | `X-ORCAST-Key` | partially live | Trigger Step Functions orchestrator |
| GET | `/api/review-dossier/latest` | `X-ORCAST-Key` | partially live | Review dossier JSON |
| GET | `/api/review-dossier/{id}` | `X-ORCAST-Key` | partially live | Dossier by id |
| GET | `/api/review-dossier/{id}/export` | keyed + reviewer | partially live | Redacted/unredacted export |

## Community & journal

| Method | Path | Auth | Truth | Description |
|--------|------|------|-------|-------------|
| POST | `/api/community/sightings` | session (proxy) | live | Submit community sighting |
| GET | `/api/community/submissions` | session (proxy) | live | Moderation queue (PII) |
| POST | `/api/community/submissions/{id}/approve` | session + reviewer | live | Approve submission |
| POST | `/api/community/submissions/{id}/reject` | session + reviewer | live | Reject submission |
| GET | `/api/journal/entries` | session (proxy) | live | User journal list |
| POST | `/api/journal/entries` | session (proxy) | live | Create journal entry |
| POST | `/api/journal/entries/{id}/publish` | session (proxy) | live | Publish to moderation queue |

## Exploration & sighting assist

| Method | Path | Auth | Truth | Description |
|--------|------|------|-------|-------------|
| GET | `/api/explore/status` | none | live | Aurora + narration backend status |
| POST | `/api/explore/sessions` | none (rate-limited on Vercel) | live | Create exploration session |
| POST | `/api/explore/prepare` | none | live | Grounded tool context (no LLM) |
| POST | `/api/explore/turn` | none | live | Guide reply + persist turn |
| GET | `/api/sighting-assist/status` | none | live | Bedrock/template status |
| POST | `/api/sighting-assist` | none | live | `/ask` grounded reply |

## Central Casting (managed agents)

| Method | Path | Auth | Truth | Description |
|--------|------|------|-------|-------------|
| GET | `/api/interactions/status` | none | live | Casting + Aurora status |
| POST | `/api/interactions/prepare` | none | live | Skill context for Gateway narration |
| POST | `/api/interactions` | none | live | Invoke cast role by id or inline agent |
| POST | `/api/interactions/plan` | `X-ORCAST-Key` | live | Keyed surface planner → `ui_intent` + skill execution |
| GET | `/api/managed-agents` | `X-ORCAST-Key` | live | List cast roles |
| GET | `/api/managed-agents/{id}` | `X-ORCAST-Key` | live | Get cast role version |
| POST | `/api/managed-agents` | `X-ORCAST-Key` | live | Create/update cast role |

## Partner API

| Method | Path | Auth | Truth | Description |
|--------|------|------|-------|-------------|
| POST | `/api/partner/verify` | partner key | partially live | Verify hashed partner key |
| GET | `/api/partner/tiers` | `X-ORCAST-Key` | partially live | Tier metadata |

See [API_AGENTS.md](devpost/API_AGENTS.md) for `/api/v1` gateway on Vercel.

### Examples

```bash
BASE=https://pjrftm3bkv.us-west-2.awsapprunner.com

curl -s "$BASE/health" | jq .
curl -s "$BASE/api/gates" | jq '{cv: .gates.cross_validation | {gate_pass, mean_deviance_skill, display_status}}'
curl -s "$BASE/api/verified-sightings" | jq '.total_count'
curl -s -X POST "$BASE/api/reports/probability" \
  -H 'Content-Type: application/json' \
  -H "X-ORCAST-Key: $ORCAST_API_KEY" \
  -d '{"region":"san_juan_islands","min_confidence":0,"report_format":"json"}' | jq '.report.report_id'
```

### Write auth (production)

When `ORCAST_API_KEY` is configured on App Runner:

```
X-ORCAST-Key: <shared secret>
```

Governance writes from the browser go through Vercel with WorkOS session; see [WORKOS_AUTH_EMAIL.md](devpost/WORKOS_AUTH_EMAIL.md).

**Production setup:**

```bash
export ORCAST_API_KEY='your-secret'
gh secret set ORCAST_API_KEY --body "$ORCAST_API_KEY"
bash tools/deployment/aws/set-api-key.sh
```

---

## Deprecated (410 Gone)

These paths return **410** with JSON `{"deprecated": true, "replacement": "..."}`:

| Path | Replacement |
|------|-------------|
| `GET /api/predictions` | `/api/reports/probability` |
| `GET /api/behavioral-analysis` | `/api/reports/probability` |
| `GET /api/dtag-data` | `/api/sightings` |

---

## Not implemented (do not document as live)

- `GET /api/real-time-data`
- `GET /api/feeding-zones`
- `GET /api/ml-predictions`
- `GET /api/recent-sightings`
- `GET /api/environmental-data`
- `GET /api/hydrophone-data`

---

## Frontend mapping

| UI route | Backend truth |
|----------|---------------|
| H0 `/gates` | `GET /api/gates` |
| H0 `/explore` | `POST /api/interactions` (cast `explore-guide-v1`) |
| `/reports` | `POST /api/reports/probability` (keyed) |
| `/historical` | `GET /api/verified-sightings` |
| `/ml-predictions` | `POST /forecast/spatial` |
| `/realtime` | `GET /api/realtime/events` (historical freshness label on Angular landing) |

Agent chat in the Angular pilot calls `queryAgent()` which regenerates a probability report summary — **not** an LLM.
