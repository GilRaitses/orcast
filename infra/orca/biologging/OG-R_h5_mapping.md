# OG-R: Biologging H5 Schema, Parse Decision, and Channel to DOF Mapping

Wave: OG-R (research, read-only) for the ORCA biologging twin program.
Status: research output. This file proposes a parse approach and a sensor-to-rig
mapping. It does not change any web code and does not commit anything.

This document answers three questions for the sub-orchestrator and O0.

1. What is the standard biologging tag H5 schema and how do we read it.
2. How do we parse it for this repo (h5wasm in the browser versus a Python pre-bake), with cost and fallback.
3. How do sensor channels map onto the orca rig DOFs defined in `docs/orca/SKELETON.md`.

Honesty is stated up front and repeated where it matters. The orca is a modeled
animal driven by simulated or partnership-gated telemetry. It is not a measured
swim of a named individual unless a real agreement-covered H5 is loaded.

---

## 1. The standard biologging tag data layout (animaltags / tagtools)

The marine-mammal biologging community standard is the **animaltags / tagtools**
toolbox (R, MATLAB, Octave, Python). Its archive and exchange format is
**NetCDF (.nc)**, which since NetCDF-4 is built on **HDF5**. A NetCDF-4 file is a
valid HDF5 file, and the `.h5` extension is used in some contexts for the same
container, so an operator export labeled H5 and an animaltags `.nc` are the same
underlying HDF5 data model for our purposes.

Sources:

- animaltags, "Technical Explanation: Converting Tag Data into a NetCDF Archive": https://animaltags.org/biologging-tools-project/metrics-computation/technicals/technical-explanation-converting-tag-data-into-a-netcdf-archive/
- animaltags, "Convert .mat Files into .nc Files": https://animaltags.org/biologging-tools-project/metrics-computation/beginning-tutorials/convert-mat-file-into-nc-file/
- animaltags, "DTAG 4: Preparing Metadata": https://animaltags.org/biologging-tools-project/data-preparation/dtag-4/dtag-4-preparing-metadata/
- tagtools `sens_struct` reference: https://rdrr.io/cran/tagtools/man/sens_struct.html
- tagtools `dsf` reference: https://animaltags.github.io/tagtools_r/reference/dsf.html
- animaltags, "Complementary Filter and Applications in Animal Movement": https://animaltags.org/biologging-tools-project/metrics-computation/beginning-tutorials/comp_filt/
- Library of Congress, NetCDF-4 format description (NetCDF-4 is HDF5): https://www.loc.gov/preservation/digital/formats/fdd/fdd000332.shtml

### 1.1 File structure

An animaltags NC/H5 file contains one general metadata structure plus one or more
**sensor structures**. Each sensor structure is a self-describing package holding
the raw channel data plus that channel's own metadata. The structures are created
with `sens_struct()` and written with `save_nc()`, read back with `load_nc()`.

A typical deployment is saved as a set of sensor structures alongside an `info`
metadata structure, for example `save_nc(ncname, info, P, A, M, Aa, Ma)`.

### 1.2 The core channels

| Channel | tagtools name | Meaning | Frame | Typical unit |
| --- | --- | --- | --- | --- |
| Pressure | `P` (`p`) | hydrostatic pressure converted to depth | scalar, world vertical | depth in metres, positive down |
| Accelerometer (tag frame) | `A` | tri-axial specific plus gravitational acceleration as the tag sits on the body | tag frame | g or m per s squared |
| Magnetometer (tag frame) | `M` | tri-axial magnetic field | tag frame | microtesla |
| Accelerometer (animal frame) | `Aw` or `Aa` | accelerometer rotated into the whale body frame using the orientation table (OTAB) | animal frame | g or m per s squared |
| Magnetometer (animal frame) | `Mw` or `Ma` | magnetometer rotated into the whale body frame | animal frame | microtesla |

The animal-frame conversion uses the OTAB (orientation table) stored inside the
`Aa` and `Ma` sensor structures. The animaltags DTAG tutorial is explicit that it
is important to save the OTAB in those structures, because it is what lets a reader
move from tag frame to whale body frame.

### 1.3 Derived orientation is computed, not stored

Pitch, roll, and heading are **not stored** in the NC/H5 file. The animaltags
tutorial states this directly and shows that they are computed after loading from
the animal-frame channels.

```
[pitch, roll] = a2pr(Aa.data)   # pitch and roll from animal-frame accelerometer
head          = m2h(Ma, Aa)     # heading from animal-frame magnetometer plus accel
```

