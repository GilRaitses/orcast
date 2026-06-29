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
//   /spectro?ocean=1    enable the basic labeled interpretive ocean stub
//   /spectro?dd=1       enable the promoted double-diffusion volumetric (labeled)
//   /spectro?perf=1     run the serial frame-time A/B and expose __SPECTRO_PERF

import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import {
  createSpectroTimeline,
  type SpectroTimeline,
} from "@/lib/scene/hud/spectro";
import {
  createInterpretiveOceanLayer,
  createDoubleDiffusionLayer,
  INTERPRETIVE_OCEAN_LABEL,
  INTERPRETIVE_OCEAN_DETAIL,
  runFrameTimeAB,
  type InterpretiveOceanLayer,
  type DoubleDiffusionLayer,
  type ABResult,
} from "@/lib/scene/ocean";

const CLIP_URL = "/hydrophone/slice/orcasound_lab_20210825_srkw.m4a";
const DEFAULT_T = 30; // visible position in the ~180 s bout

type LayerKind = "none" | "stub" | "dd";

interface Params {
  t: number;
  layer: LayerKind;
  perf: boolean;
}

function readParams(): Params {
  const p: Params = { t: DEFAULT_T, layer: "none", perf: false };
  if (typeof window === "undefined") return p;
  const q = new URLSearchParams(window.location.search);
  const t = parseFloat(q.get("t") ?? "");
  if (Number.isFinite(t)) p.t = t;
  if (q.get("dd") === "1") p.layer = "dd";
  else if (q.get("ocean") === "1") p.layer = "stub";
  if (q.get("perf") === "1") p.perf = true;
  return p;
}

// Holds whichever interpretive layer is active so the perf A/B can toggle it.
interface ActiveLayer {
  object3D: import("three").Object3D;
  setEnabled(on: boolean): void;
  update(elapsedS: number): void;
  dispose(): void;
  provenance?: string;
}

function OceanRig({
  kind,
  layerRef,
  onProvenance,
}: {
  kind: LayerKind;
  layerRef: React.MutableRefObject<ActiveLayer | null>;
  onProvenance: (line: string | null) => void;
}) {
  const scene = useThree((s) => s.scene);
  useEffect(() => {
    if (kind === "none") {
      onProvenance(null);
      return;
    }
    let layer: InterpretiveOceanLayer | DoubleDiffusionLayer;
    if (kind === "dd") {
      const dd = createDoubleDiffusionLayer({});
      onProvenance(dd.provenance);
      layer = dd;
    } else {
      layer = createInterpretiveOceanLayer({});
      onProvenance(null);
    }
    layerRef.current = layer as ActiveLayer;
    scene.add(layer.object3D);
    return () => {
      scene.remove(layer.object3D);
      layer.dispose();
      layerRef.current = null;
      onProvenance(null);
    };
  }, [scene, kind, layerRef, onProvenance]);

  useEffect(() => {
    layerRef.current?.setEnabled(kind !== "none");
  }, [kind, layerRef]);

  useFrame((state) => layerRef.current?.update(state.clock.elapsedTime));
  return null;
}

export default function SpectroSandboxScene() {
  const params = useMemo(readParams, []);
  const hostRef = useRef<HTMLDivElement>(null);
  const timelineRef = useRef<SpectroTimeline | null>(null);
  const [layerKind, setLayerKind] = useState<LayerKind>(params.layer);
  const layerRef = useRef<ActiveLayer | null>(null);
  const [time, setTime] = useState(0);
  const [status, setStatus] = useState("baking spectrogram of real clip…");
  const [provenance, setProvenance] = useState<string | null>(null);
  const [perf, setPerf] = useState<ABResult[] | null>(null);
  const layerOn = layerKind !== "none";

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

  // Serial frame-time A/B: layer off vs on, while the HUD redraws. Runs once when
  // ?perf=1, after the bake is ready. Conditions never overlap (concurrent GL
  // contexts corrupt timing); results land on __SPECTRO_PERF for the host capture.
  useEffect(() => {
    if (!params.perf || status !== "ready") return;
    let cancelled = false;
    const setLayer = (on: boolean) => layerRef.current?.setEnabled(on);
    runFrameTimeAB(
      [
        { label: "layer-off", setup: () => setLayer(false) },
        { label: "layer-on", setup: () => setLayer(true), teardown: () => setLayer(false) },
      ],
      { perConditionMs: 2000, settleMs: 300 },
    ).then((results) => {
      if (cancelled) return;
      setPerf(results);
      (window as unknown as { __SPECTRO_PERF?: unknown }).__SPECTRO_PERF = results;
    });
    return () => {
      cancelled = true;
    };
  }, [params.perf, status]);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <Canvas
        camera={{ position: [0, 0, 90], fov: 45, near: 0.1, far: 600 }}
        style={{ width: "100%", height: "100%", background: "linear-gradient(#08263d,#04161f)" }}
        gl={{ antialias: true }}
      >
        <ambientLight intensity={0.6} />
        <OceanRig kind={layerKind} layerRef={layerRef} onProvenance={setProvenance} />
      </Canvas>

      {/* DOM sibling HUD overlay (mounted imperatively by the spectro factory). */}
      <div ref={hostRef} />

      {/* Top-left readouts + ocean layer selector. */}
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
        <strong>SPECTRO timeline authority</strong> measured audio.
        <div style={{ marginTop: 6 }}>currentTimeS = {time.toFixed(2)} s</div>
        <div style={{ opacity: 0.75 }}>{status}</div>
        <div style={{ display: "flex", gap: 6, marginTop: 8 }}>
          {(["none", "stub", "dd"] as LayerKind[]).map((k) => (
            <button
              key={k}
              onClick={() => setLayerKind(k)}
              style={{
                font: "11px ui-monospace, monospace",
                color: "#cfe6ff",
                background: layerKind === k ? "rgba(40,110,150,0.95)" : "rgba(20,70,100,0.9)",
                border: "1px solid rgba(120,180,220,0.4)",
                borderRadius: 4,
                padding: "2px 8px",
                cursor: "pointer",
              }}
            >
              {k === "none" ? "no layer" : k === "stub" ? "stub" : "double-diffusion"}
            </button>
          ))}
        </div>
        {provenance && (
          <div style={{ marginTop: 8, opacity: 0.8 }}>
            {INTERPRETIVE_OCEAN_DETAIL}
            <div style={{ marginTop: 4, opacity: 0.7 }}>source · {provenance}</div>
          </div>
        )}
        {perf && (
          <div style={{ marginTop: 8, opacity: 0.9 }}>
            <strong>frame-time A/B</strong>
            {perf.map((r) => (
              <div key={r.label}>
                {r.label} · {r.stats.meanMs.toFixed(2)} ms mean · {r.stats.p95Ms.toFixed(2)} ms p95 ·{" "}
                {r.stats.estFps.toFixed(0)} fps · {r.withinDesktop ? "60fps ok" : "over 60fps"}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Mandatory interpretive chip, shown whenever any ocean layer is enabled. */}
      {layerOn && (
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
