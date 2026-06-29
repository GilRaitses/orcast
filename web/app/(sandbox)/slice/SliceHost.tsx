"use client";

// SSR-safe host (mirrors StationHost / OrcaSandboxHost): the r3f + WebGL +
// WebAudio + Web Worker composition must never be imported during SSR.

import dynamic from "next/dynamic";

const SliceScene = dynamic(() => import("./SliceScene"), {
  ssr: false,
  loading: () => (
    <div style={{ display: "grid", placeItems: "center", width: "100%", height: "100%", color: "#9fb6c8" }}>
      Loading B-side acoustic + behavior slice…
    </div>
  ),
});

export default function SliceHost() {
  return (
    <div style={{ width: "100%", height: "100vh" }}>
      <SliceScene />
    </div>
  );
}
