#!/usr/bin/env python3
"""Bake the REAL orca driver fixture from the open Tennessen et al. 2024 SRKW DTAG.

Source: `data/tennessen2024_srkw_dtag/oo14_264mprh50.mat` (Southern Resident killer
whale, calibrated PRH @ 50 Hz, ~136.5 min), Zenodo 10.5281/zenodo.13308835,
**CC-BY-4.0**. This is REAL, openly-licensed killer-whale biologging data.

This produces the orca twin's DRIVER track: `simulated: false`, `species: orca`,
`ecotype: SRKW`, `role: driver`. It reuses `prebake.bake_mat` (the new .mat reader)
so the bin/JSON format/version matches the dev track and the humpback contrast
exactly. The fluke beat uses the CORRECTED orca band (~0.15-0.6 Hz, measured
fundamental ~0.2-0.35 Hz), not the old 0.4-0.6 Hz assumption.

HONESTY: modeled orca motion, parameterized from / driven by cited open killer-whale
DTAG data (Tennessen et al. 2024, CC-BY-4.0), identified only by deployment code,
sex, and population in the source. This is the orca driver; the humpback mn09_203a
artifact is contrast only. Never present one species' motion as the other.

Writes under dev/ only. Decimates to keep the artifact lean; if the .bin exceeds
~1.5 MB it is box-bound (gitignored) and only the manifest+stats are committed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prebake import ORCA_STROKE_BAND_HZ, FORMAT_NAME, FORMAT_VERSION, bake_mat, write_track  # noqa: E402

LANE_DIR = Path(__file__).resolve().parents[1]
MAT_PATH = LANE_DIR / "data" / "tennessen2024_srkw_dtag" / "oo14_264mprh50.mat"
DEPLOYMENT = "oo14_264m"
OUT_RATE_HZ = 25.0
SIZE_BUDGET_BYTES = 1_500_000


def main() -> int:
    if not MAT_PATH.exists():
        print(f"error: orca .mat not found: {MAT_PATH}", file=sys.stderr)
        return 2

    track, stats = bake_mat(
        MAT_PATH,
        out_rate_hz=OUT_RATE_HZ,
        declination_deg=0.0,
        stroke_band=ORCA_STROKE_BAND_HZ,
        simulated_override=False,
    )
    track.provenance = (
        "REAL Southern Resident killer whale (Orcinus orca, SRKW) DTAG deployment "
        f"{DEPLOYMENT!r} from Tennessen et al. 2024, Zenodo 10.5281/zenodo.13308835, "
        "CC-BY-4.0. Baked from oo14_264mprh50.mat by dev/bake_orca_srkw_driver.py via "
        "prebake.bake_mat. Modeled orca motion parameterized from / driven by this open "
        "data; identified only by deployment code/sex/population in the source. This is "
        "the orca DRIVER; humpback mn09_203a is contrast only and never drives the twin."
    )

    out_dir = Path(__file__).resolve().parent
    base = "orca_srkw_oo14_driver"
    bin_path = out_dir / f"{base}.bin"
    manifest_path = out_dir / f"{base}.json"
    manifest = write_track(track, bin_path, manifest_path)

    manifest["species"] = "orca"
    manifest["ecotype"] = "SRKW"
    manifest["role"] = "driver"
    manifest["deployment"] = DEPLOYMENT
    manifest["stroke_band_hz"] = list(ORCA_STROKE_BAND_HZ)
    manifest["license"] = "CC-BY-4.0"
    manifest["dataset_doi"] = "10.5281/zenodo.13308835"
    manifest["citation"] = "Tennessen et al. 2024 (NOAA NWFSC / DFO), CC-BY-4.0"
    manifest["driver_stats"] = stats
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    size = bin_path.stat().st_size
    box_bound = size > SIZE_BUDGET_BYTES
    dsf = stats["fluke_dsf"]
    print(
        f"baked {bin_path.name} ({size} bytes) | species=orca ecotype=SRKW role=driver "
        f"simulated={manifest['simulated']} n_samples={manifest['n_samples']} "
        f"rate={manifest['sample_rate_hz']}Hz"
    )
    print(
        f"depth range (m): {stats['depth_range_m']} | roll p95={stats['roll_abs_p95_deg']} deg "
        f"pitch p95={stats['pitch_abs_p95_deg']} deg | fluke dsf median={dsf.get('median_hz')} Hz "
        f"(IQR {dsf.get('p25_hz')}-{dsf.get('p75_hz')})"
    )
    print(
        f"SIZE BUDGET {SIZE_BUDGET_BYTES} bytes -> "
        + (
            "BOX-BOUND: gitignore the .bin, commit manifest+stats only."
            if box_bound
            else "OK: small enough to commit the .bin."
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
