# R4: Repro + observability design (App Runner cold-start blip)

Lane: WS-COLDSTART / CS1 / R4 (generalPurpose, read-only).
Authored: 2026-06-28 ~14:14 ET (18:14 UTC).
Scope: READ-ONLY. No deploy, no config change, no recycle, no start/stop. All
commands below that mutate state are written as NOT-YET-RUN and explicitly gated.

Target service (verified live this lane):
- Name `orcast-aws-backend`, ServiceID `ed4d6e4999864a468e11349c3f1083d9`
- ARN `arn:aws:apprunner:us-west-2:198456344617:service/orcast-aws-backend/ed4d6e4999864a468e11349c3f1083d9`
- Region `us-west-2`, URL `https://pjrftm3bkv.us-west-2.awsapprunner.com`
- AutoScaling `DefaultConfiguration` rev 1 (MinSize 1 / MaxSize 25 / MaxConcurrency 100)
- Health `/health` HTTP, Interval 10s, Timeout 5s, Healthy 1, Unhealthy 5
- Instance 1024 CPU / 2048 MiB; `ObservabilityEnabled: false` (no X-Ray traces)

> NOTE on default CLI region: the operator profile defaults to `us-east-1`. Every
> command below pins `--region us-west-2`. Do not omit it or the calls return empty.

---

## 0. Headline finding (read this first)

The user-visible 404/503 is an **App Runner edge/router artifact during an instance
transition**, not an application response. Three independent reads prove it:

1. Instances are replaced roughly every ~30 minutes even at near-zero traffic. One
   replacement (`Started server process` on a new instance id `c9deca6a...`, source
   IP flips `169.254.172.3` -> `169.254.172.2`) lands at **17:39:49 UTC**, dead
   center of the reported blip window (17:35-17:45 UTC / 13:35-13:45 ET).
2. Over the last 24h the application log group has **zero** lines matching `404`,
   `503`, `Not Found`, or `Service Unavailable`. The app only ever logged 200s
   (plus one unrelated 405 from a GET on a POST-only route).
3. `5xxStatusResponses` is **0** across the window and `4xxStatusResponses` shows
   only the single 405 probe. App Runner's StatusCode metrics count app-served
   responses only, so an edge-generated 404/503 during handover is invisible to
   both the app logs and the 4xx/5xx metrics.

Implication for the harness (section 5): the gap CANNOT be measured from CloudWatch
metrics or app logs alone. It is only observable by an external client polling the
public URL through the transition. That is exactly what the harness does.

---

## 1. Observability map: AWS/AppRunner metrics for this service

Confirmed available via `list-metrics` (namespace `AWS/AppRunner`). Two dimension
shapes exist:

- Service level: dimensions `ServiceName` + `ServiceID`.
- Instance level: dimensions `ServiceName` + `ServiceID` + `Instance`.

| Metric | Dimensions present | Useful Stat | What it proves for cold-start |
|---|---|---|---|
| `ActiveInstances` | Service | Max / Average | Count of actively-allocated instances. Drops to 0 when the MinSize=1 instance is paused/idle; rises on wake. A 0->1 step marks a wake. |
| `Requests` | Service | Sum | Request volume; gives denominator and shows the burst that triggers a wake. |
| `2xxStatusResponses` | Service | Sum | App-served success count. |
| `4xxStatusResponses` | Service | Sum | App-served 4xx. NOTE: edge 404 during handover is NOT counted here. |
| `5xxStatusResponses` | Service | Sum | App-served 5xx. NOTE: edge 503 during handover is NOT counted here. |
| `RequestLatency` | Service | Maximum (p99 also) | Max latency spikes to ~4.7-5.5s on a cold wake; the clearest metric proxy for wake cost. |
| `Concurrency` | Service | Maximum | In-flight concurrency; near 0 here, so scaling is not the cause. |
| `CPUUtilization` | Service AND Instance | Max/Avg | Per-instance series begins/ends with the instance lifecycle. A new `Instance` dimension value appearing = a new instance born. |
| `MemoryUtilization` | Service AND Instance | Max/Avg | Same lifecycle signal as CPU; also relevant to the exit-code-137 (OOM) crash seen 2026-06-27 (section 3). |

There is no `3xx` metric and no separate edge/LB status metric. App Runner does not
emit a metric that distinguishes "edge returned 404/503 because no instance was
ready." That is the core observability gap.

### Confirming sample (read-only `get-metric-data`, 17:00-18:20 UTC)

Query file (`/tmp/r4_mq.json`) requested ActiveInstances(Max), Requests(Sum),
2xx/4xx/5xx(Sum), RequestLatency(Max), Concurrency(Max) at Period 60.

