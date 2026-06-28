# hosting-consolidation follow-ups (WS-HOSTFOLLOWUP)

Follow-up waveset that discharges the open items from the hosting consolidation
decision (`DD-10` / `.ddb` `orcast_hosting_consolidation_v1_20260628`): App Runner
is the canonical production backend; the Cloudflare self-host (`orcast-api.aimez.ai`)
is retired as primary and dormant as rollback.

## Waves

| Wave | Lifecycle | Mode | Adversarial gate |
|------|-----------|------|------------------|
| FW1 | reconciliation | autonomous | doc-drift grep over active-state surfaces |
| FW2 | decommission | OPERATOR-GATED (destructive) | pre traffic-dependency proof + post health |
| FW-ACCEPT | acceptance | autonomous | H0 + e-gate + auth sweep + stream probe, no regression |

## Artifacts

- `WAVESET_CHARTER.md` — authority + per-wave intent
- `wave_shape.yml` — machine shape (owners, adversarial checks, gates)
- `STEP_LOG.md` — chronological execution log

## Status

COMPLETE (2026-06-28). FW1 + FW-ACCEPT + FW2 all executed and gated. FW2
(self-host + Cloudflare teardown) was operator-authorized and run with reversible
canary sequencing; registered as `.ddb` `orcast_selfhost_decommission_v1_20260628`.
App Runner is now the sole production backend. The shared EC2 host was not
terminated (pax co-tenants still run).
