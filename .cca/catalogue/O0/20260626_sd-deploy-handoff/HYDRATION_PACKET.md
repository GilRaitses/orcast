# Hydration Packet — sd-deploy lane

Read in order. Stop after governance/canon to self-orient, then continue into the lane.

## 1. Governance / canon (read first)
1. [.cca/HYDRATION_PACKET_ORCAST_V1.md](../../../HYDRATION_PACKET_ORCAST_V1.md) — scope canon, repo/runtime map, return contract, do-not-touch list.
2. [.cca/CLAIM_BOUNDARIES.md](../../../CLAIM_BOUNDARIES.md) — allowed vs forbidden claims, canonical numbers (R_uncited 60-100%, page counts).

## 2. This lane's charter + trace
3. `/Users/gilraitses/.cursor/plans/standing_decisions_register_7417d5ac.plan.md` — active plan (SD-H first, then SD-0..SD-4). Not in repo tree.
4. [.cca/SD0_STANDING_DECISIONS_CHARTER.md](../../../SD0_STANDING_DECISIONS_CHARTER.md) — Wave Set SD charter; decision seeds A-L; SDR schema.
5. [HANDOFF_CHARTER.md](HANDOFF_CHARTER.md) — this home's authority doc (locked decisions in §B).
6. [STEP_LOG.md](STEP_LOG.md) — synthesis trace for this lane.

## 3. Evidence for the deploy fix
7. [docs/devpost/DEPLOY_VERCEL.md](../../../docs/devpost/DEPLOY_VERCEL.md) — line 27: Root Directory = web (the design).
8. [vercel.json](../../../vercel.json) — the regression to delete.
9. [web/README.md](../../../web/README.md) — line 53 false claim to correct.
10. [.cca/P2X_CLEANUP_CHARTER.md](../../../P2X_CLEANUP_CHARTER.md) + [.cca/P2X_DEFECT_REGISTER.md](../../../P2X_DEFECT_REGISTER.md) — where D1 (the wrong fix) was recorded.

## 4. Wave status / history
11. [docs/devpost/WAVES_REGISTRY.md](../../../docs/devpost/WAVES_REGISTRY.md) — wave index.
12. [.cca/STEP_LOG.md](../../../STEP_LOG.md) — full campaign log; keyword-search.

## 5. Gates / tooling
13. [tools/waves/run-gate.sh](../../../tools/waves/run-gate.sh) — gate runner (`s-doc-grep`, `a-gate`).

## Repo map (key surfaces)
| Surface | Location | Status |
|---------|----------|--------|
| Vercel frontend | `web/` -> `orcast-h0.vercel.app` | last green deploy live; new builds RED |
| FastAPI backend | `src/aws_backend/` -> App Runner | live |
| Whitepaper 1/2 | `docs/whitepaper/`, `docs/whitepaper2/` | built |
| SDR (to write) | `.cca/STANDING_DECISIONS_REGISTER.md` | does not exist yet |

## Environment notes
- Git identity: `gilraitses@gmail.com` / "Gil Raitses".
- Working tree dirty (~492 paths); commit surgically.
