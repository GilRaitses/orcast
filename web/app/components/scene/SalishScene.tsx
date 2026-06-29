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
import { BuoyMarker } from "@/lib/scene/markers";
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
  tunedFogColor,
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
// Owner-signed green-survives optic (WFX SIGN_OFF #2, R11), the SAME twin-unit
// absorption fed to both the Water2Rig (E4) and the OrcaRig env.
import { PROPOSED_RGB_EXTINCTION } from "@/lib/scene/bathy/style/waterTuning";
// --- W4 ORCA mount imports (single owner W4) --------------------------------
// The orca public API (built + sandbox-verified) plus the REAL WFX env producer
// this wave introduces. createOrcaController assembles the data-driven, WFX-lit
// SRKW; makeRealWfxEnv PMREMs the scene sky and supplies the twin-unit
// underwater optic so the orca is lit by the same atmosphere as the water.
import {
  createOrcaController,
  REAL_SRKW_MOTION_URL,
  ORCA_MESH_URL,
  type OrcaController,
  type WfxEnvHandle,
} from "@/lib/scene/orca";
import { makeRealWfxEnv } from "@/lib/scene/wfx/realWfxEnv";
// --- SLICE MOUNT imports (single owner SLICE-INTEGRATE) ----------------------
// The thin-but-real B-side slice, mounted IN PLACE on a hydrophone station
// selection. Public barrels only; no lane internal is copied or forked. This
// mirrors the proven /workbench composition (BST rig, BSH spectro authority,
// BAM precomputed classification, BRE presence-gated reenactment) but reuses the
// LIVE twin environment (SkyRig/FogTuneRig/OrcaRig stay authoritative; the slice
// never writes scene.background/fog/environment) and the EXISTING camera
// director instead of the workbench stand-ins. See the SLICE MOUNT BLOCK below
// and web/lib/scene/hydrophone/WIRING.md "How the integrator mounts this".
import {
  makeStationEquipment,
  stationSeabedPoseForEntry,
  resolveSeabedDepthM,
  createStationPovController,
  getStation,
  entryFromNode,
  STATION_CATALOG,
  STATION_POVS,
  type EquipmentRig,
  type StationCatalogEntry,
  type StationPov,
  type StationPovController,
} from "@/lib/scene/hydrophone";
import {
  createSpectroTimeline,
  type SpectroTimeline,
} from "@/lib/scene/hud/spectro";
// BSH-INTEGRATE: the interpretive double-diffusion ocean layer (additive,
// depthWrite:false, default-off). The barrel stays backward-compatible; this only
// pulls the promoted layer + its locked on-screen labels.
import {
  createDoubleDiffusionLayer,
  INTERPRETIVE_OCEAN_LABEL,
  INTERPRETIVE_OCEAN_DETAIL,
  type DoubleDiffusionLayer,
} from "@/lib/scene/ocean";
import {
  buildSpawnRecord,
  createOrcaPool,
  createTimelineDriver,
  loadClassification,
  loadClipManifest,
  type OrcaPool,
  type TimelineDriver,
  type BehaviorClassId,
} from "@/lib/scene/reenactment";

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

// --- W4 ORCA mount constants ------------------------------------------------
// Swim anchor for the integrated orca: San Juan Channel water just NE of the
// scene centre (the resting-orbit look target at SCENE_CENTER -> scene 0,0), so
// the animal stays framed in the resting orbit. The motion is REAL SRKW
// telemetry; this is a sensible modeled swim point, not a tracked position.
const ORCA_ANCHOR = { lat: 48.57, lng: -123.02 };
// Body scale. The synthetic SCENE_WIDTH=120 frame is non-metric (metric
// migration is a later wave), so a true-scale ~7 m animal would be sub-pixel.
// Scale the body to a readable in-frame size, the watchable scale the sandbox
// verified. Vertical placement stays the honest datum mapping (depthScale 1).
const ORCA_BODY_SCALE = 0.5;
// Depth descent multiplier on top of worldUnitsPerMeter. 1 keeps the honest
// datum Y = -depth_m * worldUnitsPerMeter (no vertical exaggeration), so the
// animal rides the water column above the modeled CUDEM seabed.
const ORCA_DEPTH_SCALE = 1;
// Real SRKW track playback start (seconds); the track plays from here, capped
// per-frame by min(dt, 1/30).
const ORCA_TRACK_START_S = 0;

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
const RESTING_ORBIT_ALT_M = 6000; // metres above sea level; a real look-down on the San Juans core (RP2: pitch ~31 deg) instead of a horizon graze.

