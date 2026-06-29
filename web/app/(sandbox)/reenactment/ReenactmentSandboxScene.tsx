"use client";

// BRE reenactment sandbox: REAL multi-orca reenactment breadth, before the
// O0-gated SalishScene mount. It proves, end to end on net-new code:
//   - multi-orca spawn up to nMax (3) on the REAL SRKW DTAG driver
//   - a behavior->motion ethogram from real classified DTAG segments (each clip
//     a window into the measured driver, the behavior NAME a disclosed modeled
//     kinematic match)
//   - scrub + slow synced to a playhead (this sandbox runs a local clock that
//     implements BSH's SpectroTimelineAuthority contract; the /slice route
//     exercises the real BSH WebAudio engine end to end)
//   - both camera POVs via BST's POV-selection object driving the Camera Director
//   - a per-frame frame-time readout for the nMax orcas
//
// HONESTY (locked): motion is measured SRKW DTAG telemetry only; acoustic
// presence gates visibility; the spawn COUNT equals BAM's estimate (presence
// only today). `?n=` is a CAPABILITY DEMO override, stamped + labeled on-screen
// as NOT a model estimate, so multi-orca breadth can be shown without claiming
// the classifier resolves count. The mandatory representativeness label is
// always present.
//
// Deterministic headless framing via a SINGLE query param (the render host
// passes the route as one arg, so an unescaped "&" would background the shell):
//   /reenactment                establishing 3/4 shot, n=3 capability demo, paused
//   /reenactment?view=hydrophone hydrophone POV (drives the Camera Director)
//   /reenactment?view=topdown    top-down station overview (Camera Director)
//   /reenactment?play=1          run the clock (scrub/slow demo)
// Additional overrides: ?n=1..3  ?t=<sec>  ?rate=<0..1>  ?clip=<behaviorName>

import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";

import { projectToScene, sceneDepth, type HeightmapBounds } from "@/lib/sceneIntent";
import { createCameraDirector } from "@/lib/scene/camera/director";
import type { CameraDirector, CameraDirectorHandle } from "@/lib/scene/camera/types";
import { makeSun } from "@/app/components/scene/realism/sun";
import { skyColor } from "@/app/components/scene/realism/atmosphere";

import { makeSandboxWfxEnv, type WfxEnvHandle } from "@/lib/scene/orca";

import {
  buildSpawnRecord,
  createOrcaPool,
  createTimelineDriver,
  loadClassification,
  loadClipManifest,
  bindReenactmentPov,
  type OrcaPool,
  type TimelineDriver,
  type OrcaInstanceLabel,
  type ReenactmentPov,
  type ReenactmentTimeline,
  type ReenactmentSpawnRecord,
} from "@/lib/scene/reenactment";
import type { StationPovHandle } from "@/lib/scene/hydrophone";

// --- real, verifiable facts (match the slice + station lanes) ---------------
const LAT = 48.5583362;
const LNG = -123.1735774;

const SLICE_BOUNDS: HeightmapBounds = {
  min_lat: 48.4,
  max_lat: 48.7,
  min_lng: -123.25,
  max_lng: -122.75,
};
const SCENE_DEPTH = sceneDepth(SLICE_BOUNDS);
const WUPM = 1; // 1 metre = 1 scene unit (mirrors the orca + slice sandboxes)
const SEABED_DEPTH_M = -18; // modeled seabed for the POV + context plane

const ATTRIBUTION = "Audio: Orcasound (CC BY-NC-SA 4.0)";
const UNDERWATER_TINT = "#0c3a40";
const SCENE_TIME = new Date("2026-06-27T20:00:00Z");

// Default breadth: near-column behaviors that read together in one frame
// (Traveling, Surface_Active, Side_rolls). Deep classes (Exploratory_dives,
// Vertical_loop) are honest but dive out of the establishing frame; reach them
// with ?clip=Exploratory_dives.
const DEFAULT_BEHAVIOR_CLASSES = [8, 7, 5] as const;
// Presence-positive window so the deterministic frame shows spawned orcas.
const DEFAULT_T = 61.5;

type View = "establish" | "hydrophone" | "topdown";

interface Params {
  view: View;
  n: number;
  t: number;
  rate: number;
  play: boolean;
  clip?: string;
}

