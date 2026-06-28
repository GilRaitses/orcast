"use client";

// W1 Camera Director sandbox, visual-remediation pass. Runs the East Sound
// choreography from the visual program charter against the real full-extent
// CUDEM tileset AND composes the SAME realism stack the live SalishScene uses so
// the journey reads as a believable Salish Sea fly-through:
//   - RealismRig    -> applyRealism(scene, {...}): sun + ambient + hemisphere
//                      lights, distance fog, and the sky/background color.
//   - Water2Rig     -> makeWater2({...}): the depth-driven Beer-Lambert ocean
//                      (per-frame depth pre-pass with the water hidden, run BEFORE
//                      r3f's auto-render), so shallows reveal terrain and only
//                      deep channels read as solid blue.
//   - pinned midday sun (SCENE_TIME) so the CUDEM terrain is lit, not flat.
//   - atmosphere transitions (rollInFog as a soft cut mask, descentLighting on the
//      descent beat) composed OVER the realism rig, never editing realism/ internals.
//
// Choreography (re-cut so the POV never dunks into the water):
//   1. flyTo a wide/high establishing shot over Rosario Strait / the San Juans.
//   2. descendTo a cruising altitude that stays well above the water.
//   3. followPath the Anacortes -> Orcas ferry route at a readable altitude,
//      looking forward-and-slightly-down toward the destination.
//   4. orbit East Sound as the slow resting state.
//
// The director (web/lib/scene/camera) is pure three.js and holds no React state;
// this scene attaches the live camera + OrbitControls + tiles group onto its
// handle and advances it once per frame inside useFrame. A hard altitude clamp in
// the director guarantees the camera never drops below the surface again.

import { useEffect, useMemo, useRef, useState, type MutableRefObject } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import { useTilesLayer } from "@/lib/scene/tiles";
import {
  applyRealism,
  makeSun,
  skyColor,
  type RealismHandle,
} from "@/app/components/scene/realism";
import { makeWater2, type Water2Handle } from "@/lib/scene/water2";
import {
  rollInFog,
  descentLighting,
  type TweenHandle,
} from "@/lib/scene/atmosphere/transition";
import { SCENE_WIDTH, sceneDepth, type HeightmapBounds } from "@/lib/sceneIntent";
import {
  createCameraDirector,
  type CameraDirector,
  type CameraDirectorHandle,
  type CameraState,
  type LatLngAlt,
  type OrbitHandle,
} from "@/lib/scene/camera";

const FULL_TILESET_URL =
  "https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full/tileset.json";

// Served full-extent tileset footprint (identical to SalishScene's TILESET_BOUNDS
// and the substrate field bounds). Used for project/unproject so camera targets
// share the live scene's frame.
const TILESET_BOUNDS: HeightmapBounds = {
  min_lat: 48.4,
  max_lat: 48.7,
  min_lng: -123.25,
  max_lng: -122.75,
};

const SCENE_DEPTH = sceneDepth(TILESET_BOUNDS);

// Daytime sun instant, pinned to match SalishScene so the terrain is lit (about
// 1 PM PDT = 20:00 UTC). makeSun defaults to "now", which is night for much of a
// session and leaves the CUDEM terrain near-black.
const SCENE_TIME = new Date("2026-06-27T20:00:00Z");

// Calmer sea than the live scene default (0.32). From altitude a lower wave
// amplitude reads as a believable open-water surface and removes any chance of a
// towering crest clipping the low cruising camera.
const WATER_AMPLITUDE = 0.18;

// East Sound choreography, clamped to the served bounds (Anacortes itself sits
// just east of the tileset's -122.75 edge, so the route starts in Rosario Strait
// at the eastern edge and runs west-then-north through Harney Channel into East
// Sound). Coordinates are approximate ferry-lane waypoints, not a surveyed track.
const ESTABLISH: LatLngAlt = { lat: 48.56, lng: -122.86, altitudeMeters: 2400 };
const FERRY_ROUTE: LatLngAlt[] = [
  { lat: 48.5, lng: -122.78 },
  { lat: 48.52, lng: -122.83 },
  { lat: 48.55, lng: -122.87 },
  { lat: 48.58, lng: -122.9 },
  { lat: 48.62, lng: -122.905 },
  { lat: 48.66, lng: -122.905 },
];
// Altitudes ease down along the route (above the never-below-80 m floor) so the
// look-ahead point sits slightly lower than the eye: a forward-and-slightly-down
// gaze toward the destination, descending gently as the ferry nears Orcas.
const FERRY_ALTS_M = [240, 226, 212, 200, 190, 182];
const FERRY_ROUTE_ALT: LatLngAlt[] = FERRY_ROUTE.map((p, i) => ({
  ...p,
  altitudeMeters: FERRY_ALTS_M[i],
}));
const EAST_SOUND_CENTER = { lat: 48.66, lng: -122.905 };

