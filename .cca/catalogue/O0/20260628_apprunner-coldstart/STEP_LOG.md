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
