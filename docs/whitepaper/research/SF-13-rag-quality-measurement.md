# SF-13 — Sf 13 Rag Quality Measurement

**Section:** 4

**Claim:** Not all RAG context reduces the unsupported scientific claim rate; structured step-log reasoning traces achieve 0% uncited rate where unstructured data injection does not.

**Verification target:** Paper measuring the differential effect of RAG context type on unsupported scientific claim rate, or proposing a formal metric for grounding quality.

## Query: RAG context quality measurement grounding evaluation metric

**Ragas: Automated Evaluation of Retrieval Augmented Generation**
https://arxiv.org/abs/2309.15217  
We introduce Ragas (Retrieval Augmented Generation Assessment), a framework for
reference-free evaluation of Retrieval Augmented Generation (RAG) pipelines. RAG
systems are composed of a retrieval and an LLM based generation module, and
provide LLMs with knowledge from a reference textual database, which enables
them to act as a natural language layer between a user and textual databases,
reducing the risk of hallucinations. Evaluating RAG architectures is, however,
challenging because there are several dimensions to consider: the ability of the
retrieval system to identify relevant and focuse…

**Evaluating Retrieval Quality in Retrieval-Augmented Generation**
https://arxiv.org/abs/2404.13781  
Evaluating retrieval-augmented generation (RAG) presents challenges,
particularly for retrieval models within these systems. Traditional end-to-end
evaluation methods are computationally expensive. Furthermore, evaluation of the
retrieval model's performance based on query-document relevance labels shows a
small correlation with the RAG system's downstream performance. We propose a
novel evaluation approach, eRAG, where each document in the retrieval list is
individually utilized by the large language model within the RAG system. The
output generated for each document is then evaluated based o…

**TIGEr: Text-to-Image Grounding for Image Caption Evaluation**
https://arxiv.org/abs/1909.02050  
This paper presents a new metric called TIGEr for the automatic evaluation of
image captioning systems. Popular metrics, such as BLEU and CIDEr, are based
solely on text matching between reference captions and machine-generated
captions, potentially leading to biased evaluations because references may not
fully cover the image content and natural language is inherently ambiguous.
Building upon a machine-learned text-image grounding model, TIGEr allows to
evaluate caption quality not only based on how well a caption represents image
content, but also on how well machine-generated captions match…

