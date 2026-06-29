# Wave Set F4 — reprobe dossier and Wave Set G charter

**Date:** 2026-06-23  
**Baseline:** [F0_PROBE_DOSSIER.md](F0_PROBE_DOSSIER.md)  
**Production:** https://orcast-h0.vercel.app · https://pjrftm3bkv.us-west-2.awsapprunner.com

## Wave Set F verdict

**Caveats mediated.** E5-B-1 closed (Postgres not publicly reachable). E5-D-1 and E5-B-2 closed. E5-F-1 **accepted** — deferred to G1 with judge script below. **Wave Set G is unblocked.**

## Caveat verdict table

| E5 ID | Sev | F0 state | F4 verdict | Evidence |
|-------|-----|----------|------------|----------|
| E5-B-1 | P1 | Open — `0.0.0.0/0:5432`, `nc` succeeded | **closed** | RDS `PubliclyAccessible: false`; SG ingress only App Runner connector SG; `f-network-check` PASS (`nc` DNS/timeout from public internet); App Runner `aurora_connected: true` |
| E5-F-1 | P1 | Open — no AI Gateway route | **accepted** | Workshop literal gap documented; Bedrock narration works via App Runner; G1 owns Vercel AI Gateway |
| E5-D-1 | P2 | Open — shared 60/min proxy | **closed** | Proxy: 5 sessions/min + 10 turns/min on explore paths; backend caps 20 sessions/IP/day, 30 turns/session; `f-prod-smoke` observes 429 |
| E5-B-2 | P2 | Open — “Aurora” vs RDS | **closed** | `postgres_engine: rds`; architecture.mmd/png label **RDS PostgreSQL**; CONTRACT + H0 compliance updated |
| E5-A-1 | P2 | OK | **closed** | Re-probe: `exploration/tools.py` still read-only imports; no write router escalation |
| E5-C-1 | P2 | OK | **closed** | `/explore` subtitle still anti-oracle; `/api/gates` status `fitted` |
| E5-E-1 | P2 | OK | **closed** | Dual-DB live: DynamoDB primary + Postgres exploration store; status `exploration_backend: postgres` |

## Open P0/P1

| ID | Status |
|----|--------|
| P0 | none |
| P1 | none open (E5-F-1 accepted for G1) |

## F4 panel reprobe notes

| Panel | Result |
|-------|--------|
| **F4-A** tool loop | PASS — parameterized SQL; tools scope unchanged |
| **F4-B** network | PASS — external `nc` fails; VPC connector egress + SG-to-SG; migrations via App Runner startup |
| **F4-C** abuse | PASS — explore-specific proxy limits + backend quotas; 429 JSON |
| **F4-D** UI truth | PASS — explore copy matches gates API |
| **F4-E** doc truth | PASS — RDS labeling in diagram + status fields |
| **F4-F** workshop AI | ACCEPT — no `/api/explore` AI Gateway; G1 charter below |

## Deploy / ops notes (F2)

| Item | Detail |
|------|--------|
| CFN subnet group | Kept RDS on existing public subnets (in-place subnet move blocked); hardened via `PubliclyAccessible: false` + connector SG |
| VPC egress | App Runner `EgressType: VPC` + endpoints (DynamoDB, S3, Bedrock) |
| DB password | Secrets Manager password contains `#`; use discrete `ORCAST_DB_*` env vars (not URL) |
| Post-deploy | [`sync-apprunner-explore-env.sh`](../../../tools/deployment/aws/sync-apprunner-explore-env.sh) after CFN when exploration DB enabled |
| Cost delta | NAT gateway + interface endpoint (~tens USD/mo); judge transparency item for G |

## Gate evidence (F2 exit)

```bash
./tools/waves/run-gate.sh f        # PASS (2026-06-23)
./tools/waves/run-gate.sh f-gate   # PASS
./tools/waves/run-gate.sh e-gate   # PASS (via f-gate)
./tools/waves/run-gate.sh H0       # PASS
./tools/waves/run-gate.sh i-suite  # PASS
./tools/waves/run-gate.sh P1-gate  # PASS
```

## E5-F-1 judge script (accepted)

> “Exploration narration uses Amazon Bedrock on App Runner with template fallback. Vercel AI Gateway is planned in Wave Set G1 for workshop ‘Wire Up AI’ parity; tool execution and Postgres session writes remain on App Runner by design.”

## Wave Set G objectives

1. **G1 — Vercel AI Gateway + model picker** (was E5-F-1 / old F1)  
   Add `web/app/api/explore/route.ts` with AI SDK + Gateway; keep Aurora/RDS writes on App Runner.

2. **G2 — Explore ↔ map deep links** (old F2)  
   Provenance modal from explore citations; shared viewport URL state across `/` and `/explore`.

3. **G3 — Full P1 surface probe** (old F4)  
   Run P1-A…F panels from [ADVERSARIAL_PROBE_PLAYBOOK.md](../ADVERSARIAL_PROBE_PLAYBOOK.md); file `adversarial-findings-2026-06.md`.

4. **G4 — D1–D4 data wiring** (old F5)  
   Science track; does not block exploration demo.

## Gate commands for Wave Set G entry

```bash
./tools/waves/run-gate.sh f-gate    # regression
./tools/waves/run-gate.sh e-gate
./tools/waves/run-gate.sh H0
./tools/waves/run-gate.sh P1-gate   # after G3 if expanded probe
```

## Registry patch

Set `next_wave_set: G` in [`waves.registry.yaml`](../waves.registry.yaml). Mark F1, F2, F4 `done`; G1–G4 `planned`.
