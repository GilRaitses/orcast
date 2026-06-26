# 5. Governance: quarantine, authority, and audit

Shore-based sighting submissions from citizen observers enter the orcast pipeline through a moderation queue that enforces quarantine before any submission can influence model outputs or appear in aggregated community data. The governance architecture has three components: quarantine by default, signed human authority, and an immutable decision record.

## Why quarantine is necessary

Citizen science data without explicit quality control produces systematic confidence overestimates in probabilistic models. The information quality literature frames citizen science as a user-generated content problem and establishes that quality management pipelines are a necessary condition for scientific usability, not an optional enhancement \cite{arxiv190508289}. The LIGO Gravity Spy program provides an operational precedent at scale: over 35,000 citizen scientist classifier votes are aggregated and validated against expert labels before influencing detector characterization \cite{arxiv161104596}. The Milky Way Project demonstrates that direct use of citizen labels as model training data without quality control requires ensemble aggregation and calibration against expert ground truth; unmoderated labels alone produce systematic errors \cite{arxiv140626920}. Galaxy morphology classification shows the same pattern: hybrid human-ML pipelines outperform either component alone, but only when citizen data is filtered for quality before combining \cite{arxiv140979350}.

For southern resident killer whale monitoring, the additional challenge is that citizen observer reliability varies with conditions, season, location, and experience. A submission labeled as a sighting may be a misidentification, an off-season anomaly, or a duplicate of an existing record. Without quarantine, these submissions propagate into hotspot aggregations and model inputs with the same weight as validated records.

## Signed human authority

orcast separates automated gate eligibility from human promotion authority. A model fit that passes L1 through L3 fitness gates is eligible for promotion, but promotion requires a signed decision by a registered reviewer recorded in the decision-records DynamoDB table. This mirrors the governance pattern for controlled scientific databases where human sign-off is a mandatory step before results enter downstream products. The decision record includes the reviewer identity, the verdict (promote, hold, or reject), the cited gates, and a rationale field. The record is immutable and auditable.

## Moderation queue mechanics

Community shore submissions are stored in the community-submissions DynamoDB table in a pending state. They are visible to registered reviewers in the moderation queue interface. Approval stamps attribution (the reviewer identity) and a low reliability weight before the submission can influence the model. Rejection records the submission in the audit log without propagating it. Private field journal entries remain private unless the author explicitly publishes them to the community queue, at which point they enter the same moderation pipeline.

This architecture means that the confidence meter and integrity conditions displayed on any public surface accurately reflect only validated and promoted data, with the provenance chain fully auditable to the specific reviewer decisions that authorized each data point.
