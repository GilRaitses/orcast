// Fly-through Controller for the Console Journey (WS-INTENT, Producer B).
//
// Pure orchestration over the W1 modules. Given a resolved gazetteer Place, a
// live Camera Director, and an atmosphere context, runPlaceJourney runs the
// proven sandbox beat:
//
//   1. roll fog IN as a soft mask over the opening cut (skipped when no fog)
//   2. flyTo a wide establishing altitude derived from place.bounds
//   3. roll fog back OUT
//   4. descendTo a cruising altitude well above the water
//   5. followPath an approach route ending at the place center
//   6. orbit the place center as the slow resting state
//
// This module is the JourneyScene.DirectorRig choreography lifted out of React
// (Discovery seam E). It holds NO React state, runs NO render loop of its own,
// and never edits the camera, atmosphere, or gazetteer modules. It composes
// them: the director is advanced per-frame by the caller, and every atmosphere
// tween it creates is handed to the caller's per-frame push sink, mirroring the
// sandbox `push(t)` into the rig's transition list.
//
// The waypoints derived from a place's bounds are APPROXIMATE lane points, not a
// surveyed track. The curated Anacortes -> Orcas corridor is likewise an
// approximate ferry lane, carried from the sandbox reference.

import type {
  CameraDirector,
  LatLng,
  LatLngAlt,
  OrbitHandle,
} from "@/lib/scene/camera";
import {
  rollInFog,
  type FogTarget,
  type TweenHandle,
} from "@/lib/scene/atmosphere/transition";
import type { Place, PlaceBounds } from "@/lib/geo/gazetteer";

// --- atmosphere context -----------------------------------------------------

/**
 * The atmosphere surface the controller drives: the fog object the realism rig
 * put on `scene.fog` (or null when the scene has no fog), plus a push sink the
 * caller drains each frame. Every tween the controller creates is handed to
 * `push` so the caller advances it from its render loop, exactly as the sandbox
 * DirectorRig pushes into its per-frame transition list. A null `fog` is
 * tolerated: the journey still runs, just without the soft fog mask.
 */
export interface JourneyAtmosphere {
  /** The scene fog to mask with, or null when the scene has no fog. */
  fog: FogTarget | null;
  /** Per-frame tween sink; the caller advances each pushed tween with update(dtMs). */
  push: (tween: TweenHandle) => void;
}

// --- options & handle -------------------------------------------------------

/** Optional overrides for {@link runPlaceJourney}. Sensible defaults match the sandbox. */
export interface RunPlaceJourneyOptions {
  /**
   * Curated approach lane lead-in for a known corridor, as geographic points
   * (without the final center, which the controller always appends). When
   * omitted, a corridor is looked up by place id, then a generic approach is
   * derived from the place bounds. Points are approximate lane points.
   */
  corridor?: LatLng[];
  /** Establishing flyTo duration (ms). Default 4500. */
  establishMs?: number;
  /** Fog mask-IN duration (ms). Default 1400. */
  fogMaskInMs?: number;
  /** Fog clear-OUT duration (ms). Default 3200. */
  fogClearMs?: number;
  /** descendTo duration (ms). Default 4500. */
  descendMs?: number;
  /** followPath duration (ms). Default 17000. */
  followMs?: number;
  /** Orbit angular speed (radians/second). Default 0.05. */
  orbitSpeed?: number;
}

/**
 * Cancel handle for an in-flight journey. `cancel()` supersedes the run: it
 * stops the active director move, stops the resting orbit, and cancels every
 * atmosphere tween the run pushed, so a later search can start a fresh journey
 * over the same director without the old beat fighting it. `done` resolves once
 * the beat sequence settles or is cancelled, so awaiting it never dangles.
 */
export interface JourneyHandle {
  /** Supersede the journey: stop the move, the orbit, and the pushed tweens. */
  cancel(): void;
  /** Resolves when the beat sequence settles or is cancelled. */
  readonly done: Promise<void>;
}

// --- beat constants (carried from the proven sandbox JourneyScene) ----------

// Metres per degree near 48.5 N, matching the constants the camera director and
// sceneIntent use for the horizontal/altitude scale.
const METERS_PER_DEG_LAT = 111_000;
const METERS_PER_DEG_LNG = 73_600;

// Establishing altitude band (metres above sea level). Derived from the place
// diagonal, clamped to a cinematic band so a tiny harbor still gets a wide
// opening shot and a whole island does not rocket the camera into space.
const ESTABLISH_ALT_FLOOR_M = 1800;
const ESTABLISH_ALT_CEIL_M = 3600;
const ESTABLISH_ALT_DIAG_K = 0.6;

