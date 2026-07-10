# STRIKE — standalone product boundary

- **Date:** 2026-07-10
- **Lane:** wavves/lanes/20260710_orca-strike-game
- **Operator pick:** Build Orca Strike as a **standalone game shell**, not
  wrapped in the main orcast site chrome. Later migration into the primary
  site is allowed; **this lane must not** couple to workbench, SalishScene,
  primary nav, or honesty-legend flows.
- **Locked routes:**
  - Game home: `web/app/(game)/orca-strike/` with its own `layout.tsx`
    (fullscreen, no `SiteNav` / Forecast / Explore links).
  - Public URL target: `/orca-strike` (same path; route group change only).
- **Forbidden edits (unless O0 explicitly reopens):**
  - `web/app/components/scene/SalishScene.tsx`
  - `web/app/workbench/**`
  - `web/app/layout.tsx` global nav wiring for game features
  - Any honesty-legend or measured-claim UI inside the game HUD
- **Allowed reuse (library import only):**
  - `web/lib/scene/orca/**`, `tiles/`, `geo/gazetteer.ts`, `realism/` palette
  - Existing HUNT modules: `orcaPilot/`, `boats/`, `sonar/` (extend, do not
    fork unless disjoint new behavior)
