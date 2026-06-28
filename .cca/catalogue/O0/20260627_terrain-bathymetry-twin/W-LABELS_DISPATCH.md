# W-LABELS dispatch (RP3 build + accept): geo-anchored place labels, clamped scaling, LGC glass

Lane: 3D-TWIN. Home: `.cca/catalogue/O0/20260627_terrain-bathymetry-twin/`. Build of the
RP3 research plan (`research/RP3_labels_scale_lgc.md`). GATED on O0 for commit; the accept
gate is frame-verified.

## Operator asks (verbatim intent)

More place labels; the icon/label scale should be distance-proportional with a clamp
(smaller when far, never dominating when near); labels should carry LGC glass styling.

## Hard prerequisites (do not start the build before both land)

1. The LGC lane has dropped its Part A glass tokens (`--glass-tint-cool`,
   `--glass-opacity-floor/hud`, `--glass-scrim*`, `--text-ink`, `--text-muted-ink`,
   `--accent-ink`, `--warm-ink`, `--glass-hairline`) into `web/app/globals.css :root`.
   W-LABELS consumes these tokens; it must not duplicate or invent them.
2. RP2 resting framing has landed (W-PERFUX-BUILD: tighter resting radius/altitude).
   `LABEL_REF_DIST` is defined relative to the resting distance, so the clamp constants
   are tuned only after RP2 framing is in place.

If either prerequisite is not yet landed, the build holds and reports the missing
dependency to O0; it does not proceed with placeholder tokens or a guessed framing.

## Mandate

Per `research/RP3_labels_scale_lgc.md`:

- **Which places.** Add an `inFootprint(place, TILESET_BOUNDS)` predicate (analog of the
  beacon `inBoundsNodes` filter) and render only the in-footprint gazetteer places
  (~24). Tier visibility by `place.kind` and camera distance: Tier 1 island/harbor/city
  always; Tier 2 village/terminal at a mid threshold; Tier 3 landmark only when close.
- **Anchoring.** Reuse the beacon placement seam verbatim: `projectToScene(lat,lng,...)`
  for X/Z, `surfaceYAt(group,x,z)` for surface Y, clamp `Math.max(y ?? 0, 0) +
  LABEL_LIFT_M`; re-place on the `useModelLoadTick` tick as tiles stream.
- **Clamped scale.** Drop drei `distanceFactor`. In `useFrame`, compute `dist`
  camera-to-anchor and set `s = clamp(LABEL_REF_DIST / dist, LABEL_SCALE_MIN,
  LABEL_SCALE_MAX)`, mutating the inner div `style.transform` on a ref (no React
  re-render). This is the operator's MIN/MAX curve: small but legible when far, capped
  when near. Tune `LABEL_REF_DIST` to the RP2 resting distance.
- **LGC glass.** New `.scene-label` class: cool frost fill at or above the opacity floor,
  scrim wash, ink text, hairline border, `blur=0` and NO `backdrop-filter` (M3 hard rule
  over the always-repainting canvas). Replaces the yellow `scene-beacon-label` look and
  serves both place labels and the hydrophone beacon labels.
- **Module layout.** Put the rig and the clamped-scale hook in a net-new
  `web/lib/scene/labels/` module so the shared-file diff on `SalishScene.tsx` is just the
  mount; edit `globals.css` for the `.scene-label` family only.

## Collision lock (serialize through O0)

`web/app/components/scene/SalishScene.tsx` and `web/app/globals.css` are convergence files
shared with W-CAM, W4, and the LGC lane (LGC charter section 3 collision lock). Do not edit
them in parallel with another lane; the scene mount and the CSS edit serialize through O0.

## Adversarial accept gate (frame-verified, GATED on O0)

Read-examine rendered frames at three distances (far, resting, near) and confirm:

1. Labels are anchored above the correct gazetteer place positions (not floating off the
   footprint, not sunk).
2. Scale stays within `[LABEL_SCALE_MIN, LABEL_SCALE_MAX]`: small but legible when far,
   capped (not dominating the frame) when near.
3. The LGC glass label clears WCAG AA contrast (ink on cool frost at or above the floor)
   over the worst-case composited frame; `LABEL_SCALE_MIN` keeps far text legible.
4. `tsc --noEmit` and the copy/prose gate are clean.

APPROVED only when all four hold on Read-examined frames. No commit without O0.

## Escalation / return

Escalate to O0 if a prerequisite is missing, if a clamp constant cannot be tuned against
RP2 framing, or if AA contrast fails on a real frame. Return the before/after frames, the
final `LABEL_*` constants, and the gate verdict.
