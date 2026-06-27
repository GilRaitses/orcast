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
- **Status:** ratified + verified GREEN (2026-06-26). Prod proxy: `/api/be/health`
  200, `/api/be/api/gates` 200, `/api/be/api/sightings` 200,
  `/api/be/api/evidence/assets` 401, `/api/be/api/interest` POST 200, `/` 200;
  host access logs confirm Vercel egress traffic reaches the host.

## DD-2 — Judges hit the same live URL (`orcast-h0.vercel.app`)
- **Decision:** No demo/storyboard URL change. Judges use `https://orcast-h0.vercel.app`
  exactly as before; only the backend upstream moved. The App Runner URL
  (`pjrftm3bkv.us-west-2.awsapprunner.com`) is no longer the canonical demo path
  but remains reachable for rollback.
- **Rationale:** Keeps the submitted live URL stable; the cutover is invisible to
  the demo surface.
- **Status:** ratified.

## DD-3 — App Runner scale-down is deferred to post-submission
- **Decision:** Do NOT pause/scale-down `orcast-aws-backend` until after the
  June 29 submission is accepted. Then either pause the service or set min-size 0.
- **Rationale:** Rollback insurance during judging outweighs the ~$70-85/mo
  carry for a few days.
- **Status:** open (operator action post-submission). Command of record:
  `aws apprunner pause-service --service-arn arn:aws:apprunner:us-west-2:198456344617:service/orcast-aws-backend/ed4d6e4999864a468e11349c3f1083d9`.

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
