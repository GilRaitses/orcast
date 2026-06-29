# WS-TRIPS Live-Route Discovery

Wave 1, read-only. Sub-orchestrator for WS-TRIPS. Reporting to O0.

This doc names three things the charter asked for. It also corrects one framing
in the Console Journey STEP_LOG that no longer matches HEAD.

## One-line root causes

1. Anonymous trips were excluded because the live home console posts an inline
   planner spec, not the seed or DynamoDB managed agent, and that inline spec
   originally omitted the trip panels and the branch skills, so `draft_ui_intent`
   filtered them out. This is already fixed at HEAD by commit `643eef7`.
2. The runtime `allowed_panels` for the anonymous live route comes from the
   inline `PUBLIC_PLANNER_SPEC` in `web/lib/adaptiveConsole.ts`, resolved by
   `resolve_inline_agent`, not from the seed file and not from DynamoDB.
3. The dev `/plan` 500 is a database reachability and error-mapping gap. The
   handler requires a live Postgres session, `_require_aurora` only checks that
   the env var is present rather than that the database is reachable, and the
   handler maps only `LookupError` and `ValueError`, so a real connection or
   schema failure surfaces as an unhandled 500.

## How the served planner config is loaded at runtime

The anonymous home route is `web/app/page.tsx`, which renders `AdaptiveExplore`.
Every turn calls `runAdaptiveTurn` in `web/lib/adaptiveConsole.ts`, which posts
to `/api/be/api/interactions/plan` with `agent: PUBLIC_PLANNER_SPEC`. That body
field is an inline agent spec.

On the backend, `plan_cast_interaction` in
`src/aws_backend/routers/interactions.py` builds `_inline_dict(payload)` from the
`agent` field and passes it to `plan_interaction`. Inside `plan_interaction`,
`_resolve_cast_agent` sees a non-null inline spec and calls
`resolve_inline_agent`, which copies `policy.allowed_panels` straight from the
posted JSON. `draft_ui_intent` then enforces
`panels = [p for p in panels if p["id"] in allowed_panels]` against that inline
list.

So for an anonymous visitor the effective `allowed_panels` is the inline list in
the browser bundle. The module-level `_store = build_managed_agent_store()` and
the seed `surface-planner-v1.json` are only consulted when a caller passes an
`agent_id` with no inline spec. `build_managed_agent_store` returns
`AwsManagedAgentStore` reading DynamoDB when `storage_backend == "aws"` and
`managed_agents_table` is set, otherwise the in-memory store seeded from the JSON
file. The live anonymous console never takes that path, so the seed update and
any DynamoDB write do not change what an anonymous visitor sees.

## Exact reason anonymous trips were excluded, and current state

The five trip panel ids are `compare_places`, `local_area`, `connections_plan`,
`kayak_plan`, `sidequests`. The branches that emit them live in `_branch_plan`
in `src/aws_backend/casting/planner.py`. A branch only runs when the turn carries
a valid `focus["branch"]` of `visiting`, `here-now`, `kayak`, or `curious`.

Two conditions had to both hold for an anonymous visitor to see a trip panel.
First, the browser had to send `focus.branch`. Second, the inline spec's
`allowed_panels` had to include the panel id, and for the kayak and curious
branches the inline `skills` had to include `fetch_environmental`,
`fetch_live_hydrophones`, and `fetch_verified_sightings`, or those skills get
filtered and the branch panels never assemble.

At the time of the STEP_LOG open item, neither condition held on the live route.
The inline `PUBLIC_PLANNER_SPEC` omitted the trip panels and branch skills, and
`AdaptiveExplore` had no orienting-question affordance to set `focus.branch`.

Commit `643eef7` ("surface trips on the live anonymous home route") already
closed this. At HEAD the inline spec in `web/lib/adaptiveConsole.ts` lists all
five trip panels and the three extra public T0 skills, `AdaptiveExplore.tsx`
renders the "What brings you here?" branch chips and threads `focus.branch`
through `submitMessage`, and `tests/aws_backend/test_planner_trips_branch.py`
pins the exact reduced public spec with
`test_public_spec_surfaces_trip_panels_on_anonymous_route`, parametrized over all
four branches. That commit changed only the browser spec, the browser UI, and a
backend test. It did not change any backend runtime code, because the planner
already supported inline branch panels.

