# App Runner cold-start elimination (WS-COLDSTART)

Drives the App Runner cold-start / instance-recycle gap to zero user-visible
impact — the residual risk from DD-10/FW2 (App Runner is now the sole production
backend with no warm fallback).

Observed baseline (FW-ACCEPT, 2026-06-28): a ~1-minute window where
`/api/explore/*` returned 404/503 while `/health` stayed 200, then self-recovered.
Root cause unconfirmed; routers mount unconditionally and MinSize is already 1, so
the waveset leads with research.

## Waves

| Wave | Lifecycle | Mode |
|------|-----------|------|
| CS1 | research | 4 parallel lanes (R1 mechanics, R2 app startup, R3 edge/client, R4 repro+obs) |
| CS2-CS5 | discovery → implementation → adversarial → acceptance | chartered after CS1 synthesis |

## Artifacts

- `WAVESET_CHARTER.md` — authority + per-wave intent
- `wave_shape.yml` — machine shape (lanes, knobs, targets, guardrails)
- `research/` — CS1 lane deliverables
- `RESEARCH_SYNTHESIS.md` — CS1 synthesis (after the lanes land)
- `STEP_LOG.md` — chronological log

## Target

Zero user-visible cold-start gap (a deploy or recycle never surfaces a 404/503 to
a user). App Runner cannot be literally instant; the gap is closed with a warm
pool + fast/ready startup + a bounded idempotent absorb-the-blip retry.

## Outcome: COMPLETE (gap = 0)

Root cause (CS1): App Runner edge artifact during instance handover with a single
MinSize=1 instance. Fix shipped: **M2** dedicated `orcast-warm` AutoScalingConfiguration
(MinSize=2, +~$10/mo) + **M4** bounded edge-blip retry in the Vercel proxy
(defense-in-depth). **CS4 measured a forced transition: `max_gap_while_health_up_ms`
= 0.0**, 100% status 2xx, 8/8 session-creates 200 through the rollover. Backend-image
M3 (pool/`/ready`/503-parity/pre-warm) was deferred because gap=0 was reached
without it. Registered as DDB decision `orcast_coldstart_mitigation_v1_20260628`.
