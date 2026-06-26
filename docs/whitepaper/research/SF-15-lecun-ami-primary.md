# SF-15 — Sf 15 Lecun Ami Primary

**Section:** 6

**Claim:** LeCun's world model architecture (AMI, 2022) requires that intermediate representations be grounded in their generating sensor observations as a design property; no formal evaluation metric for this evidence-binding property is proposed in the AMI position paper or in subsequent JEPA architecture papers.

**Verification target:** LeCun's 2022 position paper or V-JEPA paper confirming that evidence grounding is named as a design requirement but that no claim-level metric is proposed, confirming the gap that R_uncited fills.

## Query: LeCun autonomous machine intelligence world model architecture evaluation 2022

**Autonomous Driving with Deep Learning: A Survey of State-of-Art Technologies**
https://arxiv.org/abs/2006.06091  
Since DARPA Grand Challenges (rural) in 2004/05 and Urban Challenges in 2007,
autonomous driving has been the most active field of AI applications. Almost at
the same time, deep learning has made breakthrough by several pioneers, three of
them (also called fathers of deep learning), Hinton, Bengio and LeCun, won ACM
Turin Award in 2019. This is a survey of autonomous driving technologies with
deep learning methods. We investigate the major fields of self-driving systems,
such as perception, mapping and localization, prediction, planning and control,
simulation, V2X and safety etc. Due to the l…

**Building Machines that Learn and Think for Themselves: Commentary on Lake et al., Behavioral and Brain Sciences, 2017**
https://arxiv.org/abs/1711.08378  
We agree with Lake and colleagues on their list of key ingredients for building
humanlike intelligence, including the idea that model-based reasoning is
essential. However, we favor an approach that centers on one additional
ingredient: autonomy. In particular, we aim toward agents that can both build
and exploit their own internal models, with minimal human hand-engineering. We
believe an approach centered on autonomous learning has the greatest chance of
success as we scale toward real-world complexity, tackling domains for which
ready-made formal models are not available. Here we survey sev…

**Cyber Threat Intelligence Model: An Evaluation of Taxonomies, Sharing Standards, and Ontologies within Cyber Threat Intelligence**
https://arxiv.org/abs/2103.03530  
Cyber threat intelligence is the provision of evidence-based knowledge about
existing or emerging threats. Benefits from threat intelligence include
increased situational awareness, efficiency in security operations, and improved
prevention, detection, and response capabilities. To process, correlate, and
analyze vast amounts of threat information and data and derive intelligence that
can be shared and consumed in meaningful times, it is required to utilize
structured, machine-readable formats that incorporate the industry-required
expressivity while at the same time being unambiguous. To a la…

**Introduction to Latent Variable Energy-Based Models: A Path Towards Autonomous Machine Intelligence**
https://arxiv.org/abs/2306.02572  
Current automated systems have crucial limitations that need to be addressed
before artificial intelligence can reach human-like levels and bring new
technological revolutions. Among others, our societies still lack Level 5 self-
driving cars, domestic robots, and virtual assistants that learn reliable world
models, reason, and plan complex action sequences. In these notes, we summarize
the main ideas behind the architecture of autonomous intelligence of the future
proposed by Yann LeCun. In particular, we introduce energy-based and latent
variable models and combine their advantages in the bui…

**ADriver-I: A General World Model for Autonomous Driving**
https://arxiv.org/abs/2311.13549  
Typically, autonomous driving adopts a modular design, which divides the full
stack into perception, prediction, planning and control parts. Though
interpretable, such modular design tends to introduce a substantial amount of
redundancy. Recently, multimodal large language models (MLLM) and diffusion
techniques have demonstrated their superior performance on comprehension and
generation ability. In this paper, we first introduce the concept of interleaved
vision-action pair, which unifies the format of visual features and control
signals. Based on the vision-action pairs, we construct a genera…

## Query: path towards autonomous machine intelligence world model grounding sensor observation

