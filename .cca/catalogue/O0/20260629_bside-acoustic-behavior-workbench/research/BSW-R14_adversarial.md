# BSW-R14 - Adversarial audit (skeptic-in-residence)

> Read-only research finding (BSW-RESEARCH wave). Repo verified against `240570e`.
> Authored by explore agent d40f12; written by the BSW sub-orchestrator.
> Mandate: assume every claim is wrong until proven; surface license, perf, honesty, scope, and collision risks before O0 signs the slice.

## Top risks (ranked)

### 1. LICENSE BLOCKER - Orcasound archived audio + community corpora are CC BY-NC-SA 4.0
- Orcasound archived audio, Pod.Cast, OrcaHello annotations are **CC BY-NC-SA 4.0**. **NonCommercial** clause is incompatible with anything that reads as commercial (hackathon prize, hosted product, sponsor demo). **ShareAlike** forces derived models/spectrograms under the same NC-SA terms.
- **STOP-to-O0.** Either (a) get written permission from Orcasound, or (b) build the demo slice on a genuinely open source: **DCLDE-2027 (CC-BY 4.0)** for SRKW presence/ecotype, and a CC-BY/CC0 audio clip. Until cleared, **no NC audio in the shipped slice.**
- Live HLS stream (real-time listening) is a different use than redistributing archived clips/derived models; do not conflate.

### 2. OVERCLAIM - "how many orcas / what call type" is not honestly achievable
- BSW-R03 sets the honest target: **binary SRKW-call presence + confidence**. Count, pod ID, ecotype, individual ID, localization are **NOT achievable** from a single hydrophone with available open labels.
- Risk: HUD or narration says "3 orcas, resident call type S1" -> fabrication. **Guard:** classifier output schema must be presence + confidence only; any count/type label requires a cited corpus that supports it (none open does for count).

### 3. CROSS-SENSOR SYNC ILLUSION - audio and DTAG motion are different animals/encounters
- The demo couples real Orcasound audio (one encounter, hydrophone) with real SRKW DTAG kinematics (`orca_srkw_oo14_driver`, a different animal/time). Scrubbing audio and showing synchronized motion **implies the motion is that audio's animal** - it is not.
- **Guard:** on-screen label "kinematics: representative SRKW DTAG, not the recorded animal"; acoustic drives *which* clip class + spawn, never the literal trajectory. (BSW-R05 separation.)

### 4. INTERPRETIVE LAYER MISREAD AS DATA - double-diffusion "lava lamp"
- Salt-fingering staircases are **not** the dominant Salish process (BSW-R09). Rendering bidirectional plumes risks reading as measured ocean microstructure or "what the orca sees."
- **Guard:** mandatory `interpretive` chip; ground in cited CC0 CruiseSalish T/S; forbid "measured thermohaline" / "biosonar perception" copy.

### 5. NO REAL ACOUSTIC CLASSIFIER EXISTS IN-REPO
- Today: static ONC PNG only (`HydrophoneSignalPanel.tsx`). The "real classifier output" leg of the no-standin slice **does not exist** and must be built (BAM). Risk: demo slips to a canned label.
- **Guard:** if classifier is not ready, ship presence-only via a real pretrained open detector (OrcaHello-style, license permitting) or precomputed real inference JSON for the chosen clip - never a hardcoded "orca detected".

### 6. PERF - N orcas + spectrogram HUD + ocean layer on laptop 30 fps
- Baseline twin already pays ~2U (Water2Rig pre-pass). BSW-R08 flags N=5 orcas may strain laptop; BSH spectrogram Worker STFT + Canvas; BSH ocean layer 0.35-0.85 ms. Stacked, the 30 fps laptop budget is at risk.
- **Guard:** preset-gate (laptop caps N orcas, disables ocean layer); GPU-host A/B acceptance with each layer on/off.

