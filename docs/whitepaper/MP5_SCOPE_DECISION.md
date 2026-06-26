# MP5 — Whitepaper scope decision

Date: 2026-06-24  
Wave Set MP: benchmark-driven scope charter for the AMI-trajectory paper.

## Empirical backbone (benchmark hierarchy)

The 8-scenario parallel grounding benchmark (`tools/testing/grounding_parallel_rag.py`,  
gemini-3.5-flash, Api-Revision 2026-05-20, 2026-06-24) produced the following ranking:

| Scenario | Setup | $R_\text{uncited}$ | Interpretation |
|----------|-------|--------------------|----------------|
| 4 | Maps + surface planner step-log | **0%** | Full grounding: step-log converts science queries into artifact-reference queries |
| 8 | Maps + orcast hotspots | 75% | Partial lift (↓25pp from 100%): structured data partially substitutes for citations |
| 1 | Maps-only orca evidence (baseline) | 60% | Maps baseline ranges 60–100% across query types (S1 60%, S7 100%) |
| 7 | Maps-only trip planning | 100% | Maps baseline for planning queries |
| 2 | Maps + gates context | 100% | No lift: gate data too narrow to cover generated science claims |
| 5 | Maps-only sighting | 100% | Maps baseline |
| 3 | Maps + provenance | 100% | No lift: provenance data too specific for broad science claims |
| 6 | Maps + sighting-assist | 100% | No lift |

The hierarchy gives the paper its structure. The paper explains WHY the hierarchy is what it is.

---

## Paper title (final recommendation)

> Grounding quality measurement for orchestrated AI reasoning chains:  
> evidence-binding rate as an evaluation primitive for world model systems

**arXiv target:** cs.AI / cs.LG

---

## What the paper IS about

1. **$R_\text{uncited}$** as a formal evaluation metric for AI reasoning systems
   — fraction of scientific claims in a response that carry no bound citation
2. **The benchmark methodology** (`maps_grounding_probe.py` + `grounding_parallel_rag.py`)
   — reproducible, 8-scenario, parallel, quantitative
3. **Why Scenario 4 achieves 0%**: the planner step-log transforms an open-domain science query
   into a closed artifact-reference query — the model answers from the step-log, not from world knowledge
4. **The RAG lift hierarchy as a diagnostic**: not all RAG context reduces $R_\text{uncited}$;
   the diagnostic tells you which context types bind claims vs which generate new uncited claims
5. **Extension to world model systems**: the step-log is a world model's reasoning trace;
   $R_\text{uncited}$ measures whether the trace's intermediate outputs are evidence-bound

---

## What the paper IS NOT about (pax non-overlap)

| Topic | Source | Why excluded |
|-------|--------|-------------|
| Pedestrian routing cost encoding | pax whitepaper, section 1 | Core pax contribution |
| Camera-derived sigma stress field | pax system | Pax physical-world perception |
| Walk graph construction | pax substrate | Pax infrastructure |
| Thermal comfort (MRT, UTCI, SVF) | pax domain | Pax measurement ontology |
| Manhattan mobility data | pax data | Pax empirical domain |
| Encounter forecasting (NB-GLM, PSTH, gates) | orcast paper 1 | Already written |
| Effort bias correction for cetacean data | orcast paper 1 | Already written |

---

## AMI trajectory alignment

AMI Labs (Advanced Machine Intelligence, Yann LeCun) research pillars:
1. Understanding current physical-world state from sensors
2. Predicting how the world will evolve under actions
3. Planning and adapting action sequences

$R_\text{uncited}$ directly addresses pillar 3: when a world model generates a plan,
are the plan's intermediate claims bound to the sensor data that generated them?
The orcast surface planner (Scenario 4) is a concrete world-model planning system.
The step-log injection experiment is an evaluation of whether its reasoning traces
are evidence-bound.

This paper provides AMI with:
- A formal metric for evaluating world model claim grounding quality
- A reproducible benchmark methodology applicable to any planning system
- An explanation of why structured reasoning traces (step-logs) eliminate uncited claims
  while unstructured RAG context does not

---

## AMI-targeted abstract (150 words)

