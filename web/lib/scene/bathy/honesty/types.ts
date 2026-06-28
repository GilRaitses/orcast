// Honesty label and provenance types for the WS-BATHY waveset.
//
// This is the enforcement surface for charter honesty rule B.6: no invented
// depths presented as measured. Every bathy surface that shows a depth carries
// one of these labels, so a UI built from the scene graph can always declare
// whether a depth is MODELED or MEASURED.
//
// The baked seabed is the NOAA NCEI CUDEM 1/9 arc-second topobathy surface on
// the NAVD88 datum, an interpolated regular grid, NOT per-point measured
// soundings. It is therefore always MODELED. A measured-coverage label exists
// only for the DEFERRED measured-overlay fast-follow (see measuredOverlay.ts),
// and is asserted only where a real source flag says so, never inferred.

/** Measured bathymetry references. US side BlueTopo, BC side CHS NONNA. */
export type MeasuredSource = "BlueTopo" | "NONNA";

/**
 * The carried provenance of the MODELED seabed. Reuses the substrate honesty
 * label string so the modeled bathy surfaces and the substrate field declare
 * the same thing.
 */
export interface BathyModeledProvenance {
  kind: "modeled";
  /** Human-facing honesty label. Mirrors `SUBSTRATE_LABEL` ("modeled, not measured"). */
  label: string;
  /** The dataset the seabed geometry is baked from. */
  dataset: string;
  /** Vertical datum of the modeled surface. */
  datum: string;
  /** Source grid resolution. */
  resolution: string;
  /** Why it is modeled, not measured: an interpolated grid, not per-point soundings. */
  method: string;
  /** Licence / usage string of the modeled source. */
  license: string;
  /** Always true. This surface is derived/modeled, not an in-situ measurement. */
  modeledNotMeasured: true;
}

/**
 * Label for a MODELED bathy surface. The default and only label produced in the
 * phase-A modeled-only scope. `measured` is the literal `false`, so a modeled
 * surface can never structurally carry a measured assertion.
 */
export interface BathyModeledLabel {
  kind: "modeled";
  measured: false;
  /** The honesty label string, equal to `provenance.label`. */
  label: string;
  provenance: BathyModeledProvenance;
}

/**
 * Label for a MEASURED-COVERAGE bathy surface. Produced ONLY for the DEFERRED
 * measured-overlay fast-follow, and only where a real source flag asserts
 * coverage. Carries both the coverage label and its source attribution so the
 * served surface can declare what measured it and under what datum and licence.
 */
export interface BathyMeasuredLabel {
  kind: "measured-coverage";
  measured: true;
  /** The coverage label string. */
  label: string;
  /** Which survey reference asserts coverage here. */
  source: MeasuredSource;
  /** Full source attribution, including licence terms. */
  attribution: string;
  /**
   * Vertical datum of the measured source. NONNA is chart datum, NOT NAVD88, so
   * it must not be rendered as competing seabed geometry against the NAVD88
   * modeled surface.
   */
  datum: string;
}

/** Any honesty label a served bathy surface may carry. */
export type BathyLabel = BathyModeledLabel | BathyMeasuredLabel;

/**
 * Minimal structural target for the attach helper. A THREE.Object3D satisfies
 * this (it has `name` and `userData`), and so does a plain panel/provenance-pin
 * record, so the helper stays framework-free and unit-testable without three.
 */
export interface BathyLabelTarget {
  name?: string;
  userData?: Record<string, unknown>;
}
