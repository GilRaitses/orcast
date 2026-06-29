"use client";

// SSR-safe host (mirrors OrcaSandboxHost): the r3f + WebGL scene must never be
// imported during SSR. dynamic ssr:false keeps it client-only.

import dynamic from "next/dynamic";

const ReenactmentSandboxScene = dynamic(() => import("./ReenactmentSandboxScene"), {
  ssr: false,
  loading: () => (
    <div style={{ display: "grid", placeItems: "center", width: "100%", height: "100%", color: "#9fb6c8" }}>
      Loading reenactment sandbox…
    </div>
  ),
});

export default function ReenactmentSandboxHost() {
  return (
    <div style={{ width: "100%", height: "100vh" }}>
      <ReenactmentSandboxScene />
    </div>
  );
}
