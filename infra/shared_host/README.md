# orcast shared self-host — co-tenant runbook

> **DECOMMISSIONED (DD-10 / FW2, 2026-06-28).** This self-host is no longer
> running. `orcast-api.service` on `i-04a649f91274e9fce` was stopped + disabled
> via SSM and the `orcast-api.aimez.ai` Cloudflare ingress + CNAME were removed
> (see `.ddb` `orcast_selfhost_decommission_v1_20260628`). App Runner
> (`orcast-aws-backend`) is the SOLE production backend; both Vercel upstreams
> (`ORCAST_API_BASE`, `ORCAST_STREAM_BASE`) point to it. There is **no self-host
> rollback** anymore — reverting would require re-provisioning via this runbook
> AND repairing the DD-6 RDS path. The shared EC2 host still runs the pax
> `cv`/`shade` co-tenants and was NOT terminated. The text below is the historical
> provisioning runbook, kept for re-provisioning only; it is not the live topology.

orcast's FastAPI backend runs as a **co-tenant** on the existing pax
`aimez-services` EC2 (`i-04a649f91274e9fce`, us-east-1), reusing the cloudflared
tunnel that already fronts the pax cv/shade services. This replaces the always-on
App Runner service as the upstream for the Vercel proxy while keeping the same
managed AWS data plane (DynamoDB, S3, Bedrock, Step Functions, RDS).

This is the orcast analogue of `pax/infra/aimez_host/`, kept additive so the two
projects share one host and one tunnel.

## Topology

```
Vercel orcast-h0 (Next.js)  --/api/be proxy-->  https://orcast-api.aimez.ai
   cloudflared tunnel aimez-services (token, remote-managed)
   -> 127.0.0.1:8090  orcast-api.service (systemd, user=orcast, /opt/orcast)
   -> us-west-2: DynamoDB(9) + S3(2) + Bedrock + Step Functions  (RDS private, degraded)
pax cv.aimez.ai (8077) / shade.aimez.ai (8078) are untouched.
```

## Files

- `host_manifest.yaml` — single source of truth (packages/files/env/service/reach).
- `provision_orcast.sh` — idempotent host bootstrap (clone, venv, deps, preflight, systemd).
- `preflight.py` — fail-fast import/file/env checks before the service starts.
- `systemd/orcast-api.service` — the co-tenant unit (binds 127.0.0.1:8090).
- `env/orcast-services.env.example` — env template (names only; real values injected out-of-band).
- `iam/orcast_host_policy.json` — data-plane policy replicated from the App Runner instance role; attached to `aimez-host-role`.
- `cloudflared/orcast-ingress.md` — how the tunnel hostname + DNS are added via the Cloudflare API.

## Sequence (W-IAM -> W-HOST -> W-REACH -> verify)

1. **W-IAM** (operator console NOT required; same AWS account, run from an authed shell):
   ```bash
   aws iam put-role-policy --role-name aimez-host-role \
     --policy-name orcast-backend-data-access \
     --policy-document file://infra/shared_host/iam/orcast_host_policy.json
   ```
2. **W-HOST**: copy this kit to the host (or `git pull` once committed), run
   `provision_orcast.sh`, then inject the real env file (with `ORCAST_API_KEY`
   and `ORCAST_DB_PASSWORD`) at
   `/opt/orcast/infra/shared_host/env/orcast-services.env` (chmod 600) and
   `sudo systemctl restart orcast-api`.
3. **W-REACH**: add the tunnel ingress + DNS for `orcast-api.aimez.ai` per
   `cloudflared/orcast-ingress.md`, then set the Vercel `orcast-h0` project env
   `ORCAST_API_BASE=https://orcast-api.aimez.ai` and redeploy.
4. **Verify**: `curl https://orcast-api.aimez.ai/health` (200) and the live site
   through `/api/be`.

## Rollback

The App Runner service `orcast-aws-backend` stays RUNNING. To revert, set the
Vercel `ORCAST_API_BASE` back to `https://pjrftm3bkv.us-west-2.awsapprunner.com`
and redeploy. No host or tunnel teardown is required to roll back.

## Known limit

RDS `orcast-aws-backend-explore` is private (SD-A07) and not reachable from this
host's region/VPC, so explore-session persistence (`POST /api/explore/sessions`)
degrades exactly as it does on App Runner today. Core DynamoDB/S3/Bedrock paths
are unaffected.