`a2pr` and `m2h` return angles in **radians** in tagtools. Heading from `m2h` is
referenced to magnetic north and needs a declination correction to become true
(geographic) heading.

This matters for us: an operator H5 will usually give us `Aw`/`Mw`/`p` plus
metadata, and we either compute pitch, roll, and heading ourselves with the
`a2pr` / `m2h` equivalents, or the operator hands us a derived product that already
contains them. The in-repo BigQuery schema (see section 5) already has explicit
`pitch`, `roll`, `heading` columns, so the project's internal contract is the
derived-angle product, not raw `Aw`/`Mw`.

### 1.4 Per-channel sampling rate and alignment

Each sensor structure carries its **own sampling rate** as metadata (the `fs`
argument to `sens_struct`). Channels are commonly at different rates. For DTAG
orca work specifically, Wright et al. 2017 (Movement Ecology, fish-eating killer
whales) report DTAGs recording depth and tri-axial accel plus magnetometer at
**50 Hz (2009 to 2011) or 250 Hz (2012)**, with sensor data **downsampled to 5 Hz**
during tag calibration. Audio is recorded at a much higher rate than the movement
sensors. So a reader must treat each channel as an independent time series with its
own rate and **resample or interpolate onto a common time base** before combining
channels. We never assume the channels are already on the same clock or rate.

Source for the orca DTAG rates: Wright et al. 2017, "Fine-scale foraging movements
by fish-eating killer whales relate to the vertical distributions and escape
responses of salmonid prey": https://link.springer.com/article/10.1186/s40462-017-0094-0

### 1.5 Fluke-stroke extraction (the convention we will use)

Whales generate thrust by moving the posterior body and flukes **dorso-ventrally**
(Wright et al. 2017, and refs therein). This produces two signatures in the
accelerometer:

1. A cyclic pitching rotation that shows up most clearly in the **longitudinal**
   axis of the accelerometer and magnetometer.
2. **Specific acceleration** from the propulsion itself, which shows up most clearly
   in the **dorso-ventral (heave, Az)** axis and is only seen by the accelerometer,
   not the magnetometer.

The tagtools convention for extracting stroke rate is `dsf()` (dominant stroke
frequency): it computes the power spectrum of each accelerometer axis, sums the
three axes, and returns `fpk`, the peak frequency, plus a quality metric `q`. It
runs over an interval where propulsion is the main activity (a complete dive), and
it low-pass filters first (default cut-off 2.5 Hz) so high-frequency foraging
transients do not dominate.

To isolate the stroke oscillation for driving a fluke beat (as opposed to only
measuring its rate), the complementary-filter tutorial splits acceleration into
three bands. The procedure we adopt:

- Remove the low-frequency **orientation / gravity** component (the static accel,
  below roughly 0.1 to 0.2 Hz). This is the same content that feeds pitch and roll,
  so it must be subtracted before reading stroke.
- Keep the **mid-frequency** band, which is the stroke. The tutorial sets the upper
  cut-off `fc2` to about twice the stroke rate.
- Drop the **high-frequency** band (rapid muscle movement, unsteady flow, strikes).

Orca-appropriate band: orca are mid-sized odontocetes, so their dominant stroke
frequency sits above the roughly 0.1 to 0.5 Hz band quoted for large baleen whales.
A practical bandpass for orca is **about 0.3 to 1.0 Hz**, with cruising strokes
clustering near 0.4 to 0.6 Hz. The exact value per segment is whatever `dsf()`
returns as `fpk` on that segment, not a hard-coded constant. As a sanity anchor,
`dsf()` on the bundled tagtools harbor-seal example returns about 1.22 Hz for that
smaller animal, which is consistent with orca sitting somewhat lower.

So the driver logic is: take the animal-frame Az (heave) channel, subtract the
static/orientation component, bandpass to the orca stroke band, and read off the
instantaneous **stroke phase** (the phase of the oscillation) and **amplitude**
(the envelope of the oscillation, related to dynamic body acceleration, DBA). Phase
and amplitude are what we feed to the rig fluke beat.

---

## 2. The H5 parse decision (costed, returned to the orchestrator and O0)

The repo is a Next.js plus react-three-fiber app on `three@0.169` with an existing
glb / meshopt fetch path and **no current HDF5 dependency**. The H5 is the
operator's export and is not in the repo. Given that, the two options:

