"use client";

import { useCallback, useEffect, useMemo, useRef, useState, type MutableRefObject } from "react";
import { Canvas, ThreeEvent, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, Html } from "@react-three/drei";
import * as THREE from "three";
import type { TilesRenderer } from "3d-tiles-renderer";
import { getJSON } from "@/lib/api";
import {
  ORCASOUND_FALLBACK,
  SCENE_WIDTH,
  projectToScene,
  sceneDepth,
  type HeightmapBounds,
  type HydrophoneNode,
  type SceneIntent,
} from "@/lib/sceneIntent";
import { useTilesLayer } from "@/lib/scene/tiles";
import { applyRealism, makeSun, skyColor, type RealismHandle, type SunResult } from "./realism";
import {
  accelerateTilesPicking,
  worldPointToLatLng,
  PerfHud,
} from "@/lib/scene/picking";
import {
  loadSubstrate,
  sampleSubstrate,
  type SubstrateField,
} from "@/lib/scene/substrate";
import { makeWater2, type Water2Handle } from "@/lib/scene/water2";
// --- WS-INTENT viewport bridge (B.2 / B.7) imports --------------------------
// Phase-A modules mounted by the bridge, plus the camera director (W1) and the
// search affordance overlay. These are composed, never edited, by WS-INTENT.
import SearchAffordance from "./SearchAffordance";
import {
  createCameraDirector,
  type CameraDirector,
  type CameraDirectorHandle,
  type OrbitHandle,
} from "@/lib/scene/camera";
import {
  runPlaceJourney,
  type JourneyAtmosphere,
  type JourneyHandle,
} from "@/lib/journey/controller";
import type { TweenHandle } from "@/lib/scene/atmosphere/transition";
import { resolvePlace, type Place } from "@/lib/geo/gazetteer";
import { setActiveDirector, clearActiveDirector } from "@/lib/intent/transducer";
// --- WS-SCENIC mount imports (phase-B SCENIC slot, after INTENT before BATHY) -
// Two phase-A modules, composed via their public APIs only, never edited:
//   terrain stylist -> an elevation/slope biome tint on the streamed CUDEM tiles
//   decor -> a Preetham sky dome, a decorative true-scale horizon ring, fog tune
// All mounting lives in the WS-SCENIC MOUNT BLOCK below. The WS-INTENT block is
// left intact and room is left for the WS-BATHY mount that follows.
import { applyTerrainStyle } from "@/lib/scene/terrain";
import {
  makeSkyDome,
  makeHorizonRing,
  loadHorizonField,
  tuneFog,
  HORIZON_RING_URL,
  type HorizonField,
} from "@/lib/scene/decor";
// --- WS-BATHY mount imports (phase-B BATHY slot, after INTENT and SCENIC) -----
// MODELED-ONLY. Three phase-A modules, composed via their public APIs only,
// never edited:
//   style   -> buildBathyTint (cmocean deep submerged-seabed depth tint) and the
//              bathyWater2Options() depth-read water tuning for Water2Rig.
//   honesty -> attachModeledLabel (B.6: declare "modeled, not measured"), the
//              scene honesty note, and the DEFERRED measured-overlay stub which
//              fetches nothing and answers modeled everywhere (fast-follow).
// The measured BlueTopo/NONNA overlay is a deferred fast-follow; it is NOT
// fetched here. All mounting lives in the WS-BATHY MOUNT BLOCK below.
import { buildBathyTint, bathyWater2Options } from "@/lib/scene/bathy/style";
import {
  attachModeledLabel,
  BATHY_SCENE_HONESTY_NOTE,
  DEFERRED_MEASURED_OVERLAY,
} from "@/lib/scene/bathy/honesty";

// Full-extent multi-LoD tileset (85 tiles, 4 LoD levels, meshopt, validated 0
// errors). NOT the single-tile pilot; the pilot and pilot.bounds.json are dead
// for integration (WAVE2_DISPATCH S15 frame update).
const FULL_TILESET_URL =
  "https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full/tileset.json";

// Geographic footprint of the served full-extent tileset. This equals
// SAN_JUAN_BOUNDS (lat 48.40..48.70, lng -123.25..-122.75), which is the extent
// the batch-conversion agent baked (infra/3dtwin/host/WIRING-host.md +
// full.bounds.json) and is identical to the substrate field bounds. Used for
// project/unproject so beacon placement and pick->lat/lng share one frame.
// Derived from the served tileset contract, NOT the stale pilot.bounds.json.
const TILESET_BOUNDS: HeightmapBounds = {
  min_lat: 48.4,
  max_lat: 48.7,
  min_lng: -123.25,
  max_lng: -122.75,
};

// Scene-Z span for the synthetic SCENE_WIDTH frame the producers kept for W2.
// The picking module expects depth = sceneDepth(bounds); beacon XZ uses the same
// so picks and placements are mutual inverses.
const SCENE_DEPTH = sceneDepth(TILESET_BOUNDS);

// Sea-level datum reference (W2.6). useTilesLayer fits the tileset so its glTF Y
// (= NAVD88 elevation in metres, tileset has no root transform) maps to scene Y
// through the uniform scale with the vertical origin left at 0, so NAVD88 0 m
// lands at scene Y 0. Everything that keys off sea level (the water plane and
// foam/column reference, the shoreline tint band) reads this single reference
// instead of a hardcoded 0, so a future datum change is a one-line edit.
const SEA_LEVEL_Y = 0;

