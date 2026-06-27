# orcast Self-Host Cutover Wave-Set Charter

Date: 2026-06-26 (America/New_York)
Lane: O0 orcast-selfhost-cutover
Decision: co-tenant compute on the existing pax `aimez-services` host; cutover executed now.

Mirrors the aimez cutover pattern (`pax/infra/aimez_host/`) and the orcast
chartering pattern (`.cca/HANDOFF_WAVESETS_CHARTER.md`). Each wave marks owner and
loop-exit bar. Status reflects execution on 2026-06-26.

---

## WS-D — Discovery [AGENT] — DONE

Resolve account identity, host/role, proxy upstream, and the live data-plane inventory.

- Finding: pax and orcast are the SAME AWS account `198456344617` (no cross-account role).
- Host: `aimez-services` `i-04a649f91274e9fce` (`44.197.243.177`), role `aimez-host-role`, c6i.xlarge, Ubuntu, 6.7Gi free.
- Proxy upstream env var: `ORCAST_API_BASE` (key injected via `X-ORCAST-Key` = `ORCAST_API_KEY`).
- Tunnel `aimez-services` `e1ce3073-...` is remote-managed (token); ingress via Cloudflare API.
- Vercel CLI authed (`gilraitses-1350`); `web/.vercel` -> project `orcast-h0`.

Loop exit: account/IAM model, host, upstream var, and data-store ARNs known. MET.

## WS-HOST — Co-tenant provision [AGENT] — DONE

Install the orcast FastAPI backend as an additive co-tenant.

- Kit authored under `infra/shared_host/` (manifest, `provision_orcast.sh`, `preflight.py`, systemd unit, env template, IAM policy, ingress doc).
- Host: cloned orcast `main` @ `95a6d95` to `/opt/orcast`; **python3.12** venv (backend uses PEP 701 f-strings; 3.10 failed `review_dossier.py`); deps from `tools/deployment/aws/requirements.txt`.
- Env file injected out-of-band to `/opt/orcast/infra/shared_host/env/orcast-services.env` (chmod 600); values single-quoted (DB password has `(`/`|`/`$`).
- `orcast-api.service` enabled, bound `127.0.0.1:8090`.

Loop exit: host `/health` healthy and pax cv/shade unaffected. MET (sightings 113 / hotspots 114; pax 8077/8078 = 200).

## WS-IAM — Data-plane grant [AGENT] — DONE

Grant the host orcast data access.

- Replicated the App Runner instance-role inline policy `orcast-backend-data-access` (DynamoDB x9, S3 x2, Bedrock, Step Functions, Secrets Manager) onto `aimez-host-role`.

Loop exit: host reads orcast DynamoDB/S3. MET (113 sightings / 114 hotspots).

## WS-REACH — Tunnel + Vercel [AGENT] — DONE

Expose the host and repoint the frontend.

- Cloudflare API: appended ingress `orcast-api.aimez.ai -> http://127.0.0.1:8090` (pax `cv`/`shade` preserved) and created a proxied DNS CNAME.
- Used a FIRST-LEVEL subdomain after `api.orcast.aimez.ai` failed TLS (Universal SSL covers only `*.aimez.ai`).
- Vercel `orcast-h0`: set `ORCAST_API_BASE=https://orcast-api.aimez.ai` and `ORCAST_API_KEY` to the host value; redeployed production (aliased to `orcast-h0.vercel.app`).

Loop exit: `https://orcast-api.aimez.ai/health` 200 and the live site serves through it. MET.

## WS-VERIFY — End-to-end [AGENT] — DONE

- Prod proxy: `/api/be/health` 200, `/api/be/api/gates` 200, `/api/be/api/sightings` 200, `/api/be/api/evidence/assets` 401, `POST /api/be/api/interest` 200, `/` 200.
- Host access logs show Vercel egress traffic hitting `orcast-api.service`.
- App Runner kept RUNNING as rollback (scale-down deferred, DD-3).

Loop exit: production verified GREEN with rollback intact. MET.

## WS-DEMO — Deploy/demo decisions [AGENT] — DONE (decisions recorded; some open items remain for owners)

- `.cca/DEPLOY_DEMO_DECISIONS.md` records DD-1..DD-8: backend = self-host with App Runner rollback (DD-1), judges hit the same URL (DD-2), scale-down deferred (DD-3), committed-main on host (DD-4), interest raw-payload non-fatal gap (DD-5), RDS degraded (DD-6), demo GIFs open (DD-7), SDR drift unchanged (DD-8).
- OX operator gates (DynamoDB screenshot, Devpost, arXiv) flagged, unchanged.

Loop exit: every deploy/demo decision is recorded as ratified/open/operator-gated. MET.

## WS-DDB — Decision ledger baseline [AGENT] — DONE

- Created `orcast/.ddb` (`tools/register_sst.py`, `tools/verify_registry_hashes.py`, `decisions/`, `receipts/`, `registry.json`) mirroring the pax surface.
- Registered `.sst/system_state_baseline_v1.json` as the FIRST registry entry (`8f2b264f...`).
- Paired `decisions/orcast_system_state_baseline_v1_20260626.yaml` + `receipts/...md`. `verify_registry_hashes.py` = ok.

Loop exit: first system-state baseline registered and hash-verified. MET.

---

## Operator follow-ups (post-cutover)

- Post-submission: pause App Runner (DD-3).
- Optional: commit `infra/shared_host/`, `.ddb/`, `.sst/`, `.cca/DEPLOY_DEMO_DECISIONS.md`, and this charter (surgical adds per SD-024) so the host kit ships in `main` and future provisions `git pull` it.
- Backend P2: fix `AwsStorage.raw_payload_bucket` (DD-5).
- Unchanged OX gates: DynamoDB screenshot, Devpost, arXiv.
