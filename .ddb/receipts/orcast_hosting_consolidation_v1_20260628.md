# orcast_hosting_consolidation_v1_20260628

**Receipt kind:** decision_subordinate_mirror
**Paired authoritative decision:** `.ddb/decisions/orcast_hosting_consolidation_v1_20260628.yaml`
**Registered artifact:** `.sst/hosting_consolidation_v1.json`
**Date:** 2026-06-28 America/New_York

---

## Summary

Production serving is consolidated on Vercel + AWS App Runner. Both Vercel
upstreams (`ORCAST_API_BASE`, `ORCAST_STREAM_BASE`) resolve to App Runner. The
Cloudflare-fronted self-host co-tenant (`orcast-api.aimez.ai`) is retired as the
primary backend and left dormant as a one-env-var rollback. Supersedes DD-1/DD-2.

## Why

- Streaming needs a Cloudflare-free path (WS-STREAM WS2: cloudflared buffers SSE;
  App Runner streams). App Runner must run for streaming anyway.
- Self-host RDS is unreachable (DD-6) and broke the live console (503 on explore
  sessions). App Runner returns 200.
- The Vercel x AWS hackathon brief requires Vercel + AWS + Bedrock, not Cloudflare.

## Acceptance verification

App Runner `/health` 200; `/api/be/api/explore/sessions` via Vercel 200 (outage
resolved); `/api/be/api/evidence/assets` 401 (auth gate intact, AX-1 posture
preserved); streamed narration first token 1.8-2.8 s incremental (WS7); H0
hackathon gate PASS.

## Non-claims

No physical teardown of the self-host or Cloudflare ingress (dormant rollback
only, operator action post-submission). Live URL unchanged. Rollback to the
self-host requires repairing DD-6 first.

Authoritative registration lives in the paired YAML decision + the registered
`.sst` artifact. This receipt is a non-authoritative mirror.