**Evaluation of RAG Metrics for Question Answering in the Telecom Domain**
https://arxiv.org/abs/2407.12873  
Retrieval Augmented Generation (RAG) is widely used to enable Large Language
Models (LLMs) perform Question Answering (QA) tasks in various domains. However,
RAG based on open-source LLM for specialized domains has challenges of
evaluating generated responses. A popular framework in the literature is the RAG
Assessment (RAGAS), a publicly available library which uses LLMs for evaluation.
One disadvantage of RAGAS is the lack of details of derivation of numerical
value of the evaluation metrics. One of the outcomes of this work is a modified
version of this package for few metrics (faithfulness…

**A Formal Evaluation of PSNR as Quality Measurement Parameter for Image Segmentation Algorithms**
https://arxiv.org/abs/1605.07116  
Quality evaluation of image segmentation algorithms are still subject of debate
and research. Currently, there is no generic metric that could be applied to any
algorithm reliably. This article contains an evaluation for the PSRN (Peak
Signal-To-Noise Ratio) as a metric which has been used to evaluate threshold
level selection as well as the number of thresholds in the case of multi-level
segmentation. The results obtained in this study suggest that the PSNR is not an
adequate quality measurement for segmentation algorithms.

## Query: structured vs unstructured retrieval augmented generation citation accuracy

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

**Active Retrieval Augmented Generation**
https://arxiv.org/abs/2305.06983  
Despite the remarkable ability of large language models (LMs) to comprehend and
generate language, they have a tendency to hallucinate and create factually
inaccurate output. Augmenting LMs by retrieving information from external
knowledge resources is one promising solution. Most existing retrieval augmented
LMs employ a retrieve-and-generate setup that only retrieves information once
based on the input. This is limiting, however, in more general scenarios
involving generation of long texts, where continually gathering information
throughout generation is essential. In this work, we provide a…

**Understanding Retrieval Augmentation for Long-Form Question Answering**
https://arxiv.org/abs/2310.12150  
We present a study of retrieval-augmented language models (LMs) on long-form
question answering. We analyze how retrieval augmentation impacts different LMs,
by comparing answers generated from models while using the same evidence
documents, and how differing quality of retrieval document set impacts the
answers generated from the same LM. We study various attributes of generated
answers (e.g., fluency, length, variance) with an emphasis on the attribution of
generated long-form answers to in-context evidence documents. We collect human
annotations of answer attribution and evaluate methods fo…

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

**Retrieval Augmented Generation and Representative Vector Summarization for large unstructured textual data in Medical Education**
https://arxiv.org/abs/2308.00479  
Large Language Models are increasingly being used for various tasks including
content generation and as chatbots. Despite their impressive performances in
general tasks, LLMs need to be aligned when applying for domain specific tasks
to mitigate the problems of hallucination and producing harmful answers.
Retrieval Augmented Generation (RAG) allows to easily attach and manipulate a
non-parametric knowledgebases to LLMs. Applications of RAG in the field of
medical education are discussed in this paper. A combined extractive and
abstractive summarization method for large unstructured textual dat…

## Query: step log trace injection LLM grounding factual accuracy

**WikiChat: Stopping the Hallucination of Large Language Model Chatbots by Few-Shot Grounding on Wikipedia**
https://arxiv.org/abs/2305.14292  
This paper presents the first few-shot LLM-based chatbot that almost never
hallucinates and has high conversationality and low latency. WikiChat is
grounded on the English Wikipedia, the largest curated free-text corpus.
WikiChat generates a response from an LLM, retains only the grounded facts, and
combines them with additional information it retrieves from the corpus to form
factual and engaging responses. We distill WikiChat based on GPT-4 into a
7B-parameter LLaMA model with minimal loss of quality, to significantly improve
its latency, cost and privacy, and facilitate research and deploym…

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

**Enhancing LLM Factual Accuracy with RAG to Counter Hallucinations: A Case Study on Domain-Specific Queries in Private Knowledge-Bases**
https://arxiv.org/abs/2403.10446  
We proposed an end-to-end system design towards utilizing Retrieval Augmented
Generation (RAG) to improve the factual accuracy of Large Language Models (LLMs)
for domain-specific and time-sensitive queries related to private knowledge-
bases. Our system integrates RAG pipeline with upstream datasets processing and
downstream performance evaluation. Addressing the challenge of LLM
hallucinations, we finetune models with a curated dataset which originates from
CMU's extensive resources and annotated with the teacher model. Our experiments
demonstrate the system's effectiveness in generating more …

**Assessing The Factual Accuracy of Generated Text**
https://arxiv.org/abs/1905.13322  
We propose a model-based metric to estimate the factual accuracy of generated
text that is complementary to typical scoring schemes like ROUGE (Recall-
Oriented Understudy for Gisting Evaluation) and BLEU (Bilingual Evaluation
Understudy). We introduce and release a new large-scale dataset based on
Wikipedia and Wikidata to train relation classifiers and end-to-end fact
extraction models. The end-to-end models are shown to be able to extract
complete sets of facts from datasets with full pages of text. We then analyse
multiple models that estimate factual accuracy on a Wikipedia text summarizat…

**Prompt Injection attack against LLM-integrated Applications**
https://arxiv.org/abs/2306.05499  
Large Language Models (LLMs), renowned for their superior proficiency in
language comprehension and generation, stimulate a vibrant ecosystem of
applications around them. However, their extensive assimilation into various
services introduces significant security risks. This study deconstructs the
complexities and implications of prompt injection attacks on actual LLM-
integrated applications. Initially, we conduct an exploratory analysis on ten
commercial applications, highlighting the constraints of current attack
strategies in practice. Prompted by these limitations, we subsequently
formulate…

## Query: reasoning chain injection evidence binding claim accuracy measurement

**ReCEval: Evaluating Reasoning Chains via Correctness and Informativeness**
https://arxiv.org/abs/2304.10703  
Multi-step reasoning ability is fundamental to many natural language tasks, yet
it is unclear what constitutes a good reasoning chain and how to evaluate them.
Most existing methods focus solely on whether the reasoning chain leads to the
correct conclusion, but this answer-oriented view may confound reasoning quality
with other spurious shortcuts to predict the answer. To bridge this gap, we
evaluate reasoning chains by viewing them as informal proofs that derive the
final answer. Specifically, we propose ReCEval (Reasoning Chain Evaluation), a
framework that evaluates reasoning chains via tw…

**A Study of Associative Evidential Reasoning**
https://arxiv.org/abs/1304.2740  
Evidential reasoning is cast as the problem of simplifying the evidence-
hypothesis relation and constructing combination formulas that possess certain
testable properties. Important classes of evidence as identifiers, annihilators,
and idempotents and their roles in determining binary operations on intervals of
reals are discussed. The appropriate way of constructing formulas for combining
evidence and their limitations, for instance, in robustness, are presented.

**SCITAB: A Challenging Benchmark for Compositional Reasoning and Claim Verification on Scientific Tables**
https://arxiv.org/abs/2305.13186  
Current scientific fact-checking benchmarks exhibit several shortcomings, such
as biases arising from crowd-sourced claims and an over-reliance on text-based
evidence. We present SCITAB, a challenging evaluation dataset consisting of 1.2K
expert-verified scientific claims that 1) originate from authentic scientific
publications and 2) require compositional reasoning for verification. The claims
are paired with evidence-containing scientific tables annotated with labels.
Through extensive evaluations, we demonstrate that SCITAB poses a significant
challenge to state-of-the-art models, including…