function readParams(): Params {
  const p: Params = { view: "establish", n: 3, t: DEFAULT_T, rate: 1, play: false };
  if (typeof window === "undefined") return p;
  const q = new URLSearchParams(window.location.search);
  const v = q.get("view");
  if (v === "hydrophone" || v === "topdown" || v === "establish") p.view = v;
  const n = parseInt(q.get("n") ?? "", 10);
  if (Number.isFinite(n)) p.n = Math.min(3, Math.max(1, n));
  const t = parseFloat(q.get("t") ?? "");
  if (Number.isFinite(t)) p.t = t;
  const rate = parseFloat(q.get("rate") ?? "");
  if (Number.isFinite(rate)) p.rate = Math.min(1, Math.max(0.05, rate));
  if (q.get("play") === "1") p.play = true;
  const clip = q.get("clip");
  if (clip) p.clip = clip;
  return p;
}

// A minimal scene-time source that satisfies BSH's SpectroTimelineAuthority
// contract (the structural ReenactmentTimeline subset BRE follows). The /slice
// route drives BRE from the real BSH WebAudio engine; this clock lets the
// sandbox exercise scrub (seek) and slow-mo (playbackRate) without audio.
class SandboxClock implements ReenactmentTimeline {
  durationS: number;
  currentTimeS: number;
  playbackRate: number;
  playing: boolean;
  private subs = new Set<(s: Readonly<ReenactmentTimeline>) => void>();

  constructor(durationS: number, t0: number, rate: number, playing: boolean) {
    this.durationS = durationS;
    this.currentTimeS = Math.min(Math.max(0, t0), durationS);
    this.playbackRate = rate;
    this.playing = playing;
  }
  private notify() {
    for (const fn of this.subs) fn(this);
  }
  tick(dt: number) {
    if (!this.playing) return;
    let t = this.currentTimeS + dt * this.playbackRate;
    if (t > this.durationS) t -= this.durationS; // loop the sandbox
    this.currentTimeS = t;
    this.notify();
  }
  seek(timeS: number) {
    this.currentTimeS = Math.min(Math.max(0, timeS), this.durationS);
    this.notify();
  }
  setPlaybackRate(rate: number) {
    this.playbackRate = Math.min(1, Math.max(0.05, rate));
    this.notify();
  }
  play() {
    this.playing = true;
    this.notify();
  }
  pause() {
    this.playing = false;
    this.notify();
  }
  subscribe(fn: (s: Readonly<ReenactmentTimeline>) => void): () => void {
    this.subs.add(fn);
    return () => this.subs.delete(fn);
  }
}

interface HudState {
  countBasisLabel: string;
  representativeness: string;
  presence: boolean;
  presenceLabel: string;
  t: number;
  rate: number;
  playing: boolean;
  count: number;
  instances: OrcaInstanceLabel[];
  frameMsAvg: number;
  frameMsP95: number;
}

