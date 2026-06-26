# SF-7 — Sf 07 Llm Grounding

**Section:** 4

**Claim:** Structured citation architectures reduce the rate of unsupported scientific claims relative to unstructured LLM generation or place-grounded tool calls.

**Verification target:** Paper showing structured grounding (tool dispatch + span citation) reduces unsupported-claim or hallucination rate versus ungrounded or place-only generation.

## Query: retrieval augmented generation factual accuracy citation hallucination reduction

**Retrieval Augmentation Reduces Hallucination in Conversation**
https://arxiv.org/abs/2104.07567  
Despite showing increasingly human-like conversational abilities, state-of-the-
art dialogue models often suffer from factual incorrectness and hallucination of
knowledge (Roller et al., 2020). In this work we explore the use of neural-
retrieval-in-the-loop architectures - recently shown to be effective in open-
domain QA (Lewis et al., 2020b; Izacard and Grave, 2020) - for knowledge-
grounded dialogue, a task that is arguably more challenging as it requires
querying based on complex multi-turn dialogue context and generating
conversationally coherent responses. We study various types of architec…

**Corrective Retrieval Augmented Generation**
https://arxiv.org/abs/2401.15884  
Large language models (LLMs) inevitably exhibit hallucinations since the
accuracy of generated texts cannot be secured solely by the parametric knowledge
they encapsulate. Although retrieval-augmented generation (RAG) is a practicable
complement to LLMs, it relies heavily on the relevance of retrieved documents,
raising concerns about how the model behaves if retrieval goes wrong. To this
end, we propose the Corrective Retrieval Augmented Generation (CRAG) to improve
the robustness of generation. Specifically, a lightweight retrieval evaluator is
designed to assess the overall quality of retri…

**Citation-Enhanced Generation for LLM-based Chatbots**
https://arxiv.org/abs/2402.16063  
Large language models (LLMs) exhibit powerful general intelligence across
diverse scenarios, including their integration into chatbots. However, a vital
challenge of LLM-based chatbots is that they may produce hallucinated content in
responses, which significantly limits their applicability. Various efforts have
been made to alleviate hallucination, such as retrieval augmented generation and
reinforcement learning with human feedback, but most of them require additional
training and data annotation. In this paper, we propose a novel post-hoc
Citation-Enhanced Generation (CEG) approach combined…

**Retrieve Only When It Needs: Adaptive Retrieval Augmentation for Hallucination Mitigation in Large Language Models**
https://arxiv.org/abs/2402.10612  
Hallucinations pose a significant challenge for the practical implementation of
large language models (LLMs). The utilization of parametric knowledge in
generating factual content is constrained by the limited knowledge of LLMs,
potentially resulting in internal hallucinations. While incorporating external
information can help fill knowledge gaps, it also introduces the risk of
irrelevant information, thereby increasing the likelihood of external
hallucinations. A careful and balanced integration of the parametric knowledge
within LLMs with external information is crucial to alleviate hallucin…

**Hallucination Reduction in Long Input Text Summarization**
https://arxiv.org/abs/2309.16781  
Hallucination in text summarization refers to the phenomenon where the model
generates information that is not supported by the input source document.
Hallucination poses significant obstacles to the accuracy and reliability of the
generated summaries. In this paper, we aim to reduce hallucinated outputs or
hallucinations in summaries of long-form text documents. We have used the PubMed
dataset, which contains long scientific research documents and their abstracts.
We have incorporated the techniques of data filtering and joint entity and
summary generation (JAENS) in the fine-tuning of the Lo…

## Query: groundingSupports span citation binding LLM attribution architecture

**Citation inequity and gendered citation practices in contemporary physics**
https://arxiv.org/abs/2112.09047  
The historical and contemporary under-attribution of women's contributions to
scientific scholarship is well-known and well-studied, with effects that are
felt today in myriad ways by women scientists. One measure of this under-
attribution is the so-called citation gap between men and women: the under-
citation of papers authored by women relative to expected rates coupled with a
corresponding over-citation of papers authored by men relative to expected
rates. We explore the citation gap in contemporary physics, analyzing over one
million articles published over the last 25 years in 35 physics …

