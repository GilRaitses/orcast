# B-side acoustic + behavior research workbench - program

Curated 2026-06-29. The "B-side" of orcast: the behavior-analysis research workbench that turns
hydrophone sound and DTAG biologging into a navigable, replayable encounter in the 3D twin. A
station player puts a hydrophone-equipment model underwater, plays real archived audio, shows a
scrubbable spectrogram HUD, classifies what is heard (how many / what type of orcas), and replays
the encounter as data-driven orca motion in the world model - viewable from the hydrophone POV or
top-down. Built as one **research wave shell** followed by **five disjoint charters**, so each is a
clean lane a background agent can own.

- Family code: **BSW**. Home: `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/`.
- `repo_state_verified_against`: origin/main `240570e961913fb610c2765a4ef77cace3f216f1` (branch main, 2026-06-29).
- Charter method: `~/.cursor/skills/waveset-orchestration/SKILL.md`.
- Render runtime: react-three-fiber / `three` (same as the twin). Lands in the twin's underwater
  view; developed in net-new sandboxes first.
- Serializes against: **LGC, CVP, ORCA, WFX, 3D-TWIN** on the shared convergence files
  (`web/app/components/scene/SalishScene.tsx`, `web/app/globals.css`,
  `web/app/components/AdaptiveExplore.tsx`, `web/app/components/ActiveSurfaceHost.tsx`).

## Intent (operator)

"Get a 3D model that represents close enough what the hydrophone equipment looks like and show it
under the water when a station is chosen, then replay the sounds in a stylized way from many
perspectives. The orca's biosonar POV might persist a layer carrying the larger ocean processes -
the double diffusion of salt water going down and cold mineral-rich water coming up, like a lava
lamp in both directions. Replay these signals, and from community annotations train the
segmentation model for the whale sounds to describe what it thinks it is - how many and what type
of orcas - and let that drive the replay with the orca models. Want a spectral visualizer like the
research pages, as a HUD in the terrain bathymetry model. The station player lets you select things
and see it from the POV of the hydrophone or top-down; an interactive camera-selection object that
extends from the LGC. Scrub or slow the sound and see the reenactment in the 3D world with the
orcas, their dive behavior classified from the existing DTAG sets for the kinematics. Deep research
wave shell first, then charter the phases. Want it in the demo for the B side. Also an annotation
UI: start from the analysis .h5, mine the schema for the MLops, a managed agent skill catalog that
can block / camera-test / screen-test and capture orca behaviors in the 3D models from classified
DTAG examples. Make an annotation framework that includes the poster-folder visualization methods
as managed skills for invoking HUDs, and put tagtools UIs into a reusable processing-pipeline
studio the orchestrated console can invoke. Part of the B-side demo campaign."

Two faces of the same lane: **acoustic** (hydrophone sound -> who/what is out there) and
**kinematic** (DTAG -> how the animal moves), joined in a scrub-synced reenactment in the twin.

## The deliverable shape

```
research wave shell (BSW-RESEARCH, ~14 read-only agents)
  -> SYNTHESIS_bside.md -> PAUSE to O0
     -> ONE real demo slice (one station, one real clip, end-to-end, no standins)
     -> five breadth charters, phased build / integrate / accept
```

## The research wave shell (Wave 1, read-only)

`BSW-RESEARCH` is the "very deep wave shell" the operator asked for: ~14 parallel read-only agents,
each owning one `research/BSW-R{NN}_<topic>.md`, one adversarial member, then a sub-orchestrator
synthesis `research/SYNTHESIS_bside.md`. It grounds all five charters before any build. Defined in
`wave_shape.yml`; dispatched via `ORCHESTRATOR_DISPATCH_PROMPT.md`.

## The charters (post-synthesis; research can ground all in parallel)

