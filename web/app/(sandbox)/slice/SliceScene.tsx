"use client";

// SLICE gate (ORCHESTRATOR-owned composition; NOT a lane file). Wires all four
// disjoint net-new lanes into the one real vertical slice, end to end:
//
//   BST  modeled hydrophone-equipment rig on the modeled seabed at the real
//        Orcasound Lab station + the camera POVs that drive the Camera Director
//   BSH  Web Worker STFT spectrogram of the ONE real clip + the scrubbable HUD;
//        its SpectroTimelineAuthority is the single audio + clock authority
//   BAM  precomputed REAL acoustic-silhouette inference JSON (estimate +
//        confidence per window); presence gates spawn + the HUD label
//   BRE  multi-orca reenactment: each orca is the REAL SRKW DTAG driver, sampled
//        at the playhead's clip window, presence-gated, with the mandatory
//        representativeness label
//
// One clip, one decode, one clock: BSH's engine plays the audio AND is the
// timeline the reenactment follows. The station player UI is exercised in
// /station; here the attribution + live-listen link are shown statically so a
// single audio source owns the clock.
//
// Deterministic headless framing via a SINGLE query param (the render host
// passes the route as one arg, so an unescaped "&" would background the shell):
//   /slice                 establishing column shot, presence-positive, paused
//   /slice?view=hydrophone  hydrophone POV (drives the Camera Director)
//   /slice?view=topdown     top-down station overview (Camera Director)
//   /slice?t=30             seek the shared playhead to 30 s (paused)
//
// This file imports the four lanes' PUBLIC barrels only; it edits no lane file
// and no convergence file.

import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";

import { sceneDepth, type HeightmapBounds } from "@/lib/sceneIntent";
import { createCameraDirector } from "@/lib/scene/camera/director";
import type { CameraDirector, CameraDirectorHandle } from "@/lib/scene/camera/types";
import { makeSun } from "@/app/components/scene/realism/sun";
import { skyColor } from "@/app/components/scene/realism/atmosphere";

import {
  makeHydrophoneRig,
  stationSeabedPose,
  runStationPOV,
  type HydrophoneRig,
  type StationPov,
  type StationPovHandle,
} from "@/lib/scene/hydrophone";

import {
  createSpectroTimeline,
  type SpectroTimeline,
} from "@/lib/scene/hud/spectro";

import { makeSandboxWfxEnv, type WfxEnvHandle } from "@/lib/scene/orca";

import {
  buildSpawnRecord,
  createOrcaPool,
  createTimelineDriver,
  loadClassification,
  loadClipManifest,
  type OrcaPool,
  type TimelineDriver,
} from "@/lib/scene/reenactment";

// --- real, verifiable facts (match the lane provenance) ---------------------

// Orcasound Lab, Haro Strait (matches the clip PROVENANCE + the station lane).
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

// 1 metre = 1 scene unit (mirrors the orca + station sandboxes).
const WUPM = 1;
const FALLBACK_DEPTH_M = -18;

const CLIP_URL = "/hydrophone/slice/orcasound_lab_20210825_srkw.m4a";
const STREAM_URL = "https://live.orcasound.net/listen/orcasound-lab";
const ATTRIBUTION = "Audio: Orcasound (CC BY-NC-SA 4.0)";

// The reenactment orca plays the measured "Traveling" clip (near-surface, reads
// clearly above the seabed rig). Acoustic presence picks WHETHER it spawns.
const CLIP_ID = "Traveling";

const UNDERWATER_TINT = "#0c3a40";
const SCENE_TIME = new Date("2026-06-27T20:00:00Z");

type View = "establish" | "hydrophone" | "topdown";

interface Params {
  view: View;
  t: number;
}

// Presence-positive window (BAM classification conf ~0.85) so the deterministic
// gate frame shows the spawned orca, not an empty presence-gated scene.
const DEFAULT_T = 61.5;

