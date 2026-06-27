/** Display status for held-out CV gate (G3-D-01 remediation). */

export type CvGateInput = {
  gate_pass?: boolean | null;
  mean_deviance_skill?: number | null;
  display_pass?: boolean | null;
  display_status?: GateDisplayStatus | null;
};

export type GateDisplayStatus = "pass" | "caution" | "fail" | "na";

export function cvDisplayStatus(cv: CvGateInput | null | undefined): GateDisplayStatus {
  if (cv?.display_status) return cv.display_status;
  if (!cv || cv.gate_pass == null) return "na";
  if (cv.gate_pass === false) return "fail";
  const skill = cv.mean_deviance_skill;
  if (typeof skill === "number" && skill < 0) return "caution";
  return "pass";
}

export function cvDisplayLabel(status: GateDisplayStatus): string {
  switch (status) {
    case "pass":
      return "pass";
    case "caution":
      return "caution";
    case "fail":
      return "fail";
    default:
      return "n/a";
  }
}

export function cvDisplayExplainer(status: GateDisplayStatus): string | null {
  if (status !== "caution") return null;
  return "Fold majority passed, but mean held-out deviance skill is negative. Treat as marginal. See integrity conditions.";
}

export function computeCvDisplayPass(cv: CvGateInput | null | undefined): boolean | null {
  const status = cvDisplayStatus(cv);
  if (status === "na") return null;
  return status === "pass";
}
