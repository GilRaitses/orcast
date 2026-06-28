import type { Metadata } from "next";
import WaterSandboxHost from "./WaterSandboxHost";

// Isolated sandbox route at /water (route group keeps it out of primary nav).
// It proves the depth-driven water2 module against the real full-extent tileset
// before the integrator wires it into the live SalishScene. See
// web/lib/scene/water2/ and research/R4_ocean_water_rendering.md.
export const metadata: Metadata = {
  title: "Depth-driven water sandbox — W2.5",
  robots: { index: false, follow: false },
};

export default function WaterSandboxPage() {
  return <WaterSandboxHost />;
}