// --- WS-INTENT viewport bridge constants (B.2 / B.7) ------------------------
// Resting state per B.7 is a slow continuous orbit around the scene centre, the
// midpoint of TILESET_BOUNDS. A map_viewport intent (via the focus prop) or a
// place search supersedes it with runPlaceJourney, which itself settles back
// into an orbit at the resolved place. The orbit is the default and is never
// removed; these framing values are tuned at the Director acceptance gate.
const SCENE_CENTER = {
  lat: (TILESET_BOUNDS.min_lat + TILESET_BOUNDS.max_lat) / 2,
  lng: (TILESET_BOUNDS.min_lng + TILESET_BOUNDS.max_lng) / 2,
};
const RESTING_ORBIT_SPEED = 0.05; // radians/second, matches the sandbox resting orbit.
const RESTING_ORBIT_ALT_M = 2200; // metres above sea level; wide framing of the extent.

// When the tileset fails to load: true => fall back to Google Maps via SceneHost;
// false => keep realism water/lights and draw a minimal in-scene placeholder.
const FALLBACK_TO_MAPS = true;

// Daytime sun instant for the realism lighting. makeSun defaults to "now", which
// is night for much of a viewer's session and leaves the terrain near-black. Pin
// a representative Salish Sea midday (about 1 PM PDT = 20:00 UTC) so the lit
// terrain reads clearly. Time-of-day animation is a later wave (W3/W4).
const SCENE_TIME = new Date("2026-06-27T20:00:00Z");

// Perf overlay for the W2 gate (frame time, FPS, draw calls, geometry count).
// Disabled: the shipped PerfHud (web/lib/scene/picking) renders its DOM overlay
// with react-dom createPortal from inside the r3f Canvas, which the r3f
// reconciler rejects ("Span is not part of the THREE namespace"). That module is
// owned by picking-perf and is final here, so the HUD stays off and frame-rate
// evidence is captured out-of-band at the gate.
const SHOW_PERF_HUD = false;

// Cast a downward ray at a scene XZ and return the tile-surface Y, or null if
// the ray misses the loaded tile geometry (e.g. outside the streamed footprint).
function surfaceYAt(group: THREE.Object3D, x: number, z: number): number | null {
  const ray = new THREE.Raycaster(
    new THREE.Vector3(x, 1e5, z),
    new THREE.Vector3(0, -1, 0),
    0,
    2e5,
  );
  const hits = ray.intersectObject(group, true);
  return hits.length ? hits[0].point.y : null;
}

// --- WS-INTENT viewport bridge helpers (B.2 / B.7) --------------------------
// Geographic half-diagonal of the served extent (metres). Mirrors JourneyScene
// so the bridge can derive a fit-accurate world-units-per-metre once the
// tileset's world bounding sphere is known, keeping camera altitudes matched to
// the fitted terrain scale.
function geoRadiusMeters(b: HeightmapBounds): number {
  const latSpanM = (b.max_lat - b.min_lat) * 111_000;
  const lngSpanM = (b.max_lng - b.min_lng) * 73_600;
  return 0.5 * Math.hypot(latSpanM, lngSpanM);
}

// Build an ad-hoc gazetteer Place from a bare focus lat/lng (a planner
// map_viewport or a scene click carries coordinates but no place name). The
// small bounds box gives runPlaceJourney an establishing altitude and orbit
// radius to frame. Labelled "Selected location": a point of interest, not a
// surveyed place.
function placeFromFocus(lat: number, lng: number): Place {
  return {
    id: "focus",
    name: "Selected location",
    lat,
    lng,
    bounds: {
      min_lat: lat - 0.02,
      max_lat: lat + 0.02,
      min_lng: lng - 0.025,
      max_lng: lng + 0.025,
    },
    kind: "landmark",
  };
}

// Shared mutable refs the viewport bridge threads from SalishScene down to the
// in-canvas IntentDirectorRig (and back out to the search overlay via
// runPlaceRef). All director state lives behind these refs so the OrbitControls
// onStart handler and the out-of-canvas SearchAffordance can both reach it.
interface IntentBridgeRefs {
  handleRef: MutableRefObject<CameraDirectorHandle>;
  directorRef: MutableRefObject<CameraDirector | null>;
  orbitRef: MutableRefObject<OrbitHandle | null>;
  journeyRef: MutableRefObject<JourneyHandle | null>;
  transitionsRef: MutableRefObject<TweenHandle[]>;
  controlsRef: MutableRefObject<React.ElementRef<typeof OrbitControls> | null>;
  runPlaceRef: MutableRefObject<((place: Place) => void) | null>;
}

// Re-render counter that ticks each time a tile model streams in, so beacon and
// focus placement re-raycast onto progressively refined surface geometry.
function useModelLoadTick(tiles: TilesRenderer | null): number {
  const [tick, setTick] = useState(0);
  useEffect(() => {
    if (!tiles) return;
    const onLoad = () => setTick((t) => t + 1);
    tiles.addEventListener("load-model", onLoad);
    return () => tiles.removeEventListener("load-model", onLoad);
  }, [tiles]);
  return tick;
}

