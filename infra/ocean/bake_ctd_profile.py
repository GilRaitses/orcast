#!/usr/bin/env python3
"""Bake one CC0 CruiseSalish CTD cast into a small StratificationProfile JSON.

Input : the raw NANOOS CruiseSalish / NCEI Accession 0307188 CSV (CC0 1.0),
        staged in the box at infra/ocean/data/ (gitignored).
Output: web/lib/scene/ocean/measured_cruisesalish_profile.json (small, in-repo).

The cast is selected by CRUISE_ID + STATION_NO, because the accession's
EXPOCODE column is corrupted for several cruises (Excel rendered numeric-looking
codes as scientific notation such as 3.25E+11, collapsing three distinct cruises
into one string). CRUISE_ID is the reliable cast identifier; the intact EXPOCODE
is recorded only when it survives the round trip.

MEASURED INPUT, INTERPRETIVE OUTPUT. The cast supplies depth, temperature, and
salinity only. The render layer that consumes this profile is interpretive, not
a map of measured microstructure and not a depiction of how an animal senses its
surroundings. stratificationToTexture normalizes salinity, temperature, and the
density-gradient channel per profile at runtime, so this JSON carries only the
raw resampled samples plus origin, provenance, and maxDepthM. The sample count
matches analyticHaloclineProfile's default of 64 so the baked texture width is
identical and the shader samples both paths the same way.

No heavy runtime dependency: Python standard library only.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

SAMPLE_COUNT = 64  # matches analyticHaloclineProfile default

# These phrases must never appear as adjacent substrings in shipped copy. The web
# layer guard (interpretiveOceanLayer.assertNoForbiddenClaim) is a plain
# case-insensitive includes(), so even a negated phrase throws at scene mount.
# This offline check fails the bake before a bad provenance can ship.
FORBIDDEN_CLAIMS = (
    "measured thermohaline",
    "biosonar perception",
    "biosonar reveals",
    "what the whale sees",
    "salt fingering observed",
)


def assert_no_forbidden_claim(text: str) -> None:
    low = text.lower()
    for phrase in FORBIDDEN_CLAIMS:
        if phrase in low:
            raise SystemExit(f"ERROR: provenance contains forbidden claim: {phrase!r}")


def read_cast(path: Path, cruise_id: str, station_no: str) -> tuple[list[tuple[float, float, float]], dict]:
    """Return sorted (depth_m, temperature_c, salinity_psu) rows + provenance fields.

    Keeps only rows whose temperature and salinity quality flags are acceptable
    (2) or interpolated-acceptable (6) and whose values parse. Depth is taken from
    CTDPRS_DBAR, near 1 dbar per metre in the upper ocean.
    """
    rows: list[tuple[float, float, float]] = []
    meta: dict = {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            if r.get("CRUISE_ID") != cruise_id or r.get("STATION_NO") != station_no:
                continue
            t_raw = r.get("CTDTMP_DEG_C_ITS90", "").strip()
            s_raw = r.get("CTDSAL_PSS78", "").strip()
            tf = r.get("CTDTMP_FLAG_W", "").strip()
            sf = r.get("CTDSAL_FLAG_W", "").strip()
            p_raw = r.get("CTDPRS_DBAR", "").strip()
            if tf not in ("2", "6") or sf not in ("2", "6"):
                continue
            if t_raw in ("", "-999", "NaN") or s_raw in ("", "-999", "NaN") or p_raw in ("", "-999", "NaN"):
                continue
            try:
                p = float(p_raw)
                t = float(t_raw)
                s = float(s_raw)
            except ValueError:
                continue
            rows.append((p, t, s))
            if not meta:
                meta = {
                    "expocode": r.get("EXPOCODE", ""),
                    "cruise_id": cruise_id,
                    "station_no": station_no,
                    "date_utc": r.get("DATE_UTC", ""),
                    "time_utc": r.get("TIME_UTC", ""),
                    "lat": r.get("LATITUDE_DEC", ""),
                    "lon": r.get("LONGITUDE_DEC", ""),
                }
    rows.sort(key=lambda row: row[0])
    return rows, meta


def interp(x: float, xs: list[float], ys: list[float]) -> float:
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    lo, hi = 0, len(xs) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if xs[mid] <= x:
            lo = mid
        else:
            hi = mid
    span = xs[hi] - xs[lo]
    if span == 0:
        return ys[lo]
    f = (x - xs[lo]) / span
    return ys[lo] + f * (ys[hi] - ys[lo])


def resample(rows: list[tuple[float, float, float]], count: int) -> list[dict]:
    depths = [r[0] for r in rows]
    temps = [r[1] for r in rows]
    sals = [r[2] for r in rows]
    d0, d1 = depths[0], depths[-1]
    out: list[dict] = []
    for i in range(count):
        d = d0 + (d1 - d0) * (i / (count - 1))
        out.append({
            "depthM": round(d, 3),
            "temperatureC": round(interp(d, depths, temps), 3),
            "salinityPsu": round(interp(d, depths, sals), 3),
        })
    return out


def _iso_date(raw: str) -> str:
    """Convert M/D/YY or M/D/YYYY to YYYY-MM-DD; pass through anything else."""
    parts = raw.split("/")
    if len(parts) != 3:
        return raw
    try:
        m, d, y = (int(p) for p in parts)
    except ValueError:
        return raw
    if y < 100:
        y += 2000 if y < 70 else 1900
    return f"{y:04d}-{m:02d}-{d:02d}"


def _coord(lat_raw: str, lon_raw: str) -> str:
    """Format decimal lat/lon as hemisphere-tagged degrees, e.g. '48.40 N 123.01 W'."""
    try:
        lat = float(lat_raw)
        lon = float(lon_raw)
    except ValueError:
        return f"{lat_raw} {lon_raw}"
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    return f"{abs(lat):.2f} {ns} {abs(lon):.2f} {ew}"


def build_provenance(meta: dict, analog_of: str) -> str:
    """Construct the honest, guard-safe, prose-gate-clean provenance line.

    States exactly what is measured (depth, temperature, salinity), the CC0
    attribution and accession, the cast identity, the explicit nearby-analog
    label, and that the motion is interpretive. Keeps the two words of every
    forbidden phrase apart so the load-time guard does not throw.
    """
    cruise = meta.get("cruise_id", "")
    station = meta.get("station_no", "")
    date = _iso_date(meta.get("date_utc", ""))
    coord = _coord(meta.get("lat", ""), meta.get("lon", ""))
    prov = (
        "Measured CTD cast of depth, temperature, and salinity. "
        "NANOOS CruiseSalish, NCEI Accession 0307188, CC0 1.0, DOI 10.25921/jgrz-v584. "
        f"Cruise {cruise} station {station}, {date}, eastern Strait of Juan de Fuca near {coord}. "
        f"This is a nearby analog cast, not an on-site {analog_of} station. "
        "Halocline depth and density gradient are derived from the cast. "
        "The mixing motion is a stylized interpretation, not measured microstructure "
        "and not how an animal senses its surroundings."
    )
    return prov


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cast", required=True, type=Path, help="raw CruiseSalish CSV in the box")
    ap.add_argument("--cruise-id", required=True, help="CRUISE_ID of the selected cast")
    ap.add_argument("--station-no", required=True, help="STATION_NO of the selected cast")
    ap.add_argument("--analog-of", default="San Juan Channel / Orcasound Lab node",
                    help="the demo node this cast is a nearby analog for")
    ap.add_argument("--out", type=Path,
                    default=Path("web/lib/scene/ocean/measured_cruisesalish_profile.json"))
    args = ap.parse_args()

    rows, meta = read_cast(args.cast, args.cruise_id, args.station_no)
    if len(rows) < 2:
        raise SystemExit(
            f"ERROR: cast CRUISE_ID={args.cruise_id} STATION_NO={args.station_no} "
            f"has fewer than two acceptable depth samples ({len(rows)} found)"
        )

    provenance = build_provenance(meta, args.analog_of)
    assert_no_forbidden_claim(provenance)

    samples = resample(rows, SAMPLE_COUNT)
    profile = {
        "origin": "measured-ctd",
        "provenance": provenance,
        "maxDepthM": round(rows[-1][0], 3),
        "samples": samples,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")

    surf, deep = rows[0], rows[-1]
    print(f"wrote {args.out}")
    print(f"  cruise={meta['cruise_id']} station={meta['station_no']} expocode={meta['expocode']!r}")
    print(f"  raw measured samples={len(rows)} resampled={len(samples)} maxDepthM={profile['maxDepthM']}")
    print(f"  surface {surf[1]:.2f} C {surf[2]:.2f} PSU  deep {deep[1]:.2f} C {deep[2]:.2f} PSU")
    print(f"  provenance: {provenance}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
