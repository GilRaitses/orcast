# BSW-R12 - Skill catalog extension + behavior-capture via demo director

> Read-only research finding (BSW-RESEARCH wave). Repo verified against `240570e`.
> Authored by explore agent 7be21f; written by the BSW sub-orchestrator.

## Summary

- **Central Casting already supports managed skills end-to-end.** Skills are declared in `skills_manifest.json`, dispatched in `skills.py` (`_DISPATCH`), tier-gated (T0-T3) on `/api/interactions`, and surface UI via `panel_registry.json` + planner `allowed_panels`. Extending it for BSW = additive manifest entries + dispatch handlers + panel registrations; no framework change.
- **The demo-production director is reusable for behavior capture.** `20260628_demo-production` defines a SET/BLK/CAM/SCR staged process driven by `director.ts` camera APIs + Playwright capture. BSW behavior-capture = drive the scrub timeline to a real classified DTAG behavior span, point camera via director, capture frames/clip per behavior class.
- **Capture must use REAL classified behaviors.** Sources: real SRKW DTAG driver clips (kinematic) + real acoustic classifier presence windows (acoustic). The humpback 9-class ethogram is contrast/reference only; do not capture "humpback foraging" labeled as orca.
- **Tiering:** capture-trigger + skill-mutation skills are T2/T3 keyed; read/playback skills T0/T1. All capture artifacts (mp4/png/gif) -> box/S3, not git.
- **Standin-free fallback:** if automated capture is out of scope, the manual director beats still produce real captures; never ship a synthetic "behavior" loop.

## In-repo findings (cited)

### Skill registration + tiering
`skills_manifest.json` declares skills; `skills.py` `_DISPATCH` maps id -> `exploration.tools.*`; `panels.py` validates panel ids against `panel_registry.json` + cast `allowed_panels`. Tier gate: T0/T1 public on `/api/interactions`; T2/T3 require key; unknown -> 400; tier mismatch -> `tier_blocked`. Manifest shape `{id, tier, geo_required, produces_annotations[], data_bindings[]}` (see `SKILL_CATALOG.md`, `MANAGED_AGENTS_CONTRACT.md`).

### Demo-production director process
`20260628_demo-production` charter + `web/lib/scene/camera/director.ts` give staged automation:
- **SET** - scene/state preconditions (mount rigs, load driver clip, set timeline).
- **BLK** (blocking) - position actors (orca instances) + timeline cursor.
- **CAM** - camera moves via `flyTo`/`descendTo`/`orbit` to behavior-relevant POV.
- **SCR** (capture) - Playwright drives the page, advances timeline, captures frames/video per beat.

This is exactly the loop needed to capture a behavior: set timeline to a classified span, frame it, record it.

### Timeline + classification inputs
- Kinematic: real SRKW driver `orca_srkw_oo14_driver.json` (`simulated:false`, CC-BY-4.0) -> motion clips by frame window (per BSW-R04).
- Acoustic: classifier presence windows (per BSW-R03 honest target = binary SRKW-call presence; **not** count/type).
- Timeline authority: `SpectroTimelineAuthority` (per BSW-R06) is the scrub source BRE/capture subscribe to.

## BSW skill catalog (proposed) + behavior-capture beat set

### Proposed skills

| Skill id | Tier | Wraps | Panel | Honesty |
|----------|------|-------|-------|---------|
| `capture_behavior_clip` | T2 | director SCR beat runner | `capture_studio` | measured-derived |
| `list_classified_spans` | T1 | acoustic+kinematic span index | `tag_series` | measured |
| `seek_timeline_to_span` | T0 | `SpectroTimelineAuthority.seek` | `spectrogram_hud` | measured |
| `frame_behavior_pov` | T1 | `director.flyTo/descendTo/orbit` | scene | modeled (camera) |
| `register_captured_behavior` | T2 | persist capture artifact + provenance | `capture_studio` | measured-derived |

### Capture beat set (per behavior span)
1. **SET** - load SRKW driver clip for span; mount N orca instances (BSW-R08); set spectrogram timeline to span start.
2. **BLK** - position primary orca at span; secondary instances staged off-frame.
3. **CAM** - `descendTo` hydrophone POV or `orbit` the foraging dive; honor LGC POV tokens.
4. **SCR** - Playwright advances timeline across the span at fixed rate; capture frames -> mp4/gif; stamp provenance `{deployment_id, frame_start/end, behavior_class, acoustic_presence, honesty}`.
5. **ARTIFACT** - upload to box/S3; emit `artifact_citation` with content hash.

## Recommendations with cost + standin-free fallback

| Rec | Detail | Cost | Fallback |
|-----|--------|------|----------|
| R1 | Add BSW skill block to manifest + dispatch + panel registry | ~2 eng-days | manual director beats (no skill wrapper) |
| R2 | Reuse `20260628_demo-production` Playwright SCR runner for `capture_behavior_clip` | ~2-3 eng-days | hand-run capture, same real spans |
| R3 | Capture artifacts -> box/S3 with provenance; web carries pointers | infra only | n/a |
| R4 | T2/T3 gate capture + register skills; T0/T1 read/seek | low | n/a |
| R5 (O0) | Confirm which behaviors are real-classifiable for capture (acoustic presence + kinematic span) vs deferred | O0 gate | capture kinematic spans only; label acoustic as presence-only |

Standin-free fallback: manual director beats over real classified spans. Never a fabricated behavior loop.

## Open questions / flags for O0

1. Which behavior classes are demo-capturable with real classification (acoustic presence + real SRKW kinematic span), and which are deferred?
2. Capture artifact license/hosting (box/S3) + provenance retention?
3. Reuse demo-production cast/seeds directly, or fork a BSW capture cast?
4. Overclaim guard: capture labels must say "SRKW-call presence + kinematic span", never "orca doing X because audio said so" unless coupling is cited (BSW-R05).
5. Tiering: are capture-trigger skills operator-only (T3) for the demo?

## Sources

**orcast (240570e):** `src/aws_backend/casting/{skills.py,skills_manifest.json,panels.py,panel_registry.json,planner.py}`, `web/lib/scene/camera/director.ts`, `docs/devpost/casting/{SKILL_CATALOG.md,MANAGED_AGENTS_CONTRACT.md,INTERACTIONS_GROUNDING_PATTERN.md}`, `.cca/catalogue/O0/20260628_demo-production/` charter + beats, `BSW-STUDIO-SKILLS_CHARTER.md`, `PROGRAM.md`, `research/{BSW-R03_acoustic_ml.md,BSW-R04_kinematic_ethogram.md,BSW-R06_spectro_hud.md,BSW-R08_multiorca_reenactment.md,BSW-R10_annotation_studio_viz.md}`

**External:** `orca_srkw_oo14_driver.json` provenance (CC-BY-4.0), Playwright docs (capture runner).
