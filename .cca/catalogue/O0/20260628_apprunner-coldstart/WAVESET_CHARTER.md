# WS-COLDSTART: App Runner cold-start elimination waveset charter

## 0. How to use this charter

This waveset drives the App Runner cold-start / instance-recycle gap to zero
user-visible impact, the residual risk left by DD-10/FW2 (App Runner is now the
sole production backend with no warm fallback). Read this charter, then
`wave_shape.yml` for the machine shape (per-wave lanes, subagent counts,
adversarial layers, targets). The orchestrator runs one wave at a time and
synthesizes into `STEP_LOG.md`.

## 1. The problem and an honest target

During FW-ACCEPT a ~1-minute window was observed where `/api/explore/*` returned
404/503 while `/health` stayed 200, then self-recovered. App Runner already runs
MinSize 1 with a 10s `/health` check, and the explore/interactions routers mount
unconditionally — so the failure mode is an App Runner instance-transition / edge
artifact, and the root cause is **not yet confirmed**. The charter therefore
LEADS with research; it does not assume a fix.

App Runner cannot be literally "instant". The achievable target is **zero
user-visible cold-start gap**: a deploy or instance recycle must never surface a
404/503 to a user. Three independent levers can combine to reach it — a warm pool
(App Runner config), fast/ready startup (app), and absorbing a brief blip with a
bounded idempotent retry (edge/client). Research sizes each.

## 2. CS1 Research wave (parallelism 4, read-only)

Deep, multi-lane parallel grounding. Each lane writes one file under `research/`;
the orchestrator synthesizes `RESEARCH_SYNTHESIS.md`.

| Lane | Title | Agent | Output |
|------|-------|-------|--------|
| R1 | App Runner cold-start / recycle mechanics (AWS-grounded) | generalPurpose | `research/R1_apprunner_mechanics.md` |
| R2 | In-app startup + readiness grounding (codebase) | explore | `research/R2_app_startup.md` |
| R3 | Edge / proxy / client resilience (codebase + transport) | explore | `research/R3_edge_client_resilience.md` |
| R4 | Repro + observability design (AWS CLI + metrics) | generalPurpose | `research/R4_repro_observability.md` |

**Gate:** each lane names the mechanism + the specific knob/code/retry that
addresses the gap at its layer; R1 prices each App Runner knob; R2 rules on
whether `/health` should gate on readiness (or a separate `/ready`); R4 delivers a
SAFE repro plus a measurable "user-visible gap" definition; the synthesis ranks
root-cause hypotheses by evidence and proposes the candidate mitigation set.

## 3. Downstream (chartered after CS1)

CS2 discovery, CS3 implementation, CS4 adversarial (force recycle + deploy +
concurrent load; prove zero user-visible gap; prove the retry does not mask real
outages; confirm cost delta), CS5 acceptance. Shapes depend on the confirmed root
cause, so they are deliberately left `pending-charter`.

## 4. Hard guardrails

- CS1 changes NO infrastructure: read-only AWS describe/metrics + AWS-docs MCP/web
  + codebase reads only. No deploys, no config writes.
- `orcast-aws-backend` is the SOLE production backend. Any repro that forces a
  deployment or instance recycle is operator-gated and only runs in a later wave
  with explicit approval — never in CS1.
