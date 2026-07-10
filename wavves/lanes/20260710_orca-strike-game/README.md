# Orca Strike Game (STRIKE)

Arcade expansion of the HUNT orca-boat-hunt baseline into a standalone game:
full six-DOF controls, DTAG-derived articulation state machine, breach/blowhole
mechanics, hydrophone sonar, timed scoring rounds, and (phased) multiplayer.

## Quick start for builders

1. Read `waveset.md` (authority).
2. Read `ASSET_DEPENDENCY_MAP.md` (every path, no guessing).
3. Read locked decisions in `decisions/`.
4. Invoke skill `wavves/skills/orca-strike-game/SKILL.md`.

## Live deploy

- URL: https://orca-strike.aimez.ai/orca-strike
- Host: EC2 `i-04a649f91274e9fce`, `next dev` port 3010

## Status

| Wave | Status |
|------|--------|
| Charter | complete (2026-07-10) |
| STRIKE-W1 | complete |
| STRIKE-W2 | complete (`web/lib/scene/orcaStrike/`, tsc clean) |
| STRIKE-W3 | complete (FSM, scoring, breach, lobby shell; tsc clean) |
| STRIKE-W4 | ready to dispatch (scene integration + Bash.tv ship) |
| STRIKE-W5 multiplayer | follow-on lane (PartyKit) |

## Relation to HUNT

STRIKE extends HUNT modules (`orcaPilot`, `boats`, `sonar`) without forking
them. HUNT locks on movement scale, chase-only camera, and depth band remain
in force unless `/mod-decide` supersedes.
