# Whitepaper search-family grid

**Whitepaper working title:** Evidence-bounded encounter forecasting: an honest-model architecture for effort-biased wildlife observation data

**Axes:** Science (SF-1 to SF-6) + Systems (SF-7 to SF-14)  
**Baseline:** [WHITEPAPER_HYPOTHESIS.md](../devpost/WHITEPAPER_HYPOTHESIS.md)  
**Benchmark evidence:** [PROVENANCE_GRAPH_CONTRACT.md](../devpost/casting/PROVENANCE_GRAPH_CONTRACT.md) (Maps vs orcast grounding, 2026-06-24)

---

## Section blocking

| # | Section title | Families | Core falsifiable claim |
|---|---------------|----------|------------------------|
| 1 | The four gaps in encounter forecasting | SF-1, SF-6 | Effort bias, epistemic opacity, and governance failure are documented failure modes in wildlife encounter products |
| 2 | A gate-bounded honesty model | SF-3, SF-4, SF-5 | Null gating and explicit CV skill assessment can bound displayed confidence without hiding the forecast |
| 3 | Acoustic grounding: PSTH and Level 0 QC | SF-2 | False-positive rates in passive acoustic detection require explicit quarantine before influencing a probabilistic model |
| 4 | Provenance grounding as a system | SF-7, SF-9, SF-12 | Structured step-log citation architectures (prepare-then-narrate with artifact references) reduce unsupported claim rates below LLM tool-grounding baselines |
| 5 | Orchestrated managed agents with verified tools | SF-8 | Deterministic skill dispatch with tier-verified tools and plan-then-execute architecture prevents model hallucination of tool invocations |
| 6 | Governance: quarantine, authority, and audit | SF-10 | Human-in-the-loop promotion authority with an immutable decision record is a necessary condition for citizen-science data entering a probabilistic model |
| 7 | Geospatial grounding limits | SF-11 | Google Maps grounding resolves place citations but leaves scientific and evidence claims uncited; domain-specific provenance systems are required for the evidence layer |
| 8 | Limits and falsification | SF-5, SF-6 | orcast H1 is weakened or falsified under stated conditions; extension path is specified |

---

## Search-family grid

Column guide:
- **Claim**: the specific assertion this family must verify or falsify
- **Topic cluster**: the EM topic/keyword cluster to search
- **Representative EM queries (3–5)**: paste these directly into Emergent Mind
- **Verification target**: what a cited paper must demonstrate (minimum threshold)
- **Status**: Supported / Partial / Not found (fill after running searches)
- **orcast artifact**: the code or doc that implements or measures this claim

---

### Science axis

---

**SF-1 — Effort bias and detection/occupancy correction**

| Field | Content |
|-------|---------|
| Section | 1 |
| Claim | In wildlife monitoring datasets where detection probability is confounded with observer effort or hydrophone coverage, hotspot maps reflect detection density not animal density unless explicitly corrected |
| Topic cluster | occupancy modeling, detection bias, effort correction, spatial wildlife monitoring |
| **EM query 1** | "effort bias wildlife encounter forecasting detection probability" |
| **EM query 2** | "observer effort confounding orca sighting density hotspot" |
| **EM query 3** | "occupancy model detection correction acoustic monitoring bias" |
| **EM query 4** | "passive acoustic monitoring false positive rate presence absence detection" |
| **EM query 5** | "cetacean encounter rate spatial bias survey effort" |
| Verification target | At least one paper demonstrating that naive hotspot aggregation overstates animal presence relative to effort-corrected estimates in aquatic or wildlife data |
| Status | Not yet run |
| orcast artifact | `src/aws_backend/routers/explore.py` _keyed_automation; integrity condition "effort assumed continuous" in gates response |

---

**SF-2 — Acoustic detector QC and false positives (OrcaHello / Orcasound / PSTH)**

| Field | Content |
|-------|---------|
| Section | 3 |
| Claim | Passive acoustic detection systems (especially deep-learning classifiers like OrcaHello) have non-trivial false-positive rates that must be explicitly quarantined at Level 0 QC before influencing a statistical model |
| Topic cluster | OrcaHello, Orcasound, passive acoustic monitoring, false positive rate, bioacoustics ML classification |
| **EM query 1** | "OrcaHello killer whale acoustic classifier false positive rate" |
| **EM query 2** | "Orcasound passive acoustic monitoring uncertainty marine mammal" |
| **EM query 3** | "deep learning bioacoustics detection precision recall field deployment" |
| **EM query 4** | "PSTH peristimulus time histogram acoustic event spike train fit" |
| **EM query 5** | "Level 0 QC acoustic candidate review workflow marine mammal detector" |
| Verification target | Paper or report quantifying the false-positive rate of an acoustic ML classifier in field deployment, ideally >= 10% |
| Status | Not yet run |
| orcast artifact | `modeling/fit_kernels.py` spike-train PSTH; integrity condition "unreviewed acoustic candidates" in gate response; `src/aws_backend/routers/interactions.py` fetch_gates |

