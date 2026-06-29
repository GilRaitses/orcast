# Heavy biologging files -> the box (S3), not git

The raw orca DTAG datasets and the large derived motion tracks live in the AWS box
(`aimez-data` bucket), not in git. They are gitignored and reproducible. This file is
the pointer + the re-fetch / re-bake steps.

## Box location
`s3://aimez-data/orcast/orca-biologging/`

| Box object | Size | What it is | How to regenerate |
|---|---|---|---|
| `data/tennessen2024_srkw_dtag/oo14_264mprh50.mat` | 46 MB | Real SRKW orca PRH (Tennessen 2024, CC-BY-4.0) | re-fetch from Zenodo DOI 10.5281/zenodo.13308835 (see `data/tennessen2024_srkw_dtag/PROVENANCE.md`) |
| `data/tennessen2024_srkw_dtag/oo11_224bprh50.mat` | 6.7 MB | Real NRKW orca PRH (Tennessen 2024, CC-BY-4.0) | same Zenodo record |
| `dev/orca_srkw_oo14_driver.bin` | 5.5 MB | Baked REAL orca driver track, 25 Hz | `python dev/bake_orca_srkw_driver.py` after fetching `oo14` |
| `dev/humpback_mn09_203a_contrast.bin` | 2.7 MB | Baked humpback contrast track (operator `mn09_203a`) | `python prebake.py <humpback dive_analysis.h5>` (see `HUMPBACK_CONTRAST_DATA.md`) |

## Pull from the box
```bash
aws s3 sync s3://aimez-data/orcast/orca-biologging/data infra/orca/biologging/data
aws s3 sync s3://aimez-data/orcast/orca-biologging/dev  infra/orca/biologging/dev
```

## What IS committed (lean, reproducible)
- `prebake.py`, `dev/bake_orca_srkw_driver.py`, `dev/make_dev_track.py`, `requirements.txt`
- manifests/stats: `dev/orca_srkw_oo14_driver.json`, `dev/humpback_mn09_203a_contrast.json`, `dev/orca_dev_track.{bin,json}`
- provenance/license: `data/tennessen2024_srkw_dtag/{PROVENANCE.md,LICENSE.txt,foraging_data.csv}`
- docs: `OG-R_h5_mapping.md`, `OG-PREBAKE_NOTES.md`, the lane's `HUMPBACK_CONTRAST_DATA.md`

Honesty: orca driver = measured SRKW (Tennessen, CC-BY); humpback track = operator's
measured `mn09_203a`, contrast only. The orca twin is never driven by humpback motion.
