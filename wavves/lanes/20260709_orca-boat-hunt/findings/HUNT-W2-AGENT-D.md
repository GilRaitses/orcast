# HUNT-W2 Agent D — completion note

**Deliverable written:** `deliverable/BASHTV_BUILD_PROMPT.md`

**Source:** `waveset.md` only (no code touched, no git commands run).

## Locked decisions transcribed

| # | How it appears in the deliverable |
|---|---|
| **1** | Core mechanics → Boat-sinking: arcade floating props, ram/collision sink + splash/particle burst; no AIS; boats never presented as real vessel data. Non-goals table repeats this. |
| **2** | Core mechanics → Sonar + Floo teleport: ping reveals radar readout of boats + handful of gazetteer places with bearing/range; select target → instant snap + warp/flash beat; only fast-travel mechanic; no continuous swim-to autopilot. Prompt 2 batches boats + sonar + teleport. |
| **3** | Reusable assets table names orca rig/controller reference files; notes horizontal X/Z is not rig-owned (player pilot writes root position). |
| **4** | Not transcribed into Bash.tv prompt (orcast-only `OrcaController.ts` optional-param seam; irrelevant to fresh Bash.tv project). |
| **5** | Core mechanics → Movement: dead-reckoning heading+speed integrator, depth clamp, chase camera (described in Prompt 1 language, not orcast module names). |
| **6** | Not transcribed (orcast route `/orca-strike` is in-repo only). |
| **7** | Not transcribed (orcast directory layout is in-repo only). |
| **8** | Core mechanics → Movement: real bathymetry via full tileset; documented flat water-plane fallback acceptable, never silent. Open question 4 flags fallback trigger ambiguity. |
| **9** | Core mechanics → Disclaimer line verbatim; no acoustic/scientific/navigational claims. Non-goals table. Prompt 3 includes disclaimer. |
| **10** | Entire deliverable structure: paste-ready prompt package, real asset paths/URLs, build sequence sized for few large Bash.tv turns. |
| **11** | N/A (git policy for O0; this agent ran no git commands). |

## Confirmed asset facts included

- Orca mesh: `web/public/orca/orca.glb` / `/orca/orca.glb` / `ORCA_MESH_URL`; backup `/orca/orca-poly-backup.glb`
- Full bathymetry tileset URL, `useTilesLayer` fit options, TILESET_BOUNDS extent
- SRKW biologging: `/orca/motion/orca_srkw_oo14_driver.json` + `.bin`, CC-BY 4.0, optional ambient only
- Gazetteer: `web/lib/geo/gazetteer.ts`, ~40 Salish Sea places

## Open questions flagged (not guessed)

1. Whether Bash.tv VM has orcast repo access to fetch/copy assets
2. Exact count of gazetteer places in sonar ("handful" unspecified)
3. Boat spawn count/layout (unspecified in charter)
4. When to trigger flat-plane fallback vs retry tileset
5. SRKW biologging remains optional; player input always drives movement