Command (re-runnable, read-only):

```bash
aws cloudwatch get-metric-data --region us-west-2 \
  --metric-data-queries file:///tmp/r4_mq.json \
  --start-time 2026-06-28T17:00:00Z --end-time 2026-06-28T18:20:00Z \
  --output json
```

Pasted result (trimmed to the transition window 17:29-18:00 UTC):

```
== ActiveInstances (Max) ==
  17:29  1.0     <- wake
  17:30-17:38  0.0
  17:39  1.0     <- wake (blip-window instance boot at 17:39:49)
  17:40  1.0
  17:41  1.0
  17:42-17:52  0.0
  17:53  1.0
  17:54  1.0
  17:57  1.0
  17:59  1.0
  18:00+  0.0
== Requests (Sum) ==  17:39:10  17:40:6  17:41:5  17:53:14  17:54:16  17:59:4
== 2xxStatusResponses (Sum) == 17:39:10 17:40:5 17:41:5 17:53:14 17:54:16 17:59:4
== 4xxStatusResponses (Sum) == 17:40:1   (this is the 405 GET /api/interactions/plan probe, not the blip)
== 5xxStatusResponses (Sum) == (none)
== RequestLatency (Max ms) == 17:29:4750  17:39:671  17:40:565  17:41:76  17:54:5550  17:59:5250
== Concurrency (Max) == ~0 throughout (one sample of 1.0 at 17:54)
```

Reading: ActiveInstances oscillates 0<->1 all hour; RequestLatency Max hits
4750-5550ms on the first request after idle (the cold wake); 5xx is empty and the
only 4xx is a benign 405. The metrics confirm a wake/transition pattern but, as
predicted, do NOT contain the 404/503 the user saw.

---

## 2. App Runner logs in CloudWatch Logs

Two log groups for this service (from `describe-log-groups`):

- Service events: `/aws/apprunner/orcast-aws-backend/ed4d6e4999864a468e11349c3f1083d9/service`
- Application stdout/stderr: `/aws/apprunner/orcast-aws-backend/ed4d6e4999864a468e11349c3f1083d9/application`

(There is also a stale prior service id `4350963f9e5848e1b5f5a29efbe958a0` with the
same two suffixes; ignore it, it is a previous service generation.)

### What lives where

- The **service** log group only records DEPLOY/UPDATE lifecycle lines
  (`Starting to deploy`, `Performing health check`, `Health check is successful.
  Routing traffic`, `Successfully deployed`, and crash lines like `Container exit
  code: 137`). It does NOT record organic instance recycles. A `filter-log-events`
  over 17:00-18:20 UTC returned `NUM 0`, confirming no deploy happened in the blip
  window.
- The **application** log group records uvicorn access lines and, crucially, the
  per-instance boot banner `INFO: Started server process [N]` /
  `Application startup complete`. Each fresh instance writes this once, in its own
  log stream `instance/<instanceId>`. This is the ONLY place an organic instance
  transition is visible as a discrete event.

### Filter for instance start (boots) around a time

```bash
# instance boots over the last 24h (proves recycle cadence)
aws logs filter-log-events --region us-west-2 \
  --log-group-name "/aws/apprunner/orcast-aws-backend/ed4d6e4999864a468e11349c3f1083d9/application" \
  --start-time $(python3 -c "import time;print(int((time.time()-86400)*1000))") \
  --filter-pattern '"Started server process"' --output json
```

### Filter for 404/503 around a time

```bash
# any app-level 404/503 in last 24h (came back EMPTY -> edge artifact)
aws logs filter-log-events --region us-west-2 \
  --log-group-name "/aws/apprunner/orcast-aws-backend/ed4d6e4999864a468e11349c3f1083d9/application" \
  --start-time $(python3 -c "import time;print(int((time.time()-86400)*1000))") \
  --filter-pattern '?" 404 " ?" 503 " ?"Service Unavailable" ?"Not Found"' --output json
```

### Lines found around the blip window (~17:35-17:45 UTC)

Old instance `fca1f30e...` (booted 17:06:20, source IP `169.254.172.3`) served
explore traffic cleanly right up to the cutover:

```
17:39:13.897  POST /api/explore/sessions HTTP/1.1" 200 OK     (IP .3)
17:39:14.281  POST /api/interactions/plan HTTP/1.1" 200 OK    (IP .3)
17:39:16.580  GET /health HTTP/1.1" 200 OK                    (IP .3)  <- last line on old instance
```

New instance `c9deca6a...` boots and takes over on IP `169.254.172.2`:

```
17:39:49.882  INFO: Started server process [7]                (instance c9deca6a, IP .2)
17:39:50.029  INFO: Application startup complete.
17:39:50.952  GET /health HTTP/1.1" 200 OK                    (IP .2)
17:40:37.991  GET /api/explore/status HTTP/1.1" 200 OK        (IP .2)
17:40:38.380  GET /api/interactions/plan HTTP/1.1" 405 Method Not Allowed  (GET on POST route; benign)
17:41:07.404  POST /api/explore/sessions HTTP/1.1" 200 OK     (IP .2)
```

There is a ~33s gap (17:39:16 last-old -> 17:39:49 first-new) where the instance is
being replaced. Every explore call captured BEFORE and AFTER returns 200; no 404 or
503 is present in the app log for `/api/explore/*`. The user-visible 404/503 fell in
that handover gap and was answered by the App Runner edge, not the app. This matches
the empty 24h 404/503 search and the empty 5xx metric.

### 24h recycle cadence (proof of constant churn)

`Started server process` banners, one per fresh instance, last 24h (30 boots):

```
2026-06-27T23:07:24  5c3006a0...
2026-06-27T23:35:56  0a9cb653...
2026-06-28T00:06:21  321c4367...
2026-06-28T04:01:04  26064eab...   (deploy 76b6d649)
2026-06-28T04:25:22  27e0f2a7...   (deploy 2c3ec5ab)
2026-06-28T04:38:44  08db4a35...
2026-06-28T05:06:42  b41d2145...
2026-06-28T05:36:50  c123ed59...
2026-06-28T08:38:33  a3228ea1...
2026-06-28T09:05:58  bcd55a6b...
2026-06-28T09:19:40  a392280d...
2026-06-28T09:36:08  41628dc6...
2026-06-28T10:08:09  a0277cdf...
2026-06-28T10:41:37  0a1b9fc8...   (deploy b4122c08)
2026-06-28T10:54:20  1f389395...
2026-06-28T11:05:59  6bf7a295...
2026-06-28T11:37:49  d20234f9...
2026-06-28T12:06:23  8aa38f0b...
2026-06-28T12:35:59  7ce9f874...
2026-06-28T13:05:39  2326a973...
2026-06-28T13:36:35  c2f5dc46...
2026-06-28T14:20:23  fd63448a...
2026-06-28T14:33:05  36e12a55...
2026-06-28T15:05:58  aa6188cc...
2026-06-28T15:36:04  d591ed10...
2026-06-28T16:06:40  204c1d36...
2026-06-28T16:36:12  f16f339b...
2026-06-28T17:06:20  fca1f30e...
2026-06-28T17:39:49  c9deca6a...   <- BLIP-WINDOW TRANSITION
2026-06-28T18:05:48  1f5b3fdb...
```

Cadence is ~25-35 min between organic boots (plus the deploy-triggered ones). The
service is effectively cold-starting a brand-new instance every half hour, each one
a candidate edge-blip window. Most boots correlate to nothing user-visible because
no user request happens to land in the ~30s handover, which is why the blip looked
rare and self-healing.

---

## 3. `list-operations` correlation

```bash
aws apprunner list-operations --region us-west-2 \
  --service-arn "arn:aws:apprunner:us-west-2:198456344617:service/orcast-aws-backend/ed4d6e4999864a468e11349c3f1083d9" \
  --max-results 20 --output json
```

Operations near 2026-06-28 (times shown -04:00 ET as returned):

```
UPDATE_SERVICE     SUCCEEDED            06:40:48 -> 06:43:33 ET   (b4122c08, image ws-stream-874f830)
START_DEPLOYMENT   SUCCEEDED            00:24:33 -> 00:27:48 ET   (2c3ec5ab)
START_DEPLOYMENT   SUCCEEDED            00:00:18 -> 00:03:37 ET   (76b6d649)
... (earlier ops on 06-23/06-25/06-26, several ROLLBACK_SUCCEEDED) ...
```

Correlation verdict: the most recent operation before the blip ended at **06:43 ET
(10:43 UTC)**, ~7 hours before the 13:39 ET (17:39 UTC) transition. **No deployment
or update operation occurred in or near the blip window.** Therefore the 17:39
instance replacement was an **organic recycle**, not an operator/deploy action.
`list-operations` does not list organic instance replacements at all, which is why
the application log boot banner (section 2) is the authoritative signal for them.

Side note: the service log group shows a prior crash `Container exit code: 137`
(OOM/SIGKILL) at 2026-06-27 23:07 UTC. Worth flagging to R2 (memory headroom on the
2048 MiB instance) but it is outside the blip window and not the blip cause.

---

