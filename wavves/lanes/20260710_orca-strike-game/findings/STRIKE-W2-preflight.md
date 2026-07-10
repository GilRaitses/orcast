# STRIKE-W2 — preflight assets gate report

**Lane:** `wavves/lanes/20260710_orca-strike-game`  
**Wave:** STRIKE-W2 (preflight assets)  
**Date:** 2026-07-10  
**Orchestrator:** STRIKE-W2 subagent → O0

## Executive summary

All W2 deliverables (W2a–W2e) are created under `web/lib/scene/orcaStrike/`. TypeScript compile (`cd web && npx tsc --noEmit`) passes with exit code 0. Island definitions sit inside the HUNT tileset envelope; crop helpers produce valid 0–1 normalized coords at island centers. No edits were made to locked files (`orcaPilot/input.ts`, `OrcaStrikeScene.tsx`, SalishScene, workbench, nav).

**Go/no-go for W3:** **GO** — pure modules compile, contracts match W1b/W1d, no blockers except optional hydrophone m4a fetch at runtime (documented).

## Deliverables created

| Sub-wave | Path | Status |
|----------|------|--------|
| W2a | `web/lib/scene/orcaStrike/islands/definitions.ts` | Done |
| W2a | `web/lib/scene/orcaStrike/islands/maps.ts` | Done |
| W2b | `web/lib/scene/orcaStrike/hydrophoneSonar.ts` | Done |
| W2c | `web/lib/scene/orcaStrike/vfx/breachSplash.ts` | Done |
| W2c | `web/lib/scene/orcaStrike/vfx/blowholeSpray.ts` | Done |
| W2d | `web/lib/scene/orcaStrike/replayBuffer.ts` | Done |
| W2d | `web/lib/scene/orcaStrike/cameras/breachCamera.ts` | Done |
| W2d | `web/lib/scene/orcaStrike/cameras/replayCamera.ts` | Done |
| W2e | `web/lib/scene/orcaStrike/controls.ts` | Done |
| W2e | `web/lib/scene/orcaStrike/inputAdapter.ts` | Done |
| shared | `web/lib/scene/orcaStrike/types.ts` | Done |
| barrel | `web/lib/scene/orcaStrike/index.ts` | Done |

## Compile verification

```
cd web && npx tsc --noEmit
exit code: 0
```

Full project check (not scoped to touched files only) — no errors.

## Island definition sanity

**Tileset envelope:** `[-123.25, 48.4, -122.75, 48.7]` (west, south, east, north)

| Island ID | Bounds [W,S,E,N] | defaultDepthM | Inside tileset |
|-----------|------------------|---------------|----------------|
| `san-juan-core` | [-123.12, 48.48, -122.98, 48.62] | 8 | Yes |
| `haro-strait` | [-123.25, 48.48, -123.08, 48.7] | 10 | Yes |
| `puget-approach` | [-122.98, 48.4, -122.75, 48.58] | 6 | Yes |

`assertIslandsWithinTileset()` returns `true`.

**Normalized center check** (each island centroid → 0.5, 0.5 in its own crop):

| Island | u | v |
|--------|---|---|
| san-juan-core | 0.5 | 0.5 |
| haro-strait | 0.5 | 0.5 |
| puget-approach | 0.5 | 0.5 |

Thumb paths are declared (`/orca-strike/islands/*.png`) but assets are not shipped in W2 (W3f lobby).

## Module notes (W3 handoff)

### controls.ts + inputAdapter.ts

- `createStrikeControlsSampler()` registers Q/E/A/D/Space/B/O/F; W/S/boost/mouse flow from existing `OrcaPilotInput` via `tick(raw)`.
- `toOrcaPilotInput()` always sets `left: false`, `right: false` (STRIKE roll lock).
- Exports `depthRateMps` (±2.5 m/s for Q/E) and `bodyRollIntent` for FSM/scene hooks.
- `defaultPilotFsmAdapterInput()` stub until W3a `pilotStateMachine.ts`.

### hydrophoneSonar.ts

- Loads `/hydrophone/slice/classification.json`.
- Audio path: `/hydrophone/slice/orcasound_lab_20210825_srkw.m4a` (gitignored; fetch per `PROVENANCE.md`).
- `emitSonar()` picks highest-confidence `presence: true` window, plays 3 s slice, returns `HydrophoneSonarPulseSpec` for scene ring VFX.
- Graceful skip when no eligible window or autoplay blocked.

### replayBuffer.ts + cameras

- Ring buffer: 5 s @ 30 Hz, capacity 150, `push` / `getWindow` / `interpolateReplaySample`.
- `breachCamera`: low angle, widened FOV, chaseCamera-style update signature.
- `replayCamera`: 3 s orbit, 120° sweep, 14 m radius, 0.35× time-scale constant exported.

### VFX stubs

- `triggerBreachSplash()` / `triggerBlowholeSpray()` return pure specs + optional `*ToR3fProps()` helpers.
- No Three.js in VFX modules except camera files (match HUNT `chaseCamera.ts` pattern).

## Blockers / escalations

| Item | Severity | Notes |
|------|----------|-------|
| Hydrophone m4a on disk | Runtime | `classification.json` present; m4a gitignored. Scene must call `hydrophoneSonar.load()` early; fetch via provenance script if missing. Not a W3 code blocker. |
| Island thumb PNGs | Cosmetic | Paths declared; W3f can add or omit. |
| Context-map crop visual test | Deferred | No SonarContextMap edit in W2 per scope. Normalized math verified analytically; W3f spawn picker should screenshot-verify. |

## Forbidden actions (confirmed)

- Did not edit `web/lib/scene/orcaPilot/input.ts`
- Did not wire `OrcaStrikeScene.tsx`
- Did not edit SalishScene, workbench, root layout nav
- Did not run git

## W3 entry checklist

1. `pilotStateMachine.ts` — consume `StrikeControls`, drive `PilotFsmAdapterInput`
2. Wire `controls.tick` + `inputAdapter.toOrcaPilotInput` in scene (W4 integration hub)
3. Breach/blowhole use VFX trigger exports on FSM transitions
4. `replayBuffer.push` on pose finalize; `replayCamera.start` on `breach_land`
5. O-key calls `hydrophoneSonar.emitSonar` from scene when `ctrl.sonarEmit`
