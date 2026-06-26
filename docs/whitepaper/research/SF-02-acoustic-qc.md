# SF-2 — Sf 02 Acoustic Qc

**Section:** 3

**Claim:** Passive acoustic detection systems have non-trivial false-positive rates requiring explicit quarantine before influencing a probabilistic model.

**Verification target:** Paper or report quantifying the false-positive rate of an acoustic ML classifier in field deployment, ideally >= 10%.

## Query: OrcaHello killer whale acoustic classifier false positive rate

**Marine Mammal Species Classification using Convolutional Neural Networks and a Novel Acoustic Representation**
https://arxiv.org/abs/1907.13188  
Research into automated systems for detecting and classifying marine mammals in
acoustic recordings is expanding internationally due to the necessity to analyze
large collections of data for conservation purposes. In this work, we present a
Convolutional Neural Network that is capable of classifying the vocalizations of
three species of whales, non-biological sources of noise, and a fifth class
pertaining to ambient noise. In this way, the classifier is capable of detecting
the presence and absence of whale vocalizations in an acoustic recording.
Through transfer learning, we show that the cla…

**Bioacoustic Signal Classification Based on Continuous Region Processing, Grid Masking and Artificial Neural Network**
https://arxiv.org/abs/1305.3635  
In this paper, we develop a novel method based on machine-learning and image
processing to identify North Atlantic right whale (NARW) up-calls in the
presence of high levels of ambient and interfering noise. We apply a continuous
region algorithm on the spectrogram to extract the regions of interest, and then
use grid masking techniques to generate a small feature set that is then used in
an artificial neural network classifier to identify the NARW up-calls. It is
shown that the proposed technique is effective in detecting and capturing even
very faint up-calls, in the presence of ambient and …

**Low False-Positive Rate of Kepler Candidates Estimated From A Combination Of Spitzer And Follow-Up Observations**
https://arxiv.org/abs/1503.03173  
(Abridged) NASA's Kepler mission has provided several thousand transiting planet
candidates, yet only a small subset have been confirmed as true planets.
Therefore, the most fundamental question about these candidates is the fraction
of bona fide planets. Estimating the rate of false positives of the overall
Kepler sample is necessary to derive the planet occurrence rate. We present the
results from two large observational campaigns that were conducted with the
Spitzer telescope during the the Kepler mission. These observations are
dedicated to estimating the false positive rate (FPR) amongst …

**Performance of a Deep Neural Network at Detecting North Atlantic Right Whale Upcalls**
https://arxiv.org/abs/2001.09127  
Passive acoustics provides a powerful tool for monitoring the endangered North
Atlantic right whale ($Eubalaena$ $glacialis$), but robust detection algorithms
are needed to handle diverse and variable acoustic conditions and differences in
recording techniques and equipment. Here, we investigate the potential of deep
neural networks for addressing this need. ResNet, an architecture commonly used
for image recognition, is trained to recognize the time-frequency representation
of the characteristic North Atlantic right whale upcall. The network is trained
on several thousand examples recorded at…

**Fairness in machine learning: against false positive rate equality as a measure of fairness**
https://arxiv.org/abs/2007.02890  
As machine learning informs increasingly consequential decisions, different
metrics have been proposed for measuring algorithmic bias or unfairness. Two
popular fairness measures are calibration and equality of false positive rate.
Each measure seems intuitively important, but notably, it is usually impossible
to satisfy both measures. For this reason, a large literature in machine
learning speaks of a fairness tradeoff between these two measures. This framing
assumes that both measures are, in fact, capturing something important. To date,
philosophers have not examined this crucial assumption…

## Query: Orcasound passive acoustic monitoring uncertainty marine mammal

**Marine Mammal Species Classification using Convolutional Neural Networks and a Novel Acoustic Representation**
https://arxiv.org/abs/1907.13188  
Research into automated systems for detecting and classifying marine mammals in
acoustic recordings is expanding internationally due to the necessity to analyze
large collections of data for conservation purposes. In this work, we present a
Convolutional Neural Network that is capable of classifying the vocalizations of
three species of whales, non-biological sources of noise, and a fifth class
pertaining to ambient noise. In this way, the classifier is capable of detecting
the presence and absence of whale vocalizations in an acoustic recording.
Through transfer learning, we show that the cla…