### Option A: parse H5 in the browser with h5wasm

`h5wasm` (usnistgov) is a WebAssembly build of the HDF5 C library that reads (and
writes) HDF5 from JavaScript, exposing datasets as native typed arrays (for example
4-byte float to `Float32Array`). It is zero npm-dependency and is what the H5Web
NeXus viewer uses.

- npm: https://registry.npmjs.org/h5wasm
- repo: https://github.com/usnistgov/h5wasm

Cost:

- **New runtime dependency** and a WASM binary. The HDF5 library is a large
  monolithic binary: the bundled ESM is about **3.2 to 3.3 MB** (the maintainer
  confirms it is not tree-shakable, since it is basically one big binary, and notes
  the h5py Windows DLL is the same 3.3 MB). The published package unpacks to roughly
  14 MB total.
- **Async init**: the WASM module must be fetched and instantiated before any read,
  so the loader is async and needs a ready gate.
- **License must be verified before adoption**: npm reports the license as
  "SEE LICENSE IN LICENSE.txt" and GitHub classifies it as "Other". The underlying
  HDF5 library uses a BSD-style license, but O0 must confirm the actual `LICENSE.txt`
  terms in the pinned version before this ships. This is a hard gate, not a footnote.
- Bundle impact lands on every user even though only an operator with a real H5 would
  ever use it.

Benefit: an end user could drop a real `.nc` / `.h5` into the browser and drive the
twin live, with no offline step.

Fallback if rejected: Option B.

### Option B: Python pre-bake (h5py / tagtools), web loads plain artifacts

An offline or CI step uses **h5py** (or the tagtools tooling) to open the H5, pull
the channels, do the channel alignment and the pitch/roll/heading derivation, and
emit a compact artifact:

- a **`Float32Array` binary** (`.bin`) for the per-sample channels, plus
- a small **JSON manifest** describing channels, units, frames, sampling rate, time
  base, and honesty flags.

The web loads these with a plain `fetch`, the same pattern already used for glb and
meshopt assets. **No new web dependency.**

Cost:

- An offline / CI build step and a **stored artifact** that has to be produced and
  versioned.
- It is **not live-loadable** by an end user dropping an H5 in the browser. New data
  requires re-running the bake.

Benefit: zero web bundle cost, no new runtime license to clear for the client, the
heavy HDF5 read stays on a controlled machine, and the artifact format is small and
cache-friendly. It also keeps the partnership-gated raw data off the public client.

### Recommendation

**Recommend Option B (Python pre-bake) for this repo, with Option A held as the
costed upgrade path.**

Rationale, stated plainly:

- The repo has no HDF5 dependency today and a deliberate fetch-the-artifact pattern.
  Adding a 3.2 to 3.3 MB non-tree-shakable WASM binary to the client bundle is a real
  cost that lands on every visitor for a feature only an operator would trigger.
- The H5 is partnership-gated and not in the repo. There is no end-user "drop your
  H5 here" use case until a data-sharing agreement exists, so Option A's main benefit
  (live in-browser load) has no audience yet.
- Option B keeps gated raw data off the public client and produces an artifact in the
  exact shape the web already consumes.

This is a **costed recommendation to O0, not a default**. If and when O0 wants a live
"operator drops a real H5 in the browser" experience, Option A is the upgrade, and at
that point O0 must clear the h5wasm `LICENSE.txt` and accept the bundle and async-init
cost. Until then, bake offline.

---

## 3. The channel to DOF mapping (locked, physical)

This targets exactly the DOF names and API in `docs/orca/SKELETON.md` as defined by
the sibling OR wave: `body_yaw`, `body_pitch`, `body_roll`, a `caudal[]` oscillation
chain driven by `setFluke(phase, amplitude)`, plus `pectoral_L/R` and `jaw`, with the
typed API `setOrientation(pitch, roll, yaw)`, `setFluke(phase, amplitude)`,
`setDepthPose(...)`, `setPectoral(...)`.

