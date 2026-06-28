// The attach helper. Stamps an honesty label onto any bathy surface so that any
// surface showing a depth declares whether it is MODELED or MEASURED.
//
// Framework-free: the target only needs `name` and `userData`, which a
// THREE.Object3D, a panel record, or a provenance pin all satisfy. Mirrors the
// honesty tagging that `buildSubstrateOverlay` already does on its Points cloud.

import { BATHY_MODELED } from "./labels";
import type { BathyLabel, BathyLabelTarget } from "./types";

/** Reserved userData key the attach helper writes the full label under. */
export const BATHY_LABEL_KEY = "bathyHonestyLabel";

/**
 * Stamp `label` onto `target.userData` and reflect it into `target.name`.
 *
 * For a modeled surface this writes `modeledNotMeasured = true` and the modeled
 * label string, so the surface reads exactly like the substrate overlay. For a
 * measured-coverage surface it writes `measured = true`, the source, the
 * attribution, and the datum, so the served surface declares what measured it.
 *
 * Returns the same target for chaining. The full label is also stored under
 * `BATHY_LABEL_KEY` so a consumer can recover the typed label.
 */
export function attachBathyLabel<T extends BathyLabelTarget>(
  target: T,
  label: BathyLabel,
  baseName?: string,
): T {
  const userData = (target.userData ??= {});
  userData[BATHY_LABEL_KEY] = label;
  userData.label = label.label;

  if (label.kind === "modeled") {
    userData.modeledNotMeasured = true;
    userData.measured = false;
    userData.dataset = label.provenance.dataset;
    userData.datum = label.provenance.datum;
    userData.provenance = label.provenance;
  } else {
    userData.modeledNotMeasured = false;
    userData.measured = true;
    userData.measuredSource = label.source;
    userData.attribution = label.attribution;
    userData.datum = label.datum;
  }

  const base = baseName ?? target.name;
  if (base) {
    target.name = `${base} (${label.label})`;
  } else {
    target.name = label.label;
  }

  return target;
}

/**
 * Convenience for the common case: stamp the canonical MODELED label so any
 * depth-bearing surface declares "modeled". This is the only attach used in the
 * phase-A modeled-only scope.
 */
export function attachModeledLabel<T extends BathyLabelTarget>(
  target: T,
  baseName?: string,
): T {
  return attachBathyLabel(target, BATHY_MODELED, baseName);
}
