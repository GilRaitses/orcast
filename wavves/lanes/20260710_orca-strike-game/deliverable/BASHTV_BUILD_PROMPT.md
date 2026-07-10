# Orca Strike — Bash.tv operator card

## 1. Attach these 5 files to Bash.tv FIRST

See **`BASH_TV_OPERATOR_ATTACH.md`** for paths. Minimum:

- `orca.glb` (skinned orca — **not optional**)
- `orca_srkw_oo14_driver.json` + `.bin` (DTAG articulation)
- `classification.json`
- `orcasound_lab_20210825_srkw.m4a` (**only on your Mac, not GitHub**)

## 2. Paste this (builder — pull + integrate)

Use **`BASH_TV_BUILDER_PROMPT.txt`** for the full paste block.

Short form:

```
Reference repo: https://github.com/GilRaitses/orcast
Clone it. Attach orca.glb, DTAG json+bin, classification.json, hydrophone m4a.
Read deliverable/BASH_TV_OPERATOR_ATTACH.md then BASH_TV_AGENT_BRIEF.md.
Port web/lib/scene/orcaStrike/, boats/, sonar/, orca/, orcaPilot/ into a new game app.
Reference integration: web/app/(game)/orca-strike/OrcaStrikeScene.tsx
No placeholder orca. Q/E controls. Boats + kayaks required.
```

## Why Bash agents miss assets

| Problem | Fix |
|---------|-----|
| GitHub "reference" does not download GLB/BIN/M4A | **You attach files** or agent runs `fetch-assets.sh` |
| m4a gitignored | **You must attach** from `web/public/hydrophone/slice/` |
| Boats/kayaks are TypeScript meshes, not GLB | Agent must **port** `web/lib/scene/boats/` |
| Agent builds placeholder orca | Brief now **forbids** this; gate on skinned GLB |
| Q/E not wired | Agent must read `STRIKE-controls.md` — not HUNT S/Space |
