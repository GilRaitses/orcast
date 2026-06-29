"use client";

// SPECTRO sandbox: bakes a Web Worker STFT spectrogram of the REAL Orcasound Lab
// slice clip and renders the scrubbable Canvas 2D HUD with a playhead, exposing the
// SpectroTimelineAuthority that BRE/BST/BAM follow. The interpretive ocean layer is
// mounted into a small r3f Canvas behind the HUD and is OFF by default.
//
// Deterministic headless framing uses a SINGLE query param (an unescaped "&"
// backgrounds the render-host shell), mirroring the orca sandbox:
//   /spectro            baked spectrogram, playhead parked at a visible position
//   /spectro?t=90       seek the playhead to 90 s (paused, for a screenshot)
//   /spectro?ocean=1    enable the labeled interpretive ocean stub

import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import {
  createSpectroTimeline,
  type SpectroTimeline,
} from "@/lib/scene/hud/spectro";
import {
  createInterpretiveOceanLayer,
  INTERPRETIVE_OCEAN_LABEL,
  type InterpretiveOceanLayer,
} from "@/lib/scene/ocean";

const CLIP_URL = "/hydrophone/slice/orcasound_lab_20210825_srkw.m4a";
const DEFAULT_T = 30; // visible position in the ~180 s bout

interface Params {
  t: number;
  ocean: boolean;
}

function readParams(): Params {
  const p: Params = { t: DEFAULT_T, ocean: false };
  if (typeof window === "undefined") return p;
  const q = new URLSearchParams(window.location.search);
  const t = parseFloat(q.get("t") ?? "");
  if (Number.isFinite(t)) p.t = t;
  if (q.get("ocean") === "1") p.ocean = true;
  return p;
}

function OceanRig({ enabled, layerRef }: { enabled: boolean; layerRef: React.MutableRefObject<InterpretiveOceanLayer | null> }) {
  const scene = useThree((s) => s.scene);
  useEffect(() => {
    const layer = createInterpretiveOceanLayer({});
    layerRef.current = layer;
    scene.add(layer.object3D);
    return () => {
      scene.remove(layer.object3D);
      layer.dispose();
      layerRef.current = null;
    };
  }, [scene, layerRef]);

  useEffect(() => {
    layerRef.current?.setEnabled(enabled);
  }, [enabled, layerRef]);

  useFrame((state) => layerRef.current?.update(state.clock.elapsedTime));
  return null;
}

export default function SpectroSandboxScene() {
  const params = useMemo(readParams, []);
  const hostRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<SpectroTimeline | null>(null);
  const [oceanOn, setOceanOn] = useState(params.ocean);
  const oceanLayerRef = useRef<InterpretiveOceanLayer | null>(null);
  const [time, setTime] = useState(0);
  const [status, setStatus] = useState("baking spectrogram of real clip…");

  useEffect(() => {
    let alive = true;
    let unsub: (() => void) | null = null;
    createSpectroTimeline({
      url: CLIP_URL,
      hud: { width: 900, height: 280, caption: "measured: spectrogram of real Orcasound Lab audio" },
    })
      .then((tl) => {
        if (!alive) {
          tl.dispose();
          return;
        }
        timelineRef.current = tl;
        if (tl.hud && hostRef.current) tl.hud.mount(hostRef.current);
        tl.authority.seek(params.t, { play: false });
        unsub = tl.authority.subscribe((s) => setTime(s.currentTimeS));
        setStatus("ready");
        (window as unknown as { __SPECTRO_DEBUG?: unknown }).__SPECTRO_DEBUG = {
          durationS: tl.authority.durationS,
          sampleRate: tl.authority.sampleRate,
          fftSize: tl.cache.fftSize,
          hopSize: tl.cache.hopSize,
          freqBins: tl.cache.freqBins,
          timeBins: tl.cache.timeBins,
          seekedToS: params.t,
        };
      })
      .catch((e) => {
        console.error("spectro timeline failed", e);
        setStatus(`bake failed: ${String(e)}`);
      });
    return () => {
      alive = false;
      unsub?.();
      timelineRef.current?.dispose();
      timelineRef.current = null;
    };
  }, [params.t]);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <Canvas
        camera={{ position: [0, 0, 90], fov: 45, near: 0.1, far: 600 }}
        style={{ width: "100%", height: "100%", background: "linear-gradient(#08263d,#04161f)" }}
        gl={{ antialias: true }}
      >
        <ambientLight intensity={0.6} />
        <OceanRig enabled={oceanOn} layerRef={oceanLayerRef} />
      </Canvas>

      {/* DOM sibling HUD overlay (mounted imperatively by the spectro factory). */}
      <div ref={hostRef} />

      {/* Top-left readouts + ocean toggle. */}
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
          maxWidth: 420,
        }}
      >
        <strong>SPECTRO timeline authority</strong> measured audio.
        <div style={{ marginTop: 6 }}>
          currentTimeS = {time.toFixed(2)} s
        </div>
        <div style={{ opacity: 0.75 }}>{status}</div>
        <button
          onClick={() => setOceanOn((v) => !v)}
          style={{
            marginTop: 8,
            font: "11px ui-monospace, monospace",
            color: "#cfe6ff",
            background: "rgba(20,70,100,0.9)",
            border: "1px solid rgba(120,180,220,0.4)",
            borderRadius: 4,
            padding: "2px 8px",
            cursor: "pointer",
          }}
        >
          interpretive ocean: {oceanOn ? "on" : "off"}
        </button>
      </div>

      {/* Mandatory interpretive chip, shown only when the ocean stub is enabled. */}
      {oceanOn && (
        <div
          style={{
            position: "absolute",
            right: 12,
            top: 12,
            padding: "4px 10px",
            borderRadius: 999,
            font: "11px ui-monospace, monospace",
            color: "#04161f",
            background: "rgba(180,220,255,0.92)",
          }}
        >
          {INTERPRETIVE_OCEAN_LABEL}
        </div>
      )}
    </div>
  );
}
