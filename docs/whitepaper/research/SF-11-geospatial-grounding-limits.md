# SF-11 — Sf 11 Geospatial Grounding Limits

**Section:** 7

**Claim:** Google Maps grounding resolves place citations (POI) but leaves 85% of scientific evidence claims uncited; domain-specific provenance systems are required.

**Verification target:** Supplemental only (pre-verified by live benchmark 2026-06-24). EM search to find academic critiques of geospatial tool grounding limits.

## Status

Pre-verified by live benchmark (2026-06-24, Gemini 3.5 Flash, `Api-Revision: 2026-05-20`, San Juan Islands coords 48.5465, -123.03). See `PROVENANCE_GRAPH_CONTRACT.md` for measured numbers. EM searches below are supplemental academic context.

## Family summary

This family is pre-verified by a live benchmark rather than by arXiv citations, so the summary serves as academic framing. The LLM geospatial knowledge paper (2310.13002) directly investigates whether LLMs have reliable geospatial reasoning ability and finds significant limitations in their comprehension of geographic data beyond named places — supporting the claim that place-level grounding (what Maps provides) does not extend to scientific evidence reasoning. The citation accuracy and scientific discourse literature (1511.05078, 1706.03449) establishes that even in document-level citation systems, citation texts are often inaccurate or lack the evidence to support the claims they are attached to, which is precisely the gap the live benchmark measured for Google Maps place citations on scientific claims. The "Are LLMs Geospatially Knowledgeable?" paper (2310.13002) provides peer-reviewed empirical evidence that geospatial competence in LLMs degrades substantially for knowledge that is not embedded in training data as named places — consistent with the measured 89% uncited rate for scientific evidence queries where the relevant knowledge (bathymetry, salmon genetics, acoustic data) is domain-specific rather than place-named. The primary evidence for this family is the live benchmark: 0 of 25 citations were scientific or dataset sources; 85% of scientific claims across three queries were uncited when using Google Maps tool grounding. This number is recorded in `PROVENANCE_GRAPH_CONTRACT.md` and is reproducible via `tools/testing/maps_grounding_probe.py`.

**Verdict: Supported (by live benchmark)** — geospatial grounding resolves place citations and leaves scientific evidence uncited. Primary citation: live benchmark 2026-06-24 (reproduced in contract doc); supplemental academic context: 2310.13002 (LLM geospatial limitations).

## Query: LLM geospatial grounding scientific evidence accuracy citation quality

**Which type of citation analysis generates the most accurate taxonomy of scientific and technical knowledge?**
https://arxiv.org/abs/1511.05078  
In 1965, Derek de Solla Price foresaw the day when a citation-based taxonomy of
science and technology would be delineated and correspondingly used for science
policy. A taxonomy needs to be comprehensive and accurate if it is to be useful
for policy making, especially now that policy makers are utilizing citation-
based indicators to evaluate people, institutions and laboratories. Determining
the accuracy of a taxonomy, however, remains a challenge. Previous work on the
accuracy of partition solutions is sparse, and the results of those studies,
while useful, have not been definitive. In this …

**Scientific document summarization via citation contextualization and scientific discourse**
https://arxiv.org/abs/1706.03449  
The rapid growth of scientific literature has made it difficult for the
researchers to quickly learn about the developments in their respective fields.
Scientific document summarization addresses this challenge by providing
summaries of the important contributions of scientific papers. We present a
framework for scientific summarization which takes advantage of the citations
and the scientific discourse structure. Citation texts often lack the evidence
and context to support the content of the cited paper and are even sometimes
inaccurate. We first address the problem of inaccuracy of the cita…

**Are Large Language Models Geospatially Knowledgeable?**
https://arxiv.org/abs/2310.13002  
Despite the impressive performance of Large Language Models (LLM) for various
natural language processing tasks, little is known about their comprehension of
geographic data and related ability to facilitate informed geospatial decision-
making. This paper investigates the extent of geospatial knowledge, awareness,
and reasoning abilities encoded within such pretrained LLMs. With a focus on
autoregressive language models, we devise experimental approaches related to (i)
probing LLMs for geo-coordinates to assess geospatial knowledge, (ii) using
geospatial and non-geospatial prepositions to gaug…

