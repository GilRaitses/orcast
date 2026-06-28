# RP3 — Labels + Proportional Scaling + LGC Styling (Findings)

Lane: 3D-TWIN / W-PERFUX, sub-lane RP3 (read-only research). Reports to O0.
Date: 2026-06-28. repo_state_verified_against: `origin/main` @ `b9e2e13`.
Scope: design plan only. No code edits, no dev server, no heavy browser
automation. This doc is the single deliverable.

Grounded against the live `web/` console (LGC charter §2 locked target). Files
read: `web/app/components/scene/SalishScene.tsx`, `web/lib/geo/gazetteer.ts`,
`web/lib/sceneIntent.ts`, `web/app/globals.css`,
`web/node_modules/@react-three/drei/web/Html.js`, the LGC manifest Part A/B, and
the LGC waveset charter.

---

## 0. What exists today (verified)

- The only in-scene labels are the hydrophone beacons. `HydrophoneBeacon`
  (`SalishScene.tsx` 316-357) renders a drei `<Html>` ONLY on hover
  (`{hovered && (...)}`, line 350), `center distanceFactor={120}`, anchored at a
  fixed `position={[0, 11, 0]}` above the beacon group, class `scene-beacon-label`.
- `scene-beacon-label` (`globals.css` 509-517) is an opaque dark chip:
  `background: rgba(8,38,61,0.92)`, `color:#ffe9a8`, `border:1px solid var(--warn)`.
  It carries no LGC glass treatment and no `backdrop-filter` (so it already
  honors the M3 no-blur rule by accident, not by contract).
- Beacons are placed by `SurfaceBeacons` (361-396): for each node it calls
  `projectToScene(lat, lng, TILESET_BOUNDS, SCENE_DEPTH)` for X/Z, raycasts the
  streamed tile group with `surfaceYAt(group, x, z)` for surface Y, and clamps
  the anchor to `Math.max(y ?? 0, 0)` so a missed ray (off the footprint) lands
  at sea level. A `useModelLoadTick` re-placement loop refines Y as tiles stream.
- Place names exist only in the gazetteer (`web/lib/geo/gazetteer.ts`,
  `GAZETTEER`, 40 entries) and are consumed only by the search box
  (`resolvePlace` in `SearchAffordance`). No gazetteer place is ever drawn as a
  scene label today.
- LGC design tokens are NOT yet in `web/app/globals.css`. The `:root` block
  (lines 1-13) has `--bg/--surface/--accent/--warn` only. The LGC `--glass-*` and
  `--*-ink` tokens (manifest Part A) are unported. RP3 assumes the LGC lane lands
  Part A into this `:root`; RP3 labels then read those tokens.

So the operator's three asks map to: (1) almost nothing is labelled, (2) the one
label that exists uses `distanceFactor` with no clamp, (3) it has no glass style.

---

## (a) Plan: render more gazetteer place labels

### Which places

Filter `GAZETTEER` to the served footprint, exactly as the beacons already filter
hydrophone nodes (`SalishScene.tsx` 965-972 `inBoundsNodes`), against
`TILESET_BOUNDS` (lat 48.4..48.7, lng -123.25..-122.75). Applying that box to the
40 gazetteer entries yields roughly 24 in-footprint places:

- Islands: Orcas, Lopez, San Juan, Shaw, Decatur, Blakely, Stuart, Clark, Jones.
- Harbors / terminals: Friday Harbor, Roche Harbor, Deer Harbor, Orcas Village.
- Villages / landmarks: East Sound, Lopez Village, Rosario, Olga, Doe Bay,
  Spencer Spit, Lime Kiln Point, Cattle Point, Turn Point.

Out-of-footprint entries (Anacortes, Bellingham, Sucia, Cypress, Guemes, Patos,
Matia, Point Roberts, Sidney, Victoria, Port Townsend, Coupeville, Keystone,
Mukilteo, Edmonds, Seattle, Lake Union, SeaTac) are dropped by the same filter.
Their `surfaceYAt` ray would miss the streamed geometry and collapse them onto
the sea-level plane outside the terrain, so excluding them is correct.

Recommendation: add an `inFootprint(place, TILESET_BOUNDS)` predicate (a direct
analog of the existing beacon filter) and render only the survivors. If RP2
widens the default extent, the same predicate auto-includes the near-edge islands
(Sucia, Matia, Cypress) with no label-code change.

### How anchored

