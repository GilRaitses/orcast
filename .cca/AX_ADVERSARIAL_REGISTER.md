# AX Adversarial Final-Gate Register (AX + CX)

Date: 2026-06-27. Lane: O0 adversarial-final-gate. Pre-P1 gate.
Companion: `.cca/CX_COPY_INVENTORY.md`, `.cca/PROSE_GATE_RULES.md`, `.cca/DEPLOY_DEMO_DECISIONS.md`, `.cca/GP_GAP_REGISTER.md`.

Verdict legend: PASS / FIXED / FLAG.

## AX lane verdicts

| Lane | Verdict | Result |
|---|---|---|
| AX-0 recon | PASS | live surface mapped; App Runner RUNNING + SSM Online rollback assets confirmed |
| AX-1 authZ | FIXED (P0) | evidence/journal reachable on the public tunnel via spoofed `X-ORCAST-Reviewer-Id` (200, PII). Fixed with router-level `require_api_key` (`d866e48`); re-verified 401; key-protected control stayed 401 |
| AX-2 ONC/planner | FLAG | ONC archivefile SSRF inert in prod (disabled -> 503 before any fetch). Validate `filename` before enabling ONC |
| AX-3 abuse/rate-limit | PASS | session limit 429 after 5; global 60/min triggers (15/75 -> 429); pax co-tenant intact under load |
| AX-4 resilience | PASS | App Runner rollback 200; orcast self-heal ~6s; pax isolation; cloudflared active; RDS path fails soft (503 both paths after DD-6 completion) |
| AX-5 secrets/IAM | PASS | no secrets in source or git history (pickaxe 0); S3 data buckets fully public-blocked; host-role least-privilege |
| AX-6 data integrity | PASS | q1c + q1b PASS; i-suite deferred to host/CI |
| AX-7 claim integrity | PASS | web forbidden-claims clean; a-gate PASS (SD-025); figures PP2 prior-done |
| AX-8 gate sweep | PASS | selfhost-gate/q1b/q1c PASS; s-doc-grep only known O-2 reds; no new failures |

## CX prose sweep

copy-gate (`tools/waves/gates/copy-gate.sh`) GREEN: 0 em-dashes across all
audience-facing surfaces (web, whitepaper sections, deck sections, outreach, demo
scripts, SUBMISSION). Whitepaper PDFs rebuilt via SD-019 (WP1 10/7, WP2 5/4).
Canon: `.cca/PROSE_GATE_RULES.md` + `.cursor/rules/prose-gate.mdc`.

## Fixes applied this campaign

- P0 auth bypass: `require_api_key` on evidence + journal routers (`d866e48`).
- DD-5: interest raw-payload persistence (`fde3181`).
- DD-6 + completion: graceful 503 on RDS-unreachable explore, both keyed and unkeyed paths (`9b59e12`, `87ff466`).
- Em-dash removal: class A web+backend (`fde3181`) and class B whitepapers/outreach/demo/SUBMISSION (`3c74c35`, `644a486`, `654ef0f`).
- Adaptive interest signup with live delivery + drafted email (`e1fa4fd`).
- SES wired: aimez.ai verified+DKIM, host `ses:SendEmail`, `ORCAST_SES_SENDER=noreply@aimez.ai`, `email_delivered:true` to verified recipient.
- Build fix: r3f deps + heightmap so the explore3d landing ships (`1696b1b`).
- Earlier GP: SSH closed in favor of SSM-only access.

## AX-9 tracked-limits dossier (operator approval gate)

| Limit | Risk | Blast radius | Disposition |
|---|---|---|---|
| SES sandbox (email only to verified recipients) | medium | interest email to public signups does not send (inline link delivery works) | mitigate: submit SES production-access request (operator AWS ticket) |
| RDS explore unreachable from host | low | explore-session persistence degraded; graceful 503 | accept (parity); future VPC peering |
| ONC disabled in prod | low | hydrophone panel metadata-only | accept; enable on demand after `filename` validation (AX-2) |
| App Runner kept RUNNING as rollback (~$70-85/mo) | low | cost only | accept until post-submission, then pause (DD-3) |
| Host access SSM-only, no SSH fallback | low | access depends on SSM | accept (more secure); re-add SSH via API if SSM degrades |
| Voiceover not prose-gated (recorded audio) | low | demo narration may contain spoken em-dash phrasing | accept for now; re-record is heavy (out of scope) |
| Audit-deck `.tex` untracked-internal | low | not in repo / not judge-facing | accept; cleaned locally, not committed |
| SDR O-2/O-3/O-4 drift | low/medium | internal gate reds + claim drift | accept; existing SDR open items |
| Demo GIFs (Wave Set MX) | medium | gallery placeholders | open (operator/agent-assist) |

## Open operator gates (post-waveset)

- SES production-access request (to email arbitrary signups).
- P1 submission gates (OX): DynamoDB console screenshot, Devpost submission, arXiv upload.
- Post-submission: pause App Runner (DD-3).

## Exit

AX adversarial lanes and the CX prose sweep are clean (one P0 found and fixed; no
open P0/P1 from the campaign). Every tracked limit is dispositioned above. P1 stays
parked pending operator approval of these limits and the OX submission gates.
