# PROVENANCE — Tennessen et al. 2024 killer-whale DTAG movement data (open subset)

- **Dataset:** "Males miss and females forgo: auditory masking from vessel noise
  impairs foraging efficiency and success in killer whales — CALIBRATED MOVEMENT DATA
  AND VARIABLES SUPPORTING ANALYSES"
- **Host:** Zenodo
- **Version DOI (downloaded):** https://doi.org/10.5281/zenodo.13308835
- **Concept DOI (all versions):** https://doi.org/10.5281/zenodo.13308834
- **Published:** 2024-08-13
- **License:** CC-BY-4.0 (open access) — verified via Zenodo REST API on 2026-06-28
- **Species:** *Orcinus orca* — Northern Resident (NRKW) and Southern Resident (SRKW)
  fish-eating killer whales (NE Pacific / Salish Sea). Tag deployment naming:
  `oo<YY>_<JulianDay><pop>` where population letter `a–d` = Northern Residents, `m` =
  Southern Residents.
- **Tag:** DTAG (Woods Hole Oceanographic Institution suction-cup multisensor tag).
- **Provider credit:** NOAA Fisheries NWFSC + Fisheries and Oceans Canada (DFO).

## Honesty label
This is **real, openly-licensed killer-whale biologging data**. Where the twin's orca
motion is parameterized from it, it must be labeled "modeled orca motion, parameterized
from cited open killer-whale DTAG data (Tennessen et al. 2024, CC-BY-4.0)." Nothing here
authorizes asserting a measured swim of a *named individual* in the public twin beyond
what these files literally contain; the deployments are identified only by deployment
code, sex, and population in the source.

## What was downloaded (this directory)
A representative, license-clear subset (not the full 25-file, multi-GB record) covering
both ecotypes plus the per-dive summary table:

| File | Size | Content |
|---|---|---|
| `oo11_224bprh50.mat` | 7.1 MB | NRKW deployment, calibrated PRH @ 50 Hz, ~19.4 min |
| `oo14_264mprh50.mat` | 48.3 MB | SRKW deployment, calibrated PRH @ 50 Hz, ~136.5 min |
| `foraging_data.csv` | 127 KB | per-dive summary for ALL 25 deployments (both ecotypes) |

SHA-256:
```
16230ccc5e1ef7d5cc24bca228587b7d797e937b32d5ba09e6c441bcf0cedc47  oo11_224bprh50.mat
53d5c47a11d0dc7a750c381092feb5e4f368d6f3036f72ba289ff03c411d5ff1  oo14_264mprh50.mat
84435263cb27bfb2c5d4f239760b099e34a100b2306e462b6f330777a2a42333  foraging_data.csv
```

The other 23 `.mat` deployment files (up to 255 MB each; ~2.5 GB total) and the
separately-DOI'd raw audio (`.dtg`, tens of GB) are **also CC-BY-4.0 and openly
downloadable** from the same record but were not pulled here to keep the in-repo data
footprint small. Pull more with:
`curl -L "https://zenodo.org/api/records/13308835/files/<NAME>.mat/content" -o <NAME>.mat`

## .mat structure (verified by loading `oo11_224bprh50.mat`)
MATLAB v5 MAT-file (loads with `scipy.io.loadmat`; no HDF5/h5py needed). Variables:

| Var | Shape | Meaning (per Zenodo record + tagtools convention) |
|---|---|---|
| `p` | (N,1) | depth in metres (pressure-derived), positive down |
| `pitch` | (N,1) | animal pitch, **radians** (rotation about left–right axis) |
| `roll` | (N,1) | animal roll, **radians** (rotation about longitudinal axis) |
| `head` | (N,1) | animal heading, **radians** (rotation about dorso-ventral axis) |
| `A` | (N,3) | tag-frame tri-axial accelerometer |
| `Aw` | (N,3) | **animal-frame** tri-axial accelerometer (tag→whale frame) |
| `M` | (N,3) | tag-frame tri-axial magnetometer |
| `Mw` | (N,3) | **animal-frame** tri-axial magnetometer |
| `fs` | (1,1) | sample rate = **50 Hz** |
| `TT`, `TTfs`, `Tnew`, `diveindices` | small | dive/event tables and indices |
| `tempr` | (N,1) | temperature |
| `tag` | str | deployment id |

`N` = 58,291 samples (≈19.4 min) for `oo11_224b`; 409,370 (≈136.5 min) for `oo14_264m`.

## Mapping onto the OG-R channel→DOF contract (`infra/orca/biologging/OG-R_h5_mapping.md`)
This dataset satisfies the contract **directly and fully** (it is the calibrated-PRH
product the OG-R doc names as the project's internal target):

- `heading (head)` → `body_yaw` — already radians; apply magnetic→true declination, then
  yaw about scene +Y. (Contract expected degrees from the in-repo schema; this open set
  is already radians, so the deg→rad step is skipped for this source.)
- `pitch` → `body_pitch` — radians, a2pr convention (nose-up positive).
- `roll` → `body_roll` — radians; full ±180° range present (foraging rolls), so the rig
  must accept full range, exactly as the contract's roll-range note requires.
- `depth (p)` → world Y: `Y = -p * worldUnitsPerMeter` on the NAVD88 twin datum.
- `Aw[:,2]` (animal-frame dorso-ventral / heave, "Az") → `setFluke(phase, amplitude)`:
  subtract static gravity, bandpass to the orca stroke band, read instantaneous phase +
  envelope. Per-segment dominant stroke frequency should come from `dsf()`/FFT, not a
  constant (measured ≈0.20–0.34 Hz in these two records — see the sources catalog).
- dive context: `diveindices`/`TT` + `foraging_data.csv` (`kindet` prey-capture flag,
  `maxdep`, `durwho`) → optional honest behavior tint, not a measured DOF.

Nothing in the contract is *missing* for this source: depth + tri-axial accel +
magnetometer + derived pitch/roll/heading are all present at 50 Hz. This is the single
best openly-downloadable orca dive/kinematics dataset found.
