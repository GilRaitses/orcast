# Bash.tv agent brief — Orca Strike (build from assets)

**For the Bash.tv agent.** Build a **new playable Orca Strike game** in your Bash
project using real assets and specs from the orcast repo. **Do not** run the
pre-built orcast web app and call it done.

The operator pastes only the repo link + this file path. **All** specs live in
repo files — nothing retyped in chat.

## Reference repo (read specs + copy assets)

`https://github.com/GilRaitses/orcast`

Use the repo as **reference material**: read charter files, download assets,
optionally read source modules to port logic. The shipped game on orcast
(`web/app/(game)/orca-strike/`) is a **reference implementation**, not something
you npm-run.

## FORBIDDEN

| Do NOT | Why |
|--------|-----|
| `cd web && npm run dev` on orcast and open `/orca-strike` | That runs the forecasting site's pre-built route — not your job |
| WorkOS, Playwright, Vercel, Netlify deploy setup | Forecasting-site infra; irrelevant to the game |
| Ask operator to paste controls, scores, or FSM in chat | Read `decisions/` and `findings/` instead |
| Present boats as real vessel traffic | Arcade props only |

## Hydrate (read these files from the repo, in order)

1. This file
2. `wavves/lanes/20260710_orca-strike-game/deliverable/BASH_TV_ASSETS.md` — asset URLs + copy paths
3. `wavves/lanes/20260710_orca-strike-game/waveset.md`
4. `wavves/lanes/20260710_orca-strike-game/ASSET_DEPENDENCY_MAP.md`
5. `wavves/lanes/20260710_orca-strike-game/decisions/STRIKE-controls.md`
6. `wavves/lanes/20260709_orca-boat-hunt/decisions/HUNT-movement-scale.md`
7. `wavves/lanes/20260710_orca-strike-game/findings/STRIKE-W1b-pilot-fsm.md`
8. `wavves/lanes/20260710_orca-strike-game/findings/STRIKE-W1d-scoring-breach.md`
9. `wavves/lanes/20260710_orca-strike-game/findings/STRIKE-W1c-articulation-blend.md`

**Reference source (port logic, do not blindly copy-paste the whole app):**

- `web/lib/scene/orcaStrike/` — controls, FSM, breach, scoring (TypeScript reference)
- `web/lib/scene/orcaPilot/` — dead reckoning, chase camera
- `web/lib/scene/boats/`, `web/lib/scene/sonar/` — HUNT mechanics
- `web/lib/scene/orca/rig/OrcaRig.ts`, `motion/biologging.ts` — rig drive pattern

## Your job — build the game in 3 phases

Work in **your Bash.tv project** (Next.js + R3F or Vite + R3F). Commit after
each phase.

### Phase 1 — World + swim (one turn)

Read: `BASH_TV_ASSETS.md`, `HUNT-movement-scale.md`, `ASSET_DEPENDENCY_MAP.md` §4.

- Create a fresh game app (not the orcast `web/` forecast site).
- Load **orca.glb** and the **full tileset** (URLs in `BASH_TV_ASSETS.md`).
- Fixed arcade swim: `worldUnitsPerMeter: 1`, depth band 0–25 m, chase camera.
- Transparent water surface, sky/fog, land vs sea readable.
- Documented flat-plane fallback only if tileset fails.

### Phase 2 — STRIKE controls + mechanics (one turn)

Read: `STRIKE-controls.md`, `STRIKE-W1b-pilot-fsm.md`, `STRIKE-W1d-scoring-breach.md`.

Implement locked controls (Q/E/A/D/S/W, Space breach, B blowhole, O sonar, F
radar, 1–9 teleport). Port or reimplement:

- Pilot FSM (12 modes)
- Boat ram/sink + kayaks (arcade props)
- Breach mash, blowhole squirt, scoring table from W1d
- O-key hydrophone slice (attach operator m4a or fetch per `PROVENANCE.md`)

### Phase 3 — Lobby + solo round (one turn)

Read: `waveset.md` ACCEPT, `web/lib/scene/orcaStrike/islands/definitions.ts`
(three islands), `STRIKE-standalone.md`.

- Orca skin pick, island spawn picker on context map
- 180s solo timer, score HUD, breach slow-mo replay
- Standalone fullscreen shell (no forecast site nav)

## Acceptance

`waveset.md` § STRIKE-ACCEPT (solo). Multiplayer deferred per
`decisions/STRIKE-accept-scope.md`.

## Escalate to operator only if

- Asset download from repo/GitHub raw URLs fails
- Tileset URL blocked (no network)
- Hydrophone m4a missing after attach + provenance fetch