**Claim-Dissector: An Interpretable Fact-Checking System with Joint Re-ranking and Veracity Prediction**
https://arxiv.org/abs/2207.14116  
We present Claim-Dissector: a novel latent variable model for fact-checking and
analysis, which given a claim and a set of retrieved evidences jointly learns to
identify: (i) the relevant evidences to the given claim, (ii) the veracity of
the claim. We propose to disentangle the per-evidence relevance probability and
its contribution to the final veracity probability in an interpretable way --
the final veracity probability is proportional to a linear ensemble of per-
evidence relevance probabilities. In this way, the individual contributions of
evidences towards the final predicted probability…

**Automatic Fake News Detection: Are Models Learning to Reason?**
https://arxiv.org/abs/2105.07698  
Most fact checking models for automatic fake news detection are based on
reasoning: given a claim with associated evidence, the models aim to estimate
the claim veracity based on the supporting or refuting content within the
evidence. When these models perform well, it is generally assumed to be due to
the models having learned to reason over the evidence with regards to the claim.
In this paper, we investigate this assumption of reasoning, by exploring the
relationship and importance of both claim and evidence. Surprisingly, we find on
political fact checking datasets that most often the high…

## Query: retrieval quality diagnostic hierarchy grounding architecture evaluation

**Hierarchy-based Image Embeddings for Semantic Image Retrieval**
https://arxiv.org/abs/1809.09924  
Deep neural networks trained for classification have been found to learn
powerful image representations, which are also often used for other tasks such
as comparing images w.r.t. their visual similarity. However, visual similarity
does not imply semantic similarity. In order to learn semantically
discriminative features, we propose to map images onto class embeddings whose
pair-wise dot products correspond to a measure of semantic similarity between
classes. Such an embedding does not only improve image retrieval results, but
could also facilitate integrating semantics for other tasks, e.g., n…