function SceneContent({
  params,
  onHud,
  clockRef,
}: {
  params: Params;
  onHud: (s: HudState) => void;
  clockRef: React.MutableRefObject<SandboxClock | null>;
}) {
  const gl = useThree((s) => s.gl);
  const scene = useThree((s) => s.scene);
  const camera = useThree((s) => s.camera);

  const sun = useMemo(() => makeSun(SCENE_TIME, 48.5, -123), []);
  const sky = useMemo(() => skyColor(sun.elevationDeg), [sun]);

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

  // Station anchor scene XZ, the SAME projection the pool uses to place orcas.
  const anchor = useMemo(() => {
    const [x, z] = projectToScene(LAT, LNG, SLICE_BOUNDS, SCENE_DEPTH);
    return new THREE.Vector3(x, 0, z);
  }, []);

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

  // --- Camera Director (BST POV object drives it) ---------------------------
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
    const ax = anchor.x;
    const az = anchor.z;

    if (params.view === "establish") {
      povHandleRef.current?.stop();
      povHandleRef.current = null;
      camera.position.set(ax + 28, -3, az + 28);
      camera.lookAt(ax, -10, az);
      camera.updateProjectionMatrix();
      return;
    }
    const director = directorRef.current;
    if (!director) return;
    povHandleRef.current = bindReenactmentPov(
      director,
      { lat: LAT, lng: LNG, seabedDepthM: SEABED_DEPTH_M },
      params.view as ReenactmentPov,
      params.view === "topdown" ? { orbit: params.play, orbitSpeed: 0.03 } : {},
    );
    if (!params.play) director.update(10); // settle the eased fly-in for a paused frame
    return () => {
      povHandleRef.current?.stop();
      povHandleRef.current = null;
    };
  }, [params.view, params.play, camera, anchor]);

  // --- reenactment pool from BAM classification + the ethogram --------------
  const poolRef = useRef<OrcaPool | null>(null);
  const driverRef = useRef<TimelineDriver | null>(null);
  const poolGroupRef = useRef<THREE.Group>(null);
  const recordRef = useRef<ReenactmentSpawnRecord | null>(null);
  const [poolReady, setPoolReady] = useState(false);

  useEffect(() => {
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
        nMax: 3,
        // CAPABILITY DEMO: force the count to exercise the multi-orca rig. The
        // record is stamped `capability_demo` and labeled NOT a model estimate.
        demoCountOverride: params.n,
        clipId: params.clip,
        behaviorClasses: params.clip ? undefined : [...DEFAULT_BEHAVIOR_CLASSES],
      });
      recordRef.current = record;

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

      // The clock is the single playhead the reenactment follows.
      const clock = new SandboxClock(record.timelineDurationS, params.t, params.rate, params.play);
      clockRef.current = clock;

      driver = createTimelineDriver(clock, pool, classification, { presenceGated: true });
      poolRef.current = pool;
      driverRef.current = driver;
      setPoolReady(true);
    })().catch((e) => console.error("reenactment sandbox failed", e));

    return () => {
      alive = false;
      driver?.dispose();
      if (pool) {
        poolGroupRef.current?.remove(pool.group);
        pool.dispose();
      }
      poolRef.current = null;
      driverRef.current = null;
      clockRef.current = null;
      setPoolReady(false);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [env, params.n, params.t, params.rate, params.play, params.clip]);

  // --- drive loop: one clock -> reenactment + Camera Director + frame-time ---
  const camWorld = useRef(new THREE.Vector3());
  const frameSamples = useRef<number[]>([]);
  const lastNow = useRef<number | null>(null);

  useFrame(() => {
    const now = performance.now();
    const frameMs = lastNow.current == null ? 0 : now - lastNow.current;
    lastNow.current = now;
    if (frameMs > 0) {
      const s = frameSamples.current;
      s.push(frameMs);
      if (s.length > 120) s.shift();
    }

    const dtClamped = Math.min(frameMs / 1000, 1 / 30);
    handleRef.current.camera = camera as THREE.PerspectiveCamera;

    const clock = clockRef.current;
    if (clock) clock.tick(dtClamped);
    if (params.view !== "establish") directorRef.current?.update(dtClamped);

    const driver = driverRef.current;
    const pool = poolRef.current;
    const record = recordRef.current;
    if (driver && pool && record && clock) {
      camera.getWorldPosition(camWorld.current);
      driver.update(dtClamped, camWorld.current);
      const st = driver.getState();

      const samples = frameSamples.current;
      const avg = samples.length
        ? samples.reduce((a, b) => a + b, 0) / samples.length
        : 0;
      const sorted = [...samples].sort((a, b) => a - b);
      const p95 = sorted.length ? sorted[Math.floor(sorted.length * 0.95)] : 0;

      onHud({
        countBasisLabel: record.countBasisLabel,
        representativeness: record.honesty.representativeness,
        presence: st.presence,
        presenceLabel: st.hudLabel,
        t: st.currentTimeS,
        rate: clock.playbackRate,
        playing: clock.playing,
        count: pool.count(),
        instances: pool.instanceLabels(),
        frameMsAvg: avg,
        frameMsP95: p95,
      });

      (window as unknown as { __BRE_DEBUG?: unknown }).__BRE_DEBUG = {
        n: pool.count(),
        countBasis: record.countBasis,
        behaviors: pool.instanceLabels().map((l) => l.behaviorName),
        presence: st.presence,
        t: st.currentTimeS,
        playbackRate: clock.playbackRate,
        frame_ms_avg: Number(avg.toFixed(2)),
        frame_ms_p95: Number(p95.toFixed(2)),
        fps_est: avg > 0 ? Number((1000 / avg).toFixed(1)) : 0,
      };
    }
  });

  return (
    <group>
      <ambientLight intensity={0.42} />
      <directionalLight
        position={sun.direction.clone().multiplyScalar(60).toArray()}
        intensity={sun.intensity * 0.7}
        color={sun.color.getHex()}
      />
      <hemisphereLight args={["#bfe2ff", "#06262f", 0.4]} />

      {/* Modeled seabed plane. */}
      <mesh rotation-x={-Math.PI / 2} position={[anchor.x, SEABED_DEPTH_M, anchor.z]}>
        <planeGeometry args={[600, 600]} />
        <meshStandardMaterial color="#1d2a26" roughness={0.95} metalness={0} />
      </mesh>

      {/* Water surface plane at Y=0. */}
      <mesh rotation-x={-Math.PI / 2} position={[anchor.x, 0, anchor.z]}>
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

export default function ReenactmentSandboxScene() {
  const params = useMemo(readParams, []);
  const clockRef = useRef<SandboxClock | null>(null);
  const [hud, setHud] = useState<HudState | null>(null);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <Canvas
        camera={{ position: [28, -3, 28], fov: 50, near: 0.1, far: 2000 }}
        style={{ width: "100%", height: "100%" }}
        gl={{ antialias: true }}
        onCreated={({ gl }) => {
          gl.toneMapping = THREE.ACESFilmicToneMapping;
          gl.toneMappingExposure = 1.0;
        }}
      >
        <SceneContent params={params} onHud={setHud} clockRef={clockRef} />
      </Canvas>

      {/* Transport controls (scrub + slow). */}
      <div
        style={{
          position: "absolute",
          left: 12,
          bottom: 12,
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "10px 12px",
          borderRadius: 8,
          font: "11px ui-monospace, monospace",
          color: "#cfe6ff",
          background: "rgba(8,38,61,0.84)",
        }}
      >
        <button
          type="button"
          onClick={() => {
            const c = clockRef.current;
            if (!c) return;
            if (c.playing) c.pause();
            else c.play();
          }}
          style={{
            appearance: "none",
            border: "1px solid rgba(160,210,255,0.3)",
            borderRadius: 6,
            padding: "4px 12px",
            color: "#5fd0ff",
            background: "rgba(95,208,255,0.14)",
            cursor: "pointer",
          }}
        >
          {hud?.playing ? "Pause" : "Play"}
        </button>
        <input
          type="range"
          min={0}
          max={Math.round(clockRef.current?.durationS ?? 178)}
          step={0.5}
          value={hud ? Math.round(hud.t) : 0}
          onChange={(e) => clockRef.current?.seek(parseFloat(e.target.value))}
          style={{ width: 220 }}
        />
        <span style={{ fontVariantNumeric: "tabular-nums" }}>{fmt(hud?.t ?? 0)}</span>
        <label style={{ display: "flex", alignItems: "center", gap: 4 }}>
          rate
          <input
            type="range"
            min={0.05}
            max={1}
            step={0.05}
            value={hud?.rate ?? 1}
            onChange={(e) => clockRef.current?.setPlaybackRate(parseFloat(e.target.value))}
            style={{ width: 90 }}
          />
          <span style={{ fontVariantNumeric: "tabular-nums" }}>{(hud?.rate ?? 1).toFixed(2)}x</span>
        </label>
      </div>

      {/* Acoustic estimate + count-basis honesty chip. */}
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
          maxWidth: 320,
        }}
      >
        <div style={{ fontWeight: 600, marginBottom: 4 }}>
          {hud?.presenceLabel || "loading acoustic estimate"}
        </div>
        <div style={{ opacity: 0.85 }}>
          orcas shown {hud ? (hud.presence ? hud.count : 0) : 0}, presence-gated
        </div>
        {hud?.countBasisLabel && (
          <div style={{ marginTop: 4, color: "#ffe08a" }}>{hud.countBasisLabel}</div>
        )}
        <div style={{ opacity: 0.85, marginTop: 4 }}>{ATTRIBUTION}</div>
      </div>

      {/* Per-instance behavior labels (disclosed modeled matches). */}
      <div
        style={{
          position: "absolute",
          right: 12,
          top: 130,
          padding: "10px 12px",
          borderRadius: 8,
          font: "11px/1.5 ui-monospace, monospace",
          color: "#cfe6ff",
          background: "rgba(8,38,61,0.84)",
          maxWidth: 340,
        }}
      >
        <strong>Ethogram (kinematic, modeled match)</strong>
        {(hud?.instances ?? []).map((l) => (
          <div key={l.instanceId} style={{ marginTop: 4 }}>
            {l.behaviorName} · {l.behaviorLabel}
          </div>
        ))}
      </div>

      {/* Honesty legend + frame-time + mandatory representativeness label. */}
      <div
        style={{
          position: "absolute",
          left: 12,
          top: 12,
          padding: "10px 12px",
          borderRadius: 8,
          font: "11px/1.5 ui-monospace, monospace",
          color: "#cfe6ff",
          background: "rgba(8,38,61,0.84)",
          maxWidth: 460,
        }}
      >
        <strong>BRE multi-orca reenactment sandbox</strong> · t = {fmt(hud?.t ?? 0)}
        <div style={{ marginTop: 4 }}>measured SRKW DTAG motion · modeled 3D placement · acoustic inference</div>
        <div>
          frame-time {hud ? hud.frameMsAvg.toFixed(2) : "0.00"} ms avg, {hud ? hud.frameMsP95.toFixed(2) : "0.00"} ms p95
          for {hud?.count ?? 0} orcas. Authoritative nMax frame-time comes from the T4 GPU accept.
        </div>
        <div style={{ marginTop: 4, color: "#ffe08a" }}>
          {hud?.representativeness || "Kinematics are representative SRKW DTAG motion, not the recorded animal."}
        </div>
      </div>
    </div>
  );
}
