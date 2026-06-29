# ORCA-MATERIALS charter (OMAT) - skin material + shading

- Lane code: **OMAT** (family ORCA). Type: research-first, then gated build.
- Depends on: **OM** (UVs/topology to texture), and consumes the **WATER-FX (WFX)** light/environment.
- Owns (net-new): `web/lib/scene/orca/materials/`, `web/public/orca/textures/`. No existing-file edits in research.

## Intent
"Materials and shading ... of the orca models." A killer whale read that is believable under the
twin's water and light: correct countershading pattern, wet-skin BRDF, subsurface softness, and
consistency with the WFX environment so the orca does not look pasted into the scene.

## Grounding
- Orca coloration is **countershading**: glossy black dorsal, white ventral, a white **eyepatch**
  above/behind the eye, a grey **saddle patch** behind the dorsal fin, white flank/genital patches.
  This is pigment on skin (the eyepatch is skin, not eye - see OEYE).
- Wet cetacean skin is smooth and **highly specular** with shallow **subsurface scattering**; the
  black is near-specular-black, not matte.
- WFX (lane `WFX`, `.cca/catalogue/O0/20260628_water-fx/`) defines the sun/sky/PMREM environment
  and the underwater volumetrics/absorption. OMAT must light the orca from the **same** environment
  (above-surface PMREM/sun and underwater in-scatter/tint), or the animal will read disjoint.

## Locked decisions
- Pattern is **anatomically correct** (eyepatch, saddle, flank) - not a generic blob; either a
  painted texture set (albedo/normal/roughness) or a procedural mask, decided in research.
- Wet BRDF: high specular, low roughness, energy-conserving; subtle SSS in thin areas; the black
  stays glossy black (no crushed matte). No emissive, no cartoon rim light.
- **Light consistency with WFX is mandatory.** OMAT consumes the WFX environment; any new env API
  is coordinated with WFX via O0. Underwater the orca dims/tints per the WFX absorption, not a
  fixed studio light.
- Honesty: a modeled appearance; asserts nothing measured. Built on `three` PBR (`MeshStandard/
  Physical` or a custom shader); a new dependency is a costed recommendation.

## Waves
- **OMAT-R (research, read-only):** `web/lib/scene/orca/materials/OMAT-R_shading.md` - texture-set
  vs procedural-mask recommendation; the wet-skin BRDF spec (roughness/specular/SSS values);
  exactly how to bind the WFX above-water and underwater lighting; reference imagery + citations
  for the SRKW pattern; perf cost (texture sizes / shader).
- **OMAT-BUILD (gated on O0):** the material module + textures in the `/orca` sandbox under WFX
  lighting (above + below surface); tsc clean; visually verified countershading + wet read.

## Acceptance
- OMAT-R: a clear material approach with the pattern, BRDF spec, WFX binding, and costs.
- OMAT-BUILD (gated): orca reads as a wet, countershaded killer whale that sits correctly in the
  WFX light both above and below the surface; within budget. No commit without O0.

## Escalation
Texture-vs-procedural / dependency / WFX env-API coordination / any gated step -> pause, return to O0.
