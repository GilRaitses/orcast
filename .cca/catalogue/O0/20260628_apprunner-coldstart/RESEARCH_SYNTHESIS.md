# WS-COLDSTART CS1 — Research synthesis

Synthesized from four parallel read-only lanes (no infra changed):
- R1 App Runner mechanics — `research/R1_apprunner_mechanics.md` (agent `92d3c634`)
- R2 app startup/readiness — `research/R2_app_startup.md` (agent `6ff02d7c`)
- R3 edge/client resilience — `research/R3_edge_client_resilience.md` (agent `a997c68c`)
- R4 repro + observability — `research/R4_repro_observability.md` (agent `a105d73b`)

## 1. Verdict: root cause (ranked by evidence)

**H1 — App Runner edge artifact during instance handover (CONFIRMED, primary).**
R4's live evidence is decisive: a fresh instance booted at **17:39:49 UTC**, dead
center of the FW-ACCEPT blip window (17:35-17:45 UTC), with a **~33s handover gap**
between the last request on the old instance and the first on the new one. The
application logs show **zero** 404/503 over 24h and `5xxStatusResponses` is empty,
so the user-seen 404/503 was generated at the **App Runner routing/edge layer
during the blue/green handover** and never reached the FastAPI app. `/health`
stayed 200 because it is liveness-only and was still answered through the
transition. This is not conditional router mounting (routers mount
unconditionally, `main.py:82,84`) and not app logic.

**H2 — Idle ramp-down to provisioned (CONFIRMED, contributing).** R1's CloudWatch
trace shows `ActiveInstances=0` for most of 24h despite the 10s `/health` check:
the single `MinSize=1` instance CPU-throttles to the "provisioned" state after
~60s idle, and instances recycle every ~25-35 min (30 boots/24h). After idle, the
first traffic saw a 5xx burst then 2xx with multi-second (5-11.5s) cold app
latency. So there are really two gaps: the **edge-handover 404/503** (H1) and the
**post-wake app cold latency** (H2 + R2).

**H3 — Instance healthy but explore cold (CONFIRMED, distinct path).** R2: a fresh
instance can pass `/health` (no Aurora probe) while explore returns 503 (lazy
per-request `psycopg.connect`, no pool, 5s timeout) or 500 (interactions does not
catch DB-unreachable) or 404 ("Session not found" after a failed create in the
503 window). This is a separate, real failure path that `/ready` + pre-warm fix.

## 2. Per-layer findings

### App Runner (R1)
- MinSize 1 / MaxSize 25 / MaxConcurrency 100, `DefaultConfiguration`; health `/health` 10s; 1vCPU/2GB.
- The 10s `/health` check does NOT keep the instance "hot"; idle instances throttle.
- `MinSize>1` adds AZ spread + a ready second provisioned instance (removes the single-instance blackhole during handover) but does NOT pin instances hot.
- Most direct removal of the idle-wake gap: an external keep-warm pinger to a real route every 30-50s, ideally with `MinSize=2`.
- Cost (us-west-2, 1vCPU/2GB): `MinSize=2` idle baseline ~$20.44/mo (+$10.22 over MinSize=1); one genuinely-active instance 24/7 (keep-warm) ~$56.94/mo (+~$47); the pinger itself is cents/mo.

### App (R2)
- `/health` is liveness-only (DynamoDB scans + in-memory status), never probes Aurora → stays 200 while explore is down.
- Aurora is lazy per request, no pool; Bedrock client created per invoke; migrations run in lifespan with swallowed errors (`main.py:46-47`).
- Highest-leverage app change: add `/ready` gated on `aurora_connected()`, lifespan pre-warm (open pool + construct Bedrock client), switch App Runner health path to `/ready`, and replace per-request connects with a `psycopg_pool.ConnectionPool`.

### Edge / client (R3)
- No upstream retry in either Vercel proxy today; only the client SSE stall→JSON-narrate fallback.
- Safest fix: bounded server-side retry in `/api/be` `forward()` (1 retry, 300ms+jitter, on 502/503/504 + fetch errors; 404 only for idempotent GET allowlist) + one pre-body retry in `narrate-stream`.
- Never retry mutating POSTs after headers; guard double-writes (session create, narrate persist) with retry-before-first-byte only.

