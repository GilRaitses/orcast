# Step Log — orcast Self-Host Cutover lane

All times 2026-06-26 (America/New_York / UTC as noted from host logs).

1. WS-D discovery: AWS `sts get-caller-identity` = root `198456344617` (same account as pax). EC2 `aimez-services` `i-04a649f91274e9fce` `44.197.243.177` role `aimez-host-role`, running. App Runner `orcast-aws-backend` RUNNING. Proxy upstream var = `ORCAST_API_BASE`. Tunnel `e1ce3073-...` remote-managed (token). Vercel CLI authed; `web/.vercel` -> `orcast-h0`. CF token + account id present in `~/.pax_cutover.env`; `VERCEL_TOKEN` absent (local CLI auth used instead). Zone `aimez.ai` = `5200b6a14fd92f5ef1fc9127b28168d9`.
2. Pulled App Runner runtime env (29 vars) + instance-role inline policy `orcast-backend-data-access` for replication.
3. WS-HOST kit authored under `infra/shared_host/` (host_manifest, provision_orcast.sh, preflight.py, systemd/orcast-api.service, env example, iam policy, cloudflared ingress doc, README); scripts syntax-checked.
4. WS-IAM: `aws iam put-role-policy aimez-host-role orcast-backend-data-access` — attached alongside `aimez-host-s3`.
5. Provision stage 1: apt + `useradd orcast` + `git clone --depth 1` orcast main -> `/opt/orcast` (2817 files, `95a6d95`).
6. scp `infra/shared_host` kit + generated `/tmp/orcast-services.env` (from App Runner env) to the host.
7. Provision stage 2 (py3.10): venv + deps OK, but preflight FAILED — `review_dossier.py` line 131 PEP 701 f-string (3.12-only) + env bash-source error on the DB password special chars.
8. Fix: switched kit + host to **python3.12** (deadsnakes); regenerated env file with single-quoted values; rebuilt venv (3.12); preflight = ok.
9. Started `orcast-api.service`; `/health` healthy (storage aws, sightings 113, hotspots 114), `/api/gates` 200, `/api/sightings` 200, `/api/evidence/assets` 401; pax `cv`/`shade` still 200.
10. WS-REACH: CF API appended ingress `api.orcast.aimez.ai` + DNS — TLS handshake failed (Universal SSL covers only `*.aimez.ai`). Switched to first-level `orcast-api.aimez.ai`; ingress now `cv`/`shade`/`orcast-api`; DNS created. `https://orcast-api.aimez.ai/health` 200, gates 200, evidence 401.
11. Vercel `orcast-h0`: overwrote `ORCAST_API_BASE=https://orcast-api.aimez.ai` and `ORCAST_API_KEY` (host value); `vercel redeploy` -> `orcast-h0-jonox76v9`, aliased to `orcast-h0.vercel.app`.
12. WS-VERIFY: prod proxy `/api/be/health` 200, `/api/be/api/gates` 200, `/api/be/api/sightings` 200, `/api/be/api/evidence/assets` 401, `POST /api/be/api/interest` 200, `/` 200. Host access logs (UTC 23:10-23:11) show Vercel egress IPs hitting `orcast-api.service`. Non-fatal: interest logs `AwsStorage object has no attribute 'raw_payload_bucket'` (returns 200). App Runner kept RUNNING (rollback). Temp secret files removed locally.
13. WS-DEMO: authored `.cca/DEPLOY_DEMO_DECISIONS.md` (DD-1..DD-8 + OX gates).
14. WS-DDB: created `orcast/.ddb` (register_sst.py, verify_registry_hashes.py, decisions/, receipts/, registry.json) + `.sst/system_state_baseline_v1.json`; `register_sst.py` registered first entry `8f2b264f...`; `verify_registry_hashes.py` = ok; authored paired decision YAML + receipt MD.
15. WS-CHARTER: authored this handoff home (HANDOFF_CHARTER, HYDRATION_PACKET, ORCHESTRATOR_DISPATCH_PROMPT, STEP_LOG) + SELFHOST_CUTOVER_WAVESET_CHARTER.

Open: commit new surfaces (surgical); post-submission App Runner pause (DD-3); backend `raw_payload_bucket` fix (DD-5); OX gates.
