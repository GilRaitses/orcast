# ORCA O0 sign-off (2026-06-28)

Ratifies the decisions in `findings/SYNTHESIS_orca.md`. O0 + operator-authorized
("sign off where reasonable"). Honesty label intact: modeled animal driven by
simulated / partnership-gated biologging telemetry; not a measured swim of a named
individual.

| # | Decision | Call | Basis |
|---|---|---|---|
| 1 | H5 parse path | **Option B** - offline Python (h5py/tagtools) pre-bake to Float32Array bin + JSON; no new web runtime dep. Option A (h5wasm) deferred | SYNTHESIS_orca; avoids 3.3 MB WASM + license gate |
| 2 | Mesh download + LICENSE | **AUTHORIZED** - download the CC-BY 4.0 "Killer Whale" (Trouvaille, Sketchfab), convert to optimized glb, record `web/public/orca/LICENSE.md` with attribution. Backup: CC-BY 3.0 Poly. STOP if the only path is NC/ND/unclear | License verdict clean |
| 3 | OG-BUILD dev track | **APPROVED** - synthesize a **labeled SIMULATED** per-sample dev track from the aggregated in-repo fixture, marked simulated everywhere | Fixture is aggregated, not per-sample |
| 4 | Real Cascadia/NOAA H5 partnership data | **AGREEMENTS ASSUMED IN-PROCESS - PROCEED** (operator direction 2026-06-28). Train on genuinely-open **orca** DTAG data where it exists; contrast against the operator's **humpback** whale-tagger data; use the labeled-simulated track only as the dev stand-in until real data lands. Agreement-gated sources flagged, not blocking | Operator directed continuation |

## Added lane (2026-06-28): OG-DATA orca data sourcing + humpback contrast
A web-enabled OG-DATA sourcing lane is cleared: find/assess license-clear open orca DTAG/biologging
datasets (dive + kinematics), download only the openly-licensed ones with provenance/license, and
define the orca-vs-humpback movement contrast from the operator's whale-tagger humpback data.
Writes a sources catalog + contrast spec to the lane home and data under
`infra/orca/biologging/data/` (must NOT touch `prebake.py`/`requirements.txt`, owned by the running
OG-PREBAKE lane).

**Humpback contrast data: LOCATED** (operator confirmed 2026-06-28) -
`/Users/gilraitses/whale-behavior-analysis/Visualization_Poster_Appendix/data/dive_analysis.h5`
(real humpback `mn09_203a`, 5 Hz, 128 dives, animaltags layout). See `HUMPBACK_CONTRAST_DATA.md`
for the path set + the H5->rig channel map. Roles: (1) humpback column of the orca-vs-humpback
parameter table; (2) real-H5 validation input for `prebake.py`. Labeled humpback (contrast); the
orca twin is never driven by humpback motion.

## Dependency authorizations (for the Wave-0 build lanes)
- **OM-BUILD**: build-only CLI tooling allowed (`@gltf-transform/cli` / meshopt / KTX2)
  for conversion. **No new web runtime dependency** without a fresh O0 call. If the
  Sketchfab download requires interactive login, **STOP and return a precise manual
  download instruction** (file + target path) rather than guessing.
- **OG-PREBAKE**: offline Python deps (`h5py`, `numpy`) allowed in an isolated
  `infra/orca/biologging/requirements.txt`. Output is a dev fixture + baker script; no
  web edits.

## Build gating consequence
Two **non-colliding, net-new Wave-0 build lanes** are cleared to run in parallel now:
**OM-BUILD** (mesh, `web/public/orca/` + `infra/orca/mesh/`) and **OG-PREBAKE** (motion
data pipeline, `infra/orca/biologging/`). OR-BUILD (rig) is serial after OM. OMAT/OEYE/
OMOU/OPHYS and OINT remain gated (need rig, and OMAT needs the WFX env handoff).