## 4. SAFE repro design (DO NOT RUN IN RESEARCH; operator-gated wave only)

Goal: deterministically place an instance transition on the live sole-backend while
the harness (section 5) is recording, so we can measure the user-visible gap and
later prove it is zero after mitigation. All options below are WRITE operations and
MUST NOT run in CS1. They are specified for the later operator-gated adversarial wave
(CS4) only.

Ranked least-disruptive first:

### Option A (preferred): observe a natural recycle, trigger nothing
Section 2 proves an organic recycle happens every ~25-35 min on its own. The repro
can be purely passive: start the harness and wait <=35 min for the next
`Started server process` boot, which is the same transition class as the blip.
- Risk: lowest (zero mutation). Only cost is wall-clock wait.
- Rollback: none needed; nothing changed.
- Limitation: timing is not on-demand, so a timed wave must budget up to ~35 min.

### Option B: no-op redeploy via `start-deployment` (image unchanged)
`aws apprunner start-deployment` re-pulls the CURRENT image tag and rolls a new
instance with App Runner's normal health-gated rollover (provision -> health check
-> route -> drain old). This is the gentlest on-demand trigger because App Runner
keeps the old instance serving until the new one passes `/health`.
- NOT-YET-RUN (gated):
  ```bash
  # OPERATOR-GATED, CS4 ONLY. Re-deploys current image, forces a fresh instance.
  aws apprunner start-deployment --region us-west-2 \
    --service-arn "arn:aws:apprunner:us-west-2:198456344617:service/orcast-aws-backend/ed4d6e4999864a468e11349c3f1083d9"
  ```
- Risk: medium. It IS a production rollover on the sole backend. If the new image
  fails health (e.g. the exit-137 OOM recurs) App Runner auto-rolls-back to the last
  good revision, but there is a window of risk. AutoDeploymentsEnabled is false so
  this will not fire on its own.
- Rollback: App Runner auto-rollback on failed health; manually, redeploy the known
  good tag `ws-stream-874f830` (current running tag) the same way.

### Option C: `update-service` with a trivial change
Any `update-service` (even a no-semantic env reorder) forces a SERVICE_UPDATE
rollover. History shows several of these ended in `ROLLBACK_SUCCEEDED`, i.e. they
are riskier in practice than start-deployment here.
- Risk: highest of the three. More config surface to get wrong; observed rollbacks.
- Rollback: auto-rollback / re-apply prior config.
- Recommendation: do NOT use C for repro; B is strictly safer for the same effect.

Repro recommendation: rehearse with **A** (free, realistic), and only if on-demand
timing is required use **B** under operator gate with the harness already recording
and a human watching `describe-service` Status. Never use C for repro.

Hard guardrail restated: none of A/B/C run in CS1/research. They are written here as
specs for CS4 and require the operator gate "approve any later wave that forces a
deployment/instance recycle on the live sole-backend."

---

## 5. Measurement harness spec ("user-visible cold-start gap")

### Definition (pass/fail metric)
> user-visible gap = the maximum contiguous duration during which a REAL user call
> (`POST /api/explore/sessions` create, or `GET /api/explore/status`) returns a
> non-2xx response WHILE `GET /health` returns 2xx (or while `/health` is also
> failing, since the user still sees an outage).
>
> Target = 0 ms. Any window > 0 where a user call is non-2xx is a fail, regardless
> of whether CloudWatch recorded a 5xx (it will not; see sections 1-2).

The `/health`-up condition is what isolates the cold-start/edge blip from a real
total outage: if `/health` is up but `/api/explore/*` is down, that is the exact
failure class we are eliminating.

### Why an external poller (not metrics/logs)
Sections 1-3 prove the edge-generated 404/503 never reaches app logs or 4xx/5xx
metrics. The only way to see what a user sees is to BE the user: poll the public
URL `https://pjrftm3bkv.us-west-2.awsapprunner.com` from outside.

### Endpoints polled in parallel, fixed cadence 500 ms
1. `GET /health` (liveness reference line)
2. `GET /api/explore/status` (idempotent real user read)
3. `POST /api/explore/sessions` (real user write; idempotent-safe to create; the
   most representative of the FW-ACCEPT failure). Honor the rate limits in the live
   env: `ORCAST_EXPLORE_MAX_SESSIONS_PER_IP_DAY=20`. At 500ms cadence a session
   create every tick would blow the cap in 10s, so the harness creates a session
   only every Nth tick (or uses a partner/exempt key) and uses `GET status` as the
   high-frequency real-call probe between creates. Decision: status at 500ms every
   tick; session-create at a slower 5s cadence, both counted as "real user calls."

