// DEFERRED fast-follow: the measured-coverage overlay interface.
//
// This file documents the interface only. It fetches NOTHING and asserts NO
// measured depth in the phase-A modeled-only scope. When the operator approves
// the measured reference (open decision 1 in the dispatch README), the A1
// provenance module implements `MeasuredCoverageProvider` against fetched
// BlueTopo and CHS NONNA coverage assets staged like the substrate JSON. Until
// then `DEFERRED_MEASURED_OVERLAY` answers modeled everywhere.
//
// Honesty: coverage is asserted ONLY where a real source flag says so (BlueTopo
// `bathy_coverage` true, or NONNA present). It is NEVER inferred, and the
// default is always modeled.

import type { BathyMeasuredLabel, MeasuredSource } from "./types";

/**
 * Description of one measured reference asset. Mirrors the substrate asset
 * decision: copied verbatim, fetched at runtime from `web/public/geo/`, source
 * of truth staged under `infra/3dtwin/`, swappable without a rebuild.
 */
export interface MeasuredCoverageSource {
  source: MeasuredSource;
  /** Which side of the boundary this asset covers. */
  region: "US" | "BC";
  /** Vertical datum of the asset. NONNA is chart datum, not NAVD88. */
  datum: string;
  /** Full attribution and licence string. */
  attribution: string;
  /** Runtime asset URL, served from `web/public/geo/`, fetched like substrate. */
  url: string;
}

/**
 * The query surface a future measured overlay must implement. `coverageAt`
 * returns a measured-coverage label ONLY where the source flag asserts measured
 * coverage, and `null` everywhere else (meaning: fall back to modeled). It never
 * fabricates a measured depth and never infers coverage.
 */
export interface MeasuredCoverageProvider {
  /** The assets this provider draws coverage from. Empty until implemented. */
  readonly sources: readonly MeasuredCoverageSource[];
  /** Measured-coverage label at a lat/lng, or `null` to fall back to modeled. */
  coverageAt(lat: number, lng: number): BathyMeasuredLabel | null;
  /** True once at least one measured asset is loaded. False while deferred. */
  readonly loaded: boolean;
}

/**
 * The deferred, modeled-only provider. No assets, never loaded, answers `null`
 * (modeled) for every query. The phase-B editor can mount this safely and the
 * scene stays honestly modeled until the measured overlay is approved and the
 * A1 provider replaces it.
 */
export const DEFERRED_MEASURED_OVERLAY: MeasuredCoverageProvider = {
  sources: [],
  loaded: false,
  coverageAt: () => null,
};
