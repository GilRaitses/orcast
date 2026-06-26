export type GlossaryEntry = {
  id: string;
  term: string;
  tooltip: string;
  body: string;
  usedIn: string[];
  provenance?: string;
  seeAlso?: string[];
};

export const GLOSSARY: Record<string, GlossaryEntry> = {
  "fitness-gates": {
    id: "fitness-gates",
    term: "Fitness gates",
    tooltip: "Statistical checks the model must pass before confidence increases.",
    body:
      "Fitness gates are explicit statistical tests run after each kernel fit. They are not warnings — they are the contract for what confidence the forecast is allowed to show. Level 1 tests whether each cyclic covariate beats a phase-shuffled null; Level 2 tests out-of-sample skill and calibration.",
    usedIn: ["Gates dashboard", "Provenance modal", "Review dossier"],
    seeAlso: ["level1-psth", "integrity-conditions"],
  },
  "integrity-conditions": {
    id: "integrity-conditions",
    term: "Integrity conditions",
    tooltip: "Required disclosures about evidence scope — not optional caveats.",
    body:
      "Integrity conditions state what the current fit can and cannot claim: single-station coverage, tide overlap, unreviewed acoustic candidates, marginal cross-validation skill, and similar scope limits. They exist so the UI never oversells precision.",
    usedIn: ["Forecast confidence meter", "Gates dashboard", "Provenance modal"],
    provenance: "Derived from fit_report.json via /api/gates and /api/provenance",
    seeAlso: ["fitness-gates", "level0-detector-qc"],
  },
  "level1-psth": {
    id: "level1-psth",
    term: "Level 1: PSTH vs phase-shuffle null",
    tooltip: "Does each covariate show real temporal structure vs a shuffled-phase null?",
    body:
      "Level 1 compares the peristimulus time histogram (PSTH) of detections binned by a cyclic phase (diel, tide, lunar, season) against a null where phase labels are shuffled. A covariate only contributes when modulation is larger than expected under the null (reported as beats null).",
    usedIn: ["Gates dashboard", "Kernel fit report"],
    provenance: "modeling/psth.py → psth_with_null → fit_report.level1_psth",
    seeAlso: ["modulation", "null-z", "null-p", "beats-null", "covariate"],
  },
  covariate: {
    id: "covariate",
    term: "Covariate",
    tooltip: "A cyclic environmental clock (diel, tide, lunar, season) modeled as a Fourier kernel.",
    body:
      "Each covariate is a mean-centered Fourier kernel on a unit phase in [0, 1). The fit only includes covariates with sufficient phase coverage and overlapping measurements (e.g., tide requires currents overlapping acoustics).",
    usedIn: ["Gates table", "Provenance kernel contributions"],
    seeAlso: ["modulation", "level1-psth"],
  },
  modulation: {
    id: "modulation",
    term: "Modulation",
    tooltip: "Strength of detection-rate variation across the covariate cycle.",
    body:
      "Modulation summarizes how much the binned detection rate varies across phase bins relative to the mean. Higher modulation means stronger cyclic structure in the marginal PSTH before joint de-confounding.",
    usedIn: ["Level 1 PSTH table"],
    provenance: "psth_with_null modulation statistic",
    seeAlso: ["level1-psth", "null-z"],
  },
  "null-z": {
    id: "null-z",
    term: "Null z",
    tooltip: "How many null-standard deviations above the shuffled-phase null the modulation sits.",
    body:
      "The phase-shuffle null destroys temporal alignment while preserving marginal counts. The z-score compares observed modulation to the null distribution; larger values mean the pattern is unlikely under chance alignment.",
    usedIn: ["Level 1 PSTH table"],
    seeAlso: ["null-p", "beats-null", "modulation"],
  },
  "null-p": {
    id: "null-p",
    term: "Null p",
    tooltip: "Two-sided p-value for beating the phase-shuffle null.",
    body:
      "Null p is the tail probability under the shuffled-phase null. Small values support rejecting the null that the covariate phase is unrelated to detection timing.",
    usedIn: ["Level 1 PSTH table"],
    seeAlso: ["null-z", "beats-null"],
  },
  "beats-null": {
    id: "beats-null",
    term: "Beats null",
    tooltip: "Pass when modulation exceeds the phase-shuffle null at the gate threshold.",
    body:
      "Beats null is the Level 1 gate verdict for a covariate. Passing does not guarantee the covariate stays in the joint model (coverage and overlap rules still apply), but failing means the marginal cyclic structure is not distinguishable from shuffled phase.",
    usedIn: ["Level 1 PSTH table", "Provenance modal badges"],
    seeAlso: ["level1-psth", "null-p"],
  },
  "level0-detector-qc": {
    id: "level0-detector-qc",
    term: "Level 0 detector QC",
    tooltip: "Reviewed OrcaHello outcome mix — separate from the acoustic spike-train fit.",
    body:
      "Level 0 summarizes human-reviewed detector labels (confirmed, false positive, unknown, unreviewed) from OrcaHello. It characterizes the acoustic detector without treating every candidate as a confirmed whale event.",
    usedIn: ["Gates dashboard"],
    provenance: "orcahello_reviewed_detector_outcomes time-series → fit_report.level0_detector_qc",
    seeAlso: ["integrity-conditions"],
  },
  "held-out-cv": {
    id: "held-out-cv",
    term: "Held-out cross-validation",
    tooltip: "Out-of-sample deviance skill across time blocks.",
    body:
      "Time-blocked cross-validation holds out contiguous periods and scores predictive deviance against climatology. Negative mean skill means the model underperforms a simple baseline on held-out windows.",
    usedIn: ["Gates dashboard"],
    seeAlso: ["fitness-gates", "pit-calibration"],
  },
  "time-rescaling": {
    id: "time-rescaling",
    term: "Time-rescaling GOF",
    tooltip: "In-sample check that rescaled inter-event intervals look Exponential(1).",
    body:
      "Time-rescaling transforms detection times using the fitted intensity. Under a correct model, rescaled intervals should be standard exponential. We report this in-sample separately from held-out PIT calibration.",
    usedIn: ["Gates dashboard"],
    seeAlso: ["pit-calibration"],
  },
  "pit-calibration": {
    id: "pit-calibration",
    term: "PIT calibration",
    tooltip: "Held-out probability integral transform vs Uniform(0,1).",
    body:
      "PIT checks whether predicted counts are calibrated on held-out folds. Passing supports using the model for calibrated uncertainty; failing means confidence should stay conservative.",
    usedIn: ["Gates dashboard"],
    seeAlso: ["held-out-cv", "time-rescaling"],
  },
  "psth-kernel-consistency": {
    id: "psth-kernel-consistency",
    term: "PSTH vs kernel consistency",
    tooltip: "Diagnostic correlation between marginal PSTH and fitted kernel shape.",
    body:
      "This is a diagnostic, not a hard gate. Under correlated covariates the joint kernel can legitimately diverge from the marginal PSTH; low correlation is not automatically a failure.",
    usedIn: ["Gates dashboard"],
    seeAlso: ["level1-psth"],
  },
  provenance: {
    id: "provenance",
    term: "Provenance",
    tooltip: "Click-to-trace link from a map cell to kernels, gates, and evidence.",
    body:
      "Provenance answers why a cell looks the way it does: fitted kernel contributions, gate verdicts, spatial metadata, and a sample of nearby evidence with source links where available.",
    usedIn: ["Forecast map modal", "/api/provenance"],
    seeAlso: ["fitness-gates", "integrity-conditions"],
  },
  "sighting-check": {
    id: "sighting-check",
    term: "Sighting check",
    tooltip: "Conversational read on encounter likelihood vs verifying your observation.",
    body:
      "Sighting check separates three questions: whether the temporal model suggests elevated encounter likelihood for the pilot region, whether your specific observation was likely an orca (often unknowable without review), and whether you should submit a moderated report. Answers cite /api/provenance and /api/gates facts. Production narration uses Amazon Bedrock (Claude Haiku via IAM); template fallback when Bedrock is disabled or errors.",
    usedIn: ["/ask", "POST /api/sighting-assist"],
    provenance: "build_sighting_context → compose_reply (Bedrock Haiku or template)",
    seeAlso: ["provenance", "level0-detector-qc", "integrity-conditions"],
  },
};

export const GLOSSARY_ORDER = [
  "fitness-gates",
  "integrity-conditions",
  "level1-psth",
  "covariate",
  "modulation",
  "null-z",
  "null-p",
  "beats-null",
  "level0-detector-qc",
  "held-out-cv",
  "time-rescaling",
  "pit-calibration",
  "psth-kernel-consistency",
  "provenance",
  "sighting-check",
];
