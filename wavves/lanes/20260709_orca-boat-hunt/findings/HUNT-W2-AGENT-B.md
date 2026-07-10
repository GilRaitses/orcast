# HUNT-W2 Agent B Findings

## Scope

Built the isolated arcade boat-sinking mechanic under `web/lib/scene/boats/`.
No route files, sonar files, or orca pilot files were created or edited.

## Files Created

- `web/lib/scene/boats/BoatEntity.ts`
- `web/lib/scene/boats/spawnBoats.ts`
- `web/lib/scene/boats/collision.ts`
- `web/lib/scene/boats/sinkAnimation.ts`
- `web/lib/scene/boats/BoatMarker.tsx`
- `web/lib/scene/boats/index.ts`
- `web/lib/scene/boats/WIRING.md`
- `wavves/lanes/20260709_orca-boat-hunt/findings/HUNT-W2-AGENT-B.md`

## Numeric Constants

- `SEA_LEVEL_Y = 0`
- `DEFAULT_BOAT_COUNT = 8`
- `DEFAULT_MIN_RADIUS = 14`
- `DEFAULT_MAX_RADIUS = 54`
- `DEFAULT_BOAT_COLLISION_RADIUS = 2.2`
- `SINK_DURATION_SECONDS = 1.8`
- `MAX_SINK_TILT_RAD = Math.PI * 0.38`
- `MAX_SINK_DEPTH_Y = -2.4`
- `PARTICLE_BURST_PROGRESS = 0.2`

## Typecheck

Command run from `/Users/gilraitses/orcast/web`.

```text
> orcast-web@0.1.0 typecheck
> tsc --noEmit
```

Result: passed with exit code 0.

## Lint

Command run from `/Users/gilraitses/orcast/web`.

```text
> orcast-web@0.1.0 lint
> next lint

? How would you like to configure ESLint? https://nextjs.org/docs/basic-features/eslint
❯  Strict (recommended)
   Base
   Cancel ⚠ If you set up ESLint yourself, we recommend adding the Next.js ESLint plugin. See https://nextjs.org/docs/basic-features/eslint#migrating-existing-config
```

Result: blocked by the pre-existing repo-wide missing ESLint configuration. No
ESLint config or dependency was added.

## Gaps

No scoped implementation gaps. Route-level disclaimer rendering and live orca
controller wiring remain intentionally outside this agent's lane.