---

**SF-3 — Negative-binomial / point-process intensity for sparse counts**

| Field | Content |
|-------|---------|
| Section | 2 |
| Claim | Negative-binomial regression or Poisson point-process intensity models are the appropriate distributional family for sparse, overdispersed encounter count data where Gaussian models would underestimate zero-inflation |
| Topic cluster | negative binomial regression ecology, point process intensity ecological count data, overdispersed count models wildlife |
| **EM query 1** | "negative binomial regression wildlife count data overdispersion zero inflation" |
| **EM query 2** | "inhomogeneous Poisson process intensity ecological encounter rate" |
| **EM query 3** | "cyclic covariate diel lunar kernel encounter rate temporal model" |
| **EM query 4** | "sparse count data distribution family ecological forecasting selection" |
| **EM query 5** | "log-rate decomposition covariate contribution encounter intensity" |
| Verification target | Paper using NB or point-process intensity for wildlife encounter data and reporting superiority over Gaussian or Poisson for overdispersed field counts |
| Status | Not yet run |
| orcast artifact | `modeling/fit_kernels.py` negative-binomial kernel; `docs/methodology/FORECAST_KERNELS.md` |

---

**SF-4 — Null gating: phase-shuffled nulls and time-rescaling goodness-of-fit**

| Field | Content |
|-------|---------|
| Section | 2 |
| Claim | Phase-shuffled null tests and time-rescaling goodness-of-fit (KS test on rescaled intervals) are valid, conservative statistical gates for cyclic temporal covariates in count/point-process models |
| Topic cluster | phase shuffle null test cyclic covariate, time rescaling goodness of fit point process, KS test temporal model validation |
| **EM query 1** | "phase shuffled surrogate null test cyclic temporal covariate significance" |
| **EM query 2** | "time rescaling theorem Kolmogorov-Smirnov goodness of fit point process" |
| **EM query 3** | "diel lunar covariate null hypothesis test spike train temporal model" |
| **EM query 4** | "permutation null distribution temporal covariate ecological model gate" |
| **EM query 5** | "model selection gate criterion temporal ecological forecasting confidence bound" |
| Verification target | Paper using phase-shuffle or time-rescaling tests specifically, or a methodological review establishing these as valid null tests for cyclic covariates |
| Status | Not yet run |
| orcast artifact | `modeling/fit_kernels.py` null test; Level 1 PSTH section in `/gates` response; `FORECAST_KERNELS.md` |

---

**SF-5 — CV skill and calibration (PIT, deviance skill) for ecological forecasts**

| Field | Content |
|-------|---------|
| Section | 2, 8 |
| Claim | Negative mean held-out deviance skill and failed PIT (Probability Integral Transform) calibration are grounds for withholding displayed confidence, because they demonstrate that the model is not sharper than a reference null on out-of-sample data |
| Topic cluster | PIT calibration ecological forecast, held-out deviance skill predictive model, cross-validation ecological prediction |
| **EM query 1** | "probability integral transform PIT calibration ecological species distribution model" |
| **EM query 2** | "mean deviance skill cross-validation ecological forecasting out-of-sample" |
| **EM query 3** | "calibration ecological forecast confidence interval coverage skill score" |
| **EM query 4** | "Brier skill score deviance null model ecological forecast evaluation" |
| **EM query 5** | "negative skill score model worse than climatology null ecological prediction" |
| Verification target | Paper or framework paper establishing PIT or deviance skill as a calibration diagnostic for distributional ecological forecasts, with interpretation guidance for negative skill |
| Status | Not yet run |
| orcast artifact | `modeling/fit_kernels.py` CV loop; gate field `mean_deviance_skill`; `/gates` integrity conditions |

---

**SF-6 — Uncertainty communication and map overtrust**

