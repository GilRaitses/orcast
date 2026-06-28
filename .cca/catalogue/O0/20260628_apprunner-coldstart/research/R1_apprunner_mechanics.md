# R1: App Runner Cold-Start / Instance-Recycle Mechanics

Research lane R1 of WS-COLDSTART. Goal: ground the mechanics of AWS App Runner
cold-start, pause/throttle, and instance-transition behavior so we can drive the
user-visible cold-start gap on `orcast-aws-backend` toward zero.

Mode: READ-ONLY. No infrastructure was changed. Only `describe-*` / `list-*` /
`get-metric-statistics` calls and documentation/web research were used.

- Region: us-west-2
- Service: `orcast-aws-backend`
- Service ARN: `arn:aws:apprunner:us-west-2:198456344617:service/orcast-aws-backend/ed4d6e4999864a468e11349c3f1083d9`
- Public URL: https://pjrftm3bkv.us-west-2.awsapprunner.com
- Date of investigation: 2026-06-28

## Tooling note

The two AWS plugin MCP servers requested for this lane
(`plugin-deploy-on-aws-awsknowledge`, `plugin-deploy-on-aws-awspricing`) were in an
errored state at investigation time (their `STATUS.md` reported "The MCP server
errored"; a probe call returned "MCP server does not exist"). Documentation and
pricing grounding below therefore comes from the official AWS docs and pricing
pages via web research, cross-checked against live AWS CLI output. If exact,
account-scoped pricing is required, re-run with those MCP servers healthy.

---

## 0. Live configuration (verified)

`aws apprunner describe-service` confirmed:

- Instance: `Cpu=1024` (1 vCPU), `Memory=2048` (2 GB).
- AutoScaling: `DefaultConfiguration` rev 1, `MinSize=1`, `MaxSize=25`, `MaxConcurrency=100`, `IsDefault=true`.
- Health check: HTTP `/health`, `Interval=10s`, `Timeout=5s`, `HealthyThreshold=1`, `UnhealthyThreshold=5`.
- Egress: VPC connector `orcast-aws-backend-explore-vpc` (the app reaches RDS Postgres `orcast-aws-backend-explore...rds.amazonaws.com` over the VPC). This matters: a freshly woken instance must (re)establish DB connectivity over the VPC connector before it can serve `/api/explore/*`.
- `AutoDeploymentsEnabled=false` (deploys are manual / `StartDeployment` driven).
- Status `RUNNING`.

(Env vars in the describe output include secrets; intentionally not reproduced here.)

`list-operations` shows frequent `UPDATE_SERVICE` / `START_DEPLOYMENT` activity,
including several `ROLLBACK_SUCCEEDED` rows on 2026-06-23 and 2026-06-25, and a
successful `UPDATE_SERVICE` on 2026-06-28 06:40:48 to 06:43:33 EDT (10:40 to 10:43
UTC). Each deploy/update takes roughly 3 minutes.

---

## 0b. Live CloudWatch evidence (the smoking gun)

Namespace `AWS/AppRunner`, service-level dimensions
(`ServiceName=orcast-aws-backend`, `ServiceID=ed4d6e49...`).

### ActiveInstances is 0 for long stretches

Over a 24h window (2026-06-27 18:00 to 2026-06-28 18:10 UTC, 5-min Max),
`ActiveInstances` is `0` almost continuously, with brief `1` spikes roughly every
30 minutes. The instance is therefore in the throttled "provisioned" state most of
the time, not actively serving. This is despite the 10-second `/health` check
running continuously, which establishes that health checks do NOT keep the
instance in the active (CPU-on) state.

### The blip: idle wake transition with sustained 5xx then cold latency

1-minute resolution around the failure window (UTC):

| Minute | ActiveInstances(max) | Requests | 2xx | 5xx | Latency max (ms) |
|---|---|---|---|---|---|
| 13:35-13:45 | 0 | 0 | 0 | 0 | (idle) |
| 13:46 | 1 | 2 | 0 | 2 | 225 |
| 13:47 | 1 | 1 | 0 | 1 | 29.5 |
| 13:48 | 1 | 3 | 0 | 3 | 126 |
| 13:49-13:50 | 0 | 0 | 0 | 0 | - |
| 13:51 | 1 | 2 | 0 | 2 | 385 |
| 13:53 | 1 | 1 | 0 | 1 | 29.5 |
| 13:54 | 1 | 2 | 0 | 2 | 275 |
| 13:55-13:58 | 0 | 0 | 0 | 0 | - |
| 13:59 | 1 | 4 | 4 | 0 | 4950 |
| 14:01 | 1 | 1 | 1 | 0 | 37.5 |
| 14:03 | 1 | 3 | 3 | 0 | 11500 |
| 14:04 | 1 | 6 | 6 | 0 | 6450 |

Reading: after a long idle period (`ActiveInstances=0`), the first requests at
13:46 hit a transitioning instance and returned 5xx fast (sub-400ms). Every
request from 13:46 to 13:54 was 5xx (zero 2xx) while `ActiveInstances` flapped
1/0/1. Once the instance stabilized (13:59 onward) requests succeeded (2xx) but
with multi-second cold latency (4.95s, 11.5s, 6.45s) consistent with application
warmup (lazy imports, DB pool establishment over the VPC connector, first-hit
caches). The fast-5xx-then-slow-2xx signature is the classic "no healthy instance
yet, then cold instance" shape.

### The deploy-window 4xx

| Minute (UTC) | ActiveInstances | Requests | 2xx | 4xx |
|---|---|---|---|---|
| 10:40-10:42 | 0 | 0 | 0 | 0 |
| 10:43 | 1 | 3 | 1 | 2 |

The only 4xx of the day (2 responses) landed at 10:43 UTC, inside the
06:40-06:43 EDT `UPDATE_SERVICE` rollover window, alongside 1 successful 2xx. This
is a separate signal from the idle-wake 5xx burst and is consistent with a
brief blue/green traffic-shift artifact during deployment rollover. Sample size is
tiny (2 responses); whether the 404 originated at the App Runner edge or from the
app on a transitioning instance cannot be proven from metrics alone (see Q2 and
the R4 dependency).

---

## 1. Provisioned vs active instances, pause/wake/recycle

### The two states

App Runner instances exist in two billed states:

- Provisioned (idle): the container is kept resident in memory but CPU-throttled to near zero. AWS describes this as "a CPU-throttled instance ready to serve incoming requests within milliseconds." You pay for memory only.
- Active: the container is processing requests with full CPU. You pay vCPU + memory.

Sources:
- AWS App Runner FAQs: "If your application receives no incoming requests, App Runner will scale the containers down to a provisioned instance, a CPU-throttled instance ready to serve incoming requests within milliseconds." (https://aws.amazon.com/apprunner/faqs/)
- AWS App Runner Pricing: "When your application is idle, you pay per GB of memory for provisioned container instances which keep your application warm and eliminate cold starts. When requests come in, your application responds in milliseconds." (https://aws.amazon.com/apprunner/pricing/)
- AutoScalingConfiguration API ref: "The service always has at least `MinSize` provisioned instances. Some of them actively serve traffic. The rest of them (provisioned and inactive instances) are a cost-effective compute capacity reserve and are ready to be quickly activated. You pay for memory usage of all the provisioned instances. You pay for CPU usage of only the active subset." (https://docs.aws.amazon.com/apprunner/latest/api/API_AutoScalingConfiguration.html)
- App Runner roadmap issue #9 (AWS staff comments): the active-to-provisioned ramp-down window is about 60 seconds of no traffic, after which `ActiveInstances` drops to 0 and you pay memory only. (https://github.com/aws/apprunner-roadmap/issues/9)

When is an instance paused vs woken vs recycled:
- Paused (throttled to provisioned): after roughly 60s with no in-flight requests, the active instance ramps down to provisioned/throttled. Confirmed live: `ActiveInstances=0` dominates the 24h trace.
- Woken (provisioned to active): on the next incoming request, App Runner activates a provisioned instance. AWS claims millisecond activation. Our trace shows activation does occur, but the user-visible recovery in the observed blip took minutes, not milliseconds, which points beyond a pure platform wake (app readiness and/or instance replacement are implicated).
- Recycled / replaced: App Runner replaces instances on deployments and on health failures (`UnhealthyThreshold=5` consecutive failed `/health` checks at 10s interval = roughly 50s to mark unhealthy and replace). It also replaces instances for routine platform maintenance/host rotation.

### (a) Deployment rollover lifecycle

- App Runner uses an internal blue/green style rollover. The API docs state: "App Runner temporarily doubles the number of provisioned instances during deployments, to maintain the same capacity for both old and new code." (https://docs.aws.amazon.com/apprunner/latest/api/API_AutoScalingConfiguration.html)
- New instances are started, must pass the `/health` check, then traffic is shifted; old instances are then drained and terminated.
- In-flight requests: requests on old instances during drain can be cut off if the app does not handle SIGTERM gracefully, producing 5xx. (AWS re:Post: "App Runner continues to route traffic to the old instances for a few seconds after the deployment has completed, which results in 503 errors." https://repost.aws/questions/QUHmhjksDVQjOkVqVbkBVYZA/app-runner-503-http-errors-during-deployments)
- Brand-new requests: during the traffic-shift window a request can briefly hit an instance that is starting/draining, yielding transient 5xx (and, per our 10:43 observation, possibly 4xx).
- Failed rollovers roll back (the multiple `ROLLBACK_SUCCEEDED` operations in this service's history; re:Post documents "Failed to route incoming traffic to application" during the routing step: https://repost.aws/questions/QU0_0hYInxTt6jQ3_wQiQRrw/...).

### (b) Routine / health-driven replacement

- A health-driven replacement triggers after `UnhealthyThreshold` (5) consecutive failed `/health` checks. App Runner provisions a replacement, waits for `HealthyThreshold` (1) success, then routes to it.
- In-flight requests on a failing instance fail. Brand-new requests during the gap get 5xx (no healthy instance) until the replacement passes health.
- With `MinSize=1` and a single AZ-resident instance, a replacement event has no warm sibling to absorb traffic, so the gap is fully user-visible. This is the structural weakness of `MinSize=1`.

---

## 2. Can App Runner return 404 (not just 503) from its own routing layer?

- App Runner's own ingress/router returns 5xx (commonly 503) when there is no healthy instance to route to, during capacity or traffic-routing transitions. This is well documented for deployments (re:Post 503 thread above) and is the expected "no healthy target" behavior of a managed load balancer.
- 404 is almost always application-level: FastAPI returns 404 when no route matches. Because this app mounts the explore and interactions routers unconditionally at import time, a 404 on `/api/explore/*` would normally mean either (i) the request reached an app process whose router table was not yet fully constructed/ready, or (ii) the request reached a different/older image during a rollover whose path set differed, or (iii) a genuine path/client mismatch.
- App Runner edge vs application distinction:
  - App Runner edge (no healthy instance, routing failure): typically 503, sometimes other 5xx; fast responses; correlated with `ActiveInstances` transitions and deploy operations; not present in app logs because the request never reached the app.
  - Application 404/503: emitted by FastAPI/uvicorn; appears in app logs; 404 means route table miss; app 503 means the app deliberately returned it (for example a readiness guard) or uvicorn rejected during startup.
- What status when no healthy instance is available: 503 (Service Unavailable). This is the documented and expected App Runner behavior.

Net for the observed blip: the 5xx burst (13:46-13:54) is consistent with App
Runner-edge 503 (no healthy instance during a wake/transition). The deploy-window
404 (10:43) is more likely application-level on a transitioning instance or a
client mismatch; metrics cannot disambiguate edge-404 vs app-404. R4 repro with
synchronized App Runner access logs plus application logs is required to settle
this. There is no AWS documentation asserting that the App Runner edge emits 404
for "no healthy instance"; the documented edge failure code is 503.

---

## 3. MinSize / warm-pool semantics

- `MinSize=1` on `DefaultConfiguration` keeps exactly one provisioned instance. Provisioned does NOT mean active: when idle it is CPU-throttled (confirmed: `ActiveInstances=0` for most of the 24h trace). It is "warm" only in the sense that memory is resident; CPU must spin back up on the next request.
- The 10-second `/health` check does NOT keep the instance active. Live evidence: health checks run every 10s yet `ActiveInstances` sits at 0. Health checks are liveness probes, not billable request traffic, and do not reset the active ramp-down.
- App Runner does NOT scale to zero. The floor is `MinSize=1` (one provisioned, memory-billed instance). The only way to reach zero compute+memory is the manual `PauseService` action, which takes the service offline. (Roadmap issue #9; pricing page.)
- Would `MinSize>1` keep N instances actually warm and eliminate the wake gap? Partially, and not in the way one might hope:
  - `MinSize=N` provisions N instances and spreads them across more Availability Zones (API ref: "A higher `MinSize` increases the spread of your App Runner service over more Availability Zones"). This gives redundancy: a single instance replacement or AZ blip no longer blackholes the whole service.
  - BUT idle instances in the `MinSize` pool are still CPU-throttled to provisioned state when there is no traffic. `MinSize>1` does not pin them to active. So the fundamental provisioned-to-active wake still exists; AWS just claims it is a millisecond activation, and with N>1 there is more provisioned reserve ready to activate.
  - Therefore `MinSize>1` reduces the blast radius of single-instance transitions and improves availability, but does not by itself convert the pool into always-hot (CPU-on) instances. To keep an instance genuinely active (never throttled), you need continuous request traffic more often than the roughly 60s ramp-down window. That is an app/client-level keep-warm concern, not a `MinSize` knob.

---

## 4. Every knob that reduces cold-start / transition gaps, with tradeoff and cost

Pricing basis (us-west-2 Oregon; AWS App Runner pricing page lists the same
$0.064/vCPU-hour and $0.007/GB-hour for US East N. Virginia, US East Ohio, US West
Oregon, and Europe Ireland):

- Active instance: vCPU $0.064/vCPU-hr + memory $0.007/GB-hr.
- Provisioned (idle) instance: memory only $0.007/GB-hr, no vCPU charge.

For this service (1 vCPU, 2 GB):
- Provisioned (idle) per instance: 2 GB x $0.007 = $0.014/hr -> approx $10.22/mo (730 hr).
- Active per instance: $0.064 + (2 x $0.007) = $0.078/hr -> approx $56.94/mo if active 24/7.

Note on a pricing discrepancy: one third-party blog (techoral) claims a separate
"provisioned vCPU" rate at 10% of active. The authoritative AWS pricing page and
FAQ do not list a provisioned vCPU charge; provisioned instances are billed memory
only. This doc uses the AWS-official model (provisioned = memory only).

| Knob | Effect on cold-start / transition gap | Tradeoff | Cost impact (1 vCPU / 2 GB) |
|---|---|---|---|
| `MinSize` 1 -> 2 (dedicated AutoScalingConfiguration) | Adds a second provisioned instance and AZ spread; a single instance replacement/AZ blip no longer blackholes the service. Does not pin instances to active. | Idle instances still throttle; does not remove the app-level wake latency. | +1 provisioned instance idle baseline: +$0.014/hr = +$10.22/mo over MinSize=1. (Active hours add $0.064/hr each only while serving.) |
| Keep-warm synthetic traffic (external pinger to an app route every ~30-50s) | Most direct way to keep `ActiveInstances>=1` so the instance never ramps down to throttled; eliminates the idle-wake gap for steady-state traffic. The 10s `/health` does not achieve this; the ping must hit a real request path. | App stays active 24/7 (you pay vCPU continuously); does not help during deploy rollover or a genuine replacement. | One instance active 24/7 approx $56.94/mo (i.e. +$46.72/mo over the $10.22 idle baseline). Pinger itself (EventBridge Scheduler + tiny Lambda) is cents/mo. |
| `MaxConcurrency` (currently 100) | Lowering scales out to more instances sooner under load (helps avoid queuing on one slow/cold instance). Not a fix for the idle single-instance wake. | Too low -> more instances and cost; too high -> requests queue on a cold instance, worsening tail latency. | Indirect: changes how many active instances run under load (each active instance $0.078/hr). |
| Health-check tuning (interval/timeout/thresholds) | Raising `HealthyThreshold` and/or interval during deploys gives new instances more time to fully warm before traffic shifts, reducing premature-routing 5xx. Current `HealthyThreshold=1` shifts traffic after a single success, which can route to a not-fully-warm app. | Higher `HealthyThreshold`/interval slows detection of genuinely unhealthy instances (slower replacement). Lower `UnhealthyThreshold` replaces faster but risks flapping. | No direct AWS charge. |
| Instance size (1 vCPU/2 GB -> larger) | More CPU during the startup burst shortens app cold-init (imports, DB pool, first-hit work), shrinking the multi-second post-wake latency we observed. | Higher active and provisioned cost; over-provisioning wastes spend at idle. | 2 vCPU/4 GB active = $0.156/hr (approx $114/mo if active 24/7); provisioned idle for 4 GB = $0.028/hr (approx $20.44/mo). |
| Deployment cadence / settings (already manual) | Fewer deploys = fewer rollover blips. Each `UPDATE_SERVICE`/`START_DEPLOYMENT` triggers a traffic shift that can emit transient 5xx/4xx. | Slower release velocity. | None directly (manual deploys are free; auto-deploy from source is $1/app/mo, not applicable to ECR manual flow here). |
| Application graceful shutdown (SIGTERM draining) | Reduces in-flight 5xx during instance drain on deploy/replacement. | App-level work, not an App Runner knob. | None. |
| `PauseService` | Opposite direction (maximizes cold-start; full outage on resume). Listed for completeness only. | Service offline. | $0 while paused. |

### MinSize=2 warm pool vs MinSize=1, priced

- MinSize=1, fully idle: approx $10.22/mo (1 provisioned x 2 GB memory). Plus active vCPU only while serving.
- MinSize=2, fully idle (both throttled): approx $20.44/mo. Incremental vs MinSize=1: +$10.22/mo. This buys AZ spread and a ready second provisioned instance, but both still throttle when idle.
- Truly-warm (active, CPU-on) is traffic-driven, not a MinSize setting. Keeping one instance active 24/7 is approx $56.94/mo; two active 24/7 is approx $113.88/mo.
- During any deployment, App Runner temporarily doubles provisioned instances (extra memory cost for the roughly 3-minute deploy window; negligible, on the order of cents per deploy).

---

## 5. Recommendation

Which knob most directly removes the observed gap:

1. The idle-wake 5xx burst (the dominant blip) is removed most directly by preventing the single instance from ramping down to throttled. The highest-leverage lever is an external keep-warm pinger hitting a real, cheap application route (not `/health`, which does not keep it active) every 30-50s. This keeps `ActiveInstances>=1` and removes the provisioned-to-active wake for steady-state traffic. Cost: approx +$47/mo (one instance active around the clock) plus cents for the scheduler.

2. Move off `DefaultConfiguration` to a dedicated AutoScalingConfiguration with `MinSize=2` for redundancy and AZ spread, so a single instance replacement or AZ event no longer blackholes the service. Cost: approx +$10.22/mo idle baseline. This reduces, but does not alone eliminate, transition gaps (idle instances still throttle).

3. Tune the deploy path: raise `HealthyThreshold` above 1 (and consider a slightly longer interval) so traffic shifts only after the new instance is demonstrably warm, and add application SIGTERM graceful shutdown so draining old instances stop accepting new requests cleanly. This targets the deploy-rollover 5xx/4xx specifically.

4. Consider a modest instance-size bump (or app-level lazy-init/pre-warm of the DB pool) to shrink the multi-second post-wake latency (we observed 5-11.5s 2xx latencies right after wake), which is application cold-init, not platform wake.

Residual gap that only app/client-level mitigation can close:

- Deployment rollovers and genuine instance replacements will still produce brief windows where a request can hit a starting/draining instance. App Runner's blue/green shift is not provably zero-downtime; re:Post reports persistent transient 503s during deploys even with graceful shutdown. Closing this fully requires client-side retry/backoff on 503 (and on the transition 404), plus app-side readiness gating and SIGTERM draining.
- The first request after any cold instance still pays application warmup latency (DB connect over the VPC connector, imports, caches). Only app-level pre-warming and a keep-warm cadence reduce this; the platform wake itself is sub-second per AWS but the app's cold path is multi-second here.

### Uncertainty requiring R4 repro to confirm

- Whether the deploy-window 404 originated at the App Runner edge or from the FastAPI app on a transitioning/older instance. Metrics cannot disambiguate; R4 must capture synchronized App Runner access logs and application logs during a controlled transition.
- Why the idle-wake 5xx persisted for roughly 8-9 minutes (13:46-13:54) rather than the sub-second wake AWS advertises. This is longer than a normal activation and suggests either a health-driven replacement in progress or the app failing readiness on the woken instance (for example DB connectivity over the VPC connector not yet established). R4 must reproduce a cold hit and record whether the failures are edge-503 (no healthy instance) or app-emitted, and how long readiness actually takes.
- Whether a keep-warm pinger plus MinSize=2 fully zeroes the user-visible gap in practice, or whether deploy rollovers still leak transient errors that only client retry can mask.

---

## Sources

- AWS App Runner FAQs: https://aws.amazon.com/apprunner/faqs/
- AWS App Runner Pricing: https://aws.amazon.com/apprunner/pricing/
- Managing App Runner automatic scaling: https://docs.aws.amazon.com/apprunner/latest/dg/manage-autoscaling.html
- AutoScalingConfiguration API reference: https://docs.aws.amazon.com/apprunner/latest/api/API_AutoScalingConfiguration.html
- CreateAutoScalingConfiguration API reference: https://docs.aws.amazon.com/apprunner/latest/api/API_CreateAutoScalingConfiguration.html
- Deploying a new application version to App Runner: https://docs.aws.amazon.com/apprunner/latest/dg/manage-deploy.html
- AWS re:Post, "App Runner 503 HTTP errors during deployments": https://repost.aws/questions/QUHmhjksDVQjOkVqVbkBVYZA/app-runner-503-http-errors-during-deployments
- AWS re:Post, "App Runner deployment passes health checks but fails during traffic routing": https://repost.aws/questions/QU0_0hYInxTt6jQ3_wQiQRrw/app-runner-deployment-passes-health-checks-but-fails-during-traffic-routing-rollback-new-service-works-but-updating-existing-service-fails
- aws/apprunner-roadmap issue #9 "Scale to zero" (AWS staff comments on throttle/ramp-down): https://github.com/aws/apprunner-roadmap/issues/9

## Live commands run (read-only)

- `aws apprunner describe-service --service-arn <arn> --region us-west-2`
- `aws apprunner describe-auto-scaling-configuration --auto-scaling-configuration-arn <DefaultConfiguration arn> --region us-west-2`
- `aws apprunner list-operations --service-arn <arn> --region us-west-2 --max-results 20`
- `aws cloudwatch list-metrics --namespace AWS/AppRunner --region us-west-2`
- `aws cloudwatch get-metric-statistics --namespace AWS/AppRunner --dimensions ServiceName=orcast-aws-backend ServiceID=ed4d6e49... --metric-name {ActiveInstances,Requests,2xxStatusResponses,4xxStatusResponses,5xxStatusResponses,RequestLatency} ...`
