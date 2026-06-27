# O0 Handoff Charter — orcast Self-Host Cutover lane

**Lane:** orcast-selfhost-cutover
**Date:** 2026-06-26 (America/New_York)
**Repo:** `/Users/gilraitses/orcast` — branch `main` @ `95a6d95`

## A. Purpose

Cut the orcast production backend over from AWS App Runner to a co-tenant
self-host on the shared pax `aimez-services` EC2, so pax and orcast share one
backend host and one cloudflared tunnel; resolve the deploy/demo decisions; and
stand up an `orcast/.ddb` decision ledger seeded with the first system-state
baseline. Executed under operator authorization (cutover-now, co-tenant compute).

## B. Decisions that are LOCKED — do not reopen

1. **Co-tenant compute.** orcast FastAPI runs additively on the existing
   `aimez-services` host (`i-04a649f91274e9fce`), NOT a new instance. pax
   `cv`/`shade` and the tunnel are touched additive-only.
2. **Same AWS account.** pax and orcast are both `198456344617`; the host role
   `aimez-host-role` carries the replicated `orcast-backend-data-access` policy
   (no cross-account role).
3. **Python 3.12 on the host.** The backend uses PEP 701 f-strings
   (`routers/review_dossier.py`); 3.10 fails. Matches the Dockerfile.
4. **First-level tunnel hostname `orcast-api.aimez.ai`.** A third-level name
   (`api.orcast.aimez.ai`) fails TLS (Universal SSL covers only `*.aimez.ai`).
5. **App Runner stays RUNNING as rollback** through the June 29 window; revert is
   one `ORCAST_API_BASE` change + redeploy. Scale-down is post-submission (DD-3).
6. **Host runs committed `main` @ 95a6d95**, not the uncommitted local explore3d
   backend work (DD-4).
7. **Managed AWS data stores unchanged**; only compute moved. RDS explore stays
   degraded (DD-6), same as App Runner.
8. **Secrets stay in `~/.pax_cutover.env` and the host env file** (chmod 600);
   never committed. Surgical commits only (SD-024).

## C. Registry snapshot

| Slice | What shipped | Status |
|-------|--------------|--------|
| WS-D discovery | account/host/role/upstream/tunnel/Vercel resolved | done |
| WS-HOST | `orcast-api.service` live on `:8090` (py3.12, `/opt/orcast`) | done, healthy |
| WS-IAM | `orcast-backend-data-access` on `aimez-host-role` | done, verified |
| WS-REACH | tunnel `orcast-api.aimez.ai` + Vercel repoint + redeploy | done, GREEN |
| WS-VERIFY | prod proxy GREEN; host logs confirm traffic | done |
| WS-DEMO | `.cca/DEPLOY_DEMO_DECISIONS.md` (DD-1..DD-8) | done |
| WS-DDB | `orcast/.ddb` + first baseline entry `8f2b264f...` | done, verified |
| Host kit | `infra/shared_host/` | authored (uncommitted) |

## D. Gate / metric state

- Cutover: verified GREEN 2026-06-26 (prod proxy 200/401 matrix; host access logs).
- `.ddb` verify: `python3 .ddb/tools/verify_registry_hashes.py` = ok (1 active).
- `a-gate`: PASS 2026-06-25 — do not re-run assuming failure.

## E. Pending / operator follow-ups

- Commit the new surfaces (surgical) if they should ship in `main`:
  `infra/shared_host/`, `.ddb/`, `.sst/`, `.cca/DEPLOY_DEMO_DECISIONS.md`, this
  handoff home. Until then the host kit lives only locally + on the host.
- Post-submission: `aws apprunner pause-service ...` (DD-3).
- Backend P2: `AwsStorage.raw_payload_bucket` (DD-5).
- OX (operator, unchanged): DynamoDB screenshot, Devpost, arXiv.

## F. Return contract

When resuming this lane, state: (1) which follow-up you are taking; (2) the files
you read; (3) confirmation that App Runner is still the rollback; (4) the next
action. On completion, state deliverables (paths), gate/verify result, and the
next operator action.

## G. Transcript / provenance pointer

Plan: `/Users/gilraitses/.cursor/plans/orcast_selfhost_cutover_d240819a.plan.md`.
Companion: `.cca/DEPLOY_DEMO_DECISIONS.md`,
`.ddb/decisions/orcast_system_state_baseline_v1_20260626.yaml`,
`infra/shared_host/README.md`.