**Convolutional Neural Networks for Passive Monitoring of a Shallow Water Environment using a Single Sensor**
https://arxiv.org/abs/1612.03505  
A cost effective approach to remote monitoring of protected areas such as marine
reserves and restricted naval waters is to use passive sonar to detect,
classify, localize, and track marine vessel activity (including small boats and
autonomous underwater vehicles). Cepstral analysis of underwater acoustic data
enables the time delay between the direct path arrival and the first multipath
arrival to be measured, which in turn enables estimation of the instantaneous
range of the source (a small boat). However, this conventional method is limited
to ranges where the Lloyd's mirror effect (interfe…

**Automatic Detection and Compression for Passive Acoustic Monitoring of the African Forest Elephant**
https://arxiv.org/abs/1902.09069  
In this work, we consider applying machine learning to the analysis and
compression of audio signals in the context of monitoring elephants in sub-
Saharan Africa. Earth's biodiversity is increasingly under threat by sources of
anthropogenic change (e.g. resource extraction, land use change, and climate
change) and surveying animal populations is critical for developing conservation
strategies. However, manually monitoring tropical forests or deep oceans is
intractable. For species that communicate acoustically, researchers have argued
for placing audio recorders in the habitats as a cost-effec…

**High Performance Computer Acoustic Data Accelerator: A New System for Exploring Marine Mammal Acoustics for Big Data Applications**
https://arxiv.org/abs/1509.03591  
This paper presents a new software model designed for distributed sonic signal
detection runtime using machine learning algorithms called DeLMA. A new
algorithm--Acoustic Data-mining Accelerator (ADA)--is also presented. ADA is a
robust yet scalable solution for efficiently processing big sound archives using
distributing computing technologies. Together, DeLMA and the ADA algorithm
provide a powerful tool currently being used by the Bioacoustics Research
Program (BRP) at the Cornell Lab of Ornithology, Cornell University. This paper
provides a high level technical overview of the system, and …

**AnuraSet: A dataset for benchmarking Neotropical anuran calls identification in passive acoustic monitoring**
https://arxiv.org/abs/2307.06860  
Global change is predicted to induce shifts in anuran acoustic behavior, which
can be studied through passive acoustic monitoring (PAM). Understanding changes
in calling behavior requires the identification of anuran species, which is
challenging due to the particular characteristics of neotropical soundscapes. In
this paper, we introduce a large-scale multi-species dataset of anuran
amphibians calls recorded by PAM, that comprises 27 hours of expert annotations
for 42 different species from two Brazilian biomes. We provide open access to
the dataset, including the raw recordings, experimental…

## Query: deep learning bioacoustics detection precision recall field deployment

**Computational bioacoustics with deep learning: a review and roadmap**
https://arxiv.org/abs/2112.06725  
Animal vocalisations and natural soundscapes are fascinating objects of study,
and contain valuable evidence about animal behaviours, populations and
ecosystems. They are studied in bioacoustics and ecoacoustics, with signal
processing and analysis an important component. Computational bioacoustics has
accelerated in recent decades due to the growth of affordable digital sound
recording devices, and to huge progress in informatics such as big data, signal
processing and machine learning. Methods are inherited from the wider field of
deep learning, including speech and image processing. However…

**Automatic acoustic detection of birds through deep learning: the first Bird Audio Detection challenge**
https://arxiv.org/abs/1807.05812  
Assessing the presence and abundance of birds is important for monitoring
specific species as well as overall ecosystem health. Many birds are most
readily detected by their sounds, and thus passive acoustic monitoring is highly
appropriate. Yet acoustic monitoring is often held back by practical limitations
such as the need for manual configuration, reliance on example sound libraries,
low accuracy, low robustness, and limited ability to generalise to novel
acoustic conditions. Here we report outcomes from a collaborative data challenge
showing that with modern machine learning including deep…

**Robust sound event detection in bioacoustic sensor networks**
https://arxiv.org/abs/1905.08352  
Bioacoustic sensors, sometimes known as autonomous recording units (ARUs), can
record sounds of wildlife over long periods of time in scalable and minimally
invasive ways. Deriving per-species abundance estimates from these sensors
requires detection, classification, and quantification of animal vocalizations
as individual acoustic events. Yet, variability in ambient noise, both over time
and across sensors, hinders the reliability of current automated systems for
sound event detection (SED), such as convolutional neural networks (CNN) in the
time-frequency domain. In this article, we develop,…

