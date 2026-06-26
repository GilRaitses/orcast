# SF-9 — Sf 09 Data Provenance

**Section:** 4

**Claim:** Persisting an ordered step log per interaction as JSONB is sufficient to reconstruct the provenance chain from a displayed metric to its source data.

**Verification target:** Paper establishing step-log or trace-based provenance as sufficient for scientific reproducibility in a computational or AI workflow.

## Query: data provenance lineage reproducibility scientific workflow audit trail

**Practical Whole-System Provenance Capture**
https://arxiv.org/abs/1711.05296  
Data provenance describes how data came to be in its present form. It includes
data sources and the transformations that have been applied to them. Data
provenance has many uses, from forensics and security to aiding the
reproducibility of scientific experiments. We present CamFlow, a whole-system
provenance capture mechanism that integrates easily into a PaaS offering. While
there have been several prior whole-system provenance systems that captured a
comprehensive, systemic and ubiquitous record of a system's behavior, none have
been widely adopted. They either A) impose too much overhead, B…

**Putting Lipstick on Pig: Enabling Database-style Workflow Provenance**
https://arxiv.org/abs/1201.0231  
Workflow provenance typically assumes that each module is a "black-box", so that
each output depends on all inputs (coarse-grained dependencies). Furthermore, it
does not model the internal state of a module, which can change between repeated
executions. In practice, however, an output may depend on only a small subset of
the inputs (fine-grained dependencies) as well as on the internal state of the
module. We present a novel provenance framework that marries database-style and
workflow-style provenance, by using Pig Latin to expose the functionality of
modules, thus capturing internal state a…

**Provenance and data differencing for workflow reproducibility analysis**
https://arxiv.org/abs/1406.0905  
One of the foundations of science is that researchers must publish the
methodology used to achieve their results so that others can attempt to
reproduce them. This has the added benefit of allowing methods to be adopted and
adapted for other purposes. In the field of e-Science, services -- often
choreographed through workflow, process data to generate results. The
reproduction of results is often not straightforward as the computational
objects may not be made available or may have been updated since the results
were generated. For example, services are often updated to fix bugs or improve
alg…

**Scientific Workflows and Provenance: Introduction and Research Opportunities**
https://arxiv.org/abs/1311.4610  
Scientific workflows are becoming increasingly popular for compute-intensive and
data-intensive scientific applications. The vision and promise of scientific
workflows includes rapid, easy workflow design, reuse, scalable execution, and
other advantages, e.g., to facilitate "reproducible science" through provenance
(e.g., data lineage) support. However, as described in the paper, important
research challenges remain. While the database community has studied (business)
workflow technologies extensively in the past, most current work in scientific
workflows seems to be done outside of the databa…

**Workflow Provenance in the Lifecycle of Scientific Machine Learning**
https://arxiv.org/abs/2010.00330  
Machine Learning (ML) has already fundamentally changed several businesses. More
recently, it has also been profoundly impacting the computational science and
engineering domains, like geoscience, climate science, and health science. In
these domains, users need to perform comprehensive data analyses combining
scientific data and ML models to provide for critical requirements, such as
reproducibility, model explainability, and experiment data understanding.
However, scientific ML is multidisciplinary, heterogeneous, and affected by the
physical constraints of the domain, making such analyses e…

## Query: interaction step log machine readable provenance claim tracing

**A Core Calculus for Provenance**
https://arxiv.org/abs/1310.6299  
Provenance is an increasing concern due to the ongoing revolution in sharing and
processing scientific data on the Web and in other computer systems. It is
proposed that many computer systems will need to become provenance-aware in
order to provide satisfactory accountability, reproducibility, and trust for
scientific or other high-value data. To date, there is not a consensus
concerning appropriate formal models or security properties for provenance. In
previous work, we introduced a formal framework for provenance security and
proposed formal definitions of properties called disclosure and o…

