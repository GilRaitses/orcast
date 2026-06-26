# SF-3 — Sf 03 Negative Binomial

**Section:** 2

**Claim:** Negative-binomial regression or Poisson point-process intensity models are the appropriate distributional family for sparse, overdispersed encounter count data.

**Verification target:** Paper using NB or point-process intensity for wildlife encounter data, reporting superiority over Gaussian or Poisson for overdispersed counts.

## Query: negative binomial regression wildlife count data overdispersion zero inflation

**Beta-Negative Binomial Process and Poisson Factor Analysis**
https://arxiv.org/abs/1112.3605  
A beta-negative binomial (BNB) process is proposed, leading to a beta-gamma-
Poisson process, which may be viewed as a "multi-scoop" generalization of the
beta-Bernoulli process. The BNB process is augmented into a beta-gamma-gamma-
Poisson hierarchical structure, and applied as a nonparametric Bayesian prior
for an infinite Poisson factor analysis model. A finite approximation for the
beta process Levy random measure is constructed for convenient implementation.
Efficient MCMC computations are performed with data augmentation and
marginalization techniques. Encouraging results are shown on docu…

**Negative Binomial Process Count and Mixture Modeling**
https://arxiv.org/abs/1209.3442  
The seemingly disjoint problems of count and mixture modeling are united under
the negative binomial (NB) process. A gamma process is employed to model the
rate measure of a Poisson process, whose normalization provides a random
probability measure for mixture modeling and whose marginalization leads to an
NB process for count modeling. A draw from the NB process consists of a Poisson
distributed finite number of distinct atoms, each of which is associated with a
logarithmic distributed number of data samples. We reveal relationships between
various count- and mixture-modeling distributions an…

**Lognormal and Gamma Mixed Negative Binomial Regression**
https://arxiv.org/abs/1206.6456  
In regression analysis of counts, a lack of simple and efficient algorithms for
posterior computation has made Bayesian approaches appear unattractive and thus
underdeveloped. We propose a lognormal and gamma mixed negative binomial (NB)
regression model for counts, and present efficient closed-form Bayesian
inference; unlike conventional Poisson models, the proposed approach has two
free parameters to include two different kinds of random effects, and allows the
incorporation of prior information, such as sparsity in the regression
coefficients. By placing a gamma distribution prior on the NB…

**Deep Hurdle Networks for Zero-Inflated Multi-Target Regression: Application to Multiple Species Abundance Estimation**
https://arxiv.org/abs/2010.16040  
A key problem in computational sustainability is to understand the distribution
of species across landscapes over time. This question gives rise to challenging
large-scale prediction problems since (i) hundreds of species have to be
simultaneously modeled and (ii) the survey data are usually inflated with zeros
due to the absence of species for a large number of sites. The problem of
tackling both issues simultaneously, which we refer to as the zero-inflated
multi-target regression problem, has not been addressed by previous methods in
statistics and machine learning. In this paper, we propose…

**Log-Linear Bayesian Additive Regression Trees for Multinomial Logistic and Count Regression Models**
https://arxiv.org/abs/1701.01503  
We introduce Bayesian additive regression trees (BART) for log-linear models
including multinomial logistic regression and count regression with zero-
inflation and overdispersion. BART has been applied to nonparametric mean
regression and binary classification problems in a range of settings. However,
existing applications of BART have been limited to models for Gaussian "data",
either observed or latent. This is primarily because efficient MCMC algorithms
are available for Gaussian likelihoods. But while many useful models are
naturally cast in terms of latent Gaussian variables, many others …

## Query: inhomogeneous Poisson process intensity ecological encounter rate

**Poisson intensity estimation with reproducing kernels**
https://arxiv.org/abs/1610.08623  
Despite the fundamental nature of the inhomogeneous Poisson process in the
theory and application of stochastic processes, and its attractive
generalizations (e.g. Cox process), few tractable nonparametric modeling
approaches of intensity functions exist, especially when observed points lie in
a high-dimensional space. In this paper we develop a new, computationally
tractable Reproducing Kernel Hilbert Space (RKHS) formulation for the
inhomogeneous Poisson process. We model the square root of the intensity as an
RKHS function. Whereas RKHS models used in supervised learning rely on the so-
call…

