# Wave Set IC5 — deploy + prod smoke close dossier

**Date:** 2026-06-23  
**Preflight / prior:** [IC4_NEXT_OBJECTIVES.md](IC4_NEXT_OBJECTIVES.md)  
**Production:** https://orcast-h0.vercel.app · https://pjrftm3bkv.us-west-2.awsapprunner.com

## IC5 verdict

**IC3/IC4 changes deployed to H0 Vercel and App Runner.** Prod smoke asserts `display_status: caution` on the current fit and IC4 caution UI strings in the gates bundle. H0 `/gates` shows **Gate: caution** with the fold-majority explainer.

## Deploy record

| Target | Artifact | Result |
|--------|----------|--------|
| App Runner | `orcast-aws-backend:ic5-e50406e` | `display_status=caution` on `GET /api/gates` |
| Vercel H0 | `dpl_F5Vx1KufF9L1gQ3e6jVtgzj2dsmi` | `/gates` caution badge live |

## Gate commands

```bash
./tools/waves/run-gate.sh ic-gate   # PASS 2026-06-23
./tools/waves/run-gate.sh ic4       # regression
./tools/waves/run-gate.sh H0
```

## Open (post-IC5)

1. ~~**Optional:** sync `ORCAST_API_KEY` on App Runner~~ — **done** 2026-06-23 (`set-api-key.sh` + Vercel/GitHub sync; unkeyed writes → 401)
2. ~~**Optional:** set `AI_GATEWAY_API_KEY` on Vercel~~ — **done** 2026-06-23 (`orcast-h0-ic5` key; `GET /api/explore` → `ai_gateway_enabled: true`)
3. **Backend image:** `ic5-20260623-sync` on App Runner (includes `display_status` enrichment)
4. **Wave Set IC:** charter next slice or mark family complete in registry

## Evidence

- Backend: `curl -s $BASE/api/gates | jq '.gates.cross_validation | {gate_pass, mean_deviance_skill, display_status, display_pass}'`
- H0 UI: `/gates` → **Gate: caution** + integrity caveat for negative mean skill