| Code | Charter | Owns (net-new) | Produces |
|---|---|---|---|
| **BST** | `BSW-STATION_CHARTER.md` | `web/lib/scene/hydrophone/`, `web/public/hydrophone/`, `web/app/(sandbox)/station/` | hydrophone-equipment mesh placed underwater on station select; station player + camera POV-selection object (hydrophone POV / top-down) extending LGC tokens; binds the unused `streamUrl` + real Orcasound archived audio |
| **BAM** | `BSW-ACOUSTIC-ML_CHARTER.md` | `infra/acoustic/`, `modeling/acoustic/` | real MLops pipeline (community annotations -> labels -> train -> eval) AND a first real trained acoustic classifier (presence / call-type / count), honest metrics; weights to the box |
| **BSH** | `BSW-SPECTRO-HUD_CHARTER.md` | `web/lib/scene/hud/spectro/`, `web/lib/scene/ocean/` | scrubbable WebAudio spectrogram HUD over the twin, time-synced to scrub/slow; plus the labeled-interpretive double-diffusion ocean-process layer |
| **BRE** | `BSW-REENACTMENT_CHARTER.md` | `web/lib/scene/reenactment/`, `web/lib/scene/orca/motion/clips/` | scrub/slow audio -> multi-orca reenactment driven by classified behavior (kinematic) + real DTAG motion; camera POV selection wired to `director.ts` |
| **BSS** | `BSW-STUDIO-SKILLS_CHARTER.md` | `web/app/(workbench)/`, `infra/tagtools/`, `src/aws_backend/casting/` additions | annotation UI (audio + kinematics) + reusable tagtools/animaltags pipeline studio the console can invoke; poster viz methods registered as managed Central Casting HUD skills; behavior-capture automation reusing the demo-production director process |

## Grounding (verified, 240570e)

- **Hydrophone:** catalog API `GET /api/live-hydrophones` (`src/aws_backend/routers/read.py` ->
  `OrcasoundHydrophoneAdapter`, `src/aws_backend/sources/orcasound.py`) returns real station
  `id/name/lat/lng/status/streamUrl`. `streamUrl` (`https://live.orcasound.net/listen/{slug}`) is
  emitted on scene click (`SalishScene.tsx`) but **consumed nowhere**. Station catalog:
  `src/integrations/orcasound_hydrophones_for_orcast.json`, `live_orcasound_feeds.json`
  (slug/bucket/node_name/coords). ML station coords: `modeling/studies/common.py`.
- **Spectrogram today is a static `<img>`** (ONC PNG) in
  `web/app/components/console/HydrophoneSignalPanel.tsx` via `src/aws_backend/routers/onc.py`
  (needs `ONC_API_TOKEN`). No WebAudio, no canvas, no audio player in `web/`.
- **DTAG:** backend `/api/dtag/*` (`src/aws_backend/routers/dtag.py`) is ready but the bundled
  fixture `data/dtag_analysis_results.json` is `simulated:true`; no `web/` consumer; not on the
  public proxy allow-list (`web/app/api/be/[...path]/route.ts`).
- **Real kinematics asset exists:** the SRKW driver (Tennessen et al. 2024, CC-BY-4.0) landed in
  `web/public/orca/motion/orca_srkw_oo14_driver.{json,bin}` (`simulated:false`), 7-channel float32
  format with `track.sample(t)` interpolation (`web/lib/scene/orca/motion/biologging.ts`). Orca
  stack: `web/lib/scene/orca/` (controller/rig/materials/eyes/mouth/physics). Multi-orca = duplicate
  the `OrcaRig` mount with a distinct anchor + motion URL.
- **Real humpback DTAG h5:**
  `/Users/gilraitses/whale-behavior-analysis/Visualization_Poster_Appendix/data/dive_analysis.h5`
  (99,925 samples @ 5 Hz). Already-derived REAL products: 128 dives + descent/bottom/ascent phase
  segmentation, 51 manual expert annotations, a 9-class behavior taxonomy
  (`behavior_mapping.json`), tagtools stroke/glide (670 glides, 2405/2439 stroke peaks/troughs),
  ODBA/VDBA/jerk, validation behavior masks. **No shipped automated classifier** (the minGRU one
  is described but its artifacts show 0% accuracy). Used previously to bake the humpback contrast
  track. Humpback is **contrast/reference only**; it never drives an orca.
- **Poster viz methods** (`/Users/gilraitses/whale-behavior-analysis/Visualization_Poster_Appendix/scripts/`):
  R + ggplot2 (composite kinematic dashboard, dive overview, per-dive frames, energetics scatter,
  all static PNG) and one **interactive Plotly 3D dive lattice** (HTML). Candidate managed HUD
  skills. No spectrogram / ethogram / track-map exists yet (greenfield).
