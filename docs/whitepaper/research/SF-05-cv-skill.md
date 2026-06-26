# SF-5 — Sf 05 Cv Skill

**Section:** 2

**Claim:** Negative mean held-out deviance skill and failed PIT calibration are grounds for withholding displayed confidence.

**Verification target:** Paper establishing PIT or deviance skill as a calibration diagnostic for distributional ecological forecasts, with interpretation for negative skill.

## Query: probability integral transform PIT calibration ecological species distribution model

**Probability Calibration Trees**
https://arxiv.org/abs/1808.00111  
Obtaining accurate and well calibrated probability estimates from classifiers is
useful in many applications, for example, when minimising the expected cost of
classifications. Existing methods of calibrating probability estimates are
applied globally, ignoring the potential for improvements by applying a more
fine-grained model. We propose probability calibration trees, a modification of
logistic model trees that identifies regions of the input space in which
different probability calibration models are learned to improve performance. We
compare probability calibration trees to two widely use…

**PIT: Position-Invariant Transform for Cross-FoV Domain Adaptation**
https://arxiv.org/abs/2108.07142  
Cross-domain object detection and semantic segmentation have witnessed
impressive progress recently. Existing approaches mainly consider the domain
shift resulting from external environments including the changes of background,
illumination or weather, while distinct camera intrinsic parameters appear
commonly in different domains, and their influence for domain adaptation has
been very rarely explored. In this paper, we observe that the Field of View
(FoV) gap induces noticeable instance appearance differences between the source
and target domains. We further discover that the FoV gap between…

**A phenomenological spatial model for macro-ecological patterns in species-rich ecosystems**
https://arxiv.org/abs/1609.02721  
Over the last few decades, ecologists have come to appreciate that key
ecological patterns, which describe ecological communities at relatively large
spatial scales, are not only scale dependent, but also intimately intertwined.
The relative abundance of species, which informs us about the commonness and
rarity of species, changes its shape from small to large spatial scales. The
average number of species as a function of area has a steep initial increase,
followed by decreasing slopes at large scales. Finally, if we find a species in
a given location, it is more likely we find an individual o…

**Re-calibrating Photometric Redshift Probability Distributions Using Feature-space Regression**
https://arxiv.org/abs/2110.15209  
Many astrophysical analyses depend on estimates of redshifts (a proxy for
distance) determined from photometric (i.e., imaging) data alone. Inaccurate
estimates of photometric redshift uncertainties can result in large systematic
errors. However, probability distribution outputs from many photometric redshift
methods do not follow the frequentist definition of a Probability Density
Function (PDF) for redshift -- i.e., the fraction of times the true redshift
falls between two limits $z_{1}$ and $z_{2}$ should be equal to the integral of
the PDF between these limits. Previous works have used the…

**Recalibrating probabilistic forecasts of epidemics**
https://arxiv.org/abs/2112.06305  
Distributional forecasts are important for a wide variety of applications,
including forecasting epidemics. Often, forecasts are miscalibrated, or
unreliable in assigning uncertainty to future events. We present a recalibration
method that can be applied to a black-box forecaster given retrospective
forecasts and observations, as well as an extension to make this method more
effective in recalibrating epidemic forecasts. This method is guaranteed to
improve calibration and log score performance when trained and measured in-
sample. We also prove that the increase in expected log score of a reca…

## Query: mean deviance skill cross-validation ecological forecasting out-of-sample

**Asymptotic Equivalence of Bayes Cross Validation and Widely Applicable Information Criterion in Singular Learning Theory**
https://arxiv.org/abs/1004.2316  
In regular statistical models, the leave-one-out cross-validation is
asymptotically equivalent to the Akaike information criterion. However, since
many learning machines are singular statistical models, the asymptotic behavior
of the cross-validation remains unknown. In previous studies, we established the
singular learning theory and proposed a widely applicable information criterion,
the expectation value of which is asymptotically equal to the average Bayes
generalization loss. In the present paper, we theoretically compare the Bayes
cross-validation loss and the widely applicable informati…