### Recording / metric computation
- Each probe records: `t_send`, `t_recv`, endpoint, HTTP status, latency, error.
- Maintain three timelines (health, status, sessions). Mark each sample 2xx or not.
- Compute, per endpoint and combined-real (status OR sessions):
  - `gap_ms` = longest run of consecutive non-2xx real-call samples.
  - `gap_while_health_up_ms` = longest run of non-2xx real-call samples whose
    nearest `/health` sample within the tick was 2xx. THIS is the headline number.
  - first-bad timestamp, last-bad timestamp, count of failed real calls, the status
    codes seen (expect 404 and/or 503 from the edge).
- Cross-reference (post-run, read-only) the failed-call timestamps against the app
  log `Started server process` banner and the `RequestLatency` Max spike to confirm
  each gap aligns to a transition.

### Pseudocode
```
endpoints = {
  health:   ("GET",  BASE+"/health",               cadence=500ms),
  status:   ("GET",  BASE+"/api/explore/status",   cadence=500ms),
  sessions: ("POST", BASE+"/api/explore/sessions", cadence=5000ms, body=minimal_valid),
}
results = []  # (ts, name, status, latency_ms, ok)
run for DURATION (>= repro window + margin; for Option A budget ~40 min):
  for each endpoint due this tick:
    spawn async: t0=now; r = request(method,url,timeout=10s, headers=api_key)
                 results.append((t0, name, r.status, now-t0, 200<=r.status<300))
  sleep to next 500ms boundary
# analysis
align samples into 500ms buckets by timestamp
health_ok(bucket) = last health sample in/near bucket is 2xx
real_ok(bucket)   = status sample 2xx (and, if a session fired, it is 2xx too)
gap_while_health_up = max contiguous span where (not real_ok) and health_ok
report: gap_while_health_up_ms (TARGET 0), failed statuses, transition correlation
```

### Operational guardrails for the harness itself
- Read/PII: session create writes a real row; honor retention
  (`ORCAST_EXPLORE_RETENTION_DAYS=30`) and the per-IP/day cap. Prefer a dedicated
  test/partner key so harness traffic is attributable and exempt from the 20/day cap
  rather than exhausting a real user IP budget.
- The harness is pure client traffic over HTTPS; it changes NO infrastructure and is
  itself safe to run in research IF pointed at the live URL with a test key. But the
  THING it measures (a transition) must be produced by Option A/B, which are gated.
  So the full repro+measure loop runs only in CS4.
- CORS is irrelevant (server-to-server), but send `Origin` matching an allowed
  origin if any middleware enforces it; allowed origins include `https://orcast.org`.

### Acceptance wiring (for CS4/CS5)
- Baseline run (pre-mitigation) is expected to capture at least one
  `gap_while_health_up_ms > 0` aligned to a `Started server process` boot.
- Post-mitigation run must show `gap_while_health_up_ms == 0` across N>=3 forced or
  observed transitions AND a concurrent-load variant, AND must show the mitigation
  (e.g. a bounded idempotent retry) did not mask a genuine outage (inject a real
  hard-down and confirm the harness still reports a non-zero gap).

---

## Appendix: exact read-only commands used this lane

```bash
REG=us-west-2
ARN="arn:aws:apprunner:us-west-2:198456344617:service/orcast-aws-backend/ed4d6e4999864a468e11349c3f1083d9"
SID=ed4d6e4999864a468e11349c3f1083d9
APP="/aws/apprunner/orcast-aws-backend/$SID/application"
SVC="/aws/apprunner/orcast-aws-backend/$SID/service"

aws apprunner describe-service --region $REG --service-arn "$ARN"
aws apprunner list-operations  --region $REG --service-arn "$ARN" --max-results 20
aws cloudwatch list-metrics    --region $REG --namespace AWS/AppRunner
aws cloudwatch get-metric-data --region $REG --metric-data-queries file:///tmp/r4_mq.json \
  --start-time 2026-06-28T17:00:00Z --end-time 2026-06-28T18:20:00Z
aws logs describe-log-groups   --region $REG --log-group-name-prefix "/aws/apprunner/orcast-aws-backend"
aws logs filter-log-events     --region $REG --log-group-name "$SVC" --start-time <ms> --end-time <ms>
aws logs filter-log-events     --region $REG --log-group-name "$APP" --start-time <ms> \
  --filter-pattern '"Started server process"'
aws logs filter-log-events     --region $REG --log-group-name "$APP" --start-time <ms> \
  --filter-pattern '?" 404 " ?" 503 " ?"Service Unavailable" ?"Not Found"'
```

All of the above are `describe/list/get/filter` reads. No mutation was performed.
