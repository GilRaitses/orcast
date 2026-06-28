# Receipt: App Runner cold-start gap eliminated (WS-COLDSTART CS4)

- Decision: `orcast_coldstart_mitigation_v1_20260628`
- Kind: `coldstart_mitigation_result`
- Status: active
- Date: 2026-06-28
- Parent: `orcast_selfhost_decommission_v1_20260628` (closes its recorded residual risk)
- Artifact: `.sst/coldstart_mitigation_v1.json`

## What was decided and done

The App Runner instance-handover gap (residual risk from the self-host
decommission) is closed. A 4-lane parallel research wave (CS1) confirmed the root
cause: an App Runner edge artifact during instance handover with a single
`MinSize=1` instance (a fresh instance booted dead-center of the FW-ACCEPT blip
window; app logs showed zero 404/503 and empty 5xx metrics).

Applied:
- **M2 warm pool** — dedicated `AutoScalingConfiguration` `orcast-warm`
  (`MinSize=2`/`MaxSize=25`/`MaxConcurrency=100`), associated to
  `orcast-aws-backend`. A sibling instance always serves during a deploy or
  recycle. Cost +~$10.22/mo. Mirrored in `infra/aws/template.yaml`.
- **M4 edge retry** — bounded, double-write-safe absorb-the-blip retry in the
  Vercel proxy (`/api/be` and `narrate-stream`) as defense-in-depth.

Deferred (validated by the measurement): backend-image M3 (connection pool,
`/ready`, interactions 503 parity, lifespan pre-warm). Decided NOT to couple App
Runner health to a DB-gated `/ready`.

## Adversarial gate (CS4)

A forced `start-deployment` transition with `MinSize=2` active, measured by the
R4 external gap poller (`tools/testing/coldstart_gap_probe.py`, 500ms cadence):

| Metric | Value |
|--------|-------|
| samples | 321 |
| health up | 100% |
| `/api/explore/status` 2xx | 100% |
| `max_gap_while_health_up_ms` | **0.0** |
| gap events | 0 |
| session-create | 8/8 → 200 through the rollover |

Capture: `.cca/catalogue/O0/20260628_apprunner-coldstart/gate_captures/gap_minsize2.json`.

**Verdict: PASS — zero user-visible gap.** The proxy retry did not need to fire
(no residual edge 5xx) and is retained for multi-instance transitions.

## Non-claims

- App Runner is not literally "instant"; the achieved property is zero
  user-visible gap during a deploy/recycle, validated externally.
- Topology unchanged (DD-10): Vercel + App Runner remains the sole backend.
