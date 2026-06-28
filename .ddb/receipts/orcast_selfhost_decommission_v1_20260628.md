# orcast_selfhost_decommission_v1_20260628

**Receipt kind:** decision_subordinate_mirror
**Paired authoritative decision:** `.ddb/decisions/orcast_selfhost_decommission_v1_20260628.yaml`
**Registered artifact:** `.sst/selfhost_decommission_v1.json`
**Date:** 2026-06-28 America/New_York

---

## Summary

WS-HOSTFOLLOWUP FW2 executed. The dormant orcast self-host is decommissioned:
`orcast-api.service` on `i-04a649f91274e9fce` stopped + disabled via SSM, and the
`orcast-api.aimez.ai` Cloudflare ingress rule + `api.orcast` CNAME removed by a
read-modify-write that preserved the pax `cv`/`shade` routes and the catch-all
verbatim. App Runner is now the sole production backend.

## Gates

- **A1 (pre, canary):** PASS — self-host stopped (502), console/streaming/H0/pax
  all green; zero tunnel dependency proven before the Cloudflare edit.
- **A2 (post):** PASS — `orcast-api.aimez.ai` 404, pax `cv`/`shade` 200, console +
  explore (aurora) + narrate/stream healthy on App Runner, H0 ALL PASS.

## Rollback posture change

The one-env-var self-host rollback no longer exists. App Runner is sole. Reverting
requires re-provisioning the host service + Cloudflare ingress AND repairing the
DD-6 RDS path. Residual risk: App Runner cold-start window, no warm fallback.

## Non-claims

The shared EC2 host is not terminated (pax co-tenants still run). The
`/opt/orcast` checkout + host IAM policy were left inert; full host cleanup is a
separate optional operator task.

Authoritative registration lives in the paired YAML decision + the registered
`.sst` artifact. This receipt is a non-authoritative mirror.