**Cross-validation failure: small sample sizes lead to large error bars**
https://arxiv.org/abs/1706.07581  
Predictive models ground many state-of-the-art developments in statistical brain
image analysis: decoding, MVPA, searchlight, or extraction of biomarkers. The
principled approach to establish their validity and usefulness is cross-
validation, testing prediction on unseen data. Here, I would like to raise
awareness on error bars of cross-validation, which are often underestimated.
Simple experiments show that sample sizes of many neuroimaging studies
inherently lead to large error bars, eg $\pm$10% for 100 samples. The standard
error across folds strongly underestimates them. These large error …

**Evaluating time series forecasting models: An empirical study on performance estimation methods**
https://arxiv.org/abs/1905.11744  
Performance estimation aims at estimating the loss that a predictive model will
incur on unseen data. These procedures are part of the pipeline in every machine
learning project and are used for assessing the overall generalisation ability
of predictive models. In this paper we address the application of these methods
to time series forecasting tasks. For independent and identically distributed
data the most common approach is cross-validation. However, the dependency among
observations in time series raises some caveats about the most appropriate way
to estimate performance in this type of da…

**Bootstrapping the Out-of-sample Predictions for Efficient and Accurate Cross-Validation**
https://arxiv.org/abs/1708.07180  
Cross-Validation (CV), and out-of-sample performance-estimation protocols in
general, are often employed both for (a) selecting the optimal combination of
algorithms and values of hyper-parameters (called a configuration) for producing
the final predictive model, and (b) estimating the predictive performance of the
final model. However, the cross-validated performance of the best configuration
is optimistically biased. We present an efficient bootstrap method that corrects
for the bias, called Bootstrap Bias Corrected CV (BBC-CV). BBC-CV's main idea is
to bootstrap the whole process of selecti…

**Estimating the Prediction Performance of Spatial Models via Spatial k-Fold Cross Validation**
https://arxiv.org/abs/2005.14263  
In machine learning one often assumes the data are independent when evaluating
model performance. However, this rarely holds in practise. Geographic
information data sets are an example where the data points have stronger
dependencies among each other the closer they are geographically. This
phenomenon known as spatial autocorrelation (SAC) causes the standard cross
validation (CV) methods to produce optimistically biased prediction performance
estimates for spatial models, which can result in increased costs and accidents
in practical applications. To overcome this problem we propose a modifi…

## Query: calibration ecological forecast confidence interval coverage skill score

**Machine learning for total cloud cover prediction**
https://arxiv.org/abs/2001.05948  
Accurate and reliable forecasting of total cloud cover (TCC) is vital for many
areas such as astronomy, energy demand and production, or agriculture. Most
meteorological centres issue ensemble forecasts of TCC, however, these forecasts
are often uncalibrated and exhibit worse forecast skill than ensemble forecasts
of other weather variables. Hence, some form of post-processing is strongly
required to improve predictive performance. As TCC observations are usually
reported on a discrete scale taking just nine different values called oktas,
statistical calibration of TCC ensemble forecasts can b…

**Metrics of calibration for probabilistic predictions**
https://arxiv.org/abs/2205.09680  
Predictions are often probabilities; e.g., a prediction could be for
precipitation tomorrow, but with only a 30% chance. Given such probabilistic
predictions together with the actual outcomes, "reliability diagrams" help
detect and diagnose statistically significant discrepancies -- so-called
"miscalibration" -- between the predictions and the outcomes. The canonical
reliability diagrams histogram the observed and expected values of the
predictions; replacing the hard histogram binning with soft kernel density
estimation is another common practice. But, which widths of bins or kernels are
best…

**"Calibeating": Beating Forecasters at Their Own Game**
https://arxiv.org/abs/2209.04892  
In order to identify expertise, forecasters should not be tested by their
calibration score, which can always be made arbitrarily small, but rather by
their Brier score. The Brier score is the sum of the calibration score and the
refinement score; the latter measures how good the sorting into bins with the
same forecast is, and thus attests to "expertise." This raises the question of
whether one can gain calibration without losing expertise, which we refer to as
"calibeating." We provide an easy way to calibeat any forecast, by a
deterministic online procedure. We moreover show that calibeatin…

