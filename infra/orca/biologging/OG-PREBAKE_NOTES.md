# OG-PREBAKE notes: baking biologging H5 into a rig-DOF motion artifact

Wave: OG-PREBAKE (Wave-0 build lane). Status: build output. This lane is the
ratified **Option B** path from
`.cca/catalogue/O0/20260628_orca-biologging-twin/SIGN_OFF.md`: an OFFLINE Python
pre-bake (no new web runtime dependency). It opens an animaltags / tagtools HDF5
biologging file, derives the per-sample motion channels, maps them onto the orca
rig DOFs in `docs/orca/SKELETON.md`, and writes a compact `Float32` `.bin` plus a
JSON manifest that the later OG-BUILD web driver reads with a plain `fetch`.

The channel-to-DOF mapping and sign conventions are taken verbatim from
`infra/orca/biologging/OG-R_h5_mapping.md` section 3 and `docs/orca/SKELETON.md`
sections 3 to 5.

## Honesty (hard line)

The orca is a **modeled** animal driven by **simulated or partnership-gated**
telemetry. It is **not** a measured swim of a named individual unless a real,
agreement-covered H5 is loaded.

- The committed dev fixture `dev/orca_dev_track.bin` / `dev/orca_dev_track.json`
  is **simulated** (`"simulated": true`) and is a **synthesized dev fixture, NOT a
  measured swim**. Its provenance string and `notes[]` say so explicitly.
- `prebake.py` propagates the source's `simulated` attribute into the manifest. For
  a real, agreement-covered H5 you must pass `--mark-measured` to assert
  `simulated: false`, and only then if the data truly is measured. The default for
  an H5 with no `simulated` attribute is conservative: it stays whatever the file
  declares, and the CLI flags make the choice explicit and auditable.
- Real Cascadia / NOAA SRKW DTAG data is partnership-gated (SIGN_OFF.md decision 4)
  and outside O0 authority. Development proceeds on the labeled simulated track.

## Files in this lane

| File | What it is |
|---|---|
| `prebake.py` | Offline baker. Reads an animaltags/tagtools H5, derives channels, writes `.bin` + `.json`. Also holds the shared format constants and `write_track()` writer. |
| `requirements.txt` | Pinned offline deps (`numpy`, `h5py`). OFFLINE/CI only; never imported by `web/`. |
| `dev/make_dev_track.py` | Synthesizes the labeled SIMULATED per-sample dev track from the aggregated in-repo fixture, using the SAME `write_track()` writer so the format is byte-identical. numpy only. |
| `dev/orca_dev_track.bin` | The synthesized dev fixture (1,008,000 bytes = 36000 samples x 7 channels x 4 bytes). |
| `dev/orca_dev_track.json` | The dev fixture manifest (`simulated: true`). |
| `dev/bake_humpback_contrast.py` | Bakes the operator's REAL humpback H5 (`mn09_203a`) as a labeled `simulated: false`, `species: humpback`, `role: contrast` artifact, reusing `prebake.py`'s writer/DSP/format. Validates the baker on real per-sample data and emits the contrast baseline. |
| `dev/humpback_mn09_203a_contrast.bin` | Baked REAL humpback contrast track (2,797,900 bytes = 99925 samples x 7 channels x 4 bytes). NOT an orca driver. |
| `dev/humpback_mn09_203a_contrast.json` | Humpback contrast manifest (`simulated: false`, `species: humpback`, `role: contrast`, with a `contrast_baseline` block). |
| `dev/bake_orca_srkw_driver.py` | Bakes the REAL orca DRIVER fixture from the CC-BY Tennessen 2024 SRKW `.mat` via `prebake.bake_mat`. `simulated: false`, `species: orca`, `ecotype: SRKW`, `role: driver`. |
| `dev/orca_srkw_oo14_driver.json` | Orca driver manifest + `driver_stats` (depth/roll/pitch envelopes, per-segment fluke dsf). Committed. |
| `dev/orca_srkw_oo14_driver.bin` | Orca driver track (~5.7 MB @ 25 Hz). **Box-bound (gitignored)**; reproducible from the `.mat` via the baker. |
| `dev/.gitignore` | Box-binds the >1.5 MB orca driver `.bin`. |
| `OG-R_h5_mapping.md` | The OG-R research input (schema, parse decision, mapping). Read-only here. |

## How to bake a real H5 later

1. Create an isolated environment and install the pinned offline deps (a CPython
   with prebuilt wheels for these versions, e.g. 3.10 to 3.12):

```bash
python3.12 -m venv .venv
./.venv/bin/python -m pip install -r infra/orca/biologging/requirements.txt
```

