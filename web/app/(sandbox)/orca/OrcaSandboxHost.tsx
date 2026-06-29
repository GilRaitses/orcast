"use client";

// SSR-safe host (mirrors WaterSandboxHost): the r3f + WebGL scene must never be
// imported during SSR. dynamic ssr:false keeps it client-only.

import dynamic from "next/dynamic";

const OrcaSandboxScene = dynamic(() => import("./OrcaSandboxScene"), {
  ssr: false,
  loading: () => (
    <div style={{ display: "grid", placeItems: "center", width: "100%", height: "100%", color: "#9fb6c8" }}>
      Loading orca biologging sandbox…
    </div>
  ),
});

export default function OrcaSandboxHost() {
  return (
    <div style={{ width: "100%", height: "100vh" }}>
      <OrcaSandboxScene />
    </div>
  );
}
