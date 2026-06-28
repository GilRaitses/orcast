# WS-COLDSTART CS2 — Discovery map

Grounds the locked mitigation set (M2 + M3 + M4; M1 deferred) in files, owners,
and convergence points, and resolves the one design decision CS1 surfaced.

## Locked decisions (operator, 2026-06-28)

- Scope: **M3 + M4 (free code) + M2 `MinSize=2` (+~$10/mo)**. M1 keep-warm pinger deferred.
- CS4 forced-transition repro on the sole live backend: **authorized** (health-gated `start-deployment`, auto-rollback).

## Key design decision: do NOT repoint App Runner health to /ready

R2 proposed pointing App Runner's health check at a `/ready` gated on
`aurora_connected()`. **Rejected.** Coupling instance liveness to RDS would turn a
transient RDS blip into a total App Runner outage (all instances marked unhealthy
and replaced), which is strictly worse than today's behavior, where `/health`
stays 200 and explore degrades to a graceful 503. So:

- `/health` stays the App Runner health check (liveness only).
- `/ready` is added as an **observability** endpoint (reflects `aurora_connected`
  + pool warm); it is NOT wired to the App Runner health check.
- The cold-explore latency is removed by **pre-warming** (a lifespan-opened
  connection pool + a constructed Bedrock client), not by gating liveness.

## Convergence files + owners

| Mitigation | File(s) | Change |
|-----------|---------|--------|
| M4 (DONE) | `web/app/api/be/[...path]/route.ts` | bounded retry in `forward()`: 503 any-method, 502/504/404 GET-only, 1 retry, 300ms+jitter, body buffered so replay-safe |
| M4 (DONE) | `web/app/api/narrate-stream/route.ts` | one pre-body retry on 502/503/504 before any SSE bytes flow |
| M3 | `src/aws_backend/exploration/db.py` | module-level `psycopg_pool.ConnectionPool` (lazy open, bounded), `get_connection()` leases from it; keep per-call semantics for callers |
| M3 | `src/aws_backend/main.py` (lifespan 38-48) | best-effort pre-warm: open the pool + construct the Bedrock client; never crash the instance if RDS is briefly cold (log + continue) |
| M3 | `src/aws_backend/routers/read.py` | add `GET /ready` (observability: `aurora_connected()` + pool ready); leave `/health` unchanged |
| M3 | `src/aws_backend/routers/interactions.py` | catch DB-unreachable → 503 (parity with explore.py; today it 500s) |
| M3 | `requirements*.txt` | add `psycopg_pool` if not present |
| M2 | App Runner (AWS) | new dedicated `AutoScalingConfiguration` `MinSize=2` + associate to `orcast-aws-backend` (triggers a deployment = the CS4 transition) |
| M2 | `infra/aws/template.yaml` | mirror `MinSize=2` in IaC for parity |

## Why the combination covers the observed gap

- The confirmed symptom included `POST /api/explore/sessions` → 404 during a
  handover. M4 deliberately does NOT retry POST-404 (ambiguous, double-write
  risk). **M2 `MinSize=2`** removes the single-instance handover blackhole that
  produces that 404 (a second provisioned instance serves during the swap), so
  the handover-404 stops occurring at the source.
- M4 absorbs residual edge **503**s (and idempotent-GET 502/504/404) so they never
  reach a user.
- M3 removes the post-wake cold latency (pool + Bedrock pre-warm) and the
  interactions 500→503 parity gap, without coupling liveness to RDS.

## Test + acceptance approach

- M4: typecheck green (done). Validated under the CS4 forced transition by the
  external gap poller (R4 harness).
- M3: backend fixture tests for `/ready`, pool reuse, and interactions 503 parity;
  no live calls in CI.
- CS4: R4 gap metric `gap_while_health_up_ms` against the public URL during a
  `start-deployment` transition + concurrent load. Target = 0.

## Evidence-driven sequencing (revised after grounding the deploy risk)

M2 `MinSize=2` is **config-only** (a new AutoScalingConfiguration + associate); it
needs no new image. The backend-image M3 items (connection pool, `/ready`,
interactions 503 parity, lifespan pre-warm) all require building and deploying a
new image to the **sole live backend**, and the pool in particular introduces new
failure modes (PoolTimeout vs OperationalError breaks the existing 503 mapping)
that warrant isolated testing. R2 itself flagged the pool as secondary.

So the order is: ship M4 (done), apply M2 (config), then **measure** whether
M4 + M2 drive `gap_while_health_up_ms` to 0 (CS4). Only if measured residual
latency justifies it do we invest in the riskier backend-image M3 — and then as a
single fully-tested image deploy, not speculatively. This avoids a risky deploy to
the only prod backend without evidence it is needed.

## Status

CS2 discovery complete. CS3a (M4 proxy) implemented + typechecked + shipped.
CS3c (M2 MinSize=2) applied in CS4. Backend-image M3 (pool/`/ready`/503-parity/
pre-warm) **deferred pending CS4 evidence**. Next: CS4 (apply M2 + gap repro),
then a data-driven decision on backend-image M3, then CS5 acceptance.
