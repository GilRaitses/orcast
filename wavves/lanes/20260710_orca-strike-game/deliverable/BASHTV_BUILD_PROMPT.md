# Orca Strike Game — Bash.tv build prompt (repo-pull only)

**Do not** ask the Bash.tv agent to `git init` or scaffold a blank project. The
game already lives in **orcast**. The agent **clones or references** the public
repo and builds from paths inside it.

**Repo:** `https://github.com/GilRaitses/orcast`  
**Lane authority:** `wavves/lanes/20260710_orca-strike-game/waveset.md`  
**Asset map:** `wavves/lanes/20260710_orca-strike-game/ASSET_DEPENDENCY_MAP.md`

## Prerequisite (operator, before pasting)

These paths must be **committed and pushed** to `main` on GitHub. Until then,
the repo link will not contain the game code and Bash.tv cannot pull it.

```
web/app/(sandbox)/orca-strike/          # working HUNT baseline (playable today)
web/app/(game)/orca-strike/             # standalone shell + lobby HUD (W3f)
web/lib/scene/orcaStrike/               # STRIKE modules (W2+W3)
web/lib/scene/orcaPilot/
web/lib/scene/boats/
web/lib/scene/sonar/
wavves/lanes/20260710_orca-strike-game/ # charter + findings + decisions
wavves/skills/orca-strike-game/
wavves/skills/orca-strike-assets/
```

**Gitignored runtime asset (attach once to Bash.tv, not in repo):**

- `web/public/hydrophone/slice/orcasound_lab_20210825_srkw.m4a`  
  Fallback fetch: `web/public/hydrophone/slice/PROVENANCE.md`

---

## Reusable paths (already in orcast)

| What | Path |
|------|------|
| Playable scene (baseline) | `web/app/(sandbox)/orca-strike/OrcaStrikeScene.tsx` |
| Standalone game shell | `web/app/(game)/orca-strike/layout.tsx` |
| Lobby | `web/app/(game)/orca-strike/lobby/` |
| STRIKE library | `web/lib/scene/orcaStrike/` |
| Orca mesh | `web/public/orca/orca.glb` |
| DTAG driver | `web/public/orca/motion/orca_srkw_oo14_driver.{json,bin}` |
| Tileset | `https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full/tileset.json` |
| Hydrophone labels | `web/public/hydrophone/slice/classification.json` |

---

## Prompt 1 — Clone repo, run existing sandbox route (one turn)

Paste as **one message**:

> Use **only** the public GitHub repo `https://github.com/GilRaitses/orcast` as
> your source. **Do not** `git init` a new project or rebuild from scratch.
> Clone or open that repo (or use it as reference material if your environment
> supports repo import). This is a **Next.js** app under `web/`.
>
> 1. `cd web && npm install` (or `npm ci` if lockfile present).
> 2. Run the dev server and open the route **`/orca-strike`** — implementation
>    lives in `web/app/(sandbox)/orca-strike/` (`OrcaStrikeHost.tsx`,
>    `OrcaStrikeScene.tsx`).
> 3. Confirm you can swim the orca over the bathymetry tileset, ram boats,
>    press **F** for sonar, **1–9** to teleport.
> 4. Read `wavves/lanes/20260710_orca-strike-game/ASSET_DEPENDENCY_MAP.md` for
>    file ownership. Do not edit `web/lib/scene/orcaPilot/input.ts`.
>
> If `/orca-strike` is missing from the repo you pulled, stop and tell me — the
> operator must push latest `main` first.

**Why one turn:** verifies the repo-pull path works before STRIKE expansion.

---

## Prompt 2 — Wire STRIKE controls + library modules (one turn)

Paste after Prompt 1 works:

> Still working **inside** the cloned `orcast` repo (`web/`). Extend the game
> using **existing** modules under `web/lib/scene/orcaStrike/` (already in the
> repo). Read `wavves/lanes/20260710_orca-strike-game/findings/STRIKE-W1b-pilot-fsm.md`
> and `decisions/STRIKE-controls.md`.
>
> **Locked controls:** Q dive, E surface, S backward, W forward, A roll left,
> D roll right, Space breach mash, B blowhole mash, O hydrophone sonar, F radar,
> 1–9 teleport.
>
> 1. Wire `createStrikeControlsSampler()` + `inputAdapter` into
>    `OrcaStrikeScene.tsx` (or migrate hub to
>    `web/app/(game)/orca-strike/` per `decisions/STRIKE-standalone.md`).
> 2. Integrate `pilotStateMachine.ts`, `breach.ts`, `blowhole.ts`, `scoring.ts`,
>    `match.ts` per findings in `wavves/lanes/20260710_orca-strike-game/findings/`.
> 3. Remove the old Space-climb listener; Space is breach charge only.
> 4. O-key: use `hydrophoneSonar.ts`; attach operator-provided
>    `orcasound_lab_20210825_srkw.m4a` under `web/public/hydrophone/slice/` if
>    missing.
> 5. Standalone shell: use `web/app/(game)/orca-strike/layout.tsx` (fullscreen,
>    no site nav). Route stays `/orca-strike`.
>
> Run `cd web && npx tsc --noEmit` before finishing. Do not touch workbench or
> SalishScene.

---

## Prompt 3 — Lobby + solo round ACCEPT (one turn)

> In the same `orcast` clone, wire the lobby UI already in
> `web/app/(game)/orca-strike/lobby/` (`OrcaSelect`, `SpawnPicker`,
> `LobbyShell`) and HUD (`ScoreHud`, `TrickCombo`). Use island defs in
> `web/lib/scene/orcaStrike/islands/definitions.ts` (san-juan-core,
> haro-strait, puget-approach).
>
> Solo round: 180s timer, scoring per `scoring.ts`, breach slow-mo replay via
> `replayBuffer.ts` + `replayCamera.ts`. ACCEPT criteria in
> `wavves/lanes/20260710_orca-strike-game/waveset.md` (W4 solo; no multiplayer
> yet).
>
> Export a zip of the project when done if I need to download it.

---

## Prompt 4 — Multiplayer (follow-on, after W5 lane)

Deferred. When PartyKit lane lands, add a fourth prompt referencing
`decisions/STRIKE-mp-stack.md`. Not required for solo ACCEPT.

---

## Explicit non-goals

Same as HUNT: no AIS, no scientific/navigational claims, boats are arcade props.
STRIKE removes the old HUNT disclaimer requirement in favor of standalone game
shell; do not add workbench honesty machinery.

---

## Operator checklist

1. **Commit + push** all paths in the prerequisite list above.
2. Paste **Prompt 1** on Bash.tv with repo link only (no `git init` instruction).
3. Attach **m4a** hydrophone slice if O-key audio fails after pull.
4. Run Prompts 2–3 sequentially in the **same** Bash space.
5. Optional second Bash space only for unrelated experiments — not for splitting
   Prompts 2/3 (geo + scene frame are coupled).

## Model guidance

- **Prompt 1:** medium/high — verify repo import + tileset
- **Prompt 2:** high — FSM + scene integration
- **Prompt 3:** medium — UI + match flow
