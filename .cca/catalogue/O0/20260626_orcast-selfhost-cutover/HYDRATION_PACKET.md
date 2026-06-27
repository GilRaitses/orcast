# Hydration Packet — orcast Self-Host Cutover lane

Read in this order before acting on this lane.

1. `.cca/catalogue/O0/20260626_orcast-selfhost-cutover/HANDOFF_CHARTER.md` — locked decisions, registry snapshot, follow-ups.
2. `.cca/catalogue/O0/20260626_orcast-selfhost-cutover/SELFHOST_CUTOVER_WAVESET_CHARTER.md` — WS-D..WS-DDB, owners, loop-exit bars, status.
3. `.cca/DEPLOY_DEMO_DECISIONS.md` — DD-1..DD-8 + OX operator gates.
4. `infra/shared_host/README.md` — co-tenant runbook + rollback.
5. `infra/shared_host/host_manifest.yaml` — packages/files/env/service/reach single source of truth.
6. `infra/shared_host/cloudflared/orcast-ingress.md` — tunnel ingress + DNS via Cloudflare API (TLS note).
7. `.ddb/decisions/orcast_system_state_baseline_v1_20260626.yaml` — authoritative baseline decision.
8. `.ddb/receipts/orcast_system_state_baseline_v1_20260626.md` — subordinate mirror.
9. `.sst/system_state_baseline_v1.json` — the registered baseline artifact.
10. `.cca/STANDING_DECISIONS_REGISTER.md` — SDR (SD-011 deploy canon, SD-020 interest route, SD-A07 RDS, SD-024 surgical commits).

## Reference (pax pattern, read-only)
- `pax/infra/aimez_host/` — the source self-hosting pattern.
- `pax/.ddb/` — the source decision-ledger surface.

## Secrets (never committed)
- `~/.pax_cutover.env` (Cloudflare token/account, PAX_SERVICE_KEY).
- Host: `/opt/orcast/infra/shared_host/env/orcast-services.env` (chmod 600).
- SSH: `~/.ssh/pax-ec2-key.pem` to `ubuntu@44.197.243.177`.