// --- W-PERFUX startup LoD caps (RP1/RP2) ------------------------------------
// The resting wide frame only needs the coarse L0..L2 set, so start coarse and
// lift to full detail the instant the user engages the map (grab/zoom/focus),
// which streams leaves on demand for the place they actually look at.
//   errorTarget 16 -> 32 cuts first-paint bytes ~75% (RP1 lever 1).
//   maxDepth 2 caps the tree at L2: <=21 tiles / ~19 MiB vs 85 tiles / 75.75 MiB,
//   dropping the 64-leaf level until the cap lifts (RP2 lever 2).
const RESTING_ERROR_TARGET = 32;
const RESTING_MAX_DEPTH = 2;
const DETAIL_ERROR_TARGET = 16;
const DETAIL_MAX_DEPTH = Infinity;

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
      // WFX E4: feed the merged depthWater color path the signed-off uniforms
      // (SIGN_OFF #2 green-survives, R11). Absorption is the SAME twin-unit
      // optic the OrcaRig env carries (PROPOSED_RGB_EXTINCTION {3,1,3}); the
      // water divides it by depthColorScale internally. The tints come from the
      // owner-signed waterTuning via bathyWater2Options above.
      absorption: new THREE.Vector3(
        PROPOSED_RGB_EXTINCTION.r,
        PROPOSED_RGB_EXTINCTION.g,
        PROPOSED_RGB_EXTINCTION.b,
      ),
      refractStrength: 0.035,
      roughness: 0.12,
      runup: 0.6,
      contactSoftness: 0.06,
      skyZenith: new THREE.Color("#5a86a8"),
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
    // WFX E5: drive the water's self-contained horizon fog from the live scene
    // fog so the far water dissolves into the same haze (FogExp2). Linear/no fog
    // disables it (a no-op), keeping the water self-contained.
    const f = scene.fog;
    if (f instanceof THREE.FogExp2) handle.setFog({ color: f.color, density: f.density });
    else handle.setFog(null);
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
      <group
        onClick={(e) => {
          e.stopPropagation();
          onSelect(node);
        }}
        onPointerOver={(e) => {
          e.stopPropagation();
          setHovered(true);
        }}
        onPointerOut={() => setHovered(false)}
        scale={hovered ? 1.15 : 1}
      >
        <BuoyMarker color={color} hovered={hovered} />
      </group>
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
        // WFX E3 reconcile: the resting scene fog is now a FogExp2 (above), which
        // rollInFog masks by easing density. Pass either fog type through so the
        // journey fog-roll keeps working instead of nulling out on the swap.
        fog:
          scene.fog instanceof THREE.Fog || scene.fog instanceof THREE.FogExp2
            ? scene.fog
            : null,
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
      // WFX E2 (R10 Rec C1): tighten the far plane to the 120-unit scene so the
      // water depth pre-pass reconstructs the seabed column at higher precision.
      // The Preetham dome forces far-plane depth, so it is never clipped; the
      // true-scale horizon ring sits within fitRadius*8 (~480 u).
      camera.far = fitRadius * 8;
      camera.updateProjectionMatrix();
    }
    if (!restingStartedRef.current && !focus) {
      restingStartedRef.current = true;
      const director = directorRef.current;
      if (director && !journeyRef.current) {
        orbitRef.current = director.orbit(
          SCENE_CENTER,
          Math.max(fitRadius * 0.4, 24), // RP2: ~24 u frames ~1/3 of the extent diagonal instead of the full ~37 km.
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
    // WFX E3 (R04): swap the realism linear scene fog for an exponential-squared
    // fog retuned to the 120-unit scene, so the horizon reads as a soft haze
    // instead of a hard fog band. Density 0.012 is the sandbox-proven value; the
    // color stays in the live atmosphere family via tunedFogColor. The journey
    // fog-roll (runPlaceJourney/rollInFog) already supports FogExp2 by easing
    // density, and the Water2Rig reads this fog through handle.setFog (E5).
    scene.fog = new THREE.FogExp2(
      tunedFogColor({ elevationDeg: sun.elevationDeg, azimuthDeg: sun.azimuthDeg }),
      0.012,
    );
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

// ============================================================================
// W4 ORCA MOUNT BLOCK -- the data-driven, WFX-lit SRKW, single owner W4.
// Mounts the orca controller (mesh + rig + wet-skin material + eyes + mouth +
// REAL SRKW biologging motion + bounded secondary physics) into the live twin,
// lit by the SAME WFX environment handle the water reads. The producer
// (makeRealWfxEnv) owns the unit conversion: it PMREMs the scene sky for the
// orca's above-water IBL and derives the underwater absorption in TWIN units
// from the signed green-survives optic (PROPOSED_RGB_EXTINCTION {3,1,3}), the
// same numbers E4 feeds the water. Passing sandbox-metric into the twin would
// over-extinguish; passing twin-units into the sandbox would crush to black, so
// the producer owns the conversion and the orca consumes whatever env it is
// handed. Mounted AFTER Water2Rig so the orca is part of the opaque depth
// pre-pass the water already runs (no third full render). HONESTY: modeled
// animal, real SRKW DTAG telemetry; the humpback track is contrast-only and
// never drives this orca. Keep W4 additions inside this fence.
// ----------------------------------------------------------------------------
function OrcaRig({ worldUnitsPerMeter }: { worldUnitsPerMeter?: number }) {
  const scene = useThree((s) => s.scene);
  const gl = useThree((s) => s.gl);
  const camera = useThree((s) => s.camera);
  const sun = useScenicSun();

  // The REAL WFX env handle: a PMREM of the scene sky for the orca's IBL, plus
  // the twin-unit underwater optic. Built once from the live renderer + pinned
  // sun, disposed on unmount.
  const env = useMemo<WfxEnvHandle>(
    () =>
      makeRealWfxEnv({
        renderer: gl,
        sunDirection: sun.direction,
        sunColor: sun.color,
        sunIntensity: sun.intensity,
        waterLevelY: SEA_LEVEL_Y,
      }),
    [gl, sun],
  );

  // R03 env seam (E6): assign the WFX PMREM as scene.environment so the orca's
  // PBR IBL (and any standard-material scene PBR) is lit by the scene sky, under
  // the E1 exposure 0.5 so the dark dorsal does not wash out.
  useEffect(() => {
    const prev = scene.environment;
    scene.environment = env.pmremEnvironment;
    return () => {
      if (scene.environment === env.pmremEnvironment) scene.environment = prev;
      env.dispose?.();
    };
  }, [scene, env]);

  const anchorRef = useRef<THREE.Group>(null);
  const controllerRef = useRef<OrcaController | null>(null);
  const startRef = useRef<number | null>(null);
  const camWorld = useMemo(() => new THREE.Vector3(), []);

  // Build the controller once the fit scale is known, add c.root at the swim
  // anchor, and tear it down on unmount. depthScale + worldUnitsPerMeter map the
  // real depth_m channel onto the scene Y; the body is scaled for visibility.
  useEffect(() => {
    if (worldUnitsPerMeter == null) return;
    let alive = true;
    let built: OrcaController | null = null;
    createOrcaController({
      env,
      meshUrl: ORCA_MESH_URL,
      motionUrl: REAL_SRKW_MOTION_URL,
      worldUnitsPerMeter,
      depthScale: ORCA_DEPTH_SCALE,
      timeScale: 1,
    })
      .then((c) => {
        if (!alive) {
          c.dispose();
          return;
        }
        built = c;
        controllerRef.current = c;
        c.root.scale.setScalar(ORCA_BODY_SCALE);
        anchorRef.current?.add(c.root);
      })
      .catch((e) => console.error("orca controller failed", e));
    return () => {
      alive = false;
      const c = built ?? controllerRef.current;
      if (c) {
        anchorRef.current?.remove(c.root);
        c.dispose();
      }
      controllerRef.current = null;
      startRef.current = null;
    };
  }, [env, worldUnitsPerMeter]);

  // Advance the real track each frame (capped step), framing-independent: the
  // controller reads the camera world position for LOD + gaze only.
  useFrame((state, dt) => {
    const c = controllerRef.current;
    if (!c) return;
    if (startRef.current === null) startRef.current = state.clock.elapsedTime;
    const elapsed = ORCA_TRACK_START_S + (state.clock.elapsedTime - startRef.current);
    camera.getWorldPosition(camWorld);
    c.update(Math.min(dt, 1 / 30), elapsed, camWorld);
  });

  // Swim anchor in TILESET_BOUNDS at sea level (the same project frame beacons
  // use). The controller's setDepthPose then drops c.root below this by depth.
  const [ax, az] = useMemo(
    () => projectToScene(ORCA_ANCHOR.lat, ORCA_ANCHOR.lng, TILESET_BOUNDS, SCENE_DEPTH),
    [],
  );
  return <group ref={anchorRef} position={[ax, SEA_LEVEL_Y, az]} />;
}
// ----------------------------------------------------------------------------
// END W4 ORCA MOUNT BLOCK
// ============================================================================

// ============================================================================
// SLICE MOUNT BLOCK -- the thin-but-real B-side slice, single owner
// SLICE-INTEGRATE. Mirrors the proven /workbench composition (BST hydrophone
// rig, BSH spectro authority over the ONE real clip, BAM precomputed
// classification, BRE presence-gated SRKW reenactment) and lands it on the LIVE
// twin, GATED on a hydrophone station selection. Binding O0 rulings honored
// here:
//   SEAM 1+2 (in-place, not a swap): the slice is mounted as in-scene objects
//     anchored at the selected station. It NEVER writes scene.background,
//     scene.fog, or scene.environment -- SkyRig / FogTuneRig / OrcaRig stay the
//     sole authorities for those globals.
//   SEAM 3 (camera): the station POV reuses the EXISTING SalishScene director
//     (intentRefs); the WS-INTENT resting orbit + any journey are suppressed on
//     select. No second director is created and the per-frame director.update
//     stays owned by IntentDirectorRig. See the WS-INTENT review note in
//     web/lib/scene/camera/WIRING-slice-note.md.
//   SEAM 4 (WFX env): a second makeRealWfxEnv PMREM bake lights ONLY the
//     reenactment pool's materials (passed to createOrcaPool); it is never
//     assigned to scene.environment, so OrcaRig remains the lone writer. The
//     consolidation follow-up (ORCA exposes its env handle) is in
//     web/lib/scene/wfx/WIRING-slice-note.md.
//   SEAM 6 (first paint): the STFT/WebAudio bake and all slice loads fire ONLY
//     after a station is selected; nothing here runs on first paint.
// Honesty labels travel verbatim from the slice: the estimate+confidence chip,
// "orcas shown: N" presence-gated to 0 on absence windows, the Orcasound
// attribution, and the representativeness label (rendered as DOM chrome by
// SalishScene below, styled via the bsw-* classes in globals.css).
//
// NOTE on scale + camera (documented modeled choice, flagged for the ACCEPT
// gate): the twin's fit scale maps ~0.0024 units/m, so a true-scale ~18 m rig
// would be sub-pixel. The rig is built at a readable modeled VISIBILITY scale
// (SLICE_RIG_WUPM) -- honest station PLACEMENT, not surveyed size -- exactly the
// rationale OrcaRig uses for ORCA_BODY_SCALE. The director's hard no-dunk
// altitude clamp (web/lib/scene/camera/director.ts) keeps the eye above the
// water plane, so the "dive-to-rig" frames the station from just above the
// translucent surface rather than truly submerged; a true underwater POV needs a
// WS-INTENT opt-out and is left as a review note. Keep SLICE additions in this
// fence.
// ----------------------------------------------------------------------------

// A hydrophone station the user selected on the live twin (subset of the
// hydrophone SceneIntent the beacons already emit). streamUrl is carried through
// for the console live-listen bind; it is surfaced, never decoded here.
interface SelectedStation {
  id: string | number | null;
  name?: string | null;
  lat: number;
  lng: number;
  streamUrl?: string | null;
}

// DOM chrome state the slice publishes for the honesty chips (rendered by
// SalishScene as canvas-overlay siblings, styled by globals.css bsw-* classes).
interface SliceState {
  status: string;
  presence: boolean;
  label: string;
  count: number;
  countBasisLabel: string;
  t: number;
  attribution: string;
  streamUrl: string | null;
  // BST-INTEGRATE deepening: which modeled equipment variant is mounted, and
  // whether this station has a license-clear archived clip. A clip-less station
  // shows the rig + live-listen affordance only -- no spectrogram, no
  // reenactment, no invented audio.
  nodeClass: StationCatalogEntry["nodeClass"];
  hasClip: boolean;
  // BRE-INTEGRATE: per-spawned-orca disclosed modeled behavior labels (the
  // DTAG-segment ethogram match for each instance). Empty until the pool spawns.
  behaviors: string[];
}

// The Orcasound Lab live-listen URL, used by the deterministic ?station capture
// hook (which carries no id). Per-station audio + attribution now travel with
// the catalog entry (web/lib/scene/hydrophone/catalog.ts); no stream is invented.
const SLICE_STREAM_URL = "https://live.orcasound.net/listen/orcasound-lab";
// The reenactment plays the measured "Traveling" clip (near-surface, reads above
// the rig). Acoustic presence still gates WHETHER it is shown.
const SLICE_CLIP_ID = "Traveling";
// BRE-INTEGRATE capability-demo breadth: when the labeled `?bsw_demo=N` override
// is active, the spawned orcas rotate through these near-column DTAG-segment
// behaviors (Traveling 8, Surface_Active 7, Side_rolls 5) so multiple read in
// one frame, each carrying its disclosed modeled-match label. This is NEVER a
// model estimate: BAM is presence-only, so the REAL count stays 0/1 and these
// extra orcas appear only under the explicit override.
const SLICE_DEMO_BEHAVIOR_CLASSES = [8, 7, 5] as BehaviorClassId[];
// Presence-positive window (BAM classification confidence ~0.85) so a freshly
// selected station opens on a frame that shows the spawned orca, not an empty
// absence window.
const SLICE_DEFAULT_T = 61.5;
// Readable modeled VISIBILITY scale for the rig (units per metre). NOT true
// geographic size: see the block header. The rig is internally self-consistent
// at any scale (anchor on the modeled seabed, float at the water plane).
const SLICE_RIG_WUPM = 0.34;
// Readable orca body scale, matching the OrcaRig ORCA_BODY_SCALE convention.
const SLICE_ORCA_BODY_SCALE = 0.5;

// BST-INTEGRATE: resolve the station the user selected (or the ?station capture
// hook set) to a real catalog entry, so the right MODELED equipment variant,
// per-station modeled fallback depth, and audio binding travel with it. Match
// by id/slug first (a beacon click carries the real /api/live-hydrophones id),
// then by nearest coordinates (the ?station=lat,lng capture hook has no id),
// then synthesise an honest entry for any out-of-catalog node (live-listen
// only, node class classified, no invented clip). v1 scope = the 3 in-extent
// nodes (Orcasound Lab, North San Juan Channel, Andrews Bay).
function resolveStationEntry(station: SelectedStation): StationCatalogEntry {
  const byId = station.id != null ? getStation(String(station.id)) : null;
  if (byId) return byId;
  let best: StationCatalogEntry | null = null;
  let bestD = Infinity;
  for (const s of STATION_CATALOG) {
    const d = (s.lat - station.lat) ** 2 + (s.lng - station.lng) ** 2;
    if (d < bestD) {
      bestD = d;
      best = s;
    }
  }
  // ~0.01 deg (~1 km) tolerance: a capture-hook coordinate that lands on a real
  // node adopts that node's variant + clip; anything farther is out-of-catalog.
  if (best && bestD < 1e-4) return best;
  return entryFromNode({
    id: station.id,
    name: station.name,
    latitude: station.lat,
    longitude: station.lng,
    streamUrl: station.streamUrl,
  });
}

function SliceRig({
  station,
  pov,
  field,
  worldUnitsPerMeter,
  demoCount,
  intentRefs,
  hudHost,
  onSliceState,
}: {
  station: SelectedStation;
  pov: StationPov;
  field: SubstrateField | null;
  worldUnitsPerMeter?: number;
  // BRE-INTEGRATE: labeled capability-demo orca count (1..3) from ?bsw_demo. When
  // null, the homepage spawns exactly BAM's presence-only estimate (0/1).
  demoCount?: number | null;
  intentRefs: IntentBridgeRefs;
  hudHost: HTMLDivElement | null;
  onSliceState: (s: SliceState) => void;
}) {
  // The resolved real catalog entry: modeled node class, per-station modeled
  // fallback depth, and audio binding (archived clip vs live-listen only).
  const entry = useMemo(
    () => resolveStationEntry(station),
    [station.id, station.lat, station.lng, station.name, station.streamUrl],
  );
  const hasClip = entry.audio.kind === "archived-clip";
  const clipUrl = entry.audio.audioUrl ?? null;
  const gl = useThree((s) => s.gl);
  const camera = useThree((s) => s.camera);
  const sun = useScenicSun();

  // SEAM 4: pool-only WFX env. PMREMs the same scene sky for the reenactment
  // materials' IBL and carries the twin-unit underwater optic. It is passed to
  // createOrcaPool ONLY; it is NEVER assigned to scene.environment (OrcaRig is
  // the sole writer). One-time PMREM bake, disposed on unmount; no third render
  // pass is added (the pool joins the existing opaque depth pre-pass).
  const env = useMemo<WfxEnvHandle>(
    () =>
      makeRealWfxEnv({
        renderer: gl,
        sunDirection: sun.direction,
        sunColor: sun.color,
        sunIntensity: sun.intensity,
        waterLevelY: SEA_LEVEL_Y,
      }),
    [gl, sun],
  );
  useEffect(() => () => env.dispose?.(), [env]);

  // Modeled seabed depth (metres, negative below sea level): the LIVE CUDEM
  // substrate field first, then this station's modeled fallback (from the
  // catalog, not a single hardcoded constant). Used for the rig cable length
  // and the camera POV altitude.
  const seabedDepthM = useMemo(
    () =>
      resolveSeabedDepthM(station.lat, station.lng, {
        substrate: field,
        fallbackDepthM: entry.modeledFallbackDepthM,
      }),
    [station.lat, station.lng, field, entry.modeledFallbackDepthM],
  );

  // BST-INTEGRATE: the MODELED equipment variant for this station's node class
  // (cabled shore hydrophone vs subsurface mooring), anchored on the modeled
  // seabed via stationSeabedPoseForEntry against the LIVE substrate field. XZ
  // uses the shared projectToScene frame (beacons + OrcaRig); Y is the substrate
  // depth (per-station fallback when the field misses), both scaled by the
  // readable visibility scale so the rig is not sub-pixel (the gate-flagged
  // modeled VISIBILITY choice; see the block header). Added imperatively,
  // disposed on station change / unmount.
  const rigGroupRef = useRef<THREE.Group>(null);
  useEffect(() => {
    const [x, y, z] = stationSeabedPoseForEntry(entry, TILESET_BOUNDS, SCENE_DEPTH, {
      substrate: field,
      worldUnitsPerMeter: SLICE_RIG_WUPM,
    });
    const rig: EquipmentRig = makeStationEquipment(entry.nodeClass, {
      seabedDepthM,
      worldUnitsPerMeter: SLICE_RIG_WUPM,
    });
    rig.root.position.set(x, y, z);
    const group = rigGroupRef.current;
    group?.add(rig.root);
    return () => {
      group?.remove(rig.root);
      rig.dispose();
    };
  }, [entry, field, seabedDepthM]);

  // Per-station audio binding (REUSE of the bind SLICE-INTEGRATE wired; never
  // re-bound, never invented). Live-listen link prefers the real intent
  // streamUrl, then the catalog.
  const attribution = entry.audio.attribution;
  const liveListenUrl = station.streamUrl ?? entry.streamUrl ?? entry.audio.streamUrl;

  // BSH: the spectro timeline = the single audio + clock authority over the
  // station's archived clip. LAZY -- created only now that a station is selected
  // (SEAM 6). A clip-less station (live-listen only) bakes NOTHING: it publishes
  // the live-listen affordance and leaves the authority null, so the reenactment
  // below stays unspawned and no audio is synthesised. The Canvas-overlay HUD
  // mounts to the DOM host sibling SalishScene provides.
  const [authority, setAuthority] = useState<SpectroTimeline["authority"] | null>(null);
  const timelineRef = useRef<SpectroTimeline | null>(null);
  useEffect(() => {
    if (!hasClip || !clipUrl) {
      // Honest live-listen-only state: rig is placed, but there is no archived
      // clip to scrub, classify, or reenact.
      onSliceState({
        status: "live-listen only · no archived clip to scrub",
        presence: false,
        label: "",
        count: 0,
        countBasisLabel: "",
        t: 0,
        attribution,
        streamUrl: liveListenUrl,
        nodeClass: entry.nodeClass,
        hasClip: false,
        behaviors: [],
      });
      setAuthority(null);
      return;
    }
    let alive = true;
    onSliceState({
      status: "baking spectrogram of the real clip…",
      presence: false,
      label: "",
      count: 0,
      countBasisLabel: "",
      t: SLICE_DEFAULT_T,
      attribution,
      streamUrl: liveListenUrl,
      nodeClass: entry.nodeClass,
      hasClip: true,
      behaviors: [],
    });
    createSpectroTimeline({
      url: clipUrl,
      hud: {
        width: 760,
        height: 200,
        caption:
          "measured: STFT of real Orcasound Lab audio · scrub/slow-mo drives the reenactment",
      },
    })
      .then((tl) => {
        if (!alive) {
          tl.dispose();
          return;
        }
        timelineRef.current = tl;
        if (tl.hud && hudHost) tl.hud.mount(hudHost);
        // Station-select is a user gesture, so resuming WebAudio is permitted.
        tl.authority.seek(SLICE_DEFAULT_T, { play: true });
        setAuthority(tl.authority);
      })
      .catch((e) => {
        console.error("slice spectro timeline failed", e);
        onSliceState({
          status: `bake failed: ${String(e)}`,
          presence: false,
          label: "",
          count: 0,
          countBasisLabel: "",
          t: SLICE_DEFAULT_T,
          attribution,
          streamUrl: liveListenUrl,
          nodeClass: entry.nodeClass,
          hasClip: true,
          behaviors: [],
        });
      });
    return () => {
      alive = false;
      timelineRef.current?.dispose();
      timelineRef.current = null;
      setAuthority(null);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hudHost, entry]);

  // BRE: presence-gated reenactment pool from the BAM classification, lit by the
  // pool-only WFX env. worldUnitsPerMeter is the live fit scale (honest depth);
  // body readability comes from the bodyScale on the spawn record (SEAM-aligned
  // with OrcaRig). Added imperatively once the authority exists.
  const poolGroupRef = useRef<THREE.Group>(null);
  const poolRef = useRef<OrcaPool | null>(null);
  const driverRef = useRef<TimelineDriver | null>(null);
  const countBasisRef = useRef<string>("");
  const behaviorsRef = useRef<string[]>([]);
  useEffect(() => {
    if (!authority) return;
    let alive = true;
    let pool: OrcaPool | null = null;
    let driver: TimelineDriver | null = null;
    (async () => {
      const [classification, manifest] = await Promise.all([
        loadClassification(),
        loadClipManifest(),
      ]);
      if (!alive) return;
      // BRE-INTEGRATE: extend the SAME pool to multi-orca. Default (no override)
      // is byte-identical to the landed slice: the fixed "Traveling" clip at
      // BAM's presence-only count (0/1). The labeled `?bsw_demo=N` override
      // spawns N (capped nMax 3) across the DTAG-segment ethogram, stamped
      // `capability_demo` so the chip says "not a model estimate". Either way the
      // motion is the REAL SRKW driver and presence still gates visibility.
      const demoActive = demoCount != null && demoCount >= 1;
      const record = buildSpawnRecord(classification, manifest, {
        anchor: { lat: station.lat, lng: station.lng },
        bodyScale: SLICE_ORCA_BODY_SCALE,
        ...(demoActive
          ? {
              nMax: 3,
              demoCountOverride: demoCount,
              behaviorClasses: SLICE_DEMO_BEHAVIOR_CLASSES,
            }
          : { clipId: SLICE_CLIP_ID }),
      });
      countBasisRef.current = record.countBasisLabel;
      // ONE pool, extended to N (not a second pool). The per-instance controller
      // path is retained: the R08 shared-asset optimization (one mesh/material
      // baked once in ORCA's createOrcaController) stays DEFERRED — per-frame
      // cost is identical at nMax=3 (BUILD finding) and the change is additive to
      // ORCA-owned code. See web/lib/scene/reenactment/WIRING.md.
      pool = createOrcaPool({
        env,
        bounds: TILESET_BOUNDS,
        sceneDepth: SCENE_DEPTH,
        worldUnitsPerMeter: worldUnitsPerMeter ?? 1,
        depthScale: 1,
      });
      await pool.setSpawn(record);
      if (!alive) {
        pool.dispose();
        return;
      }
      // Per-instance modeled DTAG-segment behavior names for the honesty chrome.
      // Each spawned orca shows WHICH measured kinematic clip it is replaying; the
      // shared representativeness disclosure (rendered below) labels all of them
      // as representative SRKW motion, not the recorded animal.
      behaviorsRef.current = pool.instanceLabels().map((l) => l.behaviorName);
      poolGroupRef.current?.add(pool.group);
      driver = createTimelineDriver(authority, pool, classification, { presenceGated: true });
      poolRef.current = pool;
      driverRef.current = driver;
    })().catch((e) => console.error("slice reenactment failed", e));
    return () => {
      alive = false;
      driver?.dispose();
      if (pool) {
        poolGroupRef.current?.remove(pool.group);
        pool.dispose();
      }
      poolRef.current = null;
      driverRef.current = null;
      behaviorsRef.current = [];
    };
  }, [authority, env, station.lat, station.lng, worldUnitsPerMeter, demoCount]);

  // SEAM 3 stands: the reusable POV-selection object drives the EXISTING
  // SalishScene director (intentRefs). It creates NO second director and does
  // NOT advance it here (IntentDirectorRig owns the per-frame director.update).
  // On (re)select it suppresses the WS-INTENT resting orbit + any in-flight
  // journey, then sets the requested POV: hydrophone dive-in by default,
  // top-down adds a slow orbit. Additive only; see
  // web/lib/scene/camera/WIRING-slice-note.md.
  const povCtlRef = useRef<StationPovController | null>(null);
  useEffect(() => {
    const director = intentRefs.directorRef.current;
    if (!director) return;
    intentRefs.journeyRef.current?.cancel();
    intentRefs.journeyRef.current = null;
    intentRefs.orbitRef.current?.stop();
    intentRefs.orbitRef.current = null;
    const controller = createStationPovController({
      director,
      getStation: () => ({ lat: station.lat, lng: station.lng, seabedDepthM }),
      context: (p) => (p === "topdown" ? { orbit: true } : {}),
      initialPov: pov,
    });
    povCtlRef.current = controller;
    controller.setPov(pov);
    return () => {
      controller.stop();
      povCtlRef.current = null;
    };
  }, [intentRefs, station.lat, station.lng, seabedDepthM, pov]);

  // Drive loop: one clock (BSH authority) -> reenactment (BRE). The director is
  // advanced by IntentDirectorRig, not here. Chip state is pushed only when the
  // whole-second playhead, presence, or count changes, so the homepage does not
  // re-render the overlay every frame.
  const camWorld = useRef(new THREE.Vector3());
  const lastPush = useRef<{ t: number; presence: boolean; count: number }>({
    t: -1,
    presence: false,
    count: -1,
  });
  useFrame((_state, dt) => {
    const driver = driverRef.current;
    if (!driver || !authority) return;
    camera.getWorldPosition(camWorld.current);
    driver.update(Math.min(dt, 1 / 30), camWorld.current);
    const s = driver.getState();
    const count = poolRef.current?.count() ?? 0;
    const prev = lastPush.current;
    if (
      Math.floor(s.currentTimeS) !== Math.floor(prev.t) ||
      s.presence !== prev.presence ||
      count !== prev.count
    ) {
      lastPush.current = { t: s.currentTimeS, presence: s.presence, count };
      onSliceState({
        status: "ready",
        presence: s.presence,
        label: s.hudLabel,
        count,
        countBasisLabel: countBasisRef.current,
        t: s.currentTimeS,
        attribution,
        streamUrl: liveListenUrl,
        nodeClass: entry.nodeClass,
        hasClip: true,
        behaviors: behaviorsRef.current,
      });
    }
  });

  return (
    <group name="bsw-slice-mount">
      {/* BST rig + BRE reenactment pool, both anchored at the station and added
          imperatively. The slice adds NO lights and mutates NO scene global; it
          is lit by the live twin (SkyRig sky, OrcaRig scene.environment) and the
          pool-only WFX env. */}
      <group ref={rigGroupRef} />
      <group ref={poolGroupRef} />
    </group>
  );
}
// ----------------------------------------------------------------------------
// END SLICE MOUNT BLOCK
// ============================================================================

// ============================================================================
// BSH-INTEGRATE OCEAN MOUNT -- the interpretive double-diffusion ("lava lamp in
// both directions") layer, single owner BSH-INTEGRATE. This rig is rendered ONLY
// when the layer is toggled on, so it costs exactly 0 when off (default). The
// layer is an additive, transparent mesh with depthWrite:false and no raymarch
// and no extra render pass, so it CANNOT regress WFX's Water2 water (it never
// touches the water material, scene.fog, or scene.environment). It is added to
// the scene imperatively and disposed on unmount.
//
// HONESTY (locked): the moving strata are a stylized view of real Salish Sea
// temperature/salinity structure, NOT measured microstructure and NEVER measured
// orca biosonar perception. The host shows the mandatory interpretive chip
// whenever the layer is on. The stratification is the honestly-labeled analytic
// halocline; the measured CC0 CruiseSalish CTD upgrade is a deferred fast-follow.
//
// DEFERRED (WFX-coordinated, R09): depth-aware plume-clipping that reads a
// read-only WFX Water2Handle depth seam to clip the column to the submerged water
// is intentionally NOT built here. It needs a new seam on the water handle and so
// belongs to a WFX-coordinated pass. Today the layer is self-contained.
function OceanProcessRig({ surfaceY }: { surfaceY: number }) {
  const scene = useThree((s) => s.scene);
  const layerRef = useRef<DoubleDiffusionLayer | null>(null);
  useEffect(() => {
    const layer = createDoubleDiffusionLayer({
      width: SCENE_WIDTH * 1.4,
      height: 70,
      surfaceY,
    });
    layer.setEnabled(true);
    scene.add(layer.object3D);
    layerRef.current = layer;
    return () => {
      scene.remove(layer.object3D);
      layer.dispose();
      layerRef.current = null;
    };
  }, [scene, surfaceY]);
  useFrame((state) => layerRef.current?.update(state.clock.elapsedTime));
  return null;
}
// ===================== END BSH-INTEGRATE OCEAN MOUNT ========================

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
  selectedStation,
  pov,
  demoCount,
  hudHost,
  oceanOn,
  onSliceState,
}: {
  onIntent: (intent: SceneIntent) => void;
  focus?: { lat: number; lng: number } | null;
  beacons: HydrophoneNode[];
  field: SubstrateField | null;
  onTilesError: () => void;
  showPlaceholder: boolean;
  intentRefs: IntentBridgeRefs;
  // SLICE MOUNT wiring (single owner SLICE-INTEGRATE): the station the user
  // selected on the live twin gates the SliceRig; hudHost is the DOM sibling the
  // spectrogram HUD mounts into; onSliceState bubbles the honesty-chip state out
  // to SalishScene's DOM chrome. All three are null/no-op until a station select.
  // pov is the selected camera point of view (BST-INTEGRATE).
  selectedStation: SelectedStation | null;
  pov: StationPov;
  // BRE-INTEGRATE: labeled capability-demo orca count (1..3) from ?bsw_demo, or
  // null for the homepage default (BAM presence-only 0/1).
  demoCount: number | null;
  hudHost: HTMLDivElement | null;
  // BSH-INTEGRATE: when true, mount the additive default-off ocean-process layer.
  oceanOn: boolean;
  onSliceState: (s: SliceState) => void;
}) {
  const [fitRadius, setFitRadius] = useState<number | null>(null);

  // --- WS-SCENIC: fit-accurate world-units-per-metre for the horizon ring, and
  // a shared realism handle so the horizon ring lands at true scale alongside
  // the tiles and a later descentLighting wave can reach the realism lights. ---
  const realismHandleRef = useRef<RealismHandle | null>(null);
  const scenicWorldUnitsPerMeter =
    fitRadius != null ? fitRadius / geoRadiusMeters(TILESET_BOUNDS) : undefined;

  // W-PERFUX: start at the coarse resting caps, then lift to full leaf detail
  // once the user engages the map (handleUserGrab) or a focus journey fires.
  // The hook applies errorTarget/maxDepth live, so flipping this re-refines in
  // place with no tileset rebuild.
  const [detail, setDetail] = useState(false);

  const tiles = useTilesLayer({
    url: FULL_TILESET_URL,
    groupRotationX: -Math.PI / 2,
    fitScaleToWidth: SCENE_WIDTH,
    errorTarget: detail ? DETAIL_ERROR_TARGET : RESTING_ERROR_TARGET,
    maxDepth: detail ? DETAIL_MAX_DEPTH : RESTING_MAX_DEPTH,
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
  // RP2 guard rail: cap zoom-out at ~fitRadius*2 (~120 u) so the user cannot
  // pull back to the same far-back horizon graze the resting frame avoids.
  const maxDistance = fitRadius ? fitRadius * 2 : 120;

  // WS-INTENT: when the user grabs the controls, hand the camera to them by
  // stopping the director's resting orbit and any in-flight journey, so manual
  // orbit is genuinely usable. (onStart only fires while controls are enabled,
  // i.e. at rest or after a journey settles; the scripted beats keep them off.)
  const handleUserGrab = useCallback(() => {
    setDetail(true); // W-PERFUX: lift the startup LoD caps so leaves stream once the user engages.
    const { journeyRef, orbitRef, directorRef } = intentRefs;
    journeyRef.current?.cancel();
    journeyRef.current = null;
    orbitRef.current?.stop();
    orbitRef.current = null;
    directorRef.current?.stop();
  }, [intentRefs]);

  // W-PERFUX: a focus journey (planner map_viewport or scene click) means the
  // user is looking at a place, so lift the caps too and let detail stream there.
  useEffect(() => {
    if (focus) setDetail(true);
  }, [focus]);

  return (
    <>
      {/* WS-INTENT director rig FIRST so it positions the camera before
          Water2Rig's depth pre-pass and the auto-render this frame. */}
      <IntentDirectorRig tiles={tiles} fitRadius={fitRadius} focus={focus} refs={intentRefs} />
      <RealismRig depth={SCENE_DEPTH} exposeHandle={realismHandleRef} />
      <Water2Rig depth={SCENE_DEPTH} />
      {/* ====================================================================
          W4 ORCA MOUNT -- data-driven, WFX-lit SRKW, single owner W4. Mounted
          AFTER Water2Rig so the orca joins the opaque depth pre-pass (no third
          full render) and is lit by the same WFX env handle that informs the
          water uniforms (E4). worldUnitsPerMeter is the live fit scale.
          ==================================================================== */}
      <OrcaRig worldUnitsPerMeter={scenicWorldUnitsPerMeter} />
      {/* ======================= END W4 ORCA MOUNT ========================== */}
      {/* ====================================================================
          SLICE MOUNT -- the thin-but-real B-side slice, single owner
          SLICE-INTEGRATE. Mounted (and torn down) on a hydrophone station
          selection, so nothing here runs on first paint (SEAM 6). It anchors
          the BST rig + BRE reenactment at the selected station as in-scene
          objects (SEAM 1+2: no scene.background/fog/environment writes) and
          drives a dive-to-rig POV on the EXISTING director (SEAM 3). The
          pool-only WFX env lives inside SliceRig and is never assigned to
          scene.environment (SEAM 4). worldUnitsPerMeter is the live fit scale.
          ==================================================================== */}
      {selectedStation && (
        <SliceRig
          station={selectedStation}
          pov={pov}
          field={field}
          worldUnitsPerMeter={scenicWorldUnitsPerMeter}
          demoCount={demoCount}
          intentRefs={intentRefs}
          hudHost={hudHost}
          onSliceState={onSliceState}
        />
      )}
      {/* ======================== END SLICE MOUNT =========================== */}
      {/* ====================================================================
          BSH-INTEGRATE OCEAN MOUNT -- the interpretive double-diffusion layer.
          Rendered only when toggled on (default-off, so 0 cost when off). It is
          additive with depthWrite:false and adds no render pass, so it cannot
          regress the WFX water. Mounted AFTER Water2Rig/OrcaRig; renderOrder on
          the layer keeps it in the additive transparent pass. The mandatory
          interpretive chip is wired in the DOM chrome below.
          ==================================================================== */}
      {oceanOn && <OceanProcessRig surfaceY={SEA_LEVEL_Y} />}
      {/* ===================== END BSH-INTEGRATE OCEAN MOUNT ================= */}
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

  // --- SLICE MOUNT wiring (single owner SLICE-INTEGRATE) --------------------
  // The hydrophone station the user selected on the live twin gates the in-scene
  // SliceRig; sliceState carries the honesty-chip values the rig publishes; the
  // hudHost element (a DOM sibling of the canvas) is where the spectrogram HUD
  // mounts. Selecting a station ALSO still bubbles the intent to the console
  // (the existing onIntent prop) so the hydrophone_signal panel turn is
  // unchanged; the slice just additionally lights up in-scene.
  const [selectedStation, setSelectedStation] = useState<SelectedStation | null>(null);
  const [sliceState, setSliceState] = useState<SliceState | null>(null);
  const [hudHost, setHudHost] = useState<HTMLDivElement | null>(null);
  // BST-INTEGRATE: the selected camera POV (hydrophone dive-in vs top-down).
  // A fresh station selection always opens on the hydrophone dive-in.
  const [pov, setPov] = useState<StationPov>("hydrophone");
  // BRE-INTEGRATE: labeled capability-demo orca count (1..3) from ?bsw_demo. null
  // is the homepage default, where the spawn count is BAM's presence-only 0/1.
  // Multi-orca >1 NEVER appears as a model estimate; this override is stamped
  // `capability_demo` and the chip says so. Inert when the param is absent.
  const [demoCount, setDemoCount] = useState<number | null>(null);
  // BSH-INTEGRATE: the interpretive double-diffusion ocean layer toggle. Default
  // OFF; the layer is only mounted (and the mandatory chip shown) when this is on.
  const [oceanOn, setOceanOn] = useState(false);
  const handleIntent = useCallback((intent: SceneIntent) => {
    if (intent.type === "hydrophone") {
      setSelectedStation({
        id: intent.id ?? null,
        name: intent.name ?? null,
        lat: intent.lat,
        lng: intent.lng,
        streamUrl: intent.streamUrl ?? null,
      });
      setSliceState(null);
      setPov("hydrophone");
    }
    onIntentRef.current?.(intent);
  }, []);

  // Deterministic ACCEPT-capture hook (single owner SLICE-INTEGRATE). A headless
  // render cannot click a 3D hydrophone beacon, so an explicit query param
  // (?station=<lat>,<lng>[,<name>]) pre-selects a station to exercise the live-twin
  // slice mount for the GPU ACCEPT gate. Mirrors the /workbench readParams
  // deterministic-framing convention. Absent in normal navigation, so it is inert
  // for real users; it sets the same selectedStation a beacon click would.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const q = new URLSearchParams(window.location.search);
    const raw = q.get("station");
    if (!raw) return;
    const [latS, lngS, ...rest] = raw.split(",");
    const lat = parseFloat(latS);
    const lng = parseFloat(lngS);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;
    setSelectedStation({
      id: "capture",
      name: rest.length ? decodeURIComponent(rest.join(",")) : "Orcasound Lab",
      lat,
      lng,
      streamUrl: SLICE_STREAM_URL,
    });
    // Optional, additive: ?view=topdown pre-selects the top-down POV for a
    // headless ACCEPT capture. Inert when absent (defaults to the dive-in).
    if (q.get("view") === "topdown") setPov("topdown");
    // BSH-INTEGRATE: ?ocean=1 enables the interpretive double-diffusion layer for
    // a deterministic ACCEPT capture. Inert when absent (the layer stays off).
    if (q.get("ocean") === "1") setOceanOn(true);
    // BRE-INTEGRATE: ?bsw_demo=N (1..3) is the LABELED capability-demo override
    // that spawns multiple orcas across the DTAG-segment ethogram. It is NOT a
    // model estimate (BAM is presence-only) and the chip says so. Inert when
    // absent, so the homepage default stays at the presence-only 0/1 count.
    const demoRaw = q.get("bsw_demo");
    if (demoRaw != null) {
      const n = parseInt(demoRaw, 10);
      if (Number.isFinite(n)) setDemoCount(Math.min(3, Math.max(1, n)));
    }
  }, []);

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
        camera={{ position: [0, 28, 30], fov: 45, near: 1, far: 800 }}
        style={{ width: "100%", height: "100%", background: "linear-gradient(#0b1f33,#08263d)" }}
        onCreated={({ gl }) => {
          gl.setClearColor("#08263d");
          // WFX E1 (R05): the decisive white-sky fix is exposure 0.5 under ACES,
          // so the Preetham dome and the bright PMREM env stop blowing out.
          gl.toneMapping = THREE.ACESFilmicToneMapping;
          gl.toneMappingExposure = 0.5;
        }}
      >
        <TwinScene
          onIntent={handleIntent}
          focus={focus}
          beacons={beacons}
          field={field}
          showPlaceholder={tilesFailed}
          onTilesError={() => {
            if (FALLBACK_TO_MAPS) setAssetError(true);
            else setTilesFailed(true);
          }}
          intentRefs={intentRefs}
          selectedStation={selectedStation}
          pov={pov}
          demoCount={demoCount}
          hudHost={hudHost}
          oceanOn={oceanOn}
          onSliceState={setSliceState}
        />
      </Canvas>
      {/* SLICE MOUNT DOM chrome: the honesty chips + spectrogram HUD host, shown
          only after a station is selected. These are canvas SIBLINGS (no scene
          global writes) styled by the namespaced bsw-* classes in globals.css.
          Every honesty label travels verbatim from the accepted /workbench slice:
          the estimate + confidence chip, "orcas shown: N" presence-gated (0 on
          absence windows), the count basis, the Orcasound attribution + the
          live-listen link, and the mandatory representativeness label. */}
      {selectedStation && (
        <>
          <div className="bsw-hud" ref={setHudHost} />
          {/* BST-INTEGRATE: the reusable camera POV-selection control. Switching
              drives the EXISTING director via createStationPovController in
              SliceRig (SEAM 3). Data-driven from STATION_POVS. */}
          <div className="bsw-pov bsw-glass" role="radiogroup" aria-label="Camera point of view">
            {STATION_POVS.map((p) => (
              <button
                key={p.id}
                type="button"
                role="radio"
                aria-checked={pov === p.id}
                className={pov === p.id ? "bsw-pov-seg bsw-pov-seg-active" : "bsw-pov-seg"}
                onClick={() => setPov(p.id)}
              >
                {p.label}
              </button>
            ))}
          </div>
          {/* BSH-INTEGRATE: interpretive ocean-layer toggle. Default off; turning
              it on mounts the additive double-diffusion layer and shows the
              mandatory interpretive chip below. */}
          <button
            type="button"
            aria-pressed={oceanOn}
            className={oceanOn ? "bsw-ocean-toggle bsw-glass bsw-ocean-toggle-on" : "bsw-ocean-toggle bsw-glass"}
            onClick={() => setOceanOn((v) => !v)}
          >
            interpretive ocean layer · {oceanOn ? "on" : "off"}
          </button>
          {sliceState && (
            <>
              {sliceState.hasClip ? (
                <div className="bsw-estimate bsw-glass">
                  <div className="bsw-estimateLabel">
                    {sliceState.label || sliceState.status || "loading acoustic estimate…"}
                  </div>
                  <div className="bsw-muted">
                    orcas shown: {sliceState.presence ? sliceState.count : 0} · presence-gated
                  </div>
                  {sliceState.countBasisLabel && (
                    <div className="bsw-muted bsw-spaced">{sliceState.countBasisLabel}</div>
                  )}
                  {sliceState.presence && sliceState.behaviors.length > 0 && (
                    <div className="bsw-muted bsw-spaced">
                      DTAG-segment behaviors · {sliceState.behaviors.join(" · ")}
                    </div>
                  )}
                  <div className="bsw-muted bsw-spaced">{sliceState.attribution}</div>
                  {sliceState.streamUrl && (
                    <a
                      href={sliceState.streamUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="bsw-link"
                    >
                      Live-listen (Orcasound)
                    </a>
                  )}
                </div>
              ) : (
                <div className="bsw-estimate bsw-glass">
                  <div className="bsw-estimateLabel">Live-listen only</div>
                  <div className="bsw-muted">No archived clip bound for this station.</div>
                  <div className="bsw-muted bsw-spaced">{sliceState.attribution}</div>
                  {sliceState.streamUrl && (
                    <a
                      href={sliceState.streamUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="bsw-link"
                    >
                      Live-listen (Orcasound)
                    </a>
                  )}
                </div>
              )}
              <div className="bsw-legend bsw-glass">
                <strong>{selectedStation.name ?? "Hydrophone station"}</strong> (
                {selectedStation.lat.toFixed(4)}, {selectedStation.lng.toFixed(4)}) ·{" "}
                {sliceState.status}
                {sliceState.hasClip ? (
                  <>
                    <div className="bsw-spaced">measured: audio · spectrogram · SRKW DTAG motion</div>
                    <div>
                      modeled: {sliceState.nodeClass} equipment mesh · acoustic inference · 3D
                      placement
                    </div>
                    <div className="bsw-repr">
                      Kinematics are representative SRKW DTAG motion, not the recorded animal.
                    </div>
                  </>
                ) : (
                  <>
                    <div className="bsw-spaced">live-listen only · no archived clip to scrub</div>
                    <div>modeled: {sliceState.nodeClass} equipment mesh · 3D placement</div>
                  </>
                )}
              </div>
            </>
          )}
        </>
      )}
      {/* BSH-INTEGRATE: the mandatory interpretive chip. Rendered whenever the
          ocean layer is on (independent of the slice chrome) so the locked label
          is ALWAYS on screen while the layer can show. The layer is a stylized
          view of real Salish Sea temperature and salinity structure, never
          measured orca biosonar perception (honesty lock). */}
      {oceanOn && (
        <div className="bsw-ocean-chip bsw-glass" role="note">
          <div className="bsw-ocean-chipLabel">
            <span className="bsw-ocean-dot" aria-hidden />
            {INTERPRETIVE_OCEAN_LABEL}
          </div>
          <div className="bsw-muted bsw-spaced">{INTERPRETIVE_OCEAN_DETAIL}</div>
        </div>
      )}
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