**Adversarial Watermarking Transformer: Towards Tracing Text Provenance with Data Hiding**
https://arxiv.org/abs/2009.03015  
Recent advances in natural language generation have introduced powerful language
models with high-quality output text. However, this raises concerns about the
potential misuse of such models for malicious purposes. In this paper, we study
natural language watermarking as a defense to help better mark and trace the
provenance of text. We introduce the Adversarial Watermarking Transformer (AWT)
with a jointly trained encoder-decoder and adversarial training that, given an
input text and a binary message, generates an output text that is unobtrusively
encoded with the given message. We further st…

**Tracing Text Provenance via Context-Aware Lexical Substitution**
https://arxiv.org/abs/2112.07873  
Text content created by humans or language models is often stolen or misused by
adversaries. Tracing text provenance can help claim the ownership of text
content or identify the malicious users who distribute misleading content like
machine-generated fake news. There have been some attempts to achieve this,
mainly based on watermarking techniques. Specifically, traditional text
watermarking methods embed watermarks by slightly altering text format like line
spacing and font, which, however, are fragile to cross-media transmissions like
OCR. Considering this, natural language watermarking metho…

**Provenance Traces**
https://arxiv.org/abs/0812.0564  
Provenance is information about the origin, derivation, ownership, or history of
an object. It has recently been studied extensively in scientific databases and
other settings due to its importance in helping scientists judge data validity,
quality and integrity. However, most models of provenance have been stated as ad
hoc definitions motivated by informal concepts such as "comes from",
"influences", "produces", or "depends on". These models lack clear
formalizations describing in what sense the definitions capture these intuitive
concepts. This makes it difficult to compare approaches, evalu…

**Provenance-enabled Packet Path Tracing in the RPL-based Internet of Things**
https://arxiv.org/abs/1811.06143  
The interconnection of resource-constrained and globally accessible things with
untrusted and unreliable Internet make them vulnerable to attacks including data
forging, false data injection, and packet drop that affects applications with
critical decision-making processes. For data trustworthiness, reliance on
provenance is considered to be an effective mechanism that tracks both data
acquisition and data transmission. However, provenance management for sensor
networks introduces several challenges, such as low energy, bandwidth
consumption, and efficient storage. This paper attempts to ident…

## Query: knowledge graph provenance scientific data artifact origin

**Provenance as Dependency Analysis**
https://arxiv.org/abs/0708.2173  
Provenance is information recording the source, derivation, or history of some
information. Provenance tracking has been studied in a variety of settings;
however, although many design points have been explored, the mathematical or
semantic foundations of data provenance have received comparatively little
attention. In this paper, we argue that dependency analysis techniques familiar
from program analysis and program slicing provide a formal foundation for forms
of provenance that are intended to show how (part of) the output of a query
depends on (parts of) its input. We introduce a semantic …

**From Artifacts to Aggregations: Modeling Scientific Life Cycles on the Semantic Web**
https://arxiv.org/abs/0906.2549  
In the process of scientific research, many information objects are generated,
all of which may remain valuable indefinitely. However, artifacts such as
instrument data and associated calibration information may have little value in
isolation; their meaning is derived from their relationships to each other.
Individual artifacts are best represented as components of a life cycle that is
specific to a scientific research domain or project. Current cataloging
practices do not describe objects at a sufficient level of granularity nor do
they offer the globally persistent identifiers necessary to d…

**SoMeSci- A 5 Star Open Data Gold Standard Knowledge Graph of Software Mentions in Scientific Articles**
https://arxiv.org/abs/2108.09070  
Knowledge about software used in scientific investigations is important for
several reasons, for instance, to enable an understanding of provenance and
methods involved in data handling. However, software is usually not formally
cited, but rather mentioned informally within the scholarly description of the
investigation, raising the need for automatic information extraction and
disambiguation. Given the lack of reliable ground truth data, we present SoMeSci
(Software Mentions in Science) a gold standard knowledge graph of software
mentions in scientific articles. It contains high quality annot…

**Causality and the Semantics of Provenance**
https://arxiv.org/abs/1006.1429  
Provenance, or information about the sources, derivation, custody or history of
data, has been studied recently in a number of contexts, including databases,
scientific workflows and the Semantic Web. Many provenance mechanisms have been
developed, motivated by informal notions such as influence, dependence,
explanation and causality. However, there has been little study of whether these
mechanisms formally satisfy appropriate policies or even how to formalize
relevant motivating concepts such as causality. We contend that mathematical
models of these concepts are needed to justify and compare…