## 3. Candidate mitigation set (what each lever closes)

| # | Lever | Closes | Cost | Owner layer |
|---|-------|--------|------|-------------|
| M1 | Keep-warm pinger to a real route every 30-50s (EventBridge Scheduler → ping) | H2 idle ramp-down + recycle-to-cold (keeps an instance active) | ~cents/mo pinger; instance active carry ~+$47/mo OR accept provisioned | infra/ops |
| M2 | Dedicated AutoScalingConfiguration `MinSize=2` | H1 single-instance handover blackhole + AZ spread | +~$10.22/mo | App Runner config |
| M3 | `/ready` gated on `aurora_connected()` + lifespan pre-warm + connection pool; point App Runner health at `/ready` | H3 healthy-but-explore-cold (503/500/404-after-failed-create) + H2 app cold latency | $0 | app code + `template.yaml` |
| M4 | Bounded idempotent absorb-the-blip retry in `/api/be` + pre-body in `narrate-stream` | H1 makes the ~33s edge-handover window invisible for idempotent reads/creates | $0 | Vercel proxy |

**Reading:** M4 is the only lever that directly hides the confirmed edge-handover
404/503 (H1) from users, and it is free. M1+M2 reduce how often a handover/cold
state occurs. M3 fixes the distinct cold-explore path (H3) and the post-wake
latency. The robust answer is the combination, not any single knob; "instant" is
not literally achievable, but "zero user-visible gap" is.

## 4. What only the CS4 repro can confirm (operator-gated)

1. Whether the deploy/handover 404 is App Runner-edge vs app on a transitioning instance (R1+R4 both say edge, but a synchronized poll + app-log correlation during a forced transition proves it).
2. Whether the ~8-9 min idle-wake 5xx (R1) is health-driven replacement vs DB-over-VPC readiness delay.
3. Whether M1+M2+M3+M4 together actually drive `gap_while_health_up_ms` to 0 under a forced recycle + concurrent load.

Gap metric (R4): `gap_while_health_up_ms` = max contiguous duration where a real
user call (`POST /api/explore/sessions` or `GET /api/explore/status`) returns
non-2xx while `GET /health` returns 2xx, measured by an external 500ms poller
(sessions throttled to 5s for the 20/IP/day cap). Target = 0. Metrics/logs cannot
measure it; only an external client can.

## 5. Recommended downstream wave shape

- **CS2 Discovery:** ground M1-M4 in files/owners/knobs; name convergence files (`web/app/api/be/[...path]/route.ts`, `web/app/api/narrate-stream/route.ts`, `src/aws_backend/main.py`, `src/aws_backend/routers/read.py`, `src/aws_backend/exploration/db.py`, `infra/aws/template.yaml`); finalize the keep-warm mechanism + the cost decision.
- **CS3 Implementation:** M3 (readiness + pre-warm + pool) and M4 (bounded retry) are code-only and low-risk; M2 (MinSize=2) and M1 (pinger) are config/infra. Sequence code first (testable offline), config behind the operator cost gate.
- **CS4 Adversarial (operator-gated):** force a transition (R4 Option B `start-deployment`, health-gated, auto-rollback) under the external gap poller + concurrent load; prove `gap_while_health_up_ms = 0`; prove the retry does not mask a sustained outage; confirm the cost delta.
- **CS5 Acceptance:** measured zero user-visible gap recorded; commit/push.

## 6. Open operator gates

1. Approve any CS4 action that forces a deployment/instance recycle on the sole live backend (R4 Option B/C).
2. Confirm or override the warm-pool cost ceiling: `MinSize=2` (+~$10/mo) and/or a kept-active instance (~+$47/mo) vs accepting that M3+M4 alone (free) absorb most of the gap.

## 7. Gate verdict

CS1 PASS: every lane named the mechanism + the specific knob/code/retry at its
layer; R1 priced each knob; R2 ruled that `/health` must not be the readiness gate
and specified `/ready` + pre-warm; R3 specified the exact safe retry policy and
double-write guards; R4 delivered a safe repro + a measurable gap metric and found
the transition inside the blip window. Root cause is confirmed (edge handover,
H1) with two contributing paths (H2 idle ramp-down, H3 cold-explore). Proceed to
CS2 discovery.
