# W-PERFUX — Load Perf + View Scope + Labels Research (Dispatch)

Lane: 3D-TWIN. Wave: W-PERFUX (research-first, read-only). Reports to O0.
Date: 2026-06-28. repo_state_verified_against: `origin/main` @ `b9e2e13`.

## Operator report (verbatim intent)

Most of the land still reads underwater; do not show the view so far back in
detail; it loads super slowly, research how to make it run better and look at
what LGC will require since that may help the model load better; places need more
labels; icon scale should be distance-proportional (smaller when seen from far,
capped so it never takes up too much space when close); labels should carry LGC
styling.

## Standing clarification (do not re-litigate)

The "land underwater" datum fix is wave W2.6, already implemented diffs-only but
UNCOMMITTED and not deployed, so the live site is pre-fix. This wave does NOT
re-research the datum bug. It researches the next layer: load performance, the
default view scope, and labels/icon scaling/LGC styling.

## Three read-only research lanes (each owns ONE findings doc; no code edits)

### RP1 — load performance  → `research/RP1_load_perf.md`
Measure and explain why the twin loads slowly. Ground in:
`web/lib/scene/tiles/useTilesLayer.ts` (errorTarget=16, fit, shadows, dispose),
`infra/3dtwin/host/WIRING-host.md` + `README.md` (85 tiles, full-extent LoD bake,
CloudFront), `web/app/components/scene/SalishScene.tsx` (what mounts at start).
Get real numbers: tileset.json tile count + per-tile glTF sizes + texture sizes
via `curl -sI` against the CloudFront tileset URLs (read-only, no browser
automation; another lane may be using the browser). Rank levers: errorTarget /
maxDepth tuning, lazy LoD, KTX2/Basis textures (W5 texture-compression already
chartered), meshopt/draco, initial-extent subset, deferring non-critical rigs.
Note which levers are config-only vs require a re-bake on the EC2 host.

### RP2 — default view scope  → `research/RP2_view_scope.md`
The operator does not want the view zoomed so far back. Ground in the camera
director resting orbit (`SalishScene.tsx` RESTING_ORBIT_ALT_M ~2200, SCENE_CENTER,
fitRadius) and TILESET_BOUNDS / SAN_JUAN_BOUNDS. Propose a tighter, useful default
framing (San Juans core) and how to load LESS of the full extent at start (e.g.
constrain initial camera so the tile scheduler streams fewer high-LoD tiles, or
gate the loaded region). Quantify the expected load reduction. This lane ties
directly to RP1 (less visible extent = fewer tiles).

### RP3 — labels + proportional scaling + LGC styling  → `research/RP3_labels_scale_lgc.md`
Ground in the existing hydrophone `<Html>` beacon labels (`SalishScene.tsx`
~341-343), the gazetteer (`web/lib/geo/gazetteer.ts`, ~40 named places), and the
LGC manifest tokens (`LIQUID_GLASS_CONSOLE_MANIFEST.md` Part A/B + the LGC charter).
Design: (a) render more named-place labels from the gazetteer; (b) a
distance-proportional scale curve for label/icon size with a MIN (small/visible
when far) and a MAX clamp (never dominates when close) — evaluate drei `<Html>`
`distanceFactor` vs a custom clamped scale, and how it composes with RP2's tighter
framing; (c) apply LGC glass styling (frost tint, ink-on-glass, AA floor) to the
labels/HUD. Coordinate with W-CAM (camera/labels) and LGC (styling); flag the
shared `SalishScene.tsx` + globals.css surfaces so edits serialize later.

## All three lanes also

Read the LGC charter (`.cca/catalogue/O0/20260628_liquid-glass-console/WAVESET_CHARTER.md`)
and note where LGC's focus / self-hide model could reduce what is rendered or
reduce HUD cost, per the operator's instinct that LGC work helps the model load
better. Do NOT edit code, do NOT run a dev server, do NOT use heavy browser
automation (another lane holds the browser). curl/HTTP HEAD for asset sizes is fine.

## Escalation + return

Answer to O0, not the operator. Return: RP1 ranked measured levers, RP2 a
recommended default view scope with expected load reduction, RP3 a
label-density/scaling/LGC-style plan. Then O0 reconciles into a build wave. No
commit, no push.