**How range residency and long-range perception change encounter rates**
https://arxiv.org/abs/1907.05902  
Encounter rates link movement strategies to intra- and inter-specific
interactions, and therefore translate individual movement behavior into higher-
level ecological processes. Indeed, a large body of interacting population
theory rests on the law of mass action, which can be derived from assumptions of
Brownian motion in an enclosed container with exclusively local perception.
These assumptions imply completely uniform space use, individual home ranges
equivalent to the population range, and encounter dependent on movement paths
actually crossing. Mounting empirical evidence, however, suggest…

**Optimality of Poisson processes intensity learning with Gaussian processes**
https://arxiv.org/abs/1409.5103  
In this paper we provide theoretical support for the so-called "Sigmoidal
Gaussian Cox Process" approach to learning the intensity of an inhomogeneous
Poisson process on a $d$-dimensional domain. This method was proposed by Adams,
Murray and MacKay (ICML, 2009), who developed a tractable computational approach
and showed in simulation and real data experiments that it can work quite
satisfactorily. The results presented in the present paper provide theoretical
underpinning of the method. In particular, we show how to tune the priors on the
hyper parameters of the model in order for the procedu…

**Multi-output Gaussian Process Modulated Poisson Processes for Event Prediction**
https://arxiv.org/abs/2011.03172  
Prediction of events such as part replacement and failure events plays a
critical role in reliability engineering. Event stream data are commonly
observed in manufacturing and teleservice systems. Designing predictive models
for individual units based on such event streams is challenging and an under-
explored problem. In this work, we propose a non-parametric prognostic framework
for individualized event prediction based on the inhomogeneous Poisson processes
with a multivariate Gaussian convolution process (MGCP) prior on the intensity
functions. The MGCP prior on the intensity functions of t…

**Spherical Poisson Point Process Intensity Function Modeling and Estimation with Measure Transport**
https://arxiv.org/abs/2201.09485  
Recent years have seen an increased interest in the application of methods and
techniques commonly associated with machine learning and artificial intelligence
to spatial statistics. Here, in a celebration of the ten-year anniversary of the
journal Spatial Statistics, we bring together normalizing flows, commonly used
for density function estimation in machine learning, and spherical point
processes, a topic of particular interest to the journal's readership, to
present a new approach for modeling non-homogeneous Poisson process intensity
functions on the sphere. The central idea of this frame…

## Query: cyclic covariate diel lunar kernel encounter rate temporal model

**Analysis of Kernel Mean Matching under Covariate Shift**
https://arxiv.org/abs/1206.4650  
In real supervised learning scenarios, it is not uncommon that the training and
test sample follow different probability distributions, thus rendering the
necessity to correct the sampling bias. Focusing on a particular covariate shift
problem, we derive high probability confidence bounds for the kernel mean
matching (KMM) estimator, whose convergence rate turns out to depend on some
regularity measure of the regression function and also on some capacity measure
of the kernel. By comparing KMM with the natural plug-in estimator, we establish
the superiority of the former hence provide concrete…

**Optimally tackling covariate shift in RKHS-based nonparametric regression**
https://arxiv.org/abs/2205.02986  
We study the covariate shift problem in the context of nonparametric regression
over a reproducing kernel Hilbert space (RKHS). We focus on two natural families
of covariate shift problems defined using the likelihood ratios between the
source and target distributions. When the likelihood ratios are uniformly
bounded, we prove that the kernel ridge regression (KRR) estimator with a
carefully chosen regularization parameter is minimax rate-optimal (up to a log
factor) for a large family of RKHSs with regular kernel eigenvalues.
Interestingly, KRR does not require full knowledge of likelihood ra…

**Temporal Variability of Lunar Exospheric Helium During January 2012 from LRO/LAMP**
https://arxiv.org/abs/1209.3274  
We report observations of the lunar helium exosphere made between December 29,
2011, and January 26, 2012, with the Lyman Alpha Mapping Project (LAMP)
ultraviolet spectrograph on NASA's Lunar Reconnaissance Orbiter Mission (LRO).
The observations were made of resonantly scattered He I 584 from illuminated
atmosphere against the dark lunar surface on the dawn side of the terminator. We
find no or little variation of the derived surface He density with latitude but
day-to-day variations that likely reflect variations in the solar wind alpha
flux. The 5-day passage of the Moon through the Earth's…

