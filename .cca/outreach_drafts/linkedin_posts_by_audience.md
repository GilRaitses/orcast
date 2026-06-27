# LinkedIn posts, 5 audiences (claim-gated)

**Author:** Gil Raitses / aimez.ai
**Status:** Draft. Every claim checked against `.cca/CLAIM_BOUNDARIES.md` (capability table, exact-numbers table, forbidden list). First-person singular only, no "we/our".
**Gate note:** Maps-only uncited baseline is **60–100% (2026-06-24)**, Scenario 1 (60%, orca evidence) to Scenario 7 (100%, trip planning) in `grounding_parallel_rag.py`. Reconciled across CLAIM_BOUNDARIES, WP1, and WP2 on 2026-06-26. The separate 3-query probe average is 85%.

How to choose: post 1–2 weeks apart, lead with the audience whose feed you most want to reach first. Posts 3 (builders) and 4 (grounding) share the benchmark finding; don't run them back-to-back.

---

## Post 1, AI / ML researchers (HAII, grounding, orchestrator-in-the-loop)

*Audience: people who work on human-agent systems, RAG, LLM evaluation. Anchored to WP2.*

Human-in-the-loop agentic systems route a request through an orchestrator that dispatches tool-bearing sub-agents and narrates a result, but they ship without a metric for whether the narration is bound to the evidence the orchestrator actually gathered.

So I defined one. R_uncited is the fraction of scientific sentences in a system's output that carry no bound citation. It's a formal evaluation primitive for orchestrated-reasoning quality, not a vibe check.

The finding, from a reproducible benchmark against the Gemini Interactions API with Google Maps grounding on marine-science queries (2026-06-24): Maps-only geospatial grounding leaves 60–100% of scientific claims uncited across query types. Injecting a structured orchestrated skill-dispatch step-log as RAG context drops R_uncited to 0%.

The mechanism matters more than the number. 0% does not mean the model got better at citing science, it means the query type changed. A complete reasoning trace turns an open-domain science question into a closed artifact-reference question. That gives a RAG lift hierarchy: step-log > structured data > narrow context > unstructured. You diagnose a grounding architecture by how well its context type aligns with the query.

This is built into orcast, a gate-bounded encounter-forecasting pilot for Southern Resident killer whales, and written up as a companion paper.

Whitepaper 2 (grounding benchmark) and the measurement tool are reproducible.

#HAII #LLM #RAG #AIevaluation #AgenticAI

---

## Post 2, Marine science / conservation / ecology

*Audience: marine biologists, conservation tech, citizen-science orgs. Anchored to WP1.*

Wildlife encounter forecasts are usually shown as smooth probability maps that carry no record of the evidence behind them. You can't tell whether a hotspot reflects animal behavior, observer effort, acoustic false positives, or model overfit.

orcast is a pilot platform that enforces a different contract for Southern Resident killer whales in the Salish Sea: the forecast is always shown, but its displayed confidence is bounded by automated statistical gates, explicit integrity conditions, and a human promotion step, with a per-cell provenance trace from map cell back to source record.

Right now the effective confidence is 0%. That is the honest answer, not a bug: the held-out cross-validated deviance skill is −0.018 (3 of 5 folds passing), so the gates correctly withhold confidence rather than dress up a model that hasn't earned it. Citizen-science sightings stay quarantined until a human promotes them.

The motivation is well documented in the literature: SRKW occurrence records are largely opportunistic and effort-biased (Olson et al. 2018), preferential sampling misleads intensity estimates unless explicitly corrected (Diggle et al. 2010), and the effort-corrected surface that does exist is a static advisory product (Thornton et al. 2022). orcast is an attempt to make the evidence, and its limits, auditable.

Whitepaper 1 covers the forecasting architecture.

#MarineConservation #SalishSea #OrcaConservation #CitizenScience #DataIntegrity

---

## Post 3, Engineers / builders (the stack)

*Audience: backend / cloud / full-stack engineers. The "how it's wired" post.*

A forecast you can't audit isn't trustworthy, so I built orcast so every displayed confidence value is earned, not assumed, and made the whole evidence chain inspectable.

