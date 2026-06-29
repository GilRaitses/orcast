# OCN-ctd-data

> OCN-R1 read-only research finding. RESEARCH ONLY. No code edited, no dataset downloaded, nothing committed.
> Authored by OCN-R1 under the OCN sub-orchestrator. License and format verified via web on 2026-06-29.

## 1. Dataset identity, DOI, accession

I confirm the dataset named in `stratification.ts` and BSW-R09 as the gated measured upgrade.

| Field | Value |
|---|---|
| Product name | SalishCruiseDataPackage_v2025 |
| Producer | NOAA PMEL and Washington Ocean Acidification Center (WOAC), via NANOOS / UW APL |
| NCEI Accession | 0307188 |
| NCEI DOI | https://doi.org/10.25921/jgrz-v584 |
| NCEI metadata page | https://www.ncei.noaa.gov/data/oceans/ncei/ocads/metadata/0307188.html |
| OCADS data package page | https://www.ncei.noaa.gov/access/ocean-carbon-acidification-data-system/oceans/SalishCruise_DataPackage.html |
| NANOOS CruiseSalish portal | https://nvs.nanoos.org/CruiseSalish |
| Temporal coverage | 2008-02-04 to 2024-10-22 |
| Scope | 61 cruise data sets, southern Salish Sea and northern California Current System |
| Profiles | 1,238 oceanographic profiles |
| Sensor sample count | 13,200 sensor measurements of temperature, salinity, and oxygen |

The 1,238 profile count from BSW-R09 is exact and matches the NCEI abstract verbatim.

Citation string from the producer:

> Alin, Simone R.; Newton, Jan; Ikeda, Christopher; Boyar, Anna; Greeley, Dana; Herndon, Julian; Curry, Beth; Kozyr, Alex; Feely, Richard A. (2025). SalishCruiseDataPackage_v2025 ... (NCEI Accession 0307188). [indicate subset used]. NOAA National Centers for Environmental Information. Dataset. https://doi.org/10.25921/jgrz-v584. Accessed [date].

## 2. License confirmation with cited text

Verdict: CC0 1.0 Universal Public Domain Dedication. Confirmed yes.

The NCEI metadata page states under DATA LICENSE, quoted exactly:

> These data were produced by NOAA and the Washington Ocean Acidification Center (WOAC) and are not subject to copyright protection in the United States. NOAA and WOAC waive any potential copyright and related rights in these data worldwide through the Creative Commons Zero 1.0 Universal Public Domain Dedication (CC0-1.0). https://creativecommons.org/publicdomain/zero/1.0/

The identical statement appears on the OCADS data package page and the OCADS data product page, so the CC0 status is consistent across all three NOAA-hosted surfaces.

One non-binding item to log honestly. The producers attach a FAIR DATA USE REQUEST asking users to credit the investigators and to notify them when the data are essential to a publication. This is a courtesy request, not a license restriction, and it does not limit redistribution under CC0. For the demo I recommend honoring it by shipping the full citation and DOI in provenance and the HUD attribution chip.

## 3. Data format and access

| Aspect | Detail |
|---|---|
| Primary file | `SalishCruiseDataPackage_v2025_data_07252025.csv` |
| Format | Plain CSV, one row per sample depth, all 61 cruises stacked and sorted by station |
| Metadata file | `SalishCruiseDataPackage_v2025_metadata_07252025.xlsx` |
| What the NCEI CSV contains | CTD upcast values at the depths where Niskin bottles fired, joined to discrete bottle chemistry. Quality flags 2 (acceptable) and 3 (questionable) retained |
| Vertical resolution of NCEI CSV | Bottle-fire depths, so coarse and irregular, not a continuous profile |
| Full-resolution 0.5 dbar downcasts | Hosted separately at the NANOOS CruiseSalish portal, not inside the NCEI accession CSV |
| Access route | NCEI "Database Files" index link on the metadata page, or the NANOOS Map/Data/Plots tabs |