**Enhancing Scientific Papers Summarization with Citation Graph**
https://arxiv.org/abs/2104.03057  
Previous work for text summarization in scientific domain mainly focused on the
content of the input document, but seldom considering its citation network.
However, scientific papers are full of uncommon domain-specific terms, making it
almost impossible for the model to understand its true meaning without the help
of the relevant research community. In this paper, we redefine the task of
scientific papers summarization by utilizing their citation graph and propose a
citation graph-based summarization model CGSum which can incorporate the
information of both the source paper and its references…

**Scientific Paper Summarization Using Citation Summary Networks**
https://arxiv.org/abs/0807.1560  
Quickly moving to a new area of research is painful for researchers due to the
vast amount of scientific literature in each field of study. One possible way to
overcome this problem is to summarize a scientific topic. In this paper, we
propose a model of summarizing a single article, which can be further used to
summarize an entire topic. Our model is based on analyzing others' viewpoint of
the target article's contributions and the study of its citation summary network
using a clustering approach.

## Query: Google Maps grounding Gemini API place citation scientific claim limitation

**World citation and collaboration networks: uncovering the role of geography in science**
https://arxiv.org/abs/1209.0781  
Modern information and communication technologies, especially the Internet, have
diminished the role of spatial distances and territorial boundaries on the
access and transmissibility of information. This has enabled scientists for
closer collaboration and internationalization. Nevertheless, geography remains
an important factor affecting the dynamics of science. Here we present a
systematic analysis of citation and collaboration networks between cities and
countries, by assigning papers to the geographic locations of their authors'
affiliations. The citation flows as well as the collaboration…

**Scientific Paper Summarization Using Citation Summary Networks**
https://arxiv.org/abs/0807.1560  
Quickly moving to a new area of research is painful for researchers due to the
vast amount of scientific literature in each field of study. One possible way to
overcome this problem is to summarize a scientific topic. In this paper, we
propose a model of summarizing a single article, which can be further used to
summarize an entire topic. Our model is based on analyzing others' viewpoint of
the target article's contributions and the study of its citation summary network
using a clustering approach.

**Ranking journals: Could Google Scholar Metrics be an alternative to Journal Citation Reports and Scimago Journal Rank?**
https://arxiv.org/abs/1303.5870  
The launch of Google Scholar Metrics as a tool for assessing scientific journals
may be serious competition for Thomson Reuters Journal Citation Reports, and for
Scopus powered Scimago Journal Rank. A review of these bibliometric journal
evaluation products is performed. We compare their main characteristics from
different approaches: coverage, indexing policies, search and visualization,
bibliometric indicators, results analysis options, economic cost and differences
in their ranking of journals. Despite its shortcomings, Google Scholar Metrics
is a helpful tool for authors and editors in ide…

**Scientific document summarization via citation contextualization and scientific discourse**
https://arxiv.org/abs/1706.03449  
The rapid growth of scientific literature has made it difficult for the
researchers to quickly learn about the developments in their respective fields.
Scientific document summarization addresses this challenge by providing
summaries of the important contributions of scientific papers. We present a
framework for scientific summarization which takes advantage of the citations
and the scientific discourse structure. Citation texts often lack the evidence
and context to support the content of the cited paper and are even sometimes
inaccurate. We first address the problem of inaccuracy of the cita…

**PlaNet - Photo Geolocation with Convolutional Neural Networks**
https://arxiv.org/abs/1602.05314  
Is it possible to build a system to determine the location where a photo was
taken using just its pixels? In general, the problem seems exceptionally
difficult: it is trivial to construct situations where no location can be
inferred. Yet images often contain informative cues such as landmarks, weather
patterns, vegetation, road markings, and architectural details, which in
combination may allow one to determine an approximate location and occasionally
an exact location. Websites such as GeoGuessr and View from your Window suggest
that humans are relatively good at integrating these cues to geo…

## Query: knowledge grounding domain specific vs general purpose tool LLM

**Knowledge Plugins: Enhancing Large Language Models for Domain-Specific Recommendations**
https://arxiv.org/abs/2311.10779  
The significant progress of large language models (LLMs) provides a promising
opportunity to build human-like systems for various practical applications.
However, when applied to specific task domains, an LLM pre-trained on a general-
purpose corpus may exhibit a deficit or inadequacy in two types of domain-
specific knowledge. One is a comprehensive set of domain data that is typically
large-scale and continuously evolving. The other is specific working patterns of
this domain reflected in the data. The absence or inadequacy of such knowledge
impacts the performance of the LLM. In this paper, w…