// Cruising / settle altitudes (metres above sea level). All well above the hard
// no-dunk clamp in the director.
const DESCENT_ALT_M = 230;
const ORBIT_ALT_M = 820;

// Approx geographic half-diagonal of the served extent, used to derive a
// fit-accurate world-units-per-metre once the tileset's world bounding sphere is
// known, so altitudes match the actual (uniformly) fitted terrain scale.
function geoRadiusMeters(b: HeightmapBounds): number {
  const latSpanM = (b.max_lat - b.min_lat) * 111_000;
  const lngSpanM = (b.max_lng - b.min_lng) * 73_600;
  return 0.5 * Math.hypot(latSpanM, lngSpanM);
}

// Downward raycast surface probe over the streamed tile geometry (mirrors
// SalishScene.surfaceYAt). Lets ground look-at points sit on the real surface and
// feeds the director's no-dunk altitude clamp.
function makeSurfaceProbe(group: THREE.Object3D | null) {
  const ray = new THREE.Raycaster();
  const origin = new THREE.Vector3();
  const down = new THREE.Vector3(0, -1, 0);
  return (x: number, z: number): number | null => {
    if (!group) return null;
    origin.set(x, 1e5, z);
    ray.set(origin, down);
    ray.near = 0;
    ray.far = 2e5;
    const hits = ray.intersectObject(group, true);
    return hits.length ? hits[0].point.y : null;
  };
}

// Imperative realism mount (lights + atmosphere/fog + sky), composed exactly like
// SalishScene's RealismRig. water:false because the depth-driven Water2Rig below
// replaces the flat plane. The created handle is published to realismHandleRef so
// the atmosphere transitions can drive its lights without touching realism/.
function RealismRig({
  depth,
  realismHandleRef,
}: {
  depth: number;
  realismHandleRef: MutableRefObject<RealismHandle | null>;
}) {
  const scene = useThree((s) => s.scene);
  const localRef = useRef<RealismHandle | null>(null);
  useEffect(() => {
    const handle = applyRealism(scene, {
      date: SCENE_TIME,
      lat: 48.5,
      lng: -123,
      water: false,
      background: true,
      fog: true,
    });
    localRef.current = handle;
    realismHandleRef.current = handle;
    return () => {
      handle.dispose();
      if (realismHandleRef.current === handle) realismHandleRef.current = null;
      localRef.current = null;
    };
  }, [scene, depth, realismHandleRef]);
  useFrame((state) => localRef.current?.update(state.clock.elapsedTime));
  return null;
}

// Depth-driven ocean (water2), composed exactly like SalishScene's Water2Rig:
// each frame it runs the opaque-scene depth pre-pass (water hidden) BEFORE r3f's
// automatic render so the shader can read the seabed depth under every fragment.
// Mounted AFTER DirectorRig so the pre-pass sees the camera the director has
// already positioned this frame. Priority-0 useFrame keeps the auto-render on.
function Water2Rig({ depth }: { depth: number }) {
  const scene = useThree((s) => s.scene);
  const gl = useThree((s) => s.gl);
  const camera = useThree((s) => s.camera);
  const size = useThree((s) => s.size);
  const handleRef = useRef<Water2Handle | null>(null);

  const sun = useMemo(() => makeSun(SCENE_TIME, 48.5, -123), []);

  useEffect(() => {
    const handle = makeWater2({
      width: SCENE_WIDTH * 1.6,
      depth: depth * 1.6,
      level: 0,
      amplitude: WATER_AMPLITUDE,
      sunDirection: sun.direction,
      skyColor: skyColor(sun.elevationDeg),
    });
    handleRef.current = handle;
    scene.add(handle.mesh);
    return () => {
      scene.remove(handle.mesh);
      handle.dispose();
      handleRef.current = null;
    };
  }, [scene, depth, sun]);

  useEffect(() => {
    handleRef.current?.setSize(size.width, size.height, gl.getPixelRatio());
  }, [size, gl]);

  useFrame((state) => {
    const handle = handleRef.current;
    if (!handle) return;
    handle.renderDepthPrepass(gl, scene, camera as THREE.PerspectiveCamera);
    handle.update(state.clock.elapsedTime, camera);
  });

  return null;
}

