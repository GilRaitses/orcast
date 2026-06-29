# ORCA-EYES charter (OEYE) - eye geometry, material, gaze

- Lane code: **OEYE** (family ORCA). Type: research-first, then gated build.
- Depends on: **OM** (head geometry), **OR** (head bone for gaze), **OMAT** (skin around the eye).
- Owns (net-new): `web/lib/scene/orca/eyes/`. No existing-file edits in research.

## Intent
"Eyes ... of the orca models." Believable eyes with a wet highlight and a subtle gaze, without
overstating realism at the demo viewport.

## Grounding
- The orca **eye** sits below/behind the **white eyepatch** (the eyepatch is SKIN pigment, owned by
  OMAT, not the eye). The visible eye is small and dark; a small specular catch-light sells "wet."
- Real cetacean eyes have a flat-ish cornea and a reflective tapetum; for a real-time twin a
  small spherical eye with a clear-coat cornea + a tiny specular highlight is sufficient. Avoid
  uncanny over-detail at distance.

## Locked decisions
- Eye is a **separate small mesh/material** (cornea clear-coat + dark iris/pupil + a catch-light),
  not painted into the skin texture, so it can hold a specular highlight and optional gaze.
- **Gaze** = a bounded look-at on the head bone (toward the camera or the current W-CAM target),
  clamped to a believable range; gaze never overrides the OG body orientation, it layers on top.
- LOD: the eye detail/gaze can drop to a static dark spot at far distance (perf + anti-uncanny).
- Honesty: cosmetic; asserts nothing measured. Built on `three`.

## Waves
- **OEYE-R (research, read-only):** `web/lib/scene/orca/eyes/OEYE-R_eyes.md` - eye placement on the
  OM head (relative to the OMAT eyepatch), the cornea/iris material spec + catch-light, the gaze
  model (target source, clamp range, how it composes with OR head bone + OG orientation), and the
  LOD plan. Reference imagery + citations.
- **OEYE-BUILD (gated on O0):** the eye module in the `/orca` sandbox; tsc clean; verified that the
  eye reads wet with a catch-light and the optional gaze stays believable, not googly.

## Acceptance
- OEYE-R: placement + material + gaze + LOD spec, consistent with OMAT eyepatch and OR head bone.
- OEYE-BUILD (gated): eyes read alive (catch-light, optional subtle gaze), no uncanny look at the
  demo viewport, drop to LOD far away. No commit without O0.

## Escalation
Gaze-vs-data composition, uncanny risk, dependency, or any gated step -> pause, return to O0.
