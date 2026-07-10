# Bash.tv agent brief — Orca Strike

**For the Bash.tv agent.** The operator pastes only the repo link and this file
path into chat. **All** specs, locks, and acceptance live in the files below.
Do not ask the operator to re-type controls, score tables, or architecture in chat.

## Repo

`https://github.com/GilRaitses/orcast`

Clone or import this repo. **Do not** `git init` a new project. Work under `web/`.

## FORBIDDEN — do not do these (common Bash.tv derailments)

The orcast repo contains **forecasting site** infrastructure (WorkOS login,
Playwright demo tests, Vercel deploy config). **Orca Strike ignores all of it.**

| Do NOT | Why |
|--------|-----|
| Run `npm run demo:*` or `playwright test` | Demo capture only; not the game |
| Configure WorkOS / `WORKOS_*` env vars | `/orca-strike` bypasses AuthKit middleware |
| Set `ORCAST_REQUIRE_LOGIN=1` | Gates the forecasting site, not the game |
| Deploy to Vercel, Netlify, or any host | Run **`npm run game:dev`** in the VM only |
| Read `web/README.md` deploy section for game | Use **this file** only |
| Build a new Next app from scratch | Game already at `web/app/(game)/orca-strike/` |

**Only command to run the game:**

```bash
cd web && npm install && npm run game:dev
```

Then open **`http://localhost:3000/orca-strike`** (or whatever port Next prints).

Optional: `cp game.env.example .env.local` (all empty is fine).

## Hydrate (read in order, before any edit)

1. `wavves/lanes/20260710_orca-strike-game/deliverable/BASH_TV_AGENT_BRIEF.md` (this file)
2. `wavves/lanes/20260710_orca-strike-game/waveset.md`
3. `wavves/lanes/20260710_orca-strike-game/ASSET_DEPENDENCY_MAP.md`
4. `wavves/skills/orca-strike-game/SKILL.md`
5. `wavves/lanes/20260710_orca-strike-game/decisions/` — all `STRIKE-*.md`
6. `wavves/lanes/20260710_orca-strike-game/findings/STRIKE-W4-integration.md`

Optional deep specs (read when implementing or debugging):

- `findings/STRIKE-W1b-pilot-fsm.md` — FSM modes and frame order
- `findings/STRIKE-W1d-scoring-breach.md` — breach, blowhole, scoring, replay
- `findings/STRIKE-W3-core.md` — module contracts

## Game entry (already implemented on `main`)

| What | Path |
|------|------|
| Route | `/orca-strike` |
| Page + lobby | `web/app/(game)/orca-strike/page.tsx` |
| Scene hub | `web/app/(game)/orca-strike/OrcaStrikeScene.tsx` |
| Standalone layout | `web/app/(game)/orca-strike/layout.tsx` |
| STRIKE library | `web/lib/scene/orcaStrike/` |
| HUNT pilot / boats / sonar | `web/lib/scene/orcaPilot/`, `boats/`, `sonar/` |

## Your job (single session)

### Step 1 — Install and run

```bash
cd web && npm install
cp .env.game.example .env.local
npm run game:dev
```

Open **`/orca-strike`** (not `/`, not `/workbench`, not `/login`).

### Step 2 — Verify shipped mechanics

Use locked controls in `decisions/STRIKE-controls.md` (read file; do not guess).

Smoke checklist:

- Q/E dive and surface
- W/S forward and reverse
- A/D body roll (not turn-assist)
- Space breach mash, air phase, landing
- B blowhole squirt on kayaks
- O hydrophone sonar (audio + pulse)
- F radar, 1–9 teleport (HUNT carry-over)
- 180s solo round, score HUD, island spawn picker

### Step 3 — Hydrophone audio (if O-key is silent)

1. Read `web/public/hydrophone/slice/PROVENANCE.md`
2. Run the fetch script documented there, **or** use operator-attached
   `orcasound_lab_20210825_srkw.m4a` placed at
   `web/public/hydrophone/slice/orcasound_lab_20210825_srkw.m4a`
3. `classification.json` is already in the repo

### Step 4 — Compile gate

```bash
cd web && npx tsc --noEmit
```

Must exit 0 before reporting done.

### Step 5 — Fix gaps only

If something in the smoke checklist fails, fix **inside the cloned repo** using
existing modules. Read `findings/STRIKE-W4-integration.md` for integration
points. Do not rebuild from scratch.

When done, offer a project zip download if the operator asks.

## Hard rules (do not violate)

- **Never** edit `web/lib/scene/orcaPilot/input.ts`
- **Never** edit `web/app/components/scene/SalishScene.tsx`, `web/app/workbench/`, or primary site nav
- **Never** present boats as real vessel traffic (arcade props only)
- **Never** add scientific, acoustic, or navigational claims
- Ship target is **Bash.tv** (not EC2)
- Multiplayer is **out of scope** until `decisions/STRIKE-mp-stack.md` follow-on lane

## Acceptance

Solo ACCEPT criteria are in `waveset.md` § STRIKE-ACCEPT. W5 multiplayer is
deferred per `decisions/STRIKE-accept-scope.md`.

## Escalate to operator only if

- `/orca-strike` route missing after pulling latest `main`
- `npm install` or tileset URL blocked (no network in VM)
- Hydrophone fetch and attach both fail

Otherwise resolve from repo files without asking the operator to paste specs.
