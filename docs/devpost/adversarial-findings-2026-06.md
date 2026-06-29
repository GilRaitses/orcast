# Adversarial findings — Wave Set G3 (2026-06-23)

**Probe:** P1-A through P1-F per [ADVERSARIAL_PROBE_PLAYBOOK.md](ADVERSARIAL_PROBE_PLAYBOOK.md)  
**Live:** https://orcast-h0.vercel.app · https://pjrftm3bkv.us-west-2.awsapprunner.com

## Remediation in Wave Set G (code)

| ID | Fix |
|----|-----|
| **G3-RCE-01** | `src/aws_backend/auth.py` — production always requires `X-ORCAST-Key` on keyed routes; governance writes require `X-ORCAST-Trusted-Proxy: vercel` + reviewer id |
| G3-F-02 | `promotion/apply` now uses `require_trusted_reviewer` |
| G3-F-01 | Unredacted dossier export requires reviewer id in production |

**Deploy required** before prod reprobe closes P0.

## P0 (pre-remediation)

| ID | Finding |
|----|---------|
| G3-RCE-01 | Direct App Runner calls bypassed WorkOS when `ORCAST_API_KEY` check was no-op and trusted-proxy was optional |
| G3-A-02 | `GET /api/community/submissions` exposed PII without key |
| G3-F-01 | Unredacted audit export without sign-in on direct backend |

## P1 (open backlog)

| ID | Finding | Lane |
|----|---------|------|
| G3-D-01 | CV gate badge shows pass while `mean_deviance_skill` negative | Gates UI |
| G3-B-02 | `docs/API.md` omits governance endpoints | Docs |
| G3-C-01 | CloudFront landing “Live API” on historical `/realtime` | Angular pilot |
| G3-F-03 | Append-only decision records allow audit spam | Rate limit / binding |

## P2 (backlog)

In-memory Vercel rate limits; partner dev key shared secret; `file://` artifact URIs in fit report; CloudFront Maps key in HTML.

## False positives rejected

- H0 proxy blocks unauthenticated governance writes (401 confirmed)
- Partner gateway rejects missing keys (401)
- Double moderation approve returns 409
- Task tokens stripped from public `/api/gates`

## Gate

After backend deploy with auth hardening:

```bash
./tools/waves/run-gate.sh g-gate
./tools/waves/run-gate.sh P1-gate
```

Manual reprobe: direct App Runner `POST /api/decision-records` with spoofed headers must return **401**.
