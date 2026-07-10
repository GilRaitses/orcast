# Orca Strike — Bash.tv operator card

Everything the Bash.tv agent needs is **in the repo**. The operator pastes **one
short message** (below). No control maps, score tables, or architecture in chat.

**Repo:** `https://github.com/GilRaitses/orcast` (pushed on `main`)

---

## Paste this (only message required)

```
Reference repo: https://github.com/GilRaitses/orcast

Clone or import that repo. Do not git init a new project.

Read and follow exactly:
wavves/lanes/20260710_orca-strike-game/deliverable/BASH_TV_AGENT_BRIEF.md

Work under web/. Run /orca-strike when the dev server is up.
```

---

## Operator-only (not for chat)

| Item | Action |
|------|--------|
| Hydrophone m4a | Attach `web/public/hydrophone/slice/orcasound_lab_20210825_srkw.m4a` if O-key silent |
| Run command | **`npm run game:dev`** only — not Playwright, not deploy |
| Env | Copy `web/game.env.example` → `.env.local` (empty OK; no WorkOS) |

---

## Where context lives (agent reads these, not chat)

| Topic | File |
|-------|------|
| Agent runbook | `deliverable/BASH_TV_AGENT_BRIEF.md` |
| Authority / ACCEPT | `waveset.md` |
| Paths and ownership | `ASSET_DEPENDENCY_MAP.md` |
| Controls, deploy, scope locks | `decisions/STRIKE-*.md` |
| FSM, scoring, breach specs | `findings/STRIKE-W1b-*.md`, `STRIKE-W1d-*.md` |
| Integration map | `findings/STRIKE-W4-integration.md` |
| Build skill | `wavves/skills/orca-strike-game/SKILL.md` |

---

## Deprecated

Multi-prompt sequences (Prompt 1/2/3) are removed. The game is integrated on
`main` at `web/app/(game)/orca-strike/`. One repo-pull session + brief file is
sufficient.

Prompt 4 (PartyKit multiplayer) remains deferred; see `decisions/STRIKE-mp-stack.md`.