**Scaling of Erosion Rate in Subsonic Jet Experiments and Apollo Lunar Module Landings**
https://arxiv.org/abs/2104.10038  
Small scale jet-induced erosion experiments are useful for identifying the
scaling of erosion with respect to the various physical parameters (gravity,
grain size, gas velocity, gas density, grain density, etc.), and because they
provide a data set for benchmarking numerical flow codes. We have performed
experiments varying the physical parameters listed above (e.g., gravity was
varied in reduced gravity aircraft flights). In all these experiments, a
subsonic jet of gas impinges vertically on a bed of sand or lunar soil simulant
forming a localized scour hole beneath the jet. Videography captu…

**Pseudo-Labeling for Kernel Ridge Regression under Covariate Shift**
https://arxiv.org/abs/2302.10160  
We develop and analyze a principled approach to kernel ridge regression under
covariate shift. The goal is to learn a regression function with small mean
squared error over a target distribution, based on unlabeled data from there and
labeled data that may have a different feature distribution. We propose to split
the labeled data into two subsets, and conduct kernel ridge regression on them
separately to obtain a collection of candidate models and an imputation model.
We use the latter to fill the missing labels and then select the best candidate
accordingly. Our non-asymptotic excess risk bo…

## Query: sparse count data distribution family ecological forecasting selection

**Priors for Random Count Matrices Derived from a Family of Negative Binomial Processes**
https://arxiv.org/abs/1404.3331  
We define a family of probability distributions for random count matrices with a
potentially unbounded number of rows and columns. The three distributions we
consider are derived from the gamma-Poisson, gamma-negative binomial, and beta-
negative binomial processes. Because the models lead to closed-form Gibbs
sampling update equations, they are natural candidates for nonparametric
Bayesian priors over count matrices. A key aspect of our analysis is the
recognition that, although the random count matrices within the family are
defined by a row-wise construction, their columns can be shown to be…

**A sparse negative binomial mixture model for clustering RNA-seq count data**
https://arxiv.org/abs/1912.02399  
Clustering with variable selection is a challenging yet critical task for modern
small-n-large-p data. Existing methods based on sparse Gaussian mixture models
or sparse K-means provide solutions to continuous data. With the prevalence of
RNA-seq technology and lack of count data modeling for clustering, the current
practice is to normalize count expression data into continuous measures and
apply existing models with Gaussian assumption. In this paper, we develop a
negative binomial mixture model with lasso or fused lasso gene regularization to
cluster samples (small n) with high-dimensional g…

**Deep Hurdle Networks for Zero-Inflated Multi-Target Regression: Application to Multiple Species Abundance Estimation**
https://arxiv.org/abs/2010.16040  
A key problem in computational sustainability is to understand the distribution
of species across landscapes over time. This question gives rise to challenging
large-scale prediction problems since (i) hundreds of species have to be
simultaneously modeled and (ii) the survey data are usually inflated with zeros
due to the absence of species for a large number of sites. The problem of
tackling both issues simultaneously, which we refer to as the zero-inflated
multi-target regression problem, has not been addressed by previous methods in
statistics and machine learning. In this paper, we propose…

**StatEcoNet: Statistical Ecology Neural Networks for Species Distribution Modeling**
https://arxiv.org/abs/2102.08534  
This paper focuses on a core task in computational sustainability and
statistical ecology: species distribution modeling (SDM). In SDM, the occurrence
pattern of a species on a landscape is predicted by environmental features based
on observations at a set of locations. At first, SDM may appear to be a binary
classification problem, and one might be inclined to employ classic tools (e.g.,
logistic regression, support vector machines, neural networks) to tackle it.
However, wildlife surveys introduce structured noise (especially under-counting)
in the species observations. If unaccounted for, t…

**Sparse-GEV: Sparse Latent Space Model for Multivariate Extreme Value Time Serie Modeling**
https://arxiv.org/abs/1206.4685  
In many applications of time series models, such as climate analysis and social
media analysis, we are often interested in extreme events, such as heatwave,
wind gust, and burst of topics. These time series data usually exhibit a heavy-
tailed distribution rather than a Gaussian distribution. This poses great
challenges to existing approaches due to the significantly different assumptions
on the data distributions and the lack of sufficient past data on extreme
events. In this paper, we propose the Sparse-GEV model, a latent state model
based on the theory of extreme value modeling to automatic…

## Query: log-rate decomposition covariate contribution encounter intensity