function DirectorRig({
  handleRef,
  directorRef,
  orbitRef,
  realismHandleRef,
}: {
  handleRef: MutableRefObject<CameraDirectorHandle>;
  directorRef: MutableRefObject<CameraDirector | null>;
  orbitRef: MutableRefObject<OrbitHandle | null>;
  realismHandleRef: MutableRefObject<RealismHandle | null>;
}) {
  const scene = useThree((s) => s.scene);
  const camera = useThree((s) => s.camera);
  const controlsRef = useRef<React.ElementRef<typeof OrbitControls> | null>(null);
  const startedRef = useRef(false);
  const transitionsRef = useRef<TweenHandle[]>([]);
  const [fitRadius, setFitRadius] = useState<number | null>(null);

  // Create the director once, bound to the shared mutable handle.
  if (!directorRef.current) {
    directorRef.current = createCameraDirector(handleRef.current);
  }

  const tiles = useTilesLayer({
    url: FULL_TILESET_URL,
    groupRotationX: -Math.PI / 2,
    fitScaleToWidth: SCENE_WIDTH,
    errorTarget: 16,
    enableShadows: false,
    onFit: (sphere) => {
      setFitRadius(sphere.radius);
      const handle = handleRef.current;
      handle.fitRadius = sphere.radius;
      handle.worldUnitsPerMeter = sphere.radius / geoRadiusMeters(TILESET_BOUNDS);
      if (camera instanceof THREE.PerspectiveCamera) {
        camera.near = Math.max(sphere.radius / 2000, 0.01);
        camera.far = sphere.radius * 100;
        camera.updateProjectionMatrix();
      }
    },
  });

  // Keep the handle's live references current every frame, advance the director
  // (positions the camera), then advance any active atmosphere transitions. No
  // React state is touched in this hot loop. Runs BEFORE Water2Rig's pre-pass.
  useFrame((_state, delta) => {
    const handle = handleRef.current;
    handle.camera = camera as THREE.PerspectiveCamera;
    handle.controls = controlsRef.current ?? null;
    handle.group = tiles?.group ?? null;
    handle.getSurfaceY = makeSurfaceProbe(tiles?.group ?? null);
    directorRef.current?.update(delta);

    const list = transitionsRef.current;
    for (let i = list.length - 1; i >= 0; i--) {
      if (!list[i].update(delta * 1000)) list.splice(i, 1);
    }
  });

  // Once the tileset has fitted (radius known, terrain streaming), run the
  // choreography exactly once, with the atmosphere transitions wired in.
  useEffect(() => {
    if (fitRadius == null || startedRef.current) return;
    const director = directorRef.current;
    if (!director) return;
    startedRef.current = true;

    // Hand the camera fully to the director for the scripted journey.
    if (controlsRef.current) controlsRef.current.enabled = false;

    const orbitRadius = Math.max(fitRadius * 0.4, 12);
    let cancelled = false;
    const push = (t: TweenHandle) => transitionsRef.current.push(t);

    (async () => {
      const fog = scene.fog instanceof THREE.Fog ? scene.fog : null;
      const baseFar = fog ? fog.far : 0;

      // Establishing: roll fog IN as a soft mask over the opening cut, then a
      // wide/high pass over Rosario Strait and the San Juans.
      if (fog) push(rollInFog(1400, fog, { far: baseFar * 0.5 }));
      await director.flyTo(ESTABLISH, {
        durationMs: 4500,
        subject: "San Juan Islands",
        easing: "easeInOutCubic",
      });
      if (cancelled) return;

      // Descent: clear the fog back out and ease the lighting toward the
      // descent-to-water look while the camera drops to cruising altitude.
      if (fog) push(rollInFog(3200, fog, { far: baseFar }));
      const realism = realismHandleRef.current;
      if (realism) {
        push(
          descentLighting(3200, [realism.sunLight, realism.ambientLight], {
            intensity: realism.sunLight.intensity * 0.92,
            elevationDeg: 22,
          }),
        );
      }
      await director.descendTo(DESCENT_ALT_M, {
        durationMs: 4500,
        subject: "approach",
        easing: "easeOutCubic",
      });
      if (cancelled) return;

      // Follow: fly the ferry route at a readable altitude, looking ahead and
      // slightly down toward the destination. Slow and gentle.
      await director.followPath(FERRY_ROUTE_ALT, {
        durationMs: 17000,
        subject: "Anacortes to Orcas ferry",
        lookAhead: 0.1,
        easing: "easeInOutSine",
      });
      if (cancelled) return;

      // Settle: a slow high orbit framing East Sound, the surrounding islands,
      // and the water as the resting state.
      orbitRef.current = director.orbit(EAST_SOUND_CENTER, orbitRadius, 0.05, {
        subject: "East Sound",
        altitudeMeters: ORBIT_ALT_M,
      });
    })();

    return () => {
      cancelled = true;
      transitionsRef.current.forEach((t) => t.cancel());
      transitionsRef.current = [];
      orbitRef.current?.stop();
      director.stop();
    };
  }, [fitRadius, directorRef, orbitRef, realismHandleRef, scene]);

  return (
    <>
      {tiles && <primitive object={tiles.group} />}
      {/* makeDefault so the tiles layer culls against this camera; the director
          drives it while enabled=false during the scripted journey. */}
      <OrbitControls ref={controlsRef} makeDefault enablePan enableZoom maxPolarAngle={Math.PI / 2.02} />
    </>
  );
}

