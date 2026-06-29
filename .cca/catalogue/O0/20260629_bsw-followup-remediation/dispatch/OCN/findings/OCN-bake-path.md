# OCN-bake-path

Read-only research finding by OCN-R2 (measured-ocean-stratification wave). No code edited, no dataset downloaded, no staging.

## What this answers

I define how a real CTD cast becomes a `StratificationProfile` with `origin: "measured-ctd"`, reusing the existing `stratificationToTexture` bake unchanged, with an honest provenance line that passes the module-load forbidden-claim guard.

The end-to-end path I recommend is offline python resample to a small baked JSON, then a net-new dependency-free web loader that imports that JSON and returns a `StratificationProfile` shaped exactly like `analyticHaloclineProfile`, so it drops into `createDoubleDiffusionLayer({ profile })` with no other change.

```text
raw CTD cast (CC0, not downloaded here)
  -> infra/ocean/bake_measured_profile.py  (resample to 64, emit small JSON)
  -> web/lib/scene/ocean/measured_cruisesalish_profile.json
  -> web/lib/scene/ocean/measuredProfile.ts  (import JSON, return StratificationProfile)
  -> createDoubleDiffusionLayer({ profile })  (reuses stratificationToTexture)
```

## 1. Target shape

The target is one `StratificationProfile` object literal with `origin: "measured-ctd"`, `maxDepthM` taken from the cast, `samples` ordered surface to deep as `{ depthM, temperatureC, salinityPsu }`, and a `provenance` string. The web side reads this verbatim from the baked JSON.

`stratificationToTexture` already normalizes salinity, temperature, and the density-gradient channel per profile, so the JSON carries only raw `depthM` / `temperatureC` / `salinityPsu` plus `origin`, `provenance`, and `maxDepthM`. No precomputed channels and no normalization belong in the JSON.

The values below are ILLUSTRATIVE placeholders, NOT real CTD data. They show the shape and the surface-to-deep ordering at a sane Salish magnitude. The real numbers come from the baked cast at ship time.

```jsonc
{
  "origin": "measured-ctd",
  "provenance": "measured CTD cast from NANOOS CruiseSalish, NCEI Accession 0307188 (CC0 1.0). The cast supplies depth, temperature, and salinity only. The moving layers are an interpretive view of water-mass mixing, not a measurement of microstructure or how an animal senses its surroundings.",
  "maxDepthM": 80,
  "samples": [
    { "depthM": 0.0,  "temperatureC": 13.0, "salinityPsu": 28.0 },
    { "depthM": 1.3,  "temperatureC": 12.9, "salinityPsu": 28.1 },
    { "depthM": 2.5,  "temperatureC": 12.7, "salinityPsu": 28.3 },
    { "depthM": 12.7, "temperatureC": 11.4, "salinityPsu": 29.6 },
    { "depthM": 14.0, "temperatureC": 11.0, "salinityPsu": 29.9 },
    { "depthM": 15.2, "temperatureC": 10.6, "salinityPsu": 30.2 },
    { "depthM": 40.0, "temperatureC": 9.4,  "salinityPsu": 30.9 },
    { "depthM": 78.7, "temperatureC": 9.0,  "salinityPsu": 31.2 },
    { "depthM": 80.0, "temperatureC": 9.0,  "salinityPsu": 31.2 }
  ]
}
```

The shipped JSON holds 64 entries in the `samples` array. The block above is truncated to nine illustrative entries so the shape is readable. The 64 count matches the analytic default of `Math.max(4, opts.samples ?? 64)`, so the baked texture width equals the analytic texture width and the shader samples both identically.

## 2. Offline bake method

A python script under `infra/ocean/` reads the raw cast, resamples to a fixed 64 samples over the cast depth range from shallowest to deepest, and emits the small baked JSON above. The script does the only numeric work, so the web side stays dependency-free and never parses raw CTD files.

Resampling rule. I sort the raw cast by depth, take the cast min and max depth, build 64 evenly spaced target depths across that span, and linearly interpolate temperature and salinity at each target depth. `maxDepthM` is the cast deepest sample. No smoothing and no synthetic extension beyond the cast range, so the JSON stays faithful to the cast.