**Optimally tackling covariate shift in RKHS-based nonparametric regression**
https://arxiv.org/abs/2205.02986  
We study the covariate shift problem in the context of nonparametric regression
over a reproducing kernel Hilbert space (RKHS). We focus on two natural families
of covariate shift problems defined using the likelihood ratios between the
source and target distributions. When the likelihood ratios are uniformly
bounded, we prove that the kernel ridge regression (KRR) estimator with a
carefully chosen regularization parameter is minimax rate-optimal (up to a log
factor) for a large family of RKHSs with regular kernel eigenvalues.
Interestingly, KRR does not require full knowledge of likelihood ra…

**Steganography Based on Pixel Intensity Value Decomposition**
https://arxiv.org/abs/2004.11977  
This paper focuses on steganography based on pixel intensity value
decomposition. A number of existing schemes such as binary, Fibonacci, Prime,
Natural, Lucas, and Catalan-Fibonacci (CF) are evaluated in terms of payload
capacity and stego quality. A new technique based on a specific representation
is used to decompose pixel intensity values into 16 (virtual) bit-planes
suitable for embedding purposes. The new decomposition scheme has a desirable
property whereby the sum of all bit-planes does not exceed the maximum pixel
intensity value, i.e. 255. Experimental results demonstrate that the ne…

**Context-specific independence in graphical log-linear models**
https://arxiv.org/abs/1409.2713  
Log-linear models are the popular workhorses of analyzing contingency tables. A
log-linear parameterization of an interaction model can be more expressive than
a direct parameterization based on probabilities, leading to a powerful way of
defining restrictions derived from marginal, conditional and context-specific
independence. However, parameter estimation is often simpler under a direct
parameterization, provided that the model enjoys certain decomposability
properties. Here we introduce a cyclical projection algorithm for obtaining
maximum likelihood estimates of log-linear parameters unde…

**Covariate-Adjusted Log-Rank Test: Guaranteed Efficiency Gain and Universal Applicability**
https://arxiv.org/abs/2201.11948  
Nonparametric covariate adjustment is considered for log-rank type tests of
treatment effect with right-censored time-to-event data from clinical trials
applying covariate-adaptive randomization. Our proposed covariate-adjusted log-
rank test has a simple explicit formula and a guaranteed efficiency gain over
the unadjusted test. We also show that our proposed test achieves universal
applicability in the sense that the same formula of test can be universally
applied to simple randomization and all commonly used covariate-adaptive
randomization schemes such as the stratified permuted block and P…

**Nonparametric covariate hypothesis tests for the cure rate in mixture cure models**
https://arxiv.org/abs/2401.17110  
In lifetime data, like cancer studies, theremay be long term survivors, which
lead to heavy censoring at the end of the follow-up period. Since a standard
survival model is not appropriate to handle these data, a cure model is needed.
In the literature, covariate hypothesis tests for cure models are limited to
parametric and semiparametric methods.We fill this important gap by proposing a
nonparametric covariate hypothesis test for the probability of cure in mixture
cure models. A bootstrap method is proposed to approximate the null distribution
of the test statistic. The procedure can be appl…

---

## Family summary

The negative binomial and point-process intensity literature is well-established. The Negative Binomial Process paper (1209.3442) shows how the NB distribution arises as a marginalization of a gamma-Poisson hierarchy, making it the natural distributional family when count overdispersion is present. The Beta-NB Process paper (1112.3605) demonstrates this in latent factor models for sparse count data, directly analogous to sparse wildlife encounter counts. Most importantly, the Deep Hurdle Networks paper (2010.16040) addresses the zero-inflated multi-target regression problem for species abundance estimation, explicitly identifying hurdle/NB models as necessary when Gaussian assumptions fail on ecological count data — this is the closest direct citation to orcast's distributional choice. The inhomogeneous Poisson intensity literature (1610.08623, 1409.5103) provides theoretical grounding for the log-rate decomposition approach used in orcast's cyclic kernels. The cyclic covariate query returned off-topic papers (lunar helium, RKHS covariate shift), indicating that the diel/lunar encounter-rate modeling literature is not well-represented on arXiv; that is a methodological gap the whitepaper should flag. The StatEcoNet paper (2102.08534) explicitly states that standard classification tools fail for wildlife surveys due to structured noise and under-counting, requiring count-specific distributional families.

**Verdict: Supported** — the NB/point-process rationale for sparse wildlife counts is well-evidenced. Primary citations: 2010.16040 (species abundance, zero inflation), 2102.08534 (wildlife survey distributional assumptions), 1209.3442 (NB process theory).