// Imperative realism mount (lights + atmosphere/fog + sky) per WIRING-realism.md
// Option 2. The agent-A v1 water is DISABLED here (water: false): mini-wave W2.5
// replaces it with the depth-driven water2 surface (Water2Rig below), so the
// ocean reads as land-and-sea instead of a flat uniform blue plane.
function RealismRig({
  depth,
  exposeHandle,
}: {
  depth: number;
  // WS-SCENIC: optional shared ref that surfaces the live RealismHandle (which
  // already carries sunLight/ambientLight/hemisphereLight) so the SCENIC mount
  // and a later descentLighting wave can dim the lights WITHOUT editing
  // realism/ internals. Populated on mount, cleared on unmount.
  exposeHandle?: MutableRefObject<RealismHandle | null>;
}) {
  const scene = useThree((s) => s.scene);
  const handleRef = useRef<RealismHandle | null>(null);
  useEffect(() => {
    const handle = applyRealism(scene, {
      date: SCENE_TIME,
      lat: 48.5,
      lng: -123,
      water: false,
      // WS-SCENIC: hand scene.background to the sky dome so realism's flat
      // background and the dome's horizon gradient do not fight.
      background: false,
      waterOptions: { width: SCENE_WIDTH * 1.6, depth: depth * 1.6, level: SEA_LEVEL_Y },
    });
    handleRef.current = handle;
    if (exposeHandle) exposeHandle.current = handle; // WS-SCENIC lights handle
    return () => {
      handle.dispose();
      if (exposeHandle && exposeHandle.current === handle) exposeHandle.current = null;
    };
  }, [scene, depth, exposeHandle]);
  useFrame((state) => handleRef.current?.update(state.clock.elapsedTime));
  return null;
}