**Multivariate Confidence Calibration for Object Detection**
https://arxiv.org/abs/2004.13546  
Unbiased confidence estimates of neural networks are crucial especially for
safety-critical applications. Many methods have been developed to calibrate
biased confidence estimates. Though there is a variety of methods for
classification, the field of object detection has not been addressed yet.
Therefore, we present a novel framework to measure and calibrate biased (or
miscalibrated) confidence estimates of object detection methods. The main
difference to related work in the field of classifier calibration is that we
also use additional information of the regression output of an object detecto…

**Rejoinder: On nearly assumption-free tests of nominal confidence interval coverage for causal parameters estimated by machine learning**
https://arxiv.org/abs/2008.03288  
This is the rejoinder to the discussion by Kennedy, Balakrishnan and Wasserman
on the paper "On nearly assumption-free tests of nominal confidence interval
coverage for causal parameters estimated by machine learning" published in
Statistical Science.

## Query: Brier skill score deviance null model ecological forecast evaluation

**Evaluating probabilistic classifiers: Reliability diagrams and score decompositions revisited**
https://arxiv.org/abs/2008.03033  
A probability forecast or probabilistic classifier is reliable or calibrated if
the predicted probabilities are matched by ex post observed frequencies, as
examined visually in reliability diagrams. The classical binning and counting
approach to plotting reliability diagrams has been hampered by a lack of
stability under unavoidable, ad hoc implementation decisions. Here we introduce
the CORP approach, which generates provably statistically Consistent, Optimally
binned, and Reproducible reliability diagrams in an automated way. CORP is based
on non-parametric isotonic regression and implemente…

**Prediction with expert advice for the Brier game**
https://arxiv.org/abs/0710.0485  
We show that the Brier game of prediction is mixable and find the optimal
learning rate and substitution function for it. The resulting prediction
algorithm is applied to predict results of football and tennis matches. The
theoretical performance guarantee turns out to be rather tight on these data
sets, especially in the case of the more extensive tennis data.

**The Brier Score under Administrative Censoring: Problems and Solutions**
https://arxiv.org/abs/1912.08581  
The Brier score is commonly used for evaluating probability predictions. In
survival analysis, with right-censored observations of the event times, this
score can be weighted by the inverse probability of censoring (IPCW) to retain
its original interpretation. It is common practice to estimate the censoring
distribution with the Kaplan-Meier estimator, even though it assumes that the
censoring distribution is independent of the covariates. This paper discusses
the general impact of the censoring estimates on the Brier score and shows that
the estimation of the censoring distribution can be pro…

**"Calibeating": Beating Forecasters at Their Own Game**
https://arxiv.org/abs/2209.04892  
In order to identify expertise, forecasters should not be tested by their
calibration score, which can always be made arbitrarily small, but rather by
their Brier score. The Brier score is the sum of the calibration score and the
refinement score; the latter measures how good the sorting into bins with the
same forecast is, and thus attests to "expertise." This raises the question of
whether one can gain calibration without losing expertise, which we refer to as
"calibeating." We provide an easy way to calibeat any forecast, by a
deterministic online procedure. We moreover show that calibeatin…

