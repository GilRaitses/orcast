# OCN — measured-ocean-stratification (waveset charter)

- Lane code: `OCN`  Family: `BSWR`  Owner: dispatched sub-orchestrator (answers to O0)
- Type: execution (offline CTD bake + web scene module), GPU-verified
- Home: `.cca/catalogue/O0/20260629_bsw-followup-remediation/` ; dispatch `dispatch/OCN/`
- `repo_state_verified_against`: `61ba1d69ee36cf605f7ba741bdaa1defa8762834`
- Umbrella: `PROGRAM.md` ; predecessor: BSW `BSW-SPECTRO-HUD_CHARTER.md` (BSH owns the ocean layer)

## Intent

Ground the interpretive double-diffusion ocean layer in a measured cast, and make
the layer depth-aware against the real water surface, without regressing the WFX
water and without overclaiming. The visualization stays interpretive; only its
stratification profile becomes measured.

## Grounding (real seams + verified root cause)

- `web/lib/scene/ocean/stratification.ts`: already defines
  `StratificationOrigin = "analytic" | "measured-ctd"` and ships an
  `analyticHaloclineProfile` (stylized, surface ~28 PSU / 13 C, deep ~31.2 PSU /
  9 C). Its own comment names the upgrade: a CC0 CruiseSalish CTD profile baked
  offline (NANOOS CruiseSalish / NCEI Accession 0307188), gated, "See BSW-R09".
  `stratificationToTexture` bakes a width x 1 DataTexture the shader samples by
  depth fraction.
- `web/lib/scene/ocean/{doubleDiffusion,interpretiveOceanLayer,perf,index}.ts`:
  the interpretive layer (default-off, additive, `depthWrite:false`) that consumes
  the profile texture.
- `interpretiveOceanLayer.ts` carries an interpretive honesty label and a
  module-load forbidden-claim guard. The BSW campaign already crashed once on a
  negated "biosonar perception" phrase here; wording is gated.
- WFX water depth seam: the layer needs the real water-surface depth to clip the
  plume against the surface (R09 depth-aware plume-clipping). The WFX `Water2`
  depth handle is the read-only seam; this overlaps the ENV/WFX consolidation.

Root cause: the profile is a stylized analytic curve, and the layer is not clipped
against the measured water surface. The `measured-ctd` origin enum exists but no
measured profile is baked, and no depth-aware clip is wired.

## Locked decisions (do NOT reopen)

1. The layer stays INTERPRETIVE. Grounding the profile in a measured cast does
   NOT make the double-diffusion visualization measured. The label states exactly
   what is measured (the CTD cast: depth, temperature, salinity) and what is
   interpretive (the mixing-band visualization). Wording passes `.cca/CLAIM_BOUNDARIES.md`
   and the prose gate, and must not trip the module-load guard.
2. CruiseSalish CTD is CC0. Verify per asset before download; record provenance
   and the NCEI accession. Raw casts go to the box; only the small baked profile
   JSON + provenance ship in-repo.
3. Read-only WFX seam. OCN consumes the WFX water-surface depth through a
   read-only handle; it does NOT mutate WFX water, `scene.environment`,
   `scene.fog`, or `scene.background`. If the depth seam does not exist yet, that
   is a coordination return to O0 (it overlaps ENV), not a WFX edit by OCN.
4. Default-off, additive, `depthWrite:false` stays. No water regression: the WFX
   open-water, shoreline, and underwater frames must be unchanged with the layer
   off, and physically plausible with it on.
5. `interpretiveOceanLayer.ts` is the BSH-owned convergence point for this layer;
   any `SalishScene.tsx` touch is a single serialized editor in `OCN-INT`,
   serialized across WFX / ENV / ORCA / 3D-TWIN.

## Wave structure

- `OCN-R` (research + discovery, read-only). Parallel; each owns one `dispatch/OCN/findings/OCN-<TOPIC>.md`:
  - R1 CTD data: NANOOS CruiseSalish / NCEI 0307188 format, access, license (CC0 confirm), the variables and depth range a Salish cast provides; the offline parse path (no heavy runtime dep).
  - R2 bake path: how to turn a real cast into a `StratificationProfile` with `origin: "measured-ctd"` and an honest provenance line, reusing `stratificationToTexture`.
  - R3 depth-clip seam: the WFX water-surface depth read API (`Water2` handle); how the plume clips against the surface read-only; the overlap with ENV.
  - R4 adversarial: honesty-label correctness, the forbidden-claim guard, water-regression risk, perf budget of the depth-aware path.
- `OCN-Q` (qualify methodology). GATED. Fixes the ingestion + bake method and the depth-clip method (read-only seam shape), the exact honesty label, and the pass metric; names the CC0 download and the WFX-seam coordination for O0. Returns to O0.
- `OCN-B` (implement). Offline CTD bake script (box) + a measured `StratificationProfile` loader + the depth-aware clip, net-new under `web/lib/scene/ocean/**` + `infra/ocean/**`; no WFX or `SalishScene` mutation.
- `OCN-INT` (integrate). GATED. Single editor wires the measured profile + depth-clip into `interpretiveOceanLayer.ts` (and `SalishScene.tsx` only if a new param is needed); serialize across WFX/ENV/ORCA/3D-TWIN.
- `OCN-ADV` (adversarial review). Re-audits label honesty, the guard, water regression, perf; loops back to `OCN-B`/`OCN-INT` until zero open P0/P1.
- `OCN-ACCEPT` (accept). GATED. GPU before/after frames (layer off = WFX unchanged; layer on = depth-clipped measured profile, physically plausible); Read-examined; frame-time A/B within budget.

## Acceptance criteria (hard, checkable)

- A measured `StratificationProfile` with `origin: "measured-ctd"` and an honest CC0-attributed provenance line is baked from a real cast; raw cast in the box, baked JSON + provenance in-repo.
- The interpretive layer clips against the real water surface (no plume above the surface; correct depth placement) using a read-only WFX seam, with no WFX edit by OCN.
- Layer-off GPU frames are pixel-equivalent to pre-OCN WFX; layer-on frames are physically plausible and Read-examined.
- The honesty label is exact (measured cast vs interpretive visualization) and passes the prose gate and the module-load guard.
- Frame-time A/B is within the stated budget.

## Escalation

Per PROGRAM.md. Pause and return to O0 on the CC0 download, the WFX depth-seam
coordination (overlaps ENV), the convergence edit slot, the GPU capture, or commit.