function readParams(): Params {
  const p: Params = { view: "establish", t: DEFAULT_T };
  if (typeof window === "undefined") return p;
  const q = new URLSearchParams(window.location.search);
  const v = q.get("view");
  if (v === "hydrophone" || v === "topdown" || v === "establish") p.view = v;
  const t = parseFloat(q.get("t") ?? "");
  if (Number.isFinite(t)) p.t = t;
  return p;
}

function SceneContent({
  view,
  interacted,
  authority,
  onDriverState,
}: {
  view: View;
  interacted: boolean;
  authority: SpectroTimeline["authority"] | null;
  onDriverState: (s: { presence: boolean; label: string; t: number; count: number }) => void;
}) {
  const gl = useThree((s) => s.gl);
  const scene = useThree((s) => s.scene);
  const camera = useThree((s) => s.camera);

  const sun = useMemo(() => makeSun(SCENE_TIME, 48.5, -123), []);
  const sky = useMemo(() => skyColor(sun.elevationDeg), [sun]);

  // WFX env stand-in (PMREM sky + sun + underwater absorption), identical to the
  // orca sandbox. Replaced by the real WFX handle at integrate; no lane changes.
  const env = useMemo<WfxEnvHandle>(() => {
    const pmrem = new THREE.PMREMGenerator(gl);
    return makeSandboxWfxEnv({
      sunDirection: sun.direction,
      sunColor: sun.color,
      sunIntensity: sun.intensity,
      skyColor: sky,
      pmrem,
    });
  }, [gl, sun, sky]);

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

  useEffect(() => {
    const prevBg = scene.background;
    const prevFog = scene.fog;
    const prevEnv = scene.environment;
    scene.environment = env.pmremEnvironment;
    scene.background = new THREE.Color(UNDERWATER_TINT);
    scene.fog = new THREE.FogExp2(0x0c3a40, 0.0035);
    return () => {
      scene.background = prevBg;
      scene.fog = prevFog;
      scene.environment = prevEnv;
    };
  }, [scene, env]);

  // --- BST: rig on the modeled seabed ---------------------------------------
  const rigRef = useRef<HydrophoneRig | null>(null);
  const rigGroupRef = useRef<THREE.Group>(null);
  useEffect(() => {
    const rig = makeHydrophoneRig({ seabedDepthM, worldUnitsPerMeter: WUPM });
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

  // --- BST: Camera Director + POVs ------------------------------------------
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

  const povHandleRef = useRef<StationPovHandle | null>(null);
  useEffect(() => {
    handleRef.current.camera = camera as THREE.PerspectiveCamera;

    if (view === "establish") {
      // Orchestrator establishing column shot: 3/4 side, framing the seabed rig
      // up through the water column to the surface float + the orca above it.
      povHandleRef.current?.stop();
      povHandleRef.current = null;
      camera.position.set(pose[0] + 26, -7, pose[2] + 26);
      camera.lookAt(pose[0], -9, pose[2]);
      camera.updateProjectionMatrix();
      return;
    }

    const director = directorRef.current;
    if (!director) return;
    povHandleRef.current = runStationPOV(
      view,
      { lat: LAT, lng: LNG, seabedDepthM },
      director,
      view === "topdown" ? { orbit: true, orbitSpeed: interacted ? 0.03 : 0 } : {},
    );
    if (!interacted) director.update(10); // settle the eased fly-in for a paused frame
    return () => {
      povHandleRef.current?.stop();
      povHandleRef.current = null;
    };
  }, [view, interacted, camera, seabedDepthM, pose]);

  // --- BRE: reenactment pool from BAM classification ------------------------
  const poolRef = useRef<OrcaPool | null>(null);
  const driverRef = useRef<TimelineDriver | null>(null);
  const poolGroupRef = useRef<THREE.Group>(null);
  const [poolReady, setPoolReady] = useState(false);

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
      const record = buildSpawnRecord(classification, manifest, {
        anchor: { lat: LAT, lng: LNG },
        clipId: CLIP_ID,
      });
      pool = createOrcaPool({
        env,
        bounds: SLICE_BOUNDS,
        sceneDepth: SCENE_DEPTH,
        worldUnitsPerMeter: WUPM,
        depthScale: 1, // measured depth, true scale
      });
      await pool.setSpawn(record);
      if (!alive) {
        pool.dispose();
        return;
      }
      poolGroupRef.current?.add(pool.group);
      driver = createTimelineDriver(authority, pool, classification, { presenceGated: true });
      poolRef.current = pool;
      driverRef.current = driver;
      setPoolReady(true);
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
      setPoolReady(false);
    };
  }, [authority, env]);

  // --- drive loop: one clock (BSH) -> reenactment (BRE) + Camera Director ----
  const camWorld = useRef(new THREE.Vector3());
  useFrame((_state, dt) => {
    const clamped = Math.min(dt, 1 / 30);
    handleRef.current.camera = camera as THREE.PerspectiveCamera;
    if (view !== "establish") directorRef.current?.update(clamped);

    const driver = driverRef.current;
    if (driver && authority) {
      camera.getWorldPosition(camWorld.current);
      driver.update(clamped, camWorld.current);
      const s = driver.getState();
      onDriverState({
        presence: s.presence,
        label: s.hudLabel,
        t: s.currentTimeS,
        count: poolRef.current?.count() ?? 0,
      });
    }
  });

  return (
    <group>
      <ambientLight intensity={0.4} />
      <directionalLight
        position={sun.direction.clone().multiplyScalar(60).toArray()}
        intensity={sun.intensity * 0.7}
        color={sun.color.getHex()}
      />
      <hemisphereLight args={["#bfe2ff", "#06262f", 0.4]} />

      {/* Modeled seabed plane at the rig's seabed Y. */}
      <mesh rotation-x={-Math.PI / 2} position={[pose[0], pose[1], pose[2]]}>
        <planeGeometry args={[600, 600]} />
        <meshStandardMaterial color="#1d2a26" roughness={0.95} metalness={0} />
      </mesh>

      {/* Water surface plane at Y=0 (the float reaches it). */}
      <mesh rotation-x={-Math.PI / 2} position={[pose[0], 0, pose[2]]}>
        <planeGeometry args={[600, 600]} />
        <meshPhysicalMaterial
          color="#0e3a40"
          roughness={0.15}
          metalness={0}
          transparent
          opacity={0.4}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* BST rig (added imperatively). */}
      <group ref={rigGroupRef} />

      {/* BRE reenactment pool, anchored at the station (added imperatively). */}
      <group ref={poolGroupRef} />
      {!poolReady && null}
    </group>
  );
}