// Depth-driven water (water2, mini-wave W2.5). Builds the depth-driven ocean
// surface, adds it to the scene, and each frame runs the opaque-scene depth
// pre-pass (with the water hidden) BEFORE r3f's automatic render so the water
// shader can read the seabed depth beneath every fragment. Priority-0 useFrame
// runs ahead of the auto-render and does NOT disable it. The water alpha and
// color follow the water-column thickness (Beer-Lambert), so shallows and dry
// land reveal terrain and only deep channels read as solid blue. See
// web/lib/scene/water2/ and research/R4_ocean_water_rendering.md.
function Water2Rig({ depth }: { depth: number }) {
  const scene = useThree((s) => s.scene);
  const gl = useThree((s) => s.gl);
  const camera = useThree((s) => s.camera);
  const size = useThree((s) => s.size);
  const handleRef = useRef<Water2Handle | null>(null);

  const sun = useMemo(() => makeSun(SCENE_TIME, 48.5, -123), []);

  useEffect(() => {
    // WS-BATHY: apply the A3 depth-read water tuning (bathyWater2Options) to the
    // Water2Rig option object SalishScene owns here. These are PUBLIC Water2Options
    // levers only (palette + depth color/alpha scales) so shoals read light and
    // translucent and channels read dark and opaque over the modeled seabed. The
    // live frame (width/depth/level/sun) is passed AFTER the tuning so it always
    // wins; the editor supplies sunDirection through the tuning's overrides so the
    // glitter agrees with the realism sun. The per-channel RGB absorption upgrade
    // is NOT applied here -- it touches water2 internals and stays a request to the
    // water2 owner (web/lib/scene/bathy/style/WATER2_TUNING_REQUEST.md).
    const handle = makeWater2({
      ...bathyWater2Options({ sunDirection: sun.direction }),
      width: SCENE_WIDTH * 1.6,
      depth: depth * 1.6,
      // W2.6: the water surface (and the foam/column reference the depth shader
      // derives from uWaterLevel) sits at the NAVD88 0 m datum, now mapped to
      // scene Y 0 by the tiles fit, instead of a hardcoded literal.
      level: SEA_LEVEL_Y,
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

function HydrophoneBeacon({
  node,
  position,
  onSelect,
}: {
  node: HydrophoneNode;
  position: [number, number, number];
  onSelect: (node: HydrophoneNode) => void;
}) {
  const [hovered, setHovered] = useState(false);
  const online = (node.status ?? "online") === "online";
  const color = online ? "#ffcf33" : "#888";
  return (
    <group position={position}>
      <mesh
        position={[0, 6, 0]}
        onClick={(e) => {
          e.stopPropagation();
          onSelect(node);
        }}
        onPointerOver={(e) => {
          e.stopPropagation();
          setHovered(true);
        }}
        onPointerOut={() => setHovered(false)}
        scale={hovered ? 1.4 : 1}
      >
        <coneGeometry args={[1.6, 5, 6]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={hovered ? 0.9 : 0.4} />
      </mesh>
      <mesh position={[0, 1.5, 0]}>
        <cylinderGeometry args={[0.18, 0.18, 9, 6]} />
        <meshStandardMaterial color="#ffffff" emissive={color} emissiveIntensity={0.3} />
      </mesh>
      {hovered && (
        <Html center distanceFactor={120} position={[0, 11, 0]} style={{ pointerEvents: "none" }}>
          <div className="scene-beacon-label">{node.name ?? node.location ?? "Hydrophone"}</div>
        </Html>
      )}
    </group>
  );
}

// Places beacons on the tile surface by raycasting the streamed geometry at each
// node's projected XZ (replaces the retired heightmap sampleDepth).
function SurfaceBeacons({
  tiles,
  tick,
  nodes,
  onSelect,
}: {
  tiles: TilesRenderer | null;
  tick: number;
  nodes: HydrophoneNode[];
  onSelect: (node: HydrophoneNode) => void;
}) {
  const placed = useMemo(() => {
    if (!tiles) return [];
    return nodes.map((node, i) => {
      const [x, z] = projectToScene(
        node.latitude,
        node.longitude,
        TILESET_BOUNDS,
        SCENE_DEPTH,
      );
      const y = surfaceYAt(tiles.group, x, z);
      const key = `${node.id ?? node.name ?? i}`;
      return { node, key, position: [x, Math.max(y ?? 0, 0), z] as [number, number, number] };
    });
    // tick drives re-placement as tiles stream in and refine.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tiles, tick, nodes]);

  return (
    <>
      {placed.map(({ node, key, position }) => (
        <HydrophoneBeacon key={key} node={node} position={position} onSelect={onSelect} />
      ))}
    </>
  );
}

function FocusMarker({
  lat,
  lng,
  tiles,
  tick,
}: {
  lat: number;
  lng: number;
  tiles: TilesRenderer | null;
  tick: number;
}) {
  const position = useMemo<[number, number, number]>(() => {
    const [x, z] = projectToScene(lat, lng, TILESET_BOUNDS, SCENE_DEPTH);
    const y = tiles ? surfaceYAt(tiles.group, x, z) : null;
    return [x, Math.max(y ?? 0, 0) + 4, z];
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lat, lng, tiles, tick]);
  return (
    <mesh position={position}>
      <sphereGeometry args={[1.6, 16, 16]} />
      <meshStandardMaterial color="#ff5a5a" emissive="#ff5a5a" emissiveIntensity={0.7} />
    </mesh>
  );
}

// ============================================================================
// WS-INTENT MOUNT BLOCK (B.2 / B.7) -- viewport bridge, single owner WS-INTENT.
// Everything between this banner and its closing banner is the WS-INTENT camera
// wiring. It attaches the W1 Camera Director to the live camera + OrbitControls,
// keeps a resting slow orbit as the default state, and turns a focus change or a
// place search into runPlaceJourney. It touches ONLY camera/controls/search/focus
// wiring; the RealismRig, Water2Rig, and tiles mount are left stable for the
// later SCENIC and BATHY mounts. Keep additions inside this fence.
// ----------------------------------------------------------------------------

// Inner rig that owns the Camera Director attachment. Mounted AHEAD of Water2Rig
// so it positions the camera before Water2Rig's priority-0 depth pre-pass and
// r3f's auto-render (mirrors JourneyScene.DirectorRig). Holds no React state in
// the per-frame loop; the director reads the mutable handle lazily each frame.
function IntentDirectorRig({
  tiles,
  fitRadius,
  focus,
  refs,
}: {
  tiles: TilesRenderer | null;
  fitRadius: number | null;
  focus?: { lat: number; lng: number } | null;
  refs: IntentBridgeRefs;
}) {
  const scene = useThree((s) => s.scene);
  const camera = useThree((s) => s.camera);
  const { handleRef, directorRef, orbitRef, journeyRef, transitionsRef, controlsRef, runPlaceRef } =
    refs;
  const restingStartedRef = useRef(false);
  const lastFocusRef = useRef<string | null>(null);

  // Create the director once, bound to the shared mutable handle.
  if (!directorRef.current) {
    directorRef.current = createCameraDirector(handleRef.current);
  }

  // Run a place journey on the live director: cancel any prior journey/orbit,
  // hand the camera to the director (controls off during the scripted beats),
  // run the fog-masked fly/descend/follow/orbit, then re-enable manual orbit
  // once it settles into the resting orbit at the place. Atmosphere is fog-only
  // through scene.fog this pass; the descentLighting dim is deferred to SCENIC.
  const runPlace = useCallback(
    (place: Place) => {
      const director = directorRef.current;
      if (!director) return;
      journeyRef.current?.cancel();
      orbitRef.current?.stop();
      orbitRef.current = null;
      if (controlsRef.current) controlsRef.current.enabled = false;
      const atmosphere: JourneyAtmosphere = {
        fog: scene.fog instanceof THREE.Fog ? scene.fog : null,
        push: (t) => transitionsRef.current.push(t),
      };
      const handle = runPlaceJourney(place, director, atmosphere);
      journeyRef.current = handle;
      void handle.done.then(() => {
        if (journeyRef.current === handle && controlsRef.current) {
          controlsRef.current.enabled = true;
        }
      });
    },
    [scene, directorRef, journeyRef, orbitRef, controlsRef, transitionsRef],
  );

  // Publish runPlace so the out-of-canvas SearchAffordance overlay can drive the
  // in-canvas director (search -> resolvePlace -> runPlaceJourney, seam D).
  useEffect(() => {
    runPlaceRef.current = runPlace;
    return () => {
      if (runPlaceRef.current === runPlace) runPlaceRef.current = null;
    };
  }, [runPlace, runPlaceRef]);

  // Register the live director with the intent transducer (B.7 implicit-intent
  // feed) on mount; clear it and stop all motion on unmount.
  useEffect(() => {
    const director = directorRef.current;
    if (director) setActiveDirector(director);
    return () => {
      clearActiveDirector();
      journeyRef.current?.cancel();
      journeyRef.current = null;
      orbitRef.current?.stop();
      orbitRef.current = null;
      directorRef.current?.stop();
      transitionsRef.current.forEach((t) => t.cancel());
      transitionsRef.current = [];
    };
  }, [directorRef, journeyRef, orbitRef, transitionsRef]);

  // Per-frame: refresh the handle's live refs, advance the director (positions
  // the camera) BEFORE Water2Rig's depth pre-pass, then advance atmosphere
  // tweens. No React state is touched in this hot loop.
  useFrame((_state, delta) => {
    const handle = handleRef.current;
    handle.camera = camera as THREE.PerspectiveCamera;
    handle.controls = controlsRef.current ?? null;
    handle.group = tiles?.group ?? null;
    handle.getSurfaceY = tiles ? (x, z) => surfaceYAt(tiles.group, x, z) : null;
    directorRef.current?.update(delta);
    const list = transitionsRef.current;
    for (let i = list.length - 1; i >= 0; i--) {
      if (!list[i].update(delta * 1000)) list.splice(i, 1);
    }
  });

  // On first fit: set the fit radius + a fit-accurate world-units-per-metre,
  // widen the camera depth range so high/low framing never clips, and start the
  // resting slow orbit (B.7) when no focus journey is pending.
  useEffect(() => {
    if (fitRadius == null) return;
    const handle = handleRef.current;
    handle.fitRadius = fitRadius;
    handle.worldUnitsPerMeter = fitRadius / geoRadiusMeters(TILESET_BOUNDS);
    if (camera instanceof THREE.PerspectiveCamera) {
      camera.near = Math.max(fitRadius / 2000, 0.01);
      camera.far = fitRadius * 100;
      camera.updateProjectionMatrix();
    }
    if (!restingStartedRef.current && !focus) {
      restingStartedRef.current = true;
      const director = directorRef.current;
      if (director && !journeyRef.current) {
        orbitRef.current = director.orbit(
          SCENE_CENTER,
          Math.max(fitRadius * 0.9, 40),
          RESTING_ORBIT_SPEED,
          { subject: "Salish Sea", altitudeMeters: RESTING_ORBIT_ALT_M },
        );
      }
    }
  }, [fitRadius, focus, camera, handleRef, directorRef, orbitRef, journeyRef]);

  // A planner map_viewport or a scene click arrives as a focus change: fly the
  // live camera there, closing the map_viewport -> camera loop (seam B/F). Skips
  // an unchanged focus so a re-render does not re-trigger the same journey.
  useEffect(() => {
    if (fitRadius == null || !focus) return;
    const key = `${focus.lat},${focus.lng}`;
    if (key === lastFocusRef.current) return;
    lastFocusRef.current = key;
    runPlace(placeFromFocus(focus.lat, focus.lng));
  }, [focus, fitRadius, runPlace]);

  return null;
}
// ----------------------------------------------------------------------------
// END WS-INTENT MOUNT BLOCK
// ============================================================================

// ============================================================================
// WS-SCENIC MOUNT BLOCK (phase B) -- scenic visuals, single owner WS-SCENIC.
// Runs in the SCENIC slot, AFTER WS-INTENT (landed) and BEFORE WS-BATHY. Wires
// the two phase-A modules into the live scene by their public APIs only: the
// terrain stylist tints the streamed CUDEM tiles (vegetated land, rock faces, a
// shoreline band), the sky dome owns the background and agrees with the realism
// sun, the decorative horizon ring frames the empty water, and the fog tune
// warms the haze so the ring dissolves into it. No realism/, tiles/, decor/, or
// terrain/ internals are edited. Honesty labels (tint derived from real CUDEM;
// ring decorative, not surveyed; fog an atmosphere effect) ride along inside the
// modules' own userData. Keep WS-SCENIC additions inside this fence.
// ----------------------------------------------------------------------------

// The pinned sun shared by every scenic rig. Same SCENE_TIME / lat / lng the
// RealismRig and Water2Rig already use, so sky, directional light, and water
// glitter all agree on where the sun is.
function useScenicSun(): SunResult {
  return useMemo(() => makeSun(SCENE_TIME, 48.5, -123), []);
}

// 1. Terrain Stylist. Restyles each streamed tile material with an elevation-
// and-slope biome tint so the bare tan relief reads as living land. Effect-only
// (mounts on the live TilesRenderer, restyles already-streamed tiles, disposes
// listeners + created materials on unmount). It never changes tile geometry.
function TerrainStylistRig({
  tiles,
  worldUnitsPerMeter,
}: {
  tiles: TilesRenderer | null;
  // W2.6: the live uniform fit scale (scene units per metre). Drives the
  // shoreline-band height (and the elevation biome thresholds) off the actual
  // fit instead of the stylist's stale 0.0024 default, so the band tracks the
  // corrected sea level. Restyle re-runs once the fit reports it.
  worldUnitsPerMeter?: number;
}) {
  useEffect(() => {
    if (!tiles) return;
    const handle = applyTerrainStyle(tiles, { worldUnitsPerMeter });
    return () => handle.dispose();
  }, [tiles, worldUnitsPerMeter]);
  return null;
}

// 2. Sky dome. The core three Preetham sky, driven by the pinned sun via setSun
// so the sky follows the same sun as the light and water. RealismRig is mounted
// with background:false (above) so the dome owns scene.background.
function SkyRig() {
  const sun = useScenicSun();
  const handle = useMemo(() => makeSkyDome({ sunDirection: sun.direction }), [sun]);
  useEffect(() => {
    handle.setSun(sun.direction);
    return () => handle.dispose();
  }, [handle, sun]);
  return <primitive object={handle.object3D} />;
}

// 3. Horizon ring. A true-scale DECORATIVE terrain ring (baked AWS Terrain
// Tiles DEM, tagged decorativeNotSurveyed in userData by the module) so the
// Olympics/Cascades/Vancouver Island bearings frame the horizon instead of
// empty water. It shares scene.fog (material.fog = true) so it dissolves into
// the haze. worldUnitsPerMeter comes from the live fit so it aligns to the tiles.
function HorizonRig({ worldUnitsPerMeter }: { worldUnitsPerMeter?: number }) {
  const [field, setField] = useState<HorizonField | null>(null);
  useEffect(() => {
    let alive = true;
    loadHorizonField(HORIZON_RING_URL)
      .then((f) => {
        if (alive) setField(f);
      })
      .catch(() => {
        if (alive) setField(null);
      });
    return () => {
      alive = false;
    };
  }, []);
  const handle = useMemo(
    () => (field ? makeHorizonRing({ field, worldUnitsPerMeter }) : null),
    [field, worldUnitsPerMeter],
  );
  useEffect(() => () => handle?.dispose(), [handle]);
  return handle ? <primitive object={handle.object3D} /> : null;
}

// 4. Fog tuning. Warms the realism haze toward the low sun so the horizon ring
// dissolves into a coherent sun-side glow. Mutates the live scene.fog object in
// place only; mounted after RealismRig so scene.fog already exists.
function FogTuneRig() {
  const scene = useThree((s) => s.scene);
  const sun = useScenicSun();
  useEffect(() => {
    if (scene.fog instanceof THREE.Fog) {
      tuneFog(scene.fog, { elevationDeg: sun.elevationDeg, azimuthDeg: sun.azimuthDeg });
    }
  }, [scene, sun]);
  return null;
}
// ----------------------------------------------------------------------------
// END WS-SCENIC MOUNT BLOCK
// ============================================================================

// ============================================================================
// WS-BATHY MOUNT BLOCK (phase B) -- submerged-seabed depth read, owner WS-BATHY.
// Runs LAST in the convergence slot, AFTER WS-INTENT and WS-SCENIC (both landed).
// MODELED-ONLY. It mounts the cmocean `deep` submerged-seabed depth tint over the
// modeled CUDEM topobathy that the tiles already render, and stamps the modeled
// provenance label (B.6) so the bathymetry declares "modeled, not measured". The
// depth-read water tuning is applied to Water2Rig above (it owns the Water2Options
// object at its mount). No second per-frame depth pass is added: the Water2Rig
// pre-pass stays the only one. The measured BlueTopo/NONNA overlay is a DEFERRED
// fast-follow and is NOT fetched here (DEFERRED_MEASURED_OVERLAY answers modeled
// everywhere). No bathy/style, bathy/honesty, water2/, or substrate/ internals are
// edited; only public APIs are composed. Keep WS-BATHY additions inside this fence.
// ----------------------------------------------------------------------------

// Submerged-seabed depth tint. Reuses the SAME modeled substrate field source the
// scene already loads for the pick depth_m, and the substrate projector seam, so
// the tint reads the modeled CUDEM seabed in the live tile frame. The project
// callback mirrors how the scene places everything else: projectToScene for X/Z
// in the TILESET_BOUNDS/SCENE_DEPTH frame (the same frame the beacons use), and
// depth_m * worldUnitsPerMeter for Y (W2.6: the live fit scale, replacing the
// legacy HEIGHT_SCALE that ran ~12x too tall). Mounted at scene root (the
// projectToScene frame), disposed on unmount. The honesty label and the scene
// honesty note travel with the object's userData; the deferred measured-overlay
// stub records loaded=false so the scene stays honestly modeled. With the live
// fit scale and the corrected datum the tint Y now agrees with the fit-scaled
// tile frame (the prior A2 reconciliation seam), sea level at scene Y 0.
function BathyRig({
  field,
  worldUnitsPerMeter,
}: {
  field: SubstrateField | null;
  // W2.6: the live uniform fit scale (scene units per metre). Replaces the legacy
  // HEIGHT_SCALE (0.04, ~12x too tall) so the modeled seabed tint sits on the same
  // vertical scale as the rendered CUDEM tiles, with sea level (NAVD88 0 m) at
  // scene Y 0. depth_m is signed (negative below sea level), so depth_m * scale is
  // the world Y directly.
  worldUnitsPerMeter?: number;
}) {
  const scene = useThree((s) => s.scene);
  useEffect(() => {
    if (!field || worldUnitsPerMeter == null) return;
    const project = (
      lat: number,
      lng: number,
      depthM: number,
    ): [number, number, number] => {
      const [x, z] = projectToScene(lat, lng, TILESET_BOUNDS, SCENE_DEPTH);
      return [x, depthM * worldUnitsPerMeter, z];
    };
    const tint = buildBathyTint(field, { project });
    // B.6: declare the modeled provenance on the depth-bearing object. The tint
    // already self-tags modeled; attachModeledLabel stamps the canonical typed
    // label so any UI built from the scene graph reads the same honesty string.
    attachModeledLabel(tint.object, "bathy-seabed-tint");
    // Carry the scene honesty note and the deferred measured-overlay state on the
    // object so the scene honesty record is recoverable from the graph. No fetch:
    // DEFERRED_MEASURED_OVERLAY is the modeled-only stub (loaded === false).
    tint.object.userData.sceneHonestyNote = BATHY_SCENE_HONESTY_NOTE;
    tint.object.userData.measuredOverlayLoaded = DEFERRED_MEASURED_OVERLAY.loaded;
    tint.apply(scene);
    return () => tint.dispose();
  }, [scene, field, worldUnitsPerMeter]);
  return null;
}
// ----------------------------------------------------------------------------
// END WS-BATHY MOUNT BLOCK
// ============================================================================

// The composed live twin: mounts the tileset, realism, BVH picking, beacons, and
// the focus marker inside the r3f Canvas.
function TwinScene({
  onIntent,
  focus,
  beacons,
  field,
  onTilesError,
  showPlaceholder,
  intentRefs,
}: {
  onIntent: (intent: SceneIntent) => void;
  focus?: { lat: number; lng: number } | null;
  beacons: HydrophoneNode[];
  field: SubstrateField | null;
  onTilesError: () => void;
  showPlaceholder: boolean;
  intentRefs: IntentBridgeRefs;
}) {
  const [fitRadius, setFitRadius] = useState<number | null>(null);

  // --- WS-SCENIC: fit-accurate world-units-per-metre for the horizon ring, and
  // a shared realism handle so the horizon ring lands at true scale alongside
  // the tiles and a later descentLighting wave can reach the realism lights. ---
  const realismHandleRef = useRef<RealismHandle | null>(null);
  const scenicWorldUnitsPerMeter =
    fitRadius != null ? fitRadius / geoRadiusMeters(TILESET_BOUNDS) : undefined;

  const tiles = useTilesLayer({
    url: FULL_TILESET_URL,
    groupRotationX: -Math.PI / 2,
    fitScaleToWidth: SCENE_WIDTH,
    errorTarget: 16,
    enableShadows: false,
    onFit: (sphere) => setFitRadius(sphere.radius),
  });

  const tick = useModelLoadTick(tiles);

  // Install BVH-accelerated raycasting on the tile meshes as they stream.
  useEffect(() => {
    if (!tiles) return;
    return accelerateTilesPicking(tiles);
  }, [tiles]);

  // Degrade to the fallback toggle if the root tileset cannot load.
  const onTilesErrorRef = useRef(onTilesError);
  onTilesErrorRef.current = onTilesError;
  useEffect(() => {
    if (!tiles) return;
    const onErr = () => onTilesErrorRef.current();
    tiles.addEventListener("load-error", onErr);
    return () => tiles.removeEventListener("load-error", onErr);
  }, [tiles]);

  function handlePick(e: ThreeEvent<MouseEvent>) {
    if (!tiles) return;
    e.stopPropagation();
    const { lat, lng } = worldPointToLatLng(e.point, TILESET_BOUNDS, SCENE_DEPTH, tiles.group);
    const d = field ? sampleSubstrate(field, lat, lng) : NaN;
    onIntent({ type: "cell", lat, lng, depth_m: Number.isFinite(d) ? d : undefined });
  }

  // fitRadius is deterministic (= SCENE_WIDTH / 2) under fitScaleToWidth, so the
  // static camera/controls below already frame it; the value gates "tiles ready".
  const minDistance = fitRadius ? fitRadius * 0.5 : 30;
  const maxDistance = fitRadius ? fitRadius * 8 : 600;

  // WS-INTENT: when the user grabs the controls, hand the camera to them by
  // stopping the director's resting orbit and any in-flight journey, so manual
  // orbit is genuinely usable. (onStart only fires while controls are enabled,
  // i.e. at rest or after a journey settles; the scripted beats keep them off.)
  const handleUserGrab = useCallback(() => {
    const { journeyRef, orbitRef, directorRef } = intentRefs;
    journeyRef.current?.cancel();
    journeyRef.current = null;
    orbitRef.current?.stop();
    orbitRef.current = null;
    directorRef.current?.stop();
  }, [intentRefs]);

  return (
    <>
      {/* WS-INTENT director rig FIRST so it positions the camera before
          Water2Rig's depth pre-pass and the auto-render this frame. */}
      <IntentDirectorRig tiles={tiles} fitRadius={fitRadius} focus={focus} refs={intentRefs} />
      <RealismRig depth={SCENE_DEPTH} exposeHandle={realismHandleRef} />
      <Water2Rig depth={SCENE_DEPTH} />
      {/* ====================================================================
          WS-SCENIC MOUNT -- scenic visuals (terrain tint, sky, horizon, fog),
          single owner WS-SCENIC. Mounted AFTER RealismRig so scene.fog exists
          for FogTuneRig and the sky dome owns the background RealismRig
          released. Room is left BELOW for the WS-BATHY mount that follows.
          ==================================================================== */}
      <TerrainStylistRig tiles={tiles} worldUnitsPerMeter={scenicWorldUnitsPerMeter} />
      <SkyRig />
      <HorizonRig worldUnitsPerMeter={scenicWorldUnitsPerMeter} />
      <FogTuneRig />
      {/* ===================== END WS-SCENIC MOUNT ========================== */}
      {/* ====================================================================
          WS-BATHY MOUNT -- submerged-seabed depth tint, single owner WS-BATHY.
          Mounted LAST (after INTENT and SCENIC) and BEFORE the tiles primitive,
          in the room left below the SCENIC block. MODELED-ONLY: the cmocean deep
          tint reads the modeled CUDEM seabed via the same substrate field source
          and projector seam the scene already uses; the modeled provenance label
          rides along (B.6). The depth-read water tuning is applied in Water2Rig
          above. The measured overlay stays a deferred fast-follow (no fetch).
          ==================================================================== */}
      <BathyRig field={field} worldUnitsPerMeter={scenicWorldUnitsPerMeter} />
      {/* ====================== END WS-BATHY MOUNT ========================== */}
      {tiles && <primitive object={tiles.group} onClick={handlePick} />}
      {showPlaceholder && (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
          <planeGeometry args={[SCENE_WIDTH, SCENE_WIDTH]} />
          <meshStandardMaterial color="#0a2540" roughness={0.9} />
        </mesh>
      )}
      <SurfaceBeacons
        tiles={tiles}
        tick={tick}
        nodes={beacons}
        onSelect={(n) =>
          onIntent({
            type: "hydrophone",
            id: n.id ?? null,
            name: n.name,
            lat: n.latitude,
            lng: n.longitude,
            streamUrl: n.streamUrl,
          })
        }
      />
      {/* FocusMarker kept as a secondary cue alongside the camera journey. */}
      {focus && <FocusMarker lat={focus.lat} lng={focus.lng} tiles={tiles} tick={tick} />}
      {/* WS-INTENT: makeDefault so the tiles cull against the camera the director
          drives; ref so the director can steer the look-at; onStart hands control
          back to the user when they grab. */}
      <OrbitControls
        ref={intentRefs.controlsRef}
        makeDefault
        enablePan
        enableZoom
        maxPolarAngle={Math.PI / 2.05}
        minDistance={minDistance}
        maxDistance={maxDistance}
        target={[0, 0, 0]}
        onStart={handleUserGrab}
      />
      {SHOW_PERF_HUD && <PerfHud corner="top-right" />}
    </>
  );
}

interface SalishSceneProps {
  onIntent?: (intent: SceneIntent) => void;
  focus?: { lat: number; lng: number } | null;
}

export default function SalishScene({ onIntent, focus }: SalishSceneProps) {
  const [nodes, setNodes] = useState<HydrophoneNode[]>([]);
  const [field, setField] = useState<SubstrateField | null>(null);
  const [assetError, setAssetError] = useState(false);
  const [tilesFailed, setTilesFailed] = useState(false);
  const onIntentRef = useRef(onIntent);
  onIntentRef.current = onIntent;

  // --- WS-INTENT viewport bridge: shared director refs (B.2 / B.7) ----------
  // Created here so both the in-canvas IntentDirectorRig and the out-of-canvas
  // SearchAffordance overlay can reach the same live director. The rig populates
  // directorRef/orbitRef/journeyRef/runPlaceRef; the overlay reads runPlaceRef.
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
  const journeyRef = useRef<JourneyHandle | null>(null);
  const transitionsRef = useRef<TweenHandle[]>([]);
  const controlsRef = useRef<React.ElementRef<typeof OrbitControls> | null>(null);
  const runPlaceRef = useRef<((place: Place) => void) | null>(null);
  const intentRefs: IntentBridgeRefs = {
    handleRef,
    directorRef,
    orbitRef,
    journeyRef,
    transitionsRef,
    controlsRef,
    runPlaceRef,
  };

  useEffect(() => {
    getJSON<{ data?: HydrophoneNode[]; hydrophones?: HydrophoneNode[] }>("/api/live-hydrophones")
      .then((res) => {
        const list = res.hydrophones ?? res.data ?? [];
        setNodes(list.length ? list : ORCASOUND_FALLBACK);
      })
      .catch(() => setNodes(ORCASOUND_FALLBACK));
  }, []);

  // Modeled CUDEM depth field for pick depth_m (modeled, not measured).
  useEffect(() => {
    loadSubstrate()
      .then(setField)
      .catch(() => setField(null));
  }, []);

  // Bubble a tileset failure to the host so it can fall back to Maps.
  useEffect(() => {
    if (assetError) {
      window.dispatchEvent(new CustomEvent("salish-scene-error"));
    }
  }, [assetError]);

  if (assetError) {
    return null;
  }

  const inBoundsNodes = nodes.filter(
    (n) =>
      n.latitude >= TILESET_BOUNDS.min_lat &&
      n.latitude <= TILESET_BOUNDS.max_lat &&
      n.longitude >= TILESET_BOUNDS.min_lng &&
      n.longitude <= TILESET_BOUNDS.max_lng,
  );
  const beacons = inBoundsNodes.length ? inBoundsNodes : nodes.slice(0, 1);

  return (
    // WS-INTENT: position:relative wrapper so the SearchAffordance overlay (seam
    // D) can float over the canvas without reflowing it. The canvas keeps its
    // full size; the bridge only adds the overlay sibling.
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <Canvas
        camera={{ position: [0, 80, 120], fov: 45, near: 1, far: 800 }}
        style={{ width: "100%", height: "100%", background: "linear-gradient(#0b1f33,#08263d)" }}
        onCreated={({ gl }) => gl.setClearColor("#08263d")}
      >
        <TwinScene
          onIntent={(intent) => onIntentRef.current?.(intent)}
          focus={focus}
          beacons={beacons}
          field={field}
          showPlaceholder={tilesFailed}
          onTilesError={() => {
            if (FALLBACK_TO_MAPS) setAssetError(true);
            else setTilesFailed(true);
          }}
          intentRefs={intentRefs}
        />
      </Canvas>
      {/* WS-INTENT search affordance: search -> resolvePlace -> runPlaceJourney
          on the live director. Resolves offline against the curated gazetteer;
          waypoints are approximate lane points, not a surveyed track. */}
      <SearchAffordance
        onSearch={(q) => {
          const place = resolvePlace(q);
          if (place) runPlaceRef.current?.(place);
        }}
      />
    </div>
  );
}
