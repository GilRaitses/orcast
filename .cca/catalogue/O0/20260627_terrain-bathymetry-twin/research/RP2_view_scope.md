# RP2 — Default View Scope (findings)

Lane: 3D-TWIN / W-PERFUX, RP2 (default view scope). Reports to O0.
Date: 2026-06-28. Read-only research. No code changed, no commit.
repo_state_verified_against: `origin/main` @ `b9e2e13` per the dispatch.
Dispatch: `.cca/catalogue/O0/20260627_terrain-bathymetry-twin/W-PERFUX_RESEARCH_DISPATCH.md`.

Operator issue (verbatim intent): the model view shows "so far back" — too wide a
default scope, showing far-back periphery detail the operator does not want, and
contributing to slow load. Goal: a tighter useful default framing on the San
Juans core, and how to load LESS of the full extent at start.

Honesty note: the tile counts and byte sizes below are read from the host bake
docs (`infra/3dtwin/host/README.md`, `WIRING-host.md`), not measured live this
lane. Live per-tile HTTP sizes are RP1's deliverable (`research/RP1_load_perf.md`);
RP2 reuses RP1's reasoning about which tiles dominate the payload. The camera and
LoD constants below are read from the actual source files cited inline.

---

## Grounding constants (read from source)

Served tileset (`infra/3dtwin/host/README.md`, `WIRING-host.md`):

| Field | Value |
|---|---|
| Extent (= `SAN_JUAN_BOUNDS` / `TILESET_BOUNDS`) | lat 48.40..48.70, lng -123.25..-122.75 |
| Full extent metres | ~36.9 km E-W x ~33.3 km N-S |
| Tiles | 85 total. L0 = 1, L1 = 4, L2 = 16, L3 (leaf) = 64. Quadtree, REPLACE |
| Geometric error per level (m) | tileset 160, root/L0 80, L1 40, L2 20, leaf/L3 10 |
| Geometry | 16,343,109 verts / 32,537,090 tris total |
| Optimized payload | 75.8 MiB on S3 (meshopt), served via CloudFront |

Scene fit and camera (`web/app/components/scene/SalishScene.tsx`,
`web/lib/scene/tiles/useTilesLayer.ts`, `web/lib/sceneIntent.ts`,
`web/lib/scene/camera/director.ts`):

| Quantity | Source | Value |
|---|---|---|
| `SCENE_WIDTH` | sceneIntent.ts:57 | 120 scene units |
| `fitScaleToWidth` | SalishScene.tsx:774 | `SCENE_WIDTH` (fits bounding-sphere DIAMETER to 120) |
| Resulting `fitRadius` | useTilesLayer fit math (`scale = target / (radius*2)`) | 60 units (world sphere radius after fit) |
| `errorTarget` | SalishScene.tsx:776 | 16 px (overrides the hook default 12) |
| `maxDepth` | useTilesLayer default, not set by the scene | Infinity (refine to leaves) |
| geo half-diagonal of extent | `geoRadiusMeters(TILESET_BOUNDS)` | ~24,815 m |
| `worldUnitsPerMeter` | `fitRadius / geoRadiusMeters` (SalishScene.tsx:537) | ~0.00242 units/m |
| `SCENE_CENTER` | SalishScene.tsx:119-122 | midpoint of extent, lat 48.55, lng -123.00 |
| `RESTING_ORBIT_ALT_M` | SalishScene.tsx:124 | 2200 m above sea level |
| resting orbit radius | SalishScene.tsx:550 `Math.max(fitRadius*0.9, 40)` | 54 units |
| initial Canvas camera | SalishScene.tsx:980 | position [0, 80, 120], fov 45 |
| OrbitControls min/max distance | SalishScene.tsx:808-809 | min `fitRadius*0.5` = 30, max `fitRadius*8` = 480 |

---

## (a) Current default framing and why it shows so much

Three things stack to produce "so far back":

1. **The fit frames the whole extent.** `fitScaleToWidth = SCENE_WIDTH` scales the
   tileset so its full bounding-sphere diameter is 120 scene units, and every
   downstream distance (`fitRadius` = 60, OrbitControls min/max, the resting
   orbit radius) is sized to that full ~37 x 33 km sphere. The default is, by
   construction, "see the entire baked extent."

2. **The resting orbit is a shallow grazing angle, not an overhead look.** The
   director places the resting camera at horizontal radius `fitRadius*0.9` = 54
   units but altitude `RESTING_ORBIT_ALT_M` = 2200 m, which is only
   2200 * 0.00242 = ~5.3 units of world Y. Pitch above horizontal is
   atan(5.3 / 54) = ~5.6 degrees. At a ~5.6 degree look-down the ground plane
   foreshortens hard toward the horizon, so the frame fills with the far edge of
   the extent and everything beyond it (the decorative horizon ring, the Olympics
   and Vancouver Island bearings). That grazing periphery is the "far-back detail"
   the operator does not want.

