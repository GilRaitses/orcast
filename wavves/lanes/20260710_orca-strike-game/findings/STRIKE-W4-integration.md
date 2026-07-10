# STRIKE-W4 — integration gate report

**Lane:** `wavves/lanes/20260710_orca-strike-game`  
**Wave:** STRIKE-W4 (integration)  
**Date:** 2026-07-10  
**Orchestrator:** STRIKE-W4 subagent → O0

## Executive summary

W4 migrated the playable scene from `(sandbox)/orca-strike/` into `(game)/orca-strike/`, wired all W3 mechanics into `OrcaStrikeScene.tsx`, and connected the lobby → countdown → active round flow with `ScoreHud` and `TrickCombo`. TypeScript check passes (`cd web && npx tsc --noEmit`, exit 0). Locked files untouched (`orcaPilot/input.ts`, SalishScene, workbench, root nav).

**Go/no-go for Bash.tv ship:** **ACCEPT**

## W4 checklist (10/10)

| # | Item | Status |
|---|------|--------|
| 1 | Frame order: controls.tick → tickPilotFsm → toOrcaPilotInputFromFsm → pilot.update → depth/roll/breach Y → controller.update → applyStrikeRigLayers | Done |
| 2 | Depth clamp 0–25 m via `STRIKE_MIN/MAX_DEPTH_M` + `fsm.depthRateMps` | Done |
| 3 | `tickBreachAirFrame` during `breach_air`; tricks + kayak overlap scored | Done |
| 4 | `breach_land`: splash, replayBuffer push, `shouldStartBreachReplay` → replayCamera + match replay | Done |
| 5 | `blowhole_squirt`: squirt origin, cone hits, spray trigger, kayak score | Done |
| 6 | O-key: `hydrophoneSonar.emitSonar` + `scoreSonarEmit` | Done |
| 7 | Match tick + `ScoreHud` + `TrickCombo` | Done |
| 8 | Spawn lat/lng → metric `projectToScene` scale (`METRIC_SCENE_SCALE`) | Done |
| 9 | Cameras: breach_air → breachCamera; replay → replayCamera; else chase | Done |
| 10 | Route canonical at `(game)/orca-strike/`; sandbox `page.tsx` removed (Next route conflict) | Done |

## Files created / moved / edited

### Created (game route)

| Path | Role |
|------|------|
| `web/app/(game)/orca-strike/OrcaStrikeHost.tsx` | SSR-safe dynamic host with spawn + match props |
| `web/app/(game)/orca-strike/OrcaStrikeScene.tsx` | **W4 integration hub** (STRIKE FSM, scoring, match, cameras) |
| `web/app/(game)/orca-strike/SeaSurface.tsx` | Migrated from sandbox |
| `web/app/(game)/orca-strike/SceneAtmosphere.tsx` | Migrated from sandbox |
| `web/app/(game)/orca-strike/SonarContextMap.tsx` | Migrated from sandbox |
| `web/app/(game)/orca-strike/MobileControlsOverlay.tsx` | Migrated; HUD top offset 12 (no site nav) |
| `web/app/(game)/orca-strike/orcaStrikeTerrainStyle.ts` | Migrated from sandbox |

### Edited

| Path | Change |
|------|--------|
| `web/app/(game)/orca-strike/page.tsx` | Lobby → game scene mount; `startCountdown` on Start |
| `web/app/(game)/orca-strike/layout.tsx` | Unchanged (fullscreen stub) |
| `web/app/(game)/orca-strike/hud/ScoreHud.tsx` | Consumed by page overlay |
| `web/app/(game)/orca-strike/hud/TrickCombo.tsx` | Consumed by page overlay |

### Deleted

| Path | Reason |
|------|--------|
| `web/app/(sandbox)/orca-strike/page.tsx` | Next.js route conflict with `(game)/orca-strike/page.tsx` at `/orca-strike` |

### Left in sandbox (orphan, not routed)

| Path | Notes |
|------|-------|
| `web/app/(sandbox)/orca-strike/OrcaStrikeScene.tsx` | Superseded; O0 may delete in cleanup commit |
| `web/app/(sandbox)/orca-strike/OrcaStrikeHost.tsx` | Superseded |
| `web/app/(sandbox)/orca-strike/orcaStrikeInput.ts` | Superseded by `createStrikeControlsSampler` |

## Compile verification

```
cd web && npx tsc --noEmit
exit code: 0
```

Note: removed stale `.next/types/app/(sandbox)/orca-strike/page.ts` after deleting sandbox page (cache artifact only).

## Integration notes for O0

1. **Spawn projection:** `latLngToMetricSceneXZ` scales `projectToScene` output by `TILESET_METRIC_DIAMETER_UNITS / SCENE_WIDTH` so lobby picks align with the metric tileset fit.
2. **Place targets for F/O sonar:** gazetteer blips scaled to metric before `buildRadarTargets` / `scoreSonarEmit` candidates.
3. **Space key:** breach mash only via `createStrikeControlsSampler`; Space-climb listener removed.
4. **Match return to lobby:** `tickMatch` → `returnToLobby` after results overlay; page clears game mount when `match.phase === "lobby"`.
5. **Visual verify still needed:** breach replay camera, blowhole VFX particles, hydrophone m4a runtime (W2 graceful skip if missing).

## Forbidden actions (confirmed)

- Did not edit `web/lib/scene/orcaPilot/input.ts`
- Did not edit SalishScene, workbench, root layout nav
- Did not run git

## O0 commit guidance (Bash.tv repo-pull)

Suggested commit scope:

- `web/app/(game)/orca-strike/**` (all new + edited scene/lobby/hud)
- Delete `web/app/(sandbox)/orca-strike/page.tsx`
- Optional cleanup: remove remaining `(sandbox)/orca-strike/` duplicates
- `wavves/lanes/20260710_orca-strike-game/findings/STRIKE-W4-integration.md`

Ship target: Bash.tv standalone build at `/orca-strike`.
