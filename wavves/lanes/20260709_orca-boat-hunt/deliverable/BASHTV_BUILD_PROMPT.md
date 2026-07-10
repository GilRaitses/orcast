# Orca Strike — Bash.tv build prompt

**Orca Strike** is an arcade game where you pilot an orca over real Salish Sea bathymetry, ram stylized boats to sink them with splash effects, and use a sonar ping plus instant teleport to jump to nearby boats or curated place names. Real terrain and place data provide flavor and geography; this is not a simulation, navigation aid, or scientific instrument.

---

## Reusable real assets

These assets live in the **orcast** repo, which is public on GitHub:
`https://github.com/GilRaitses/orcast`. Per the Sup Team's own Discord Q&A
(recorded in `wavves/lanes/20260710_bash-ecosystem-recon/findings/BREC-capabilities.md`,
"Update" section): "if its a public github link you can give it the link
and it can reference it," and separately, "you can add files to the agent
and it can add them to the app." Both paths are usable here: **give the
agent the repo URL as reference material** (see Prompt 1's opening lines
below) AND attach `orca.glb` directly as a file. Neither path's exact
fidelity is confirmed (whether "reference" means the agent reads the file
verbatim or paraphrases/regenerates from it), so every asset below still
carries its own inlined prose fallback — treat the GitHub reference as the
primary path, and the inlined values/description as the safety net if the
agent doesn't actually pull from the link.

| Asset | Exact path / URL | What it is | License / provenance | How to use in a fresh Bash.tv project |
|---|---|---|---|---|
| Orca mesh (primary) | Repo: `web/public/orca/orca.glb` · Served: `/orca/orca.glb` · Constant: `ORCA_MESH_URL` in `web/lib/scene/orca/loadOrcaMesh.ts` | glTF orca model | CC-BY 3.0 (Poly-derived; see repo) | Primary: agent reads it via the referenced GitHub repo link (Prompt 1). Secondary: operator attaches the `.glb` file directly if the attach UI accepts it. Either way, load with `GLTFLoader` (Three.js) or `@react-three/drei` `useGLTF`, attached to a root group you move each frame for horizontal swim. If both fail, fall back to the built-from-description mesh in Prompt 1. |
| Orca mesh (backup) | Served: `/orca/orca-poly-backup.glb` | Lower-poly fallback glTF | CC-BY 3.0 | Same as primary; swap if the primary mesh fails to load. |
| Bathymetry + terrain tileset (**full**, not pilot) | `https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full/tileset.json` | OGC 3D Tiles 1.1 dataset (CUDEM-derived San Juan Islands / Salish Sea bathymetry + terrain, NAVD88 metres, CloudFront + CORS) | Hosted dataset (see orcast tile usage) | Load with any 3D Tiles renderer (orcast uses `3d-tiles-renderer`). Recommended fit: `groupRotationX: -Math.PI/2`, `fitScaleToWidth: 120`, `errorTarget: 16` (see `web/lib/scene/tiles/useTilesLayer.ts`). Extent bounds: `min_lat: 48.4`, `max_lat: 48.7`, `min_lng: -123.25`, `max_lng: -122.75`. |
| Scene geo frame | `web/lib/sceneIntent.ts` | `SCENE_WIDTH=120`, `projectToScene` / `unprojectFromScene`, `sceneDepth(bounds)` — the lat/lng ↔ world mapping frame | orcast internal | Values already transcribed into Prompt 1/2 prose (120-unit width, bounds) — operator does not need to hand this file to the agent. |
| Curated Salish Sea gazetteer | `web/lib/geo/gazetteer.ts` | ~40 real named places (islands, harbors, landmarks) as `{id, name, lat, lng, bounds, kind}`; offline, no network | Curated list in orcast | Primary: agent reads it via the referenced GitHub repo link (Prompt 2) and picks ~8 well-spaced entries. Fallback: an 8-place subset spanning the scene bounds is inlined directly into Prompt 2 below, so the build prompt still works if the repo-reference read doesn't actually happen. |
| World ↔ lat/lng picking | `web/lib/scene/picking/worldPointToLatLng.ts` | Inverts raycast hits to lat/lng via the scene frame | orcast internal | Reference only, for the operator writing Prompt 2's bearing/range math in prose (already reflected there); do not expect the Bash.tv agent to read this file directly. |
| SRKW biologging motion driver (optional ambient) | `/orca/motion/orca_srkw_oo14_driver.json` + sibling `.bin` | Real Southern Resident killer whale biologging track (Tennessen et al. 2024) | CC-BY 4.0 | **Not used for player movement** in this game (the player drives movement). Named in Prompt 3 as an optional flavor-text credit only; do not plan on attaching or fetching the actual driver file. Reference: `web/lib/scene/orca/motion/biologging.ts`. |
| Orca rig / controller reference | `web/lib/scene/orca/OrcaController.ts`, `web/lib/scene/orca/rig/OrcaRig.ts`, `web/lib/scene/orca/motion/biologging.ts` | Locked composition-order rig (orientation, depth, fluke, jaw, eyes) | orcast internal | Operator-side reading only, informs the mesh/pose description already folded into Prompt 1; horizontal X/Z position is **not** owned by this rig pattern in orcast either — same "pilot writes root position" split applies to the from-scratch build. |
| Sandbox template (no bathy) | `web/app/(sandbox)/orca/OrcaSandboxScene.tsx` | Canvas + orca + orbiting chase camera; flat water plane; biologging playback, no player input | orcast internal | Operator-side reference for the chase-camera pattern already described in Prompt 1; not handed to the Bash.tv agent as a file. |
| Camera beat reference (teleport settle) | `web/lib/scene/camera/director.ts` | Eased `flyTo` / `descendTo` / `orbit` for scripted beats | orcast internal | Operator-side reference for the warp/flash beat described in Prompt 2; not for moment-to-moment gameplay camera, not handed to the agent as a file. |
| Marker component pattern | `web/lib/scene/markers/buoyMarker.tsx` | Pure r3f marker; caller owns placement | orcast internal | Operator-side reference informing the boat-marker description in Prompt 2. |
| Tile hook reference | `web/lib/scene/tiles/useTilesLayer.ts` | `TilesRenderer` lifecycle, fit-to-width, z-up → y-up rotation | orcast internal | Operator-side reference for the fit parameters already inlined into Prompt 1 (`groupRotationX`, `fitScaleToWidth`, `errorTarget`); the agent still needs to `npm install` the `3d-tiles-renderer` package itself inside the Bash.tv VM — package-install availability is a BREC open question, not yet confirmed either way. |

