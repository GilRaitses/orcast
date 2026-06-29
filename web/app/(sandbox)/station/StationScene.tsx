"use client";

// STATION sandbox: a real MULTI-STATION hydrophone player.
//
// Select any real Orcasound node inside the rendered tileset extent (the same
// set GET /api/live-hydrophones serves: Orcasound Lab, North San Juan Channel,
// Andrews Bay). On select, the MODELED equipment variant for that node class
// (cabled shore hydrophone vs subsurface mooring) is placed at the station's
// real lat/lng on the modeled seabed, its audio is bound (the one license-clear
// archived clip for Orcasound Lab, MEASURED; live-listen link only for the
// others, never synthesised), and the reusable camera POV-selection object
// switches the shared Camera Director between the hydrophone POV and top-down.
// Proves the lane's modules before the O0-gated integrator mounts them.
//
// Deterministic headless framing via single query params (the render host
// passes the route as one arg):
//   /station                     default = Orcasound Lab, hydrophone POV, paused
//   /station?view=topdown        top-down overview of the default station
//   /station?station=north-sjc   the North San Juan Channel mooring, hydrophone POV
//
// Built on three + WebAudio only. Imports the Camera Director + sceneIntent
// (read-only convergence files) but never modifies them.

import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { createCameraDirector } from "@/lib/scene/camera/director";
import type { CameraDirector, CameraDirectorHandle } from "@/lib/scene/camera/types";
import { sceneDepth, type HeightmapBounds } from "@/lib/sceneIntent";
import {
  makeStationEquipment,
  stationSeabedPoseForEntry,
  StationPlayer,
  createStationPovController,
  listSelectableStations,
  getStation,
  stationPlayerOptions,
  type EquipmentRig,
  type StationCatalogEntry,
  type StationPov,
  type StationPovController,
} from "@/lib/scene/hydrophone";
import PovChip from "./PovChip";
import StationChip from "./StationChip";

// Slice bounds from SalishScene TILESET_BOUNDS.
const SLICE_BOUNDS: HeightmapBounds = {
  min_lat: 48.4,
  max_lat: 48.7,
  min_lng: -123.25,
  max_lng: -122.75,
};
const SCENE_DEPTH = sceneDepth(SLICE_BOUNDS);

// Sandbox visible scale: 1 metre = 1 scene unit (mirrors the orca sandbox), so
// the equipment rig and its true-depth seabed placement read clearly.
const WUPM = 1;

const UNDERWATER_TINT = "#0c3a40";

const STATIONS = listSelectableStations();
const DEFAULT_STATION = STATIONS[0];

interface Params {
  pov: StationPov;
  stationId: string;
}

function readParams(): Params {
  const p: Params = { pov: "hydrophone", stationId: DEFAULT_STATION.id };
  if (typeof window === "undefined") return p;
  const q = new URLSearchParams(window.location.search);
  if (q.get("view") === "topdown") p.pov = "topdown";
  if (q.get("view") === "hydrophone") p.pov = "hydrophone";
  const slug = q.get("station");
  const match = slug ? getStation(slug) : null;
  if (match && match.withinTilesetExtent) p.stationId = match.id;
  return p;
}