| Field | Content |
|-------|---------|
| Section | 1, 8 |
| Claim | Users of confidence-smoothed spatial forecasts systematically overtrust displayed certainty, especially when maps do not expose the statistical basis or limits of model skill |
| Topic cluster | uncertainty visualization ecology, map overtrust confidence, ecological forecast communication uncertainty |
| **EM query 1** | "uncertainty visualization map user trust ecological forecast" |
| **EM query 2** | "confidence display spatial forecast decision making overtrust cognitive bias" |
| **EM query 3** | "forecast communication uncertainty public wildlife management" |
| **EM query 4** | "species distribution model confidence map user interpretation" |
| **EM query 5** | "honesty information interface design ecological uncertainty" |
| Verification target | Paper demonstrating user overtrust or miscalibrated decision-making when spatial forecasts omit uncertainty bounds or methodological caveats |
| Status | Not yet run |
| orcast artifact | `WHITEPAPER_HYPOTHESIS.md` H1; integrity conditions at `/`; `/gates` confidence meter |

---

### Systems axis

---

**SF-7 — LLM grounding and citation architectures (RAG, groundingSupports, hallucination reduction)**

| Field | Content |
|-------|---------|
| Section | 4 |
| Claim | Structured citation architectures (span-bound source references, prepare-then-narrate skill dispatch, step-log persistence) reduce the rate of unsupported scientific claims relative to unstructured LLM generation or place-grounded tool calls |
| Topic cluster | retrieval augmented generation citation hallucination reduction, grounding LLM factual accuracy, source attribution span binding |
| **EM query 1** | "retrieval augmented generation factual accuracy citation hallucination reduction" |
| **EM query 2** | "groundingSupports span citation binding LLM attribution architecture" |
| **EM query 3** | "prepare then narrate tool grounding LLM deterministic skill dispatch" |
| **EM query 4** | "structured step log LLM interaction provenance scientific claim" |
| **EM query 5** | "citation architecture place grounding vs dataset grounding evidence quality" |
| Verification target | Paper showing that structured grounding (tool dispatch + span citation) reduces unsupported-claim rate or hallucination rate relative to ungrounded or place-only grounded generation |
| Status | Not yet run |
| orcast artifact | `INTERACTIONS_GROUNDING_PATTERN.md`; `maps_grounding_probe.py` benchmark (85% Maps uncited baseline vs orcast) |

---

**SF-8 — Agent orchestration, plan-then-execute, tool verification**

| Field | Content |
|-------|---------|
| Section | 5 |
| Claim | Plan-then-execute architectures where the orchestrator selects tools deterministically from an allow-listed manifest (rather than letting the LLM choose tools freely) reduce tool hallucination and improve verifiability of outputs |
| Topic cluster | plan execute agent orchestration, tool selection hallucination, agentic workflow verification, skills manifest dispatch |
| **EM query 1** | "plan execute LLM agent tool selection hallucination deterministic" |
| **EM query 2** | "orchestrator managed subagent parallel lane verification skill dispatch" |
| **EM query 3** | "tool use allow-list manifest safety agent LLM" |
| **EM query 4** | "ReAct plan act verify agent workflow grounding" |
| **EM query 5** | "agent orchestration step log audit trail reproducibility verification" |
| Verification target | Paper demonstrating reduced error or hallucination when tool invocation is constrained to an explicit manifest vs free LLM tool-calling |
| Status | Not yet run |
| orcast artifact | `SKILL_CATALOG.md` tiers; `MANAGED_AGENTS_CONTRACT.md` policy; `skills_manifest.json`; tier_blocked 400 |

---

**SF-9 — Data provenance, lineage, reproducibility, audit trails**

| Field | Content |
|-------|---------|
| Section | 4 |
| Claim | Persisting an ordered step log (resolve_agent, skill_invocation, model_output) per interaction as a machine-readable JSONB record is sufficient to reconstruct the provenance chain from a displayed metric to its source data |
| Topic cluster | data provenance lineage scientific reproducibility, interaction step log audit trail, JSONB provenance trace |
| **EM query 1** | "data provenance lineage reproducibility scientific workflow audit trail" |
| **EM query 2** | "interaction step log machine readable provenance claim tracing" |
| **EM query 3** | "knowledge graph provenance scientific data artifact origin" |
| **EM query 4** | "FAIR data principles provenance metadata reproducibility" |
| **EM query 5** | "claim method experiment data graph scientific provenance visualization" |
| Verification target | Paper establishing step-log or trace-based provenance as sufficient for scientific reproducibility in a computational or AI workflow |
| Status | Not yet run |
| orcast artifact | `INTERACTIONS_GROUNDING_PATTERN.md` step schema; `exploration_turns` `interaction_steps JSONB`; `PROVENANCE_GRAPH_CONTRACT.md` |