### 7. CONVERGENCE COLLISION - SalishScene.tsx nexus
- Six lanes (WFX/ORCA/LGC/CVP/3D-TWIN + 5 BSW charters) edit `SalishScene.tsx`. Uncoordinated merges break mount order / the single depth pre-pass invariant.
- **Guard:** serialize per BSW-R13 Phases A-F; one owner arbitrates mount order.

### 8. LGC DEPENDENCY - tokens unbuilt
- Every BSW HUD wants LGC glass tokens; `globals.css` has none. Risk: BSW blocks on LGC or ships inconsistent glass.
- **Guard:** local `.bsw-glass` fallback; swap when LGC lands.

### 9. R-RUNTIME / GPL CREEP - poster viz + tagtools
- ggplot2 PNGs + `tagtools` (GPL-3) tempt an R sidecar in the hot path (cold starts, copyleft). 
- **Guard:** offline R batch on box; ship artifacts only; Python primitives for recompute; isolate GPL.

### 10. DEADLINE vs SCOPE - five charters is a lot
- Five charters (station, acoustic ML, spectro HUD, reenactment, studio/skills) + research is broad for one demo. Risk: shallow everywhere.
- **Guard:** O0 picks ONE vertical slice (proposed in SYNTHESIS) to land end-to-end; others are follow-on.

## Honesty-label audit (measured / modeled / interpretive)

| Element | Correct label | Overclaim risk |
|---------|---------------|----------------|
| Orcasound audio | measured | license (NC) not honesty |
| Spectrogram | measured (derived from audio) | none if from real clip |
| Acoustic classifier output | modeled (inference) | count/type overclaim |
| SRKW DTAG motion | measured (real tag) | "this audio's animal" |
| Orca mesh / rig | modeled | none if labeled |
| Hydrophone equipment mesh | modeled | mesh license |
| Ocean-process layer | **interpretive** | "measured ocean" / "biosonar" |
| Humpback h5 / poster viz | measured (humpback) | species conflation w/ orca |

## STOP-to-O0 flags (consolidated)

1. **CC BY-NC-SA audio + annotations** (R01, R02, R14) - resolve license before shipping any NC asset.
2. **LiveOcean** unclear redistribution license (R09) - exclude or clear.
3. **ONC partner CC-BY-NC** subsets (R09) - verify per-dataset.
4. **whale-behavior h5 + 51 manual labels** redistribution scope (R10, R11).
5. **Hydrophone equipment mesh** license if external CAD (R07).
6. **Count/type acoustic claim** must be removed from any copy (R03, R14).
7. **Cross-sensor sync** label required (R05, R14).
8. **Interpretive ocean label** required (R09, R14).

## Recommendations (adversarial bottom line)

- Do not ship any CC-NC asset in the demo slice until O0 clears it; default to DCLDE-2027 (CC-BY) + a CC-BY/CC0 audio clip.
- Lock classifier output to presence + confidence; ban count/type in UI strings.
- Mandatory on-screen labels: cross-sensor representativeness, interpretive ocean, modeled mesh.
- Preset-gate perf; GPU-host A/B acceptance.
- Serialize SalishScene.tsx edits; one mount-order arbiter.
- Pick one end-to-end vertical slice; treat the other four charters as follow-on.

## Sources

**orcast (240570e):** `web/app/components/console/HydrophoneSignalPanel.tsx`, `web/app/components/scene/SalishScene.tsx`, `web/app/components/AdaptiveExplore.tsx`, `web/lib/scene/water2/depthWater.ts`, `PROGRAM.md`, all five charters, `research/{BSW-R01..R13}.md`

**External (licenses):** Orcasound (CC BY-NC-SA 4.0), Pod.Cast / OrcaHello (CC BY-NC-SA 4.0), DCLDE-2027 (CC-BY 4.0), LiveOcean (experimental, no clear license), `tagtools` (GPL-3), SalishSeaCast (Apache 2.0), CruiseSalish/NCEI 0307188 (CC0).