function SceneContent({
  station,
  pov,
  interacted,
}: {
  station: StationCatalogEntry;
  pov: StationPov;
  interacted: boolean;
}) {
  const scene = useThree((s) => s.scene);
  const camera = useThree((s) => s.camera);

  // Modeled seabed pose for the selected station (NEVER clamped to the surface).
  const pose = useMemo(
    () =>
      stationSeabedPoseForEntry(station, SLICE_BOUNDS, SCENE_DEPTH, {
        worldUnitsPerMeter: WUPM,
      }),
    [station],
  );
  const seabedDepthM = pose[1] / WUPM;

  // Keep the live station geo in a ref so the POV controller always re-frames
  // the currently-selected node when it switches or refreshes.
  const stationGeoRef = useRef({ lat: station.lat, lng: station.lng, seabedDepthM });
  stationGeoRef.current = { lat: station.lat, lng: station.lng, seabedDepthM };

  // Underwater Beer-Lambert-ish tint, mirroring the orca sandbox under-view.
  useEffect(() => {
    const prevBg = scene.background;
    const prevFog = scene.fog;
    scene.background = new THREE.Color(UNDERWATER_TINT);
    scene.fog = new THREE.FogExp2(0x0c3a40, 0.003);
    return () => {
      scene.background = prevBg;
      scene.fog = prevFog;
    };
  }, [scene]);

  // The mutable director handle. The director reads it lazily each frame, so the
  // camera can be attached after creation (mirrors SalishScene.IntentDirectorRig).
  const handleRef = useRef<CameraDirectorHandle>({
    camera: null,
    controls: null,
    bounds: SLICE_BOUNDS,
    sceneDepth: SCENE_DEPTH,
    group: null,
    worldUnitsPerMeter: WUPM,
    fitRadius: null,
    getSurfaceY: null,
  });
  const directorRef = useRef<CameraDirector | null>(null);
  if (!directorRef.current) {
    directorRef.current = createCameraDirector(handleRef.current);
  }

  // The reusable POV-selection object, created once and bound to the director.
  const povRef = useRef<StationPovController | null>(null);
  if (!povRef.current && directorRef.current) {
    povRef.current = createStationPovController({
      director: directorRef.current,
      getStation: () => stationGeoRef.current,
      context: (p) => (p === "topdown" ? { orbit: true } : {}),
      initialPov: pov,
    });
  }

  // Build the MODELED equipment variant for this station's node class and place
  // its root on the modeled seabed. Rebuilt whenever the station changes.
  const rigRef = useRef<EquipmentRig | null>(null);
  const rigGroupRef = useRef<THREE.Group>(null);
  useEffect(() => {
    const rig = makeStationEquipment(station.nodeClass, {
      seabedDepthM,
      worldUnitsPerMeter: WUPM,
    });
    rig.root.position.set(pose[0], pose[1], pose[2]);
    rigRef.current = rig;
    rigGroupRef.current?.add(rig.root);
    return () => {
      const r = rigRef.current;
      if (r) {
        rigGroupRef.current?.remove(r.root);
        r.dispose();
        rigRef.current = null;
      }
    };
  }, [station.nodeClass, pose, seabedDepthM]);

  // Drive the POV through the reusable controller. The deterministic
  // (non-interacted) shot snaps to the end pose so a headless screenshot is
  // reproducible; a top-down overview is framed as a static orbit (speed 0).
  // After the user picks a POV (or station) the move animates and the top-down
  // orbits slowly.
  useEffect(() => {
    const controller = povRef.current;
    if (!controller) return;
    handleRef.current.camera = camera as THREE.PerspectiveCamera;

    controller.setPov(
      pov,
      pov === "topdown" ? { orbit: true, orbitSpeed: interacted ? 0.03 : 0 } : {},
    );

    if (!interacted) {
      // Settle the eased fly-in immediately for a deterministic paused frame.
      directorRef.current?.update(10);
    }

    return () => {
      controller.stop();
    };
  }, [pov, interacted, camera, station, seabedDepthM]);

  // Per-frame: keep the handle's camera live and advance the director. The
  // deterministic shot has already settled, so this is a no-op there; the
  // interactive shot animates the fly-in and the slow top-down orbit here.
  useFrame((_state, dt) => {
    handleRef.current.camera = camera as THREE.PerspectiveCamera;
    directorRef.current?.update(Math.min(dt, 1 / 30));
  });

  const sunDir = useMemo(() => new THREE.Vector3(0.4, 1, 0.2).normalize(), []);

  return (
    <group>
      <ambientLight intensity={0.45} />
      <directionalLight position={sunDir.clone().multiplyScalar(60).toArray()} intensity={0.9} color={0xbfe2ff} />
      <hemisphereLight args={["#bfe2ff", "#06262f", 0.4]} />

      {/* Modeled seabed plane at the rig's seabed Y. */}
      <mesh rotation-x={-Math.PI / 2} position={[pose[0], pose[1], pose[2]]}>
        <planeGeometry args={[400, 400]} />
        <meshStandardMaterial color="#1d2a26" roughness={0.95} metalness={0} />
      </mesh>

      {/* Water surface plane at Y=0 (the float reaches it). */}
      <mesh rotation-x={-Math.PI / 2} position={[pose[0], 0, pose[2]]}>
        <planeGeometry args={[400, 400]} />
        <meshPhysicalMaterial
          color="#0e3a40"
          roughness={0.15}
          metalness={0}
          transparent
          opacity={0.45}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* The modeled hydrophone rig is added here imperatively. */}
      <group ref={rigGroupRef} />

      {/*
        INTEGRATOR MOUNT SLOT (3D): the reenactment orcas (web/lib/scene/reenactment/)
        will be composed here by the O0-gated orchestrator, anchored at the station.
        This lane does NOT import reenactment/ so the route compiles standalone.
      */}
      <group name="bsw-reenactment-mount-slot" position={[pose[0], pose[1], pose[2]]} />
    </group>
  );
}