// Cruising and resting altitudes, and the approach altitude band, all well above
// the director's hard no-dunk clamp. Carried from the sandbox.
const CRUISE_ALT_M = 230;
const ORBIT_ALT_M = 820;
const APPROACH_ALT_START_M = 240;
const APPROACH_ALT_END_M = 182;

// Default beat timings (ms) and orbit speed, matching the sandbox choreography.
const DEFAULT_ESTABLISH_MS = 4500;
const DEFAULT_FOG_MASK_IN_MS = 1400;
const DEFAULT_FOG_CLEAR_MS = 3200;
const DEFAULT_DESCEND_MS = 4500;
const DEFAULT_FOLLOW_MS = 17000;
const DEFAULT_ORBIT_SPEED = 0.05;

// The fog mask pulls the linear-fog `far` to this fraction of its resting value,
// matching the sandbox's `baseFar * 0.5` soft cut mask.
const FOG_MASK_FAR_FRACTION = 0.5;

// Curated approach corridors keyed by place id. The Anacortes -> Orcas ferry
// lane (carried from the sandbox FERRY_ROUTE lead-in, minus its terminal point,
// which the controller always replaces with the resolved place center). These
// are approximate ferry-lane waypoints, not a surveyed track.
const ORCAS_FERRY_CORRIDOR: LatLng[] = [
  { lat: 48.5, lng: -122.78 },
  { lat: 48.52, lng: -122.83 },
  { lat: 48.55, lng: -122.87 },
  { lat: 48.58, lng: -122.9 },
  { lat: 48.62, lng: -122.905 },
];

const CURATED_CORRIDORS: Record<string, LatLng[]> = {
  "east-sound": ORCAS_FERRY_CORRIDOR,
  "orcas-island": ORCAS_FERRY_CORRIDOR,
  "orcas-village": ORCAS_FERRY_CORRIDOR,
  rosario: ORCAS_FERRY_CORRIDOR,
};

// --- derivations ------------------------------------------------------------

