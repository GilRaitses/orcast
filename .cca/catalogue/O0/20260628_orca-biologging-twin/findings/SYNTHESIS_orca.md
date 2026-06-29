# ORCA biologging twin, research synthesis (SYNTHESIS_orca.md)

Dated 2026-06-28. Written by the dispatched ORCA sub-orchestrator after the three read-only
research waves OM-R, OR-R, OG-R completed in parallel. This synthesis reconciles the rig wave
and the motion wave, records the decisions that need O0 sign-off, and fixes the build
sequencing. No build, no download, no conversion, no web edits, and no commit were performed.

## Findings documents produced

| Wave | Lane | Findings doc | Verdict |
|---|---|---|---|
| OM-R | mesh | `infra/orca/mesh/OM-R_candidates.md` | acceptable license-clean mesh found, no escalation |
| OR-R | rig | `docs/orca/SKELETON.md` | rig contract defined (bone hierarchy, named DOFs, typed API) |
| OG-R | motion | `infra/orca/biologging/OG-R_h5_mapping.md` | parse decision + channel-to-DOF mapping + honesty |

This synthesis lives at `.cca/catalogue/O0/20260628_orca-biologging-twin/findings/SYNTHESIS_orca.md`.

## 1. Recommended mesh (license verified)

Primary recommendation, "Killer Whale" by Trouvaille.

- Source URL: https://sketchfab.com/3d-models/killer-whale-63b680d7e58f463a9868ed7bf163094a
- Author: Trouvaille (@dashdu)
- License: Creative Commons Attribution 4.0 (CC-BY 4.0). Derivatives allowed, which the program
  requires because the mesh will be re-rigged and converted to glb.
