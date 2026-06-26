# Primary-Anchor Claim Gate

Status: methodology of record for orcast whitepapers
Date: 2026-06-25

## Problem this gate fixes

The current orcast whitepapers assert gaps as if self-evident. WP1 opens with "four
gaps in encounter forecasting"; WP2 leans on a LeCun/AMI framing. Neither derives its
gap from a single, named, well-cited primary study that a hostile reviewer would accept.
This is motivated retrieval: the SF-01..SF-16 search families in
`tools/testing/em_research.py` are organized around claims-to-support, so they always
return *something*, and an unsupported "there is a gap" slips through.

The neuro reference paper (`Raitses_SeptalGABAergicTiming_2026`) does the opposite: it
names "the primary circuit study" and builds the gap *from* it. That is the standard this
gate enforces.

## The rule

A whitepaper may not assert a gap, a deficiency, or a "no existing system does X" claim
unless ALL of the following hold:

1. **A primary study is named.** One published, peer-reviewed or government-science
   source that establishes the state of the art the gap is measured against. Not a
   keyword-matched pile of five abstracts.
2. **The primary study is verified.** Its claimed content is confirmed by reading the
   source, not the search-engine synthesis. (The synthesis for WP1's anchor mislabeled
   the authors as "Watson"; the verified authors are Thornton et al. The gate caught it.)
3. **The gap is derived by verified absence.** The gap is demonstrated by what the
   primary study does NOT do, confirmed by searching the source text for the missing
   element and finding it absent — not by asserting the field ignores it.
4. **The contribution maps to the absence.** orcast's contribution must be the specific
   thing the primary study lacks, stated as such.

Any claim failing 1–4 is downgraded to "open question" or removed.

## Verification procedure

For each anchor, record in this file:
- exact citation (authors, year, venue, identifier)
- the verified claim (quoted phrase + where found in the source)
- the verified absence (the grep that returned empty)
- the derived gap and orcast's mapped contribution

---

## WP1 anchor — encounter forecasting / field studies

**Primary study (verified):**
Thornton, S.J., Toews, S., Stredulinsky, E., Gavrilchuk, K., Konrad, C., Burnham, R.,
Noren, D.P., Holt, M.M., & Vagle, S. (2022). *Southern Resident Killer Whale (Orcinus
orca) summer distribution and habitat use in the southern Salish Sea and the Swiftsure
Bank area (2009 to 2020).* DFO Canadian Science Advisory Secretariat (CSAS) Research
Document 2022/037. National Capital Region.

**Why it qualifies:** Government science (DFO Pacific Science Enterprise Centre with NOAA
NMFS co-authors Noren and Holt), directly on SRKW in the exact waters orcast covers (Haro
Strait, Salish Sea), and it is the authoritative effort-corrected occurrence product.

**Verified claim (read from source):**
- "preferential sampling bias in sightings data"
- "adjusting for variability in both observer effort and whale detectability"
- "effort-correct the sightings data to create a relative density estimate"
- Method: Log-Gaussian Cox Process; sightings strengthened with PAM acoustic detections.

**Verified absence → derived gap:**
Thornton et al. produce a single effort-corrected density *surface*. It is a static
research advisory product. It does not (a) expose, per displayed cell, the evidence and
statistical gates that earned that cell's confidence; (b) bound displayed confidence by a
held-out skill / calibration gate that can withhold confidence when skill is negative;
(c) govern live citizen-science ingestion with quarantine and signed human promotion.

**orcast's mapped contribution:** the operational layer Thornton et al. is not — per-cell
provenance, gate-bounded confidence (including the honest 0% when CV deviance skill is
negative), and quarantined community ingest with an immutable promotion audit.

**Allowed framing:** "Thornton et al. (2022) [primary] established the effort-corrected
SRKW occurrence surface for these waters using a Log-Gaussian Cox Process that adjusts for
observer effort and detectability. That advisory product does not expose, per displayed
cell, the gates and evidence that earned its confidence. orcast supplies that operational
provenance and confidence-governance layer." (No "wildlife forecasts hide evidence"
assertion required.)

---

## WP2 anchor — HAII / orchestrated managed agents

This is the second paper. The routing/chat-console system is its primary objective, not a
side note in WP1. Two anchors bracket it.