Important format nuance that affects the bake. The NCEI accession CSV gives temperature, salinity, oxygen, and sigma-theta at bottle-fire depths only, which is a sparse irregular ladder down the water column rather than a smooth profile. The continuous 0.5 dbar binned downcast profiles, the source of the 0.5 dbar figure cited in BSW-R09, live at the NANOOS CruiseSalish portal. For a smooth 1D texture I want the 0.5 dbar NANOOS downcast for one station. For a quick honest two-anchor gradient the NCEI bottle-depth CSV is enough.

## 4. Variables and depth range

Column names confirmed from the NCEI metadata variable table.

| Quantity | CSV column | Unit | Notes |
|---|---|---|---|
| Pressure | `CTDPRS_DBAR` | dbar | Stands in for depth, near 1 dbar per metre |
| Temperature | `CTDTMP_ITS90_DEG_C` | deg C, ITS-90 | SBE CTD sensor |
| Practical salinity | `CTDSAL_PSS78` | PSS-78 | Calculated from conductivity |
| Sigma-theta density anomaly | `SIGMATHETA_KG_M3` | kg/m3 | Potential density anomaly referenced to 0 dbar, TEOS-10 after 2013 and EOS-80 before |
| Dissolved oxygen, adjusted | `CTDOXY_UMOL_KG_ADJ` | umol/kg | CTD sensor corrected to bottle Winkler |
| Dissolved oxygen, raw sensor | `CTD_OXY_mg_L` | mg/L | Uncorrected |
| Latitude | `LATITUDE_DEC` | deg N | |
| Longitude | `LONGITUDE_DEC` | deg E, negative west | |
| Station | `STATION` | numeric | The number after the P in PRISM station IDs |
| Time | `DATE_UTC`, `TIME_UTC`, `DATE_LOCAL`, `TIME_LOCAL` | UTC and local | |
| Bottle index | `NISKIN_NO` | count | Deepest trip is 1 |

Observed dynamic ranges from the abstract, excluding the single very deep cast:

| Quantity | Range |
|---|---|
| Temperature | 6.0 to 23.3 deg C |
| Salinity | 15.6 to 34.0 PSS-78 |
| Oxygen | 9 to 612 umol/kg |

Depth coverage runs from the seawater surface to near-bottom at each station. Puget Sound main basin stations reach roughly 200 m, Admiralty Reach is shallower, and the compilation includes one very deep cast that the abstract calls out as an outlier. These measured ranges bracket the analytic profile in `stratification.ts` of surface near 28 PSU and 13 C and deep near 31.2 PSU and 9 C, so the analytic curve is physically consistent with this dataset and a measured cast can replace it without a large visual jump.

## 5. Cast selection near the demo station

Demo stations in this repo include Orcasound Lab near 48.5583362, -123.1735774 and nearby San Juan Channel nodes.

Honest geographic caveat I must flag. The NCEI accession bounding box is north 48.493, south 47.1333, west -125.4712, east -122.2937. The Orcasound Lab demo coordinate at latitude 48.558 sits just north of the stated northern extent, so this accession most likely has no cast exactly co-located with the San Juan Channel demo node. The cruise grid concentrates on Puget Sound basins, Admiralty Reach at the sill, and the Sound-to-Sea transect through the eastern Strait of Juan de Fuca toward La Push. The nearest representative casts are therefore Admiralty Reach or eastern Strait of Juan de Fuca stations, which share the same estuarine halocline regime as San Juan Channel even though they are not the identical location. The NANOOS CruiseSalish portal may carry additional stations beyond this accession, and that is the place to look first for a closer match.

Recommended selection criteria for one representative cast, to be applied later under the operator gate and without downloading now:

