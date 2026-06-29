# UI intent schema (v1)

Keyed surface planner output for Wave IC6/J. See [J0_SURFACE_PLANNER_CHARTER.md](J0_SURFACE_PLANNER_CHARTER.md).

## Response shape

Returned by `POST /api/interactions/plan` (keyed only):

```json
{
  "status": "success",
  "ui_intent": {
    "version": "1.0.0",
    "planner_agent_id": "surface-planner-v1",
    "skill_plan": ["fetch_gates", "fetch_decision_records"],
    "panels": [
      {
        "id": "gates_summary",
        "surface": "sidebar",
        "priority": 1,
        "props": { "emphasis": "caution" }
      },
      {
        "id": "map_viewport",
        "surface": "map",
        "viewport": { "lat": 48.55, "lng": -123.05, "zoom": 10 }
      }
    ],
    "deep_links": [
      { "label": "Gates", "href": "/gates" },
      { "label": "Decisions", "href": "/decisions" }
    ],
    "focus": { "cell": "48.55,-123.05" }
  },
  "prepare": {
    "context": {},
    "steps": [],
    "annotations": []
  },
  "resolved_spec_hash": "…"
}
```

## Field reference

| Field | Required | Notes |
|-------|----------|-------|
| `ui_intent.version` | yes | Schema semver (`1.0.0`) |
| `ui_intent.planner_agent_id` | yes | Cast role that produced the plan |
| `ui_intent.skill_plan` | yes | Subset of manifest skills; executed after validation |
| `ui_intent.panels[]` | yes | Allow-listed panel ids from [`panel_registry.json`](../../../src/aws_backend/casting/panel_registry.json) |
| `ui_intent.panels[].id` | yes | e.g. `gates_summary`, `map_viewport` |
| `ui_intent.panels[].surface` | yes | `map` or `sidebar` |
| `ui_intent.panels[].priority` | no | Sort order within surface |
| `ui_intent.panels[].props` | no | Panel-specific hints (client interprets) |
| `ui_intent.panels[].viewport` | no | Map panel center/zoom |
| `ui_intent.deep_links[]` | no | Filtered by cast `policy.allowed_deep_links` |
| `ui_intent.focus` | no | Geo focus `{ "cell": "lat,lng" }` |

## Panel registry v1

| `panel.id` | H0 surface |
|------------|------------|
| `map_viewport` | Explore map |
| `explore_trace` | Steps / annotations accordion |
| `gates_summary` | Gates card / link |
| `provenance_pin` | Provenance modal |
| `decisions_table` | Decision audit log |
| `review_dossier` | Review dossier page |
| `moderation_queue` | Moderation queue |
| `provenance_graph` | Metric provenance graph (C/M/X/Data, renders from `prepare.steps[]` + `prepare.annotations[]`) |

Unknown `panel.id` or skill → HTTP 400 `{ "error": "invalid_ui_intent", … }`.

## Step type `plan_output`

Added to interaction `steps[]` on keyed plan responses:

```json
{
  "type": "plan_output",
  "planner_agent_id": "surface-planner-v1",
  "skill_plan": ["fetch_gates"],
  "panel_ids": ["gates_summary", "explore_trace"]
}
```

## Cast role policy extensions

Planner roles set `policy.planner_mode: true` and `policy.allowed_panels[]`. Non-planner roles must not emit `ui_intent`.