2. Run the baker on the deployment file. A NetCDF-4 `.nc` is a valid HDF5 file, so
   both `.h5` and `.nc` work. MATLAB v7.3 `.mat` files are also HDF5 and readable by
   `h5py`; older v7 `.mat` are not HDF5 and must be re-exported (animaltags
   `save_nc`) first.

```bash
./.venv/bin/python infra/orca/biologging/prebake.py path/to/deployment.nc \
  --out-dir web/public/orca/motion \
  --name <deployment_id> \
  --rate 25 \
  --declination <deg_for_site> \
  --mark-measured        # ONLY if this is real, agreement-covered data
```

3. What the baker expects in the H5 (animaltags / tagtools layout):
   - A pressure/depth channel `P` (or `p`/`depth`).
   - Animal-frame accelerometer `Aa`/`Aw` (falls back to tag-frame `A`). Used for
     `a2pr` pitch/roll and for the dorso-ventral (`Az`) fluke beat.
   - Animal-frame magnetometer `Ma`/`Mw` (falls back to `M`). Used for `m2h`
     heading. If absent, heading is set to 0 and a note records it.
   - Each sensor struct carries its own sampling rate as an `fs` / `sampling_rate`
     attribute (channels commonly differ; the baker resamples each onto one time
     base via `--rate`).
   - If the file already carries a derived `pitch` / `roll` / `heading` product (the
     in-repo BigQuery contract, OG-R section 1.3), those are used directly; degrees
     are auto-detected by range and converted to radians.
   - An optional `simulated` / `is_simulated` file attribute is propagated to the
     manifest (overridable with `--mark-simulated` / `--mark-measured`).

4. `prebake.py` does the tagtools-equivalent derivation (`a2pr` for pitch/roll,
   `m2h` for tilt-compensated magnetic heading, plus magnetic declination for true
   heading), extracts the fluke beat (band-pass the `Az` heave to the orca stroke
   band, then read instantaneous phase and a normalized envelope via a numpy FFT
   Hilbert), resamples everything to `--rate`, and writes the `.bin` + `.json`.

5. The web driver then loads the new `.bin` / `.json` the same way it loads the dev
   fixture. No web code change is needed for new data; just re-run the bake.

## To regenerate the dev fixture

```bash
./.venv/bin/python infra/orca/biologging/dev/make_dev_track.py
```

Deterministic (seed `20260628`); rewrites `dev/orca_dev_track.bin` + `.json`
byte-for-byte.

## Bin + JSON format spec (the web loader contract)

### Binary (`.bin`)

- **Encoding**: little-endian IEEE-754 `float32`.
- **Layout**: sample-major (interleaved), i.e. a row-major `(n_samples,
  n_channels)` matrix. For sample `i` the values are
  `[c0_i, c1_i, ... c6_i]` contiguously, then sample `i+1`, and so on.
- **Size**: `n_samples * n_channels * 4` bytes. `n_channels` is currently 7.
- **No header** in the `.bin`; all shape/units/order live in the JSON manifest.
- All values are guaranteed finite (the writer rejects NaN/Inf).

Web loader sketch:

```js
const meta = await (await fetch("orca_dev_track.json")).json();
const buf  = await (await fetch(meta.bin_file)).arrayBuffer();
const data = new Float32Array(buf); // length === n_samples * n_channels
// value for sample i, channel j:  data[i * meta.n_channels + j]
// channel j name/units/DOF:       meta.channels[j]
```

### Manifest (`.json`)

| Key | Meaning |
|---|---|
| `format`, `format_version` | `orca-biologging-prebake`, version `1`. |
| `simulated` | **Honesty flag.** `true` for the dev fixture / simulated data. |
| `provenance` | Plain-language statement of where the data came from. |
| `source` | Structured provenance (type, source file/fixture, seed, rates, `measured`). |
| `bin_file` | Filename of the sibling `.bin`. |
| `layout`, `dtype`, `byte_order` | Binary layout (`float32-le`, sample-major). |
| `sample_rate_hz`, `n_samples`, `n_channels`, `duration_s` | Time base. |
| `angle_units` | `radians` at the rig boundary. |
| `declination_deg_applied` | Magnetic declination added to get true heading. |
| `stroke_band_hz` | Orca stroke band used for the fluke beat (`[0.3, 1.0]`). |
| `datum` | `NAVD88-0m`; `depth_m` is positive-down metres; the web applies `Y = -depth_m * worldUnitsPerMeter` at the LIVE fit value. |
| `channels[]` | Ordered channel descriptors (name, unit, DOF, frame, sign, source). |
| `notes[]` | Honesty / limitation notes (simulated, no horizontal track, etc.). |
| `bin_bytes` | Size of the `.bin` for an integrity check. |