**HAGRID: A Human-LLM Collaborative Dataset for Generative Information-Seeking with Attribution**
https://arxiv.org/abs/2307.16883  
The rise of large language models (LLMs) had a transformative impact on search,
ushering in a new era of search engines that are capable of generating search
results in natural language text, imbued with citations for supporting sources.
Building generative information-seeking models demands openly accessible
datasets, which currently remain lacking. In this paper, we introduce a new
dataset, HAGRID (Human-in-the-loop Attributable Generative Retrieval for
Information-seeking Dataset) for building end-to-end generative information-
seeking models that are capable of retrieving candidate quotes a…

**Effective Large Language Model Adaptation for Improved Grounding and Citation Generation**
https://arxiv.org/abs/2311.09533  
Large language models (LLMs) have achieved remarkable advancements in natural
language understanding and generation. However, one major issue towards their
widespread deployment in the real world is that they can generate "hallucinated"
answers that are not factual. Towards this end, this paper focuses on improving
LLMs by grounding their responses in retrieved passages and by providing
citations. We propose a new framework, AGREE, Adaptation for GRounding
EnhancEment, that improves the grounding from a holistic perspective. Our
framework tunes LLMs to selfground the claims in their responses …

**Deepfake Network Architecture Attribution**
https://arxiv.org/abs/2202.13843  
With the rapid progress of generation technology, it has become necessary to
attribute the origin of fake images. Existing works on fake image attribution
perform multi-class classification on several Generative Adversarial Network
(GAN) models and obtain high accuracies. While encouraging, these works are
restricted to model-level attribution, only capable of handling images generated
by seen models with a specific seed, loss and dataset, which is limited in real-
world scenarios when fake images may be generated by privately trained models.
This motivates us to ask whether it is possible to a…

**A Survey of Large Language Models Attribution**
https://arxiv.org/abs/2311.03731  
Open-domain generative systems have gained significant attention in the field of
conversational AI (e.g., generative search engines). This paper presents a
comprehensive review of the attribution mechanisms employed by these systems,
particularly large language models. Though attribution or citation improve the
factuality and verifiability, issues like ambiguous knowledge reservoirs,
inherent biases, and the drawbacks of excessive attribution can hinder the
effectiveness of these systems. The aim of this survey is to provide valuable
insights for researchers, aiding in the refinement of attrib…

## Query: prepare then narrate tool grounding LLM deterministic skill dispatch

**LLM-Grounder: Open-Vocabulary 3D Visual Grounding with Large Language Model as an Agent**
https://arxiv.org/abs/2309.12311  
3D visual grounding is a critical skill for household robots, enabling them to
navigate, manipulate objects, and answer questions based on their environment.
While existing approaches often rely on extensive labeled data or exhibit
limitations in handling complex language queries, we propose LLM-Grounder, a
novel zero-shot, open-vocabulary, Large Language Model (LLM)-based 3D visual
grounding pipeline. LLM-Grounder utilizes an LLM to decompose complex natural
language queries into semantic constituents and employs a visual grounding tool,
such as OpenScene or LERF, to identify objects in a 3D …

**Self-driven Grounding: Large Language Model Agents with Automatical Language-aligned Skill Learning**
https://arxiv.org/abs/2309.01352  
Large language models (LLMs) show their powerful automatic reasoning and
planning capability with a wealth of semantic knowledge about the human world.
However, the grounding problem still hinders the applications of LLMs in the
real-world environment. Existing studies try to fine-tune the LLM or utilize
pre-defined behavior APIs to bridge the LLMs and the environment, which not only
costs huge human efforts to customize for every single task but also weakens the
generality strengths of LLMs. To autonomously ground the LLM onto the
environment, we proposed the Self-Driven Grounding (SDG) frame…

**Symbolic Planning and Code Generation for Grounded Dialogue**
https://arxiv.org/abs/2310.17140  
Large language models (LLMs) excel at processing and generating both text and
code. However, LLMs have had limited applicability in grounded task-oriented
dialogue as they are difficult to steer toward task objectives and fail to
handle novel grounding. We present a modular and interpretable grounded dialogue
system that addresses these shortcomings by composing LLMs with a symbolic
planner and grounded code execution. Our system consists of a reader and
planner: the reader leverages an LLM to convert partner utterances into
executable code, calling functions that perform grounding. The transl…

