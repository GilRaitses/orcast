# STRIKE waveset: orca-strike-game

Lane code: STRIKE  
Owner: O0 (operator-facing thread)  
Type: execution (arcade game expansion on HUNT baseline)  
repo_state_verified_against: cbe6483fb2157edcdca27e7b21dfffa7b961a7b5 (main, before this lane)

Working-tree note: at charter time the repo has a large set of pre-existing
uncommitted changes from unrelated concurrent work. STRIKE must not touch,
depend on, or commit any of those paths unless O0 explicitly widens scope.
STRIKE's file set is disjoint: new code under `web/lib/scene/orcaStrike/` and
`web/app/(game)/orca-strike/`, plus controlled edits to HUNT-owned sandbox
files during migration.

## Intent

Operator framing (2026-07-10), verbatim intent:

- **Controls:** Q dive, E surface, S backward, W forward, A roll left, D roll
  right.
- **Rig state machine** for DTAG-derived articulation across idle, swim, dive,
  surface, roll, boost, breach, blowhole modes.
- **Space:** breach with button-mash (mobile gesture equivalent), aerial
  tricks, slow-mo replay on landing; jump over kayak = high points; land on
  boat = win.
- **B (mash):** blowhole charge and water squirt; squirting kayaks = high
  points.
- **O:** sonar emit using hydrophone annotation samples.
- **Multiplayer:** MMO-style swim with other orcas; Dodo-code room invites to
  your island; timed rounds (Counter-Strike structure, cooperative scoring not
  orca combat).
- **Match flow:** select orca → pick spawn on context map → timed solo/team
  round.
- **Standalone:** build completely separate from main orcast site; migrate
  later only.

HUNT baseline (already landed, uncommitted): player-piloted orca, bathymetry
tileset, boat ram/sink, F-key radar + 1–9 teleport, chase camera, sandbox
route at `/orca-strike`.

## Grounding

Authority asset map: `ASSET_DEPENDENCY_MAP.md` (read in full before any edit).

Key existing files (verified at hash above):

- `web/app/(sandbox)/orca-strike/OrcaStrikeScene.tsx` — current integration hub
- `web/lib/scene/orcaPilot/` — input (LOCKED), deadReckoning, chaseCamera
- `web/lib/scene/orca/rig/OrcaRig.ts` + `motion/biologging.ts` — rig drive
- `web/public/orca/orca.glb` + `motion/orca_srkw_oo14_driver.{json,bin}`
- `web/public/hydrophone/slice/` — O-key audio source (fetch if gitignored)
- `web/lib/scene/boats/`, `web/lib/scene/sonar/` — HUNT mechanics
- Deploy: EC2 `i-04a649f91274e9fce`, port 3010, `orca-strike.aimez.ai`

Locked decisions (do not reopen without `/mod-decide`):

- `decisions/STRIKE-controls.md` — full control map
- `decisions/STRIKE-standalone.md` — `(game)` route group, no site nav
- `decisions/STRIKE-multiplayer.md` — phased W5, co-op scoring
- `decisions/STRIKE-mp-stack.md` — **PartyKit** on **Bash.tv** (not EC2)
- `decisions/STRIKE-accept-scope.md` — **ACCEPT at W4 solo**; W5 follow-on lane
- `decisions/STRIKE-hydrophone-audio.md` — attach m4a + provenance fetch fallback
- HUNT carry-over: `HUNT-movement-scale.md`, `HUNT-orbit-coexistence.md`,
  `HUNT-bathy-fidelity.md`

## Wave structure

### STRIKE-W1 — Discovery (parallel, read-only)

| Sub-wave | Deliverable | Model hint |
|----------|-------------|------------|
| W1a | Finalize `ASSET_DEPENDENCY_MAP.md` gaps | medium |
| W1b | `findings/STRIKE-W1b-pilot-fsm.md` — mode graph + transitions | high |
| W1c | `findings/STRIKE-W1c-articulation-blend.md` — DTAG channel → DOF | high |
| W1d | `findings/STRIKE-W1d-scoring-breach.md` — breach/blowhole/replay spec | medium |
| W1e | `findings/STRIKE-W1e-multiplayer.md` — stack pick + protocol sketch | high |
| W1f | `findings/STRIKE-W1f-adversarial.md` — scope/lock audit | high |