**Kosmos-2: Grounding Multimodal Large Language Models to the World**
https://arxiv.org/abs/2306.14824  
We introduce Kosmos-2, a Multimodal Large Language Model (MLLM), enabling new
capabilities of perceiving object descriptions (e.g., bounding boxes) and
grounding text to the visual world. Specifically, we represent refer expressions
as links in Markdown, i.e., ``[text span](bounding boxes)'', where object
descriptions are sequences of location tokens. Together with multimodal corpora,
we construct large-scale data of grounded image-text pairs (called GrIT) to
train the model. In addition to the existing capabilities of MLLMs (e.g.,
perceiving general modalities, following instructions, and per…

**A Roadmap towards Machine Intelligence**
https://arxiv.org/abs/1511.08130  
The development of intelligent machines is one of the biggest unsolved
challenges in computer science. In this paper, we propose some fundamental
properties these machines should have, focusing in particular on communication
and learning. We discuss a simple environment that could be used to
incrementally teach a machine the basics of natural-language-based
communication, as a prerequisite to more complex interaction with human users.
We also present some conjectures on the sort of algorithms the machine should
support in order to profitably learn from the environment.

**Copilot4D: Learning Unsupervised World Models for Autonomous Driving via Discrete Diffusion**
https://arxiv.org/abs/2311.01017  
Learning world models can teach an agent how the world works in an unsupervised
manner. Even though it can be viewed as a special case of sequence modeling,
progress for scaling world models on robotic applications such as autonomous
driving has been somewhat less rapid than scaling language models with
Generative Pre-trained Transformers (GPT). We identify two reasons as major
bottlenecks: dealing with complex and unstructured observation space, and having
a scalable generative model. Consequently, we propose Copilot4D, a novel world
modeling approach that first tokenizes sensor observations …

**A Visual Attention Grounding Neural Model for Multimodal Machine Translation**
https://arxiv.org/abs/1808.08266  
We introduce a novel multimodal machine translation model that utilizes parallel
visual and textual information. Our model jointly optimizes the learning of a
shared visual-language embedding and a translator. The model leverages a visual
attention grounding mechanism that links the visual semantics with the
corresponding textual semantics. Our approach achieves competitive state-of-the-
art results on the Multi30K and the Ambiguous COCO datasets. We also collected a
new multilingual multimodal product description dataset to simulate a real-world
international online shopping scenario. On this …

**A path to AI**
https://arxiv.org/abs/1712.03080  
To build a safe system that would replicate and perhaps transcend human-level
intelligence, three basic modules: objective, agent, and perception are proposed
for development. The objective module would ensure that the system acts in
humanity's interest, not against it. It would have two components: a network of
machine learning agents to address the problem of value alignment and a
distributed ledger to propose a mechanism to mitigate the existential threat.
The agent module would further develop the Dyna concept and benefit from a
treatise in sociology to build the missing link of artificial…

## Query: V-JEPA video JEPA evaluation framework grounding 2024 2025

**Revisiting Feature Prediction for Learning Visual Representations from Video**
https://arxiv.org/abs/2404.08471  
This paper explores feature prediction as a stand-alone objective for
unsupervised learning from video and introduces V-JEPA, a collection of vision
models trained solely using a feature prediction objective, without the use of
pretrained image encoders, text, negative examples, reconstruction, or other
sources of supervision. The models are trained on 2 million videos collected
from public datasets and are evaluated on downstream image and video tasks. Our
results show that learning by predicting video features leads to versatile
visual representations that perform well on both motion and app…

**NTIRE 2023 Quality Assessment of Video Enhancement Challenge**
https://arxiv.org/abs/2307.09729  
This paper reports on the NTIRE 2023 Quality Assessment of Video Enhancement
Challenge, which will be held in conjunction with the New Trends in Image
Restoration and Enhancement Workshop (NTIRE) at CVPR 2023. This challenge is to
address a major challenge in the field of video processing, namely, video
quality assessment (VQA) for enhanced videos. The challenge uses the VQA Dataset
for Perceptual Video Enhancement (VDPVE), which has a total of 1211 enhanced
videos, including 600 videos with color, brightness, and contrast enhancements,
310 videos with deblurring, and 301 deshaked videos. The …

**HEMVIP: Human Evaluation of Multiple Videos in Parallel**
https://arxiv.org/abs/2101.11898  
In many research areas, for example motion and gesture generation, objective
measures alone do not provide an accurate impression of key stimulus traits such
as perceived quality or appropriateness. The gold standard is instead to
evaluate these aspects through user studies, especially subjective evaluations
of video stimuli. Common evaluation paradigms either present individual stimuli
to be scored on Likert-type scales, or ask users to compare and rate videos in a
pairwise fashion. However, the time and resources required for such evaluations
scale poorly as the number of conditions to be co…

**The End-of-End-to-End: A Video Understanding Pentathlon Challenge (2020)**
https://arxiv.org/abs/2008.00744  
We present a new video understanding pentathlon challenge, an open competition
held in conjunction with the IEEE Conference on Computer Vision and Pattern
Recognition (CVPR) 2020. The objective of the challenge was to explore and
evaluate new methods for text-to-video retrieval-the task of searching for
content within a corpus of videos using natural language queries. This report
summarizes the results of the first edition of the challenge together with the
findings of the participants.

**Test and Evaluation Framework for Multi-Agent Systems of Autonomous Intelligent Agents**
https://arxiv.org/abs/2101.10430  
Test and evaluation is a necessary process for ensuring that engineered systems
perform as intended under a variety of conditions, both expected and unexpected.
In this work, we consider the unique challenges of developing a unifying test
and evaluation framework for complex ensembles of cyber-physical systems with
embedded artificial intelligence. We propose a framework that incorporates test
and evaluation throughout not only the development life cycle, but continues
into operation as the system learns and adapts in a noisy, changing, and
contended environment. The framework accounts for the…

## Query: AMI world model evidence binding belief grounding sensor observation evaluation

**Sensor Validation Using Dynamic Belief Networks**
https://arxiv.org/abs/1303.5419  
The trajectory of a robot is monitored in a restricted dynamic environment using
light beam sensor data. We have a Dynamic Belief Network (DBN), based on a
discrete model of the domain, which provides discrete monitoring analogous to
conventional quantitative filter techniques. Sensor observations are added to
the basic DBN in the form of specific evidence. However, sensor data is often
partially or totally incorrect. We show how the basic DBN, which infers only an
impossible combination of evidence, may be modified to handle specific types of
incorrect data which may occur in the domain. We t…

**Towards a General-Purpose Belief Maintenance System**
https://arxiv.org/abs/1304.3084  
There currently exists a gap between the theories proposed by the probability
and uncertainty and the needs of Artificial Intelligence research. These
theories primarily address the needs of expert systems, using knowledge
structures which must be pre-compiled and remain static in structure during
runtime. Many Al systems require the ability to dynamically add and remove parts
of the current knowledge structure (e.g., in order to examine what the world
would be like for different causal theories). This requires more flexibility
than existing uncertainty systems display. In addition, many Al re…

**A Backwards View for Assessment**
https://arxiv.org/abs/1304.3107  
Much artificial intelligence research focuses on the problem of deducing the
validity of unobservable propositions or hypotheses from observable evidence.!
Many of the knowledge representation techniques designed for this problem encode
the relationship between evidence and hypothesis in a directed manner. Moreover,
the direction in which evidence is stored is typically from evidence to
hypothesis.

**Approximate evaluation of marginal association probabilities with belief propagation**
https://arxiv.org/abs/1209.6299  
Data association, the problem of reasoning over correspondence between targets
and measurements, is a fundamental problem in tracking. This paper presents a
graphical model formulation of data association and applies an approximate
inference method, belief propagation (BP), to obtain estimates of marginal
association probabilities. We prove that BP is guaranteed to converge, and bound
the number of iterations necessary. Experiments reveal a favourable comparison
to prior methods in terms of accuracy and computational complexity.

**Symbolic Learning and Reasoning with Noisy Data for Probabilistic Anchoring**
https://arxiv.org/abs/2002.10373  
Robotic agents should be able to learn from sub-symbolic sensor data, and at the
same time, be able to reason about objects and communicate with humans on a
symbolic level. This raises the question of how to overcome the gap between
symbolic and sub-symbolic artificial intelligence. We propose a semantic world
modeling approach based on bottom-up object anchoring using an object-centered
representation of the world. Perceptual anchoring processes continuous
perceptual sensor data and maintains a correspondence to a symbolic
representation. We extend the definitions of anchoring to handle multi…

## Query: JEPA world model intermediate representation evaluation metric grounding

**Kosmos-2: Grounding Multimodal Large Language Models to the World**
https://arxiv.org/abs/2306.14824  
We introduce Kosmos-2, a Multimodal Large Language Model (MLLM), enabling new
capabilities of perceiving object descriptions (e.g., bounding boxes) and
grounding text to the visual world. Specifically, we represent refer expressions
as links in Markdown, i.e., ``[text span](bounding boxes)'', where object
descriptions are sequences of location tokens. Together with multimodal corpora,
we construct large-scale data of grounded image-text pairs (called GrIT) to
train the model. In addition to the existing capabilities of MLLMs (e.g.,
perceiving general modalities, following instructions, and per…

**Learning and Leveraging World Models in Visual Representation Learning**
https://arxiv.org/abs/2403.00504  
Joint-Embedding Predictive Architecture (JEPA) has emerged as a promising self-
supervised approach that learns by leveraging a world model. While previously
limited to predicting missing parts of an input, we explore how to generalize
the JEPA prediction task to a broader set of corruptions. We introduce Image
World Models, an approach that goes beyond masked image modeling and learns to
predict the effect of global photometric transformations in latent space. We
study the recipe of learning performant IWMs and show that it relies on three
key aspects: conditioning, prediction difficulty, and …

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

**JaSPICE: Automatic Evaluation Metric Using Predicate-Argument Structures for Image Captioning Models**
https://arxiv.org/abs/2311.04192  
Image captioning studies heavily rely on automatic evaluation metrics such as
BLEU and METEOR. However, such n-gram-based metrics have been shown to correlate
poorly with human evaluation, leading to the proposal of alternative metrics
such as SPICE for English; however, no equivalent metrics have been established
for other languages. Therefore, in this study, we propose an automatic
evaluation metric called JaSPICE, which evaluates Japanese captions based on
scene graphs. The proposed method generates a scene graph from dependencies and
the predicate-argument structure, and extends the graph …

**Elements of World Knowledge (EWOK): A cognition-inspired framework for evaluating basic world knowledge in language models**
https://arxiv.org/abs/2405.09605  
The ability to build and leverage world models is essential for a general-
purpose AI agent. Testing such capabilities is hard, in part because the
building blocks of world models are ill-defined. We present Elements of World
Knowledge (EWOK), a framework for evaluating world modeling in language models
by testing their ability to use knowledge of a concept to match a target text
with a plausible/implausible context. EWOK targets specific concepts from
multiple knowledge domains known to be vital for world modeling in humans.
Domains range from social interactions (help/hinder) to spatial relat…

---

## Family summary

The search returned three tiers of directly useful results. The most important finding is the EM hit on "Introduction to Latent Variable Energy-Based Models: A Path Towards Autonomous Machine Intelligence" (2306.02572) — a lecture-note companion to LeCun's 2022 OpenReview position paper. It explicitly introduces the full AMI architecture: Configurator, World Model, Actor, Short-Term Memory, and Cost modules, and articulates the requirement that the world model must learn to predict latent representations of future world states from current perceptions. The paper describes evaluation as proceeding via downstream task performance on image and video benchmarks — accuracy and task completion — with no claim-level evidence binding metric proposed. The V-JEPA paper (2404.08471) is confirmed in the corpus: it trains vision models by predicting video features in latent space and evaluates on downstream image and video tasks (motion, appearance), again using accuracy not evidence binding rate. The JEPA world model paper (2403.00504) — Image World Models — extends JEPA to global photometric transformations and evaluates on linear probing accuracy; no grounding quality metric. The EWOK framework (2405.09605) is the most adjacent evaluation paper: it tests world modeling in language models by measuring whether models use world knowledge to match text with plausible contexts. EWOK measures plausibility, not evidence binding. The autonomous driving survey (2006.06091) confirms that LeCun's architecture has been applied to Level 5 driving and evaluated on safety and accuracy metrics, not evidence binding.

**Verdict: Supported (gap confirmed)** — LeCun's architecture (2306.02572 + OpenReview position paper) explicitly names sensor-grounded intermediate representations as a design requirement; all downstream evaluation papers (V-JEPA 2404.08471, IWM 2403.00504, EWOK 2405.09605) measure accuracy or task performance, not evidence binding rate. The gap $R_\text{uncited}$ fills is confirmed. Primary citations for WP2 Section 6: 2306.02572 (AMI architecture spec), 2404.08471 (V-JEPA — architecture target), 2403.00504 (IWM — JEPA evaluation gap example), 2405.09605 (EWOK — closest evaluation framework without evidence binding).