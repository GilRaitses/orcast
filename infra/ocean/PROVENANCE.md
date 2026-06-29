# Measured ocean stratification profile — provenance, license, attribution

The interpretive double-diffusion ocean layer's stratification profile is
grounded in one real CC0 CTD cast. The visualization stays interpretive. Only
the profile that places the halocline and sets band sharpness is measured. The
raw cast is a box asset and is gitignored. Only the small baked JSON plus this
record ship in-repo.

## Data asset

| Asset | Source | License | Attribution |
|-------|--------|---------|-------------|
| CruiseSalish CTD data package, full CSV | `https://www.ncei.noaa.gov/data/oceans/ncei/ocads/data/0307188/SalishCruiseDataPackage_v2025_data_09072025.csv` | CC0 1.0 Universal Public Domain Dedication | NOAA PMEL and Washington Ocean Acidification Center, via NANOOS / UW APL |

License text on the NCEI metadata page, quoted exactly:

> These data were produced by NOAA and the Washington Ocean Acidification Center
> (WOAC) and are not subject to copyright protection in the United States. NOAA
> and WOAC waive any potential copyright and related rights in these data
> worldwide through the Creative Commons Zero 1.0 Universal Public Domain
> Dedication (CC0-1.0). https://creativecommons.org/publicdomain/zero/1.0/

- NCEI Accession 0307188
- DOI `https://doi.org/10.25921/jgrz-v584`
- NCEI metadata `https://www.ncei.noaa.gov/data/oceans/ncei/ocads/metadata/0307188.html`
- NANOOS CruiseSalish portal `https://nvs.nanoos.org/CruiseSalish`

CC0 carries no obligation. The producers attach a non-binding FAIR data-use
courtesy request to credit the investigators, which the demo honors by shipping
the DOI and accession in the profile provenance and the on-screen attribution.

## Selected cast (honest nearby-analog labeling)

The demo node is the Orcasound Lab hydrophone at 48.5583 N, 123.1736 W in San
Juan Channel. The NCEI accession's northernmost station reaches latitude 48.486,
south of that node, so the accession holds no on-site San Juan Channel cast. The
nearest representative cast is in the eastern Strait of Juan de Fuca, which
shares the same estuarine halocline regime. It is labeled in the provenance as a
nearby analog, not an on-site station.

| Field | Value |
|-------|-------|
| CRUISE_ID | `BOLD085` |
| EXPOCODE | `31B520081108` (intact; many accession EXPOCODEs are Excel-corrupted to scientific notation) |
| STATION_NO | `25` |
| Cast date | 2008-08-14 (summer, sharp seasonal thermocline over the halocline) |
| Location | 48.40 N, 123.01 W, eastern Strait of Juan de Fuca, about 21 km south of the demo node |
| Depth coverage | 1.1 to 164.3 dbar, full water column |
| Acceptable T/S samples | 9 bottle-fire depths, flags 2 |
| Surface | 10.81 C, 30.47 PSU |
| Deep | 7.66 C, 33.20 PSU |

The cast is monotonic, fresher and warmer over saltier and colder, a real
estuarine halocline with a clear pycnocline between 50 and 81 m. It is not a
salt-fingering staircase, consistent with BSW-R09 on the open Salish basin.

The accession CSV records bottle-fire depths, a sparse irregular ladder. The
full 0.5 dbar continuous downcasts live on the NANOOS CruiseSalish portal and
are a later refinement. The shipped profile linearly resamples the 9 real
measured samples to 64 even depths so the baked texture width matches the
analytic path. The interpolation is a resample of real measurements, not
synthetic data.

## EXPOCODE corruption note

The accession CSV's EXPOCODE column renders several cruises as Excel scientific
notation, for example `3.25E+11`, which collapses cruises TN270, TN216, and
TN256 into one string. The bake selects by `CRUISE_ID` plus `STATION_NO`, the
reliable identifiers, and records the intact EXPOCODE only when it survives.
`BOLD085` keeps its intact EXPOCODE `31B520081108`.

## Files

| File | Role | In git? |
|------|------|---------|
| `infra/ocean/bake_ctd_profile.py` | offline bake, stdlib only, with a forbidden-claim guard check | yes |
| `infra/ocean/data/SalishCruiseDataPackage_v2025_data_09072025.csv` | raw CC0 cast package | no (box) |
| `web/lib/scene/ocean/measured_cruisesalish_profile.json` | baked 64-sample profile + provenance | yes (small) |
| `web/lib/scene/ocean/measuredProfile.ts` | dependency-free loader returning a StratificationProfile | yes |

## Reproduce

```
mkdir -p infra/ocean/data
curl -sSL "https://www.ncei.noaa.gov/data/oceans/ncei/ocads/data/0307188/SalishCruiseDataPackage_v2025_data_09072025.csv" \
  -o infra/ocean/data/SalishCruiseDataPackage_v2025_data_09072025.csv
python3 infra/ocean/bake_ctd_profile.py \
  --cast infra/ocean/data/SalishCruiseDataPackage_v2025_data_09072025.csv \
  --cruise-id BOLD085 --station-no 25
```

## Box pointer

Mirror the raw package to the box under
`s3://198456344617-us-west-2-orcast-aws-backend-reports/bsw-ocean/cruisesalish/`
and re-fetch from the public NCEI URL above (no credentials, CC0).
