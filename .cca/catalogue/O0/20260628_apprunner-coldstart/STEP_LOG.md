# WS-COLDSTART — STEP_LOG

## 2026-06-28 chartered + CS1 dispatched

Chartered the cold-start elimination waveset for the DD-10/FW2 residual risk.
Ground truth captured live before dispatch: App Runner MinSize 1 / MaxSize 25 /
MaxConcurrency 100 (DefaultConfiguration); health /health every 10s (healthy=1,
unhealthy=5); instance 1vCPU/2GB; explore + interactions routers mount
UNCONDITIONALLY (main.py 82,84) — so the observed 404 blip is not conditional
mounting and the root cause is unconfirmed.

Dispatched CS1 research as 4 parallel subagent lanes (R1 App Runner mechanics, R2
app startup/readiness, R3 edge/client resilience, R4 repro + observability),
read-only, no infra changes.

## 2026-06-28 CS1 research — PASS

All four lanes returned and are written under research/. Synthesis in
RESEARCH_SYNTHESIS.md.

Root cause CONFIRMED: App Runner EDGE artifact during instance handover (H1). R4
found a fresh instance boot at 17:39:49 UTC — dead center of the FW-ACCEPT blip
window — with a ~33s handover gap; app logs show zero 404/503 and empty 5xx
metrics, so the error was generated at the App Runner routing layer, never
reaching the app. /health stayed 200 (liveness-only). Two contributing paths:
H2 idle ramp-down (ActiveInstances=0 most of 24h; recycle every ~25-35 min; the
10s /health does not keep it hot), H3 healthy-but-explore-cold (lazy per-request
psycopg, no pool; interactions 500 not 503; 404 after a failed create).

Candidate mitigation set (combination, not one knob): M1 keep-warm pinger, M2
MinSize=2 (+~$10/mo), M3 /ready + lifespan pre-warm + connection pool (free,
code), M4 bounded idempotent absorb-the-blip retry in /api/be + pre-body in
narrate-stream (free, code). M4 is the only free lever that directly hides the
confirmed edge-handover gap; M3 fixes the distinct cold-explore path.

Gate verdict: CS1 PASS. Proceed to CS2 discovery. Open operator gates: approve a
CS4 forced-transition repro on the sole live backend; confirm/override the
warm-pool cost ceiling.

## 2026-06-28 operator decisions + CS2 + CS3a (M4)

Operator locked: scope M2+M3+M4 (M1 deferred); CS4 forced-transition repro
AUTHORIZED; proceed to commit + charter + implement. CS1 research committed/pushed
(bc88b2c).

CS2 discovery complete (DISCOVERY_MAP.md). Key decision: do NOT repoint App Runner
health to /ready — coupling liveness to RDS would turn an RDS blip into a total
outage (worse than today's graceful 503). /health stays the liveness check; /ready
is added observability-only; cold latency removed via lifespan pre-warm.

CS3a (M4) implemented + typecheck green: bounded double-write-safe retry in
web/app/api/be/[...path]/route.ts forward() (503 any-method; 502/504/404 GET-only;
1 retry, 300ms+jitter; body buffered so replay-safe) and a single pre-body retry
on 502/503/504 in web/app/api/narrate-stream/route.ts. M4 directly absorbs the
confirmed edge-handover gap for idempotent/no-side-effect calls; M2 (MinSize=2)
covers the handover-404 at the source.

Remaining: CS3b (M3 backend: pool + Bedrock pre-warm, /ready, interactions 503
parity), CS3c (M2 MinSize=2), CS4 (deploy + authorized forced-transition repro
under the gap poller), CS5 acceptance.

## 2026-06-28 CS3c (M2) + CS4 adversarial — PASS

Created a dedicated AutoScalingConfiguration `orcast-warm` (MinSize=2 / MaxSize=25
/ MaxConcurrency=100) and associated it to orcast-aws-backend (UPDATE_SERVICE op
1470d3f1, SUCCEEDED). Mirrored in infra/aws/template.yaml (AppRunnerWarmAutoScaling
+ AutoScalingConfigurationArn) so a stack deploy will not revert to MinSize=1.

Note: the first measurement was lost because a nohup background poller was reaped
when the tool call returned. Re-ran correctly inside one long-blocking command:
started the R4 gap poller, then forced a fresh transition (start-deployment op
e455f6f0, SUCCEEDED) so the poller captured the whole window.

CS4 result with MinSize=2 active: 321 samples, health up 100%, /api/explore/status
2xx 100%, max_gap_while_health_up_ms = 0.0, 0 gap events, 8/8 session-creates 200
through the rollover. Capture: gate_captures/gap_minsize2.json. The Vercel-proxy
M4 retry never needed to fire (no residual edge 5xx) and is retained as
defense-in-depth.

Evidence-driven deferral upheld: backend-image M3 (pool, /ready, interactions 503
parity, lifespan pre-warm) NOT shipped — gap=0 was reached without it, so the
riskier sole-backend image deploy is not justified now.

CS5 acceptance: registered DDB decision orcast_coldstart_mitigation_v1_20260628
(.sst/coldstart_mitigation_v1.json + decisions/receipts). Waveset COMPLETE.