function clamp(v: number, lo: number, hi: number): number {
  return v < lo ? lo : v > hi ? hi : v;
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

/** Approximate geographic diagonal of a place box, in metres. */
function geoDiagonalMeters(b: PlaceBounds): number {
  const latM = (b.max_lat - b.min_lat) * METERS_PER_DEG_LAT;
  const lngM = (b.max_lng - b.min_lng) * METERS_PER_DEG_LNG;
  return Math.hypot(latM, lngM);
}

/**
 * Establishing altitude (metres) derived from the place bounds. A larger place
 * gets a higher opening shot so the whole extent plus surrounding context fits
 * the frame, clamped to a cinematic band.
 */
export function establishAltitudeMeters(bounds: PlaceBounds): number {
  return clamp(
    geoDiagonalMeters(bounds) * ESTABLISH_ALT_DIAG_K,
    ESTABLISH_ALT_FLOOR_M,
    ESTABLISH_ALT_CEIL_M,
  );
}

/**
 * Build the approach polyline for a place: a corridor lead-in (curated, looked
 * up by id, or supplied) followed by the place center, with altitudes easing
 * down across the run. When no corridor applies, a generic lead-in is derived
 * from the place center and bounds, approaching from open water to the
 * south-east. The returned path always ENDS exactly at the place center, so the
 * follow beat lands on target. Waypoints are approximate lane points.
 */
export function approachPath(place: Place, corridor?: LatLng[]): LatLngAlt[] {
  const leadIn = corridor ?? CURATED_CORRIDORS[place.id] ?? derivedLeadIn(place);
  const center: LatLng = { lat: place.lat, lng: place.lng };
  const points: LatLng[] = [...leadIn, center];
  const last = points.length - 1;
  return points.map((p, i) => ({
    lat: p.lat,
    lng: p.lng,
    altitudeMeters: lerp(
      APPROACH_ALT_START_M,
      APPROACH_ALT_END_M,
      last === 0 ? 1 : i / last,
    ),
  }));
}

/**
 * Derive a generic approach lead-in from a place center and bounds. Begins about
 * three half-boxes to the south and east of center (an approach from open water)
 * and steps straight in toward the center. Approximate lane points, not surveyed.
 */
function derivedLeadIn(place: Place): LatLng[] {
  const b = place.bounds;
  const halfLat = (b.max_lat - b.min_lat) / 2;
  const halfLng = (b.max_lng - b.min_lng) / 2;
  return [
    { lat: place.lat - halfLat * 3, lng: place.lng + halfLng * 3 },
    { lat: place.lat - halfLat * 2, lng: place.lng + halfLng * 2 },
    { lat: place.lat - halfLat, lng: place.lng + halfLng },
  ];
}

// --- the journey ------------------------------------------------------------

/**
 * Run the place journey beat over a live director, composing the atmosphere
 * transitions through the caller's push sink. Returns immediately with a cancel
 * handle; the beat advances as the caller ticks the director and drains the push
 * sink each frame. A null `atmosphere.fog` is tolerated, the journey just skips
 * the fog mask.
 *
 * Beat order on the director: flyTo (establishing) -> descendTo (cruise) ->
 * followPath (approach ending at center) -> orbit (resting state).
 */
export function runPlaceJourney(
  place: Place,
  director: CameraDirector,
  atmosphere: JourneyAtmosphere,
  opts: RunPlaceJourneyOptions = {},
): JourneyHandle {
  let cancelled = false;
  let orbit: OrbitHandle | null = null;
  const pushed: TweenHandle[] = [];

  const fog = atmosphere.fog ?? null;
  // Resting fog far so the clear-out beat can ease back to it. Linear fog only;
  // a FogExp2 has no far, so its clear-out falls back to the rollInFog default.
  const restingFar = fog && isLinearFog(fog) ? fog.far : null;

  const pushTween = (tween: TweenHandle): void => {
    pushed.push(tween);
    atmosphere.push(tween);
  };

  const center: LatLng = { lat: place.lat, lng: place.lng };
  const establishAltM = establishAltitudeMeters(place.bounds);
  const path = approachPath(place, opts.corridor);
  const orbitSpeed = opts.orbitSpeed ?? DEFAULT_ORBIT_SPEED;

  const done = (async () => {
    // Establishing: roll fog IN as a soft mask over the opening cut, then a wide
    // high pass framing the place from the derived establishing altitude.
    if (fog) {
      const far = restingFar != null ? restingFar * FOG_MASK_FAR_FRACTION : undefined;
      pushTween(rollInFog(opts.fogMaskInMs ?? DEFAULT_FOG_MASK_IN_MS, fog, { far }));
    }
    await director.flyTo(
      { lat: center.lat, lng: center.lng, altitudeMeters: establishAltM },
      {
        durationMs: opts.establishMs ?? DEFAULT_ESTABLISH_MS,
        subject: place.name,
        easing: "easeInOutCubic",
      },
    );
    if (cancelled) return;

    // Descent: clear the fog back out and drop to a cruising altitude.
    if (fog) {
      const far = restingFar != null ? restingFar : undefined;
      pushTween(rollInFog(opts.fogClearMs ?? DEFAULT_FOG_CLEAR_MS, fog, { far }));
    }
    await director.descendTo(CRUISE_ALT_M, {
      durationMs: opts.descendMs ?? DEFAULT_DESCEND_MS,
      subject: "approach",
      easing: "easeOutCubic",
    });
    if (cancelled) return;

    // Follow: fly the approach route at a readable altitude, looking ahead and
    // slightly down toward the destination, ending at the place center.
    await director.followPath(path, {
      durationMs: opts.followMs ?? DEFAULT_FOLLOW_MS,
      subject: `approach to ${place.name}`,
      lookAhead: 0.1,
      easing: "easeInOutSine",
    });
    if (cancelled) return;

    // Settle: a slow orbit framing the place as the resting state.
    orbit = director.orbit(center, orbitRadius(place), orbitSpeed, {
      subject: place.name,
      altitudeMeters: ORBIT_ALT_M,
    });
  })();

  return {
    cancel(): void {
      if (cancelled) return;
      cancelled = true;
      for (const tween of pushed) tween.cancel();
      orbit?.stop();
      director.stop();
    },
    done,
  };
}

/**
 * Orbit radius (world units) for the resting state. Scaled from the place
 * diagonal so a wide island orbits further out than a tight harbor, with a small
 * floor so a point place still orbits at a readable standoff.
 */
function orbitRadius(place: Place): number {
  const diagM = geoDiagonalMeters(place.bounds);
  return Math.max(diagM * 0.0008, 12);
}

// Local linear-fog check mirroring the atmosphere module's predicate, so the
// controller can read a resting `far` without importing three.
function isLinearFog(fog: FogTarget): fog is Extract<FogTarget, { far: number }> {
  return (fog as { isFog?: boolean }).isFog === true;
}
