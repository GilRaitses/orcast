# Exploration guide — Wave Set E contract

Canonical API + schema for the Aurora-backed exploration guide. DynamoDB + S3 remain the **system of record**; Aurora stores guided session history only.

## Data split

| Store | Role |
|-------|------|
| DynamoDB + S3 | Sightings, gates, audit, fit artifacts (unchanged) |
| Aurora PostgreSQL | `exploration_sessions`, `exploration_turns` — multi-turn guide history, tool traces, deep links |

## Network (production)

App Runner uses a **VPC connector** to reach **private RDS PostgreSQL** in dedicated subnets. Security group ingress on 5432 is limited to the App Runner connector SG only (`PubliclyAccessible: false`). DynamoDB, S3, and Bedrock are reached via VPC endpoints; outbound NOAA/external APIs use a NAT gateway in the exploration VPC.

Local dev: set `ORCAST_DATABASE_URL=postgresql://orcast:orcast@127.0.0.1:5432/orcast_explore` and run `001_initial.sql` once.

## Schema

```sql
-- migrations/001_initial.sql

CREATE TABLE IF NOT EXISTS exploration_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  client_ip_hash TEXT,
  title TEXT
);

CREATE TABLE IF NOT EXISTS exploration_turns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES exploration_sessions(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  tool_calls_json JSONB DEFAULT '[]'::jsonb,
  gate_ids TEXT[] DEFAULT '{}',
  provenance_refs TEXT[] DEFAULT '{}',
  model TEXT,
  source TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_exploration_turns_session
  ON exploration_turns(session_id, created_at);
```

## REST API

All paths are on App Runner; H0 reaches them via `/api/be/...` (public, rate-limited).

### `GET /api/explore/status`

Returns Bedrock + Aurora connectivity (mirrors sighting-assist status shape).

```json
{
  "status": "success",
  "aurora_enabled": true,
  "aurora_connected": true,
  "bedrock_enabled": true,
  "narration_backend": "bedrock",
  "fallback": "template"
}
```

When `ORCAST_DATABASE_URL` is empty: `aurora_enabled: false`, `aurora_connected: false`.

### `POST /api/explore/sessions`

Create a session. Optional body: `{ "title": "..." }`.

Response: `{ "status": "success", "session_id": "<uuid>" }`

503 when Aurora disabled.

### `POST /api/explore/turn`

```json
{
  "session_id": "<uuid>",
  "message": "What gates block promotion?",
  "viewport": { "lat": 48.55, "lng": -123.05, "zoom": 10 },
  "focus": { "cell": "48.55,-123.05" }
}
```

Response:

```json
{
  "status": "success",
  "reply": "...",
  "citations": [{ "label": "Fitness gates", "href": "/gates" }],
  "deep_links": [{ "label": "Provenance", "href": "/?lat=48.55&lng=-123.05" }],
  "source": "bedrock",
  "model": "global.anthropic.claude-haiku-4-5-20251001-v1:0",
  "tools_used": ["fetch_gates", "fetch_provenance"]
}
```

503 when Aurora disabled. 404 when session not found.

## Read-only tools (internal)

Implemented in `src/aws_backend/exploration/tools.py`. Called only from `guide.py` — **never** exposed as HTTP write endpoints and **never** raw SQL against DynamoDB from the LLM.

| Tool | Data source |
|------|-------------|
| `fetch_gates` | `_load_fit_report()` / kernel gate helpers |
| `fetch_provenance` | `KernelForecaster` + provenance router logic |
| `fetch_hotspots` | hotspots read path |
| `fetch_forecast_cell` | kernel forecast at lat/lng/when |

No write tools. No promotion, moderation, or decision-record endpoints.

## UI copy rules

Use:

- "Exploration guide"
- "Navigate gates and provenance"
- "Grounded in the same gates as the forecast"

Do **not** use:

- "Ask the AI"
- "AI forecast oracle"
- "Chat with orcast"

## Migration (E4)

After CFN deploy and App Runner roll:

```bash
psql "$ORCAST_DATABASE_URL" -f src/aws_backend/exploration/migrations/001_initial.sql
```

Run once per environment from a bastion or local tunnel to Aurora.

## CFN outputs

- `ExplorationDatabaseEndpoint`
- `ExplorationDatabaseSecretArn`

App Runner env: `ORCAST_DATABASE_URL` (resolved from secret at deploy).