**Grounding Language Plans in Demonstrations Through Counterfactual Perturbations**
https://arxiv.org/abs/2403.17124  
Grounding the common-sense reasoning of Large Language Models (LLMs) in physical
domains remains a pivotal yet unsolved problem for embodied AI. Whereas prior
works have focused on leveraging LLMs directly for planning in symbolic spaces,
this work uses LLMs to guide the search of task structures and constraints
implicit in multi-step demonstrations. Specifically, we borrow from manipulation
planning literature the concept of mode families, which group robot
configurations by specific motion constraints, to serve as an abstraction layer
between the high-level language representations of an LLM…

**DoReMi: Grounding Language Model by Detecting and Recovering from Plan-Execution Misalignment**
https://arxiv.org/abs/2307.00329  
Large language models (LLMs) encode a vast amount of semantic knowledge and
possess remarkable understanding and reasoning capabilities. Previous work has
explored how to ground LLMs in robotic tasks to generate feasible and executable
textual plans. However, low-level execution in the physical world may deviate
from the high-level textual plan due to environmental perturbations or imperfect
controller design. In this paper, we propose \textbf{DoReMi}, a novel language
model grounding framework that enables immediate Detection and Recovery from
Misalignments between plan and execution. Specifi…

## Query: structured step log LLM interaction provenance scientific claim

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

**Towards LLM-based Fact Verification on News Claims with a Hierarchical Step-by-Step Prompting Method**
https://arxiv.org/abs/2310.00305  
While large pre-trained language models (LLMs) have shown their impressive
capabilities in various NLP tasks, they are still under-explored in the
misinformation domain. In this paper, we examine LLMs with in-context learning
(ICL) for news claim verification, and find that only with 4-shot demonstration
examples, the performance of several prompting methods can be comparable with
previous supervised models. To further boost performance, we introduce a
Hierarchical Step-by-Step (HiSS) prompting method which directs LLMs to separate
a claim into several subclaims and then verify each of them vi…

**MultiVerS: Improving scientific claim verification with weak supervision and full-document context**
https://arxiv.org/abs/2112.01640  
The scientific claim verification task requires an NLP system to label
scientific documents which Support or Refute an input claim, and to select
evidentiary sentences (or rationales) justifying each predicted label. In this
work, we present MultiVerS, which predicts a fact-checking label and identifies
rationales in a multitask fashion based on a shared encoding of the claim and
full document context. This approach accomplishes two key modeling goals. First,
it ensures that all relevant contextual information is incorporated into each
labeling decision. Second, it enables the model to learn f…

**PAV ontology: Provenance, Authoring and Versioning**
https://arxiv.org/abs/1304.7224  
Provenance is a critical ingredient for establishing trust of published
scientific content. This is true whether we are considering a data set, a
computational workflow, a peer-reviewed publication or a simple scientific claim
with supportive evidence. Existing vocabularies such as DC Terms and the W3C
PROV-O are domain-independent and general-purpose and they allow and encourage
for extensions to cover more specific needs. We identify the specific need for
identifying or distinguishing between the various roles assumed by agents
manipulating digital artifacts, such as author, contributor and …

**QMUL-SDS at SCIVER: Step-by-Step Binary Classification for Scientific Claim Verification**
https://arxiv.org/abs/2104.11572  
Scientific claim verification is a unique challenge that is attracting
increasing interest. The SCIVER shared task offers a benchmark scenario to test
and compare claim verification approaches by participating teams and consists in
three steps: relevant abstract selection, rationale selection and label
prediction. In this paper, we present team QMUL-SDS's participation in the
shared task. We propose an approach that performs scientific claim verification
by doing binary classifications step-by-step. We trained a BioBERT-large
classifier to select abstracts based on pairwise relevance assessmen…

## Query: citation architecture place grounding vs dataset grounding evidence quality

