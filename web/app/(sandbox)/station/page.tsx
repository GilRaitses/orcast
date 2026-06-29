import type { Metadata } from "next";
import StationHost from "./StationHost";

// Isolated sandbox route at /station (route group keeps it out of primary nav).
// Self-verification surface for the BSW hydrophone lane: the modeled
// equipment rig placed at the real Orcasound Lab station on the seabed, a
// station audio player bound to the one real archived clip, and a camera POV
// selector (hydrophone POV + top-down) driving the existing Camera Director.
// Sandbox-only; the O0-gated integrator mounts these modules into SalishScene.
export const metadata: Metadata = {
  title: "Station hydrophone sandbox",
  robots: { index: false, follow: false },
};

export default function StationSandboxPage() {
  return <StationHost />;
}