3. **The pre-director frame is even further back.** Before the director attaches
   on first fit, the Canvas camera sits at [0, 80, 120], a distance of ~144 units
   from origin, more than twice `fitRadius`. The first painted frames are the
   widest of all.

Load consequence (reusing RP1 reasoning): the grazing wide framing puts the ENTIRE
85-tile tree inside the view frustum, so every tile is a candidate the scheduler
must consider and at least stream ancestors for, and the periphery is never culled.
Per the host bake, the leaf level dominates the payload: 64 of 85 tiles, and with
the bake's roughly constant per-tile vertex budget (each tile decimated by stride
so vertices stay ~constant per level) the leaves carry on the order of 64/85 =
~75% of the 16.3M verts / 75.8 MiB. A default that frames the whole extent is
therefore the worst case for start-time tile count and bytes. Exact requested-byte
numbers at the default framing are RP1's to measure.

---

## (b) Recommended tighter default camera (San Juans core)

Keep the geo center close to where it is: `SCENE_CENTER` (lat 48.55, lng -123.00)
already sits in the middle of the four ferry-served islands. A small nudge west to
~lng -123.05 biases the frame toward Haro Strait, where the Orcasound Lab
hydrophone (48.5583, -123.1735) and the core whale geography sit, but the center is
not the problem. The problem is radius and pitch. The fix is camera-only: raise the
pitch so the frame looks down onto a bounded ground patch instead of grazing to the
horizon, and pull the radius in so the patch is the ~12-15 km island core rather
than the full ~37 km extent.

Recommended resting-orbit values (edit the SalishScene.tsx resting-orbit
useEffect, SalishScene.tsx:543-554, and the constant at :124):

| Knob | Current | Recommended | Effect |
|---|---|---|---|
| orbit radius factor | `fitRadius * 0.9` = 54 u | `fitRadius * 0.40` = ~24 u (floor ~30) | frames ~1/3 of the extent diagonal |
| `RESTING_ORBIT_ALT_M` | 2200 m (~5.3 u Y) | ~6000 m (~14.5 u Y) | pitch atan(14.5/24) = ~31 deg, a real look-down |
| camera-to-center dist | ~54.3 u, pitch ~5.6 deg | ~28 u, pitch ~31 deg | frames a ~10-14 km core, no horizon graze |
| initial Canvas camera | [0, 80, 120], dist ~144 u | ~[0, 28, 30], dist ~41 u | first painted frame is not the widest |

Optional guard rail, not a default: cap OrbitControls `maxDistance` from
`fitRadius*8` = 480 down to ~`fitRadius*2` = 120, so a user cannot accidentally
zoom back out to the same horizon-graze that the operator is complaining about.
`minDistance` = 30 is fine.

These are all camera-only constants and the orbit options (`altitudeMeters`,
radius) that SalishScene already passes to `director.orbit(...)`. No new module,
no data change.

A second framing option, if O0 prefers a named anchor over the geometric center,
is to frame `san-juan-island` from the gazetteer (lat 48.5333, lng -123.0833,
half-extent ~0.085 deg) directly through `runPlaceJourney` on first load, which
already settles into an orbit at the resolved place. That reuses the existing
journey primitives but adds a scripted opening move instead of a static resting
pose, so it is heavier than the constant edits above and overlaps W-CAM. The
constant edits are the smaller change.

---

## (c) Loading less of the full extent at start

Two levers, both config-only (no re-bake), best combined.

### Lever 1 — tighter camera, frustum culling (camera-only, soft)