**Do not use** the smaller pilot tileset (`https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/pilot/tileset.json`) for this game — use the **full** URL above.

---

## Core mechanics

Transcribed from locked decisions 1, 2, and 9. Do not soften, contradict, or extend these.

### Movement — free swim over bathymetry

- Player pilots the orca with **WASD + mouse-look** (or equivalent keyboard + pointer-look) for free swim over the real bathymetry tileset.
- Horizontal position is integrated each frame from heading + speed (dead reckoning); depth stays in a safe band above the seabed.
- Third-person chase camera follows the orca root.
- The orca swims over the **real bathymetry**, not a flat plane, when the tileset loads correctly. If the tileset URL or fit blocks progress within time budget, a **documented flat water-plane fallback** is acceptable — never a silent fallback.

### Boat-sinking — arcade ram mechanic

- Spawn **floating boat props** on the water surface. Boats are **stylized arcade props**.
- **No AIS or real vessel-traffic data** exists and none is fetched. Boats must **never** be presented as real vessel data.
- Orca **rams / collides** with a boat → boat plays a **sink animation** with a **small splash / particle burst**.

### Sonar ping + instant teleport (Floo-style)

- A **sonar-ping action** reveals a **radar-style readout** of nearby targets:
  - spawned **boats**, plus
  - a **handful of curated gazetteer places** (`gazetteer.ts` destinations)
- Each target shows **bearing and range** from the orca.
- Selecting a pinged target **instantly teleports** the orca there: snap position, play a short **warp / flash beat**.
- This is the **only fast-travel mechanic**. There is **no continuous "swim to" auto-pilot** requirement.

### Required in-scene disclaimer (locked decision 9)

Display this line in-scene:

> **arcade prototype, not navigational or scientific data**

### Honesty boundary (locked decision 9)

- **No acoustic / scientific claims.**
- **No AIS claim.**
- **No navigational claim.**
- Do not present fictional boats as real vessel-traffic data.

---

## Suggested build sequence for Bash.tv (few large prompts)

Bash.tv bills for **VM + agent time per session/turn**. One large, complete spec per turn beats many small back-and-forth clarifications. Batch work into **3 self-contained prompts** below; each prompt should be pasted as a single message and expected to land a working slice before the next prompt.

### Prompt 1 — World scaffold + orca pilot (one turn)

> **STRIKE lane note (2026-07-10):** If building the full Orca Strike game from
> orcast, use `wavves/lanes/20260710_orca-strike-game/deliverable/BASHTV_BUILD_PROMPT.md`
> instead — **repo-pull only**, no `git init`. The HUNT prompts below are for
> from-scratch Bash.tv builds when the sandbox route is not yet on GitHub.

