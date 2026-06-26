# orcast Claim Boundaries

Any claim emitted by an agent — in prose, in a social post, in whitepaper text, or in a Devpost description — must appear in the ALLOWED column or be derivable from a live evidence source listed here.

**Violation procedure:** If you are about to emit a claim not in the ALLOWED column, flag it in your message before proceeding and wait for instruction.

---

## System capability claims

| Claim | Status | Evidence source |
|-------|--------|-----------------|
| orcast shows gate-bounded encounter confidence | ALLOWED | `/api/be/api/gates` → `effective_confidence`, `caveats` |
| Every map cell traces to kernels and gate verdicts | ALLOWED | `/api/be/api/provenance`, provenance modal in demo |
| Citizen-science sightings are quarantined until a human promotes them | ALLOWED | `community-submissions` DynamoDB table, moderation queue |
| The grounding benchmark: surface planner step-log achieves 0% uncited rate | ALLOWED | `tools/testing/grounding_parallel_rag.py` run 2026-06-24; cite date |
| Maps-only grounding baseline: 60–100% uncited (8-scenario) | ALLOWED | `tools/testing/grounding_parallel_rag.py` run 2026-06-24, Scenario 1 (60%) and Scenario 7 (100%) |
| Maps-only 3-query probe: 85% uncited averaged (89% evidence query) | ALLOWED | `tools/testing/maps_grounding_probe.py` run 2026-06-24 |
| 9 DynamoDB tables as system of record | ALLOWED | `tools/waves/gates/q1c-ddb-schema.sh` PASS; live count confirmed |
| Managed AI agents with step-log provenance | ALLOWED | `surface-planner-v1` interaction trace visible in Beat 04 |
| The model was fitted but has 0% effective confidence | ALLOWED | `effective_confidence = 0.0` from `/api/be/api/gates` (no promotion yet) |
| Evidence uploads (images, audio) via /ask | ALLOWED | Wave Set U code done; note "deployment pending" if claiming live |
| Account page showing user's journal, uploads, submissions | ALLOWED | Code done; note "deployment pending" |
| orcast predicts whale locations | **FORBIDDEN** | No spatial prediction; orcast forecasts encounter likelihood at a station |
| orcast identifies orca species from images | **FORBIDDEN** | No computer vision; sighting check is LLM-grounded text, not CV |
| orcast achieves high forecast accuracy | **FORBIDDEN** | CV deviance skill is negative; model explicitly does not claim skill |
| The promoted badge means the model is reliable | **FORBIDDEN** | Promotion was authorized; effective_confidence is 0% because deviance skill is negative |
| 0% confidence means the system is broken | **FORBIDDEN** | 0% is the honest answer: gates correctly suppress confidence |
| R_uncited = 0% means the AI cites scientific sources | **FORBIDDEN** | It means the LLM answers from artifact references, not from world knowledge; the query type changed, not citation generation |
| LeCun's AMI framework gap is filled by orcast | **FORBIDDEN** | This is a future-work hypothesis, not demonstrated; see WP2 Section 7 |

---

## Quantitative claims — use these exact numbers

| Metric | Value | Date | Source |
|--------|-------|------|--------|
| DynamoDB tables | 9 | Live | q1c-ddb-schema.sh |
| Sightings records | 229 | 2026-06-25 | q1c scan |
| Hotspots | 113 | 2026-06-25 | q1c scan |
| Decision records | 3 | 2026-06-25 | q1c scan |
| Managed agent cast roles | 4 | 2026-06-25 | q1c scan |
| R_uncited step-log | 0% | 2026-06-24 | grounding_parallel_rag.py Scenario 4 |
| R_uncited Maps-only baseline | 60–100% | 2026-06-24 | grounding_parallel_rag.py Scenario 1 (60%), Scenario 7 (100%) |
| Demo video duration | 2m 13s (132.6s) | 2026-06-25 | a-video-gate |
| WP1 full PDF pages | 10 | 2026-06-26 | latexmk/biber rebuild |
| WP1 share PDF pages | 7 | 2026-06-26 | latexmk/biber rebuild |
| WP2 full PDF pages | 5 | 2026-06-26 | pdfinfo Build/Raitses_orcast_grounding_2026.pdf |
| WP2 share PDF pages | 4 | 2026-06-26 | pdfinfo Build/Raitses_orcast_grounding_2026_share.pdf |
| OrcaHello false-positive rate | 0.673 (reported) | 2022-06-22 fit | level0_detector_qc in /api/gates |
| CV deviance skill | −0.018 | Fit date 2022-06-22 | /api/gates held-out CV |
| CV folds passing | 3/5 | Fit date 2022-06-22 | /api/gates |

---

## Prose register constraints (for whitepaper rewrite)

Reference: `/Users/gilraitses/neuro/Raitses_SeptalGABAergicTiming_2026/Build/Raitses_SeptalGABAergicTiming_2026.pdf`

| Pattern | Status |
|---------|--------|
| "In this section we show that…" | FORBIDDEN — open with the claim |
| "We propose a framework for…" | FORBIDDEN — state the claim directly |
| "This paper contributes…" | FORBIDDEN — the contribution is the claim, not the meta-claim |
| "Our approach…" | FORBIDDEN — describe the mechanism, not the ownership |
| Passive voice for results | FORBIDDEN — "The gate battery reduces confidence" not "Confidence is reduced by the gate battery" |
| Bullet lists in body prose sections | FORBIDDEN — convert to prose |
| Hedging qualifiers ("might", "could", "seems to") | FORBIDDEN — state what the data shows; if uncertain, state the condition |
| Numbered inline citations [n] after each claim | REQUIRED |
| Opening each paragraph with the claim | REQUIRED |
| Falsifiability criterion stated explicitly | REQUIRED in each section that makes a testable prediction |

---

## Primary-anchor claim gate (see docs/whitepaper/PRIMARY_ANCHOR_CLAIM_GATE.md)

No "there is a gap" / "no existing system does X" claim may be emitted unless a named,
verified, well-cited primary study is cited AND the gap is shown by verified absence in
that source. Asserted gaps are downgraded to "open question" or removed.

| Claim | Status | Primary anchor |
|-------|--------|----------------|
| SRKW occurrence is built from opportunistic, effort-biased hotspot data | ALLOWED | Olson et al. 2018, ESR 37:105–118 |
| Effort-biased (preferential) sampling misleads intensity estimates without explicit correction | ALLOWED | Diggle, Menezes & Su 2010, JRSS-C 59(2):191–232 |
| An effort-corrected SRKW surface exists but is a static advisory product | ALLOWED | Thornton et al. 2022, DFO CSAS Res. Doc. 2022/037 |
| Orchestrator-in-the-loop agent systems ship without an output-grounding metric | ALLOWED | Magentic-UI (Mozannar et al. 2025, arXiv:2507.22358) — verified absence of any grounding metric |
| Mixed-initiative interaction requires inference over uncertain user intent | ALLOWED | Horvitz 1999, CHI '99 pp. 159–166 |
| LeCun's AMI gap is filled by orcast | **FORBIDDEN** | future-work hypothesis only; LeCun is context, not a load-bearing anchor |
