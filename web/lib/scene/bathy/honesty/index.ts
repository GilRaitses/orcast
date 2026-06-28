// web/lib/scene/bathy/honesty
//
// The canonical honesty label model for the WS-BATHY waveset. The enforcement
// surface for charter rule B.6: no invented depths presented as measured.
//
// The baked seabed is the NOAA NCEI CUDEM 1/9 arc-second topobathy surface on
// NAVD88, an interpolated grid, so it is always MODELED. Use `attachModeledLabel`
// to stamp any depth-bearing bathy surface so it declares "modeled". The
// measured-coverage label and the `MeasuredCoverageProvider` interface are for
// the DEFERRED measured-overlay fast-follow and fetch nothing here.
//
// See WIRING-bathy-honesty.md for the integrator-facing contract.

export type {
  BathyLabel,
  BathyLabelTarget,
  BathyMeasuredLabel,
  BathyModeledLabel,
  BathyModeledProvenance,
  MeasuredSource,
} from "./types";

export {
  BATHY_MEASURED_COVERAGE_LABEL,
  BATHY_MODELED,
  BATHY_MODELED_LABEL,
  BATHY_MODELED_PROVENANCE,
  BATHY_SCENE_HONESTY_NOTE,
  MEASURED_SOURCE_ATTRIBUTION,
  measuredCoverageLabel,
} from "./labels";

export {
  attachBathyLabel,
  attachModeledLabel,
  BATHY_LABEL_KEY,
} from "./attach";

export {
  DEFERRED_MEASURED_OVERLAY,
  type MeasuredCoverageProvider,
  type MeasuredCoverageSource,
} from "./measuredOverlay";
