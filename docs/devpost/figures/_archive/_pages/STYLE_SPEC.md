# ORCAST draw.io remediation style spec

Reference image: `docs/devpost/figures/_ref/decisiondb-fig2.png`

## Shared visual style

- Use the DecisionDB Figure 2 style as the primary reference: simple rectangular boxes, one light purple accent family, thin purple strokes, and minimal text.
- Prefer two-compartment entity boxes: a shaded header row and white field rows.
- Keep labels short enough to render without overlap at `--scale 2`.
- Every page must include:
  - A short title.
  - A small version/date note.
  - A legend or note explaining connector semantics.
- Avoid crossing connectors where possible. Orthogonal edges should have explicit waypoints if needed.
- Use ASCII text only.

## ER notation for Pages 1 and 5

For schema/provenance pages, match the arXiv Figure 2 endpoint convention:

- The referenced primary key end uses a filled arrowhead into the `(PK)` row:
  - `endArrow=block;endFill=1`
- The dependent foreign/logical-reference end uses an open/crow-foot-like marker:
  - `startArrow=open` or `startArrow=ERmany`
- Add a literal `FK` label at or near the dependent endpoint.
- Attach schema edges to key/field rows where possible, not to the outer table box.
- Mark key rows explicitly with `(PK)` and `(FK)` or `(logical FK)`.

Page 1 is DynamoDB, not a relational database. Its legend must say:

`Logical references only: DynamoDB enforces pk only; no FK constraints; current access patterns are scan-based unless noted.`

## Flow notation for Pages 2-4

- Do not use FK/crow-foot notation for control-flow or data-flow diagrams.
- Use filled arrowheads for flow direction.
- Label each arrow with a concrete action, e.g. `writes reports/{id}.json`, `redirect`, or `reads models/*`.
- Use dashed lines only for optional/manual paths.

## Page-specific checklist

### Page 1 - DynamoDB ERD

- Replace the incorrect `decision-records -> reports` relationship.
- `decision-records.kernel_version` must reference the fitted-kernel artifact / model version, not `reports`.
- `reports.hotspots[]` must be labeled as a denormalized snapshot embed, not a live composition.
- Include the DynamoDB app-level-reference disclaimer.

### Page 2 - Data layer

- Include the separate reports S3 bucket: `ORCAST_REPORTS_BUCKET`, `reports/{id}.json`.
- Show `BathymetryAdapter` as a static `data/geo` read, not a streaming external-source adapter.
- Do not claim every adapter sets `source_url`; distinguish source-linked adapters from local/static adapters.

### Page 3 - Workflows

- Reconcile the gate threshold with the live system.
- Annotate that current fitted confidence is around 0.5 and may route to Hold depending on the configured threshold.
- Show the manual `/api/decision-records` reviewer path.
- Include a compact Catch/Retry/error note for `FitAndGate`.

### Page 4 - Request + Auth flow

- Show the browser redirecting to hosted WorkOS AuthKit on `*.authkit.app`.
- Show `/api/gates` / `serve.py` reading `models/*` from S3.
- Keep public reads vs authenticated mutations/PII visually clear.

### Page 5 - DecisionDB mapping

- Add a new page mapping DecisionDB concepts to ORCAST:
  - snapshot -> frozen source payloads + time-series streams.
  - representation -> kernel configuration / fitted kernel version.
  - engine_run -> NB-GLM fit and gate run.
  - decision -> gate verdict and reviewer verdict.
  - f_map -> decision-records as a partial materialization.
- Cite `arXiv:2602.11295`.
- Note gaps honestly: ORCAST does not yet use content-addressed IDs and does not yet have a full materialized `f_map` table.
