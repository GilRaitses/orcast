// Cinematic Camera Director (W1 Agent A) for the orcast console.
//
// A pure three.js camera-animation controller. It is created once with a mutable
// handle that the scene fills in (camera + OrbitControls + tiles group). It holds
// NO React state and runs NO render loop of its own: the scene advances it by
// calling `update(deltaSeconds)` inside its per-frame tick (e.g. r3f `useFrame`).
//
// Geo<->world mapping reuses the SalishScene conventions verbatim, importing
// `projectToScene` / `unprojectFromScene` (NOT copies) so the camera frame can
// never drift from the convergence-file definition:
//   - horizontal: scene X/Z = projectToScene(lat,lng,bounds,sceneDepth) + group origin
//   - vertical:   world Y = altitudeMeters * worldUnitsPerMeter (sea level = Y=0)
// Framing distances reuse the sandbox bounding-sphere fit idea: the fit radius
// (from useTilesLayer.onFit) sets the default standoff, exactly as
// TilesSandboxScene positions the camera at center + dir * radius * k.

import * as THREE from "three";
import {
  SCENE_WIDTH,
  projectToScene,
  unprojectFromScene,
} from "@/lib/sceneIntent";
import { resolveEasing } from "./easing";
import type {
  CameraDirector,
  CameraDirectorHandle,
  CameraState,
  FollowPathOptions,
  LatLng,
  LatLngAlt,
  MoveOptions,
  OrbitHandle,
  OrbitOptions,
} from "./types";

// Metres per degree of longitude near 48.5N. Matches the constant baked into
// `sceneDepth` in sceneIntent.ts (73.6 km/deg) so the altitude scale lines up
// with the horizontal projectToScene scale by default.
const METERS_PER_DEG_LNG = 73_600;

const DEFAULT_FLY_MS = 2500;
const DEFAULT_DESCEND_MS = 3000;
const DEFAULT_FOLLOW_MS = 6000;
const DEFAULT_LOOK_AHEAD = 0.06;

// Hard no-dunk safety clamp. The camera eye may never sit closer to the surface
// than this. Two floors, whichever is higher: a metric clearance (metres above
// the higher of the water plane Y=0 and the probed tile surface) and a minimum
// world-unit headroom that always clears the displaced water crests (water2's
// wave amplitude is ~0.18-0.32 scene units), so a low fly-by can never plunge
// below a wave even where the metric clearance maps to a tiny world distance.
const MIN_ALT_ABOVE_SURFACE_METERS = 40;
const MIN_WAVE_HEADROOM_UNITS = 0.5;

// An active eased move: advanced by elapsed time, settles its promise on finish.
interface ActiveTween {
  kind: "tween";
  durationMs: number;
  elapsedMs: number;
  ease: (t: number) => number;
  apply: (p: number) => void;
  settle: () => void;
}

// An active continuous orbit: advanced by angular speed until stopped.
interface ActiveOrbit {
  kind: "orbit";
  advance: (dt: number) => void;
  settle: () => void;
}

type Active = ActiveTween | ActiveOrbit;

/**
 * Create a Camera Director bound to a mutable handle. The handle's `camera`,
 * `controls`, `group`, `fitRadius`, and `worldUnitsPerMeter` may be attached or
 * changed after creation; the director reads them lazily each frame.
 */