### Channel order and DOF mapping (the locked table)

Channel index = position in `manifest.channels[]`. Angles are **radians**; the web
maps them to the rig API in `docs/orca/SKELETON.md` section 4
(`setOrientation`, `setFluke`, `setDepthPose`).

| idx | channel | unit | rig DOF / API | sign / frame |
|---|---|---|---|---|
| 0 | `t_s` | seconds | (time base) | `t = i / sample_rate_hz` |
| 1 | `body_yaw_rad` | radians | `body_yaw` via `setOrientation` yaw | true heading (declination-corrected); web maps to yaw about scene `+Y` so the rostrum (`+X`) points along heading |
| 2 | `body_pitch_rad` | radians | `body_pitch` via `setOrientation` pitch | positive = nose-up (tagtools `a2pr`); about lateral `Z` |
| 3 | `body_roll_rad` | radians | `body_roll` via `setOrientation` roll | positive = dorsal banks toward `+Z` (port); full range, no small-angle clamp |
| 4 | `depth_m` | metres, positive-down | world `Y` via `setDepthPose` | `Y = -depth_m * worldUnitsPerMeter` at the live fit value; NAVD88-0m datum; translation, not a bone |
| 5 | `fluke_phase_rad` | radians `[0, 2*pi)` | `setFluke` phase | continuous phase of the dorso-ventral (`Az`) stroke oscillation |
| 6 | `fluke_amplitude` | normalized `0..1` | `setFluke` amplitude | envelope (DBA) of the stroke oscillation; `0` = no beat, `1` = full nominal stroke |

Notes that carry over from OG-R and SKELETON:

- The fluke beat is **dorso-ventral** (pitch-axis `Z` on the `caudal[0..5]` chain),
  never lateral, and propagates tailward with a per-joint phase delay handled by the
  rig. The baker only supplies phase + amplitude.
- Depth is a **vertical translation**, not a bone rotation. `worldUnitsPerMeter` is
  read **live** by the web (e.g. `DEFAULT_WORLD_UNITS_PER_METER` or the per-fit value
  the scene attaches), never hard-coded in the artifact.
- The artifact carries **no absolute horizontal world position**. The source science
  reconstructs it by dead-reckoning (WHOI `ptrack`: swim speed from pitch and depth
  rate, stepped by heading) then georeferenced to GPS surfacings. Any horizontal
  track in the twin must be labeled **reconstructed**, not measured GPS.

## Real orca SRKW driver (Tennessen oo14, box-bound)

The orca twin's DRIVER track, baked from the **real open** Southern Resident killer
whale DTAG `oo14_264mprh50.mat` (Tennessen et al. 2024, Zenodo 10.5281/zenodo.13308835,
**CC-BY-4.0**, 50 Hz, ~136.5 min) via `prebake.bake_mat` (new OLD-format MATLAB reader,
`scipy.io.loadmat`; `scipy` pinned in `requirements.txt`, offline only). Same
bin/JSON format/version/7 channels as the dev track and humpback contrast.

- **Manifest:** `simulated: false`, `species: orca`, `ecotype: SRKW`, `role: driver`,
  provenance = Tennessen 2024 Zenodo CC-BY-4.0. Modeled orca motion driven by this open
  data; identified only by deployment code/sex/population.
- **Lean / box-bound:** baked at **25 Hz** (decimated from 50 Hz); the `.bin` is ~5.7 MB,
  over the ~1.5 MB commit budget, so it is **gitignored** (`dev/.gitignore`) and only the
  manifest + `driver_stats` are committed. Reproduce with
  `./.venv/bin/python dev/bake_orca_srkw_driver.py`.
- **Measured on bake:** depth −2.5 to **155 m**; \|roll\| p95 **133°**, \|pitch\| p95 **62°**
  (full ±π roll present); per-segment active-window fluke **dsf median ~0.18 Hz, IQR
  ~0.15–0.29 Hz** (corrected orca band 0.15–0.6 Hz).
- **Fluke correction applied:** the orca heave fundamental is **~0.2–0.35 Hz, NOT the old
  0.4–0.6 Hz** assumption (see `OG-R_h5_mapping.md` 1.5). The driver reads the per-segment
  `dominant_stroke_freq` (active-stroking windows), never a constant. `ORCA_STROKE_BAND_HZ`
  in `prebake.py` is the corrected band.

