# Bash.tv — operator attach list (do this BEFORE pasting the agent prompt)

Bash.tv **cannot** reliably pull binary assets from a GitHub "reference" link.
The agent will build ugly placeholder polygons unless **you attach these files**
to the Bash chat first (or the agent runs `fetch-assets.sh` and you attach m4a).

## Attach to Bash.tv now (drag into agent file upload)

| # | File on your Mac | Size check | Required |
|---|------------------|------------|----------|
| 1 | `web/public/orca/orca.glb` | ~487 KB | **YES — skinned orca skeleton, NOT a substitute mesh** |
| 2 | `web/public/orca/motion/orca_srkw_oo14_driver.json` | ~5 KB | **YES — DTAG articulation manifest** |
| 3 | `web/public/orca/motion/orca_srkw_oo14_driver.bin` | ~1.1 MB | **YES — DTAG motion samples** |
| 4 | `web/public/hydrophone/slice/classification.json` | ~17 KB | YES — O-key sonar windows |
| 5 | `web/public/hydrophone/slice/orcasound_lab_20210825_srkw.m4a` | ~2.2 MB | **YES — NOT on GitHub; you must attach** |

**Absolute paths on your machine:**

```
/Users/gilraitses/orcast/web/public/orca/orca.glb
/Users/gilraitses/orcast/web/public/orca/motion/orca_srkw_oo14_driver.json
/Users/gilraitses/orcast/web/public/orca/motion/orca_srkw_oo14_driver.bin
/Users/gilraitses/orcast/web/public/hydrophone/slice/classification.json
/Users/gilraitses/orcast/web/public/hydrophone/slice/orcasound_lab_20210825_srkw.m4a
```

Tell the agent to place them at the same paths under `public/` in the game app.

## What is NOT a separate file (agent ports from repo source)

| Feature | Repo path — agent must READ and reimplement |
|---------|---------------------------------------------|
| Boats + kayaks | `web/lib/scene/boats/` (`spawnBoats.ts`, `spawnKayaks.ts`, `BoatMarker.tsx`, `KayakMarker.tsx`) — **procedural meshes, not GLB** |
| Rig driver | `web/lib/scene/orca/rig/OrcaRig.ts` + `motion/biologging.ts` — works **with** orca.glb skeleton |
| Q/E/A/D controls | `decisions/STRIKE-controls.md` + `web/lib/scene/orcaStrike/controls.ts` |
| Pilot FSM | `web/lib/scene/orcaStrike/pilotStateMachine.ts` |

## If attach fails — agent runs fetch script

`deliverable/fetch-assets.sh` downloads items 1–4 from GitHub raw URLs.
Item 5 (m4a) still requires operator attach.

## Hard gate for agent

**Stop and report** if `orca.glb` is not loaded with a **skinned mesh** (bones for
spine, head, jaw, caudal, pectoral). Never build a "stylized polygon orca"
substitute.
