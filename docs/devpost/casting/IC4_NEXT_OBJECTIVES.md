# Wave Set IC4 — G5 remediation close dossier

**Date:** 2026-06-23  
**Preflight:** [IC4_PREFLIGHT.md](IC4_PREFLIGHT.md)  
**Production:** https://orcast-h0.vercel.app · https://pjrftm3bkv.us-west-2.awsapprunner.com

## IC4 verdict

**G5 remediation items H3, H4, and G3-C-01 addressed in code.** Gates CV card shows **caution** when fold-majority passes but mean deviance skill is negative. `docs/API.md` catalogs governance, kernel, explore, and casting routes with corrected auth. Angular landing uses per-route truth badges.

## Finding → fix map

| ID | Finding | Fix | Evidence |
|----|---------|-----|----------|
| G3-D-01 | CV badge pass while `mean_deviance_skill < 0` | [`web/lib/gateDisplay.ts`](../../../web/lib/gateDisplay.ts), [`gates/page.tsx`](../../../web/app/gates/page.tsx), `_enrich_cv_display` in [`kernel.py`](../../../src/aws_backend/routers/kernel.py) | Prod repro: `gate_pass=true`, skill `-0.018`; UI shows **caution** |
| G3-B-02 | `docs/API.md` omits governance endpoints | Expanded [`docs/API.md`](../../API.md) | Doc grep `ic4-doc-grep` |
| G3-C-01 | Uniform "Live API" on `/realtime` | Per-route badges in [`landing.component.ts`](../../../orcast-angular/src/app/components/landing/landing.component.ts) | `/realtime` → **Historical data** |

## Delivered in IC4

| Lane | Deliverable |
|------|-------------|
| IC4-A | `cvDisplayStatus`, caution badge, `display_status` on `/api/gates` CV block |
| IC4-B | API.md sections + IC4 preflight/close dossier |
| IC4-C | Angular `badge--historical`, UI_COPY update |
| IC4-D | `ic4-local`, `ic4-doc-grep` gates |

## Open → IC5

1. **Deploy** H0 Vercel + App Runner image with IC4 UI/API doc changes
2. **`ic-gate` prod smoke** — assert `/api/gates` returns `display_status: caution` on current fit
3. **Optional:** sync `ORCAST_API_KEY` on App Runner (H0 governance curls currently 503)
4. **Optional:** `AI_GATEWAY_API_KEY` on Vercel

## Gate commands

```bash
./tools/waves/run-gate.sh ic4-local
./tools/waves/run-gate.sh ic
./tools/waves/run-gate.sh ic-gate   # after IC5 deploy
./tools/waves/run-gate.sh H0
```

## Registry patch

Mark IC4 `done`; keep `next_wave_set: IC` until IC5 lands.