**Foundational anchor (verified):**
Horvitz, E. (1999). *Principles of Mixed-Initiative User Interfaces.* Proc. ACM SIGCHI
Conference on Human Factors in Computing Systems (CHI '99), pp. 159–166.
DOI 10.1145/302979.303030.

Establishes mixed-initiative interaction: coupling automated services with direct
manipulation under explicit uncertainty about user goals, with probabilistic inference of
user intent and cost-benefit timing of automated action. This is the canonical primary
source for intent-aware human-AI collaboration.

**Contemporary anchor (verified):**
Mozannar, H., Bansal, G., Tan, C., Fourney, A., Dibia, V., Chen, J., Gerrits, J., Payne,
T., Kunzler Maldaner, M., Grunde-McLaughlin, M., Zhu, E., Bassman, G., Alber, J., Chang,
P., Loynd, R., Niedtner, F., Kamar, E., Murad, M., Hosn, R., & Amershi, S. (2025).
*Magentic-UI: Towards Human-in-the-loop Agentic Systems.* Microsoft Research AI Frontiers,
MSR-TR-2025-40 / arXiv:2507.22358.

(Co-author Saleema Amershi also led *Guidelines for Human-AI Interaction*, CHI 2019, so
this anchor sits in the established HAII lineage rather than being a one-off.)

**Verified claim (read from source):**
- "a lead Orchestrator agent that directs a set of agents to perform actions"
- "Model Context Protocol (MCP) tools via custom agents"
- interaction mechanisms: "co-planning, co-tasking, multi-tasking, action guards, and
  long-term memory"
- human user "treated as an agent that plays a special role in the multi-agent team"

This is a near-mirror of orcast's architecture: orchestrator-in-the-loop, MCP tools,
authorized sub-agents with skills, human-in-the-loop, plan-then-execute, action gates.

**Verified absence → derived gap:**
Grep of the full Magentic-UI text for `uncited | evidence-binding | grounding quality |
citation rate | R_uncited` returned empty. Magentic-UI evaluates autonomous task
completion, simulated/real user interaction, and safety. It proposes NO claim-level
evidence-binding metric for the orchestrated reasoning trace — it does not measure whether
the narrated output is bound to the artifacts the orchestrator actually gathered.

**orcast's mapped contribution:** R_uncited applied to the orchestrator's step-log — a
claim-level grounding-quality metric for the orchestrated trace, plus the intent-mining
feedback loop from the chat console. The contribution is the measurement layer Magentic-UI
(and the broader human-in-the-loop agent literature it represents) does not provide.

**Allowed framing:** "Horvitz (1999) [foundational] framed mixed-initiative interaction as
inference over uncertain user intent; Magentic-UI (Mozannar et al., 2025) [contemporary]
realizes this as an orchestrator directing MCP-tool sub-agents with the human in the loop.
Neither proposes a claim-level metric for whether the orchestrated trace's narrated output
is bound to the evidence it gathered. R_uncited supplies that metric." No LeCun/AMI
gap-assertion required; LeCun stays as optional future-work context, not load-bearing.

---

## What changes in the existing papers

| Paper | Current load-bearing gap claim | Replace with |
|-------|-------------------------------|--------------|
| WP1 | "four gaps in encounter forecasting" (asserted) | Gap derived from Thornton et al. 2022 by verified absence |
| WP2 | LeCun AMI requires evidence binding (asserted) | Gap derived from Magentic-UI 2025 by verified absence; Horvitz 1999 as foundation; LeCun demoted to optional context |

## Decisions taken (2026-06-25) and applied

1. **WP1 journal anchor (resolved):** journal primaries preferred over the advisory doc.
   The cited chain is now Olson et al. 2018 (ESR; opportunistic SRKW hotspot data) +
   Diggle, Menezes & Su 2010 (JRSS-C; preferential-sampling LGCP correction), with
   Thornton et al. 2022 (DFO CSAS) cited as the applied effort-correction for this
   population. Applied in `LX/Sections/02_four_gaps.tex`; entries added to
   `LX/references.bib` (olson2018, diggle2010, thornton2022). WP1 rebuilt: 10 pp, 0
   undefined citations.
2. **WP2 reframe (resolved):** the grounding benchmark is folded into a Magentic-UI /
   Horvitz-anchored human-in-the-loop paper. Title now ends "...for human-in-the-loop
   agentic systems"; abstract, Section 2, and Section 6 re-anchored; LeCun AMI demoted to
   context in `references2.bib`. Entries added: horvitz1999, magenticui2025. WP2 rebuilt:
   5 pp full / 4 pp share, 0 undefined citations.
3. This gate does not touch the frozen hackathon submission (DEVPOST_DRAFT.md, demo). It
   governs the whitepaper rewrites only.
