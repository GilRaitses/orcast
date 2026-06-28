# orcast Deploy + Demo Decisions — Resolution Register

Date: 2026-06-26 (America/New_York)
Lane: O0 orcast-selfhost-cutover. Companion to `.cca/STANDING_DECISIONS_REGISTER.md`
(SDR) and `.ddb/decisions/orcast_system_state_baseline_v1_20260626.yaml`.

Schema: `id · decision · rationale · status`. status ∈ {ratified, open, operator-gated}.

---

## DD-1 — Production backend is the self-hosted co-tenant, App Runner is rollback
- **Decision:** The Vercel `/api/be` proxy upstream (`ORCAST_API_BASE`) points to
  `https://orcast-api.aimez.ai` — the orcast FastAPI service co-tenanted on the
  shared `aimez-services` EC2 (`i-04a649f91274e9fce`), fronted by the existing
  cloudflared tunnel. The App Runner service `orcast-aws-backend` stays RUNNING as
  an instant rollback target through the June 29 judging window.
- **Rationale:** Consolidates orcast + pax onto one host/tunnel; removes the
  always-on App Runner cost as the primary path while keeping a one-env-var
  rollback during the deadline.
- **Status:** SUPERSEDED by DD-10 (2026-06-28). The self-host/Cloudflare path is
  retired as primary; App Runner is now canonical. The self-host was subsequently
  decommissioned (DD-10 follow-up / FW2, 2026-06-28).

## DD-2 — Judges hit the same live URL (`orcast-h0.vercel.app`)
- **Decision:** No demo/storyboard URL change. Judges use `https://orcast-h0.vercel.app`
  exactly as before; only the backend upstream moved. The App Runner URL
  (`pjrftm3bkv.us-west-2.awsapprunner.com`) is no longer the canonical demo path
  but remains reachable for rollback.
- **Rationale:** Keeps the submitted live URL stable; the cutover is invisible to
  the demo surface.
- **Status:** SUPERSEDED by DD-10 (2026-06-28). The live URL
  (`orcast-h0.vercel.app`) is unchanged, but the App Runner URL
  (`pjrftm3bkv.us-west-2.awsapprunner.com`) is again the canonical backend path.

## DD-3 — App Runner scale-down is deferred to post-submission
- **Decision:** Do NOT pause/scale-down `orcast-aws-backend` until after the
  June 29 submission is accepted. Then either pause the service or set min-size 0.
- **Rationale:** Rollback insurance during judging outweighs the ~$70-85/mo
  carry for a few days.
- **Status:** RECONCILED by DD-10 (2026-06-28). App Runner is now the PRIMARY
  production backend, not a rollback target, so it must **not** be paused or
  scaled to zero — doing so would take production down. The `aws apprunner
  pause-service` command of record is RETIRED. The cost-removal candidate is now
  the dormant self-host (the FW2 decommission wave in
  `.cca/catalogue/O0/20260628_hosting-consolidation-followups/`), not App Runner.

## DD-4 — Backend code on the host is committed `main` (95a6d95), not the local tree
- **Decision:** The host runs a clean `git clone` of public `main` @ `95a6d95`.
  The uncommitted local explore3d backend work (ONC routers, planner/interactions
  edits) is NOT on the host and NOT in production.
- **Rationale:** Reproducible, parity with the deployed App Runner image (which
  also predates the explore3d work). Shipping uncommitted code to prod is out of
  scope for the cutover.
- **Status:** ratified. Follow-up (open): commit + redeploy the explore3d backend
  surface deliberately if it is to go live (`git -C /opt/orcast pull --ff-only` +
  `sudo systemctl restart orcast-api`).

## DD-5 — Interest signup raw-payload snapshot gap (non-fatal)
- **Decision:** Accept as-is for the cutover. `POST /api/interest` returns 200;
  the host logs `AwsStorage object has no attribute 'raw_payload_bucket'` and
  skips the raw-payload snapshot. Signup is not blocked.
- **Rationale:** Non-fatal; present in committed `main`; endpoint contract
  (SD-020) still satisfied (200). Fix belongs to a backend code wave, not infra.
- **Status:** open (P2 backend fix).

## DD-6 — RDS explore persistence remains degraded
- **Decision:** Explore-session writes (`POST /api/explore/sessions`) degrade on
  the host exactly as on App Runner: RDS `orcast-aws-backend-explore` is private
  (SDR SD-A07) and unreachable from the host region/VPC.
- **Rationale:** No regression vs current production. DynamoDB/S3/Bedrock/Step
  Functions paths are unaffected.
- **Status:** accepted-as-is (parity). Future: VPC peering or a reachable session
  store if explore persistence is required live.

## DD-7 — Demo media (Wave Set MX) still open
- **Decision:** Gallery demo GIFs remain a separate capture task (see
  `.cca/HANDOFF_WAVESETS_CHARTER.md` Wave Set MX); not affected by the cutover.
- **Status:** open (agent-assist + operator).