The gate battery: a fitted cyclic kernel (diel, lunar, seasonal) must clear a phase-shuffled null test, a time-rescaling goodness-of-fit check, a held-out deviance skill gate, and PIT calibration before it can contribute to displayed confidence. Fail any gate and the map shows the integrity condition and the reason confidence is withheld, not a blank.

The provenance panel: click any map cell and drill down to the acoustic detections, fitted kernels, and gate verdicts that produced its value. The provenance graph renders the interaction step-log as a typed node graph, Claim → Method → Experiment → Data, with grounded_in tracing a claim to its research origin, and a "no signal" badge on any claim with no supporting experiment. Every annotation is bound to an artifact ID.

Stack: Amazon DynamoDB (9 tables, system of record), AWS Step Functions, App Runner, Amazon Bedrock, S3, Vercel, WorkOS AuthKit. Submitted to the AWS + Vercel hackathon as an aimez.ai project.

Live demo and both whitepapers linked below.

#AWS #DynamoDB #StepFunctions #Bedrock #Vercel #SystemDesign

---

## Post 4, AI honesty / trust & safety / grounding-vs-hallucination

*Audience: people who care about LLM trust, hallucination, evaluation rigor. Sharpest single finding.*

I ran the same marine-science question through two grounding setups and measured how much of the scientific content was actually backed by a citation (2026-06-24).

Google Maps grounding, the kind that powers "near me" answers, left 60–100% of scientific claims uncited depending on the query. It grounded the park, the lighthouse, and the museum as places, and grounded none of the fisheries data, census, or hydrophone evidence the answer named.

A structured step-log from an orchestrated skill-dispatch pipeline, injected as context, brought the uncited rate to 0%.

The honest read: that 0% is not the model becoming a better scholar. It's the query changing shape, from an open-domain science question (answered from parametric memory) into a closed artifact-reference question (answered from the trace). The honesty primitive is the part Maps grounding lacks: any claim with no supporting artifact renders a visible "no signal" badge instead of confident prose.

If your product narrates over retrieved evidence, the question isn't "does it cite?", it's "what fraction of the scientific sentences are bound to an artifact?" That's a number you can measure and regress on per release.

#AIsafety #Hallucination #TrustworthyAI #LLMevaluation #Grounding

---

## Post 5, Founders / solo builders / indie

*Audience: indie hackers, solo founders, the "shipped it alone" crowd. The build-discipline narrative.*

I shipped orcast solo, as aimez.ai: a gate-bounded encounter-forecasting system for endangered killer whales, two whitepapers, and a reproducible benchmark, into the AWS + Vercel hackathon.

The hardest discipline wasn't the code. It was refusing to overclaim. I keep a claim-boundaries file that every sentence, in the product, the papers, and posts like this one, has to pass. "Predicts whale locations" is forbidden (there's no spatial prediction). "Identifies orca from photos" is forbidden (no computer vision). "High accuracy" is forbidden (the cross-validated skill is negative).

So the system's headline number is 0% effective confidence, and that's the feature. The gates correctly suppress confidence the model hasn't earned, and the UI shows the reason instead of a reassuring map. Building the thing that tells the truth about its own uncertainty was the whole point.

Solo doesn't mean unrigorous. It means you are the only gate, so you write the gates down.

Live demo and whitepapers in comments.

#BuildInPublic #SoloFounder #IndieHackers #AI #aimezai

---

## Pre-publish checklist (all posts)

- [ ] No "we/our", first-person singular or aimez.ai.
- [ ] Every number matches CLAIM_BOUNDARIES exact-numbers table + carries its date where required (R_uncited: 2026-06-24).
- [ ] No forbidden claim (predicts locations / CV species ID / high accuracy / promoted=reliable / 0%=broken / R_uncited=0% means cites science / LeCun gap filled).
- [ ] Maps baseline stated as 60–100% (reconciled across CLAIM_BOUNDARIES, WP1, WP2).
- [ ] Attach media: provenance drilldown GIF (post 3), /explore routing GIF (post 1), gates dashboard screenshot with 0% + reason (posts 2, 4, 5).
- [ ] Live link: https://orcast-h0.vercel.app
