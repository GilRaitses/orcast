# BSW-R13 - Integration seams + convergence-file collision map

> Read-only research finding (BSW-RESEARCH wave). Repo verified against `240570e`.
> Authored by explore agent a91c33; written by the BSW sub-orchestrator.

## Summary

- **Six convergence files carry all BSW integration risk:** `web/app/components/scene/SalishScene.tsx`, `web/app/globals.css`, `web/app/components/AdaptiveExplore.tsx`, `web/app/components/ActiveSurfaceHost.tsx`, `web/lib/uiIntent.ts`, `web/lib/scene/camera/director.ts`. `SalishScene.tsx` is the highest-collision nexus (WFX, ORCA, LGC, CVP, 3D-TWIN, and all five BSW charters touch it).
- **LGC tokens are unbuilt.** `globals.css` has base tokens but no Liquid Glass Console glass token set. Every BSW HUD surface depends on LGC. **BSW must ship minimal local glass fallbacks** and adopt LGC tokens when they land - a hard ordering dependency.
- **`streamUrl` is dropped today.** `SalishScene.tsx` emits it on hydrophone select; `AdaptiveExplore.tsx` drops it from `hydrophone_signal` props. BST/BSH need a one-line prop plumb (the only required edit to an existing data path).
- **Recommended serialization (Phases A-E):** LGC tokens -> BST station/camera -> BSH spectrogram+timeline authority -> BAM acoustic classifier -> BRE multi-orca reenactment -> BSS studio/skills. Ocean-process layer slots after Water2Rig in mount order.
- **No new full render passes.** All scene additions join the existing Water2Rig depth pre-pass / mount-after-water order.

## Convergence-file collision map

### `web/app/components/scene/SalishScene.tsx` (HIGHEST RISK)
Mount order matters: Water2Rig owns the only depth pre-pass; OrcaRig mounts after to join it. Emits `SceneIntent` on hydrophone click (incl. `streamUrl`).

| Lane | Touch | Collision with BSW |
|------|-------|--------------------|
| WFX | Water2Rig, FogTuneRig, depth pre-pass | BSH ocean-process layer must slot after Water2Rig, read its depth target read-only |
| ORCA | OrcaRig mount | BRE multi-orca instancing extends OrcaRig mount |
| LGC | HUD overlays | BST/BSH/BSS surfaces consume LGC tokens |
| CVP | camera/viewport | BST camera POV via director |
| 3D-TWIN | scene composition | shared mount slots |

**BSW slots:** HydrophoneStationRig (BST) after bathy; OceanProcessRig (BSH) after Water2Rig; multi-orca (BRE) in OrcaRig slot; IntentDirectorRig (BST camera).

### `web/app/globals.css`
Base tokens only; **no LGC glass tokens**. `.hydrophone-spectrogram` (546-552) is BSH-relevant. BSW HUD CSS must namespace (`.bsw-*`) and provide local glass fallback until LGC lands. Collision: LGC owns the glass token authority; BSW must not define competing global glass vars.

### `web/app/components/AdaptiveExplore.tsx`
Plan -> panels -> narrate loop; injects `hydrophone_signal` client-side; **drops `streamUrl`** (237-245). BST/BSH edit: plumb `streamUrl` into panel props. Collision: CVP/LGC also touch panel injection; serialize.

### `web/app/components/ActiveSurfaceHost.tsx`
`renderPanel` switch (307-368). New BSW panels (`spectrogram_hud`, `tag_series`, `dive_panel`, `label_editor`, `pipeline_studio`, `poster_*_hud`, `capture_studio`) add cases. Collision: every lane adding panels edits this switch - additive, low-risk if ids namespaced.

### `web/lib/uiIntent.ts`
`UiIntentPanel` type + `PANEL_LABELS`. BSS adds labels for new panels. Additive, low-risk.

### `web/lib/scene/camera/director.ts`
`flyTo`/`descendTo`/`orbit`. BST camera POV; BRE behavior framing. **No underwater dive clamp relaxation yet** - BSH ocean layer + dive POV depend on it. Collision: CVP owns camera; coordinate.

## LGC token dependency (hard ordering)
BSW HUD surfaces (spectrogram chip, station label, studio panels, interpretive label) all want LGC glass tokens. Until LGC ships them in `globals.css`, BSW ships `.bsw-glass` local fallback (backdrop-filter + rgba). When LGC lands, swap fallback -> tokens. **Do not block BSW on LGC**, but record the swap as a follow-up.

## Recommended serialization order (Phases A-E)

| Phase | Lane | Depends on | Convergence edits |
|-------|------|-----------|-------------------|
| A | LGC tokens (external) | - | `globals.css` glass tokens |
| B | BST station + camera POV | A (fallback ok) | `SalishScene.tsx` (rig), `AdaptiveExplore.tsx` (streamUrl), `director.ts` (POV) |
| C | BSH spectrogram + SpectroTimelineAuthority + ocean layer | B (streamUrl), Water2Rig | `SalishScene.tsx` (OceanProcessRig), `globals.css` (.hydrophone-spectrogram), `ActiveSurfaceHost.tsx` |
| D | BAM acoustic classifier output | C (timeline) | panels only |
| E | BRE multi-orca reenactment | C (timeline), D (presence), R04 clips | `SalishScene.tsx` (OrcaRig multi), `director.ts` |
| F | BSS studio + skills + capture | C-E | `ActiveSurfaceHost.tsx`, `uiIntent.ts`, manifest/panels |

## Recommendations with cost + fallback

| Rec | Detail | Cost | Fallback |
|-----|--------|------|----------|
| R1 | Namespace all BSW panels/CSS (`bsw-*`) to keep switch edits additive | low | n/a |
| R2 | Plumb `streamUrl` in AdaptiveExplore (one prop) | ~0.25 day | station shows label without live URL |
| R3 | Local `.bsw-glass` fallback; swap to LGC tokens when ready | ~0.5 day | local glass ships demo |
| R4 | OceanProcessRig + multi-orca join existing pre-pass; no new full render | per-charter | layer disabled |
| R5 (O0) | Confirm director underwater dive clamp relaxation owner (CVP vs BST) | O0 gate | layer dormant above water |

## Open questions / flags for O0

1. LGC token ship date vs BSW demo deadline - block or fallback?
2. Director dive-clamp relaxation: CVP or BST owns it?
3. `streamUrl` plumb: BST or BSH owns the AdaptiveExplore edit?
4. Panel registry: add BSW panels server-side or keep client-injected like `hydrophone_signal`?
5. Mount-order arbitration in `SalishScene.tsx` across WFX/ORCA/LGC/CVP/BSW - who serializes the merge?

## Sources

**orcast (240570e):** `web/app/components/scene/SalishScene.tsx`, `web/app/globals.css`, `web/app/components/AdaptiveExplore.tsx`, `web/app/components/ActiveSurfaceHost.tsx`, `web/lib/uiIntent.ts`, `web/lib/scene/camera/director.ts`, `web/lib/scene/water2/depthWater.ts`, `PROGRAM.md`, all five BSW charters, `research/{BSW-R03..R12}.md`, prior lane catalogues (`20260628_water-fx`, LGC/CVP charters where present).
