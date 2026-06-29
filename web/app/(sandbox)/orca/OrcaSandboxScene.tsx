"use client";

// ORCA sandbox: a data-driven, WFX-lit killer whale. Proves mesh + rig +
// wet-skin countershading + eyes + mouth + REAL SRKW biologging motion +
// bounded secondary physics, above the surface and underwater, before the
// O0-gated SalishScene mount. Deterministic shots via the query string so a
// headless browser can frame above/underwater without clicking.
//
//   /orca?view=above        camera above the surface (PMREM sky lighting)
//   /orca?view=under        camera underwater (Beer-Lambert tint)
//   /orca?t=120             scrub the track to 120 s
//   /orca?motion=sim        use the labeled SIMULATED dev track (default: real SRKW)
//   /orca?mesh=backup       use the CC-BY 3.0 Poly backup mesh
//   /orca?paused=1          freeze the clock (for screenshots)
//   /orca?spin=0            disable the slow auto-orbit

import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { makeSun } from "@/app/components/scene/realism/sun";
import { skyColor, fogColorForSky } from "@/app/components/scene/realism/atmosphere";
import {
  createOrcaController,
  makeSandboxWfxEnv,
  REAL_SRKW_MOTION_URL,
  SIM_DEV_MOTION_URL,
  ORCA_MESH_URL,
  ORCA_MESH_BACKUP_URL,
  type OrcaController,
  type WfxEnvHandle,
} from "@/lib/scene/orca";

const SCENE_TIME = new Date("2026-06-27T20:00:00Z");

interface Params {
  view: "above" | "under";
  t: number;
  motion: "real" | "sim";
  mesh: "primary" | "backup";
  paused: boolean;
  spin: boolean;
}

function readParams(): Params {
  const p: Params = { view: "under", t: 0, motion: "real", mesh: "primary", paused: false, spin: true };
  if (typeof window === "undefined") return p;
  const q = new URLSearchParams(window.location.search);
  if (q.get("view") === "above") p.view = "above";

  // The headless render host passes the route as a single arg; an unescaped "&"
  // backgrounds the host shell and breaks multi-param query strings. So the
  // UNDER view defaults to a deterministic deep, paused belly pose from a SINGLE
  // param (`?view=under`), with explicit params still able to override.
  if (p.view === "under") {
    p.t = 1312; // deep dive segment (strong WFX tint), per driver depth profile
    p.paused = true;
    p.spin = false;
  }

  const t = parseFloat(q.get("t") ?? "");
  if (Number.isFinite(t)) p.t = t;
  if (q.get("motion") === "sim") p.motion = "sim";
  if (q.get("mesh") === "backup") p.mesh = "backup";
  if (q.get("paused") === "1") p.paused = true;
  if (q.get("paused") === "0") p.paused = false;
  if (q.get("spin") === "0") p.spin = false;
  if (q.get("spin") === "1") p.spin = true;
  return p;
}