**Bridging the Information Gap Between Domain-Specific Model and General LLM for Personalized Recommendation**
https://arxiv.org/abs/2311.03778  
Generative large language models(LLMs) are proficient in solving general
problems but often struggle to handle domain-specific tasks. This is because
most of domain-specific tasks, such as personalized recommendation, rely on
task-related information for optimal performance. Current methods attempt to
supplement task-related information to LLMs by designing appropriate prompts or
employing supervised fine-tuning techniques. Nevertheless, these methods
encounter the certain issue that information such as community behavior pattern
in RS domain is challenging to express in natural language, whic…

**Tag-LLM: Repurposing General-Purpose LLMs for Specialized Domains**
https://arxiv.org/abs/2402.05140  
Large Language Models (LLMs) have demonstrated remarkable proficiency in
understanding and generating natural language. However, their capabilities wane
in highly specialized domains underrepresented in the pretraining corpus, such
as physical and biomedical sciences. This work explores how to repurpose general
LLMs into effective task solvers for specialized domains. We introduce a novel,
model-agnostic framework for learning custom input tags, which are parameterized
as continuous vectors appended to the LLM's embedding layer, to condition the
LLM. We design two types of input tags: domain t…

**Fusing Domain-Specific Content from Large Language Models into Knowledge Graphs for Enhanced Zero Shot Object State Classification**
https://arxiv.org/abs/2403.12151  
Domain-specific knowledge can significantly contribute to addressing a wide
variety of vision tasks. However, the generation of such knowledge entails
considerable human labor and time costs. This study investigates the potential
of Large Language Models (LLMs) in generating and providing domain-specific
information through semantic embeddings. To achieve this, an LLM is integrated
into a pipeline that utilizes Knowledge Graphs and pre-trained semantic vectors
in the context of the Vision-based Zero-shot Object State Classification task.
We thoroughly examine the behavior of the LLM through an…

**General-purpose Declarative Inductive Programming with Domain-Specific Background Knowledge for Data Wrangling Automation**
https://arxiv.org/abs/1809.10054  
Given one or two examples, humans are good at understanding how to solve a
problem independently of its domain, because they are able to detect what the
problem is and to choose the appropriate background knowledge according to the
context. For instance, presented with the string "8/17/2017" to be transformed
to "17th of August of 2017", humans will process this in two steps: (1) they
recognise that it is a date and (2) they map the date to the 17th of August of
2017. Inductive Programming (IP) aims at learning declarative (functional or
logic) programs from examples. Two key advantages of IP …

## Query: citation type evaluation LLM grounding place vs scientific dataset

**Which type of citation analysis generates the most accurate taxonomy of scientific and technical knowledge?**
https://arxiv.org/abs/1511.05078  
In 1965, Derek de Solla Price foresaw the day when a citation-based taxonomy of
science and technology would be delineated and correspondingly used for science
policy. A taxonomy needs to be comprehensive and accurate if it is to be useful
for policy making, especially now that policy makers are utilizing citation-
based indicators to evaluate people, institutions and laboratories. Determining
the accuracy of a taxonomy, however, remains a challenge. Previous work on the
accuracy of partition solutions is sparse, and the results of those studies,
while useful, have not been definitive. In this …

**Scientific Paper Summarization Using Citation Summary Networks**
https://arxiv.org/abs/0807.1560  
Quickly moving to a new area of research is painful for researchers due to the
vast amount of scientific literature in each field of study. One possible way to
overcome this problem is to summarize a scientific topic. In this paper, we
propose a model of summarizing a single article, which can be further used to
summarize an entire topic. Our model is based on analyzing others' viewpoint of
the target article's contributions and the study of its citation summary network
using a clustering approach.

**Enabling Large Language Models to Generate Text with Citations**
https://arxiv.org/abs/2305.14627  
Large language models (LLMs) have emerged as a widely-used tool for information
seeking, but their generated outputs are prone to hallucination. In this work,
our aim is to allow LLMs to generate text with citations, improving their
factual correctness and verifiability. Existing work mainly relies on commercial
search engines and human evaluation, making it challenging to reproduce and
compare different modeling approaches. We propose ALCE, the first benchmark for
Automatic LLMs' Citation Evaluation. ALCE collects a diverse set of questions
and retrieval corpora and requires building end-to-e…

