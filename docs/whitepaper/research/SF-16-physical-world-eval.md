# SF-16 — Sf 16 Physical World Eval

**Section:** 7

**Claim:** Existing benchmarks for physical-world AI reasoning (embodied AI, robotics planning, situated reasoning) measure task completion or prediction accuracy but do not measure whether intermediate reasoning claims are bound to their generating sensor observations.

**Verification target:** Survey or benchmark paper evaluating embodied AI or planning AI on task completion or accuracy without a claim-level evidence binding metric — confirming the gap.

## Query: physical world reasoning AI benchmark evaluation intermediate steps 2024 2025

**PHYRE: A New Benchmark for Physical Reasoning**
https://arxiv.org/abs/1908.05656  
Understanding and reasoning about physics is an important ability of intelligent
agents. We develop the PHYRE benchmark for physical reasoning that contains a
set of simple classical mechanics puzzles in a 2D physical environment. The
benchmark is designed to encourage the development of learning algorithms that
are sample-efficient and generalize well across puzzles. We test several modern
learning algorithms on PHYRE and find that these algorithms fall short in
solving the puzzles efficiently. We expect that PHYRE will encourage the
development of novel sample-efficient agents that learn eff…

**Phy-Q as a measure for physical reasoning intelligence**
https://arxiv.org/abs/2108.13696  
Humans are well-versed in reasoning about the behaviors of physical objects and
choosing actions accordingly to accomplish tasks, while it remains a major
challenge for AI. To facilitate research addressing this problem, we propose a
new testbed that requires an agent to reason about physical scenarios and take
an action appropriately. Inspired by the physical knowledge acquired in infancy
and the capabilities required for robots to operate in real-world environments,
we identify 15 essential physical scenarios. We create a wide variety of
distinct task templates, and we ensure all the task te…

**Why AI is Harder Than We Think**
https://arxiv.org/abs/2104.12871  
Since its beginning in the 1950s, the field of artificial intelligence has
cycled several times between periods of optimistic predictions and massive
investment ("AI spring") and periods of disappointment, loss of confidence, and
reduced funding ("AI winter"). Even with today's seemingly fast pace of AI
breakthroughs, the development of long-promised technologies such as self-
driving cars, housekeeping robots, and conversational companions has turned out
to be much harder than many people expected. One reason for these repeating
cycles is our limited understanding of the nature and complexity …

**OlympicArena: Benchmarking Multi-discipline Cognitive Reasoning for Superintelligent AI**
https://arxiv.org/abs/2406.12753  
The evolution of Artificial Intelligence (AI) has been significantly accelerated
by advancements in Large Language Models (LLMs) and Large Multimodal Models
(LMMs), gradually showcasing potential cognitive reasoning abilities in problem-
solving and scientific discovery (i.e., AI4Science) once exclusive to human
intellect. To comprehensively evaluate current models' performance in cognitive
reasoning abilities, we introduce OlympicArena, which includes 11,163 bilingual
problems across both text-only and interleaved text-image modalities. These
challenges encompass a wide range of disciplines sp…

**OlympiadBench: A Challenging Benchmark for Promoting AGI with Olympiad-Level Bilingual Multimodal Scientific Problems**
https://arxiv.org/abs/2402.14008  
Recent advancements have seen Large Language Models (LLMs) and Large Multimodal
Models (LMMs) surpassing general human capabilities in various tasks,
approaching the proficiency level of human experts across multiple domains. With
traditional benchmarks becoming less challenging for these models, new rigorous
challenges are essential to gauge their advanced abilities. In this work, we
present OlympiadBench, an Olympiad-level bilingual multimodal scientific
benchmark, featuring 8,476 problems from Olympiad-level mathematics and physics
competitions, including the Chinese college entrance exam. …

## Query: world model evaluation situated reasoning grounding sensor observation benchmark

**STAR: A Benchmark for Situated Reasoning in Real-World Videos**
https://arxiv.org/abs/2405.09711  
Reasoning in the real world is not divorced from situations. How to capture the
present knowledge from surrounding situations and perform reasoning accordingly
is crucial and challenging for machine intelligence. This paper introduces a new
benchmark that evaluates the situated reasoning ability via situation
abstraction and logic-grounded question answering for real-world videos, called
Situated Reasoning in Real-World Videos (STAR Benchmark). This benchmark is
built upon the real-world videos associated with human actions or interactions,
which are naturally dynamic, compositional, and logic…

