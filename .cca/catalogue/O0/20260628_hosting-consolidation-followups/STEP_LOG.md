# WS-HOSTFOLLOWUP — STEP_LOG

## 2026-06-28 chartered

Chartered the follow-up waveset for DD-10 (hosting consolidation). Three waves:
FW1 reconciliation (autonomous), FW2 decommission (operator-gated, destructive),
FW-ACCEPT acceptance (autonomous). Each work wave carries an adversarial check
before final acceptance. Active-state drift scoped to three surfaces;
historical logs frozen.

## 2026-06-28 FW1 reconciliation — PASS

Edited the three active-state surfaces only:
- `.cca/DEPLOY_DEMO_DECISIONS.md` DD-3: RECONCILED by DD-10. App Runner is the
  PRIMARY backend, must not be paused; the `aws apprunner pause-service` command
  of record is RETIRED; the cost-removal candidate is the dormant self-host (FW2).
- `infra/shared_host/README.md`: DD-10 banner (retired as primary; dormant
  rollback; FW2 decommission target).
- `infra/shared_host/cloudflared/orcast-ingress.md`: DD-10 banner (ingress is the
  FW2 decommission target; procedure doubles as the teardown reference).

**Adversarial A1 (doc-drift): PASS.** Curated doc-grep over the three active
surfaces: each mentions the topology AND carries a DD-10 banner (0 fails). No
live doc instructs pausing the now-primary App Runner. Historical logs untouched.

## 2026-06-28 FW2 decommission — CHARTERED, OPERATOR-GATED (not executed)

Destructive SSM + Cloudflare-API teardown of the dormant self-host. Left as the
single open operator gate; no agent runs it. pax cv/shade co-tenants are
preserved verbatim. Rollback to the self-host first requires repairing DD-6.

## 2026-06-28 FW-ACCEPT — PASS (no regression from FW1)

- doc-drift A1: PASS (above).
- H0 hackathon gate: ALL PASS (agent_smoke, narration_backend=bedrock, health
  200, public gates no token leak).
- Prod auth sweep: App Runner /health 200; evidence/assets no-key 401; spoofed
  `X-ORCAST-Reviewer-Id` 401 (AX-1 posture intact).
- Explore sessions via Vercel: stable 200 (5/5 after the transient below).
- Explore router mounted (openapi: explore + interactions incl. narrate/stream);
  `/api/explore/status` 200, aurora_connected=true, exploration_backend=postgres.
- Streamed narration through the full prod chain: validated incremental at
  first-token 1.64s / 134 tokens earlier this session; endpoint confirmed mounted.
- WS6 rate limiting enforced: repeated probing tripped the per-IP daily session
  quota (HTTP 429) — control working as designed.

**Observed risk (not an FW1 regression):** during the sweep, `/api/explore/*`
briefly returned 404/503 (empty body) for ~1 minute while `/health` and
`/api/gates` stayed 200, then fully recovered. This is an App Runner instance
recycle / cold-start window and maps to the baseline_v3 tracked limit "App Runner
is the sole live backend; no warm fallback". FW1 is doc-only and cannot cause it.
Recorded as a tracked risk for the FW2 operator decision (a warm fallback or a
min-instance / health-alarm posture should be considered before tearing down the
dormant self-host).

Verdict: FW1 + FW-ACCEPT GREEN. FW2 remains the single open operator gate.

## 2026-06-28 FW2 decommission — EXECUTED (operator-authorized) — PASS

Operator authorized the teardown ("if it's safe"). Confirmed App Runner is the
standing replacement and ran the teardown with reversible canary sequencing.

Feasibility/safety pre-checks: SSM instance Online (Run Command, no plugin
needed); Cloudflare token available; shared tunnel had 4 rules (cv 8077, shade
8078, orcast-api 8090, catch-all 404); pax cv/shade 200.

Execution:
1. SSM (cmd 67fe0e80-d1ba-407e-aaa0-178371d064eb): `systemctl stop` + `disable`
   orcast-api.service → is-active=inactive, is-enabled=disabled.
2. **A1 canary (PASS):** with the self-host down (orcast-api.aimez.ai 502), the
   console (/api/be/health, gates, sightings all 200), pax cv/shade (200), and H0
   (ALL PASS) stayed green — zero prod dependency on the tunnel, proven before any
   Cloudflare edit (instantly reversible via `systemctl start` if it had failed).
3. Cloudflare read-modify-write: removed ONLY the orcast-api.aimez.ai ingress rule
   (ingress cv,shade,orcast,404 → cv,shade,404) and deleted the api.orcast CNAME.
   pax routes + catch-all preserved verbatim.
4. **A2 post-teardown (PASS):** orcast-api.aimez.ai 404 (route gone); pax cv/shade
   200; console + explore (aurora_connected=true) + narrate/stream healthy on App
   Runner; H0 ALL PASS.

Registered `.ddb` `orcast_selfhost_decommission_v1_20260628` (5 active, verify ok).

Rollback posture changed: no one-env-var self-host rollback remains; App Runner is
sole. Reverting needs re-provisioning + DD-6 repair. Residual risk: App Runner
cold-start window, no warm fallback (min-instances/health-alarm recommended).

Verdict: WS-HOSTFOLLOWUP COMPLETE (FW1 + FW-ACCEPT + FW2 all green). The shared
EC2 host was NOT terminated (pax co-tenants still run); /opt/orcast checkout + host
IAM left inert as an optional future cleanup.