Paste this as one message. The first two sentences are session setup (git checkpointing + reference material) per the platform's own recommended prompt patterns — include them even though this is a single-turn build, they cost nothing extra and make Prompt 2/3 safer:

> Initialize a Git repository and commit after every round of changes. Use the following link as reference material for this project: `https://github.com/GilRaitses/orcast` (a public repo; look for `web/public/orca/orca.glb`, `web/lib/geo/gazetteer.ts`, and `web/lib/scene/tiles/useTilesLayer.ts` if you can read from it). Build a new Three.js + React Three Fiber project (Next.js App Router or Vite + R3F — your choice). Load an orca glTF — try `web/public/orca/orca.glb` from the referenced repo, or attach `orca.glb` as a file if your attach feature accepts it; if neither works, build a simple stylized orca mesh instead (dark grey/black body, white belly patch, dorsal fin, flukes — no need to match a reference exactly). Mount the **full** bathymetry tileset at `https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full/tileset.json` using a 3D Tiles renderer with `groupRotationX: -Math.PI/2`, fit the tileset to a 120-unit-wide scene frame, and `errorTarget: 16`. Implement WASD + pointer-lock mouse-look free swim: integrate heading + speed into orca root X/Z each frame using a **fixed, arcade-scale movement speed independent of the tileset's real-world fit** (do not scale swim speed by the tileset's metres-per-scene-unit conversion — that scale makes real swim speeds imperceptibly slow over a 120-unit scene; pick a fixed per-frame step that feels responsive, e.g. reaching the far edge of the scene in a few seconds at top speed). Clamp depth above seabed. Third-person chase camera. Reimplement a lat/lng ↔ world mapping (a simple linear projection is fine) over bounds `min_lat: 48.4, max_lat: 48.7, min_lng: -123.25, max_lng: -122.75` mapped onto the 120-unit scene frame. If the tileset fails to load or fit within this session, switch to a **documented** flat water plane at Y=0 and note the fallback in a comment. No boats or sonar yet — just swim over terrain with a visible orca.

**Why one turn:** scene frame, tileset fit, input, camera, and orca mount are tightly coupled; splitting them causes rework and extra agent turns.

### Prompt 2 — Boats + sonar + teleport (one turn)

Paste this as one message:

> On the existing orca-strike scene, add: (1) **Boat spawning** — stylized floating props on the water surface (net-new geometry/materials; no AIS data). (2) **Ram collision** — when orca world position enters a boat collision radius, trigger sink animation (rotate/lower) plus a small splash particle burst. (3) **Sonar HUD** — ping action lists nearby targets: all spawned boats, plus real named places. If you can still read the referenced repo, pull ~8 well-spaced entries from `web/lib/geo/gazetteer.ts`; otherwise use these 8 (lat/lng, convert with the same mapping as Prompt 1): Roche Harbor (48.6111, -123.1556), Friday Harbor (48.5343, -123.0179), San Juan Island (48.5333, -123.0833), Deer Harbor (48.6182, -123.0011), Orcas Island (48.6667, -122.9333), East Sound (48.6935, -122.9043), Shaw Island (48.5833, -122.9333), Lopez Island (48.4807, -122.8868). Show bearing and range from the orca for every target. (4) **Instant teleport** — selecting a sonar target snaps orca position to that target's world position and plays a short warp/flash beat (no continuous swim-to autopilot). Boats are arcade props, never labeled as real vessel traffic.

**Why one turn:** sonar range/bearing, boat positions, and teleport destination all share the same geo frame; building HUD without boats (or vice versa) wastes a billing cycle.

### Prompt 3 — Polish + disclaimer (one turn, optional)

Paste this as one message:

> Polish pass on the orca-strike prototype: tune chase camera lag/distance, improve splash/particle FX on boat sink, add minimal UI chrome for sonar ping and target selection, and display the required disclaimer line **"arcade prototype, not navigational or scientific data"** persistently in-scene. Optional: wire idle fluke animation driven by swim speed; optionally add a one-line credit "orca movement style informed by real Southern Resident killer whale biologging (Tennessen et al. 2024)" as flavor text only — no data file is attached or fetched for this. Player movement stays input-driven. Do not add AIS, acoustic estimates, or navigational claims.

**Why one turn:** polish items are independent of core wiring and safe to batch once mechanics work.

---

## Explicit non-goals

Do **not** build or imply any of the following (from locked decisions 1, 2, and 9):

