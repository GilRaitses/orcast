# orcast_gp_preflight_v1_20260626

**Receipt kind:** decision_subordinate_mirror
**Paired authoritative decision:** `.ddb/decisions/orcast_gp_preflight_v1_20260626.yaml`
**Registered artifact:** `.sst/gp_preflight_v1.json`
**Registry decision_id:** `d60cedb514fd29db0028c4b74ec05c3773649ba67d7f541a9f3ef8c5572e2e21`
**Date:** 2026-06-26 America/New_York
**Lane:** O0 orcast-selfhost-cutover (GP hardening)

---

## Summary

Adversarial gap-detection + preflight wave set over the cutover surfaces (Phase A)
and the live deployment (Phase B). Both phases clean after remediation. Full
per-wave verdicts in `.cca/GP_GAP_REGISTER.md`.

## Verdicts

| Wave | Verdict |
|---|---|
| GP-A1 secret-leak | FIXED (.gitignore env coverage) |
| GP-A2 static preflight | PASS |
| GP-A3 plan-vs-reality | FIXED (provision script hostname) |
| GP-A4 gate regression | PASS (only known O-2 reds) |
| GP-A5 commit scope | FIXED (pycache cleanup; scope locked) |
| GP-B1 reachability+TLS | PASS |
| GP-B2 proxy+authz | PASS (host traffic confirmed) |
| GP-B3 co-tenant | PASS |
| GP-B4 security exposure | FIXED (SSH SG single /32) |
| GP-B5 rollback+resilience | PASS (self-heal ~6s; RDS fails soft) |

## Fixes applied this wave
- `.gitignore`: `infra/shared_host/env/*.env`
- `infra/shared_host/provision_orcast.sh`: 2 lines `api.orcast.aimez.ai` -> `orcast-api.aimez.ai`
- removed stray `__pycache__` under `.ddb/tools` and `infra/shared_host`
- SG `sg-08ad4456a152e4b27`: added current `/32`, revoked stale `172.56.31.148/32`

## Notes
- COMMIT remains operator-gated (surgical add list prepared).
- Methodology fix recorded: re-ran scans under bash + grep -r after a zsh/rg false-clean.

Authoritative registration lives in the paired YAML decision + the registered
`.sst` artifact. This receipt is a non-authoritative mirror.
