# GP Gap Register — Adversarial Gap-Detection + Preflight Wave Set

Date: 2026-06-26 (America/New_York)
Lane: O0 orcast-selfhost-cutover. Scope: the self-host cutover surfaces
(`infra/shared_host/`, `.ddb/`, `.sst/`, `.cca/DEPLOY_DEMO_DECISIONS.md`, the two
`.cca/catalogue/O0/2026062*-*/` handoff homes) and the live deployment.

Verdict legend: PASS (clean) / FIXED (gap found and remediated) / FLAG (recorded, owner action).

---

## Phase A — Pre-commit

| Wave | Verdict | Finding / action |
|---|---|---|
| GP-A1 secret-leak | FIXED | No secret values in any surface. Gap: `.gitignore` `.env` line did not cover `infra/shared_host/env/orcast-services.env`. Fix: added `infra/shared_host/env/*.env` (keeps `*.example` tracked). |
| GP-A2 static preflight | PASS | `bash -n`, `py_compile`, `ReadLints` (0), JSON/YAML valid, IAM policy 7 stmts, `verify_registry_hashes.py` ok, `register_sst.py` idempotent. |
| GP-A3 plan-vs-reality | FIXED | Docs canonical (orcast-api.aimez.ai, ORCAST_API_BASE, py3.12, decision_id 8f2b264f). Live: App Runner RUNNING, host venv Python 3.12.13. Gap: 2 lines in `provision_orcast.sh` gave operational guidance pointing at the rejected `api.orcast.aimez.ai`. Fix: corrected both to `orcast-api.aimez.ai` (TLS-rationale mentions elsewhere are intentional). |
| GP-A4 gate regression | PASS | `s-doc-grep` fails ONLY on the two pre-existing SDR O-2 reds (`orcast-erd-workflows.drawio` missing, `next_wave_set H1`) — no new breakage. `q1c-ddb-schema` PASS (9 tables, managed-agents 4). `.ddb` ledger verify ok. |
| GP-A5 commit scope | FIXED | Locked 7-path surgical scope. Gap: GP-A2 `py_compile` left `__pycache__/*.pyc` under `.ddb/tools/` and `infra/shared_host/`. Fix: removed; confirmed `__pycache__/` is globally ignored. Real env file confirmed git-ignored; no `.DS_Store`/binary/large strays in scope. |

### Methodology gap (self-caught, P1)
Initial GP-A1/A3 scans returned false "clean" because (a) **zsh does not word-split unquoted `$VAR`** (multi-path args collapsed to one bogus path) and (b) **ripgrep skips dot-directories** (`.ddb`, `.sst`, `.cca`) by default. Re-ran all scans under `bash` with `grep -r` (and `rg --hidden --no-ignore`). All Phase A verdicts above are the corrected results.

---

## Phase B — Live deployment

| Wave | Verdict | Finding / action |
|---|---|---|
| GP-B1 reachability + TLS | PASS | DNS resolves (Cloudflare anycast). `/health`,`/api/gates`,`/api/sightings` 200; `/api/evidence/assets` 401. TLS cert CN=aimez.ai (Google Trust Services, valid through Aug 18 2026) covers the first-level SNI (https 200 proves it). Direct-to-backend `/api/journal`=404 (safe; no data leak). |
| GP-B2 proxy + authz | PASS | Via `orcast-h0.vercel.app/api/be`: public 200; `evidence`/`journal`/`decision-records`/`review-dossier` all 401; `interest` POST 200. Host journal shows Vercel egress (44.203.153.98) hitting the service; protected paths short-circuit to 401 at the proxy and never reach the backend (defense in depth). |
| GP-B3 co-tenant | PASS | pax `cv`/`shade` 200; tunnel ingress = [cv, shade, orcast-api]; `orcast-api`/`pax-infer`/`pax-shade`/`cloudflared` all active AND enabled; headroom 6.6Gi free, load 0.00, orcast-api 105 MB. |
| GP-B4 security exposure | FIXED | Keyed endpoint 401 with no key AND bogus key; error body terse (`{"detail":"Sign in required"}`); no CORS echo for evil origin; no server/version banner (edge `server: cloudflare`); host env file `600 orcast:orcast`. SSH SG: no `0.0.0.0/0`. Gap: stale prior-IP `/32` allow. Fix: added current IP (`gp-waveset-ops`) and revoked stale `172.56.31.148/32`; SSH now a single current `/32`. |
| GP-B5 rollback + resilience | PASS | App Runner rollback intact (`/health` 200, status RUNNING). `orcast-api` `Restart=always`; `systemctl restart` self-healed healthy in ~6s; pax cv/shade untouched; edge+proxy 200 post-restart. RDS-degraded path fails soft (`explore/sessions` 500, process survives) per DD-6. |

---

## Open items returned to owners
- O-2 (SDR): `s-doc-grep` two pre-existing reds remain (unrelated to GP).
- DD-5: `AwsStorage.raw_payload_bucket` non-fatal interest gap (backend P2).
- DD-6: RDS explore returns generic 500; a graceful 503 with a message would be cleaner (backend P3).
- Host SSH SG is locked to a single mobile IP that rotates; re-add the current IP when it changes (or move to SSM Session Manager) — operational note.

## Exit
Phase A: secret-free, all preflights green, commit scope locked (awaiting operator approval). Phase B: live deployment GREEN, co-tenant intact, rollback proven, SSH hardened. Net new fixes this wave set: `.gitignore` env coverage, 2 provision script lines, `__pycache__` cleanup, SSH SG tightening.
