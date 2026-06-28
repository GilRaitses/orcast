// Canonical honesty label constants for the WS-BATHY waveset.
//
// The modeled provenance reuses `SUBSTRATE_LABEL` so the bathy surfaces and the
// substrate depth field declare the same honesty string. The measured-coverage
// label and source attributions exist for the DEFERRED measured-overlay
// fast-follow only (see measuredOverlay.ts); no measured data is fetched here.

import { SUBSTRATE_LABEL } from "../../substrate";
import type {
  BathyMeasuredLabel,
  BathyModeledLabel,
  BathyModeledProvenance,
  MeasuredSource,
} from "./types";

/** Honesty label string for the modeled seabed. Equal to `SUBSTRATE_LABEL`. */
export const BATHY_MODELED_LABEL = SUBSTRATE_LABEL;

/** Honesty label string for a measured-coverage surface. */
export const BATHY_MEASURED_COVERAGE_LABEL = "measured coverage";

/**
 * The carried provenance of the baked MODELED seabed. The same CUDEM topobathy
 * surface that feeds the render tiles and the substrate depth field.
 */
export const BATHY_MODELED_PROVENANCE: BathyModeledProvenance = {
  kind: "modeled",
  label: BATHY_MODELED_LABEL,
  dataset: "NOAA NCEI CUDEM 1/9 arc-second topobathy",
  datum: "NAVD88",
  resolution: "1/9 arc-second",
  method: "interpolated regular grid, not per-point measured soundings",
  license: "NOAA NCEI public domain US Government work",
  modeledNotMeasured: true,
};

/** The single modeled honesty label shared by every modeled bathy surface. */
export const BATHY_MODELED: BathyModeledLabel = {
  kind: "modeled",
  measured: false,
  label: BATHY_MODELED_LABEL,
  provenance: BATHY_MODELED_PROVENANCE,
};

/**
 * Source attributions for the DEFERRED measured references. These describe the
 * licence terms a measured-coverage label must carry. They do NOT assert that
 * any point is measured; coverage is asserted only by the A1 provenance signal
 * at a real lat/lng, never by these constants.
 */
export const MEASURED_SOURCE_ATTRIBUTION: Record<MeasuredSource, string> = {
  BlueTopo: "NOAA Office of Coast Survey BlueTopo, public domain",
  NONNA:
    "Canadian Hydrographic Service NONNA, Open Government Licence Canada, attribution required, chart datum not NAVD88",
};

/**
 * Construct a MEASURED-COVERAGE label from a real source assertion. Requires the
 * caller to pass the source and its datum, so a measured label can only be made
 * where the A1 provenance signal already asserts coverage. No depth value is
 * fabricated here; this only labels a surface the caller already proved measured.
 */
export function measuredCoverageLabel(
  source: MeasuredSource,
  datum: string,
): BathyMeasuredLabel {
  return {
    kind: "measured-coverage",
    measured: true,
    label: BATHY_MEASURED_COVERAGE_LABEL,
    source,
    attribution: MEASURED_SOURCE_ATTRIBUTION[source],
    datum,
  };
}

/**
 * The scene honesty-note text the phase-B `SalishScene.tsx` editor adds to the
 * scene honesty record. Modeled-only scope: no measured-coverage overlay is
 * loaded, so every depth surface is labeled modeled.
 */
export const BATHY_SCENE_HONESTY_NOTE =
  "The seabed shown here is modeled, not measured. It is the NOAA NCEI CUDEM " +
  "1/9 arc-second topobathy surface on the NAVD88 datum, an interpolated " +
  "regular grid rather than per-point measured soundings. Depth readings and " +
  "the depth-tinted water are styling and physics over this modeled seabed, " +
  "not a survey. No measured-coverage overlay is loaded, so every depth " +
  "surface is labeled modeled.";