function fmt(t: number): string {
  if (!Number.isFinite(t)) return "0:00";
  const m = Math.floor(t / 60);
  const s = Math.floor(t % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function SliceScene() {
  const params = useMemo(readParams, []);
  const [view, setView] = useState<View>(params.view);
  const [interacted, setInteracted] = useState(false);

  const hostRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<SpectroTimeline | null>(null);
  const [authority, setAuthority] = useState<SpectroTimeline["authority"] | null>(null);
  const [status, setStatus] = useState("baking spectrogram of the real clip…");
  const [driverState, setDriverState] = useState<{
    presence: boolean;
    label: string;
    t: number;
    count: number;
  }>({ presence: false, label: "", t: params.t, count: 0 });

  // BSH timeline = the single audio + clock authority over the ONE real clip.
  useEffect(() => {
    let alive = true;
    createSpectroTimeline({
      url: CLIP_URL,
      hud: {
        width: 760,
        height: 200,
        caption: "measured: STFT of real Orcasound Lab audio · scrub/slow-mo drives the reenactment",
      },
    })
      .then((tl) => {
        if (!alive) {
          tl.dispose();
          return;
        }
        timelineRef.current = tl;
        if (tl.hud && hostRef.current) tl.hud.mount(hostRef.current);
        tl.authority.seek(params.t, { play: false });
        setAuthority(tl.authority);
        setStatus("ready");
      })
      .catch((e) => {
        console.error("slice spectro timeline failed", e);
        setStatus(`bake failed: ${String(e)}`);
      });
    return () => {
      alive = false;
      timelineRef.current?.dispose();
      timelineRef.current = null;
      setAuthority(null);
    };
  }, [params.t]);

  const onView = (next: View) => {
    setInteracted(true);
    setView(next);
  };

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <Canvas
        camera={{ position: [26, -7, 26], fov: 50, near: 0.1, far: 2000 }}
        style={{ width: "100%", height: "100%" }}
        gl={{ antialias: true }}
        onCreated={({ gl }) => {
          gl.toneMapping = THREE.ACESFilmicToneMapping;
          gl.toneMappingExposure = 1.0;
        }}
      >
        <SceneContent
          view={view}
          interacted={interacted}
          authority={authority}
          onDriverState={setDriverState}
        />
      </Canvas>

      {/* DOM-sibling spectrogram HUD (BSH), mounted imperatively. */}
      <div ref={hostRef} />

      {/* View selector (drives BST's Camera Director for the POV views). */}
      <div
        style={{
          position: "absolute",
          left: 12,
          top: 12,
          display: "flex",
          gap: 6,
          font: "11px ui-monospace, monospace",
        }}
      >
        {(["establish", "hydrophone", "topdown"] as View[]).map((v) => (
          <button
            key={v}
            type="button"
            onClick={() => onView(v)}
            style={{
              appearance: "none",
              border: "1px solid rgba(120,180,220,0.4)",
              borderRadius: 6,
              padding: "4px 10px",
              cursor: "pointer",
              color: view === v ? "#04161f" : "#cfe6ff",
              background: view === v ? "rgba(180,220,255,0.92)" : "rgba(20,70,100,0.9)",
            }}
          >
            {v}
          </button>
        ))}
      </div>

      {/* Acoustic estimate chip (BAM) — estimate + confidence wording ONLY. */}
      <div
        style={{
          position: "absolute",
          right: 12,
          top: 12,
          padding: "10px 14px",
          borderRadius: 10,
          font: "12px/1.4 ui-sans-serif, system-ui, sans-serif",
          color: "#cfe6ff",
          background: "rgba(8,38,61,0.86)",
          maxWidth: 300,
        }}
      >
        <div style={{ fontWeight: 600, marginBottom: 4 }}>
          {driverState.label || "loading acoustic estimate…"}
        </div>
        <div style={{ opacity: 0.85 }}>
          orcas shown: {driverState.presence ? driverState.count : 0} · presence-gated
        </div>
        <div style={{ opacity: 0.85, marginTop: 4 }}>{ATTRIBUTION}</div>
        <a
          href={STREAM_URL}
          target="_blank"
          rel="noreferrer"
          style={{ color: "#8fd0ff", opacity: 0.85 }}
        >
          Live-listen: orcasound-lab
        </a>
      </div>

      {/* Honesty legend + mandatory representativeness label. */}
      <div
        style={{
          position: "absolute",
          left: 12,
          top: 52,
          padding: "10px 12px",
          borderRadius: 8,
          font: "11px/1.5 ui-monospace, monospace",
          color: "#cfe6ff",
          background: "rgba(8,38,61,0.84)",
          maxWidth: 430,
        }}
      >
        <strong>Orcasound Lab slice</strong> ({LAT}, {LNG}) · t = {fmt(driverState.t)} · {status}
        <div style={{ marginTop: 4 }}>
          measured: audio · spectrogram · SRKW DTAG motion
        </div>
        <div>modeled: equipment mesh · acoustic inference · 3D placement</div>
        <div style={{ marginTop: 4, color: "#ffe08a" }}>
          Kinematics are representative SRKW DTAG motion, not the recorded animal.
        </div>
      </div>
    </div>
  );
}