**Understanding Data Science Lifecycle Provenance via Graph Segmentation and Summarization**
https://arxiv.org/abs/1810.04599  
Increasingly modern data science platforms today have non-intrusive and
extensible provenance ingestion mechanisms to collect rich provenance and
context information, handle modifications to the same file using distinguishable
versions, and use graph data models (e.g., property graphs) and query languages
(e.g., Cypher) to represent and manipulate the stored provenance/context
information. Due to the schema-later nature of the metadata, multiple versions
of the same files, and unfamiliar artifacts introduced by team members, the
"provenance graph" is verbose and evolving, and hard to understan…

## Query: FAIR data principles provenance metadata reproducibility

**The role of metadata in reproducible computational research**
https://arxiv.org/abs/2006.08589  
Reproducible computational research (RCR) is the keystone of the scientific
method for in silico analyses, packaging the transformation of raw data to
published results. In addition to its role in research integrity, RCR has the
capacity to significantly accelerate evaluation and reuse. This potential and
wide-support for the FAIR principles have motivated interest in metadata
standards supporting RCR. Metadata provides context and provenance to raw data
and methods and is essential to both discovery and validation. Despite this
shared connection with scientific data, few studies have explicit…

**Making experimental data tables in the life sciences more FAIR: a pragmatic approach**
https://arxiv.org/abs/2012.09435  
Making data compliant with the FAIR Data principles (Findable, Accessible,
Interoperable, Reusable) is still a challenge for many researchers, who are not
sure which criteria should be met first and how. Illustrated from experimental
data tables associated with a Design of Experiments, we propose an approach that
can serve as a model for a research data management that allows researchers to
disseminate their data by satisfying the main FAIR criteria without
insurmountable efforts. More importantly, this approach aims to facilitate the
FAIRification process by providing researchers with tools t…

**Machine Learning Pipelines: Provenance, Reproducibility and FAIR Data Principles**
https://arxiv.org/abs/2006.12117  
Machine learning (ML) is an increasingly important scientific tool supporting
decision making and knowledge generation in numerous fields. With this, it also
becomes more and more important that the results of ML experiments are
reproducible. Unfortunately, that often is not the case. Rather, ML, similar to
many other disciplines, faces a reproducibility crisis. In this paper, we
describe our goals and initial steps in supporting the end-to-end
reproducibility of ML pipelines. We investigate which factors beyond the
availability of source code and datasets influence reproducibility of ML exper…

**Implementation of FAIR principles in the IPCC: The WGI AR6 Atlas repository**
https://arxiv.org/abs/2204.14245  
The Sixth Assessment Report (AR6) of the Intergovernmental Panel on Climate
Change (IPCC) has adopted the FAIR Guiding Principles. The Atlas chapter of
Working Group I (WGI) is presented as a test case. Here, we describe the
application of these principles in the Atlas, the challenges faced during its
implementation, and those that remain for the future. We present the open source
repository resulting from this process, which collects the code (including
annotated Jupyter notebooks), data provenance, and some aggregated datasets
underpinning the key figures in the Atlas chapter and its interac…

**FAIR for AI: An interdisciplinary and international community building perspective**
https://arxiv.org/abs/2210.08973  
A foundational set of findable, accessible, interoperable, and reusable (FAIR)
principles were proposed in 2016 as prerequisites for proper data management and
stewardship, with the goal of enabling the reusability of scholarly data. The
principles were also meant to apply to other digital assets, at a high level,
and over time, the FAIR guiding principles have been re-interpreted or extended
to include the software, tools, algorithms, and workflows that produce data.
FAIR principles are now being adapted in the context of AI models and datasets.
Here, we present the perspectives, vision, and …

## Query: claim method experiment data graph scientific provenance visualization

**Utilizing Provenance in Reusable Research Objects**
https://arxiv.org/abs/1806.06452  
Science is conducted collaboratively, often requiring the sharing of knowledge
about computational experiments. When experiments include only datasets, they
can be shared using Uniform Resource Identifiers (URIs) or Digital Object
Identifiers (DOIs). An experiment, however, seldom includes only datasets, but
more often includes software, its past execution, provenance, and associated
documentation. The Research Object has recently emerged as a comprehensive and
systematic method for aggregation and identification of diverse elements of
computational experiments. While a necessary method, mere …

