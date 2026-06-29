# Managed agents — Central Casting contract (Wave Set M)

Canonical schema for versioned cast roles on the Aimez control plane. DynamoDB holds configs; Postgres holds interaction traces.

Grounding pattern (IC): [INTERACTIONS_GROUNDING_PATTERN.md](INTERACTIONS_GROUNDING_PATTERN.md). Skill catalog: [SKILL_CATALOG.md](SKILL_CATALOG.md).

## ManagedAgent schema

```json
{
  "id": "explore-guide-v1",
  "version": "1.0.0",
  "instructions": "You are the ORCAST Exploration Guide…",
  "skills": ["fetch_gates", "fetch_provenance", "fetch_hotspots", "fetch_forecast_cell"],
  "data_bindings": {
    "gates": "live:/api/gates"
  },
  "model": {
    "provider": "bedrock",
    "model_id": "global.anthropic.claude-haiku-4-5-20251001-v1:0"
  },
  "policy": {
    "write_tools": false,
    "allowed_deep_links": ["/gates", "/explore", "/"]
  },
  "active": true
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `id` | yes | Stable slug, e.g. `explore-guide-v1` |
| `version` | yes | Semver string; DDB sort key |
| `instructions` | yes | System prompt for narration |
| `skills` | yes | Subset of `SKILL_CATALOG` keys |
| `data_bindings` | no | Declarative artifact pointers |
| `model` | no | Default Bedrock model on App Runner |
| `policy` | yes | `write_tools`, `allowed_deep_links`, `allowed_panels`, `planner_mode` |
| `active` | yes | Inactive versions excluded from latest resolution |

## Skill catalog (M scope)

| Skill | Read-only | Description |
|-------|-----------|-------------|
| `fetch_gates` | yes | Fit report + promotion gates |
| `fetch_provenance` | yes | Cell kernel provenance |
| `fetch_forecast_cell` | yes | Cell intensity summary |
| `fetch_hotspots` | yes | Top hotspot cells |

Unknown skill names → HTTP 400. Write skills blocked when `policy.write_tools` is false.

## Registry API (keyed)

All routes require `X-ORCAST-Key`.

### `GET /api/managed-agents`

List active agent ids and latest versions.

### `GET /api/managed-agents/{agent_id}`

Return latest active version, or `?version=1.0.0` for pin.

### `POST /api/managed-agents`

Create or update a version (body = full ManagedAgent JSON).

## Interactions API (public, rate-limited)

### `GET /api/interactions/status`

Extends explore status with `casting_enabled`, `managed_agents_table`.

### `POST /api/interactions` (by ID or inline agent)

Request (by id):

```json
{
  "session_id": "<uuid>",
  "message": "What blocks promotion?",
  "agent_id": "explore-guide-v1",
  "agent_version": "1.0.0",
  "viewport": { "lat": 48.55, "lng": -123.05 }
}
```

Request (inline hydration, IC3):

```json
{
  "session_id": "<uuid>",
  "message": "What blocks promotion?",
  "agent": {
    "instructions": "You are the ORCAST Exploration Guide…",
    "skills": ["fetch_gates", "fetch_provenance"],
    "policy": { "write_tools": false, "allowed_deep_links": ["/gates", "/explore", "/"] }
  }
}
```

When `agent` is present, `agent_id` is optional (defaults to `inline-{session_prefix}`). `hydration_mode` is `inline` or `by_id`.

### `POST /api/interactions/prepare` (IC3)

Same request body as `POST /api/interactions`. Returns grounded `context`, partial `steps`, and `annotations` without LLM narration or Postgres write. Used by Vercel `web/app/api/interactions/route.ts` (prepare → Gateway → persist).

Response (extends explore turn):

```json
{
  "status": "success",
  "reply": "...",
  "citations": [],
  "deep_links": [],
  "source": "bedrock",
  "model": "...",
  "tools_used": ["fetch_gates"],
  "managed_agent_id": "explore-guide-v1",
  "agent_version": "1.0.0",
  "resolved_spec_hash": "<sha256>",
  "hydration_mode": "by_id",
  "skills_invoked": ["fetch_gates", "fetch_provenance"],
  "steps": [
    { "type": "resolve_agent", "managed_agent_id": "explore-guide-v1", "agent_version": "1.0.0" },
    { "type": "skill_invocation", "skill": "fetch_gates", "output_status": "success", "duration_ms": 12 },
    { "type": "model_output", "provider": "bedrock", "annotations": [] }
  ],
  "annotations": [
    { "type": "gate_citation", "label": "Fitness gates", "href": "/gates" }
  ]
}
```

`steps` and `annotations` follow [INTERACTIONS_GROUNDING_PATTERN.md](INTERACTIONS_GROUNDING_PATTERN.md). IC1 persists `steps` on assistant turns; IC3 renders them in [`ExploreGuidePanel.tsx`](../../../web/app/components/ExploreGuidePanel.tsx).

Inline `agent: { ... }` hydration is supported (IC3). Vercel Gateway route: `web/app/api/interactions/route.ts`.

### `POST /api/interactions/plan` (IC6/J, keyed)

Requires `X-ORCAST-Key`. Defaults to `surface-planner-v1`. Returns validated `ui_intent` (panel ids, `skill_plan`, deep links) plus executed `prepare` payload. See [UI_INTENT_SCHEMA.md](UI_INTENT_SCHEMA.md).

```json
{
  "session_id": "<uuid>",
  "message": "Show decision audit log",
  "viewport": { "lat": 48.55, "lng": -123.05 }
}
```

Vercel reviewer proxy: `web/app/api/interactions/plan/route.ts` (WorkOS session + server-side key).

## Postgres trace columns (migrations 003 + 004)

On `exploration_turns` (assistant rows):

- `interaction_id` UUID
- `managed_agent_id` TEXT
- `agent_version` TEXT
- `resolved_spec_hash` TEXT
- `hydration_mode` TEXT
- `skills_invoked` TEXT[]
- `interaction_steps` JSONB (IC1) — ordered `steps[]` per grounding pattern

## Environment

| Variable | Role |
|----------|------|
| `ORCAST_MANAGED_AGENTS_TABLE` | DynamoDB table name |
| `ORCAST_DATABASE_URL` | Postgres session store |
| `ORCAST_API_KEY` | Registry CRUD auth |

## Out of scope (M / IC3 boundary)

- Gemini, Vertex, Google embeddings, Interactions API
- IC4: gates UI honesty, `docs/API.md` truth
- IC5: prod `ic-gate` deploy verification