| Non-goal | Reason |
|---|---|
| AIS / real vessel / ferry / shipping-lane data | None exists in orcast; boats are fictional arcade props |
| Presenting boats as real vessel-traffic data | Locked decision 1 |
| Scientific, acoustic, or navigational claims | Locked decision 9 |
| Continuous "swim to" autopilot beyond one-shot teleport | Locked decision 2 — instant teleport is the **only** fast-travel mechanic |
| Fetching or displaying live marine traffic | Out of scope; no data source |
| Workbench-style measured/modeled honesty machinery | HUNT is arcade-only; the single disclaimer line is sufficient |

---

## Notes for the Bash.tv operator

**Resolved, most recently by the operator-provided Discord Q&A with the Sup Team** (layered on top of the earlier video/PDF-only BREC recon; both are recorded in `wavves/lanes/20260710_bash-ecosystem-recon/findings/BREC-capabilities.md`):

1. **Repo access:** Yes, two confirmed paths — a public GitHub link given as reference material ("if its a public github link you can give it the link and it can reference it"), which `orcast` qualifies for, and direct file attachment ("you can add files to the agent and it can add them to the app," not limited to images as the video alone suggested). Fidelity of the reference path (verbatim read vs. paraphrase) is still not confirmed, so this prompt package uses the GitHub link as the *primary* path in Prompt 1 and keeps every inlined prose value as a fallback rather than relying on the link alone.
2. **Gazetteer subset:** 8 well-spaced entries inlined directly into Prompt 2, with an instruction to prefer pulling from the referenced repo's `gazetteer.ts` first if that read actually works.
3. **Execution model:** Confirmed single-agent, serial-prompt-queue per space ("it runs in queue") — no in-space parallel/background subagents. The Sup Team does confirm you can run **two separate Bash spaces at once** ("you can experiment with working from two bashes at once"), but Prompts 1-3 below are intentionally kept sequential in one space, since the scene frame, tileset fit, boat/sonar geo math, and camera are too tightly coupled to safely split across two independently-queued spaces.
4. **Version control / checkpoints:** Folded into Prompt 1's opening line ("Initialize a Git repository and commit after every round of changes") per the Sup Team's own recommended pattern, so a bad Prompt 2 or 3 result can be rolled back without losing Prompt 1's work.
5. **Getting the finished build back out:** Confirmed possible — `"Create a zip of the project and give me a link to download it."` Use this after Prompt 3 if the build needs to be archived or handed off.

**Still open (do not guess — decide at runtime if needed):**

1. **Boat count / spawn layout:** Not specified in the charter. Default to a small fixed spawn set (e.g. 3–6 boats) scattered within the tileset bounds unless the operator sets a number before Prompt 2.
2. **Flat-plane fallback trigger:** Locked decision 8 allows a documented flat water-plane fallback if the real tileset blocks progress. Define "blocks progress" at Prompt 1 time (e.g. tileset fails to load within N minutes, or fit sphere never resolves).
3. **SRKW biologging:** Optional ambient asset only; player movement must remain input-driven regardless. Treated as flavor text only in Prompt 3, not a loaded asset, since the driver JSON's own import fidelity is unconfirmed.
4. **`.glb` load fidelity:** Whether the referenced-repo read or the direct file attach actually loads the real mesh (vs. the agent building a placeholder anyway) is unverified until you watch Prompt 1 run. The built-from-description fallback mesh in Prompt 1 covers this either way.
5. **npm/pip package install and VM internet access:** Neither is confirmed, and `web/lib/scene/tiles/useTilesLayer.ts`'s `3d-tiles-renderer` package plus its runtime fetch of the tileset URL depend on both. If Prompt 1's tileset mount fails for either reason, that's expected to trigger the documented flat-plane fallback, not a retry loop.

**Model / thinking-level guidance:** the Sup Team confirms model and thinking-level can be switched per prompt, and that mixing tiers is often cheaper and better than one config throughout. Suggested for this 3-prompt sequence: a stronger/higher-reasoning model for **Prompt 1** (tileset fit + camera + input coupling is the hardest slice to get right first try), the same or a step down for **Prompt 2** (mostly additive, same geo frame), and a fast/cheap tier for **Prompt 3** (polish only). OpenRouter image generation is available if richer boat/splash art is wanted beyond code-driven placeholder geometry, but is not required for any locked mechanic here.

**Credit discipline recap:** 3 large prompts ≈ 3 billed agent turns for a complete playable prototype, run in one space, sequentially, with git checkpoints after each. Avoid a 4th turn unless Prompt 2 leaves a named gap (e.g. teleport works but sonar list is empty).
