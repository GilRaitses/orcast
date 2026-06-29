# BSW-R10 - Annotation studio + poster-viz as managed skills

> Read-only research finding (BSW-RESEARCH wave). Repo verified against `240570e`.
> Authored by explore agent ec90f41f; written by the BSW sub-orchestrator.

## Summary

- **Console seam is prepare-then-narrate:** `AdaptiveExplore.tsx` calls `/api/interactions/plan`, paints `ui_intent.panels` via `ActiveSurfaceHost.tsx`, then streams narration. Panel ids are allowlisted in agent `policy.allowed_panels` and validated against `panel_registry.json`; client-side injection (e.g. `hydrophone_signal`) is an existing precedent for scene-driven panels.
- **Real h5 ground truth:** `dive_analysis.h5` (99,925 samples @ 5 Hz, 128 dives, 121 datasets). Manual ethogram: 51 rows in `log_mn09_203a.csv` (50 labeled + 1 End), 9-class taxonomy in `behavior_mapping.json`, annotation groups at `/annotations/*` and validation masks at `/analysis/validation/behaviors/types/*`.
- **Poster viz inventory (5 methods):** three ggplot2 static figures + 128 per-dive PNGs should **server-render via existing R scripts** (offline/box, not hot App Runner path); Plotly 3D lattice should **port to Plotly.js** in a HUD panel with **pre-rendered HTML iframe fallback**; energetics scatter is a strong **JS port** candidate (128 points) with R PNG as acceptance fallback.
- **No kinematic annotation write API exists yet.** Interaction `annotations[]` are grounding citations persisted on Postgres turns. Behavioral round-trip is chartered as **B-ANNOT** (span schema + versioned taxonomy + provenance envelope) and must extend beyond `POST /api/community/sightings` (geo sightings, different schema).
- **Managed skills extend Central Casting:** register read skills in `skills_manifest.json` + `skills.py` dispatch; pair each viz skill with a HUD panel in `panel_registry.json`, `uiIntent.ts` labels, `ActiveSurfaceHost.tsx` renderer, planner `allowed_panels`. Heavy PNG/HTML artifacts land on the box/S3.
- **R runtime is a costed dependency, not default:** recommend offline R batch (reuse `run_all.R`) + artifact URLs for production skills; standin-free fallback is pre-baked artifacts + JS ports, never synthetic figures.

## In-repo findings (cited)

### Console invocation (plan -> panels -> narrate)

```137:148:web/app/components/AdaptiveExplore.tsx
        const resp = await runAdaptiveTurn(sid, ctx);
        if (extraPanel) { hydrophonePanel.current = extraPanel; }
        if (hydrophonePanel.current) {
          const exists = resp.ui_intent.panels.some((p) => p.id === "hydrophone_signal");
          if (!exists) { resp.ui_intent.panels = [hydrophonePanel.current, ...resp.ui_intent.panels]; }
        }
        setPlan(resp);
```

```237:245:web/app/components/AdaptiveExplore.tsx
      const extraPanel: UiIntentPanel | null =
        intent.type === "hydrophone"
          ? { id: "hydrophone_signal", surface: "sidebar", priority: 0,
              props: { station: intent.name ?? null, lat: intent.lat, lng: intent.lng } }
          : null;
```

Public planner allowlist (`adaptiveConsole.ts:41-54`) includes `hydrophone_signal`, `map_viewport`, `explore_trace`, `gates_summary`, `provenance_*`, trip panels. `ActiveSurfaceHost.tsx` `renderPanel` switch; unknown ids return null. **No B-side workbench panels yet** (`tag_series`, `dive_panel`, `label_editor` chartered in BSIDE_CHARTER but absent).

Panel validation (`src/aws_backend/casting/panels.py`) checks `panel_registry.json` (13 panels) + allowlist; **`hydrophone_signal` is not registered** (client injection only). New BSS panels must be added to registry + seed allowlists.