## DD-8 — SDR deploy-drift O-2/O-3/O-4 unchanged by this lane
- **Decision:** The cutover does not touch the SDR open items O-2 (s-doc-grep
  stale assertions), O-3 (nine-table canon), or O-4 (claim drift). They remain as
  recorded in the SDR.
- **Status:** open (tracked in SDR §3).

## DD-9 — Explore3d backend shipped; ONC disabled in production
- **Decision:** The explore3d backend (ONC hydrophone relay + public-route surface
  planner) is shipped to the host (`5a7e2e8`) and the proxy allow-list (`77d4d0c`).
  ONC is intentionally DISABLED in production: `ORCAST_ENABLE_ONC` is false and
  `ONC_API_TOKEN` is unset, so `/api/onc/hydrophone-signal` returns `enabled:false`
  metadata-only (200) and `/api/onc/archivefile` returns 503.
- **Rationale:** Ship the code path now (additive, import-preflighted, graceful
  degradation) without committing to a live ONC token before it is vetted.
- **Status:** open limit. To enable: set `ONC_API_TOKEN` (secret) + `ORCAST_ENABLE_ONC=true`
  in the host env file and `systemctl restart orcast-api` (via SSM). The explore3d
  FRONTEND (3D landing) remains unshipped (separate demo decision).

## DD-10 — Consolidate production on Vercel + App Runner; retire Cloudflare/self-host as primary (supersedes DD-1, DD-2)
- **Decision:** Production serving is consolidated on Vercel (frontend + edge proxy
  and stream routes) and AWS App Runner (`orcast-aws-backend`). Both Vercel
  upstreams resolve to App Runner: `ORCAST_API_BASE` (the generic `/api/be` JSON
  proxy, repointed from `orcast-api.aimez.ai`) and `ORCAST_STREAM_BASE` (the
  dedicated `/api/narrate-stream` SSE route). The Cloudflare-fronted self-host
  co-tenant (`orcast-api.aimez.ai`) is retired as the primary backend and left
  dormant as a one-env-var rollback; no physical teardown is performed here.
- **Rationale:**
  1. Streaming needs a Cloudflare-free endpoint — WS-STREAM WS2 proved cloudflared
     buffers SSE while App Runner streams. App Runner must run for streaming anyway.
  2. The self-host RDS path is unreachable (DD-6) and broke the live console (503
     on `POST /api/explore/sessions`); App Runner reaches RDS and returns 200.
  3. The Vercel × AWS hackathon brief (`docs/devpost/H0_WORKSHOP_COMPLIANCE.md`)
     requires a Vercel + AWS + Bedrock spine and does not require Cloudflare.
- **Status:** ratified + verified GREEN (2026-06-28). Registered in `.ddb`
  (`orcast_hosting_consolidation_v1_20260628`, baseline `v3`). Verification: App
  Runner `/health` 200; `/api/be/api/explore/sessions` via Vercel 200 (outage
  resolved); `/api/be/api/evidence/assets` 401 (auth gate intact); streamed
  narration first token 1.8-2.8 s incremental; H0 hackathon gate PASS.
- **Follow-up — DONE (FW2, 2026-06-28):** the self-host is decommissioned.
  `orcast-api.service` was stopped + disabled via SSM and the `orcast-api.aimez.ai`
  Cloudflare ingress + CNAME were removed (pax `cv`/`shade` preserved verbatim).
  Registered as `.ddb` `orcast_selfhost_decommission_v1_20260628`. **Rollback
  posture changed:** there is no longer a one-env-var self-host rollback — App
  Runner is the sole backend; reverting requires re-provisioning the host +
  Cloudflare ingress AND repairing the DD-6 RDS path. Residual risk: App Runner
  cold-start window, no warm fallback (consider min-instances / health alarm).

---

## Tracked limits register (for the pre-submission approval gate)

P1 submission is parked until these are reviewed and approved by the operator.

| Limit | State | Severity | Tracked in |
|---|---|---|---|
| RDS explore unreachable from host (explore-session writes 503) | accepted (parity) | medium | DD-6 |
| ONC disabled in prod (metadata-only / 503) | open, enable-on-demand | low | DD-9 |
| explore3d FRONTEND (3D landing) not deployed | open decision | medium | DD-4/DD-9 |
| App Runner kept RUNNING as rollback (~$70-85/mo) | intentional until post-submission | low | DD-3 |
| Host access SSM-only; inbound SSH closed | hardened (no fallback if SSM down) | low | GP-B4 |
| SDR O-2/O-3/O-4 drift | open | low/medium | SDR §3 |
| Demo GIFs (Wave Set MX) | open | medium | DD-7 |
| interest raw-payload | FIXED + verified | resolved | DD-5 |
| explore generic 500 -> 503 | FIXED + verified | resolved | DD-6 |

---

## Operator-gated (OX) — unchanged, human credentials required
- AWS DynamoDB console screenshot (us-west-2, 9 tables) -> submission figures.
- Devpost submission (June 29 5:00 PM ET).
- arXiv upload of both tarballs; backfill arXiv links into outreach drafts.

These do not block any agent wave and are recorded in `.cca/OPEN_ITEMS.md` and
SDR SD-A09.
