# WS-HOSTFOLLOWUP: hosting-consolidation follow-ups waveset charter

## 0. How to use this charter

This waveset discharges the follow-ups left open by the hosting consolidation
decision (`DD-10` / `.ddb` `orcast_hosting_consolidation_v1_20260628`), which made
AWS App Runner the canonical production backend and retired the Cloudflare
self-host (`orcast-api.aimez.ai`) as primary. Read this charter, then
`wave_shape.yml` for the machine shape (per-wave owners, adversarial checks,
gates). The orchestrator runs one wave at a time and synthesizes into
`STEP_LOG.md`. Every work wave carries an adversarial check that must pass before
final acceptance.

## 1. Why a follow-up waveset

The consolidation decision shipped and passed its own gates, but it left three
open items: stale decision text that now contradicts the live topology, the
physical decommission of the dormant self-host, and the loss of a warm fallback.
Leaving these uncharted risks drift (a future reader pausing App Runner per the
old DD-3 would take prod down) and an indefinite dormant-but-billed self-host.

## 2. The waves (parameterized in wave_shape.yml)

### FW1 Reconciliation (parallelism 1, autonomous)

Reconcile the **active** current-state surfaces only; historical logs are frozen
point-in-time records and are not rewritten.

| Surface | Drift | Fix |
|---------|-------|-----|
| `.cca/DEPLOY_DEMO_DECISIONS.md` DD-3 | "Do NOT pause App Runner until post-submission, then pause it" — now dangerous; App Runner is primary | Reconcile: App Runner is primary, do not pause; the self-host is the decommission candidate (FW2) |
| `infra/shared_host/README.md` | present tense "replaces the always-on App Runner service as the upstream" | DD-10 banner: retired as primary, dormant rollback only |
| `infra/shared_host/cloudflared/orcast-ingress.md` | runbook reads as the live ingress | DD-10 banner: ingress is the FW2 decommission target |

**Adversarial A1 (doc-drift):** a curated doc-grep over the active-state surfaces
finds zero stale "App Runner is rollback / pause App Runner / self-host is
primary" claims that lack a DD-10 superseded banner.

### FW2 Decommission (parallelism 1, OPERATOR-GATED, destructive — charter only)

Physically retire the self-host: remove the `orcast-api.aimez.ai` Cloudflare
ingress rule + the `api.orcast` CNAME (read-modify-write; pax `cv`/`shade` routes
preserved verbatim), and stop+disable `orcast-api.service` on
`i-04a649f91274e9fce` via SSM. No agent runs this; an operator executes it.

**Adversarial A1 (pre, traffic-dependency):** prove zero Vercel prod traffic
resolves to `orcast-api.aimez.ai` (both `ORCAST_API_BASE` and `ORCAST_STREAM_BASE`
point to App Runner) before teardown.
**Adversarial A2 (post, health):** console + streaming + H0 stay green after
removal; the rollback path is re-documented as App Runner-only.

Rollback to the self-host first requires repairing the DD-6 RDS path, so this is
a one-way step until that is fixed.

### FW-ACCEPT Acceptance (parallelism 1, autonomous)

Re-run the consolidated-path gates (doc-grep, H0, e-gate, prod auth sweep, stream
probe) to prove the FW1 edits caused no regression. Record in `STEP_LOG.md`.
Commit + push if green. FW2 remains the single open operator gate after this.

## 3. Acceptance criteria

- FW1 adversarial A1 clean; historical logs untouched.
- No regression: H0 PASS, e-gate PASS, auth sweep 401s intact, streamed narration
  incremental through the prod chain.
- FW2 stays operator-gated and reversible until an operator runs it.

## 4. Collision governance

FW1 edits only the three active-state surfaces. FW2 is destructive + operator-only
and preserves the pax co-tenant routes verbatim. Agents commit/push only after
all FW1 + FW-ACCEPT gates pass.
