# Q0 — Scrutiny and Gap Closing charter

Date: 2026-06-25
Wave set: **Q** (Scrutiny)
Predecessor: Wave Sets R, SC complete; a-gate PASS (2026-06-25)
Purpose: Find and close every gap between the production build, the submission copy, and the diagrams before the June 29 deadline.

## Scrutiny methodology

Each Q1 sub-wave scans one layer and writes findings to `docs/devpost/Q_GAP_REGISTER.md` with severity:
- **P0**: Demo or submission breaks on camera — judge sees failure
- **P1**: Claim in DEVPOST or whitepaper is not demonstrable or code-grounded
- **P2**: Minor inconsistency — accurate but suboptimal

## Layers covered

| Wave | Layer | Method |
|------|-------|--------|
| Q1a | UI/visual | Playwright assertions (new scrutiny.spec.ts) |
| Q1b | API/backend | curl + JSON schema checks |
| Q1c | Data layer | Python DynamoDB scan |
| Q1d | Submission copy | Manual + benchmark re-run |
| Q1e | Architecture diagram | Code cross-reference |
| Q1f | Whitepaper claims | grep for E1–E8 equation terms in code |

## Remediation and close

Q2–QN close gaps in severity order. QF is a final adversarial review that re-runs all Q1 checks and delivers a signed verdict.
