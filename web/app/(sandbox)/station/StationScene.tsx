"use client";

// STATION sandbox: the modeled hydrophone-equipment rig placed at the real
// Orcasound Lab station on the modeled seabed, an audio player bound to the one
// real archived clip (MEASURED), and a camera POV selector (hydrophone POV +
// top-down) that drives the existing Camera Director. Proves the lane's modules
// before the O0-gated integrator mounts them into SalishScene.
//
// Deterministic headless framing via a SINGLE query param (the render host
// passes the route as one arg, so an unescaped "&" would break a multi-param
// query string):
//   /station              default = hydrophone POV, underwater, paused
//   /station?view=topdown top-down station overview
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
  makeHydrophoneRig,
  stationSeabedPose,
  StationPlayer,
  runStationPOV,
  type HydrophoneRig,
  type StationPov,
  type StationPovHandle,
} from "@/lib/scene/hydrophone";
import PovChip from "./PovChip";

// --- real, verifiable facts -------------------------------------------------

// Orcasound Lab, Haro Strait (matches PROVENANCE.md for the archived clip).
const LAT = 48.5583362;
const LNG = -123.1735774;

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
const FALLBACK_DEPTH_M = -18;

const AUDIO_URL = "/hydrophone/slice/orcasound_lab_20210825_srkw.m4a";
const STREAM_URL = "https://live.orcasound.net/listen/orcasound-lab";
const ATTRIBUTION = "Audio: Orcasound (CC BY-NC-SA 4.0)";

const UNDERWATER_TINT = "#0c3a40";

interface Params {
  pov: StationPov;
}

function readParams(): Params {
  const p: Params = { pov: "hydrophone" };
  if (typeof window === "undefined") return p;
  const q = new URLSearchParams(window.location.search);
  if (q.get("view") === "topdown") p.pov = "topdown";
  if (q.get("view") === "hydrophone") p.pov = "hydrophone";
  return p;
}

function SceneContent({
  pov,
  interacted,
}: {
  pov: StationPov;
  interacted: boolean;
}) {
  const scene = useThree((s) => s.scene);
  const camera = useThree((s) => s.camera);

  // Modeled seabed pose for the rig (NEVER clamped to the surface).
  const pose = useMemo(
    () =>
      stationSeabedPose(LAT, LNG, SLICE_BOUNDS, SCENE_DEPTH, {
        worldUnitsPerMeter: WUPM,
        fallbackDepthM: FALLBACK_DEPTH_M,
      }),
    [],
  );
  const seabedDepthM = pose[1] / WUPM;

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

  // Build the modeled rig once and place its root on the modeled seabed.
  const rigRef = useRef<HydrophoneRig | null>(null);
  const rigGroupRef = useRef<THREE.Group>(null);
  useEffect(() => {
    const rig = makeHydrophoneRig({
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
  }, [pose, seabedDepthM]);

  // Drive the POV through the director. The deterministic (non-interacted) shot
  // snaps to the end pose so a headless screenshot is reproducible; a top-down
  // overview is framed as a static orbit (speed 0). After the user picks a POV
  // the move animates, and the top-down orbits slowly.
  const povHandleRef = useRef<StationPovHandle | null>(null);
  useEffect(() => {
    const director = directorRef.current;
    if (!director) return;
    handleRef.current.camera = camera as THREE.PerspectiveCamera;

    povHandleRef.current = runStationPOV(
      pov,
      { lat: LAT, lng: LNG, seabedDepthM },
      director,
      pov === "topdown"
        ? { orbit: true, orbitSpeed: interacted ? 0.03 : 0 }
        : {},
    );

    if (!interacted) {
      // Settle the eased fly-in immediately for a deterministic paused frame.
      director.update(10);
    }

    return () => {
      povHandleRef.current?.stop();
      povHandleRef.current = null;
    };
  }, [pov, interacted, camera, seabedDepthM]);

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

function useStationPlayer() {
  const playerRef = useRef<StationPlayer | null>(null);
  const [status, setStatus] = useState<string>("idle");
  const [error, setError] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    const player = new StationPlayer({
      audioUrl: AUDIO_URL,
      streamUrl: STREAM_URL,
      attribution: ATTRIBUTION,
    });
    playerRef.current = player;
    setStatus("loading");
    player
      .load()
      .then(() => {
        setStatus("ready");
        setDuration(player.getDuration());
        // Seam: publish the player so the spectrogram lane can read the SAME
        // decoded real AudioBuffer (player.getAudioBuffer()).
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
  }, []);

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
  const [pov, setPov] = useState<StationPov>(params.pov);
  const [interacted, setInteracted] = useState(false);
  const player = useStationPlayer();

  const onPov = (next: StationPov) => {
    setInteracted(true);
    setPov(next);
  };

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
        <SceneContent pov={pov} interacted={interacted} />
      </Canvas>

      <PovChip value={pov} onChange={onPov} />

      {/* Station audio player (MEASURED clip) + attribution (must be shown). */}
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
        <div style={{ opacity: 0.85 }}>{ATTRIBUTION}</div>
        <a href={STREAM_URL} target="_blank" rel="noreferrer" style={{ color: "#8fd0ff", opacity: 0.85 }}>
          Live-listen: orcasound-lab
        </a>
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
          maxWidth: 420,
        }}
      >
        <strong>Orcasound Lab station</strong> (48.5583362, -123.1735774)
        <div style={{ marginTop: 4 }}>measured: audio · modeled: equipment mesh</div>
        <div style={{ opacity: 0.7, marginTop: 4 }}>
          POV {pov}. Rig on the modeled seabed (~{Math.abs(FALLBACK_DEPTH_M)} m). Camera driven by the
          shared Camera Director.
        </div>
      </div>
    </div>
  );
}
