# ORCA appearance + physics - research synthesis (OMAT / OEYE / OMOU / OPHYS)

Sub-orchestrator: appearance + physics lanes. Wave: research-only, read-only. Status: findings
written; no source edited; no dependency installed; no build lane marked done. All builds remain
O0-gated.

**Honesty statement.** Every lane below specifies a MODELED orca driven by SIMULATED /
partnership-gated biologging telemetry. Nothing here asserts measured behavior of a named
individual. Appearance is generic SRKW; the mouth-open cue is labeled modeled behavior; the
physics is bounded polish that provably tracks the telemetry.

Findings docs written this wave:
- `web/lib/scene/orca/materials/OMAT-R_shading.md`
- `web/lib/scene/orca/eyes/OEYE-R_eyes.md`
- `web/lib/scene/orca/mouth/OMOU-R_mouth.md`
- `web/lib/scene/orca/physics/OPHYS-R_dynamics.md`
- this synthesis

---

## 1. Lane recommendations (2-3 lines each)

**OMAT (skin shading).** Use a hybrid: a hand-authored RGBA region mask plus a small albedo/
normal/roughness set on the OM UVs, not a pure procedural mask. Wet-skin BRDF as
`MeshPhysicalMaterial` with a thin clearcoat film: dorsal black `#0b0d10` roughness 0.16 (glossy,
never matte), white ventral/eyepatch roughness ~0.22-0.24 with cheap sheen-SSS, grey saddle
~0.30. Light from the WFX PMREM + sun above water and inject the WFX per-channel Beer-Lambert
absorption + in-scatter below water via `onBeforeCompile`.

**OEYE (eyes + gaze).** A separate small eye mesh below/behind the OMAT eyepatch, clearcoat
cornea + near-black iris, catch-light from the same WFX env (not a baked speck). Gaze is a
bounded, damped look-at toward the W-CAM camera/target, clamped yaw +/-25 deg, pitch +/-15 deg,
composed strictly AFTER OG/OR/OPHYS on the OR head bone and never writing body orientation. LOD
drops gaze then the eye mesh at distance to kill uncanny.

**OMOU (mouth).** Interior sub-mesh (about 48 conical interlocking teeth, mandible-parented lower
row, tongue, dark cavity) revealed by the OR `jaw` DOF; articulation 0-3 deg relaxed, 8-15 deg
subtle open, hard cap < 25 deg, no gape. Open cue raised in probability during OG dive/buzz
context, default closed; labeled modeled behavior, explicitly not a feeding claim (fixture
`foraging_dives` is 0, classifier `not_trained`).

**OPHYS (secondary dynamics).** Spine IK for heading-follow (zeta 1.0), under-damped caudal/fluke
follow-through (zeta 0.6-0.8, omega_n 6-12 rad/s), damped pectoral trailing flex; banking flex
derived from OG turn rate and clamped, consistent with OG roll. Bounded, clamped, frame-rate
independent via a fixed-timestep accumulator. Hand-rolled (~120-200 LOC), no new dependency.

---

## 2. Cross-lane reconciliation items for O0 (build-time)

**WFX lighting handoff (top item).** OMAT (and the OEYE catch-light) must consume the SAME
environment as the water, above and below. This requires WFX to publish:
1. a **PMREM environment texture** from its procedural sky (none exists today; `applyRealism.ts`
   only sets a flat `scene.background`), owned by WFX-R04 + WFX-R05;
2. the **underwater per-channel absorption vector + in-scatter color + water-level Y + visibility**
   as shared uniforms, owned by WFX-R08 + WFX-R09 + WFX-R11, consistent with
   `web/lib/scene/water2/depthWater.ts` and the pending `WATER2_TUNING_REQUEST.md`
   (`uAbsorption ~ vec3(3.0, 1.6, 0.9)`).
**Blocker note:** the entire WFX `research/` folder is currently EMPTY, so the proposed
`WfxEnvHandle` interface (OMAT-R section 3) is a proposal O0 must reconcile against the WFX
synthesis before OMAT-BUILD or OEYE-BUILD. Until WFX exposes the env, the orca cannot be lit
consistently.

**OR DOF contract (`docs/orca/SKELETON.md` / `web/lib/scene/orca/rig/`).** Not yet written.
Needed before the dependent builds:
- head-bone name + optional head DOF (OEYE gaze offset),
- `jaw` hinge axis/pivot/limits and a mandible bone the OMOU lower tooth row + tongue parent to,
- spine bone count + caudal chain length + all joint limits (OPHYS IK + clamps).

**OG mapping contract (`infra/orca/biologging/OG-R_h5_mapping.md` + `driveOrca`).** Not yet
written. Needed:
- a per-frame behavior-context signal (in-dive + normalized foraging intensity) for the OMOU
  open cue,
- the raw per-frame OG pose exposed so OPHYS can layer on it AND the OPHYS harness can run the
  A/B tolerance comparison,
- the per-frame ordering lock: **OG -> OPHYS -> OEYE gaze** (OMOU jaw independent).

**OM mesh/UV contract.** Not yet written. Needed: UV-unwrapped head/body for OMAT textures, a
left/right head locator at the lower-leading eyepatch corner for OEYE, and the rostrum-vs-
mandible vertex split for OMOU.

**Intra-appearance boundaries.** Eyepatch = OMAT skin; eye = OEYE mesh below it. Exterior lip
line = OMAT; mouth interior = OMOU. Reconcile these seams so no gap shows at the eye socket or
the gape.

---

## 3. Build-order recommendation (all O0-gated; not started)

Hard prerequisites for every appearance/physics build: **OM** (mesh/UVs), **OR** (DOFs), **OG**
(driver) from the concurrent core orchestrator, plus the **WFX env handoff** for OMAT/OEYE.

Suggested order once prerequisites land:
1. **OMAT-BUILD** first - it owns the skin, the region mask, and the WFX env binding the others
   depend on (OEYE catch-light reuses the env; OMOU lip seam meets OMAT skin).
2. **OPHYS-BUILD** next - it only needs OR + OG, runs independent of lighting, and its tolerance
   harness should be green before the orca is shown moving.
3. **OEYE-BUILD** and **OMOU-BUILD** - depend on OMAT (eyepatch/lip seams) and OR (head bone /
   `jaw`); can run in parallel with each other once OMAT lands.
4. **OINT (convergence)** - mounting the lit, rigged, driven, polished orca into the underwater
   view of `web/app/components/scene/SalishScene.tsx` is a later O0-gated step that serializes
   against W-CAM / W-LABELS / W3 / W4 / WFX / LGC. Out of scope here.

No build lane is marked done. The WFX env handoff and the OR/OG contracts are the gating
reconciliation items.