```python
#!/usr/bin/env python3
"""Bake one CC0 CruiseSalish CTD cast into a small StratificationProfile JSON.

Input  : a raw cast file with columns depth_m, temperature_c, salinity_psu
         (NANOOS CruiseSalish / NCEI Accession 0307188, CC0 1.0).
Output : web/lib/scene/ocean/measured_cruisesalish_profile.json

The web side stays dependency-free: stratificationToTexture normalizes
salinity, temperature, and the density-gradient channel per profile at
runtime, so this JSON carries only raw depth/temp/salinity samples plus
origin, provenance, and maxDepthM. Sample count matches the analytic
default of 64 so the baked texture width is identical.

MEASURED INPUT, INTERPRETIVE OUTPUT. The cast supplies depth, temperature,
and salinity only. The moving render layer is an interpretive view of
water-mass mixing, not a map of microstructure.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

SAMPLE_COUNT = 64  # matches analyticHaloclineProfile default

PROVENANCE = (
    "measured CTD cast from NANOOS CruiseSalish, NCEI Accession 0307188 "
    "(CC0 1.0). The cast supplies depth, temperature, and salinity only. "
    "The moving layers are an interpretive view of water-mass mixing, not a "
    "measurement of microstructure or how an animal senses its surroundings."
)


def read_cast(path: Path) -> list[tuple[float, float, float]]:
    """Return raw (depth_m, temperature_c, salinity_psu) rows, sorted by depth."""
    rows: list[tuple[float, float, float]] = []
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            d = float(r["depth_m"])
            t = float(r["temperature_c"])
            s = float(r["salinity_psu"])
            rows.append((d, t, s))
    rows.sort(key=lambda row: row[0])
    return rows


def interp(x: float, xs: list[float], ys: list[float]) -> float:
    """Linear interpolation of ys at x; clamps to the endpoints."""
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    lo = 0
    hi = len(xs) - 1
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cast", required=True, type=Path, help="raw CTD cast CSV")
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("web/lib/scene/ocean/measured_cruisesalish_profile.json"),
    )
    args = ap.parse_args()

    rows = read_cast(args.cast)
    if len(rows) < 2:
        print("ERROR: cast needs at least two depth samples")
        return 1

    samples = resample(rows, SAMPLE_COUNT)
    profile = {
        "origin": "measured-ctd",
        "provenance": PROVENANCE,
        "maxDepthM": round(rows[-1][0], 3),
        "samples": samples,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out} with {len(samples)} samples, maxDepthM={profile['maxDepthM']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

The raw cast column names above are a contract the operator maps when running the bake. If the NCEI CSV uses different headers such as pressure in dbar instead of depth in metres, the operator adds the column rename or the dbar to metre conversion inside `read_cast`, and nothing else changes.

## 3. Web loader

The net-new file is `web/lib/scene/ocean/measuredProfile.ts`. It imports the baked JSON, narrows the `origin` field to the `StratificationOrigin` union, and returns a value typed exactly as `StratificationProfile`, the same return type as `analyticHaloclineProfile`. It reuses `stratificationToTexture` by leaving the bake entirely to `createDoubleDiffusionLayer`, so the loader itself imports nothing from `stratification.ts` except the type. That keeps the loader dependency-free and the normalization path identical.

```typescript
// Measured CTD stratification profile, baked offline from one CC0 CruiseSalish
// cast (NCEI Accession 0307188) into a small JSON by infra/ocean/bake_measured_profile.py.
//
// HONESTY. The cast supplies depth, temperature, and salinity only. The render
// layer that consumes this profile is interpretive, not a map of measured
// microstructure and not a depiction of how an animal senses its surroundings.
// This module performs NO bake of its own: it returns a plain StratificationProfile
// and lets createDoubleDiffusionLayer call the shared stratificationToTexture so
// the per-profile normalization stays identical to the analytic path.