| Sensor channel | Rig DOF | Units, frame, sign, and notes |
| --- | --- | --- |
| `heading` | `body_yaw` | World heading-follow. Tag heading is referenced to **magnetic** north in the NED convention (0 at North, increasing clockwise toward East). Apply magnetic declination to get true heading, then convert to scene yaw about **+Y**. tagtools `m2h` returns **radians**; the in-repo schema stores **degrees**, so convert degrees to radians before calling `setOrientation`. Map true heading angle to a rotation about scene +Y so the body nose points along the heading direction. |
| `pitch` | `body_pitch` | Nose up or down. tagtools `a2pr` convention: **positive pitch is nose-up**. Radians from `a2pr`, degrees in the in-repo schema, convert as needed. Sign into the rig must be verified against `SKELETON.md` body_pitch sign (reconciliation note below). |
| `roll` | `body_roll` | Bank into turns. tagtools `a2pr` convention: roll is rotation about the longitudinal axis. Radians from `a2pr`, degrees in-repo. Note orca foraging dives include sustained near-90-degree rolls, so the rig must accept the full roll range, not a small-angle approximation. Sign into the rig must be verified against `SKELETON.md`. |
| `depth` (from pressure `p`) | world Y on twin datum (vertical position) | Depth is metres **positive down**. The twin datum is NAVD88 0 m equals scene Y 0 (see W2.6 datum dispatch and `infra/3dtwin`). Vertical placement is `Y = -depth * worldUnitsPerMeter`, so the animal sits below the datum. `worldUnitsPerMeter` is about **0.003** in this scene, but the driver must read the **live fit value** (`DEFAULT_WORLD_UNITS_PER_METER` in `web/lib/scene/decor/horizonRing.ts`, or the per-fit value the journey and Salish scenes attach) rather than hard-coding it. This drives the dive trajectory. |
| accelerometer **Az** oscillation | fluke beat `setFluke(phase, amplitude)` | Take the animal-frame **dorso-ventral (heave, Az)** accelerometer channel, subtract the static gravity/orientation component, and bandpass to the orca stroke band (about 0.3 to 1.0 Hz, with `dsf().fpk` giving the per-segment dominant rate). Feed the instantaneous oscillation **phase** to `setFluke` phase and the oscillation **amplitude / DBA envelope** to `setFluke` amplitude. The rig fluke beat is **dorso-ventral** through the `caudal[]` chain, which matches the physical dorso-ventral propulsion of cetaceans. |
| dive / foraging context | optional behavior tint or `speed` | Honest and labeled. `behavior_type`, `dive_phase`, `foraging_indicator`, and `speed` from the schema can tint the twin (for example a foraging label, or scaling apparent effort with speed). This is presentation context, not a measured DOF, and must be labeled as such. Orca cruising speed is roughly 2.1 to 2.7 m per s per Wright et al. 2017, useful as a plausibility bound. |

### 3.1 Frame conversion (tag NED to three.js scene)

- Tag and tagtools orientation are in **NED** (north-east-down): x to North, y to
  East, z Down, angles in radians, heading referenced to magnetic north.
- The three.js scene is **up = +Y**, with yaw taken about +Y and a defined forward
  axis. Down in NED maps to negative scene Y (which is why depth uses `-depth`).
- Conversion steps:
  1. Correct heading for magnetic declination to get true heading.
  2. Convert any degree-valued inputs (the in-repo schema is in degrees) to radians.
  3. Map true heading to a yaw rotation about scene +Y.
  4. Map pitch and roll into the rig body axes, verifying sign against `SKELETON.md`.
  5. Place the body vertically at `Y = -depth * worldUnitsPerMeter`.

### 3.2 Sample-rate alignment

Channels arrive at different rates (depth, accel, magnetometer can each differ, and
the orca DTAG baseline is 50 or 250 Hz raw, 5 Hz calibrated). The driver builds a
single time base and **interpolates each channel to the render frame time**, so the
animation is **frame-rate independent**. Orientation channels use linear or slerp
interpolation as appropriate. The fluke beat is driven by the continuous extracted
phase, so it stays smooth between samples regardless of frame rate.

### 3.3 How depth, pitch, and heading combine into the swim trajectory

- **Vertical**: depth gives world Y directly (`Y = -depth * worldUnitsPerMeter`).
- **Attitude**: pitch, roll, heading give the body orientation via
  `setOrientation(pitch, roll, yaw)`.
- **Horizontal track**: the channels do **not** contain an absolute horizontal
  world position. In the source science it is reconstructed by **dead-reckoning**
  (the WHOI `ptrack` approach: estimate swim speed from pitch and rate of change of
  depth, combine with heading to step horizontal position), then georeferenced to
  GPS surfacing fixes. For the twin, horizontal motion is therefore either
  dead-reckoned from speed plus heading plus pitch, or supplied as a synthesized
  plausible track. Either way it must be labeled as reconstructed, not measured GPS.

---

