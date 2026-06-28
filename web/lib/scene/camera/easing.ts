// Easing curves for the Camera Director. Pure functions of t in [0,1].

import type { EasingFn, EasingName } from "./types";

export const EASINGS: Record<EasingName, EasingFn> = {
  linear: (t) => t,
  easeInQuad: (t) => t * t,
  easeOutQuad: (t) => t * (2 - t),
  easeInOutQuad: (t) => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t),
  easeInCubic: (t) => t * t * t,
  easeOutCubic: (t) => 1 - Math.pow(1 - t, 3),
  easeInOutCubic: (t) =>
    t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
  easeInOutSine: (t) => -(Math.cos(Math.PI * t) - 1) / 2,
};

/** Resolve an easing option (name or function) to a concrete function. */
export function resolveEasing(easing?: EasingName | EasingFn): EasingFn {
  if (typeof easing === "function") return easing;
  if (easing && easing in EASINGS) return EASINGS[easing];
  return EASINGS.easeInOutCubic;
}