**Gate:** O0 reviews W1 findings before W2 dispatch.

### STRIKE-W2 — Preflight assets (parallel)

| Sub-wave | Deliverable |
|----------|-------------|
| W2a | `web/lib/scene/orcaStrike/islands/definitions.ts` + `maps.ts` |
| W2b | `web/lib/scene/orcaStrike/hydrophoneSonar.ts` stub + audio load path |
| W2c | `web/lib/scene/orcaStrike/vfx/` stubs (breach, blowhole) |
| W2d | `web/lib/scene/orcaStrike/replayBuffer.ts` + camera spec |
| W2e | `web/lib/scene/orcaStrike/controls.ts` + `inputAdapter.ts` |

**Gate:** controls compile; island defs render in context-map crop test.

### STRIKE-W3 — Core mechanics (parallel, new files)

| Sub-wave | Deliverable |
|----------|-------------|
| W3a | `pilotStateMachine.ts` + rig blend integration |
| W3b | `scoring.ts` + `match.ts` (solo timer round) |
| W3c | Breach mash + air tricks + landing detection |
| W3d | Blowhole mash + kayak squirt hitbox |
| W3e | O-key hydrophone sonar (audio + visual pulse) |
| W3f | Lobby shell: orca pick + `SpawnPicker.tsx` |

### STRIKE-W4 — Integration (GATED, single editor)

One agent owns convergence:

1. Create `web/app/(game)/orca-strike/layout.tsx` (fullscreen standalone).
2. Migrate or mirror sandbox components into `(game)/orca-strike/`.
3. Wire `OrcaStrikeScene.tsx` to FSM, scoring, breach, blowhole, sonar.
4. Remove dependency on main site nav; keep `/orca-strike` URL.
5. Deploy verify on `orca-strike.aimez.ai`.

**Forbidden in W4:** `SalishScene.tsx`, workbench, global nav edits.

### STRIKE-W5 — Multiplayer (GATED on W1e + O0)

Room codes, remote orca ghosts, score sync. No W5 code until architecture
approved in `findings/STRIKE-W1e-multiplayer.md`.

### STRIKE-ACCEPT — Verification

| Check | Method |
|-------|--------|
| Q/E/A/D/S/W controls | manual + headless key inject if available |
| FSM visible articulation | screenshot idle vs roll vs breach |
| Breach replay | slow-mo plays after landing |
| Blowhole on kayak | score +300 |
| O sonar | hydrophone audio plays |
| Spawn picker | three islands selectable |
| Standalone shell | no Forecast/Explore chrome |
| Deploy | live URL loads |

## Model routing

| Wave | Suggested model | Reason |
|------|-----------------|--------|
| W1b,c,f | claude-sonnet-5-thinking-high | FSM + rig math |
| W1d,e | gpt-5.6-terra-medium | game design + net recon |
| W2–W3 | composer-2.5-fast or sonnet | implementation volume |
| W4 | claude-opus-4-8-thinking-high | single convergence editor |
| W5 | gpt-5.3-codex | protocol + sync |

## Escalation

Subagents return to O0 orchestrator only. O0 escalates to human operator for:

- Any edit to locked `orcaPilot/input.ts`
- Multiplayer provider pick (PartyKit vs DO vs other)
- Widening scope into workbench or SalishScene
- New `/mod-decide` when HUNT locks conflict with STRIKE controls

## Git

Wave subagents NEVER run git. O0 is sole git actor. Each wave ends with an
explicit file list for commit.

## Acceptance (lane complete)

1. Standalone `/orca-strike` game on **Bash.tv** with full control map (STRIKE-controls).
2. Pilot FSM drives visible rig articulation per mode.
3. Solo timed round with scoring, breach replay, blowhole, O-sonar.
4. Lobby: orca select + island spawn picker (3 islands).
5. `ASSET_DEPENDENCY_MAP.md` matches shipped files.
6. **W5 multiplayer is out of ACCEPT scope** — follow-on lane after W4 solo lands.

## Skills (builder agents)

- `wavves/skills/orca-strike-game/SKILL.md` — lane workflow
- `wavves/skills/orca-strike-assets/SKILL.md` — asset map quick reference

Read both before STRIKE-W2+.