1. Proximity. Pick the station with minimum great-circle distance to 48.5583362, -123.1735774. If no station reaches that latitude, take the northernmost Admiralty Reach or eastern Strait of Juan de Fuca station as the nearest analog and label it as a nearby analog rather than an on-site cast.
2. Full water column. Prefer a station whose deepest bottle or downcast bin approaches the local seabed so the halocline and the deep layer are both captured.
3. Season. Match the demo mood. A summer cruise in July or September gives the strongest surface warming and the sharpest seasonal thermocline over the halocline, which reads clearly as stratification. An April cruise gives a weaker thermocline. I recommend a July or September Puget Sound cruise for the most legible layered profile.
4. Quality. Keep only rows with temperature and salinity flags of 2, treat flag 3 as questionable, and drop anything else.
5. Single cast. Resolve to one EXPOCODE plus one STATION plus one cast time so the bake is one profile with unambiguous provenance.

Selection stays a recommendation only. No station has been chosen or downloaded in this wave.

## 6. Offline parse path and minimal dependencies

The bake runs offline on the box, not in the web runtime. Nothing here is added to the browser bundle. The web layer consumes only the baked JSON.

Because the NCEI product is plain CSV, the Python standard library `csv` module is sufficient and there is no heavy runtime dependency.

| Dependency | Needed? | Reason |
|---|---|---|
| Python stdlib `csv` | Yes | Reads the NCEI CSV with zero third-party install |
| `pandas` | Optional | Convenience for filtering by station and flag, not required |
| `netCDF4` or `xarray` | Only if a NANOOS export is netCDF | The NCEI accession is CSV, so these are not needed for it |
| `gsw` | Not for the bake | Sigma-theta is already a column, so no seawater recompute is required for a simple T and S and density bake |

Sketch of the offline parser, illustrative only and not added to the repo in this wave:

```python
import csv

TARGET_EXPOCODE = "..."   # one cruise, chosen under the gate
TARGET_STATION = "..."    # one station, chosen under the gate

samples = []
with open("SalishCruiseDataPackage_v2025_data_07252025.csv", newline="") as f:
    for row in csv.DictReader(f):
        if row["EXPOCODE"] != TARGET_EXPOCODE:
            continue
        if row["STATION"] != TARGET_STATION:
            continue
        if row["CTDTMP_FLAG_W"] not in ("2", "6"):
            continue
        if row["CTDSAL_FLAG_W"] not in ("2", "6"):
            continue
        samples.append({
            "pressure_dbar": float(row["CTDPRS_DBAR"]),
            "temp_c": float(row["CTDTMP_ITS90_DEG_C"]),
            "salinity_pss78": float(row["CTDSAL_PSS78"]),
            "sigma_theta_kg_m3": float(row["SIGMATHETA_KG_M3"]),
        })

samples.sort(key=lambda s: s["pressure_dbar"])
# Emit baked JSON plus provenance (DOI, accession, EXPOCODE, station, cast time, license).
```

For a smooth 256-step texture the parser would resample the sorted samples onto an even depth axis offline and write that array into the baked JSON. The web runtime then reads only that small JSON, so the three.js bundle gains no parsing or netCDF dependency.

## 7. What is gated

CC0 is confirmed, but no data has been downloaded in this wave. The actual download stays an O0 operator gate.

| Item | Status |
|---|---|
| License clearance | Confirmed CC0 1.0 by me via three NOAA pages. License-clear. |
| Raw cast download | GATED. Operator pulls the raw cast to the box, not into the repo. |
| In-repo artifacts | Only baked JSON plus provenance enter the repo. No raw CSV, no netCDF in-repo. |
| Code edits | None in this wave. OCN-R1 is read-only on code. |
| Commit or stage | None in this wave. |

The gate sequence for later, stated for the operator. License is clear now. Under the gate the operator downloads one chosen raw cast to the box, runs the offline parser, and commits only the baked JSON and a provenance record that carries the DOI 10.25921/jgrz-v584, accession 0307188, EXPOCODE, station, cast time, and the CC0 statement. The full FAIR DATA USE citation rides along in provenance and the HUD attribution chip.
