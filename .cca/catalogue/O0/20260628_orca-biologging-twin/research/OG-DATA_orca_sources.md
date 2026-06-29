# OG-DATA — Open orca biologging source catalog (sourcing lane)

Lane: **OG-DATA** (web-enabled sourcing) for the ORCA biologging twin. Read-alongside:
`SIGN_OFF.md` decision 4 + OG-DATA note, `ORCA-MOTION_CHARTER.md` real-data section,
`infra/orca/biologging/OG-R_h5_mapping.md` (channel→DOF contract).

Operator direction (2026-06-28): assume data-sharing agreements are in process, proceed
without delay, **download only openly-licensed data**, flag agreement-gated sources.

## Honesty hard line (applies to everything below)
The twin's orca is a **modeled** animal. Its motion is "**modeled orca motion,
parameterized from cited open killer-whale DTAG data**." Where a number comes from the
downloaded CC-BY set it is real orca data; where it comes from a paper it is cited
literature. We assert nothing measured about a *named individual* beyond what an open
file literally contains (the open set identifies deployments only by code, sex, ecotype).

---

## Headline counts
- **Open orca datasets found: 1** genuinely open + downloadable with per-sample
  kinematics → **Tennessen et al. 2024** (CC-BY-4.0, Zenodo). **Downloaded.**
- **Agreement-gated / not-open orca sources flagged: 4** — Wright et al. 2017 (open text,
  data not deposited), NWFSC InPort SRKW DTAGs (agency-gated), Antarctic Type B/C
  satellite-dive (by request, depth-only), Norway herring-feeding orca (paper only).
- **Plus:** 1 open **humpback** contrast set (CC0, Dryad bubble-net) whose license is
  open but whose download is blocked by bot-protection in this environment; 1
  license-ambiguous tagtools example repo (not downloaded).

