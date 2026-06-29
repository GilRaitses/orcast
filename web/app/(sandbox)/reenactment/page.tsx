import type { Metadata } from "next";
import ReenactmentSandboxHost from "./ReenactmentSandboxHost";

// Isolated sandbox route at /reenactment (route group keeps it out of primary
// nav). Proves BRE's deepened multi-orca reenactment breadth: spawn up to nMax
// on the REAL SRKW DTAG driver, a behavior->motion ethogram from real classified
// DTAG segments, scrub/slow synced to a BSH-contract playhead, both camera POVs
// via BST's POV-selection object, and a frame-time readout. Sandbox-only until
// the O0-gated integrator mounts the reenactment into the live SalishScene.
export const metadata: Metadata = {
  title: "BRE multi-orca reenactment sandbox",
  robots: { index: false, follow: false },
};

export default function ReenactmentSandboxPage() {
  return <ReenactmentSandboxHost />;
}
