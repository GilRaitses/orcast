# 8. Limits and falsification

## Current limits

The pilot deployment has known scope constraints that are part of the honesty model, not deficiencies to be concealed before submission.

The acoustic data covers one hydrophone station (Haro Strait, OrcaHello) over approximately 7.5 months. The temporal kernels are estimated from this single station's unreviewed candidate stream. Diel and lunar kernels are fitted; tide, season, and salmon index kernels are in the leveled program but not yet fitted at L1. The spatial kernel is prior-dominated. Effective confidence is 0 percent promoted until a reviewer records a promotion decision, which has not yet occurred.

Two search families returned Partial verdicts in the research phase. The effort bias family (SF-1) lacks a cetacean-specific effort-correction measurement in the arXiv corpus; the analogs (PAWS poaching prediction \cite{arxiv190306669}, ML for wildlife conservation \cite{arxiv211012951}) support the methodological claim but not a cetacean-domain number. The null gating family (SF-4) lacks ecology-journal documentation of phase-shuffled null tests for diel/lunar covariates; the neuroscience precedents \cite{arxiv201004875,arxiv150602361} establish the statistical machinery but not the ecological application specifically.

## Falsification table

The following conditions would weaken or falsify hypothesis H1 in this deployment:

| Observation | Interpretation |
|-------------|----------------|
| Displayed confidence rises without a promotion decision | Gate policy failed; H1 weakened for that event |
| Provenance modal omits a failed gate | Honesty contract violated; audit chain broken |
| Citizen submission influences model without moderation approval | Governance gap persists; corollary 3 falsified |
| Sighting check returns a confident yes/no without gate-grounded uncertainty disclosure | LLM layer violated prepare-then-narrate constraint |
| New covariate passes all gates but CV deviance skill is negative | Gate battery correctly withholds confidence; this is a correct outcome, not a failure |

## Extension path

The extension path after the pilot adds stations, reviewed OrcaHello labels, effort covariates, and spatial kernels. Each addition re-runs the full gate battery. The hypothesis is that effective confidence moves only when gates and human authority agree. If confidence rises after adding reviewed labels and fitting the spatial kernel, that is an expected outcome of the system functioning correctly; the audit chain will show the specific gate verdicts and promotion decisions that authorized the increase.

The W-Eval next-phase study (chartered separately) tests H1 directly through a structured field observer panel comparing steward trust in orcast's gate-bounded forecast against a confidence-smoothed baseline map.