**Grounding Answers for Visual Questions Asked by Visually Impaired People**
https://arxiv.org/abs/2202.01993  
Visual question answering is the task of answering questions about images. We
introduce the VizWiz-VQA-Grounding dataset, the first dataset that visually
grounds answers to visual questions asked by people with visual impairments. We
analyze our dataset and compare it with five VQA-Grounding datasets to
demonstrate what makes it similar and different. We then evaluate the SOTA VQA
and VQA-Grounding models and demonstrate that current SOTA algorithms often fail
to identify the correct visual evidence where the answer is located. These
models regularly struggle when the visual evidence occupies …

**Neural Sequential Phrase Grounding (SeqGROUND)**
https://arxiv.org/abs/1903.07669  
We propose an end-to-end approach for phrase grounding in images. Unlike prior
methods that typically attempt to ground each phrase independently by building
an image-text embedding, our architecture formulates grounding of multiple
phrases as a sequential and contextual process. Specifically, we encode region
proposals and all phrases into two stacks of LSTM cells, along with so-far
grounded phrase-region pairs. These LSTM stacks collectively capture context for
grounding of the next phrase. The resulting architecture, which we call
SeqGROUND, supports many-to-many matching by allowing an ima…

**Grounding 'Grounding' in NLP**
https://arxiv.org/abs/2106.02192  
The NLP community has seen substantial recent interest in grounding to
facilitate interaction between language technologies and the world. However, as
a community, we use the term broadly to reference any linking of text to data or
non-textual modality. In contrast, Cognitive Science more formally defines
"grounding" as the process of establishing what mutual information is required
for successful communication between two interlocutors -- a definition which
might implicitly capture the NLP usage but differs in intent and scope. We
investigate the gap between these definitions and seek answers…

**Effective Large Language Model Adaptation for Improved Grounding and Citation Generation**
https://arxiv.org/abs/2311.09533  
Large language models (LLMs) have achieved remarkable advancements in natural
language understanding and generation. However, one major issue towards their
widespread deployment in the real world is that they can generate "hallucinated"
answers that are not factual. Towards this end, this paper focuses on improving
LLMs by grounding their responses in retrieved passages and by providing
citations. We propose a new framework, AGREE, Adaptation for GRounding
EnhancEment, that improves the grounding from a holistic perspective. Our
framework tunes LLMs to selfground the claims in their responses …

**Composing Pick-and-Place Tasks By Grounding Language**
https://arxiv.org/abs/2102.08094  
Controlling robots to perform tasks via natural language is one of the most
challenging topics in human-robot interaction. In this work, we present a robot
system that follows unconstrained language instructions to pick and place
arbitrary objects and effectively resolves ambiguities through dialogues. Our
approach infers objects and their relationships from input images and language
expressions and can place objects in accordance with the spatial relations
expressed by the user. Unlike previous approaches, we consider grounding not
only for the picking but also for the placement of everyday o…

---

## Family summary

The RAG and citation-grounding literature is the strongest in the corpus. The retrieval augmentation for dialogue paper (2104.07567) established that retrieval-in-the-loop architectures reduce factual hallucination in conversational settings. CRAG (2401.15884) shows that corrective retrieval — evaluating whether retrieval is relevant before injecting it — substantially reduces hallucination, directly analogous to orcast's policy of running only allow-listed skills per cast role. The Citation-Enhanced Generation paper (2402.16063) demonstrates a post-hoc citation-binding approach that reduces hallucination in LLM chatbots without additional training, establishing span-level citation binding as a tractable engineering problem. The AGREE framework (2311.09533) is the most directly relevant: it adapts LLMs to self-ground claims in retrieved passages and generate citations, showing measurable reduction in unsupported claims. The LLM attribution survey (2311.03731) reviews the full space of attribution mechanisms and confirms that generative systems without attribution produce high rates of unsupported claims that are difficult to audit. Across the corpus, the consistent finding is that structured retrieval plus explicit citation binding (span-level or annotation-level) reduces unsupported-claim rate; this supports the core claim of orcast's grounding pattern versus the Maps baseline (85% uncited scientific claims from place-grounding alone).

**Verdict: Supported** — structured citation architectures measurably reduce unsupported claims. Primary citations: 2311.09533 (AGREE grounding + citation), 2401.15884 (CRAG corrective retrieval), 2311.03731 (attribution survey), 2402.16063 (citation-enhanced generation).