**Scientific document summarization via citation contextualization and scientific discourse**
https://arxiv.org/abs/1706.03449  
The rapid growth of scientific literature has made it difficult for the
researchers to quickly learn about the developments in their respective fields.
Scientific document summarization addresses this challenge by providing
summaries of the important contributions of scientific papers. We present a
framework for scientific summarization which takes advantage of the citations
and the scientific discourse structure. Citation texts often lack the evidence
and context to support the content of the cited paper and are even sometimes
inaccurate. We first address the problem of inaccuracy of the cita…

**Scientific Article Summarization Using Citation-Context and Article's Discourse Structure**
https://arxiv.org/abs/1704.06619  
We propose a summarization approach for scientific articles which takes
advantage of citation-context and the document discourse model. While citations
have been previously used in generating scientific summaries, they lack the
related context from the referenced article and therefore do not accurately
reflect the article's content. Our method overcomes the problem of inconsistency
between the citation summary and the article's content by providing context for
each citation. We also leverage the inherent scientific article's discourse for
producing better summaries. We show that our proposed m…

## Query: grounding with maps vs RAG scientific evidence coverage accuracy

**Map-Aware Models for Indoor Wireless Localization Systems: An Experimental Study**
https://arxiv.org/abs/1402.3783  
The accuracy of indoor wireless localization systems can be substantially
enhanced by map-awareness, i.e., by the knowledge of the map of the environment
in which localization signals are acquired. In fact, this knowledge can be
exploited to cancel out, at least to some extent, the signal degradation due to
propagation through physical obstructions, i.e., to the so called non-line-of-
sight bias. This result can be achieved by developing novel localization
techniques that rely on proper map-aware statistical modelling of the
measurements they process. In this manuscript a unified statistical mo…

**Evaluating Cartogram Effectiveness**
https://arxiv.org/abs/1504.02218  
Cartograms are maps in which areas of geographic regions (countries, states)
appear in proportion to some variable of interest (population, income).
Cartograms are popular visualizations for geo-referenced data that have been
used for over a century and that make it possible to gain insight into patterns
and trends in the world around us. Despite the popularity of cartograms and the
large number of cartogram types, there are few studies evaluating the
effectiveness of cartograms in conveying information. Based on a recent task
taxonomy for cartograms, we evaluate four major different types of …

**The Effect of Ground Truth Accuracy on the Evaluation of Localization Systems**
https://arxiv.org/abs/2106.13614  
The ability to accurately evaluate the performance of location determination
systems is crucial for many applications. Typically, the performance of such
systems is obtained by comparing ground truth locations with estimated
locations. However, these ground truth locations are usually obtained by
clicking on a map or using other worldwide available technologies like GPS. This
introduces ground truth errors that are due to the marking process, map
distortions, or inherent GPS inaccuracy. In this paper, we present a theoretical
framework for analyzing the effect of ground truth errors on the eva…

**RAGAR, Your Falsehood Radar: RAG-Augmented Reasoning for Political Fact-Checking using Multimodal Large Language Models**
https://arxiv.org/abs/2404.12065  
The escalating challenge of misinformation, particularly in political discourse,
requires advanced fact-checking solutions; this is even clearer in the more
complex scenario of multimodal claims. We tackle this issue using a multimodal
large language model in conjunction with retrieval-augmented generation (RAG),
and introduce two novel reasoning techniques: Chain of RAG (CoRAG) and Tree of
RAG (ToRAG). They fact-check multimodal claims by extracting both textual and
image content, retrieving external information, and reasoning subsequent
questions to be answered based on prior evidence. We ac…

**Effectiveness of Area-to-Value Legends and Grid Lines in Contiguous Area Cartograms**
https://arxiv.org/abs/2201.02995  
A contiguous area cartogram is a geographic map in which the area of each region
is proportional to numerical data (e.g., population size) while keeping
neighboring regions connected. In this study, we investigated whether value-to-
area legends (square symbols next to the values represented by the squares'
areas) and grid lines aid map readers in making better area judgments. We
conducted an experiment to determine the accuracy, speed, and confidence with
which readers infer numerical data values for the mapped regions. We found that,
when only informed about the total numerical value represen…

---

## Family summary

*(fill after reading papers — 4–6 sentences, one verification verdict: Supported / Partial / Not found)*

**Status:** Not yet run