### Managed skills (Central Casting)
Dispatch in `skills.py` maps skill ids to `exploration.tools.*`. Tiering (`SKILL_CATALOG.md`): T0/T1 public on `/api/interactions`; T2/T3 keyed; unknown/disabled -> 400; T2/T3 on public -> `tier_blocked`. Manifest entry pattern: `{id, tier, geo_required, produces_annotations[], data_bindings[]}`. **No poster-viz or h5 skills exist.**

### Existing annotation persistence (two meanings)
1. **Interaction grounding annotations** (read-path citations): `gate_citation`, `provenance_citation`, `artifact_citation`, etc., persisted on assistant turns via `save_interaction_exchange` -> Postgres `exploration_turns.interaction_steps`.
2. **Community/expert behavioral submissions** (write-path, different domain): `POST /api/community/sightings` -> DynamoDB with coarse behaviors {feeding, traveling, socializing, resting, unknown}; hydrophone annotate button is gated UI only; DTAG read API exposes `taxonomy_version: "unratified-0"`, no annotation CRUD. **B-ANNOT (chartered, not built):** "annotation span schema + versioned taxonomy registry + prediction provenance envelope."

orcast has **h5 pre-bake precedent** (`infra/orca/biologging/prebake.py`, box-bound, honesty labels). H5 is **not in repo** (operator path is external whale-behavior export).

## Poster-viz inventory (each method: what it shows, h5 inputs, render decision, cost, fallback)

Path: `Visualization_Poster_Appendix/scripts/`. Driver `run_all.R`. Config `data_config.yaml`.

