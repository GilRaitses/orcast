# WS-TRIPS step log

Suborchestrator for WS-TRIPS. This task ran the Research wave then the Discovery
wave only. Read-only on code; only Markdown was written, all in this folder. No
dev server, no commit, no other subagents launched.

## 2026-06-27

1. Read the program charter, the W3 trips dispatch, and the finalized
   `CONNECTIONS_RESEARCH.md` (endpoints, fields, adapter signatures, the
   Arlington -> Anacortes coverage gap).
2. Read the W1 TS port `web/lib/trips/model.ts` and confirmed the lazy metadata
   rollup foot-gun (totalCost / overallProbability recompute only in addDay /
   addDayTrip).
3. Read the planner core (`casting/planner.py`), the skills manifest, the
   interactions route (`routers/interactions.py`), the panel host
   (`ActiveSurfaceHost.tsx`), `web/lib/uiIntent.ts`, and the panel registry +
   validation (`casting/panels.py`, `panel_registry.json`).
4. Read the DONE W2 clients (`sources/wsf.py`, `sources/wsdot_traffic.py`) and the
   WSDOT test fixtures; confirmed the live, gitignored, accruing corridor history
   log at `data/external/traffic_corridor/seatac_anacortes.jsonl`.
5. Found the existing tide/current model surface: `modeling/tide_harmonic.py`
   (`HarmonicTide`) and `modeling/tide_phase.py` (`TidalPhase`,
   `HarmonicTidalPhase`). Confirmed it is a harmonic predictor (modeled), not
   observed currents.
6. Read the policy/manifest validation, the planner agent seed
   (`seeds/surface-planner-v1.json`) with its `allowed_panels` / `skills`
   allow-lists, the camera director (`scene/camera/director.ts`), the GatedAction
   chip, and an existing console panel (`HydrophoneSignalPanel.tsx`) as a template.
7. Confirmed by glob that the WS-TRIPS create-files are greenfield (no
   `casting/trips/`, `modeling/traffic/`, `sources/flights.py`, `sources/seaplane.py`,
   `KayakPanel.tsx`, `SidequestPanel.tsx`).
8. Wrote RESEARCH_SYNTHESIS.md (branch design, connection-feasibility reasoning,
   corridor ETA model approach, kayak tide surface, lazy-rollup note) — research
   gate met.
9. Wrote DISCOVERY_MAP.md (planner + branch seam, the multi-file panel
   registration seam, one-file-one-owner table, kayak tide seam, honesty map) —
   discovery gate met.
10. Wrote IMPLEMENTATION_DISPATCH.md (PROPOSED: producers A/A2/B/C/D + phase-B
    editor E, each with task / deliverables / validation / collision-avoidance,
    plus four open decisions for the operator). Held for the program gate.

Waves complete: Research, Discovery. Not started: Implementation, Adversarial,
Remediation, Acceptance.

## 2026-06-28 Wave 2 (live-route remediation, two tasks)

Ran under O0 reconciliation. Operator decided both tasks. No commit, no deploy,
no git add. The web fix `643eef7` is already an ancestor of `origin/main` and
Vercel auto-deploys main, so HEAD is live.

### Task A browser-verify, render verdict CONFIRMED

Loaded the live anonymous home console at https://orcast-h0.vercel.app through
the browser MCP, selected the "Planning a visit" orienting-question chip, typed
"plan a trip from Seattle to the San Juans to see orcas", and sent the turn. The
DOM rendered the trip panels for the visiting branch. The COMPARE PLACES panel
showed "Comparing whale-viewing places across the archipelago" and the
connections plan panel showed the modeled drive leg, the ferry leg, and the
"WSDOT travel-time coverage on I-5 ends near Arlington around milepost 208"
honesty note. Screenshot evidence is at
`.cca/catalogue/O0/20260627_console-ws-trips/gate_screenshots/ws_trips_live_visiting_panels.png`.

To confirm all five trip panel ids I replayed the exact anonymous plan request
the browser posts, from the page context, against the live backend. All four
branches returned 200 and surfaced their panels.

