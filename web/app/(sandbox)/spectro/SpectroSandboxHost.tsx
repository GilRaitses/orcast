"use client";

// SSR-safe host (mirrors OrcaSandboxHost): the r3f + WebAudio scene must never be
// imported during SSR. dynamic ssr:false keeps it client-only.

import dynamic from "next/dynamic";

const SpectroSandboxScene = dynamic(() => import("./SpectroSandboxScene"), {
  ssr: false,
  loading: () => (
    <div style={{ display: "grid", placeItems: "center", width: "100%", height: "100%", color: "#9fb6c8" }}>
      Loading spectro sandbox…
    </div>
  ),
});

export default function SpectroSandboxHost() {
  return (
    <div style={{ width: "100%", height: "100vh" }}>
      <SpectroSandboxScene />
    </div>
  );
}