function SceneContent({ params }: { params: Params }) {
  const gl = useThree((s) => s.gl);
  const scene = useThree((s) => s.scene);
  const camera = useThree((s) => s.camera);

  const sun = useMemo(() => makeSun(SCENE_TIME, 48.5, -123), []);
  const sky = useMemo(() => skyColor(sun.elevationDeg), [sun]);

  // WFX environment stand-in (PMREM sky + sun + underwater absorption). Replaced
  // by the real WFX handle at integrate time; no orca module changes.
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

  // The orca is lit by the WFX env + the WFX sun (shared scene light, no private
  // orca lighting pass). Set scene.environment so the PBR IBL comes from the sky.
  useEffect(() => {
    scene.environment = env.pmremEnvironment;
    if (params.view === "under") {
      scene.background = new THREE.Color("#0c3a40");
      scene.fog = new THREE.FogExp2(0x0c3a40, 0.012);
    } else {
      scene.background = sky.clone();
      scene.fog = new THREE.Fog(fogColorForSky(sky), 40, 160);
    }
    return () => {
      scene.environment = null;
      scene.fog = null;
    };
  }, [scene, env, sky, params.view]);

  const controllerRef = useRef<OrcaController | null>(null);
  const stageRef = useRef<THREE.Group>(null);
  const [ready, setReady] = useState(false);

  const depthScale = params.view === "under" ? 0.12 : 0.0;
  const stageY = params.view === "above" ? 2.2 : 0.0;

  useEffect(() => {
    let alive = true;
    const motionUrl = params.motion === "sim" ? SIM_DEV_MOTION_URL : REAL_SRKW_MOTION_URL;
    const meshUrl = params.mesh === "backup" ? ORCA_MESH_BACKUP_URL : ORCA_MESH_URL;
    createOrcaController({
      env,
      meshUrl,
      motionUrl,
      worldUnitsPerMeter: 1,
      depthScale,
      timeScale: 1,
    })
      .then((c) => {
        if (!alive) {
          c.dispose();
          return;
        }
        controllerRef.current = c;
        stageRef.current?.add(c.root);
        const fl = c.track.manifest.driver_stats?.fluke_dsf;
        (window as unknown as { __ORCA_DEBUG?: unknown }).__ORCA_DEBUG = {
          mesh: meshUrl,
          motion: motionUrl,
          simulated: c.track.manifest.simulated,
          species: c.track.manifest.species,
          role: c.track.manifest.role,
          license: c.track.manifest.license,
          duration_s: c.track.duration,
          sample_rate_hz: c.track.sampleRate,
          cost: c.cost,
          fluke_dsf_median_hz: fl?.median_hz,
          fluke_band_hz: fl?.band_hz,
          depth_range_m: c.track.manifest.driver_stats?.depth_range_m,
        };
        setReady(true);
      })
      .catch((e) => console.error("orca controller failed", e));
    return () => {
      alive = false;
      const c = controllerRef.current;
      if (c) {
        stageRef.current?.remove(c.root);
        c.dispose();
        controllerRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [env, params.motion, params.mesh, depthScale]);

  const tmp = new THREE.Vector3();
  const startRef = useRef<number | null>(null);

  useFrame((state, dt) => {
    const c = controllerRef.current;
    if (!c) return;
    if (startRef.current === null) startRef.current = state.clock.elapsedTime;
    const elapsed = params.paused ? params.t : params.t + (state.clock.elapsedTime - startRef.current);

    c.update(Math.min(dt, 1 / 30), elapsed, camera.position);

    // Always frame the orca (the target tracks its root wherever it dives). The
    // azimuth advances only when spinning and not paused; otherwise a fixed
    // broadside so a paused screenshot is deterministic.
    c.root.getWorldPosition(tmp);
    const target = tmp;
    const a = params.spin && !params.paused ? state.clock.elapsedTime * 0.12 : Math.PI / 2;
    const r = 9.5;
    // Above: a near-level broadside slightly above, reading the wet glossy black
    // DORSAL. Under: drop the camera below the animal and look UP so the white
    // countershaded ventral + eyepatch read against the WFX underwater tint
    // (the classic whale-from-below silhouette), not just the dark back again.
    const below = params.view === "under";
    camera.position.set(
      target.x + Math.cos(a) * r,
      below ? target.y - 3.4 : target.y + 1.2,
      target.z + Math.sin(a) * r,
    );
    camera.lookAt(target.x, below ? target.y + 1.1 : target.y - 1.4, target.z);
  });

  return (
    <group>
      <ambientLight intensity={params.view === "under" ? 0.35 : sun.ambientIntensity} />
      <directionalLight
        position={sun.direction.clone().multiplyScalar(50).toArray()}
        intensity={params.view === "under" ? sun.intensity * 0.5 : sun.intensity}
        color={sun.color.getHex()}
      />
      <hemisphereLight args={["#bfe2ff", "#08323a", 0.35]} />

      {/* Water surface plane at Y=0 for above/under context. */}
      <mesh rotation-x={-Math.PI / 2} position-y={0}>
        <planeGeometry args={[200, 200]} />
        <meshPhysicalMaterial
          color={params.view === "under" ? "#0e3a40" : "#2e6f9e"}
          roughness={0.12}
          metalness={0}
          transmission={params.view === "under" ? 0.0 : 0.6}
          transparent
          opacity={params.view === "under" ? 0.85 : 0.55}
          side={THREE.DoubleSide}
        />
      </mesh>

      <group ref={stageRef} position-y={stageY} />
      {!ready && null}
    </group>
  );
}

export default function OrcaSandboxScene() {
  const params = useMemo(readParams, []);
  const [debug, setDebug] = useState<Record<string, unknown> | null>(null);

  // Surface the published debug object in the HUD (also on window.__ORCA_DEBUG).
  useEffect(() => {
    const id = setInterval(() => {
      const d = (window as unknown as { __ORCA_DEBUG?: Record<string, unknown> }).__ORCA_DEBUG;
      if (d) setDebug(d);
    }, 500);
    return () => clearInterval(id);
  }, []);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <Canvas
        camera={{ position: params.view === "under" ? [11, -2, 0] : [12, 5, 0], fov: 45, near: 0.1, far: 600 }}
        style={{ width: "100%", height: "100%" }}
        gl={{ antialias: true }}
        onCreated={({ gl }) => {
          gl.toneMapping = THREE.ACESFilmicToneMapping;
          gl.toneMappingExposure = 1.0;
        }}
      >
        <SceneContent params={params} />
      </Canvas>

      <div
        style={{
          position: "absolute",
          left: 12,
          bottom: 12,
          padding: "12px 14px",
          borderRadius: 8,
          font: "11px/1.5 ui-monospace, monospace",
          color: "#cfe6ff",
          background: "rgba(8,38,61,0.84)",
          maxWidth: 420,
        }}
      >
        <strong>ORCA biologging twin</strong> - MODELED animal.
        <div style={{ marginTop: 6 }}>
          Motion: {params.motion === "real" ? "REAL SRKW DTAG" : "SIMULATED dev track"}
          {debug?.species ? ` (${String(debug.species)}, ${String(debug.role)})` : ""}
          {debug?.simulated === false ? " - measured, CC-BY 4.0 (Tennessen 2024)" : ""}
          {debug?.simulated === true ? " - simulated, labeled" : ""}
        </div>
        <div>Humpback data is CONTRAST ONLY and never drives this orca.</div>
        {debug?.fluke_dsf_median_hz != null && (
          <div>
            Fluke dominant ~{Number(debug.fluke_dsf_median_hz).toFixed(3)} Hz (band{" "}
            {JSON.stringify(debug.fluke_band_hz)}) - corrected 0.2-0.35 Hz read.
          </div>
        )}
        {debug?.cost != null && (
          <div>
            Cost: {(debug.cost as Record<string, unknown>).triangles as number} tris,{" "}
            {(debug.cost as Record<string, unknown>).bones as number} bones, LOD{" "}
            {(debug.cost as Record<string, unknown>).lod as string}, GPU-skinned.
          </div>
        )}
        <div style={{ opacity: 0.7, marginTop: 4 }}>
          View {params.view}. Lit by the WFX env stand-in (PMREM sky + underwater
          Beer-Lambert). Real WFX handle swaps in at integrate.
        </div>
      </div>
    </div>
  );
}