- visiting: compare_places, connections_plan, explore_trace
- here-now: local_area, connections_plan, provenance_pin
- kayak: kayak_plan
- curious: sidequests, explore_trace

That covers all five trip panel ids: compare_places, local_area,
connections_plan, kayak_plan, sidequests.

Precise resolution of the O0 discrepancy. Three live plan calls on one session
isolated the differentiator.

- inline spec plus focus.branch=visiting returned the trip panels.
- agent_id surface-planner-v1 plus focus.branch=visiting returned only
  explore_trace.
- agent_id surface-planner-v1 with no branch returned gates_summary plus
  explore_trace, matching the O0 curl.

The managed by_id path drops the trip panels even with a branch, which proves the
deployed DynamoDB `surface-planner-v1` item still carries the pre-trips
`allowed_panels`. The seed file update was never written to the served store. The
live anonymous console is unaffected because it posts the inline
`PUBLIC_PLANNER_SPEC` whose `allowed_panels` includes the trip panels, so the
inline path overrides the stale managed agent. The ui_intent label reads
surface-planner-v1 on the inline path only because `plan_cast_interaction`
threads `DEFAULT_PLANNER_ID` into `resolve_inline_agent` as the resolved id, and
`hydration_mode` reports by_id because the plan path leaves the
`prepare_interaction_with_skills` default. Both are cosmetic labels and do not
change which allow-list applies.

### Task B /plan 500 to 503 hardening, diffs-only

Root cause restated. `_require_aurora` passes when the connection env var is
present, it does not probe connectivity. `SessionStore.session_exists` then opens
a real connection through `get_connection`, which raises `RuntimeError` when the
driver or DSN is missing and `psycopg.Error` when the host is unreachable or the
schema is unmigrated. The plan handler maps only `LookupError` and `ValueError`,
so the DB error escaped as an unhandled 500.

Change set, both files one owner, no planner runtime logic touched.

- `src/aws_backend/routers/interactions.py`: added a defensive `psycopg` import
  and a `_DB_UNAVAILABLE_ERRORS` tuple of `(RuntimeError, psycopg.Error)`, added
  a `_require_session` helper that wraps `session_exists`, maps a DB connection or
  migration failure to HTTP 503 with the existing contract message, and keeps the
  404 for a missing session. Swapped the inline session check in
  `plan_cast_interaction` for `_require_session`. Other turn handlers were left
  unchanged to keep the diff surgical, and they share the same latent risk.
- `tests/aws_backend/test_interactions_plan.py`: added two L3 tests. One forces
  `session_exists` to raise `RuntimeError` and asserts 503, which runs in this
  env where psycopg is absent. One forces `psycopg.OperationalError` and asserts
  503, gated by `pytest.importorskip` so it runs wherever the driver is present.

Validation. `tests/aws_backend/test_interactions_plan.py` reports 8 passed, 1
skipped. The full `tests/aws_backend` suite reports 324 passed, 1 skipped. The
skip is the psycopg-driver test in a driver-less env. Run with `.venv/bin/python`
because the default python3 has no pytest. tsc was not run because this wave
touched no web sources.

### Adversarial gate before declaring complete

1. Browser evidence is a real screenshot of the live DOM, not inferred, plus
   live API confirmation of all five panel ids.
2. The 503 diff is surgical, one helper plus one call-site swap, and is backed by
   two L3 tests, with the full suite green.
3. No commits, no git add, no deploy, no push, no secrets touched.

### Remaining operator gate for O0

The deployed DynamoDB `surface-planner-v1` allowed_panels is stale and excludes
the trip panels. The anonymous console does not depend on it, so trips render
correctly today. Any by_id caller such as a keyed reviewer console or a raw
integration will not surface trip panels until the updated seed is written to the
served managed-agent store. Writing to DynamoDB is a prod mutation, so I did not
do it. O0 decides whether a managed-store write is in scope. The 503 hardening is
a diff awaiting an operator commit and a backend redeploy.

Waves complete: Research, Discovery, Wave 2 live-route verify plus 503 hardening.
