import type { Metadata } from "next";
import SliceHost from "./SliceHost";

// Isolated sandbox route at /slice (route group keeps it out of primary nav).
// ORCHESTRATOR-owned composition gate for BSW-SLICE-BUILD: it wires the four
// disjoint net-new lanes (BST station rig + POVs, BSH STFT spectrogram timeline,
// BAM precomputed acoustic inference, BRE presence-gated SRKW reenactment) into
// the one real vertical slice. It imports only the lanes' public barrels and
// edits no convergence file; the O0-gated integrator mounts these into
// SalishScene later.
export const metadata: Metadata = {
  title: "B-side acoustic + behavior slice",
  robots: { index: false, follow: false },
};

export default function SliceSandboxPage() {
  return <SliceHost />;
}