HONESTY: the orca driver = measured SRKW (Tennessen, CC-BY); the humpback below =
operator's measured `mn09_203a`, contrast only. Never merged; one species' motion is
never presented as the other.

## Humpback contrast baseline (real mn09_203a)

This is the **real** humpback baseline for the OG-DATA orca-vs-humpback species
table. It also served as the real-H5 validation of `prebake.py`'s bin/JSON pipeline
and Az-band fluke method (the output is byte-format-identical to the orca dev track,
proving the baker works on real per-sample animaltags data).

**Honesty:** this is real **humpback** (*Megaptera novaeangliae*) data, the
operator's own deployment. It is labeled `species: humpback`, `role: contrast`,
`simulated: false`. The orca twin is **never** driven by it; humpback kinematics are
never presented as orca.

- **Source (external, read-only, not copied into orcast):**
  `/Users/gilraitses/whale-behavior-analysis/Visualization_Poster_Appendix/data/dive_analysis.h5`
- **Animal:** `mn09_203a` ("lavaliers_Calf"), 5 Hz tag, ~5.55 h (19,985 s),
  99,925 samples, **128 detected dives**.
- **Baker:** `dev/bake_humpback_contrast.py` (reads the documented H5 paths
  `/depth/values`, `/data/pitch|roll|head`, `/data/Aw.3`; reuses `prebake.write_track`
  and `prebake.stroke_phase_amplitude`). The H5 already carries a derived
  pitch/roll/heading product (radians), used directly.
- **Recovered on bake:** depth range **−0.39 to 39.19 m**; fluke beat **0.23 Hz**.
- **Output:** `dev/humpback_mn09_203a_contrast.bin` (2,797,900 bytes) +
  `dev/humpback_mn09_203a_contrast.json` (carries a full `contrast_baseline` block).

### Dive distribution over the 128 dives (real, tag-computed `/dives/metrics/*`)

| Metric | min | median | max | mean |
|---|---|---|---|---|
| max depth (m) | 6.81 | **20.85** | **39.03** | 20.65 |
| descent rate (m/s) | 0.03 | **0.47** | 1.25 | 0.52 |
| ascent rate (m/s) | 0.03 | **0.45** | 1.33 | 0.50 |
| descent duration (s) | 10.0 | 32.4 | 202.2 | 39.6 |
| bottom duration (s) | 11.6 | 30.1 | 261.4 | 45.7 |
| ascent duration (s) | 5.6 | 30.2 | 328.2 | 49.1 |
| dive duration (s) | 30.0 | **66.7** | 411.0 | 88.7 |

### Fluke-beat frequency (from the Az / `Aw.3` band)

- **Fluke beat: ~0.23 Hz** (median inter-stroke interval 4.4 s, from the tag's 2,405
  detected stroke peaks on the whale-frame accel). This is the headline contrast
  number.
- Az-band whole-record spectral peak: ~0.13 Hz — **biased low** because humpbacks
  glide intermittently (670 glide periods), so the FFT undercounts active stroking.
  The stroke-peak rate is the credible estimator and is reported as such.
- Extraction band for the baked fluke phase/amplitude channel:
  **0.12–0.6 Hz** (humpback), distinct from the orca **0.3–1.0 Hz** band. The lower
  edge excludes the slow dive-cycle/posture drift so the fluke channel carries only
  the stroke oscillation.

### Behavior mix (from the event log `log_mn09_203a.csv`, fraction of annotated time)

| Behavior | fraction |
|---|---|
| Exploratory dives | 34.9% |
| Side rolls | 21.7% |
| Noodle feeding | 18.1% |
| Kick feeding | 8.6% |
| Feeding loop | 5.7% |
| Surface Active | 5.2% |
| Traveling | 2.5% |
| Side rolls and loop | 2.4% |
| Vertical loop | 1.0% |

The mix is **feeding-dominated** (exploratory dives, side rolls, and three
bubble-net/feeding behaviors), consistent with a foraging humpback. This is the
behavioral contrast against open-data orca cruising/foraging parameters that OG-DATA
will place in the orca column.

### Contrast headline (for the OG-DATA table)

Real humpback `mn09_203a`: shallow (median max depth ~21 m, max ~39 m), slow vertical
rates (~0.45–0.47 m/s), short dives (median ~67 s), **slow fluke beat ~0.23 Hz**, and
a feeding-dominated behavior budget. The orca column comes from open orca data
(OG-DATA search); orca dives are deeper and the orca stroke band is higher
(0.3–1.0 Hz, cruising ~0.4–0.6 Hz). Never merge the two: humpback is contrast only.
