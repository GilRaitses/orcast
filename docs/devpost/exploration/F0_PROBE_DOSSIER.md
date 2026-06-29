# F0 — deep probe dossier

**Date:** 2026-06-23  
**Baseline:** [E5_NEXT_OBJECTIVES.md](E5_NEXT_OBJECTIVES.md)  
**Live RDS:** `orcast-aws-backend-explore.cjymkcu2uzi1.us-west-2.rds.amazonaws.com`

## F0-A — tool loop / write escalation

| Field | Value |
|-------|--------|
| Severity | P2 (confirmed OK) |
| Evidence | `exploration/tools.py` imports `kernel_model.serve`, `routers.kernel` helpers only; no `community`, `promotion`, or `write` routers |
| Abuse | `ExploreTurnRequest.message` passed to Bedrock/template; SQL uses `%s` placeholders in `session_store.py` |
| Exploit story | Cannot approve moderation or inject SQL via explore API without separate auth bypass |
| Lane | F1-A not required; F4 re-probe |

## F0-B — Postgres network exposure (P1)

| Field | Value |
|-------|--------|
| Severity | **P1** |
| Evidence | CFN `ExplorationDbSecurityGroup` ingress `CidrIp: 0.0.0.0/0` port 5432; `PubliclyAccessible: true` |
| Repro | `nc -zv orcast-aws-backend-explore.cjymkcu2uzi1.us-west-2.rds.amazonaws.com 5432` → **Connection succeeded** (2026-06-23) |
| Exploit story | Any host can attempt Postgres auth if password leaks from Secrets Manager or brute-force |
| Lane | **F1-A** |

## F0-C — explore abuse / cost (P2)

| Field | Value |
|-------|--------|
| Severity | P2 |
| Evidence | Single 60/min IP bucket in `web/app/api/be/[...path]/route.ts`; no backend session cap |
| Exploit story | Attacker creates many sessions + turns; each turn invokes Bedrock until global 429 |
| Lane | **F1-B**, **F1-C** (retention limits blast radius) |

## F0-D — UI overclaim (P2)

| Field | Value |
|-------|--------|
| Severity | P2 (OK) |
| Evidence | `/explore` subtitle: "not a separate AI oracle"; live `/api/gates` status `fitted` |
| Lane | F4 re-probe only |

## F0-E — doc truth (P2)

| Field | Value |
|-------|--------|
| Severity | P2 |
| Evidence | Status fields say `aurora_*`; architecture.mmd label "Aurora PostgreSQL"; production engine is **RDS Postgres 16.14** |
| Lane | **F1-D** |

## F0 summary

| Open P1 | Lane |
|---------|------|
| E5-B-1 | F1-A |
| E5-F-1 | Defer G1 |

Proceed to F1 parallel remediation.
