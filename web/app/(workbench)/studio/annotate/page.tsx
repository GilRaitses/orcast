import type { Metadata } from "next";
import AnnotateHost from "./AnnotateHost";

// Net-new BSS annotation studio at /studio/annotate. The (workbench) route group
// adds no URL segment, so this does NOT collide with the existing /workbench
// slice route (O0 gate 1, Option B). Sandbox-only; the O0-gated integrator wires
// the studio panels into the console turn at BSS-INTEGRATE.
export const metadata: Metadata = {
  title: "Annotation studio",
  description:
    "Annotate real DTAG kinematics with provenance. Reads the real h5-derived dive_analysis products and round-trips a provenance-tagged annotation.",
  robots: { index: false, follow: false },
};

export default function AnnotateStudioPage() {
  return <AnnotateHost />;
}
