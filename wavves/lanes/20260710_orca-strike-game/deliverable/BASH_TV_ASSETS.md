# Bash.tv asset manifest — Orca Strike

**Authority for Phase 1.** Download or reference these from the orcast repo.
Do not guess URLs.

Repo: `https://github.com/GilRaitses/orcast`  
Raw base: `https://raw.githubusercontent.com/GilRaitses/orcast/main/`

## Meshes and motion

| Asset | Repo path | Raw URL |
|-------|-----------|---------|
| Orca GLB | `web/public/orca/orca.glb` | `https://raw.githubusercontent.com/GilRaitses/orcast/main/web/public/orca/orca.glb` |
| DTAG driver JSON | `web/public/orca/motion/orca_srkw_oo14_driver.json` | `.../web/public/orca/motion/orca_srkw_oo14_driver.json` |
| DTAG driver BIN | `web/public/orca/motion/orca_srkw_oo14_driver.bin` | `.../web/public/orca/motion/orca_srkw_oo14_driver.bin` |

Attach `orca.glb` directly in Bash.tv if raw fetch fails.

## Terrain

| Asset | Value |
|-------|-------|
| Tileset (full, not pilot) | `https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full/tileset.json` |
| Bounds | lat 48.4–48.7, lng -123.25 to -122.75 |
| Fit hints | See `web/lib/scene/tiles/useTilesLayer.ts` in repo — `groupRotationX: -π/2`, metric fit, `errorTarget: 16` |
| Movement scale lock | `wavves/lanes/20260709_orca-boat-hunt/decisions/HUNT-movement-scale.md` — `worldUnitsPerMeter: 1` |

## Hydrophone (O-key sonar)

| Asset | Repo path | Notes |
|-------|-----------|-------|
| Classifications | `web/public/hydrophone/slice/classification.json` | In repo |
| Audio slice | `web/public/hydrophone/slice/orcasound_lab_20210825_srkw.m4a` | **Gitignored** — operator attaches to Bash, or fetch per `web/public/hydrophone/slice/PROVENANCE.md` |

## Geo / places (F radar + teleport)

| Asset | Repo path |
|-------|-----------|
| Gazetteer | `web/lib/geo/gazetteer.ts` |
| Scene frame | `web/lib/sceneIntent.ts` — `SCENE_WIDTH=120`, `projectToScene` |

## Islands (spawn picker)

Read and port values from:

`web/lib/scene/orcaStrike/islands/definitions.ts`

Locked v1: `san-juan-core`, `haro-strait`, `puget-approach`.

## Spec files (mechanics — read, do not skip)

| Topic | File |
|-------|------|
| Controls | `decisions/STRIKE-controls.md` |
| FSM | `findings/STRIKE-W1b-pilot-fsm.md` |
| Scoring / breach / blowhole | `findings/STRIKE-W1d-scoring-breach.md` |
| Rig blends | `findings/STRIKE-W1c-articulation-blend.md` |
| Full path map | `ASSET_DEPENDENCY_MAP.md` |

## Reference implementation (read to port, not to npm-run)

| Module | Repo path |
|--------|-----------|
| STRIKE library | `web/lib/scene/orcaStrike/` |
| Pilot | `web/lib/scene/orcaPilot/` |
| Boats | `web/lib/scene/boats/` |
| Sonar | `web/lib/scene/sonar/` |
| Integrated scene | `web/app/(game)/orca-strike/OrcaStrikeScene.tsx` |

## npm packages (game app only)

```
three @react-three/fiber @react-three/drei 3d-tiles-renderer
```

Install in **your** Bash game project. Do not assume orcast `web/package.json`
scripts are your entrypoint.