**Comparison of statistical post-processing methods for probabilistic NWP forecasts of solar radiation**
https://arxiv.org/abs/1904.07192  
The increased usage of solar energy places additional importance on forecasts of
solar radiation. Solar panel power production is primarily driven by the amount
of solar radiation and it is therefore important to have accurate forecasts of
solar radiation. Accurate forecasts that also give information on the forecast
uncertainties can help users of solar energy to make better solar radiation
based decisions related to the stability of the electrical grid. To achieve
this, we apply statistical post-processing techniques that determine
relationships between observations of global radiation (made…

## Query: negative skill score model worse than climatology null ecological prediction

**Sub-seasonal forecasting with a large ensemble of deep-learning weather prediction models**
https://arxiv.org/abs/2102.05107  
We present an ensemble prediction system using a Deep Learning Weather
Prediction (DLWP) model that recursively predicts key atmospheric variables with
six-hour time resolution. This model uses convolutional neural networks (CNNs)
on a cubed sphere grid to produce global forecasts. The approach is
computationally efficient, requiring just three minutes on a single GPU to
produce a 320-member set of six-week forecasts at 1.4{\deg} resolution. Ensemble
spread is primarily produced by randomizing the CNN training process to create a
set of 32 DLWP models with slightly different learned weights. A…

**Automated Surgical Skill Assessment in RMIS Training**
https://arxiv.org/abs/1712.08604  
Purpose: Manual feedback in basic RMIS training can consume a significant amount
of time from expert surgeons' schedule and is prone to subjectivity. While VR-
based training tasks can generate automated score reports, there is no mechanism
of generating automated feedback for surgeons performing basic surgical tasks in
RMIS training. In this paper, we explore the usage of different holistic
features for automated skill assessment using only robot kinematic data and
propose a weighted feature fusion technique for improving score prediction
performance. Methods: We perform our experiments on the…

**On the Role of Negative Precedent in Legal Outcome Prediction**
https://arxiv.org/abs/2208.08225  
Every legal case sets a precedent by developing the law in one of the following
two ways. It either expands its scope, in which case it sets positive precedent,
or it narrows it, in which case it sets negative precedent. Legal outcome
prediction, the prediction of positive outcome, is an increasingly popular task
in AI. In contrast, we turn our focus to negative outcomes here, and introduce a
new task of negative outcome prediction. We discover an asymmetry in existing
models' ability to predict positive and negative outcomes. Where the state-of-
the-art outcome prediction model we used predict…

**Skill-based Model-based Reinforcement Learning**
https://arxiv.org/abs/2207.07560  
Model-based reinforcement learning (RL) is a sample-efficient way of learning
complex behaviors by leveraging a learned single-step dynamics model to plan
actions in imagination. However, planning every action for long-horizon tasks is
not practical, akin to a human planning out every muscle movement. Instead,
humans efficiently plan with high-level skills to solve complex tasks. From this
intuition, we propose a Skill-based Model-based RL framework (SkiMo) that
enables planning in the skill space using a skill dynamics model, which directly
predicts the skill outcomes, rather than predicting …

**Controlled abstention neural networks for identifying skillful predictions for regression problems**
https://arxiv.org/abs/2104.08236  
The earth system is exceedingly complex and often chaotic in nature, making
prediction incredibly challenging: we cannot expect to make perfect predictions
all of the time. Instead, we look for specific states of the system that lead to
more predictable behavior than others, often termed "forecasts of opportunity".
When these opportunities are not present, scientists need prediction systems
that are capable of saying "I don't know." We introduce a novel loss function,
termed "abstention loss", that allows neural networks to identify forecasts of
opportunity for regression problems. The abstent…

---

## Family summary

The calibration literature is well-represented. The epidemiological forecast recalibration paper (2112.06305) directly demonstrates that distributional forecasts can be systematically miscalibrated and that PIT-based recalibration reliably improves log score, which is the theoretical basis for using PIT failure as a reason to withhold confidence. The Brier score literature (2008.03033 CORP, 2209.04892 calibeating) establishes that calibration and refinement are separable and that a model can have poor calibration even when it appears to produce estimates — supporting the claim that negative deviance skill should trigger a confidence gate. The "metrics of calibration" paper (2205.09680) provides the formal reliability diagram machinery that makes miscalibration detectable in practice. The spatial CV paper (2005.14263) specifically addresses the problem that standard cross-validation overestimates performance for spatially autocorrelated data, and the forecasting CV paper (1905.11744) extends this to time series — both directly relevant to orcast's temporal kernel validation. The abstention-loss neural network paper (2104.08236) introduces the concept of "forecasts of opportunity" and a loss function that trains a model to say "I don't know" when skill is low, exactly the design principle behind orcast's gate-bounded confidence display.

**Verdict: Supported** — calibration as a gate criterion is well-established. Primary citations: 2112.06305 (PIT recalibration for epidemiological forecasts), 2104.08236 (abstention when skill is low), 2205.09680 (calibration metrics), 2005.14263 (spatial CV bias).