The renderer culls and prioritizes against the live camera
(`tiles.setCamera`, `setResolutionFromRenderer`, `tiles.update()` each frame in
useTilesLayer). Tiles fully outside the frustum are not requested. A default that
frames a ~12-15 km core (option b) keeps only the core tiles in-frustum and culls
the periphery. A core window of roughly 1/4 of the full area keeps roughly 1/4 of
the 64 leaves in-frustum, so leaf requests at start drop on the order of 60-75%
versus framing the whole extent. This is soft: a pan or zoom-out immediately pulls
more, and the exact saving depends on `errorTarget` (RP1's knob) and viewport
height. It needs no tileset change.

### Lever 2 — initial `maxDepth` cap (config-only, deterministic)

`useTilesLayer` already accepts `maxDepth` and applies it live without rebuilding
the renderer (useTilesLayer.ts:144-149). The scene does not set it today, so it is
Infinity (refine to leaves). Setting `maxDepth = 2` at start caps the tree at L2
(geometric error 20 m): at most 1 + 4 + 16 = 21 tiles, and the entire 64-tile leaf
level never loads. Because the leaves are ~75% of the geometry and bytes, a
`maxDepth = 2` start is a deterministic ~75% reduction in start-time tris/bytes
(on the order of 75.8 MiB down toward ~19 MiB, 32.5M tris down toward ~8M),
independent of framing. `maxDepth = 3` keeps the full tree and is the "release"
target.

Compose: hold `maxDepth = 2` (or 3) at rest, then lift toward Infinity on the
first user zoom-in or a focus journey, so leaf detail streams on demand for the
place the user actually looked at. This is the "lazy LoD" lever RP1 ranks, framed
here as a default-state depth cap that the camera or focus releases. Wired in
SalishScene.tsx as a `maxDepth` state passed to the existing `useTilesLayer`
prop, raised in the OrbitControls `onStart` / focus handlers that already exist.

### Combined expectation

Tighter default camera + `maxDepth = 2`: only the ~16 L2 tiles plus their parents
that overlap the core window stream at start, well under 20% of the full payload,
with leaf detail arriving only when the user engages. The clean, low-risk first
move is camera-only framing plus the `maxDepth` cap. Neither requires a re-bake.

### Region gating (heavier, optional, needs a re-bake)

True "load only the core region" (a served core-only `tileset.json` subtree) is
not config-only: the current bake is one quadtree over the full bbox, and
`3d-tiles-renderer` has no built-in lat/lng load mask, so an in-client region gate
reduces to frustum culling (lever 1) plus the depth cap (lever 2). Authoring a
core-only tileset is a host-side re-bake (RP1 / `full-extent-host` territory) and
should be a follow-up only if the two config-only levers prove insufficient after
RP1's live measurement.

---

## (d) Composition with labels (RP3) and the LGC focus model

- **RP3 label scaling.** A tighter default frames fewer gazetteer places at once
  (core islands such as San Juan, Orcas, Lopez, Shaw, Friday Harbor, Roche Harbor,
  Lime Kiln, plus Haro Strait), so fewer `<Html>` label nodes mount at start, which
  is itself a DOM/portal cost saving that compounds RP3's work. Off-core places
  (Victoria, Sidney, Bellingham, Anacortes, Port Townsend, Seattle) fall outside
  the default frame and only appear when the user pans or searches there, which
  naturally bounds label count. RP3 should cull labels to the camera frustum (or to
  the focused region) so label density tracks RP2's scope. At rest the camera is at
  a ~28-unit standoff, a narrow distance band, so RP3's distance-proportional
  min/max clamp has a small dynamic range to cover at the default and a capped
  `maxDistance` keeps the `<Html>` `distanceFactor` in a sane range.

- **LGC focus model.** The LGC charter binds the focus model's universal sink
  (`{kind:"map"}`) to the live scene, with a single-focus, self-hiding layout. RP2
  supplies the two LoD knobs that the focus controller can modulate: camera scope
  (via the director's orbit radius/altitude) and depth/detail (`maxDepth` and
  `errorTarget`). When focus leaves the scene (a panel or chat takes the single
  focus and the dock self-hides), the scene is not the user's attention, so LGC can
  drive it to the cheaper resting state (hold the `maxDepth` cap, raise
  `errorTarget`, reduce label rendering). When the map regains focus, release the
  cap and refine. This is the concrete mechanism behind the operator's instinct
  that LGC work helps the model load better: focus-gated LoD plus self-hide-gated
  label/HUD count.

---

## Collision / sequencing note for O0

All of (b) and lever 2 land in `web/app/components/scene/SalishScene.tsx`, the
single convergence file, which W-CAM, W4, and LGC also edit. Per the lane execution
model (`wave_shape.yml`: `single_convergence_file_editor_per_wave`) and the LGC
charter collision lock, any build of these changes must serialize against those
lanes and rebase first. The `maxDepth` knob change also touches the `useTilesLayer`
call site in SalishScene, not the hook internals.

---

## Return to O0 (6-10 line summary)

Recommended default framing: keep the geo center near `SCENE_CENTER` (a small nudge
west toward Haro Strait is optional) but change the resting orbit from a far-back
graze to a real look-down on the San Juans core, by pulling the orbit radius from
`fitRadius*0.9` (~54 u) to ~`fitRadius*0.40` (~24 u) and raising `RESTING_ORBIT_ALT_M`
from 2200 m to ~6000 m, which moves the pitch from ~5.6 deg to ~31 deg and frames a
~10-14 km island core instead of the full ~37 km extent. Also tighten the initial
Canvas camera from [0,80,120] to ~[0,28,30] and optionally cap OrbitControls
`maxDistance` from 480 to ~120. Expected load reduction: the tighter frame
frustum-culls the periphery for roughly 60-75% fewer leaf-tile requests at start
(soft), and adding an initial `maxDepth = 2` cap on the existing `useTilesLayer`
prop deterministically drops the 64-tile leaf level for ~75% fewer start-time
tris/bytes (toward ~19 MiB / ~8M tris), lifted on zoom or focus. Verdict: this is
camera-only plus one config-only `maxDepth` cap, both editable in SalishScene.tsx
with no re-bake. True region gating (a served core-only tileset) would need a host
re-bake and is an optional follow-up only if RP1's live numbers say the config
levers are not enough. Exact requested-byte figures depend on RP1's measurement and
on `errorTarget`, which RP1 owns.
