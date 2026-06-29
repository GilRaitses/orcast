import type { Metadata } from "next";
import WorkbenchHost from "./WorkbenchHost";

// Dedicated B-side route at /workbench. Promotes the verified /slice composition
// (BST station rig + POVs, BSH STFT spectrogram timeline, BAM precomputed
// acoustic inference, BRE presence-gated SRKW reenactment) to a real, navigable
// research route. It reuses the four lanes' public barrels, edits no convergence
// file, and keeps all chrome styling in route-scoped CSS modules.
export const metadata: Metadata = {
  title: "Acoustic + behavior workbench",
  description:
    "Research workbench: real Orcasound Lab hydrophone audio, a scrubbable STFT spectrogram, a precomputed SRKW-call presence estimate, and a presence-gated SRKW DTAG reenactment.",
};

export default function WorkbenchPage() {
  return <WorkbenchHost />;
}
