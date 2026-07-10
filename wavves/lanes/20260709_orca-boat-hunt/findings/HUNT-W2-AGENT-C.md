# HUNT-W2 Agent C Progress

## Files Created

- `web/lib/scene/sonar/radarTargets.ts`
- `web/lib/scene/sonar/ping.ts`
- `web/lib/scene/sonar/teleport.ts`
- `web/lib/scene/sonar/index.ts`
- `web/lib/scene/sonar/WIRING.md`

## Curated Place Picks

- Friday Harbor
- Roche Harbor
- Deer Harbor
- Lime Kiln Point
- Jones Island
- Orcas Village
- East Sound
- San Juan Island

## Numeric Constants

- Ping visible duration is `7` seconds.
- Teleport beat duration is `420` milliseconds.
- Teleport snaps position immediately to the selected target. The visual flash fades over the beat.

## Implementation Notes

- `buildRadarTargets` returns relative bearing in radians. `0` is the orca's current forward heading, positive is clockwise to the right.
- `getCuratedPlaceTargets` imports `GAZETTEER` and projects selected places through `projectToScene`.
- `createSonarPing` stores a one-shot target snapshot for the HUD.
- `createTeleportBeat` returns the X/Z the integrator should apply, but never writes to an orca object.
- `WIRING.md` documents that `controller.root.position` is written only by the future gated integration wave.

## Validation

`npm run typecheck` from `/Users/gilraitses/orcast/web` passed.

```text
> orcast-web@0.1.0 typecheck
> tsc --noEmit
```

`npm run lint < /dev/null` from `/Users/gilraitses/orcast/web` is blocked by the pre-existing repo-wide ESLint setup prompt. I did not create an ESLint config or install packages.

```text
> orcast-web@0.1.0 lint
> next lint

? How would you like to configure ESLint? https://nextjs.org/docs/basic-features/eslint
❯  Strict (recommended)
   Base
   Cancel ⚠ If you set up ESLint yourself, we recommend adding the Next.js ESLint plugin. See https://nextjs.org/docs/basic-features/eslint#migrating-existing-config
```

## Gaps

No scoped implementation gaps. I did not create an optional React HUD overlay because the pure ping snapshot and target data surface are the gated integration boundary.
