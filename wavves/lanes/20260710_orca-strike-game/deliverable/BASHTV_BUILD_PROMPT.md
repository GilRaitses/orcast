# Orca Strike — Bash.tv operator card

**Mode: BUILD FROM ASSETS** — Bash.tv creates the game using repo specs and real
assets. It does **not** run the pre-built orcast `/orca-strike` route.

**Repo:** `https://github.com/GilRaitses/orcast`

---

## Paste this (only message required)

```
Reference repo: https://github.com/GilRaitses/orcast

Build a new Orca Strike game from the repo assets and spec files.
Do NOT run orcast/web npm run dev and call it done.

Read and follow exactly:
wavves/lanes/20260710_orca-strike-game/deliverable/BASH_TV_AGENT_BRIEF.md
wavves/lanes/20260710_orca-strike-game/deliverable/BASH_TV_ASSETS.md
```

---

## Operator-only (not for chat)

| Item | Action |
|------|--------|
| Orca mesh | Attach `web/public/orca/orca.glb` if GitHub raw fetch fails |
| Hydrophone m4a | Attach `web/public/hydrophone/slice/orcasound_lab_20210825_srkw.m4a` for O-key |
| Phases | 3 turns per brief (world → mechanics → lobby); specs all in repo files |

---

## Where context lives (agent reads files, not chat)

| Topic | File |
|-------|------|
| Build runbook | `deliverable/BASH_TV_AGENT_BRIEF.md` |
| Asset URLs | `deliverable/BASH_TV_ASSETS.md` |
| Authority / ACCEPT | `waveset.md` |
| Controls + locks | `decisions/STRIKE-*.md` |
| FSM / scoring / breach | `findings/STRIKE-W1b-*.md`, `STRIKE-W1d-*.md` |
| Reference TS to port | `web/lib/scene/orcaStrike/` |

---

## orcast vs Bash.tv

| | orcast repo | Bash.tv job |
|--|-------------|-------------|
| Purpose | Forecast site + reference implementation | **Ship standalone game** |
| Entry | `web/app/(game)/orca-strike/` exists as reference | **Build fresh** from assets |
| WorkOS / Playwright | Present in repo | **Ignore** |