## 4. Reconciliation notes for `docs/orca/SKELETON.md` (sibling OR wave)

These are flagged so the two docs can be made consistent.

1. **Vertical position versus dive pose.** My mapping needs an explicit setter for
   the animal's **vertical world position** (`Y = -depth * worldUnitsPerMeter`). The
   listed `setDepthPose(...)` is ambiguous about whether it sets a vertical world
   position or only a diving body posture (for example arching for descent). Request:
   `SKELETON.md` should state clearly either that `setDepthPose` takes a depth in
   metres and is responsible for vertical placement on the twin datum, or that there
   is a separate vertical-position input and `setDepthPose` is posture only. If the
   latter, a `setDepth(meters)` or equivalent vertical-position setter is the missing
   DOF/setter.

2. **Angle units.** tagtools `a2pr` / `m2h` return **radians**; the in-repo BigQuery
   schema stores **degrees**. `setOrientation` should declare its unit (three.js is
   radians). The driver converts, but `SKELETON.md` should pin the API unit so the
   conversion lives in exactly one place.

3. **Sign conventions.** body_pitch and body_roll signs in `SKELETON.md` should be
   stated explicitly (positive pitch = nose up, positive roll = which side down) so
   the tag-to-rig sign mapping is unambiguous and not guessed.

4. **Roll range.** Orca foraging includes near-90-degree rolls, so body_roll must
   support the full range, not a small-angle clamp.

---

## 5. Honesty framing (locked)

- The orca is a **modeled** animal. Its motion is driven by **simulated or
  partnership-gated** biologging telemetry. It is **not** a measured swim of a named
  individual unless a real, agreement-covered H5 is loaded.
- The in-repo dtag fixture `cascadia_2010_k33_test` (`data/dtag_analysis_results.json`)
  is **simulated** (`simulated: true`, methodology "TagTools-inspired") and is the
  **development fixture only**. The read API in `src/aws_backend/routers/dtag.py`
  surfaces this honestly: `partnership_gated: true`, the bundled example is flagged
  `simulated: true`, and the feeding classifier reports `model_state: not_trained`
  with a uniform-probability caveat.
- Real Cascadia / NOAA DTAG data is **partnership-gated** and requires a data-sharing
  agreement before any real per-sample H5 can be loaded.
- The fixture is **aggregated dive analysis, not a per-sample time series.** It
  contains `dive_events` with `max_depth`, `descent_rate`, `ascent_rate`, `duration`,
  `bottom_time`, `mean_dba`, and `foraging_indicators`, plus `surface_analysis` and an
  `energetic_model`. It reports `total_samples: 36000` over `duration_hours: 0.2`,
  which implies a roughly **50 Hz per-sample stream existed upstream** (36000 / (0.2 *
  3600) = 50), but that per-sample stream is **not in this JSON**. So the fixture
  alone cannot drive a per-sample orientation or a per-sample Az fluke beat.

---

## 6. Data-access decisions needing O0 sign-off

1. **Real H5 partnership gate.** A real per-sample orca H5 (Cascadia / NOAA DTAG)
   requires a data-sharing agreement. O0 owns the decision to pursue that agreement.
   Until it exists, the twin runs on the fixture or on synthesized data and must be
   labeled modeled / simulated.

2. **Aggregated-fixture limitation and the dev driver.** Because the in-repo fixture
   is aggregated dive analysis and has no per-sample channels, the development driver
   needs a **synthesized plausible per-sample track** to move at all. The honest
   approach: build a depth track from the aggregated dive events
   (`max_depth`, `descent_rate`, `ascent_rate`, `duration`, `bottom_time`) shaped into
   a descent / bottom / ascent profile per dive and stitched with the surface periods,
   then derive a plausible pitch from the depth rate and a synthetic Az oscillation in
   the orca stroke band so the fluke beats. This synthesized track must be labeled
   simulated, and it is a **data-access / honesty decision for O0** whether the dev
   build ships with this synthesis or waits for a real per-sample H5. Recommendation:
   allow the labeled synthesis for development so the rig and mapping can be exercised,
   and keep it clearly marked simulated until a real H5 is available.

3. **h5wasm license clearance (only if Option A is ever chosen).** If O0 later chooses
   the in-browser h5wasm path, the actual `LICENSE.txt` of the pinned h5wasm version
   must be reviewed and accepted before it ships, along with the 3.2 to 3.3 MB bundle
   cost. Under the recommended Option B this gate does not apply.
