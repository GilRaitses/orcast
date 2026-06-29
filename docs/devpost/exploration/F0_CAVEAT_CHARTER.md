# Wave Set F — caveat mediation charter

Maps every [E5_NEXT_OBJECTIVES.md](E5_NEXT_OBJECTIVES.md) finding to acceptance tests, owner lane, and closed definition.

## Exit bar

Wave Set **G** starts only when F4 dossier shows **zero open P1** caveats (E5-B-1, E5-F-1 deferred to G1).

| E5 ID | Sev | Owner lane | Closed when |
|-------|-----|------------|-------------|
| E5-B-1 | P1 | F1-A | External `nc` to RDS:5432 fails; App Runner `aurora_connected: true` |
| E5-F-1 | P1 | G1 | Deferred — documented in F4 as open until G1 |
| E5-D-1 | P2 | F1-B | Explore 429 before global 60/min; backend session/turn caps enforced |
| E5-B-2 | P2 | F1-D | Docs/diagram say RDS Postgres; status includes `postgres_engine: rds` |
| E5-A-1 | P2 | F4 reprobe | No write-tool escalation (re-verify) |
| E5-C-1 | P2 | F4 reprobe | UI copy still anti-oracle (re-verify) |
| E5-E-1 | P2 | F4 reprobe | Dual-DB story matches prod (re-verify) |

## Acceptance commands

```bash
# E5-B-1 (before F1-A fix — should succeed; after — must fail)
nc -zv -w 3 "$EXPLORATION_RDS_HOST" 5432

# E5-B-1 (after F1-A)
./tools/waves/run-gate.sh f-network-check

# E5-D-1
./tools/waves/gates/f-prod-smoke.sh   # includes abuse 429 check

# Regression
./tools/waves/run-gate.sh f
./tools/waves/run-gate.sh e-gate
./tools/waves/run-gate.sh H0
```

## F-family waves

| ID | Type | Deliverable |
|----|------|-------------|
| F0 | probe | [F0_PROBE_DOSSIER.md](F0_PROBE_DOSSIER.md) |
| F1 | implement | Parallel lanes F1-A…E |
| F2 | deploy | CFN + migrations + Vercel |
| F4 | reprobe | [F4_NEXT_OBJECTIVES.md](F4_NEXT_OBJECTIVES.md) |
