# ORCA-RIG charter (OR) - skeleton write-up + armature/skinning

- Lane code: **OR** (under family ORCA). Type: research-first (anatomy), then gated rig build.
- Depends on: **OM** (a clean, separable mesh to weight). Can research in parallel with OM-R.
- Owns (net-new): `docs/orca/SKELETON.md`, `web/lib/scene/orca/rig/`. Touches no existing file in research.

## Intent
"Write up the skeleton" - document the real orca (killer whale) skeleton, then build an armature
with skinning weights and named degrees of freedom the motion driver (OG) can address.

## Grounding (anatomy the rig must honor)
Odontocete skeletal plan: skull (rostrum + cranium, hinged lower jaw); vertebral column
cervical (7, partly fused) -> thoracic (with ribs) -> lumbar -> caudal; pectoral flippers
(humerus/radius/ulna/manus) on the pectoral girdle; **no pelvic girdle, no hind limbs**; the
**fluke is a fibrous structure on the caudal vertebrae (no bone in the fluke itself)** - it is
driven by the caudal chain. Swimming is dorso-ventral (up-down) fluke oscillation, unlike fish.

## Waves
- **OR-R (research, read-only):** `docs/orca/SKELETON.md` - the anatomical write-up with a
  labelled bone hierarchy and citations, mapped to a practical render armature: root -> spine
  chain (thoracic/lumbar) -> caudal chain (-> fluke) ; head/jaw ; two pectoral flippers. Define
  the **named DOFs** the driver will use: `body_yaw, body_pitch, body_roll` (heading-following
  turn/pitch/bank), a `caudal[ ]` oscillation chain (fluke-beat), `pectoral_L/R` (steering),
  `jaw` (optional). State joint counts + axes + sensible limits. Cite anatomy references.
- **OR-BUILD (gated on O0):** build the armature on the OM mesh in `web/lib/scene/orca/rig/`
  (bone hierarchy, bind pose, skinning weights so the caudal chain bends the fluke smoothly and
  flippers articulate), expose a typed `OrcaRig` API: `setOrientation(pitch,roll,yaw)`,
  `setFluke(phase,amplitude)`, `setDepthPose(...)`, `setPectoral(...)`. Net-new module; tsc clean;
  verified in the `/orca` sandbox with manual sliders.

## Acceptance
- OR-R: `SKELETON.md` is anatomically correct (cited), with the bone hierarchy + named DOFs +
  limits the driver will address.
- OR-BUILD (gated): the rig deforms the mesh believably (fluke beats dorso-ventrally, body banks
  into turns, no skin tearing) under manual sandbox sliders; `OrcaRig` API typed. No commit w/o O0.

## Handoff
The `OrcaRig` API (named DOFs) is the contract **ORCA-MOTION (OG)** drives from biologging
telemetry. OR defines the DOFs; OG maps sensor channels onto them.

## Escalation
Anatomy/quality trade-offs, dependency choices, or the gated build -> pause, return to O0.