Reuse the beacon placement seam verbatim so labels and beacons share one frame:

```ts
// per place, identical math to SurfaceBeacons (SalishScene.tsx 372-387)
const [x, z] = projectToScene(place.lat, place.lng, TILESET_BOUNDS, SCENE_DEPTH);
const y = surfaceYAt(tiles.group, x, z);              // null when off-footprint
const anchor: [number, number, number] = [x, Math.max(y ?? 0, 0) + LABEL_LIFT_M, z];
```

`LABEL_LIFT_M` is a small lift above the surface (the beacons use `+11` for the
cone tip; a place label wants a smaller lift, roughly `+4` to `+6` scene units, so
it floats just over land). Drive re-placement off the same `useModelLoadTick`
tick the beacons use (`SalishScene.tsx` 780, 387) so labels re-raycast onto
refined geometry as tiles stream.

Implement as a sibling rig `PlaceLabels` next to `SurfaceBeacons`, mounted inside
`TwinScene`. Keep the per-place projection/raycast in a `useMemo` keyed on
`[tiles, tick]`, mirroring `SurfaceBeacons` (372-387), so the cost matches the
existing beacon path and adds no new per-frame raycasting beyond placement.

### Density and declutter

24 always-on DOM labels can crowd at a wide framing. Tier label visibility by
`place.kind` and camera distance so density rises as the camera closes in:

- Tier 1 (always shown): `island`, `harbor`, `city`. The structural anchors.
- Tier 2 (shown when the camera is within a mid threshold): `village`,
  `terminal`.
- Tier 3 (shown only when close): `landmark` (Lime Kiln, Cattle Point, Turn
  Point, Rosario, Olga, Doe Bay, Spencer Spit).

The tier gate reads the same per-frame camera distance the scale clamp already
computes (section b), so it is free. This is the label-density analog of LoD and
is the primary anti-clutter lever. Pairwise screen-space overlap suppression is a
later refinement and is NOT required for the first build.

---

## (b) Distance-proportional scaling with MIN and MAX clamp

### How drei `distanceFactor` actually behaves (grounded)

From `@react-three/drei/web/Html.js`:

```js
// Html.js line 274
const scale = distanceFactor === undefined ? 1 : objectScale(group, camera) * distanceFactor;
el.style.transform = `translate3d(${vec[0]}px,${vec[1]}px,0) scale(${scale})`;
```

with, for a perspective camera (`objectScale`, lines 42-48):

```
objectScale = 1 / (2 * tan(vFOV/2) * dist)
=> appliedScale = distanceFactor / (2 * tan(vFOV/2) * dist)
```

So with `distanceFactor` set, the rendered scale is inversely proportional to the
camera-to-anchor distance `dist`, with NO bound. As the user zooms in
(`dist -> 0`) the label scale grows without limit and fills the screen. As they
zoom out (`dist` large) it shrinks toward zero and disappears. With
`distanceFactor` undefined, scale is a constant `1` (fixed pixel size at every
distance: a hard cap everywhere, but it never shrinks when far). Neither mode
gives the operator's requested MIN-and-MAX curve.

Quantified for the current scene (deterministic `fitRadius = SCENE_WIDTH/2 = 60`,
`fov 45`, `distanceFactor 120`):

- At the resting orbit (`dist` ~54 scene units): scale ~2.7x the CSS size.
- Zoomed to `minDistance = fitRadius*0.5 = 30`: scale ~4.8x (grows ~80%, the
  "takes up too much space" complaint).
- Zoomed to `maxDistance = fitRadius*8 = 480`: scale ~0.30x (near-invisible).

### Recommended approach: custom clamped scale (keep DOM, drop distanceFactor)

Render the label as a drei `<Html>` WITHOUT `distanceFactor` (so it has no
built-in growth), wrap the styled content in an inner div, and set that inner
div's `transform: scale(s)` each frame from a clamped curve:

```ts
// inside the label component, anchor world-pos in a ref `groupRef`
useFrame(({ camera }) => {
  const dist = camera.position.distanceTo(groupRef.current.getWorldPosition(tmp));
  const raw = LABEL_REF_DIST / dist;                 // 1.0 at the design distance
  const s = Math.min(LABEL_SCALE_MAX, Math.max(LABEL_SCALE_MIN, raw));
  innerRef.current.style.transform = `scale(${s})`;  // DOM transform, no React rerender
});
```