function useStationPlayer(station: StationCatalogEntry) {
  const playerRef = useRef<StationPlayer | null>(null);
  const [status, setStatus] = useState<string>("idle");
  const [error, setError] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    const player = new StationPlayer(stationPlayerOptions(station));
    playerRef.current = player;
    setStatus("loading");
    setError(null);
    setPlaying(false);
    setCurrentTime(0);
    setDuration(0);
    player
      .load()
      .then(() => {
        setStatus(player.getStatus());
        setDuration(player.getDuration());
        // Seam: publish the player so the spectrogram lane can read the SAME
        // decoded real AudioBuffer (player.getAudioBuffer()). Only meaningful
        // for a station with a bound clip.
        (window as unknown as { __STATION_PLAYER?: StationPlayer }).__STATION_PLAYER = player;
      })
      .catch((e) => {
        setStatus("error");
        setError(e instanceof Error ? e.message : String(e));
      });

    const id = window.setInterval(() => {
      const p = playerRef.current;
      if (!p) return;
      setPlaying(p.isPlaying());
      setCurrentTime(p.getCurrentTime());
    }, 200);

    return () => {
      window.clearInterval(id);
      const p = playerRef.current;
      if (p) {
        delete (window as unknown as { __STATION_PLAYER?: StationPlayer }).__STATION_PLAYER;
        p.dispose();
        playerRef.current = null;
      }
    };
  }, [station]);

  const toggle = () => {
    const p = playerRef.current;
    if (!p || p.getStatus() !== "ready") return;
    if (p.isPlaying()) p.pause();
    else p.play();
    setPlaying(p.isPlaying());
  };

  return { status, error, playing, currentTime, duration, toggle };
}