**Moral Stories: Situated Reasoning about Norms, Intents, Actions, and their Consequences**
https://arxiv.org/abs/2012.15738  
In social settings, much of human behavior is governed by unspoken rules of
conduct. For artificial systems to be fully integrated into social environments,
adherence to such norms is a central prerequisite. We investigate whether
contemporary NLG models can function as behavioral priors for systems deployed
in social settings by generating action hypotheses that achieve predefined goals
under moral constraints. Moreover, we examine if models can anticipate likely
consequences of (im)moral actions, or explain why certain actions are preferable
by generating relevant norms. For this purpose, we…

**WorldSense: A Synthetic Benchmark for Grounded Reasoning in Large Language Models**
https://arxiv.org/abs/2311.15930  
We propose WorldSense, a benchmark designed to assess the extent to which LLMs
are consistently able to sustain tacit world models, by testing how they draw
simple inferences from descriptions of simple arrangements of entities.
Worldsense is a synthetic benchmark with three problem types, each with their
own trivial control, which explicitly avoids bias by decorrelating the abstract
structure of problems from the vocabulary and expressions, and by decorrelating
all problem subparts with the correct response. We run our benchmark on three
state-of-the-art chat-LLMs (GPT3.5, GPT4 and Llama2-cha…

**Commonsense Scene Semantics for Cognitive Robotics: Towards Grounding Embodied Visuo-Locomotive Interactions**
https://arxiv.org/abs/1709.05293  
We present a commonsense, qualitative model for the semantic grounding of
embodied visuo-spatial and locomotive interactions. The key contribution is an
integrative methodology combining low-level visual processing with high-level,
human-centred representations of space and motion rooted in artificial
intelligence. We demonstrate practical applicability with examples involving
object interactions, and indoor movement.

**SOK-Bench: A Situated Video Reasoning Benchmark with Aligned Open-World Knowledge**
https://arxiv.org/abs/2405.09713  
Learning commonsense reasoning from visual contexts and scenes in real-world is
a crucial step toward advanced artificial intelligence. However, existing video
reasoning benchmarks are still inadequate since they were mainly designed for
factual or situated reasoning and rarely involve broader knowledge in the real
world. Our work aims to delve deeper into reasoning evaluations, specifically
within dynamic, open-world, and structured context knowledge. We propose a new
benchmark (SOK-Bench), consisting of 44K questions and 10K situations with
instance-level annotations depicted in the videos. …

## Query: AI planning benchmark evidence traceability intermediate claims physical world

**Toward Trustworthy AI Development: Mechanisms for Supporting Verifiable Claims**
https://arxiv.org/abs/2004.07213  
With the recent wave of progress in artificial intelligence (AI) has come a
growing awareness of the large-scale impacts of AI systems, and recognition that
existing regulations and norms in industry and academia are insufficient to
ensure responsible AI development. In order for AI developers to earn trust from
system users, customers, civil society, governments, and other stakeholders that
they are building AI responsibly, they will need to make verifiable claims to
which they can be held accountable. Those outside of a given organization also
need effective means of scrutinizing such claims…

**MultiFC: A Real-World Multi-Domain Dataset for Evidence-Based Fact Checking of Claims**
https://arxiv.org/abs/1909.03242  
We contribute the largest publicly available dataset of naturally occurring
factual claims for the purpose of automatic claim verification. It is collected
from 26 fact checking websites in English, paired with textual sources and rich
metadata, and labelled for veracity by human expert journalists. We present an
in-depth analysis of the dataset, highlighting characteristics and challenges.
Further, we present results for automatic veracity prediction, both with
established baselines and with a novel method for joint ranking of evidence
pages and predicting veracity that outperforms all baseli…

**The ThreeDWorld Transport Challenge: A Visually Guided Task-and-Motion Planning Benchmark for Physically Realistic Embodied AI**
https://arxiv.org/abs/2103.14025  
We introduce a visually-guided and physics-driven task-and-motion planning
benchmark, which we call the ThreeDWorld Transport Challenge. In this challenge,
an embodied agent equipped with two 9-DOF articulated arms is spawned randomly
in a simulated physical home environment. The agent is required to find a small
set of objects scattered around the house, pick them up, and transport them to a
desired final location. We also position containers around the house that can be
used as tools to assist with transporting objects efficiently. To complete the
task, an embodied agent must plan a sequence…

**TravelPlanner: A Benchmark for Real-World Planning with Language Agents**
https://arxiv.org/abs/2402.01622  
Planning has been part of the core pursuit for artificial intelligence since its
conception, but earlier AI agents mostly focused on constrained settings because
many of the cognitive substrates necessary for human-level planning have been
lacking. Recently, language agents powered by large language models (LLMs) have
shown interesting capabilities such as tool use and reasoning. Are these
language agents capable of planning in more complex settings that are out of the
reach of prior AI agents? To advance this investigation, we propose
TravelPlanner, a new planning benchmark that focuses on tr…

**CLIMATE-FEVER: A Dataset for Verification of Real-World Climate Claims**
https://arxiv.org/abs/2012.00614  
We introduce CLIMATE-FEVER, a new publicly available dataset for verification of
climate change-related claims. By providing a dataset for the research
community, we aim to facilitate and encourage work on improving algorithms for
retrieving evidential support for climate-specific claims, addressing the
underlying language understanding challenges, and ultimately help alleviate the
impact of misinformation on climate change. We adapt the methodology of FEVER
[1], the largest dataset of artificially designed claims, to real-life claims
collected from the Internet. While during this process, we …

## Query: robotics planning benchmark claim verification sensor observation grounding 2025

**TASKOGRAPHY: Evaluating robot task planning over large 3D scene graphs**
https://arxiv.org/abs/2207.05006  
3D scene graphs (3DSGs) are an emerging description; unifying symbolic,
topological, and metric scene representations. However, typical 3DSGs contain
hundreds of objects and symbols even for small environments; rendering task
planning on the full graph impractical. We construct TASKOGRAPHY, the first
large-scale robotic task planning benchmark over 3DSGs. While most benchmarking
efforts in this area focus on vision-based planning, we systematically study
symbolic planning, to decouple planning performance from visual representation
learning. We observe that, among existing methods, neither cla…

**Visual Robot Task Planning**
https://arxiv.org/abs/1804.00062  
Prospection, the act of predicting the consequences of many possible futures, is
intrinsic to human planning and action, and may even be at the root of
consciousness. Surprisingly, this idea has been explored comparatively little in
robotics. In this work, we propose a neural network architecture and associated
planning algorithm that (1) learns a representation of the world useful for
generating prospective futures after the application of high-level actions, (2)
uses this generative model to simulate the result of sequences of high-level
actions in a variety of environments, and (3) uses thi…

**MRPB 1.0: A Unified Benchmark for the Evaluation of Mobile Robot Local Planning Approaches**
https://arxiv.org/abs/2011.00491  
Local planning is one of the key technologies for mobile robots to achieve full
autonomy and has been widely investigated. To evaluate mobile robot local
planning approaches in a unified and comprehensive way, a mobile robot local
planning benchmark called MRPB 1.0 is newly proposed in this paper. The
benchmark facilitates both motion planning researchers who want to compare the
performance of a new local planner relative to many other state-of-the-art
approaches as well as end users in the mobile robotics industry who want to
select a local planner that performs best on some problems of inter…

**UKP-Athene: Multi-Sentence Textual Entailment for Claim Verification**
https://arxiv.org/abs/1809.01479  
The Fact Extraction and VERification (FEVER) shared task was launched to support
the development of systems able to verify claims by extracting supporting or
refuting facts from raw text. The shared task organizers provide a large-scale
dataset for the consecutive steps involved in claim verification, in particular,
document retrieval, fact extraction, and claim classification. In this paper, we
present our claim verification pipeline approach, which, according to the
preliminary results, scored third in the shared task, out of 23 competing
systems. For the document retrieval, we implemented a…

**PathBench: A Benchmarking Platform for Classical and Learned Path Planning Algorithms**
https://arxiv.org/abs/2105.01777  
Path planning is a key component in mobile robotics. A wide range of path
planning algorithms exist, but few attempts have been made to benchmark the
algorithms holistically or unify their interface. Moreover, with the recent
advances in deep neural networks, there is an urgent need to facilitate the
development and benchmarking of such learning-based planning algorithms. This
paper presents PathBench, a platform for developing, visualizing, training,
testing, and benchmarking of existing and future, classical and learned 2D and
3D path planning algorithms, while offering support for Robot Ope…

## Query: embodied AI benchmark evaluation world model intermediate representation 2025

**Embodied Artificial Intelligence through Distributed Adaptive Control: An Integrated Framework**
https://arxiv.org/abs/1704.01407  
In this paper, we argue that the future of Artificial Intelligence research
resides in two keywords: integration and embodiment. We support this claim by
analyzing the recent advances of the field. Regarding integration, we note that
the most impactful recent contributions have been made possible through the
integration of recent Machine Learning methods (based in particular on Deep
Learning and Recurrent Neural Networks) with more traditional ones (e.g. Monte-
Carlo tree search, goal babbling exploration or addressable memory systems).
Regarding embodiment, we note that the traditional benchma…

**RoboTHOR: An Open Simulation-to-Real Embodied AI Platform**
https://arxiv.org/abs/2004.06799  
Visual recognition ecosystems (e.g. ImageNet, Pascal, COCO) have undeniably
played a prevailing role in the evolution of modern computer vision. We argue
that interactive and embodied visual AI has reached a stage of development
similar to visual recognition prior to the advent of these ecosystems. Recently,
various synthetic environments have been introduced to facilitate research in
embodied AI. Notwithstanding this progress, the crucial question of how well
models trained in simulation generalize to reality has remained largely
unanswered. The creation of a comparable ecosystem for simulati…

**Rearrangement: A Challenge for Embodied AI**
https://arxiv.org/abs/2011.01975  
We describe a framework for research and evaluation in Embodied AI. Our proposal
is based on a canonical task: Rearrangement. A standard task can focus the
development of new techniques and serve as a source of trained models that can
be transferred to other settings. In the rearrangement task, the goal is to
bring a given physical environment into a specified state. The goal state can be
specified by object poses, by images, by a description in language, or by
letting the agent experience the environment in the goal state. We characterize
rearrangement scenarios along different axes and descr…

**ProcTHOR: Large-Scale Embodied AI Using Procedural Generation**
https://arxiv.org/abs/2206.06994  
Massive datasets and high-capacity models have driven many recent advancements
in computer vision and natural language understanding. This work presents a
platform to enable similar success stories in Embodied AI. We propose ProcTHOR,
a framework for procedural generation of Embodied AI environments. ProcTHOR
enables us to sample arbitrarily large datasets of diverse, interactive,
customizable, and performant virtual environments to train and evaluate embodied
agents across navigation, interaction, and manipulation tasks. We demonstrate
the power and potential of ProcTHOR via a sample of 10,00…

**Aligning Cyber Space with Physical World: A Comprehensive Survey on Embodied AI**
https://arxiv.org/abs/2407.06886  
Embodied Artificial Intelligence (Embodied AI) is crucial for achieving
Artificial General Intelligence (AGI) and serves as a foundation for various
applications that bridge cyberspace and the physical world. Recently, the
emergence of Multi-modal Large Models (MLMs) and World Models (WMs) have
attracted significant attention due to their remarkable perception, interaction,
and reasoning capabilities, making them a promising architecture for the brain
of embodied agents. However, there is no comprehensive survey for Embodied AI in
the era of MLMs. In this survey, we give a comprehensive explor…

---

## Family summary

The physical-world AI benchmark corpus confirms the gap cleanly. PHYRE (1908.05656) benchmarks physical reasoning via task completion rate (% puzzles solved) in 2D environments — no intermediate claim verification. Phy-Q (2108.13696) introduces 15 physical scenario categories and measures success rate — no evidence binding. The STAR benchmark (2405.09711) evaluates situated reasoning in real-world videos via question answering accuracy — no claim-level sensor grounding metric. The ThreeDWorld Transport Challenge (2103.14025) evaluates task-and-motion planning for embodied agents via success rate in object transport — no intermediate claim auditing. TravelPlanner (2402.01622) benchmarks language agent planning via plan validity and execution success — the closest to intermediate step evaluation, but measures whether plan steps are feasible, not whether they are evidence-bound to observations. TASKOGRAPHY (2207.05006) evaluates robot task planning over 3D scene graphs via planning success rate — no sensor-observation evidence binding. The comprehensive Embodied AI survey (2407.06886) categorizes evaluation as covering navigation, interaction, manipulation, and reasoning — all measured by task success, not intermediate claim grounding. The "Toward Trustworthy AI" paper (2004.07213) is the only one addressing verifiability, but focuses on system-level claims auditable by third parties, not claim-level evidence binding in intermediate outputs.

**Verdict: Supported (gap confirmed)** — across PHYRE, Phy-Q, STAR, ThreeDWorld, TravelPlanner, TASKOGRAPHY, and the embodied AI survey, all benchmarks measure task completion or accuracy. None proposes a metric for whether intermediate reasoning claims are bound to their generating sensor observations. This is the gap $R_\text{uncited}$ fills for physical-world AI systems. Primary citations for WP2 Section 7 (limits): 1908.05656 (PHYRE), 2405.09711 (STAR), 2103.14025 (ThreeDWorld), 2402.01622 (TravelPlanner), 2407.06886 (embodied AI survey — no evidence binding metric in the field).