This means the STEP_LOG framing that the SERVED planner config still needs
wiring is stale for the anonymous path. The remaining exposure is deployment and
the `/plan` 500, not a missing backend code change.

## Root cause of the dev /plan 500

`plan_cast_interaction` runs `_require_aurora()`, then constructs
`SessionStore()` and calls `store.session_exists(payload.session_id)` before
planning. `aurora_configured` in `src/aws_backend/exploration/db.py` returns True
when `ORCAST_DATABASE_URL` or the `ORCAST_DB_HOST` and `ORCAST_DB_PASSWORD` pair
is merely present. It does not open a connection. `aurora_connected` is the real
connectivity probe and is not used on this path.

`SessionStore.session_exists` calls `get_connection()`, which runs
`psycopg.connect(**_connect_kwargs())`. If the database is unreachable, if
`psycopg` is not installed, or if the `exploration_sessions` table is not
migrated, that call raises. The `/plan` handler only catches `LookupError` mapped
to 404 and `ValueError` mapped to 400. A `psycopg` or `RuntimeError` is neither,
so FastAPI returns 500.

This matches the observed behavior. A dev backend with the env var set but the
Postgres instance unreachable or unmigrated passes `_require_aurora`, then 500s
inside `session_exists`. The visiting and here-now branches add a second, smaller
risk worth noting. In `build_connection_plan`, the call to `_connection_clients`
sits outside the surrounding `try`, so if connection client wiring ever raised it
would also escape as a 500. In the current code `ConnectionClients.default`
degrades every unresolved adapter to a no-op and does not raise, so this is a
latent edge rather than the observed cause.

In production with a healthy Aurora and a session created first through
`api/explore/sessions`, this path returns 200 with the trip panels for a branch
turn. The 500 is an environment and error-mapping problem, not a planner-logic
bug.

## What this implies for Wave 2 and Wave 3

Wave 2 implementation is smaller than the STEP_LOG suggested, because the
allowed_panels half is already committed. The defensible minimal change set is to
harden `/plan` so a database connection or schema failure degrades to a clean 503
through the existing `_require_aurora` contract instead of an unhandled 500, and
to confirm the existing regression test stays green. No backend planner change is
required to surface trips.

Wave 3 deploy plan centers on a Vercel front-end deploy of HEAD so the inline
spec and the branch UI reach anonymous visitors, plus an operator confirmation
that production Aurora is reachable and migrated so `/plan` does not 500. Whether
HEAD is already deployed is an operator and O0 question I cannot answer from the
repo alone.

## Files read

- src/aws_backend/casting/planner.py
- src/aws_backend/casting/seeds/surface-planner-v1.json
- src/aws_backend/casting/registry.py
- src/aws_backend/casting/concierge.py
- src/aws_backend/casting/policy.py
- src/aws_backend/casting/manifest.py
- src/aws_backend/casting/skills.py
- src/aws_backend/casting/skills_manifest.json
- src/aws_backend/casting/trips/connections.py
- src/aws_backend/routers/interactions.py
- src/aws_backend/exploration/db.py
- src/aws_backend/exploration/session_store.py
- web/app/page.tsx
- web/app/components/AdaptiveExplore.tsx
- web/app/components/ActiveSurfaceHost.tsx
- web/lib/adaptiveConsole.ts
- web/app/api/interactions/plan/route.ts
- web/app/api/be/[...path]/route.ts
- tests/aws_backend/test_planner_trips_branch.py

## Confidence

The runtime allowed_panels source and the exclusion reason are read directly from
the code paths and are high confidence. The dev 500 root cause is inferred from
the handler control flow and the connection helper. I did not reproduce it,
because reproducing requires standing up the backend with a database, which is
out of scope for a read-only discovery wave. The strongest single piece of
evidence is the narrow except clause in `plan_cast_interaction` combined with the
config-only check in `aurora_configured`.
