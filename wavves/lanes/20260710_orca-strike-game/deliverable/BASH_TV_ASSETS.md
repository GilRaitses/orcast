# Bash.tv asset manifest — Orca Strike

**Read `BASH_TV_OPERATOR_ATTACH.md` first.** Binary assets do not arrive via
GitHub "reference" paraphrase. Download with `fetch-assets.sh` or operator attach.

Repo: `https://github.com/GilRaitses/orcast`  
Raw base: `https://raw.githubusercontent.com/GilRaitses/orcast/main`

## MANDATORY files (game is broken without these)

| Asset | Repo path | Full raw URL | In GitHub? |
|-------|-----------|--------------|------------|
| **Orca GLB (skinned rig)** | `web/public/orca/orca.glb` | https://raw.githubusercontent.com/GilRaitses/orcast/main/web/public/orca/orca.glb | YES |
| **DTAG driver JSON** | `web/public/orca/motion/orca_srkw_oo14_driver.json` | https://raw.githubusercontent.com/GilRaitses/orcast/main/web/public/orca/motion/orca_srkw_oo14_driver.json | YES |
| **DTAG driver BIN** | `web/public/orca/motion/orca_srkw_oo14_driver.bin` | https://raw.githubusercontent.com/GilRaitses/orcast/main/web/public/orca/motion/orca_srkw_oo14_driver.bin | YES |
| **Hydrophone labels** | `web/public/hydrophone/slice/classification.json` | https://raw.githubusercontent.com/GilRaitses/orcast/main/web/public/hydrophone/slice/classification.json | YES |
| **Hydrophone audio** | `web/public/hydrophone/slice/orcasound_lab_20210825_srkw.m4a` | — | **NO — operator attach only** |

### Verify orca.glb loaded correctly

- File size ~**486752** bytes
- `GLTFLoader` shows **skinned mesh** with bones (not a single BoxGeometry substitute)
- Load pattern: `web/lib/scene/orca/loadOrcaMesh.ts`, rig: `web/lib/scene/orca/rig/OrcaRig.ts`

### Verify DTAG driver

- JSON ~5118 bytes, BIN ~1146236 bytes
- 7 channels: yaw, pitch, roll, depthM, flukePhase, flukeAmp (see `biologging.ts` header)
- `driveOrca(rig, pose)` applies articulation each frame

## Terrain (URL, not in repo)

| Asset | Value |
|-------|-------|
| Tileset | https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full/tileset.json |
| Bounds | lat 48.4–48.7, lng -123.25 to -122.75 |
| Movement scale | `decisions/HUNT-movement-scale.md` — `worldUnitsPerMeter: 1` |

## Boats and kayaks (CODE — not GLB files)

Agent must **read and port** from repo:

| File | Role |
|------|------|
| `web/lib/scene/boats/spawnBoats.ts` | spawn floating boats |
| `web/lib/scene/boats/spawnKayaks.ts` | spawn kayaks |
| `web/lib/scene/boats/BoatMarker.tsx` | boat mesh ~2.8 m |
| `web/lib/scene/boats/KayakMarker.tsx` | kayak capsule ~1.5 m |
| `web/lib/scene/boats/collision.ts` | ram detection |
| `web/lib/scene/boats/sinkAnimation.ts` | sink on hit |

**Phase 2 is incomplete without boats AND kayaks in the scene.**

## Controls Q/E (locked — read file)

`decisions/STRIKE-controls.md`:

- **Q** = dive (depth rate +)
- **E** = surface (depth rate −)
- **Not** S/Space (old HUNT remap)

Port: `web/lib/scene/orcaStrike/controls.ts` + `inputAdapter.ts` + `pilotStateMachine.ts`

## Reference TypeScript to port (read, do not npm-run orcast web)

| Module | Path |
|--------|------|
| Full STRIKE stack | `web/lib/scene/orcaStrike/` |
| Orca rig + material | `web/lib/scene/orca/` |
| Pilot | `web/lib/scene/orcaPilot/` |
| Sonar | `web/lib/scene/sonar/` |
| Integrated scene (reference) | `web/app/(game)/orca-strike/OrcaStrikeScene.tsx` |

## First command in new Bash project

```bash
bash wavves/lanes/20260710_orca-strike-game/deliverable/fetch-assets.sh
# or use operator-attached files at public/ paths above
```

Then confirm m4a exists before implementing O-key.
