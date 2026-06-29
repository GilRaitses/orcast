# Wave Set E — adversarial validation dossier

**Date:** 2026-06-23  
**Scope:** Exploration guide (Aurora/RDS + `/explore` + `/api/explore/*`)  
**Live checks:** `./tools/waves/run-gate.sh e-gate` and `H0` green on https://orcast-h0.vercel.app

## Wave Set E verdict

**Ship with caveats.** No P0 blockers for hackathon demo. Two P1 items (Postgres network exposure, missing AI Gateway) and several P2 follow-ups for Wave Set F.

## Findings table

| ID | Severity | Panel | Evidence | Exploit / impact story |
|----|----------|-------|----------|------------------------|
| E5-B-1 | P1 | E5-B | [`infra/aws/template.yaml`](../../infra/aws/template.yaml) — `ExplorationDbSecurityGroup` ingress `0.0.0.0/0:5432` | Postgres reachable from any IP if credentials leak; brute-force surface |
| E5-D-1 | P2 | E5-D | [`web/app/api/be/[...path]/route.ts`](../../web/app/api/be/[...path]/route.ts) — 60 req/min per IP, shared with all public POSTs | Explore turn spam could exhaust Bedrock budget before rate limit |
| E5-A-1 | P2 | E5-A | [`exploration/tools.py`](../../src/aws_backend/exploration/tools.py) — imports kernel helpers only; no HTTP write tools | Tool loop cannot call moderation/promotion (verified by scope) |
| E5-C-1 | P2 | E5-C | [`web/app/explore/page.tsx`](../../web/app/explore/page.tsx) — "not a separate AI oracle" subtitle | Copy aligns with anti-oracle thesis |
| E5-E-1 | P2 | E5-E | [`architecture.png`](../figures/architecture.png) — Aurora box labeled "not system of record" | Dual-DB story matches live `/explore/status` (`aurora_connected: true`) |
| E5-F-1 | P1 | E5-F | No `web/app/api/explore/route.ts` AI Gateway route | Workshop "Wire Up AI" literal gap remains (Bedrock via App Runner only) |
| E5-B-2 | P2 | E5-B | RDS `db.t4g.micro` public + IGW (not Aurora Serverless) | Docs updated honestly; workshop says Aurora |

## Remediation waves

| Finding | Remediation lane | Action |
|---------|------------------|--------|
| E5-B-1 | F3-network | VPC connector + private RDS + SG limited to App Runner egress |
| E5-F-1 | F1-gateway | Vercel AI Gateway route; generation only, tools stay on App Runner |
| E5-D-1 | F2-rate | Separate explore rate bucket or session cap per IP/day |

## Next wave set F objectives (ranked)

1. **F1 — AI Gateway + model picker (workshop literal)**  
   Add `web/app/api/explore/route.ts` with Vercel AI SDK + AI Gateway; keep Aurora writes on App Runner. Optional UI model picker env toggle.

2. **F2 — Exploration ↔ map deep links (U-wave tie-in)**  
   Open provenance modal from explore citations; preserve viewport in URL state across `/` and `/explore`.

3. **F3 — Postgres hardening**  
   Replace public RDS SG with App Runner VPC connector; rotate credentials; add session retention + IP hash TTL policy.

4. **F4 — General P1 surface probe**  
   Run full P1-A…F panels from [ADVERSARIAL_PROBE_PLAYBOOK.md](../ADVERSARIAL_PROBE_PLAYBOOK.md); file `adversarial-findings-2026-06.md`.

5. **F5 — Data wiring D1–D4**  
   Science track; does not block exploration demo.

## Gate commands for Wave Set F entry

```bash
./tools/waves/run-gate.sh e-gate    # regression
./tools/waves/run-gate.sh H0
./tools/waves/run-gate.sh P1-gate   # after F4 panels
```

## Production evidence (E4)

| Check | Result |
|-------|--------|
| CFN `EnableExplorationDatabase=true` | Stack `orcast-aws-backend` UPDATE_COMPLETE |
| RDS endpoint | `orcast-aws-backend-explore.cjymkcu2uzi1.us-west-2.rds.amazonaws.com` |
| Migration `001_initial.sql` | Applied |
| Backend `/api/explore/status` | `aurora_connected: true` |
| H0 live turn | `e-gate` session + turn PASS |
| Vercel `/explore` | Deployed to orcast-h0.vercel.app |

## Registry patch

Set `next_wave_set: F` in [`waves.registry.yaml`](../waves.registry.yaml). Mark E3–E5 `done`.