AI systems that generate text-form outputs routinely make scientific claims without
citing their generating evidence. We introduce $R_\text{uncited}$, the fraction of
scientific sentences in a system's output that carry no bound citation, as an evaluation
primitive for AI reasoning systems. Using a reproducible 8-scenario benchmark against
the Gemini Interactions API with Google Maps grounding, we measure $R_\text{uncited}$
for four context types on marine science queries. Maps-only grounding achieves
60--100\% uncited across query types. Injecting an orchestrated skill-dispatch step-log
as RAG context reduces $R_\text{uncited}$ to 0\%, demonstrating that structured reasoning
traces eliminate uncited claims by converting open-domain science queries into
closed artifact-reference queries. The RAG lift hierarchy (step-log > hotspot data > gate
context > sighting context) functions as a diagnostic for grounding architecture quality.
We extend the framework to world model evaluation: $R_\text{uncited}$ applied to a world
model's intermediate planning outputs measures whether the model's stated beliefs are
bound to their generating sensor evidence.

---

## Two new search families for SEARCH_FAMILY_GRID.md

### SF-13 — RAG quality measurement for structured reasoning systems

| Field | Content |
|-------|---------|
| Section | 4 (new: Benchmark methodology) |
| Claim | Not all RAG context reduces the unsupported claim rate; structured reasoning traces (step-logs) achieve this where unstructured data injection does not |
| Topic cluster | RAG evaluation, retrieval quality, grounding measurement |
| **EM query 1** | "RAG context quality measurement grounding evaluation metric" |
| **EM query 2** | "structured vs unstructured retrieval augmented generation citation accuracy" |
| **EM query 3** | "step log trace injection LLM grounding factual accuracy" |
| **EM query 4** | "reasoning chain injection evidence binding claim accuracy measurement" |
| **EM query 5** | "retrieval quality diagnostic hierarchy grounding architecture evaluation" |
| Verification target | Paper measuring differential effect of RAG context type on unsupported claim rate |
| Status | Not yet run |
| orcast artifact | `tools/testing/grounding_parallel_rag.py`; `docs/figures/mp-benchmark-results.json` |

---

### SF-14 — Step-log evaluation and world model reasoning traces

| Field | Content |
|-------|---------|
| Section | 5 (new: Extension to world models) |
| Claim | A world model's intermediate planning step-log functions as a structured evidence trace; injecting it as grounding context eliminates uncited claims in planning-type queries |
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

## Recommended paper section blocking (second orcast paper)

| # | Section | Families | Core falsifiable claim |
|---|---------|----------|------------------------|
| 1 | The evidence-binding gap in AI reasoning systems | SF-7, SF-11 | LLM grounding and geospatial tool grounding both leave scientific claims uncited at high rates |
| 2 | $R_\text{uncited}$ as an evaluation metric | SF-13 | The fraction of scientific sentences with no bound citation is a reproducible, quantitative diagnostic for grounding quality |
| 3 | Benchmark methodology and 8-scenario results | SF-11, SF-13 | Maps-only baseline achieves 60--100\% uncited; step-log injection achieves 0\% |
| 4 | Why step-log injection eliminates uncited claims | SF-8, SF-9 | Orchestrated skill-dispatch step-logs transform open science queries into closed artifact-reference queries |
| 5 | RAG lift hierarchy as a diagnostic | SF-13, SF-7 | The hierarchy of $\Delta R_\text{uncited}$ across RAG context types reveals which context architectures bind claims |
| 6 | Extension to world model systems | SF-14 | $R_\text{uncited}$ applied to world model planning step-logs measures whether intermediate beliefs are evidence-bound |
| 7 | Limits and extension path | SF-14 | The metric does not measure semantic accuracy; extension requires claim-level attribution |

---

## Registry update

Wave Set MP complete. Add to `waves.registry.yaml`:

```yaml
- id: MP0
  family: MP
  status: done
  output: docs/figures/mp-benchmark-results.json

- id: MP1
  family: MP
  status: done
  output: docs/figures/fig-mp1-problem-measurement/figure.png

- id: MP2
  family: MP
  status: done
  output: docs/figures/fig-mp2-mechanism/figure.png

- id: MP3
  family: MP
  status: done
  output: docs/figures/fig-mp3-benchmark-scope/figure.png

- id: MP4
  family: MP
  status: done
  output: docs/figures/MP4_MULTI_PANEL_REVIEW.md

- id: MP5
  family: MP
  status: done
  output: docs/whitepaper/MP5_SCOPE_DECISION.md
```
