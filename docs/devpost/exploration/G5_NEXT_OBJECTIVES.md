# Wave Set G5 — next objectives (post Wave Set G)

**Date:** 2026-06-23  
**Baseline:** Wave Set G (G1–G4)

## G verdict

**Ship with follow-ups.** G1 AI Gateway route + model picker, G2 viewport deep links, G3 adversarial dossier, G4 data wiring assessment delivered. **Deploy auth hardening (G3 P0) before judging governance.**

## Completed in G

| ID | Deliverable |
|----|-------------|
| G1 | `web/app/api/explore/route.ts` — Vercel AI Gateway + model picker; App Runner `prepare` + `gateway_reply` persist |
| G2 | Shared `?lat=&lng=&provenance=1` across `/` and `/explore`; provenance modal from explore deep links |
| G3 | [adversarial-findings-2026-06.md](../adversarial-findings-2026-06.md) + auth hardening |
| G4 | [G4_DATA_WIRING_STATUS.md](../G4_DATA_WIRING_STATUS.md) |

## Open items → Wave Set H

1. **H1 — Deploy + reprobe G3 P0** — backend image with auth fix; verify direct App Runner governance calls fail
2. **H2 — Set `AI_GATEWAY_API_KEY` on Vercel** — enable live Gateway narration (falls back to Bedrock via App Runner today)
3. **H3 — Gates UI honesty** — CV pass badge vs negative skill (G3-D-01)
4. **H4 — Docs truth** — governance routes in `docs/API.md`; CloudFront “Live API” copy
5. **H5 — D3/D4 completion** — OrcaHello backfill resilience; bathymetry L3 asset

## Gate commands

```bash
./tools/waves/run-gate.sh g
./tools/waves/run-gate.sh g-gate
./tools/waves/run-gate.sh f-gate
./tools/waves/run-gate.sh H0
```

## Registry patch

Set `next_wave_set: H`; mark G1–G4 `done`.