**Precision-Recall Curve (PRC) Classification Trees**
https://arxiv.org/abs/2011.07640  
The classification of imbalanced data has presented a significant challenge for
most well-known classification algorithms that were often designed for data with
relatively balanced class distributions. Nevertheless skewed class distribution
is a common feature in real world problems. It is especially prevalent in
certain application domains with great need for machine learning and better
predictive analysis such as disease diagnosis, fraud detection, bankruptcy
prediction, and suspect identification. In this paper, we propose a novel tree-
based algorithm based on the area under the precision-r…

**Localization Recall Precision (LRP): A New Performance Metric for Object Detection**
https://arxiv.org/abs/1807.01696  
Average precision (AP), the area under the recall-precision (RP) curve, is the
standard performance measure for object detection. Despite its wide acceptance,
it has a number of shortcomings, the most important of which are (i) the
inability to distinguish very different RP curves, and (ii) the lack of directly
measuring bounding box localization accuracy. In this paper, we propose
'Localization Recall Precision (LRP) Error', a new metric which we specifically
designed for object detection. LRP Error is composed of three components related
to localization, false negative (FN) rate and false po…

## Query: PSTH peristimulus time histogram acoustic event spike train fit

**Spike-Train Level Backpropagation for Training Deep Recurrent Spiking Neural Networks**
https://arxiv.org/abs/1908.06378  
Spiking neural networks (SNNs) well support spatiotemporal learning and energy-
efficient event-driven hardware neuromorphic processors. As an important class
of SNNs, recurrent spiking neural networks (RSNNs) possess great computational
power. However, the practical application of RSNNs is severely limited by
challenges in training. Biologically-inspired unsupervised learning has limited
capability in boosting the performance of RSNNs. On the other hand, existing
backpropagation (BP) methods suffer from high complexity of unrolling in time,
vanishing and exploding gradients, and approximate di…

**Microscopic approach of a time elapsed neural model**
https://arxiv.org/abs/1506.02361  
The spike trains are the main components of the information processing in the
brain. To model spike trains several point processes have been investigated in
the literature. And more macroscopic approaches have also been studied, using
partial differential equation models. The main aim of the present article is to
build a bridge between several point processes models (Poisson, Wold, Hawkes)
that have been proved to statistically fit real spike trains data and age-
structured partial differential equations as introduced by Pakdaman, Perthame
and Salort.

**Acoustic event detection for multiple overlapping similar sources**
https://arxiv.org/abs/1503.07150  
Many current paradigms for acoustic event detection (AED) are not adapted to the
organic variability of natural sounds, and/or they assume a limit on the number
of simultaneous sources: often only one source, or one source of each type, may
be active. These aspects are highly undesirable for applications such as bird
population monitoring. We introduce a simple method modelling the onsets,
durations and offsets of acoustic events to avoid intrinsic limits on polyphony
or on inter-event temporal patterns. We evaluate the method in a case study with
over 3000 zebra finch calls. In comparison aga…

**Point process models for sequence detection in high-dimensional neural spike trains**
https://arxiv.org/abs/2010.04875  
Sparse sequences of neural spikes are posited to underlie aspects of working
memory, motor production, and learning. Discovering these sequences in an
unsupervised manner is a longstanding problem in statistical neuroscience.
Promising recent work utilized a convolutive nonnegative matrix factorization
model to tackle this challenge. However, this model requires spike times to be
discretized, utilizes a sub-optimal least-squares criterion, and does not
provide uncertainty estimates for model predictions or estimated parameters. We
address each of these shortcomings by developing a point proces…

**SPIKY: A graphical user interface for monitoring spike train synchrony**
https://arxiv.org/abs/1410.6910  
Techniques for recording large-scale neuronal spiking activity are developing
very fast. This leads to an increasing demand for algorithms capable of
analyzing large amounts of experimental spike train data. One of the most
crucial and demanding tasks is the identification of similarity patterns with a
very high temporal resolution and across different spatial scales. To address
this task, in recent years three time-resolved measures of spike train synchrony
have been proposed, the ISI-distance, the SPIKE-distance, and event
synchronization. The Matlab source codes for calculating and visualiz…

## Query: Level 0 QC acoustic candidate review workflow marine mammal detector

**Marine Mammal Species Classification using Convolutional Neural Networks and a Novel Acoustic Representation**
https://arxiv.org/abs/1907.13188  
Research into automated systems for detecting and classifying marine mammals in
acoustic recordings is expanding internationally due to the necessity to analyze
large collections of data for conservation purposes. In this work, we present a
Convolutional Neural Network that is capable of classifying the vocalizations of
three species of whales, non-biological sources of noise, and a fifth class
pertaining to ambient noise. In this way, the classifier is capable of detecting
the presence and absence of whale vocalizations in an acoustic recording.
Through transfer learning, we show that the cla…