function StateHud({ directorRef }: { directorRef: MutableRefObject<CameraDirector | null> }) {
  const [state, setState] = useState<CameraState | null>(null);
  useEffect(() => {
    const id = window.setInterval(() => {
      setState(directorRef.current?.getState() ?? null);
    }, 250);
    return () => window.clearInterval(id);
  }, [directorRef]);

  return (
    <div
      style={{
        position: "absolute",
        left: 12,
        bottom: 12,
        padding: "10px 14px",
        borderRadius: 8,
        font: "11px/1.5 ui-monospace, monospace",
        color: "#cfe6ff",
        background: "rgba(8,38,61,0.82)",
        width: 300,
        pointerEvents: "none",
      }}
    >
      <strong>Camera Director (W1)</strong> East Sound journey.
      <div style={{ marginTop: 6 }}>
        subject: {state?.subject ?? "-"}
        <br />
        altitude: {state ? `${state.altitude.toFixed(0)} m` : "-"}
        <br />
        target: {state?.target ? `${state.target.lat.toFixed(4)}, ${state.target.lng.toFixed(4)}` : "-"}
        <br />
        orbiting: {state ? (state.isOrbiting ? "yes" : "no") : "-"}
      </div>
    </div>
  );
}

export default function JourneyScene() {
  // Shared mutable handle the scene attaches the camera/controls/tiles onto. The
  // director reads it lazily each frame (no React coupling in the hot loop).
  const handleRef = useRef<CameraDirectorHandle>({
    camera: null,
    controls: null,
    bounds: TILESET_BOUNDS,
    sceneDepth: SCENE_DEPTH,
    group: null,
    fitRadius: null,
    getSurfaceY: null,
  });
  const directorRef = useRef<CameraDirector | null>(null);
  const orbitRef = useRef<OrbitHandle | null>(null);
  const realismHandleRef = useRef<RealismHandle | null>(null);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <Canvas
        camera={{ position: [0, 80, 120], fov: 45, near: 1, far: 800 }}
        style={{ width: "100%", height: "100%", background: "linear-gradient(#0b1f33,#08263d)" }}
        onCreated={({ gl }) => gl.setClearColor("#08263d")}
      >
        {/* DirectorRig FIRST so it positions the camera before Water2Rig's
            depth pre-pass and the auto-render this frame. */}
        <DirectorRig
          handleRef={handleRef}
          directorRef={directorRef}
          orbitRef={orbitRef}
          realismHandleRef={realismHandleRef}
        />
        <RealismRig depth={SCENE_DEPTH} realismHandleRef={realismHandleRef} />
        <Water2Rig depth={SCENE_DEPTH} />
      </Canvas>
      <StateHud directorRef={directorRef} />
    </div>
  );
}
