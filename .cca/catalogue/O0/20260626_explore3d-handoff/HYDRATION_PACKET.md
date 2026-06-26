# Hydration Packet — explore3d lane

Read in order. Stop after governance/canon to self-orient, then continue into the lane. Hydrate from files, not the chat transcript.

## 1. Authority / plan (read first)
1. `/Users/gilraitses/.cursor/plans/explore_3d_narrator_a0fcc729.plan.md` — the authoritative plan (two workstreams, P0/P1/P2, todos). Not in repo tree.
2. [HANDOFF_CHARTER.md](HANDOFF_CHARTER.md) — locked decisions (§B).
3. [docs/devpost/casting/ORCHESTRATOR_NARRATOR_FRAMEWORK.md](../../../../docs/devpost/casting/ORCHESTRATOR_NARRATOR_FRAMEWORK.md) — orchestrator<->narrator contract.

## 2. Canon
4. [.cca/CLAIM_BOUNDARIES.md](../../../CLAIM_BOUNDARIES.md) — allowed/forbidden claims, canonical values.
5. [.cca/STANDING_DECISIONS_REGISTER.md](../../../STANDING_DECISIONS_REGISTER.md) — decision-of-record (esp. SD-001 orchestrator-in-the-loop; SD-011 deploy; O-1..O-4).

## 3. Backend orchestration / casting (the piece being reworked)
6. [src/aws_backend/casting/](../../../../src/aws_backend/casting/) — registry, concierge, planner, skills, panel_registry.json, seeds/*.json.
7. [src/aws_backend/routers/interactions.py](../../../../src/aws_backend/routers/interactions.py) — `/api/interactions`, `/prepare`, `/plan` (note: `/plan` supports `narrate:true`, does NOT persist yet).
8. [docs/devpost/casting/MANAGED_AGENTS_CONTRACT.md](../../../../docs/devpost/casting/MANAGED_AGENTS_CONTRACT.md), [UI_INTENT_SCHEMA.md](../../../../docs/devpost/casting/UI_INTENT_SCHEMA.md), [INTERACTIONS_GROUNDING_PATTERN.md](../../../../docs/devpost/casting/INTERACTIONS_GROUNDING_PATTERN.md), [IC8_NEXT_OBJECTIVES.md](../../../../docs/devpost/casting/IC8_NEXT_OBJECTIVES.md).

## 4. Web surfaces (the UI being replaced)
9. [web/app/components/ExploreGuidePanel.tsx](../../../../web/app/components/ExploreGuidePanel.tsx) — dated static UI to retire.
10. [web/app/components/ActiveSurfaceHost.tsx](../../../../web/app/components/ActiveSurfaceHost.tsx) + [web/lib/uiIntent.ts](../../../../web/lib/uiIntent.ts) — console panels (thin today) to rebuild.
11. [web/app/components/MapHero.tsx](../../../../web/app/components/MapHero.tsx) — Google Maps surface (fallback only).
12. [web/app/components/Nav.tsx](../../../../web/app/components/Nav.tsx) — hard-coded nav to replace.
13. [web/app/api/be/[...path]/route.ts](../../../../web/app/api/be/[...path]/route.ts) — proxy public/protected allowlists; expose `/api/interactions/plan` publicly.
14. [web/app/page.tsx](../../../../web/app/page.tsx) — landing to rebuild as the explore-first shell.

## 5. Data sources
15. [docs/data-procurement/ACCESS_WALKTHROUGH.md](../../../../docs/data-procurement/ACCESS_WALKTHROUGH.md) — (to be written) ONC + deferred-platform access steps.
16. `/api/be/api/live-hydrophones` + Orcasound roster; `data/geo/san_juan_bathymetry.json` + island mask (3D terrain seed).
17. ONC Oceans 3.0 API: discovery `locations?deviceCategoryCode=HYDROPHONE`, `archivefile` (spectrogram PNG / `dataProductCode=HSD`), SeaTube annotations (product 126). Token via `ONC_API_TOKEN` env only.

## 6. Tooling / deploy
18. Deploy = Git push -> `orcast-h0` (Root Directory=`web`). Verify: build green + `/` 200 + adaptive turn + hydrophone fetch.
19. [tools/waves/run-gate.sh](../../../../tools/waves/run-gate.sh) — gates; video gate must be re-run after demo re-record.

## Environment notes
- Git identity: `gilraitses@gmail.com` / "Gil Raitses"; surgical commits only; do not push without operator ask.
- `ONC_API_TOKEN` is a secret: env/secret only, never committed; rotate after hackathon.
- Working tree dirty (~492 paths).