import type { StratificationProfile, StratificationOrigin } from "./stratification";
import baked from "./measured_cruisesalish_profile.json";

/**
 * Return the baked measured CTD profile, typed exactly like
 * analyticHaloclineProfile's return so it drops into
 * createDoubleDiffusionLayer({ profile }) with no other change.
 */
export function measuredHaloclineProfile(): StratificationProfile {
  return {
    origin: baked.origin as StratificationOrigin,
    provenance: baked.provenance,
    maxDepthM: baked.maxDepthM,
    samples: baked.samples.map((s) => ({
      depthM: s.depthM,
      temperatureC: s.temperatureC,
      salinityPsu: s.salinityPsu,
    })),
  };
}
```

The host swaps the profile with a single argument and no other change.

```typescript
import { createDoubleDiffusionLayer } from "@/lib/scene/ocean";
import { measuredHaloclineProfile } from "@/lib/scene/ocean/measuredProfile";

const layer = createDoubleDiffusionLayer({ profile: measuredHaloclineProfile() });
```

`createDoubleDiffusionLayer` already calls `assertNoForbiddenClaim(..., profile.provenance)` before baking, so the measured provenance is guarded on the same path as the analytic one with no extra wiring. The barrel can re-export `measuredHaloclineProfile` from `web/lib/scene/ocean/index.ts` alongside `analyticHaloclineProfile` if the host prefers a single import surface. That re-export is the only optional touch outside the net-new file and is not required for the drop-in.

The JSON import needs `resolveJsonModule` enabled in the web tsconfig. If it is not already on, that one flag is the only build-config change, and it carries no runtime dependency.

## 4. Provenance line

Recommended provenance string, used verbatim in both the python `PROVENANCE` constant and the baked JSON.

```text
measured CTD cast from NANOOS CruiseSalish, NCEI Accession 0307188 (CC0 1.0). The cast supplies depth, temperature, and salinity only. The moving layers are an interpretive view of water-mass mixing, not a measurement of microstructure or how an animal senses its surroundings.
```

This names the cast as NANOOS CruiseSalish, carries the CC0 1.0 attribution and the NCEI Accession 0307188, is honest that the cast supplies depth, temperature, and salinity only, and states that the visualization is interpretive.

Forbidden-substring check against the guard in `interpretiveOceanLayer.ts`, lowercased per `assertNoForbiddenClaim`.

| Forbidden substring | Present in recommended provenance |
|---|---|
| measured thermohaline | no |
| biosonar perception | no |
| biosonar reveals | no |
| what the whale sees | no |
| salt fingering observed | no |

The string contains the word `measured` and the word `microstructure` but never the contiguous substring `measured thermohaline`, and it never mentions biosonar, the whale, or salt fingering. It passes the guard.

## 5. Rejected alternatives

| Choice | Recommended | Rejected | Why |
|---|---|---|---|
| Bake target | small resampled JSON, baked to texture at runtime by `stratificationToTexture` | precomputed PNG or DataTexture shipped as a binary asset | The runtime `stratificationToTexture` path already exists and normalizes salinity, temperature, and the density-gradient channel per profile. A PNG would freeze a separate normalization, drift from the analytic path, and add a binary asset and a decode step. JSON keeps one normalization for both origins. |
| Payload | small 64-sample resampled JSON | the full raw CTD cast shipped to the web | The cast can hold hundreds of bins at fine pressure spacing and extra columns. Shipping it bloats the bundle and forces raw parsing on the web side. A 64-sample JSON matches the analytic texture width and keeps the web side dependency-free. Raw cast is a box item, not a ship item. |
| Loader bake | loader returns a plain profile and lets `createDoubleDiffusionLayer` call `stratificationToTexture` | loader bakes its own texture | Baking in the loader would duplicate the bake call and risk a divergent texture. Returning a plain `StratificationProfile` reuses the one shared bake unchanged. |
| Numeric work | python under `infra/ocean/` | resample in TypeScript at load time | Offline resampling keeps the heavy and source-format-specific parsing out of the bundle and out of the render path, and keeps the web build free of CSV or interpolation code. |