---

**SF-10 — Human-in-the-loop moderation and promotion authority**

| Field | Content |
|-------|---------|
| Section | 6 |
| Claim | Citizen-science data entered into a probabilistic model without quarantine and human review authority produces systematic confidence overestimates; a signed promotion step is a necessary governance condition |
| Topic cluster | citizen science data quality moderation, human in the loop machine learning governance, crowdsourced data quality control |
| **EM query 1** | "citizen science data quality control machine learning integration governance" |
| **EM query 2** | "human in the loop moderation approval crowdsourced label quality" |
| **EM query 3** | "wildlife observation citizen science bias verification expert review" |
| **EM query 4** | "community science data quarantine moderation queue attribution reliability" |
| **EM query 5** | "human authority AI decision promotion immutable audit record" |
| Verification target | Paper quantifying data quality degradation or model error increase when unmoderated crowdsourced data enters a probabilistic model without review |
| Status | Not yet run |
| orcast artifact | `community-submissions` DynamoDB table; `/moderation`; `decision-records` table; `WHITEPAPER_HYPOTHESIS.md` corollary 3 |

---

**SF-11 — Geospatial grounding limits for scientific evidence (pre-verified)**

| Field | Content |
|-------|---------|
| Section | 7 |
| Claim | Google Maps grounding (Gemini Interactions API, google_maps tool) is effective for POI/logistics grounding (34.9 citations/1k words, 0% uncited) but resolves 0% of scientific or dataset citations and leaves 85% of scientific claims in evidence-type queries uncited |
| Topic cluster | geospatial grounding LLM scientific evidence, maps grounding vs scientific citation, place citation vs dataset citation |
| **EM query 1** | "LLM geospatial grounding scientific evidence accuracy citation quality" |
| **EM query 2** | "Google Maps grounding Gemini API place citation scientific claim limitation" |
| **EM query 3** | "knowledge grounding domain specific vs general purpose tool LLM" |
| **EM query 4** | "citation type evaluation LLM grounding place vs scientific dataset" |
| **EM query 5** | "grounding with maps vs RAG scientific evidence coverage accuracy" |
| Verification target | **Pre-verified by live benchmark** (2026-06-24, Gemini 3.5 Flash, `Api-Revision: 2026-05-20`, San Juan coords). EM search supplemental only to find related academic critiques of geospatial tool grounding |
| Status | Pre-verified (see PROVENANCE_GRAPH_CONTRACT.md) |
| orcast artifact | `tools/testing/maps_grounding_probe.py`; `docs/devpost/figures/_demo-run/maps-grounding-baseline.json` (written by `--write-baseline`) |

---

**SF-12 — Claim/method/experiment knowledge graphs (Emergent Mind, GraphiMind, MindSearch)**

| Field | Content |
|-------|---------|
| Section | 4 |
| Claim | Claim/method/experiment graph architectures (C -> M -> X -> Data) over interaction step logs enable inline citation binding at the claim span level, equivalent to the GraphiMind and MindSearch literature approaches for scientific paper knowledge graphs |
| Topic cluster | GraphiMind knowledge graph scientific paper, MindSearch multi-agent search, claim method experiment graph, knowledge graph interactive novelty |
| **EM query 1** | "GraphiMind scientific paper knowledge graph claim method experiment novelty" |
| **EM query 2** | "MindSearch multi-agent query decomposition knowledge graph construction" |
| **EM query 3** | "knowledge graph claim citation binding interactive grounding interface" |
| **EM query 4** | "claim method experiment directed graph scientific provenance visualization" |
| **EM query 5** | "supporting contrasting background citation edge scientific knowledge graph" |
| Verification target | Paper describing a C/M/X or equivalent graph schema for scientific provenance, or a system that binds text-span citations to structured knowledge nodes |
| Status | Not yet run |
| orcast artifact | `PROVENANCE_GRAPH_CONTRACT.md` node schema and edge types; `ProvenanceGraph.tsx` (this deploy) |

---

---

**SF-13 — RAG quality measurement for structured reasoning systems**