export function createCameraDirector(
  handle: CameraDirectorHandle,
): CameraDirector {
  // Current look-at point in world space. Kept in sync with controls.target.
  const lookAt = new THREE.Vector3();
  let hasLookAt = false;
  let subject: string | null = null;
  let active: Active | null = null;

  // Scratch objects so the hot loop allocates nothing.
  const scratchOrigin = new THREE.Vector3();
  const scratchDir = new THREE.Vector3();

  // --- geometry helpers -----------------------------------------------------

  function worldUnitsPerMeter(): number {
    if (typeof handle.worldUnitsPerMeter === "number" && handle.worldUnitsPerMeter > 0) {
      return handle.worldUnitsPerMeter;
    }
    const lngSpan = handle.bounds.max_lng - handle.bounds.min_lng;
    const widthMeters = Math.abs(lngSpan) * METERS_PER_DEG_LNG;
    return widthMeters > 0 ? SCENE_WIDTH / widthMeters : 1;
  }

  function groupOrigin(): THREE.Vector3 {
    if (handle.group) return handle.group.getWorldPosition(scratchOrigin);
    return scratchOrigin.set(0, 0, 0);
  }

  function altToWorldY(altitudeMeters: number): number {
    return altitudeMeters * worldUnitsPerMeter();
  }

  function worldYToAlt(y: number): number {
    const s = worldUnitsPerMeter();
    return s > 0 ? y / s : 0;
  }

  // Ground look-at point: scene XZ from projectToScene (+ group origin), Y on the
  // tile surface when a probe is available, else sea level.
  function groundWorld(lat: number, lng: number, out: THREE.Vector3): THREE.Vector3 {
    const [sx, sz] = projectToScene(lat, lng, handle.bounds, handle.sceneDepth);
    const origin = groupOrigin();
    const wx = sx + origin.x;
    const wz = sz + origin.z;
    const surfaceY = handle.getSurfaceY ? handle.getSurfaceY(wx, wz) : null;
    return out.set(wx, surfaceY != null ? surfaceY : 0, wz);
  }

  // Full world point honouring an explicit altitude (above sea level) when given.
  function pointWorld(p: LatLngAlt, out: THREE.Vector3): THREE.Vector3 {
    groundWorld(p.lat, p.lng, out);
    if (typeof p.altitudeMeters === "number") out.y = altToWorldY(p.altitudeMeters);
    return out;
  }

  function fitRadius(): number {
    return typeof handle.fitRadius === "number" && handle.fitRadius > 0
      ? handle.fitRadius
      : SCENE_WIDTH / 2;
  }

  // Raise the camera eye to the no-dunk floor if any move/orbit would drop it
  // below the surface. Reads the water plane (scene Y=0) and, when a terrain
  // probe is attached, the tile surface under the eye XZ; the floor is the higher
  // of the two plus a clearance. Additive: it only ever lifts the eye, never
  // changes the look-at, easing, or getState contract.
  function enforceAltitudeClamp(): void {
    const cam = handle.camera;
    if (!cam) return;
    let surfaceY = 0; // water surface plane
    if (handle.getSurfaceY) {
      const s = handle.getSurfaceY(cam.position.x, cam.position.z);
      if (typeof s === "number" && Number.isFinite(s) && s > surfaceY) surfaceY = s;
    }
    const metricClear = MIN_ALT_ABOVE_SURFACE_METERS * worldUnitsPerMeter();
    const minY = surfaceY + Math.max(metricClear, MIN_WAVE_HEADROOM_UNITS);
    if (cam.position.y < minY) cam.position.y = minY;
  }

  // --- controls plumbing ----------------------------------------------------

  function pushLookAt() {
    const cam = handle.camera;
    if (!cam) return;
    if (handle.controls) {
      handle.controls.target.copy(lookAt);
      handle.controls.update();
    } else {
      cam.lookAt(lookAt);
    }
  }

  // Stop the active animation without resolving callers that awaited it being
  // superseded (callers awaiting a move that is replaced simply resolve, so a
  // descend->follow->orbit chain never deadlocks).
  function clearActive() {
    if (active) {
      const a = active;
      active = null;
      a.settle();
    }
  }

  function beginTween(
    durationMs: number,
    easing: MoveOptions["easing"],
    apply: (p: number) => void,
    subjectOpt?: string,
  ): Promise<void> {
    clearActive();
    if (subjectOpt) subject = subjectOpt;
    if (!handle.camera) {
      // No camera attached yet: apply the end state once so the scene starts framed.
      apply(1);
      pushLookAt();
      return Promise.resolve();
    }
    return new Promise<void>((resolve) => {
      // Run one frame at p=0 immediately so the very first rendered frame already
      // shows the start of the move rather than the prior pose.
      apply(0);
      enforceAltitudeClamp();
      pushLookAt();
      active = {
        kind: "tween",
        durationMs: Math.max(1, durationMs),
        elapsedMs: 0,
        ease: resolveEasing(easing),
        apply,
        settle: resolve,
      };
    });
  }

  // --- public moves ---------------------------------------------------------

  function flyTo(target: LatLngAlt, opts: MoveOptions = {}): Promise<void> {
    const cam = handle.camera;
    const endTarget = new THREE.Vector3();
    groundWorld(target.lat, target.lng, endTarget);

    const startEye = new THREE.Vector3();
    const startTarget = lookAt.clone();
    const endEye = new THREE.Vector3();

    if (cam) startEye.copy(cam.position);
    else startEye.copy(endTarget).add(new THREE.Vector3(1, 0.8, 1).normalize().multiplyScalar(fitRadius() * 2));
    if (!hasLookAt) startTarget.copy(endTarget);

    // Keep the current viewing direction for continuity; fall back to a pleasant
    // default 3/4 angle if eye and target coincide.
    scratchDir.copy(startEye).sub(startTarget);
    if (scratchDir.lengthSq() < 1e-6) scratchDir.set(1, 0.8, 1);
    scratchDir.normalize();

    if (typeof target.altitudeMeters === "number") {
      // Frame from the given altitude: keep the horizontal heading, set eye Y to
      // the altitude, and stand off horizontally enough to keep a forward pitch.
      const ay = altToWorldY(target.altitudeMeters);
      const horiz = new THREE.Vector3(scratchDir.x, 0, scratchDir.z);
      if (horiz.lengthSq() < 1e-6) horiz.set(0, 0, 1);
      horiz.normalize();
      const horizDist = Math.max(ay * 1.5, fitRadius() * 0.12);
      endEye.set(
        endTarget.x + horiz.x * horizDist,
        ay,
        endTarget.z + horiz.z * horizDist,
      );
    } else {
      const dist = fitRadius() * 1.6;
      endEye.copy(endTarget).addScaledVector(scratchDir, dist);
    }

    return beginTween(
      opts.durationMs ?? DEFAULT_FLY_MS,
      opts.easing,
      (p) => {
        if (cam) cam.position.lerpVectors(startEye, endEye, p);
        lookAt.lerpVectors(startTarget, endTarget, p);
        hasLookAt = true;
      },
      opts.subject,
    );
  }

  function descendTo(altitudeMeters: number, opts: MoveOptions = {}): Promise<void> {
    const cam = handle.camera;
    const ay = altToWorldY(altitudeMeters);
    const startEye = new THREE.Vector3();
    if (cam) startEye.copy(cam.position);
    else startEye.set(0, fitRadius(), fitRadius());

    const target = hasLookAt ? lookAt.clone() : groupOrigin().clone();

    // Pull the eye in over the target as it drops, keeping the current heading,
    // so the descent ends low and close rather than far and high.
    const horiz = new THREE.Vector3(startEye.x - target.x, 0, startEye.z - target.z);
    const hlen = horiz.length();
    if (hlen < 1e-6) horiz.set(0, 0, 1);
    horiz.normalize();
    const horizDist = Math.max(ay * 2.0, hlen * 0.25);
    const endEye = new THREE.Vector3(
      target.x + horiz.x * horizDist,
      ay,
      target.z + horiz.z * horizDist,
    );

    return beginTween(
      opts.durationMs ?? DEFAULT_DESCEND_MS,
      opts.easing,
      (p) => {
        if (cam) cam.position.lerpVectors(startEye, endEye, p);
        lookAt.copy(target);
        hasLookAt = true;
      },
      opts.subject,
    );
  }

  function followPath(points: LatLngAlt[], opts: FollowPathOptions = {}): Promise<void> {
    const cam = handle.camera;
    if (points.length < 2) {
      // Degenerate path: behave like flyTo the single point (or no-op when empty).
      if (points.length === 1) return flyTo(points[0], opts);
      return Promise.resolve();
    }

    const closed = opts.closed ?? false;
    const lookAhead = Math.min(0.5, Math.max(0, opts.lookAhead ?? DEFAULT_LOOK_AHEAD));
    const defaultAltM = cam ? worldYToAlt(cam.position.y) || 1 : 1;

    const worldPts = points.map((p) => {
      const v = new THREE.Vector3();
      groundWorld(p.lat, p.lng, v);
      v.y = altToWorldY(
        typeof p.altitudeMeters === "number" ? p.altitudeMeters : defaultAltM,
      );
      return v;
    });

    const curve = new THREE.CatmullRomCurve3(worldPts, closed, "catmullrom", 0.5);
    const eye = new THREE.Vector3();
    const ahead = new THREE.Vector3();
    const tangent = new THREE.Vector3();

    return beginTween(
      opts.durationMs ?? DEFAULT_FOLLOW_MS,
      opts.easing,
      (p) => {
        const u = THREE.MathUtils.clamp(p, 0, 1);
        curve.getPointAt(u, eye);
        const ua = closed ? (u + lookAhead) % 1 : Math.min(1, u + lookAhead);
        curve.getPointAt(ua, ahead);
        if (eye.distanceToSquared(ahead) < 1e-6) {
          // Near the end of an open curve the look-at collapses onto the eye; use
          // the path tangent so the camera keeps facing down-route.
          curve.getTangentAt(u, tangent);
          ahead.copy(eye).add(tangent);
        }
        if (cam) cam.position.copy(eye);
        lookAt.copy(ahead);
        hasLookAt = true;
      },
      opts.subject,
    );
  }

  function orbit(
    center: LatLng,
    radius: number,
    speed: number,
    opts: OrbitOptions = {},
  ): OrbitHandle {
    clearActive();
    if (opts.subject) subject = opts.subject;

    const centerWorld = new THREE.Vector3();
    groundWorld(center.lat, center.lng, centerWorld);
    const cam = handle.camera;

    const ay =
      typeof opts.altitudeMeters === "number"
        ? altToWorldY(opts.altitudeMeters)
        : cam
          ? cam.position.y
          : altToWorldY(400);

    // Start the orbit at the camera's current bearing so it begins without a jump.
    let angle = 0;
    if (cam) angle = Math.atan2(cam.position.z - centerWorld.z, cam.position.x - centerWorld.x);

    const orbitState: ActiveOrbit = {
      kind: "orbit",
      advance: (dt) => {
        angle += speed * dt;
        if (cam) {
          cam.position.set(
            centerWorld.x + Math.cos(angle) * radius,
            ay,
            centerWorld.z + Math.sin(angle) * radius,
          );
          enforceAltitudeClamp();
        }
        lookAt.copy(centerWorld);
        hasLookAt = true;
        pushLookAt();
      },
      settle: () => {},
    };
    active = orbitState;

    // Place the camera immediately so the first frame is already on the orbit.
    orbitState.advance(0);

    return {
      stop: () => {
        if (active === orbitState) active = null;
      },
      isActive: () => active === orbitState,
    };
  }

  function stop(): void {
    clearActive();
  }

  function getState(): CameraState {
    const cam = handle.camera;
    let target: LatLng | null = null;
    if (hasLookAt) {
      const origin = groupOrigin();
      target = unprojectFromScene(
        lookAt.x - origin.x,
        lookAt.z - origin.z,
        handle.bounds,
        handle.sceneDepth,
      );
    }
    const altitude = cam ? worldYToAlt(cam.position.y) : 0;
    return {
      target,
      altitude,
      subject,
      isOrbiting: active != null && active.kind === "orbit",
    };
  }

  function update(deltaSeconds: number): void {
    if (!active) return;
    const dt = Number.isFinite(deltaSeconds) && deltaSeconds > 0 ? deltaSeconds : 0;
    if (active.kind === "orbit") {
      active.advance(dt);
      return;
    }
    active.elapsedMs += dt * 1000;
    const raw = Math.min(1, active.elapsedMs / active.durationMs);
    active.apply(active.ease(raw));
    enforceAltitudeClamp();
    pushLookAt();
    if (raw >= 1) {
      const done = active;
      active = null;
      done.settle();
    }
  }

  function isAnimating(): boolean {
    return active != null;
  }

  return {
    flyTo,
    descendTo,
    followPath,
    orbit,
    stop,
    getState,
    update,
    isAnimating,
  };
}
