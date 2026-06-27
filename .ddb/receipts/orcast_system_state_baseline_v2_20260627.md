# orcast_system_state_baseline_v2_20260627

**Receipt kind:** decision_subordinate_mirror
**Paired authoritative decision:** `.ddb/decisions/orcast_system_state_baseline_v2_20260627.yaml`
**Registered artifact:** `.sst/system_state_baseline_v2.json`
**Registry decision_id:** `57853cfb36d2cf41f35191cfc46cee443410460a7a88a53e2097c41176dc5e34`
**Supersedes:** `orcast_system_state_baseline_v1_20260626`
**Date:** 2026-06-27 America/New_York

---

## Summary

Updated platform baseline after shipping the explore3d backend (DD-4) and the
pre-submission hardening. Supersedes v1.

| Layer | State |
|---|---|
| Backend host | `5a7e2e8` — ONC relay + public-route planner + DD-5/DD-6 fixes |
| Frontend (Vercel) | `77d4d0c` — ONC + interactions/plan public allow-list |
| Host access | SSM-only; inbound SSH closed |
| ONC | shipped but DISABLED (metadata-only / 503) |
| explore3d frontend | not deployed |
| Rollback | App Runner RUNNING |

## Verification
- `selfhost-gate` PASS; ONC signal (proxy) 200, archive 503; interest persists to S3; explore 503 (graceful).

## Tracked limits (pending operator approval before P1)
RDS explore (DD-6), ONC disabled (DD-9), explore3d frontend undeployed (DD-4/DD-9),
App Runner rollback cost (DD-3), SSM-only access (GP-B4), SDR O-2/O-3/O-4, demo GIFs (DD-7).

Authoritative registration lives in the paired YAML decision + the registered
`.sst` artifact. This receipt is a non-authoritative mirror.
