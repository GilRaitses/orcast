# Orca Strike — Bash.tv operator card

## 1. Attach these 5 files to Bash.tv FIRST

See **`BASH_TV_OPERATOR_ATTACH.md`** for paths. Minimum:

- `orca.glb` (skinned orca — **not optional**)
- `orca_srkw_oo14_driver.json` + `.bin` (DTAG articulation)
- `classification.json`
- `orcasound_lab_20210825_srkw.m4a` (**only on your Mac, not GitHub**)

## 2. Paste this

```
Reference repo: https://github.com/GilRaitses/orcast

I attached orca.glb, DTAG driver json+bin, classification.json, and hydrophone m4a.
Place them under public/ at the paths in BASH_TV_OPERATOR_ATTACH.md.

Build a new Orca Strike game from assets. Do NOT use placeholder polygon orca.
Do NOT skip boats, kayaks, or Q/E controls.

Read and follow in order:
wavves/lanes/20260710_orca-strike-game/deliverable/BASH_TV_OPERATOR_ATTACH.md
wavves/lanes/20260710_orca-strike-game/deliverable/BASH_TV_AGENT_BRIEF.md
wavves/lanes/20260710_orca-strike-game/deliverable/BASH_TV_ASSETS.md

Run deliverable/fetch-assets.sh if any download is missing (except m4a).
```

## Why Bash agents miss assets

| Problem | Fix |
|---------|-----|
| GitHub "reference" does not download GLB/BIN/M4A | **You attach files** or agent runs `fetch-assets.sh` |
| m4a gitignored | **You must attach** from `web/public/hydrophone/slice/` |
| Boats/kayaks are TypeScript meshes, not GLB | Agent must **port** `web/lib/scene/boats/` |
| Agent builds placeholder orca | Brief now **forbids** this; gate on skinned GLB |
| Q/E not wired | Agent must read `STRIKE-controls.md` — not HUNT S/Space |
