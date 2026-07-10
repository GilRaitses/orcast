# STRIKE-W3 — core mechanics gate report

**Lane:** `wavves/lanes/20260710_orca-strike-game`  
**Wave:** STRIKE-W3 (core mechanics)  
**Date:** 2026-07-10  
**Orchestrator:** STRIKE-W3 subagent → O0

## Executive summary

All W3 deliverables (W3a–W3f) are implemented. Pure mechanics modules compile under `web/lib/scene/orcaStrike/`; lobby/HUD shells live under `web/app/(game)/orca-strike/`. TypeScript check passes (`cd web && npx tsc --noEmit`, exit 0). No locked files edited (`orcaPilot/input.ts`, `OrcaStrikeScene.tsx`, SalishScene, workbench, nav). `OrcaStrikeScene.tsx` was not wired; W4 owns integration.

**Go/no-go for W4:** **GO**

## Files created / updated

### W3a — pilot FSM + rig blend

| Path | Role |
|------|------|
| `web/lib/scene/orcaStrike/pilotStateMachine.ts` | 12-mode FSM, `tickPilotFsm`, rig blend table, `applyStrikeRigLayers` |
| `web/lib/scene/orcaStrike/types.ts` | Extended: `PilotFsmOutput`, `RigBlendWeights`, `MotionOverrides`, match/scoring types |
| `web/lib/scene/orcaStrike/inputAdapter.ts` | `toOrcaPilotInputFromFsm`, FSM adapter consumption |

### W3b — scoring + match

| Path | Role |
|------|------|
| `web/lib/scene/orcaStrike/scoring.ts` | Locked score table, once-per-round keys, trick combo multipliers |
| `web/lib/scene/orcaStrike/match.ts` | lobby/countdown/active/replay/ended, 180s timer, deck win |

### W3c — breach

| Path | Role |
|------|------|
| `web/lib/scene/orcaStrike/breach.ts` | Mash, launch impulse, air tricks, kayak AABB, deck landing, replay hook, `tickBreachAirFrame` |

### W3d — blowhole

| Path | Role |
|------|------|
| `web/lib/scene/orcaStrike/blowhole.ts` | Charge/decay, squirt cone hitbox, kayak overlap |

### W3e — sonar scoring

| Path | Role |
|------|------|
| `web/lib/scene/orcaStrike/sonarScoring.ts` | `sonar_new_blip` +50, blip reveal by pulse radius; `hydrophoneSonar.ts` unchanged (W2 API complete) |

### W3f — lobby / HUD shells

| Path | Role |
|------|------|
| `web/app/(game)/orca-strike/layout.tsx` | Fullscreen stub, no site nav |
| `web/app/(game)/orca-strike/page.tsx` | Lobby preview entry |
| `web/app/(game)/orca-strike/lobby/OrcaSelect.tsx` | 3 orca skin options |
| `web/app/(game)/orca-strike/lobby/SpawnPicker.tsx` | Island tabs + click map spawn |
| `web/app/(game)/orca-strike/lobby/LobbyShell.tsx` | Composes select + spawn + Start |
| `web/app/(game)/orca-strike/hud/ScoreHud.tsx` | Score + MM:SS timer |
| `web/app/(game)/orca-strike/hud/TrickCombo.tsx` | Air trick indicator stub |

### Barrel

| Path | Role |
|------|------|
| `web/lib/scene/orcaStrike/index.ts` | Exports all W3 modules |

## Compile verification

```
cd web && npx tsc --noEmit
exit code: 0
```

## W4 integration checklist

1. **Frame order** (per STRIKE-W1b): `controls.tick` → `tickPilotFsm` → `toOrcaPilotInputFromFsm` → `pilot.update` → apply depth rate + roll + breach world Y → `controller.update` → `applyStrikeRigLayers`.
2. **Depth clamp:** integrate `fsm.depthRateMps` into `pose.depthM`, clamp 0–25 m (`STRIKE_MIN/MAX_DEPTH_M`).
3. **Breach air:** during `breach_air`, call `tickBreachAirFrame`; score tricks via `applyMatchScoreEvent`; kayak hits → `breach_over_kayak`.
4. **Breach land:** on `breach_land` transition, `triggerBreachSplash`, `replayBuffer.push` history; if `shouldStartBreachReplay`, `createReplayCamera().start` + `match` replay phase.
5. **Blowhole:** on `blowhole_squirt` entry, `computeSquirtOrigin` + `checkSquirtConeHits` + `triggerBlowholeSpray`; score `blowhole_hit_kayak`.
6. **O sonar:** on `ctrl.sonarEmit`, `hydrophoneSonar.emitSonar` + `scoreSonarEmit` with radar blip candidates.
7. **Match:** lobby `LobbyShell` → `startCountdown` → `tickMatch` each frame; mount `ScoreHud` + `TrickCombo`.
8. **Spawn:** `StrikeSpawnSelection` lat/lng → `projectToScene` with tileset bounds + `defaultDepthM`.
9. **Cameras:** `breach_air` → `breachCamera`; replay phase → `replayCamera`; else chase cam.
10. **Route:** migrate sandbox scene into `(game)/orca-strike/`; deploy Bash.tv target.

## Module contracts (quick reference)

| Export | Consumer |
|--------|----------|
| `tickPilotFsm(dt, ctrl, state, pose)` | Scene useFrame |
| `toOrcaPilotInputFromFsm(raw, ctrl, fsm.output)` | Before `pilot.update` |
| `applyStrikeRigLayers(rig, fsm.output, sec)` | After `controller.update` |
| `tickMatch(match, { dt, scoreResults })` | Scene + HUD |
| `tickBreachAirFrame` | During `breach_air` only |
| `scoreSonarEmit` | O-key handler |

## Escalations

| Item | Severity | Notes |
|------|----------|-------|
| Hydrophone m4a on disk | Runtime | Same W2 note; `emitSonar` graceful skip if missing |
| Island thumb PNGs | Cosmetic | Paths declared; lobby uses canvas gradient |
| `(game)` vs `(sandbox)` URL | W4 | Both may coexist until W4 migrates `/orca-strike` host |
| `projectToScene` vs metric tileset fit | W4 | Spawn picker stores lat/lng; scene must use same projection as `OrcaStrikeScene` tileset fit |
| Visual verify | W4 | FSM articulation, breach replay, blowhole score require scene screenshots |

## Forbidden actions (confirmed)

- Did not edit `web/lib/scene/orcaPilot/input.ts`
- Did not edit `OrcaStrikeScene.tsx`
- Did not edit SalishScene, workbench, root layout nav
- Did not run git

## Acceptance alignment

| STRIKE-ACCEPT item | W3 status |
|--------------------|-----------|
| Q/E/A/D/S/W controls | FSM + adapter ready; scene wire W4 |
| FSM articulation | `pilotStateMachine` + `applyStrikeRigLayers` ready |
| Breach replay | `breach.ts` replay hook + W2 `replayBuffer`/cameras ready |
| Blowhole kayak score | `blowhole.ts` cone + `scoring.ts` ready |
| O sonar | `hydrophoneSonar` + `sonarScoring` ready |
| Spawn picker | `SpawnPicker.tsx` + 3 islands |
| Standalone shell | `(game)/orca-strike/layout.tsx` stub |
| Deploy Bash.tv | Out of W3 scope |
