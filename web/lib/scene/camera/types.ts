// Public type surface for the cinematic Camera Director (W1 Agent A).
//
// These types are deliberately framework-free: the director is pure three.js
// driven and is advanced by a per-frame tick, so nothing here imports React or
// react-three-fiber. The scene (W2 convergence) attaches a live camera + controls
// onto a mutable handle and calls `update(dt)` each frame; no React state lives in
// the hot loop.

import type * as THREE from "three";
import type { HeightmapBounds } from "@/lib/sceneIntent";

/** A geographic point in WGS84 degrees. */
export interface LatLng {
  lat: number;
  lng: number;
}

/** A geographic point with an optional altitude above sea level (Y=0), metres. */
export interface LatLngAlt extends LatLng {
  altitudeMeters?: number;
}

/** Named easing curves resolvable by `flyTo`/`descendTo`/`followPath` options. */
export type EasingName =
  | "linear"
  | "easeInQuad"
  | "easeOutQuad"
  | "easeInOutQuad"
  | "easeInCubic"
  | "easeOutCubic"
  | "easeInOutCubic"
  | "easeInOutSine";

/** A raw easing function mapping a normalised t in [0,1] to an eased [0,1]. */
export type EasingFn = (t: number) => number;

/** Options shared by the one-shot eased moves. */
export interface MoveOptions {
  /** Animation length in milliseconds. Each move has a sensible default. */
  durationMs?: number;
  /** Named easing or a custom function. Defaults to `easeInOutCubic`. */
  easing?: EasingName | EasingFn;
  /**
   * Human-readable subject label surfaced by `getState().subject`. Lets the
   * intent transducer report what the camera is dwelling on. Unset keeps the
   * previously set subject.
   */
  subject?: string;
}

/** Options for `followPath`. */
export interface FollowPathOptions extends MoveOptions {
  /**
   * How far ahead along the curve the look-at point leads the eye, as a fraction
   * of the whole path in [0,1]. Larger = the camera looks further down the route.
   * Defaults to 0.06.
   */
  lookAhead?: number;
  /** Treat the points as a closed loop. Defaults to false. */
  closed?: boolean;
}

/** Options for `orbit`. */
export interface OrbitOptions {
  /** Subject label for `getState().subject` while orbiting. */
  subject?: string;
  /**
   * Camera altitude above sea level during the orbit, metres. Defaults to the
   * camera's current altitude when the orbit starts.
   */
  altitudeMeters?: number;
}

/** Handle returned by `orbit`; the orbit runs until `stop()` is called. */
export interface OrbitHandle {
  /** End this orbit. Safe to call repeatedly. */
  stop: () => void;
  /** True while this orbit is the director's active animation. */
  isActive: () => boolean;
}

/** Snapshot read by the intent transducer; never mutated by the caller. */
export interface CameraState {
  /** Current look-at point as geographic coordinates, or null before attach. */
  target: LatLng | null;
  /** Camera altitude above sea level (Y=0) in metres. */
  altitude: number;
  /** Last subject label set by a move/orbit, or null. */
  subject: string | null;
  /** True while a continuous orbit is running. */
  isOrbiting: boolean;
}

/**
 * Minimal OrbitControls surface the director drives. Both three's stock
 * `OrbitControls` and drei's `<OrbitControls>` instance satisfy this, so the
 * director needs no dependency on either.
 */
export interface ControlsLike {
  target: THREE.Vector3;
  update: () => void;
  enabled?: boolean;
}

/**
 * Mutable attachment point wired by the scene. The director reads these every
 * frame, so the scene can attach the camera/controls/tiles AFTER the director is
 * created (e.g. once the r3f canvas and tileset exist). All geo<->world mapping
 * reuses the `SalishScene` conventions:
 *  - horizontal: `projectToScene` / `unprojectFromScene` over `bounds` + `sceneDepth`
 *  - the group's world position recentres world<->scene (matches `worldPointToLatLng`)
 */
export interface CameraDirectorHandle {
  /** The live perspective camera, or null until attached. */
  camera: THREE.PerspectiveCamera | null;
  /** The OrbitControls instance, or null. When present it is driven + updated. */
  controls: ControlsLike | null;
  /** Geographic bounds of the served tileset extent (the `SalishScene` frame). */
  bounds: HeightmapBounds;
  /** Scene-Z span, i.e. `sceneDepth(bounds)` from `sceneIntent.ts`. */
  sceneDepth: number;
  /** `tiles.group`; its world position recentres world<->scene. Optional. */
  group?: THREE.Object3D | null;
  /**
   * World units per metre for altitude mapping. Optional override; when unset the
   * director derives it from `bounds` to match the `projectToScene` horizontal
   * scale. The scene may set a fit-accurate value once the tileset has fitted.
   */
  worldUnitsPerMeter?: number;
  /** World-space fit radius (from `useTilesLayer.onFit`), used for framing. */
  fitRadius?: number | null;
  /**
   * Optional terrain probe: given scene-world X/Z, return the tile-surface Y or
   * null on a miss. When provided, ground look-at points sit on the surface.
   */
  getSurfaceY?: ((x: number, z: number) => number | null) | null;
}

/** The cinematic camera controller. */
export interface CameraDirector {
  /** Ease the camera to frame a geographic target (optionally at an altitude). */
  flyTo(target: LatLngAlt, opts?: MoveOptions): Promise<void>;
  /** Ease the camera down toward sea level to the given altitude (metres). */
  descendTo(altitudeMeters: number, opts?: MoveOptions): Promise<void>;
  /** Fly the camera along a geographic path, looking ahead down the route. */
  followPath(points: LatLngAlt[], opts?: FollowPathOptions): Promise<void>;
  /** Begin a continuous orbit around a centre; runs until the handle stops. */
  orbit(center: LatLng, radius: number, speed: number, opts?: OrbitOptions): OrbitHandle;
  /** Stop any active animation (eased move or orbit). */
  stop(): void;
  /** Read the current camera state for the intent transducer. */
  getState(): CameraState;
  /** Advance the active animation by `deltaSeconds`. Call once per frame. */
  update(deltaSeconds: number): void;
  /** True while an eased move or orbit is active. */
  isAnimating(): boolean;
}