- Attribution text to ship in `web/public/orca/LICENSE.md` and any published build: "Killer
  Whale" by Trouvaille (https://sketchfab.com/dashdu) licensed under CC-BY 4.0
  (https://creativecommons.org/licenses/by/4.0/), via Sketchfab. Confirm the exact creator
  handle and the copy-paste attribution string Sketchfab presents in the download dialog at
  download time.
- Fit and rig-readiness: full-body orca with dorsal fin, pectoral flippers, and fluke modeled in
  one piece, about 3.1k triangles, Sketchfab exports glTF and glb that line up with the proven
  glb plus EXT_meshopt_compression path in `web/lib/scene/tiles/useTilesLayer.ts`. An adult orca
  around 6 to 8 m lands near 0.018 to 0.024 scene units at the live worldUnitsPerMeter of about
  0.003. It is triangulated and low detail, so OM-BUILD should expect light cleanup or a quick
  retopo for a smooth fluke deformation, and should verify UVs after download.

Backup recommendation, "Killer Whale" by Poly by Google.

- Source URL: https://poly.pizza/m/7pqZEQ9b_E-
- License: CC-BY 3.0. Attribution: "Killer Whale" by Poly by Google, CC-BY 3.0, via Poly Pizza.
- Native glTF and OBJ, cleanest provenance in the survey, about 1.5k triangles, no textures.

Topology alternative if OM-BUILD wants the cleanest quad base, the DaveC Orca on BlendSwap
(https://blendswap.com/blend/4425, CC-BY), native Blender geometry, at the cost of a .blend to
glb export step.

License verdict: no escalation. All recommended assets carry verified CC-BY with derivatives
allowed. The Pisa museum skeleton scan (CC-BY-SA, STL) is recorded as an anatomy reference only,
not as the swimming skin. The rejected pile (Sketchfab Free Standard, CGTrader Royalty Free,
AI-generated CC0 claims, unmarked portfolio previews) is excluded on license grounds. See
`infra/orca/mesh/OM-R_candidates.md` for the full ranked table and the rejected list.

## 2. Skeleton and DOF contract (reconciled, the rig is the source of truth)

The contract is fixed in `docs/orca/SKELETON.md`. It follows real odontocete anatomy with cited
references (Buchholtz and Schur 2004 for vertebral counts and cervical fusion, Heyning and
Dahlheim 1988 for the species account, Cooper et al. 2007 and 2017 for the flipper bones and the
locked elbow and wrist, Fish 1998 and Fish et al. for the dorso-ventral thunniform stroke and
the boneless fluke).

Bone hierarchy, in brief.

```text
root
└── hips_anchor                       (body_pitch / body_roll / body_yaw pivot)
    ├── spine_lumbar
    │   └── spine_thoracic            (stiff, rib-braced trunk)
    │       ├── neck_fused (7 fused)  -> skull -> jaw
    │       ├── scapula_L -> pectoral_L  (rigid hydrofoil)
    │       └── scapula_R -> pectoral_R  (rigid hydrofoil)
    └── caudal[0..5]                  (propulsive chain)
        └── fluke_surface             (boneless, skinned to caudal tip)
dorsal_fin_surface                    (boneless, on spine_thoracic)
```

No pelvic girdle and no hind limbs, by anatomy. The fluke and dorsal fin carry no bone, so all
fluke motion comes from bending the six-joint caudal chain. The propulsive beat is dorso-ventral
about the lateral axis, never lateral sway and never an independent boneless flap.

Named DOFs and limits.

| DOF | Axis | Positive | Limit (degrees) |
|---|---|---|---|
| body_yaw | world up +Y | nose from +X toward +Z (port) | unbounded heading, about ±60 per turn |
| body_pitch | lateral Z | nose up | ±60 typical, ±90 for steep dives |
| body_roll | longitudinal +X | dorsal banks to port | ±45 typical, ±90 allowed |
| caudal[0..5] fluke beat | lateral Z (pitch axis) | dorso-ventral, tail-up positive, phase delay tailward | per joint tailward 8, 10, 14, 18, 22, 25 |
| pectoral_L / pectoral_R | pitch Z, sweep +Y, dihedral +X | leading-edge up, trailing-edge rear, tip raised | ±30, ±25, ±30 |
| jaw (optional) | lateral Z | open | 0 to about 35 |

Typed rig API the build wave implements, angles in radians at the API boundary.

```ts
setOrientation(pitch, roll, yaw)          // body_pitch (Z), body_roll (+X), body_yaw (+Y)
setFluke(phase, amplitude)                // dorso-ventral caudal[0..5] beat, propagates tailward
setDepthPose(depthMeters, { pitchBias })  // root TRANSLATION along world Y on the twin datum
setPectoral(side, { pitch, sweep, dihedral })
setJaw?(openRadians)                      // optional mandible hinge
```

Frame convention, +X forward (rostrum), +Y up (depth maps onto world Y), Z lateral. Right hand
rule about each named axis.

### Reconciliation of OR-R and OG-R

OG-R was written in parallel and could not see the rig doc, so it raised four reconciliation
requests. All four are already satisfied by `docs/orca/SKELETON.md`. Recorded resolutions so the
two docs agree on the record:

1. Vertical position versus dive pose. Resolved. `setDepthPose(depthMeters, { pitchBias })` is
   the vertical-position setter. It translates the root along world Y on the twin datum from a
   depth in metres and may add an optional pitch bias for descent or ascent posture. The
   canonical attitude still comes from `setOrientation`. No separate `setDepth` is needed.
2. Angle units. Resolved. The rig API takes radians at its boundary. The motion driver converts
   the in-repo degree-valued schema and the tagtools radian outputs into radians in exactly one
   place before calling the API.
3. Sign conventions. Resolved. Positive body_pitch is nose up. Positive body_roll banks the
   dorsal surface toward +Z (port, a left bank). These are stated in the rig doc and the motion
   driver maps tag signs onto them.
4. Roll range. Resolved. body_roll allows ±90, which covers the sustained near-90-degree
   foraging rolls OG-R flagged from Wright et al. 2017.

Conclusion: the rig DOFs (OR) and the sensor-to-DOF mapping (OG) are mutually consistent. The
fluke beat is dorso-ventral on the caudal chain in both documents, depth is a vertical
translation rather than a bone rotation in both, and the orientation channels target the same
three body DOFs through the same typed API.

## 3. H5 parse and mapping decision

Parse decision, recommend Option B, the Python pre-bake, with Option A held as a costed upgrade.

- Option B (recommended): an offline or CI step using h5py or the tagtools tooling opens the H5,
  aligns channels, derives pitch, roll, and heading, and emits a compact Float32Array binary plus
  a small JSON manifest of channels, units, rates, time base, and honesty flags. The web loads
  these with a plain fetch, the same pattern the glb and meshopt assets already use. Cost: an
  offline build step and a stored, versioned artifact, and it is not live-loadable by an end user
  dropping an H5 in the browser. Benefit: zero new web runtime dependency, no client license to
  clear, gated raw data stays off the public client.
- Option A (upgrade path): parse H5 in the browser with h5wasm. Cost: a new runtime dependency, a
  roughly 3.2 to 3.3 MB non-tree-shakable WASM binary on every visitor, async init, and a hard
  license gate because npm reports "SEE LICENSE IN LICENSE.txt" and GitHub classifies it "Other",
  so O0 must clear the pinned `LICENSE.txt` before adoption. Benefit: an end user could drop a
  real H5 in the browser and drive the twin live, a use case with no audience until a data-sharing
  agreement exists.

Channel-to-DOF mapping (locked, physical), targeting the rig API above.

| Sensor channel | Rig DOF | Units, frame, sign |
|---|---|---|
| heading | body_yaw via setOrientation | magnetic NED, declination-corrected to true, then yaw about scene +Y, radians |
| pitch | body_pitch via setOrientation | tagtools a2pr, positive nose up, radians |
| roll | body_roll via setOrientation | tagtools a2pr, longitudinal axis, full range incl near ±90, radians |
| depth (from pressure p) | world Y via setDepthPose | metres positive down, Y = -depth * worldUnitsPerMeter, read the live fit value not a hard-coded 0.003 |
| accelerometer Az oscillation | setFluke(phase, amplitude) | animal-frame heave, remove gravity, bandpass to the orca stroke band about 0.3 to 1.0 Hz with dsf().fpk per segment, feed phase and DBA amplitude |
| dive / foraging context | optional behavior tint or speed | labeled presentation context, not a measured DOF |

Frame and timing: convert tag NED to the y-up scene, correct declination, convert degrees to
radians once, interpolate every channel to the render frame time so the animation is frame-rate
independent, and reconstruct horizontal track by dead-reckoning from speed, heading, and pitch
(WHOI ptrack style) or by a synthesized plausible track. Horizontal track must be labeled
reconstructed, not measured GPS. See `infra/orca/biologging/OG-R_h5_mapping.md` for the cited
schema, the dsf and complementary-filter procedure, and the per-step conversion.

## 4. Decisions needing O0 sign-off

Dependency decisions.

1. H5 parse path. Recommended Option B, the offline Python pre-bake, no new web runtime
   dependency. This is the default unless O0 wants a live in-browser H5 drop, in which case
   Option A (h5wasm) is the upgrade and O0 must clear the pinned h5wasm `LICENSE.txt` and accept
   the 3.2 to 3.3 MB bundle and async-init cost. Fallback for Option A is Option B.
2. Mesh source adoption. OM-BUILD downloads and converts a CC-BY asset. The download, the
   conversion, and recording `web/public/orca/LICENSE.md` are O0 and operator gated. The
   attribution string must be confirmed at download time and must travel with the converted glb.

Data-access and honesty decisions.

3. Real H5 partnership gate. A real per-sample orca H5 (Cascadia or NOAA DTAG) requires a
   data-sharing agreement. O0 owns the decision to pursue it. Until it exists, the twin runs on
   the simulated fixture or on synthesized data and must be labeled modeled and simulated.
4. Aggregated-fixture limitation. The in-repo fixture `cascadia_2010_k33_test`
   (`data/dtag_analysis_results.json`, `simulated: true`) is aggregated dive analysis, not a
   per-sample time series. It reports 36000 samples over 0.2 h, which implies a roughly 50 Hz
   stream existed upstream, but that stream is not in the JSON, so the fixture alone cannot drive
   per-sample orientation or a per-sample Az fluke beat. OG-R recommends, and I forward for O0
   sign-off, that OG-BUILD synthesize a labeled plausible per-sample track from the aggregated
   dive events (depth profile from max_depth, descent_rate, ascent_rate, duration, bottom_time,
   stitched with surface periods, plausible pitch from depth rate, synthetic Az in the orca
   stroke band) so the rig and mapping can be exercised in development, kept clearly marked
   simulated until a real H5 is loaded.

Honesty label (locked, restated). The orca is a modeled animal. Its motion is driven by
simulated or partnership-gated biologging telemetry. It is not a measured swim of a named
individual unless a real, agreement-covered H5 is loaded. The sandbox and HUD must say so.

## 5. Build sequencing (all waves O0 and operator gated)

The build order is serial because each wave hands a concrete artifact to the next.

1. OM-BUILD. Download the chosen CC-BY mesh, record `web/public/orca/LICENSE.md` with the
   verified source, author, license, and attribution, convert and optimize to
   `web/public/orca/orca.glb` (gltfpack or meshopt, optional KTX2), scale and orient to the twin
   frame (heading +X, up +Y), and add a loader stub `web/lib/scene/orca/loadOrcaMesh.ts`. tsc
   clean. Gate: download and conversion are O0 and operator gated.
2. OR-BUILD. Build the armature on the OM mesh in `web/lib/scene/orca/rig/` following
   `docs/orca/SKELETON.md`, with skinning weights so the caudal chain bends the fluke smoothly
   and the flippers articulate, and expose the typed `OrcaRig` API. Verify in the `/orca` sandbox
   with manual sliders. Depends on OM-BUILD (needs the mesh to weight).
3. OG-BUILD. Build the loader and driver in `web/lib/scene/orca/motion/`, `loadBiologging(source)`
   to a typed time series and a per-frame `driveOrca(rig, t)` that sets the rig DOFs from the
   stream by the mapping in section 3, frame-rate independent, with a clearly labeled procedural
   fallback only when no stream is loaded. Tune in the `/orca` sandbox against the simulated
   fixture. Depends on OR-BUILD (drives the `OrcaRig` API).
4. OINT. Mount the driven orca into `web/app/components/scene/SalishScene.tsx` underwater view
   (3D-TWIN W4), single editor, serialized against W-CAM, W-LABELS, W3, W4, WFX, and LGC. Commit
   is an operator gate.

## 6. Status and return

Research is complete and read-only. The three findings docs and this synthesis are written. No
download, no conversion, no web edits, no `next dev` or `next build`, and no commit were
performed. All BUILD waves and the OINT mount are paused pending O0 and operator sign-off on the
decisions in section 4. Returning to O0.