Clamp behavior (this IS the operator's curve):

- `LABEL_SCALE_MIN` (suggest ~0.6): the floor when far. The label stays small but
  legible instead of vanishing. Pair with a Tier gate so far-away clutter is cut
  by hiding Tier 2/3, not by shrinking Tier 1 to nothing.
- `LABEL_SCALE_MAX` (suggest ~1.6 to 2.0): the cap when close. The label can never
  grow past this no matter how far the user zooms in, so it never dominates the
  frame.
- `LABEL_REF_DIST`: the distance at which scale is exactly 1.0. Tune it to RP2's
  resting framing so labels read at a comfortable size at the default view.

Properties: a true MIN+MAX clamp; no per-frame React re-render (mutate
`style.transform` on a ref); DOM stays styled by LGC CSS (section c). Cost is one
`distanceTo` per label per frame, cheaper than drei's occlusion raycast and on the
order of the existing director per-frame work.

### Why not the alternatives

- `distanceFactor` alone: no clamp (shown above). Rejected.
- `distanceFactor` undefined (constant pixel size): a fixed cap but no
  shrink-when-far, so far labels stay large and crowd the wide view. Rejected as
  the sole mechanism, though it is effectively the `MIN == MAX` degenerate case.
- In-scene SDF text or sprites (Troika / `<sprite>`) with a per-frame clamped
  `object.scale`: best raw perf for many labels and no DOM, but it cannot consume
  the LGC CSS glass tokens (frost fill, ink, hairline) without re-implementing
  them in a texture or shader. The operator explicitly wants LGC glass on labels,
  so DOM `<Html>` wins. Revisit sprites only if label count grows past the point
  where DOM transforms regress M3 frame time.

### Composition with RP2's tighter framing

RP2 proposes a closer default (San Juans core, lower resting altitude than the
current `RESTING_ORBIT_ALT_M = 2200`). A closer camera means a smaller `dist`,
which under raw `distanceFactor` makes every label larger at rest, worsening the
"too big" problem exactly as RP2 lands. The clamp is what makes RP2 safe: set
`LABEL_REF_DIST` to RP2's new resting distance so scale is 1.0 at rest, and
`LABEL_SCALE_MAX` then bounds any further zoom-in. RP3's clamp constants must be
tuned AFTER RP2 fixes the resting framing, since `LABEL_REF_DIST` is defined in
terms of it. This is the one cross-dependency O0 should sequence: RP2 framing
first, then RP3 clamp tuning.

---

## (c) LGC glass styling for labels and HUD

Labels sit over the always-repainting r3f canvas, so they are governed by the
LGC manifest's instrument-over-unbounded-luminance case and the two hard rules
(manifest Part B "Two HARD rules").

Tokens to use (manifest Part A), assuming the LGC lane has dropped them into
`web/app/globals.css :root`:

- Fill: cool instrument frost, NOT plain frost, because the label sits over
  unbounded-luminance terrain/water. Use `--glass-tint-cool` (226 232 240).
- AA opacity floor: clamp the fill alpha in CSS so the token governs. Target the
  HUD-chip alpha but never below the floor:
  `background: rgb(var(--glass-tint-cool) / max(var(--glass-opacity-hud), var(--glass-opacity-floor)))`,
  with `--glass-opacity-floor = 0.62`, `--glass-opacity-hud = 0.66`.
- Scrim: because it is over live frames, paint the AA-insurance scrim wash under
  the text per the manifest's scrim composition (linear-gradient of
  `rgb(var(--glass-scrim) / var(--glass-scrim-alpha))` over the cool fill).
- Text as ink, never as fill: primary label text `color: rgb(var(--text-ink))`
  (11 16 21). Secondary/sub text `--text-muted-ink`. Online/selected accent as
  glyph color `--accent-ink` (deep green); offline/warning as `--warm-ink` (deep
  terracotta). This replaces the current yellow `#ffe9a8` text and `--warn`
  border on `scene-beacon-label`.
- Hairline: `border: 1px solid rgb(var(--glass-hairline) / 0.5)`.
- Blur: `0`. M3 rule: every surface over the always-repainting canvas passes
  `blur=0`, fill + scrim only, NO `backdrop-filter`. Labels and any map HUD chips
  get no `backdrop-filter` at all. `backdrop-filter` is reserved for the chat
  shell and the console dock, which are not over the canvas. (The current
  `scene-beacon-label` already has no blur; keep it that way and make it a
  contract, not an accident.)

