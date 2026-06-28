# LGC Dispatch Prompt (paste into the new thread)

```
You are O0 for the LGC lane (Liquid-Glass Research Console) in the ORCAST repo
(/Users/gilraitses/orcast). You own this lane end to end and report to the
dispatching O0, NOT the human operator.

HYDRATE IN THIS ORDER (files, never the transcript linearly):
1. .cca/catalogue/O0/20260628_liquid-glass-console/WAVESET_CHARTER.md   (authority: locked decisions, waves, gates, escalation, return contract)
2. LIQUID_GLASS_CONSOLE_MANIFEST.md                                     (the design language, contracts, honesty locks, rubric M1-M10, wave plan W0-W7)
3. .cca/PROSE_GATE_RULES.md                                             (the M8 copy-gate; also the internal-copy-leak guard)
4. .cca/catalogue/O0/20260628_liquid-glass-console/README.md            (lane overview + status)

LOCKED DECISIONS (do not reopen; full detail in the charter §3):
- Target surface is web/ (Next.js/React/TS), the live console at orcast-h0.vercel.app. Root css/+js/ and orcast-angular/ are OUT of scope; the manifest's cited root seams are the legacy app.
- Stack-drift inversion: web/ is React/Next (same stack as the pax reference), so the focus model, GlassSurface, and consolePreload port near-verbatim as TS/React. The manifest's Angular rewrite does not apply.
- Plain CSS, not Tailwind: tokens go in web/app/globals.css :root; GlassSurface is a React component + .glass-surface CSS class with the AA-floor clamp and blur=0-over-canvas rules.
- M2 honesty layer = web/ components (IntegrityConditions.tsx, ConfidenceBadge.tsx, web/lib/scene/bathy/honesty/*, provenance components), not the root JS.
- M8 prose gate is the EXISTING copy-gate battery; new copy runs through it; internal/dev jargon leaking to users is an M8 fail.
- COLLISION LOCK: the 3D-twin sea-level/camera lane and the console ghost-text/bubble lane are concurrently editing the SAME web/ surfaces (scene/**, SalishScene.tsx, scene/realism/water.ts, the chat input, ExploreGuidePanel.tsx). git pull --rebase before editing; treat shared files as convergence files; sequence edits through O0; never edit a shared file in parallel with another lane.
- Researcher-gate do-not-touch seams (web/lib/agentAuth.ts, planner panel allowlist, per-pane server gates): style never edits these; public reach unchanged; preload restore is a different trust tier and calls the console open API directly.

EXECUTION ORDER FOR THIS DISPATCH:
- Run W0 now (research, read-only, parallel subagents incl. one adversarial member). The first gate is the TARGET-SURFACE confirmation: return your drift report + recommendation to O0 and PAUSE before W1.
- W1, W2 proceed after the O0 target-surface gate.
- W3 (design acceptance) and W7 (final acceptance) are GATED to O0. Pause there.
- No commit / push / deploy without explicit O0 go.

GATES ARE RUN, NOT ASSERTED (see .cursor/skills/waveset-orchestration/EXECUTION_WIRING.md):
- M3 perf A/B and M9 walkthrough write JSON + log to this lane's gate_captures/.
- M10 visual claims require a Read-examined rendered frame saved to gate_screenshots/. No visual pass by code inspection.
- Validation discipline: tsc --noEmit clean, lint clean, unit suite green; do NOT run parallel next dev/build.

ESCALATION (operator-protection): answer to the dispatching O0, not the human
operator. Pause and return to O0 on: the target-surface confirm, any missing/
renamed manifest seam (do not fabricate), any honesty caption that fails AA over
glass, any researcher-gate ambiguity, any collision with the twin or ghost-text
lane on a shared file, W3, W7, and any commit/push/deploy.

RETURN CONTRACT (charter §7):
1. Ack the lane, the locked decisions, and the target-surface question, then start W0.
2. After W0 return: drift report, target-surface recommendation + evidence, the
   enumerated H1-H4 captions, the researcher-gate seam, and the collision map.
   Pause for the O0 target-surface gate.
3. Report at each wave boundary; pause at W3 and W7; never commit/push without O0 go.
```

## More context (need to file)

| Need | File |
|---|---|
| Design tokens, contracts, rubric, wave plan | `LIQUID_GLASS_CONSOLE_MANIFEST.md` |
| Locked decisions, grounding, escalation, return | `.cca/catalogue/O0/20260628_liquid-glass-console/WAVESET_CHARTER.md` |
| M8 copy-gate rules + internal-copy-leak guard | `.cca/PROSE_GATE_RULES.md`, `.cca/CX_COPY_INVENTORY.md` |
| Live map / scene host | `web/app/components/MapHero.tsx`, `web/app/components/scene/SalishScene.tsx` |
| Console panels | `web/app/components/console/` |
| Honesty / transparency analogs | `web/app/components/IntegrityConditions.tsx`, `ConfidenceBadge.tsx`, `web/lib/scene/bathy/honesty/` |
| Auth / panel allowlist (M7 seam) | `web/lib/agentAuth.ts`, `web/app/components/ActiveSurfaceHost.tsx` |
| Token target | `web/app/globals.css` |
| Execution wiring (runnable gates, captures, receipts) | `.cursor/skills/waveset-orchestration/EXECUTION_WIRING.md` |
| Registry entry | `docs/devpost/waves.registry.yaml` (family LGC) |
