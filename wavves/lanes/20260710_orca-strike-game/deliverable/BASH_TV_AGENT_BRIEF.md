# Bash.tv agent brief — Orca Strike (build from assets)

Build a **new** Orca Strike game in your Bash project. **All specs in repo files.**

## Step 0 — Assets BEFORE any game code (mandatory)

Read: `deliverable/BASH_TV_OPERATOR_ATTACH.md`

1. Run `deliverable/fetch-assets.sh` **OR** use operator-attached files at:
   - `public/orca/orca.glb`
   - `public/orca/motion/orca_srkw_oo14_driver.{json,bin}`
   - `public/hydrophone/slice/classification.json`
   - `public/hydrophone/slice/orcasound_lab_20210825_srkw.m4a` (**operator attach — not on GitHub**)

2. **GATE:** Load `orca.glb` with GLTFLoader. If you see a placeholder polygon
   orca instead of the skinned GLB, **STOP** and fix asset paths. Never substitute
   a handmade mesh.

3. Wire `OrcaRig` + `driveOrca` + DTAG driver (read `web/lib/scene/orca/rig/OrcaRig.ts`,
   `motion/biologging.ts`). Articulation comes from the **skeleton + DTAG bin**,
   not invented animation.

## FORBIDDEN

| Do NOT | Why |
|--------|-----|
| Build a "simple stylized orca" mesh | Use **orca.glb** only |
| Skip boats/kayaks | Port `web/lib/scene/boats/` — Phase 2 incomplete without them |
| Use S/Space for dive/surface | **Q dive, E surface** per `decisions/STRIKE-controls.md` |
| Run orcast `web/` npm run dev as deliverable | Build fresh game app |
| WorkOS / Playwright / deploy platforms | Irrelevant |

## Hydrate (read from repo, in order)

1. `deliverable/BASH_TV_OPERATOR_ATTACH.md`
2. `deliverable/BASH_TV_ASSETS.md`
3. `decisions/STRIKE-controls.md`
4. `findings/STRIKE-W1b-pilot-fsm.md`
5. `findings/STRIKE-W1d-scoring-breach.md`
6. `findings/STRIKE-W1c-articulation-blend.md`
7. `ASSET_DEPENDENCY_MAP.md`

## Build phases

### Phase 1 — Assets + tileset + orca with DTAG rig

- `fetch-assets.sh` or attached files
- Tileset URL in `BASH_TV_ASSETS.md`
- Load orca.glb, build OrcaRig, sample DTAG driver
- Chase camera, depth 0–25 m

### Phase 2 — STRIKE controls + boats + kayaks + sonar

- **Q/E/A/D/S/W/Space/B/O/F/1-9** per `STRIKE-controls.md`
- Port `orcaStrike/controls.ts`, `pilotStateMachine.ts`, `boats/`, `sonar/`
- Spawn boats AND kayaks (procedural markers from repo source)

### Phase 3 — Scoring, breach, blowhole, lobby

- Port `breach.ts`, `blowhole.ts`, `scoring.ts`, `match.ts`, `hydrophoneSonar.ts`
- O-key plays m4a slice from `classification.json`
- Island spawn picker from `islands/definitions.ts`

## Acceptance checklist (report each item PASS/FAIL)

- [ ] orca.glb skinned mesh visible (black/white, not grey primitives)
- [ ] DTAG driver moves rig (fluke, pitch, roll visible)
- [ ] Q dive, E surface work
- [ ] Boats spawn and sink on ram
- [ ] Kayaks spawn (breach/blowhole targets)
- [ ] O-key plays hydrophone audio
- [ ] F sonar + 1-9 teleport

Repo: `https://github.com/GilRaitses/orcast`