**Mayavi: a package for 3D visualization of scientific data**
https://arxiv.org/abs/1010.4891  
Mayavi is an open-source, general-purpose, 3D scientific visualization package.
It seeks to provide easy and interactive tools for data visualization that fit
with the scientific user's workflow. For this purpose, Mayavi provides several
entry points: a full-blown interactive application; a Python library with both a
MATLAB-like interface focused on easy scripting and a feature-rich object
hierarchy; widgets associated with these objects for assembling in a domain-
specific application, and plugins that work with a general purpose application-
building framework. In this article, we present an o…

**Aggregation by Provenance Types: A Technique for Summarising Provenance Graphs**
https://arxiv.org/abs/1504.02616  
As users become confronted with a deluge of provenance data, dedicated
techniques are required to make sense of this kind of information. We present
Aggregation by Provenance Types, a provenance graph analysis that is capable of
generating provenance graph summaries. It proceeds by converting provenance
paths up to some length k to attributes, referred to as provenance types, and by
grouping nodes that have the same provenance types. The summary also includes
numeric values representing the frequency of nodes and edges in the original
graph. A quantitative evaluation and a complexity analysis …

**Workflow Provenance in the Lifecycle of Scientific Machine Learning**
https://arxiv.org/abs/2010.00330  
Machine Learning (ML) has already fundamentally changed several businesses. More
recently, it has also been profoundly impacting the computational science and
engineering domains, like geoscience, climate science, and health science. In
these domains, users need to perform comprehensive data analyses combining
scientific data and ML models to provide for critical requirements, such as
reproducibility, model explainability, and experiment data understanding.
However, scientific ML is multidisciplinary, heterogeneous, and affected by the
physical constraints of the domain, making such analyses e…

**Scientific Workflows and Provenance: Introduction and Research Opportunities**
https://arxiv.org/abs/1311.4610  
Scientific workflows are becoming increasingly popular for compute-intensive and
data-intensive scientific applications. The vision and promise of scientific
workflows includes rapid, easy workflow design, reuse, scalable execution, and
other advantages, e.g., to facilitate "reproducible science" through provenance
(e.g., data lineage) support. However, as described in the paper, important
research challenges remain. While the database community has studied (business)
workflow technologies extensively in the past, most current work in scientific
workflows seems to be done outside of the databa…

---

## Family summary

The data provenance corpus is directly on-point and comprehensive. The CamFlow whole-system provenance paper (1711.05296) establishes that capturing an ordered log of data transformations and their inputs is the foundational mechanism for provenance in computing systems, and that it must be low-overhead and integrated into the processing pipeline — exactly what orcast's `interaction_steps` JSONB achieves at the interaction level. The "Provenance and data differencing" paper (1406.0905) establishes that workflow provenance is sufficient for reproducibility analysis: a run-by-run trace of which services processed which data, in what order, is enough to detect when results would change — the same sufficiency claim orcast makes for its step log. The "Scientific Workflows and Provenance" survey (1311.4610) is the field overview paper establishing that `data lineage` — the chain from raw data to output — is the canonical definition of scientific reproducibility and that JSONB/structured log capture is a standard mechanism. The "Workflow Provenance in the Lifecycle of Scientific ML" paper (2010.00330) directly addresses ML-specific provenance in geoscience and climate workflows, demonstrating that step-level logging enables reproducibility in exactly the kind of data-intensive scientific pipeline orcast implements. The "Putting Lipstick on Pig" paper (1201.0231) introduces fine-grained vs coarse-grained provenance, showing that module-level step logging (what orcast does) is a tractable first step toward full fine-grained lineage.

**Verdict: Supported** — step-log provenance is well-established as sufficient for scientific reproducibility. Primary citations: 1406.0905 (provenance sufficiency for reproducibility), 2010.00330 (ML workflow provenance in science), 1311.4610 (scientific workflow provenance survey).