| Field | Content |
|-------|---------|
| Section | 4 (new: Benchmark methodology) |
| Claim | Not all RAG context reduces $R_\text{uncited}$; structured step-log reasoning traces achieve 0% where unstructured data injection does not |
| Topic cluster | RAG evaluation, retrieval quality, grounding measurement, step-log injection |
| **EM query 1** | "RAG context quality measurement grounding evaluation metric" |
| **EM query 2** | "structured vs unstructured retrieval augmented generation citation accuracy" |
| **EM query 3** | "step log trace injection LLM grounding factual accuracy" |
| **EM query 4** | "reasoning chain injection evidence binding claim accuracy measurement" |
| **EM query 5** | "retrieval quality diagnostic hierarchy grounding architecture evaluation" |
| Verification target | Paper measuring differential effect of RAG context type on unsupported claim rate |
| Status | Not yet run |
| orcast artifact | `tools/testing/grounding_parallel_rag.py`; `docs/figures/mp-benchmark-results.json` |

---

**SF-14 — Step-log evaluation and world model reasoning traces (done)**

| Field | Content |
|-------|---------|
| Section | 5 (new: Extension to world models) |
| Claim | A world model planning step-log functions as a structured evidence trace; injecting it as grounding context eliminates uncited claims in planning-type queries |
| Topic cluster | World model evaluation, planning trace verification, JEPA evaluation, intermediate representation grounding |
| **EM query 1** | "world model evaluation intermediate representation grounding evidence binding" |
| **EM query 2** | "JEPA joint embedding predictive architecture evaluation framework 2025 2026" |
| **EM query 3** | "planning step log intermediate output verification grounding quality" |
| **EM query 4** | "LeCun world model evaluation benchmark physical world reasoning 2026" |
| **EM query 5** | "AI agent reasoning chain traceability evidence citation intermediate steps" |
| Verification target | Paper proposing or applying evaluation frameworks for world model intermediate outputs |
| Status | Not yet run |
| orcast artifact | `tools/testing/grounding_parallel_rag.py` Scenario 4; `INTERACTIONS_GROUNDING_PATTERN.md` |

---

**SF-15 — LeCun AMI position paper and the evidence-binding evaluation gap**

| Field | Content |
|-------|---------|
| Section | 6 (WP2 World model extension) |
| Claim | LeCun's world model architecture requires evidence-grounded intermediate representations as a design property; no claim-level metric exists prior to $R_\text{uncited}$ |
| Status | **Done — Supported (gap confirmed)** |
| Verdict | AMI architecture (2306.02572), V-JEPA (2404.08471), IWM (2403.00504) all confirm the design requirement without proposing a measurement |
| orcast artifact | `docs/whitepaper2/LX/Sections/06_world_model_extension.tex` |

---

**SF-16 — Physical world evaluation benchmarks for planning AI systems**

| Field | Content |
|-------|---------|
| Section | 7 (WP2 Limits) |
| Claim | Existing physical-world AI benchmarks measure task completion, not intermediate evidence binding |
| Status | **Done — Supported (gap confirmed)** |
| Verdict | PHYRE, STAR, ThreeDWorld, TravelPlanner, embodied AI survey: all task-completion metrics, no evidence binding measurement |
| orcast artifact | `docs/whitepaper2/LX/Sections/07_limits.tex` |

---

## Status summary

| Family | Section | Status | Verdict |
|--------|---------|--------|---------|
| SF-1 Effort bias | 1 | Done | Partial |
| SF-2 Acoustic QC | 3 | Done | Supported |
| SF-3 Negative binomial | 2 | Done | Supported |
| SF-4 Null gating | 2 | Done | Partial |
| SF-5 CV skill | 2, 8 | Done | Supported |
| SF-6 Uncertainty communication | 1, 8 | Done | Supported |
| SF-7 LLM grounding / citation | 4 | Done | Supported |
| SF-8 Agent orchestration | 5 | Done | Supported |
| SF-9 Data provenance | 4 | Done | Supported |
| SF-10 Human-in-the-loop | 6 | Done | Supported |
| SF-11 Geospatial grounding limits | 7 | Done | Supported (live benchmark) |
| SF-12 Claim/method/experiment graphs | 4 | Done | Supported |
| SF-13 RAG quality measurement | 4 | Done | Supported |
| SF-14 Step-log / world model eval | 5 | Done | Partial (gap confirmed as novel) |
| SF-15 LeCun AMI primary source | 6 | Done | Supported (gap confirmed) |
| SF-16 Physical-world eval benchmarks | 7 | Done | Supported (gap confirmed) |