Proposed CSS shape (new class, replaces the old beacon-label look and serves
place labels too):

```css
/* label chip over the live 3D canvas: cool frost + scrim, ink text, NO blur (M3) */
.scene-label {
  background:
    linear-gradient(rgb(var(--glass-scrim) / var(--glass-scrim-alpha)),
                    rgb(var(--glass-scrim) / var(--glass-scrim-alpha))),
    rgb(var(--glass-tint-cool) / max(var(--glass-opacity-hud), var(--glass-opacity-floor)));
  color: rgb(var(--text-ink));
  border: 1px solid rgb(var(--glass-hairline) / 0.5);
  border-radius: 6px;
  padding: 0.2rem 0.5rem;
  font-size: 0.78rem;
  white-space: nowrap;
  /* NO backdrop-filter: M3 hard rule over the repainting canvas */
}
.scene-label--hydrophone { color: rgb(var(--accent-ink)); }     /* online accent as ink */
.scene-label--offline    { color: rgb(var(--warm-ink)); }       /* offline/warning as ink */
```

M1 contrast note: dark ink (11 16 21) on the cool frost at >= 0.62 alpha clears
WCAG AA against the worst-case composited frame. This must be Read-verified on a
rendered frame at W5 (M10), not asserted. The clamp's `LABEL_SCALE_MIN` must keep
text large enough to qualify as large-text (3:1) at the far floor.

LGC focus/self-hide tie-in (the operator's instinct that LGC helps the model load
lighter): the place-label Tier gate can be wired to the LGC focus model so that
when a console or edge panel owns focus, Tier 2/3 labels recede (drop to the MIN
floor or hide), cutting DOM label count and HUD repaint cost while a panel is
active. Honesty captions (manifest H1-H4) are never receded by this, and labels
are decorative, so M5 self-hide-never-conceals is not at risk from them. This is
a coordination note for LGC, not RP3 scope.

---

## (d) Shared surfaces needing serialized edits

These are convergence files. Per LGC charter §3 collision lock (`scene/**` and
`globals.css` are concurrently edited by the twin camera lane and the
ghost-text/console lane), every edit below must serialize through O0 with W-CAM
and LGC. Do not edit any of these in parallel with another lane.

1. `web/app/components/scene/SalishScene.tsx` (shared with W-CAM camera work and
   LGC F1/F2 glass-over-canvas):
   - Add a `PlaceLabels` rig (sibling of `SurfaceBeacons`, ~361-396) and mount it
     in `TwinScene` (~860).
   - Edit `HydrophoneBeacon` (316-357): remove `distanceFactor={120}` (351), wrap
     the label content in an inner div, add the clamped per-frame scale, switch
     the class to the new `.scene-label`, and make the label persistent or
     hover-promoted rather than hover-only if the density plan calls for it.
   - Add the `inFootprint` predicate and the `LABEL_*` tuning constants near the
     existing scene constants (111-142).

2. `web/app/globals.css` (shared with the LGC token drop and the ghost-text
   `.chat-*` classes):
   - Depends on the LGC lane landing Part A tokens into `:root` (1-13). RP3 must
     not duplicate the tokens; it consumes them.
   - Replace/extend `.scene-beacon-label` (509-517) with the `.scene-label`
     family above. Sequence after the LGC token drop so the `var(--glass-*)`
     references resolve.

3. New, non-colliding module (recommended to keep the shared-file edits minimal):
   `web/lib/scene/labels/` for the clamped-scale hook and the `PlaceLabels`
   placement logic. Net-new files do not collide; `SalishScene.tsx` then only
   imports and mounts them, shrinking the diff on the shared convergence file.

Cross-lane sequencing O0 should enforce: LGC Part A tokens -> RP2 resting framing
-> RP3 `LABEL_REF_DIST`/clamp tuning + glass label CSS. RP3's scale constants are
defined relative to RP2's framing, so RP3 build cannot finalize tuning before RP2
lands.

---

## Open items for O0

- `LABEL_REF_DIST`, `LABEL_SCALE_MIN`, `LABEL_SCALE_MAX`, and `LABEL_LIFT_M` are
  proposed starting values, to be tuned at a gate against RP2's framing on a
  Read-verified frame (M10).
- Whether place labels are always-on (Tier 1) or fully hover-promoted is a
  density/clutter decision for the build wave; the Tier plan supports either.
- M1 contrast for ink-on-cool-frost must be Read-verified at W5, not assumed.