## Single best openly-downloadable orca dataset
**Tennessen et al. 2024 — "CALIBRATED MOVEMENT DATA …"**, Zenodo
[10.5281/zenodo.13308835](https://doi.org/10.5281/zenodo.13308835), **license CC-BY-4.0**
(verified via the Zenodo REST API: `metadata.license.id == "cc-by-4.0"`, `access:open`).
Real DTAG calibrated PRH at **50 Hz** for both **Northern Resident** and **Southern
Resident** fish-eating killer whales, containing `p` (depth), `Aw`/`A` (tri-axial accel,
animal + tag frame), `Mw`/`M` (magnetometer), and derived `pitch`/`roll`/`head`
(radians) — i.e. exactly the OG-R contract product. Downloaded subset:
`oo11_224bprh50.mat` (NRKW, 19.4 min), `oo14_264mprh50.mat` (SRKW, 136.5 min),
`foraging_data.csv` (per-dive `maxdep`/`durwho`/prey-capture for all 25 deployments).
See `infra/orca/biologging/data/tennessen2024_srkw_dtag/PROVENANCE.md`.

---

## Ranked candidate table

| Rank | Dataset | Host | Species / ecotype | Sensors / variables | Sample rate | Format | License (exact) | Downloadable w/o agreement? |
|---|---|---|---|---|---|---|---|---|
| 1 | **Tennessen et al. 2024 calibrated movement data** ([zenodo 13308835](https://doi.org/10.5281/zenodo.13308835)) | Zenodo | *O. orca* — NRKW + SRKW (fish-eating) | depth, Aw/A accel, Mw/M mag, pitch/roll/head, temp | 50 Hz | `.mat` (v5) + `.csv` | **CC-BY-4.0** | **YES — downloaded** |
| 2 | Wright et al. 2017 ([10.1186/s40462-017-0094-0](https://doi.org/10.1186/s40462-017-0094-0)) | Movement Ecology / figshare | *O. orca* — NRKW (fish-eating) | depth, tri-axial accel, mag, audio | 50/250 Hz → 5 Hz calib | n/a | **CC-BY-4.0 (article text only)** | NO (per-sample data not deposited) |
| 3 | Bubble-net humpback ([dryad m0cfxppbj](https://datadryad.org/dataset/doi:10.5061/dryad.m0cfxppbj)) | Dryad | *M. novaeangliae* (HUMPBACK contrast) | depth + speed profiles, lunge/dive kinematics | profile-rate | `.csv` | **CC0-1.0** | License open; **blocked by WAF/PoW here** |
| g | NWFSC InPort DTAGs SRKW ([item 17972](https://www.fisheries.noaa.gov/inport/item/17972)) | NOAA NWFSC | *O. orca* — SRKW | sound, pitch/roll/heading, depth | DTAG | agency portal | not an open data license | **NO — agreement-gated (in process)** |
| g | Antarctic Type B/C satellite-dive (Durban & Pitman 2012 [10.1098/rsbl.2011.0875](https://doi.org/10.1098/rsbl.2011.0875); Andrews et al. 2008 [10.1007/s00300-008-0487-z](https://doi.org/10.1007/s00300-008-0487-z)) | journals / SWFSC | *O. orca* — Type B/C | Argos location + dive-depth bins (TDR-style) | dive bins | n/a | not openly deposited | **NO — by request** |
| g | Norway herring-feeding orca (Mul et al. [10.1111/mms.12931](https://doi.org/10.1111/mms.12931)) | Marine Mammal Science | *O. orca* — Norwegian herring | video + accel, depth, mag (roll/pitch/jerk) | multisensor | n/a | paywalled, no open deposit | **NO — paper only** |
| a | tagtools example data ([github](https://github.com/animaltags/tagtools_data)) | GitHub / R pkg | mixed (incl. humpback `testset7.nc`) | depth/accel/mag examples | varies | `.nc` | **NONE in repo** (pkg copy = GPL-3 software lic.) | technically yes, but **unlicensed data — not downloaded** |

(g = agreement-gated / not open; a = license-ambiguous.)

---

## What was downloaded vs flagged

**Downloaded (open, CC-BY-4.0):** Tennessen et al. 2024 subset →
`infra/orca/biologging/data/tennessen2024_srkw_dtag/` with `LICENSE.txt`, `PROVENANCE.md`,
SHA-256s. Both ecotypes + the all-deployment dive-summary CSV.

**Flagged, not downloaded:**
- Wright et al. 2017 — open article, no open per-sample deposit. Cited, not pulled.
- NWFSC InPort SRKW DTAGs — agency-gated (the charter's partnership track); in process.
- Antarctic Type B/C — by-request, and **depth-only** (satellite + dive bins, no accel).
- Norway herring orca — paper only, no deposit.
- Dryad bubble-net **humpback** (CC0) — license is open, but the file download is gated by
  an AWS WAF + within.website Anubis proof-of-work challenge that blocks headless curl and
  same-origin browser fetch. **Not agreement-gated** — a human in a browser can pull it.
- tagtools_data GitHub — no explicit data license; excluded under the "openly licensed
  only" rule.

---

## How the open set maps onto the OG-R channel→DOF contract

Verified by loading the `.mat` (MATLAB v5; `scipy.io.loadmat`, **no HDF5/h5py needed**).
The contract in `OG-R_h5_mapping.md` is satisfied **fully** — this is the calibrated-PRH
product the contract names as the project's internal target:

| OG-R contract channel | Present in this set? | Field | Note |
|---|---|---|---|
| heading → `body_yaw` | yes | `head` (rad) | already radians; apply declination → true → yaw about +Y |
| pitch → `body_pitch` | yes | `pitch` (rad) | a2pr nose-up-positive |
| roll → `body_roll` | yes | `roll` (rad) | **full ±180° range present** → rig must accept full range |
| depth → world Y | yes | `p` (m) | `Y = -p * worldUnitsPerMeter` on NAVD88 datum |
| Az heave → `setFluke(phase,amp)` | yes | `Aw[:,2]` | subtract gravity, bandpass to stroke band, read phase+envelope |
| dive/foraging context | yes | `diveindices`/`TT`, `foraging_data.csv` (`kindet`,`maxdep`) | honest tint only |

**Nothing in the contract is missing for this source** (depth + tri-axial accel +
magnetometer + derived PRH @ 50 Hz). Contrast: the Antarctic Type B set is **depth-only**
(satellite dive bins, no accel/mag) → it could seed a depth track but **cannot** drive the
Az fluke beat or pitch/roll attitude.

---

## Real kinematics computed from the downloaded open data
(Computed directly from the two CC-BY `.mat` files + `foraging_data.csv`. These are the
honest, source-grounded numbers feeding the orca side of the parameter table in
`OG-DATA_orca_vs_humpback.md`.)

| Metric | NRKW `oo11_224b` (19.4 min) | SRKW `oo14_264m` (136.5 min) | Source |
|---|---|---|---|
| depth: mean / max | 6.6 m / 17.6 m | 17.0 m / 155.1 m | `p` channel |
| depth p95 | 16.2 m | 141.7 m | `p` channel |
| pitch range; \|pitch\| p95 | ±84°; 40° | ±90°; 62° | `pitch` (rad→deg) |
| roll range; \|roll\| p95 / p99 | ±180°; 171° / 178° | ±180°; 133° / 175° | `roll` (rad→deg) |
| dominant heave (Aw_z) freq | 0.34 Hz (submerged) / 0.20 Hz (full) | 0.21 Hz (submerged) / 0.23 Hz (full) | FFT of `Aw[:,2]` |

Per-dive depth across **all 25 deployments** (`foraging_data.csv`):

| Ecotype | n dives | maxdep mean / median / p90 / max | dive duration mean / max |
|---|---|---|---|
| NRKW | 1506 | 16.0 / 4.2 / 33.9 / 271.9 m | 66.3 s / 524.2 s |
| SRKW | 221 | 20.9 / 3.7 / 68.3 / 198.4 m | 97.6 s / 511.2 s |

Honest caveats: (1) the dominant heave frequency varies by segment/behavior — the
per-segment value should come from `dsf()` over a dive, not a constant; measured fundamentals
here sit ≈0.20–0.34 Hz, somewhat **lower** than the 0.4–0.6 Hz cruising figure assumed in
the OG-R doc, so the driver should read the measured `fpk`, not the assumption. (2) median
dive depth is shallow (~4 m) with a long deep tail — most dives are shallow, foraging dives
reach tens-to-~150 m; report distributions, not just maxima.

---

## Citations (URLs / DOIs + license)
- Tennessen et al. 2024, Zenodo data, DOI 10.5281/zenodo.13308835 — **CC-BY-4.0**.
  Associated article: Global Change Biology (2024). Provider: NOAA NWFSC + DFO.
- Wright et al. 2017, Movement Ecology 5:3, DOI 10.1186/s40462-017-0094-0 — article **CC-BY-4.0**.
- Bubble-net humpback, Dryad DOI 10.5061/dryad.m0cfxppbj — **CC0-1.0**.
- Durban & Pitman 2012, Biology Letters, DOI 10.1098/rsbl.2011.0875 — (journal; data by request).
- Andrews, Pitman & Ballance 2008, Polar Biology, DOI 10.1007/s00300-008-0487-z — (journal).
- Mul et al., herring-feeding orca, Marine Mammal Science, DOI 10.1111/mms.12931 — (paywalled).
- NWFSC InPort DTAGs SRKW: https://www.fisheries.noaa.gov/inport/item/17972 — agency-gated.
- tagtools / animaltags: https://animaltags.org , https://github.com/animaltags/tagtools_data
  (repo has no data license).
