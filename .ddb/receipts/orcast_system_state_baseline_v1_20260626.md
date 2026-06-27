# orcast_system_state_baseline_v1_20260626

**Receipt kind:** decision_subordinate_mirror
**Paired authoritative decision:** `.ddb/decisions/orcast_system_state_baseline_v1_20260626.yaml`
**Registered artifact:** `.sst/system_state_baseline_v1.json`
**Registry decision_id:** `8f2b264f24e280696788b7a10ead61092bc4a866da77d6a1911415cca098e90b`
**Date:** 2026-06-26 America/New_York
**Lane:** O0 orcast-selfhost-cutover
**Ratification authority:** operator

---

## Summary

First entry in the orcast `.ddb` decision ledger. Records the platform baseline
after cutting the production backend from AWS App Runner to a co-tenant self-host
on the shared `aimez-services` EC2, fronted by the existing cloudflared tunnel.
Managed AWS data stores are unchanged.

## Topology of record

| Layer | State |
|---|---|
| Frontend | Vercel `orcast-h0` -> `orcast-h0.vercel.app`, Root Directory `web` |
| Proxy upstream | `ORCAST_API_BASE = https://orcast-api.aimez.ai` |
| Backend | `orcast-api.service` on `127.0.0.1:8090`, python3.12 venv, `/opt/orcast` @ `95a6d95` |
| Host | `aimez-services` `i-04a649f91274e9fce` (co-tenant with pax 8077/8078) |
| Reach | tunnel `e1ce3073-...` -> `orcast-api.aimez.ai` (first-level, `*.aimez.ai` TLS) |
| IAM | `aimez-host-role` + inline `orcast-backend-data-access` |
| Data plane | us-west-2: 9 DynamoDB tables, 2 S3 buckets, Bedrock, Step Functions |
| Rollback | App Runner `orcast-aws-backend` RUNNING |

## Verification

- Prod proxy: `/api/be/health` 200, `/api/be/api/gates` 200, `/api/be/api/sightings` 200, `/api/be/api/evidence/assets` 401, `POST /api/be/api/interest` 200, `/` 200.
- Host `/health`: `sightings_loaded` 113, `hotspots_loaded` 114 (DynamoDB reachable from the host via the new policy).
- Host access logs confirm Vercel egress traffic reaches `orcast-api.service`.
- `a-gate`: PASS 2026-06-25.

## Known limits (see `.cca/DEPLOY_DEMO_DECISIONS.md`)

- DD-6: RDS `orcast_explore` unreachable from the host (explore-session writes degraded; parity with App Runner).
- DD-5: interest raw-payload snapshot skipped (non-fatal; signup returns 200).
- DD-3: App Runner scale-down deferred to post-submission.

## Authority

Authoritative structured registration lives in the paired YAML decision plus the
registered `.sst` artifact. This receipt is a non-authoritative human-readable
mirror.
