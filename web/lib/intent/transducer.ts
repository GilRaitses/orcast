// Intent transducer (WS-INTENT Producer A). A React-free bridge between the live
// Camera Director and each planner turn (B.7 implicit-intent feed).
//
// Responsibilities, kept deliberately small and framework-free:
//  1. A director registry. The Viewport Bridge registers the live director on
//     mount via `setActiveDirector` and clears it on unmount, so this module can
//     read the camera without any React coupling.
//  2. A throttled sampler of `CameraDirector.getState()` (leading + trailing,
//     ~250 ms), so a burst of frames or enrich calls collapses to a few reads
//     rather than one read per frame.
//  3. `enrichTurnContext(base)`, which folds the latest sampled look-at target
//     into the turn's `viewport`/`focus` and carries the dwell subject/altitude
//     as additive metadata, so the planner knows where the camera is dwelling.
//     With no director attached it returns the base unchanged.

import type { CameraDirector, CameraState } from "@/lib/scene/camera";
import type { TurnContext } from "@/lib/adaptiveConsole";

/**
 * A turn context enriched with implicit camera intent. Strictly a superset of
 * `TurnContext`: the extra fields are additive metadata and are ignored by the
 * existing request-body builder, so enrichment never changes existing behavior.
 */
export interface EnrichedTurnContext extends TurnContext {
  /** Camera dwell subject label from the active move/orbit, when known. */
  cameraSubject?: string | null;
  /** Camera altitude above sea level (Y=0) in metres, when a director is attached. */
  cameraAltitudeMeters?: number;
  /** True when the camera is continuously orbiting a subject. */
  cameraOrbiting?: boolean;
}

/** Throttle window for sampling `getState()`, in milliseconds (leading + trailing). */
export const SAMPLE_THROTTLE_MS = 250;

let activeDirector: CameraDirector | null = null;
let latestState: CameraState | null = null;
let lastSampleAt = 0;
let trailingTimer: ReturnType<typeof setTimeout> | null = null;

// Injectable clock so the throttle is deterministic under test. Defaults to the
// wall clock in production.
let clock: () => number = () => Date.now();

/** Register the live Camera Director. Called by the Viewport Bridge on mount. */
export function setActiveDirector(director: CameraDirector | null): void {
  activeDirector = director;
  latestState = null;
  lastSampleAt = 0;
  if (trailingTimer != null) {
    clearTimeout(trailingTimer);
    trailingTimer = null;
  }
}

/** Clear the active director. Called by the Viewport Bridge on unmount. */
export function clearActiveDirector(): void {
  setActiveDirector(null);
}

/** True when a director is currently registered. */
export function hasActiveDirector(): boolean {
  return activeDirector != null;
}

function takeSample(): void {
  if (!activeDirector) return;
  latestState = activeDirector.getState();
  lastSampleAt = clock();
}

/**
 * Request a throttled sample. The first call (or any call after the window has
 * elapsed) samples on the leading edge; calls inside the window coalesce into a
 * single trailing sample, so a burst of N calls produces at most two reads.
 */
function requestSample(): void {
  if (!activeDirector) return;
  const elapsed = clock() - lastSampleAt;
  if (elapsed >= SAMPLE_THROTTLE_MS) {
    takeSample();
    return;
  }
  if (trailingTimer == null) {
    trailingTimer = setTimeout(() => {
      trailingTimer = null;
      takeSample();
    }, SAMPLE_THROTTLE_MS - elapsed);
  }
}

/** Latest throttled snapshot, or null before the first sample. Read-only view. */
export function latestCameraState(): CameraState | null {
  return latestState;
}

/**
 * Enrich a planner turn with the camera's implicit intent. Folds the sampled
 * look-at target into `viewport`/`focus` only where the base does not already
 * carry an explicit value, so an explicit scene click or planner viewport wins
 * and existing behavior is preserved. Camera subject/altitude/orbit ride along
 * as additive metadata. Returns the base unchanged when no director is attached.
 */
export function enrichTurnContext(base: TurnContext): EnrichedTurnContext {
  if (!activeDirector) return base;
  requestSample();
  const state = latestState;
  if (!state) return base;

  const enriched: EnrichedTurnContext = {
    ...base,
    cameraSubject: state.subject,
    cameraAltitudeMeters: state.altitude,
    cameraOrbiting: state.isOrbiting,
  };

  if (state.target) {
    const { lat, lng } = state.target;
    if (base.viewport == null) {
      enriched.viewport = { lat, lng };
    }
    if (base.focus == null) {
      enriched.focus = { cell: `${lat},${lng}` };
    }
  }

  return enriched;
}

/**
 * Test-only seam to drive the throttle deterministically. Not used in
 * production code paths; the default clock is the wall clock.
 */
export function __setClockForTest(fn: (() => number) | null): void {
  clock = fn ?? (() => Date.now());
}
