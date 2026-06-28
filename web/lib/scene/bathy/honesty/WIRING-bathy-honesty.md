# WIRING-bathy-honesty

Owner: WS-BATHY producer A4, Honesty Labeler. Scope: `web/lib/scene/bathy/honesty/` only. Pure helpers, no scene edits, no fetch. Does not edit `SalishScene.tsx`, the style module, or substrate and water2 internals. `three` not imported. No new dependency.

## What this is

The canonical honesty label model for the WS-BATHY waveset and the enforcement surface for charter rule B.6, no invented depths presented as measured.

The baked seabed is the NOAA NCEI CUDEM 1/9 arc-second topobathy surface on the NAVD88 datum, an interpolated regular grid, not per-point measured soundings. It is therefore always MODELED. The modeled honesty string reuses `SUBSTRATE_LABEL` so the bathy surfaces and the substrate depth field declare the same thing, `modeled, not measured`.

A measured-coverage label and a `MeasuredCoverageProvider` interface exist for the DEFERRED measured-overlay fast-follow only. They fetch nothing in this phase and assert measured only where a real source flag says so, never inferred.

## Exported API

```ts
import {
  BATHY_MODELED,
  BATHY_MODELED_LABEL,
  BATHY_MODELED_PROVENANCE,
  BATHY_MEASURED_COVERAGE_LABEL,
  BATHY_SCENE_HONESTY_NOTE,
  MEASURED_SOURCE_ATTRIBUTION,
  measuredCoverageLabel,
  attachModeledLabel,
  attachBathyLabel,
  BATHY_LABEL_KEY,
  DEFERRED_MEASURED_OVERLAY,
  type BathyLabel,
  type BathyModeledLabel,
  type BathyMeasuredLabel,
  type BathyModeledProvenance,
  type BathyLabelTarget,
  type MeasuredSource,
  type MeasuredCoverageProvider,
  type MeasuredCoverageSource,
} from "@/lib/scene/bathy/honesty";
```

### The provenance label object

`BATHY_MODELED_PROVENANCE: BathyModeledProvenance` carries the modeled seabed provenance.

```ts
{
  kind: "modeled",
  label: "modeled, not measured",          // === SUBSTRATE_LABEL
  dataset: "NOAA NCEI CUDEM 1/9 arc-second topobathy",
  datum: "NAVD88",
  resolution: "1/9 arc-second",
  method: "interpolated regular grid, not per-point measured soundings",
  license: "NOAA NCEI public domain US Government work",
  modeledNotMeasured: true,
}
```

`BATHY_MODELED: BathyModeledLabel` is the single modeled label every modeled bathy surface carries. Its `measured` field is the literal `false`, so a modeled surface can never structurally carry a measured assertion.

### The attach helper

`attachModeledLabel(target, baseName?)` stamps the canonical modeled label onto any depth-bearing surface so it declares `modeled`. The target only needs `name` and `userData`, which a `THREE.Object3D`, a panel record, or a provenance pin all satisfy, so the helper stays framework-free.

```ts
import { attachModeledLabel } from "@/lib/scene/bathy/honesty";

// On a THREE object, a panel, or a provenance pin:
attachModeledLabel(seabedTint, "bathy-seabed-tint");
// seabedTint.userData.modeledNotMeasured === true
// seabedTint.userData.label === "modeled, not measured"
// seabedTint.userData[BATHY_LABEL_KEY] === BATHY_MODELED  (the typed label)
// seabedTint.name === "bathy-seabed-tint (modeled, not measured)"
```

`attachBathyLabel(target, label, baseName?)` is the general form for stamping either a modeled or a measured-coverage label. A measured-coverage label additionally writes `measured = true`, `measuredSource`, `attribution`, and `datum`.

### The scene honesty note

`BATHY_SCENE_HONESTY_NOTE` is the proposed text the phase-B `SalishScene.tsx` editor adds to the scene honesty record. Modeled-only scope, it states the seabed is modeled CUDEM on NAVD88 and that no measured-coverage overlay is loaded.

## DEFERRED measured-overlay interface (fast-follow, no data fetched)

When the operator approves the measured reference (dispatch README open decision 1), the A1 provenance module implements `MeasuredCoverageProvider` against fetched BlueTopo (US) and CHS NONNA (BC) coverage assets, staged like the substrate JSON under `infra/3dtwin/` and copied to `web/public/geo/`.

```ts
interface MeasuredCoverageSource {
  source: "BlueTopo" | "NONNA";
  region: "US" | "BC";
  datum: string;        // NONNA is chart datum, not NAVD88
  attribution: string;
  url: string;          // fetched at runtime from web/public/geo/
}

interface MeasuredCoverageProvider {
  readonly sources: readonly MeasuredCoverageSource[];
  coverageAt(lat: number, lng: number): BathyMeasuredLabel | null; // null = modeled
  readonly loaded: boolean;
}
```

Until then `DEFERRED_MEASURED_OVERLAY` is a safe modeled-only stub. It has no assets, `loaded` is false, and `coverageAt` returns `null` for every query, so the scene stays honestly modeled. The phase-B editor can mount it now and swap in the A1 provider later without changing the mount.

Honesty rules the provider must keep, coverage is asserted only where the source flag is true, BlueTopo `bathy_coverage` true or NONNA present. It defaults to modeled everywhere else, never infers measured, and notes the NONNA chart datum so NONNA is not rendered as competing NAVD88 seabed geometry.

## Validation

`cd web && npx tsc --noEmit` passes (exit 0).

`cd web && npx tsx lib/scene/bathy/honesty/honesty.test.ts` passes: the provenance label reads modeled, a modeled surface never receives a measured label, a measured-coverage surface carries both the coverage label and its source attribution, and the deferred measured-overlay interface is typed and answers modeled everywhere.