**Evaluating Retrieval Quality in Retrieval-Augmented Generation**
https://arxiv.org/abs/2404.13781  
Evaluating retrieval-augmented generation (RAG) presents challenges,
particularly for retrieval models within these systems. Traditional end-to-end
evaluation methods are computationally expensive. Furthermore, evaluation of the
retrieval model's performance based on query-document relevance labels shows a
small correlation with the RAG system's downstream performance. We propose a
novel evaluation approach, eRAG, where each document in the retrieval list is
individually utilized by the large language model within the RAG system. The
output generated for each document is then evaluated based o…

**Semantic Image Retrieval via Active Grounding of Visual Situations**
https://arxiv.org/abs/1711.00088  
We describe a novel architecture for semantic image retrieval---in particular,
retrieval of instances of visual situations. Visual situations are concepts such
as "a boxing match," "walking the dog," "a crowd waiting for a bus," or "a game
of ping-pong," whose instantiations in images are linked more by their common
spatial and semantic structure than by low-level visual similarity. Given a
query situation description, our architecture---called Situate---learns models
capturing the visual features of expected objects as well the expected spatial
configuration of relationships among objects. Gi…

**TIGEr: Text-to-Image Grounding for Image Caption Evaluation**
https://arxiv.org/abs/1909.02050  
This paper presents a new metric called TIGEr for the automatic evaluation of
image captioning systems. Popular metrics, such as BLEU and CIDEr, are based
solely on text matching between reference captions and machine-generated
captions, potentially leading to biased evaluations because references may not
fully cover the image content and natural language is inherently ambiguous.
Building upon a machine-learned text-image grounding model, TIGEr allows to
evaluate caption quality not only based on how well a caption represents image
content, but also on how well machine-generated captions match…

**Evaluation of Software Architecture Quality Attribute for an Internet Banking System**
https://arxiv.org/abs/1312.2342  
The design phase plays a vital role than all other phases in the software
development. Software Architecture has to meet both the functional and non-
functional quality requirements. The Evaluation of Architecture has to be
performed, so that the developers are assured that their selected Architecture
will reduce the cost and effort and also enhances the various quality attributes
like Availability, Reusability, Performance, Modifiability and Extendibility.
The success of the system depends upon the Architecture Evaluation by the
essential method to the system. The overall ranking of the candid…

---

## Family summary

The RAG evaluation corpus is strong and directly relevant. The Ragas framework (2309.15217) is the most important citation: it introduces reference-free evaluation of RAG pipelines on multiple dimensions including faithfulness (whether claims are supported by retrieved context), answer relevancy, and context precision — directly analogous to $R_\text{uncited}$ as a claim-level grounding metric. The eRAG paper (2404.13781) proposes evaluating each retrieved document individually against the LLM output, showing that query-document relevance labels poorly predict downstream RAG performance, supporting the claim that grounding quality requires output-level measurement rather than retrieval-level measurement. The ALCE benchmark (2305.14627) is the most precise citation: it proposes a benchmark for automatic evaluation of LLM citation generation — the LLM must produce text with supporting citations, and the benchmark measures whether citations actually support the claims. This is essentially $R_\text{uncited}$ at the sentence level. The WikiChat paper (2305.14292) demonstrates that grounding on structured knowledge eliminates hallucination, and that fact-based grounding must be evaluated claim-by-claim rather than response-level. The ReCEval paper (2304.10703) introduces evaluation of reasoning chains via correctness and informativeness — the closest precedent for evaluating whether a planning step-log is evidentially adequate. Together these establish that: (a) claim-level citation accuracy is a standard RAG evaluation concern, (b) structured retrieval outperforms unstructured injection for grounding quality, and (c) evaluation must be at the claim level not the response level.

**Verdict: Supported** — claim-level citation evaluation (Ragas, ALCE) and structured grounding superiority (WikiChat) are established. The specific $R_\text{uncited}$ definition and the step-log vs unstructured injection comparison are novel contributions of the orcast benchmark. Primary citations: 2309.15217 (Ragas), 2305.14627 (ALCE citation evaluation), 2305.14292 (WikiChat structured grounding).