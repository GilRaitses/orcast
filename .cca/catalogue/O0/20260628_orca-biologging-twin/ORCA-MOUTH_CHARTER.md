# ORCA-MOUTH charter (OMOU) - jaw, teeth, tongue + articulation

- Lane code: **OMOU** (family ORCA). Type: research-first, then gated build.
- Depends on: **OM** (head/jaw geometry), **OR** (the `jaw` DOF), **OG** (dtag triggers for opening).
- Owns (net-new): `web/lib/scene/orca/mouth/`. No existing-file edits in research.

## Intent
"Mouth ... of the orca models." A credible mouth: lower-jaw articulation, interior geometry
(teeth, tongue, gum line), and data-aware opening tied to behavior (e.g. foraging/buzz events),
without turning the calm twin animal into an aggressive trope.

## Grounding
- Killer whales have **~40-56 conical interlocking teeth** (roughly 10-14 per quadrant), one set,
  no baleen. The lower jaw (mandible) hinges; the rostrum/upper jaw is largely fixed.
- OR already exposes a `jaw` DOF. OMOU supplies the geometry the jaw reveals (teeth/tongue/mouth
  cavity) and the open/close articulation + behavior triggers.
- OG carries dtag `foraging_indicators` (`buzz_events`, `click_rate`) and `dive_type`; a mouth-open
  cue can be tied to foraging/buzz moments - clearly labeled as modeled behavior, not a claim.

## Locked decisions
- Mouth interior is a **separate sub-mesh** (teeth row, tongue, gum/cavity) revealed by the OR
  `jaw` DOF; teeth count anatomically plausible (not a shark grin).
- Default state is **closed/relaxed**; opening is subtle and occasional, driven (when a stream is
  loaded) by OG foraging/buzz context, otherwise a rare idle. No aggressive gaping.
- Honesty: mouth-open as a foraging cue is **modeled behavior**, labeled; it does not assert the
  animal fed. Built on `three`.
- LOD: interior detail can drop far away (perf).

## Waves
- **OMOU-R (research, read-only):** `web/lib/scene/orca/mouth/OMOU-R_mouth.md` - anatomy
  (teeth count/shape, jaw hinge, tongue), the interior sub-mesh plan, the articulation curve on the
  OR `jaw` DOF, the OG trigger mapping (buzz/foraging -> subtle open, with the honesty caveat), and
  LOD. Reference imagery + citations.
- **OMOU-BUILD (gated on O0):** the mouth module in the `/orca` sandbox; tsc clean; verified jaw
  opens/closes believably with interior geometry, default relaxed, optional foraging-cued open.

## Acceptance
- OMOU-R: anatomy + interior + articulation + trigger + LOD spec, consistent with OR `jaw` + OG.
- OMOU-BUILD (gated): jaw articulates with credible interior, calm by default, foraging cue subtle
  and labeled. No commit without O0.

## Escalation
Behavior-trigger honesty, anatomy/quality, dependency, or any gated step -> pause, return to O0.
