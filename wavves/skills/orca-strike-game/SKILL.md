---
name: orca-strike-game
description: Build the STRIKE standalone Orca Strike arcade game lane. Use when implementing controls, pilot FSM, breach/blowhole, scoring, lobby, or migrating to the (game) route shell. Read ASSET_DEPENDENCY_MAP.md first.
---

# Orca Strike Game Builder

Lane home: `wavves/lanes/20260710_orca-strike-game/`

## Before any edit

1. Read `waveset.md` (wave gates and acceptance).
2. Read `ASSET_DEPENDENCY_MAP.md` (every path — no guessing).
3. Read locked decisions in `decisions/STRIKE-*.md`.
4. Pair with `wavves/skills/orca-strike-assets/SKILL.md` for quick lookups.

## Hard rules

- **Standalone:** code lives under `web/app/(game)/orca-strike/` and
  `web/lib/scene/orcaStrike/`. Do not wire into workbench, SalishScene, or
  primary site nav.
- **Do not edit** `web/lib/scene/orcaPilot/input.ts`. Map Q/E/A/D/S/W/Space/B/O
  in `orcaStrike/controls.ts` → `inputAdapter.ts`.
- **Single integration hub:** `OrcaStrikeScene.tsx` wires FSM, scoring, cameras.
  Library modules stay pure (no React in `orcaStrike/` except net ghosts).
- **HUNT locks:** `worldUnitsPerMeter: 1`, chase camera only, 0–25 m depth band.
- **Visual verify:** screenshot or Read tool on rendered output before claiming done.
- **Git:** subagents never commit; return file list to O0.

## Implementation order (after W1 approval)

```
W2: controls + islands + hydrophone stub + vfx stubs + replay buffer
W3: pilotStateMachine → scoring/match → breach → blowhole → O-sonar → lobby UI
W4: (game) layout + scene convergence + deploy verify
W5: multiplayer (gated)
```

## Pilot FSM contract

```typescript
// web/lib/scene/orcaStrike/pilotStateMachine.ts
export type PilotMode =
  | 'idle' | 'swim' | 'dive' | 'surface'
  | 'roll_left' | 'roll_right' | 'boost'
  | 'breach_charge' | 'breach_air' | 'breach_land'
  | 'blowhole_charge' | 'blowhole_squirt';

export interface PilotFsmOutput {
  mode: PilotMode;
  rigBlend: { swim: number; roll: number; breach: number; blowhole: number };
  motionOverrides: Partial<BiologgingPose>;
}
```

`OrcaStrikeScene` calls `tick()` then `driveOrca()` — never skip FSM.

## Scoring events (locked defaults)

| Event | Points |
|-------|--------|
| Breach over kayak | 500 |
| Blowhole hit kayak | 300 |
| Ram sink boat | 200 |
| Land on boat | round win |
| O sonar new blip | 50 |

## Deploy verify

URL: `https://orca-strike.aimez.ai/orca-strike`  
Host: EC2 `i-04a649f91274e9fce`, port 3010.

## Escalate to O0 when

- HUNT lock conflicts with new control behavior
- Hydrophone audio missing (needs provenance fetch)
- Multiplayer provider choice blocks W5
- Any need to edit `SalishScene.tsx` or workbench