| # | Script / output | What it shows | Primary inputs | Decision | Cost | Standin-free fallback |
|---|-----------------|---------------|----------------|----------|------|------------------------|
| 1 | `03_composite_dashboard.R` -> `01_composite_dashboard.png` | Multi-panel event dashboard (pitch/roll/head, norm jerk, depth, phase) for longest annotated event | CSV `mn09_203a.csv` + `log_mn09_203a.csv`; `calculate_normjerk()` | **Server-render PNG** | R + tidyverse + patchwork; ~10-30 s/event | Pre-bake PNG per span on box; JS fallback: simplified 4-panel from h5 slices, labeled "simplified, not poster-identical" |
| 2 | `04_dive_overview.R` -> `02_dive_overview.png` | Full-deployment depth vs ETI, color/width = twistiness | h5 `/depth/values`, `/eti/values`, `/data/{pitch,roll,head}`, `/dives/dive_indices`; `signal` pkg | **Server-render PNG** | R + signal + viridis | Pre-bake PNG; JS fallback: depth-vs-time without twistiness encoding, labeled "twistiness omitted" |
| 3 | `05_dive_frames.R` -> 128 PNGs | Per-dive depth profile + twistiness + bottom markers | h5 depth/eti/orientation, `/dives/dive_indices` (128x3), segment attrs | **Server-render PNG** (batch offline) | 128 x ~2 s ~4+ min; ~tens of MB box | Pre-bake all frames; skill `fetch_poster_dive_frame(dive_id)` returns URL; JS fallback single-dive canvas |
| 4 | `06_hierarchical_visualization.R` -> `04_*.html` | **Interactive Plotly 3D lattice** (time x dive# x depth) | h5 depth/eti/dive_indices/orientation/accel | **JS port (Plotly.js)** for HUD interactivity | plotly.js ~1-3 MB gzip; medium dev | **Primary fallback:** serve pre-rendered HTML iframe (no R at runtime). Not acceptable: PNG-only as primary (loses lattice interaction) |
| 5 | `07_energetics_analysis.R` -> `05_*.png` | Scatter ODBA vs max depth, color = duration | h5 `/dives/metrics/{odba,max_depth,duration}` | **JS port** (128 points) | Low: recharts/d3/plotly | R PNG for acceptance pixel-parity; honest empty state if acceleration missing |

Shared h5 paths (from `data_config.yaml`): `/depth/values`, `/eti/values`, `/dives/dive_indices` [128,3], `/analysis/animal_frame_metrics/odba`, `/annotations`, `/behaviors/types`, `/analysis/metadata/sample_rate` (5 Hz). Composite dashboard is the legacy CSV path; for studio alignment, slice the same frame ranges from h5 rather than shipping raw CSV.

## Annotation studio UX (read real h5-derived data; round-trip with provenance)

**Read path:** workbench home `web/app/(workbench)/`. Do not load 54M h5 in browser - use a backend slice API (deployment id `mn09_203a`, `frame_start/end`, `channels[]`, reusing `prebake.py` patterns or pre-baked JSON/bin on box) + catalog endpoints (list dives, list manual spans). Expose `behavior_mapping.json` as `taxonomy_version: "mn09-ethogram-v1"`.

UI panels (from BSIDE, mapped to BSS): `tag_series` (multichannel time series), `dive_panel` (dive picker + phase bars), `label_editor` (span selection + class picker), `poster_*_hud` (managed viz skills). Honesty: humpback `mn09_203a` is contrast/reference only; label species/deployment on every surface; orca motion stays on SRKW driver.

**Round-trip annotation contract (extends B-ANNOT, not in repo):**
```typescript
interface KinematicAnnotationSpan {
  id: string; deployment_id: "mn09_203a"; taxonomy_version: "mn09-ethogram-v1";
  behavior_class_id: 1..9; frame_start: number; frame_end: number;
  state?: string; event_label?: string;
  provenance: { author_reviewer_id: string; created_at: string;
    source: "expert_manual"|"community"|"model_assisted"; model_id?: string;
    parent_annotation_id?: string; license: "operator-whale-behavior-analysis"; };
  honesty: "measured" | "modeled";
}
```
Write path: gated (`GatedAction`); T2 keyed skill `persist_kinematic_annotation` -> DynamoDB/Postgres (mirror community-submissions moderation); success produces `artifact_citation`. **`POST /api/community/sightings` is not a valid stand-in** (geo-centric, 5 coarse behaviors, no frame indices). Read existing 51 annotations from `log_mn09_203a.csv` aligned to 5 Hz; validation masks exist for 5 of 9 classes.

## Managed HUD skill registration plan

| Skill id | Tier | Wraps | Panel id | Produces |
|----------|------|-------|----------|----------|
| `fetch_h5_deployment_catalog` | T1 | h5 manifest + dive/annotation list | `tag_series` | `artifact_citation` |
| `fetch_poster_composite` | T1 | R batch or cached PNG | `poster_composite_hud` | `artifact_citation` |
| `fetch_poster_dive_overview` | T0 | cached PNG or R render | `poster_dive_overview_hud` | `artifact_citation` |
| `fetch_poster_dive_frame` | T1 | cached PNG for `dive_id` | `poster_dive_frame_hud` | `artifact_citation` |
| `fetch_poster_3d_lattice` | T1 | Plotly.js bundle OR HTML artifact URL | `poster_3d_lattice_hud` | `artifact_citation` |
| `fetch_poster_energetics` | T0 | JS data bundle (128 pts) or PNG | `poster_energetics_hud` | `artifact_citation` |
| `run_tagtools_pipeline_step` | T2 | `infra/tagtools/` stage runner | `pipeline_studio` | `artifact_citation` |
| `persist_kinematic_annotation` | T2 | annotation write + provenance | `label_editor` | `artifact_citation` |

Registration checklist per skill: (1) `skills_manifest.json` entry; (2) `skills.py` `_DISPATCH` handler + `_annotations_for_skill` branch; (3) cast seed (`workbench-planner-v1.json` or extend `surface-planner-v1`) + allowed_panels; (4) `panel_registry.json` entry; (5) `uiIntent.ts` `PANEL_LABELS`; (6) `ActiveSurfaceHost.tsx` renderPanel cases; (7) planner keywords. Demo director integration: reuse `20260628_demo-production` blk/cam/scr to capture HUD frames.

## Recommendations with cost + standin-free fallback (incl. R-runtime decision)

| R-runtime option | Cost | Verdict |
|--------|------|---------|
| A. R in App Runner/Lambda hot path | container +500 MB-1 GB; cold start 10-60 s | **Do not default.** Escalate only if on-demand poster regen is hard requirement. |
| B. Offline R batch on box (recommended) | reuse `run_all.R`; cron/operator-triggered; artifacts to S3 | **Primary.** Skills serve cached artifacts with content hash + `generated_at`. |
| C. JS ports where fidelity low-risk | energetics scatter, partial time-series | **Use for interactive HUD**; label when not poster-identical. |

Standin-free fallback ladder: (1) pre-baked real artifacts from real h5; (2) JS port from real h5 slices with explicit simplification labels; (3) honest empty/`not_available` (never synthetic PNGs or mock annotations).

Plotly: plotly.js ~1-3 MB gzip vs iframe pre-rendered HTML (already produced at `output/04_hierarchical_visualization.html`). Annotation persistence: implement B-ANNOT schema first, then T2 write skill; until then studio is read-only + local draft with export. Tier: poster fetch T0/T1 public read; annotation writes + tagtools mutations T2 keyed. All PNG/HTML/bin -> box/S3; web bundle carries manifest pointers + small JSON slices.

## Open questions for O0

1. R-runtime: offline-only batch (B) production path, or App Runner R sidecar (A) for on-demand re-render?
2. Taxonomy ratification: adopt humpback 9-class as `mn09-ethogram-v1`, or reduced SRKW-native ethogram before orca behavior-capture claims?
3. Annotation store: DynamoDB new table vs Postgres extension vs append-only h5 export? Who moderates expert kinematic spans vs community geo sightings?
4. License: whale-behavior h5 + 51 manual labels redistribution scope for box-hosted artifacts and multi-reviewer writes?
5. Composite dashboard input: keep CSV replay for parity, or mandate h5-only slices?
6. Plotly bundle budget: plotly.js in main twin chunk vs iframe-only 3D lattice (coordinate with BSH)?
7. Panel registry gap: add `hydrophone_signal` to `panel_registry.json` so planner can emit it server-side?
8. Cross-species honesty: which poster viz skills appear on public `/explore` vs keyed `/workbench` only?

## Sources

**orcast (commit 240570e):** `web/app/components/AdaptiveExplore.tsx`, `web/app/components/ActiveSurfaceHost.tsx`, `web/lib/uiIntent.ts`, `web/lib/adaptiveConsole.ts`, `web/lib/api.ts`, `web/app/components/console/HydrophoneSignalPanel.tsx`, `src/aws_backend/casting/{skills.py,skills_manifest.json,panels.py,panel_registry.json,planner.py,seeds/surface-planner-v1.json}`, `src/aws_backend/routers/{interactions.py,community.py,dtag.py}`, `infra/orca/biologging/prebake.py`, `docs/devpost/casting/{SKILL_CATALOG.md,INTERACTIONS_GROUNDING_PATTERN.md,MANAGED_AGENTS_CONTRACT.md}`, `BSW-STUDIO-SKILLS_CHARTER.md`, `PROGRAM.md`, `research/BSW-R04_kinematic_ethogram.md`, `.cca/catalogue/O0/20260627_bside-build/BSIDE_CHARTER.md`

**whale-behavior-analysis (external, read verified):** `Visualization_Poster_Appendix/scripts/{run_all.R,01_setup.R,02_data_loading.R,03_composite_dashboard.R,04_dive_overview.R,05_dive_frames.R,06_hierarchical_visualization.R,07_energetics_analysis.R,data_config.yaml}`, `Visualization_Poster_Appendix/data/{dive_analysis.h5,log_mn09_203a.csv,mn09_203a.csv}`, `dive_analysis_schema_flat.json`, `DATA_BINDING_MANIFEST.md`, `behavior_mapping.json`
