# orcast_system_state_baseline_v3_20260628

**Receipt kind:** decision_subordinate_mirror
**Paired authoritative decision:** `.ddb/decisions/orcast_system_state_baseline_v3_20260628.yaml`
**Registered artifact:** `.sst/system_state_baseline_v3.json`
**Date:** 2026-06-28 America/New_York

---

## Summary

Production system-state baseline v3. Topology moves from `selfhost_cotenant` (v2)
to `vercel_apprunner` (v3): the backend serves from AWS App Runner and both Vercel
upstreams (`ORCAST_API_BASE`, `ORCAST_STREAM_BASE`) resolve to App Runner.
WS-STREAM streamed narration is live; explore-session writes reach RDS (200). The
Cloudflare self-host co-tenant is dormant rollback only. Supersedes baseline v2.

## Verification

App Runner `/health` 200; explore sessions via Vercel 200; evidence/assets 401;
streamed narration first token 1.8-2.8 s incremental.

Authoritative registration lives in the paired YAML decision + the registered
`.sst` artifact. This receipt is a non-authoritative mirror.