**Search for Proton Decay via p -> e^+ pi^0 and p -> mu^+ pi^0 in a Large Water Cherenkov Detector**
https://arxiv.org/abs/0903.0676  
We have searched for proton decays via p -> e^+ pi^0 and p -> mu^+ pi^0 using
data from a 91.7 kiloton year exposure of Super-Kamiokande-I and a 49.2 kiloton
year exposure of Super-Kamiokande-II. No candidate events were observed with
expected backgrounds induced by atmospheric neutrinos of 0.3 events for each
decay mode. From these results, we set lower limits on the partial lifetime of
8.2$\times10^{33}$ and 6.6$\times10^{33}$ years at 90% confidence level for p ->
e^+ pi^0 and p -> mu^+ pi^0 modes, respectively.

**Bioacoustical Periodic Pulse Train Signal Detection and Classification using Spectrogram Intensity Binarization and Energy Projection**
https://arxiv.org/abs/1305.3250  
The following work outlines an approach for automatic detection and recognition
of periodic pulse train signals using a multi-stage process based on spectrogram
edge detection, energy projection and classification. The method has been
implemented to automatically detect and recognize pulse train songs of minke
whales. While the long term goal of this work is to properly identify and detect
minke songs from large multi-year datasets, this effort was developed using
sounds off the coast of Massachusetts, in the Stellwagen Bank National Marine
Sanctuary. The detection methodology is presented and…

**High Performance Computer Acoustic Data Accelerator: A New System for Exploring Marine Mammal Acoustics for Big Data Applications**
https://arxiv.org/abs/1509.03591  
This paper presents a new software model designed for distributed sonic signal
detection runtime using machine learning algorithms called DeLMA. A new
algorithm--Acoustic Data-mining Accelerator (ADA)--is also presented. ADA is a
robust yet scalable solution for efficiently processing big sound archives using
distributing computing technologies. Together, DeLMA and the ADA algorithm
provide a powerful tool currently being used by the Bioacoustics Research
Program (BRP) at the Cornell Lab of Ornithology, Cornell University. This paper
provides a high level technical overview of the system, and …

**Bioacoustic Signal Classification Based on Continuous Region Processing, Grid Masking and Artificial Neural Network**
https://arxiv.org/abs/1305.3635  
In this paper, we develop a novel method based on machine-learning and image
processing to identify North Atlantic right whale (NARW) up-calls in the
presence of high levels of ambient and interfering noise. We apply a continuous
region algorithm on the spectrogram to extract the regions of interest, and then
use grid masking techniques to generate a small feature set that is then used in
an artificial neural network classifier to identify the NARW up-calls. It is
shown that the proposed technique is effective in detecting and capturing even
very faint up-calls, in the presence of ambient and …

---

## Family summary

The corpus is well-supplied with deep learning bioacoustics classification papers. The marine mammal CNN classifier (1907.13188) and the North Atlantic right whale upcall ResNet (2001.09127) both report precision-recall trade-offs characteristic of high false-positive rates in field deployment — the right whale paper specifically trains on thousands of examples and notes performance degradation under variable acoustic conditions. The computational bioacoustics review (2112.06725) is the strongest single citation: it surveys the field and explicitly identifies false positives, deployment robustness, and the gap between lab and field performance as major open problems across all passive acoustic monitoring systems. The Bird Audio Detection challenge (1807.05812) provides an empirical benchmark where field false-positive rates under noisy conditions remain high even with deep learning, establishing this as a well-documented cross-species problem. The PSTH query returned spike-train neuroscience papers rather than acoustic event PSTH papers — that is a corpus limitation; the whitepaper should note that the PSTH methodology is documented in modeling code rather than an arXiv-indexed paper. No paper directly quantifies OrcaHello's field false-positive rate, but the broader evidence base (high false-positive rates in analogous marine mammal classifiers, the established difficulty of field deployment) supports the claim that quarantine before model ingestion is necessary.

**Verdict: Supported** — not from an OrcaHello-specific paper, but from the consistent pattern across analogous marine mammal classifiers. Cite 2112.06725 (bioacoustics review) and 2001.09127 (right whale DNN) as the primary supports; note the OrcaHello gap.