- **Scene frame:** `web/lib/sceneIntent.ts` `projectToScene(lat,lng,bounds,depth)`, `TILESET_BOUNDS`
  (48.4-48.7 lat, -123.25--122.75 lng), `SEA_LEVEL_Y=0`, `worldUnitsPerMeter` from tile fit; vertical
  via `Y=-depth_m*worldUnitsPerMeter`. Camera: `web/lib/scene/camera/director.ts`
  (moveTo/descendTo/followPath/orbit) + `web/lib/journey/controller.ts`.
- **Console/intent:** `web/app/components/AdaptiveExplore.tsx` (two-phase plan->narrate turn) +
  `web/app/components/ActiveSurfaceHost.tsx` (renders planner `ui_intent.panels`) + `web/lib/uiIntent.ts`.
  Planner `surface-planner-v1`; panels are allowlisted ids.
- **LGC** is chartered but **unbuilt** in `web/` (no glass tokens, `GlassSurface`, or focus model);
  CVP is the active baseline-styling lane on the same hot files. **Managed skills** = backend
  Central Casting (`src/aws_backend/casting/skills.py`, `docs/devpost/casting/SKILL_CATALOG.md`),
  not Cursor skills.
- **Demo director process** (reuse for B-side capture):
  `.cca/catalogue/O0/20260628_demo-production/` (PROGRAM/BEAT_SET/NARRATION, blk/cam/scr stages).

## Locked decisions (do NOT reopen)

- **No standins in the demo.** The slice is real end-to-end: real archived hydrophone audio, a
  real spectrogram computed from that audio, a real (small but trained) classifier's real output,
  and reenactment driven by real DTAG kinematics. No canned/scripted classification, no fabricated
  detections, no placeholder "swim loop" pretending to be data.
- **Honesty labels.** `measured` (recorded audio, DTAG telemetry) vs `modeled` (mesh, motion
  mapping, equipment model) vs `interpretive`. The orca is a modeled animal; its motion is driven
  by real (or clearly-labeled simulated) telemetry. The HUD says which is which.
- **The double-diffusion / thermohaline "lava lamp" layer is `interpretive`.** Double-diffusive
  convection is real Salish Sea oceanography, but "orca biosonar perceives it" is speculative; it
  ships as a clearly-labeled interpretive layer, never claimed as measured orca cognition.
- **Two ML tracks stay separate.** ACOUSTIC (sound -> who/what) and KINEMATIC (DTAG -> how it
  moves) are different data, different models. Acoustic drives WHICH orcas appear; kinematic drives
  HOW they move. Orca motion comes from real SRKW DTAG; the humpback h5 is contrast/reference only.
- **License + privacy first.** No audio clip, annotation corpus, dataset, or mesh ships without a
  verified open license (CC0/CC-BY/permissive) recorded with source URL + attribution. Any NC/ND/
  unclear license: STOP and return to O0.
- **Read-only research first.** `BSW-RESEARCH` writes only findings docs; downloads, training, and
  any `web/` edits run on later gated waves. No `next dev`/`next build` in a parallel wave; `tsc`
  clean; net-new files preferred; commit is an operator gate.
- **Built on `three` + existing stack.** A new runtime dependency (audio/FFT/3D lib) is a costed
  recommendation, not a default. Compute-neutral: any new render pass joins the existing depth
  pre-pass or is costed against the 60fps-desktop / 30fps-laptop budget.
- **Heavy assets to the box (S3), not git:** audio, model weights, baked motion tracks, large h5
  derivatives. Gitignored + documented with a re-fetch pointer.
- **Slice uses a minimal local glass surface aligned to LGC tokens;** full LGC integration is
  deferred (LGC is unbuilt). Do not block the B-side on LGC; coordinate token names via O0.

## Escalation (operator-protection catch)
The dispatched sub-orchestrator answers to **O0, not the human operator**. Any license/privacy
ambiguity, dependency choice, partnership/data-access question, model-feasibility or overclaim
risk, locked-decision conflict, regression, or gated step: **pause and return to O0**. No First AD
solicits the human.

## Registry
Family BSW (umbrella) + the research wave and five charters registered in
`docs/devpost/waves.registry.yaml`. Downloads, training, integration, and commit are operator gates.