function fmt(t: number): string {
  if (!Number.isFinite(t)) return "0:00";
  const m = Math.floor(t / 60);
  const s = Math.floor(t % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function StationScene() {
  const params = useMemo(readParams, []);
  const [stationId, setStationId] = useState<string>(params.stationId);
  const [pov, setPov] = useState<StationPov>(params.pov);
  const [interacted, setInteracted] = useState(false);

  const station = useMemo(
    () => getStation(stationId) ?? DEFAULT_STATION,
    [stationId],
  );
  const player = useStationPlayer(station);

  const onPov = (next: StationPov) => {
    setInteracted(true);
    setPov(next);
  };
  const onStation = (id: string) => {
    setInteracted(true);
    setStationId(id);
  };

  const hasClip = station.audio.kind === "archived-clip";

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <Canvas
        camera={{ position: [10, -8, 10], fov: 50, near: 0.1, far: 2000 }}
        style={{ width: "100%", height: "100%" }}
        gl={{ antialias: true }}
        onCreated={({ gl }) => {
          gl.toneMapping = THREE.ACESFilmicToneMapping;
          gl.toneMappingExposure = 1.0;
        }}
      >
        <SceneContent station={station} pov={pov} interacted={interacted} />
      </Canvas>

      <StationChip stations={STATIONS} value={station.id} onChange={onStation} />
      <PovChip value={pov} onChange={onPov} />

      {/* Station audio player + attribution (must be shown). */}
      <div
        style={{
          position: "absolute",
          right: 12,
          top: 12,
          display: "flex",
          flexDirection: "column",
          gap: 6,
          padding: "12px 14px",
          borderRadius: 10,
          font: "12px/1.4 ui-sans-serif, system-ui, sans-serif",
          color: "#cfe6ff",
          background: "rgba(8,38,61,0.84)",
          maxWidth: 280,
        }}
      >
        {hasClip ? (
          <>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <button
                type="button"
                onClick={player.toggle}
                disabled={player.status !== "ready"}
                style={{
                  appearance: "none",
                  border: "1px solid rgba(160,210,255,0.25)",
                  borderRadius: 8,
                  padding: "6px 14px",
                  background: player.status === "ready" ? "rgba(95,208,255,0.16)" : "rgba(95,208,255,0.06)",
                  color: player.status === "ready" ? "#5fd0ff" : "rgba(207,230,255,0.5)",
                  cursor: player.status === "ready" ? "pointer" : "default",
                }}
              >
                {player.playing ? "Pause" : "Play"}
              </button>
              <span style={{ fontVariantNumeric: "tabular-nums" }}>
                {fmt(player.currentTime)} / {fmt(player.duration)}
              </span>
            </div>
            {player.status === "loading" && <div style={{ opacity: 0.7 }}>Loading real clip…</div>}
            {player.status === "error" && (
              <div style={{ color: "#ff9b8a" }}>Audio unavailable: {player.error}</div>
            )}
          </>
        ) : (
          <div style={{ opacity: 0.85 }}>
            No archived clip bound for this station. Live-listen only.
          </div>
        )}
        <div style={{ opacity: 0.85 }}>{station.audio.attribution}</div>
        {station.streamUrl && (
          <a href={station.streamUrl} target="_blank" rel="noreferrer" style={{ color: "#8fd0ff", opacity: 0.85 }}>
            Live-listen: {station.slug}
          </a>
        )}
      </div>

      {/*
        INTEGRATOR MOUNT SLOT (HUD): the spectrogram HUD overlay
        (web/lib/scene/hud/) will be composed here by the orchestrator, reading
        the SAME decoded AudioBuffer via window.__STATION_PLAYER.getAudioBuffer().
        This lane does NOT import hud/ so the route compiles standalone.
      */}

      {/* HUD honesty caption. */}
      <div
        style={{
          position: "absolute",
          left: 12,
          bottom: 12,
          padding: "10px 12px",
          borderRadius: 8,
          font: "11px/1.5 ui-monospace, monospace",
          color: "#cfe6ff",
          background: "rgba(8,38,61,0.84)",
          maxWidth: 460,
        }}
      >
        <strong>{station.name}</strong> ({station.lat.toFixed(6)}, {station.lng.toFixed(6)})
        <div style={{ marginTop: 4 }}>
          {hasClip ? "measured: audio · " : "live-listen only · "}modeled: equipment mesh (
          {station.nodeClass})
        </div>
        <div style={{ opacity: 0.7, marginTop: 4 }}>
          POV {pov}. Rig on the modeled seabed (~{Math.abs(station.modeledFallbackDepthM)} m,
          modeled fallback; CUDEM substrate supersedes at integrate). Camera driven by the shared
          Camera Director.
        </div>
      </div>
    </div>
  );
}
