# 2. A gate-bounded honesty model

The orcast gate policy operationalizes a specific claim: a forecast can be shown with confidence proportional to the statistical evidence that supports it, without hiding the forecast when evidence is weak. This section describes the distributional choice, the gate battery, and the confidence bounding mechanism.

## Distributional family

Encounter counts are sparse, overdispersed, and zero-inflated. Gaussian models underestimate zero-inflation and are miscalibrated for count data at this density. Negative binomial and Poisson point-process intensity models are the appropriate distributional family. The negative binomial process literature establishes this theoretically: the NB distribution arises as a gamma-Poisson marginalization and provides two free parameters to capture both overdispersion and count-level random effects \cite{arxiv111203605}. For species abundance estimation, hurdle and NB models are required when Gaussian assumptions fail on ecological count data \cite{arxiv201016040}. Species distribution modeling frameworks for wildlife surveys explicitly identify structured noise and under-counting as reasons that standard classifiers fail and count-specific distributional families are required \cite{arxiv210208534}.

The orcast kernel model (described in the methodology of record \cite{methodology}) uses log-linear intensity in the form of equation (E1), decomposing the log encounter rate into a baseline plus additive cyclic kernel contributions from diel, lunar, and seasonal covariates.

## Null gating

Each fitted cyclic kernel must beat a phase-shuffled null before it is allowed to contribute to displayed confidence. The phase-shuffled null generates a reference distribution by permuting the assignment of detection times to stimulus phases, preserving the marginal detection rate while destroying any phase relationship. The observed kernel amplitude is compared to the shuffle distribution; a p-value above a threshold means the kernel provides no reliable signal.

The mathematical foundation is established in point-process neuroscience. Point process models for spike trains \cite{arxiv201004875} and the microscopic approach to time-elapsed neural models \cite{arxiv150602361} both use exactly this Poisson-process machinery with phase-structured null comparisons. The time-rescaling goodness-of-fit test uses the compensator transformation to produce residuals that should be exponentially distributed if the model fits \cite{arxiv160603988}; a Kolmogorov-Smirnov test on these residuals is the second gate component.

An open measurement gap (C-2) is that this methodology is documented in applied neuroscience and statistical literature rather than cetacean ecological literature on arXiv. The whitepaper cites the methodological precedents and notes the gap.

## CV skill and calibration

Gates L2 and L3 in the leveled fitness program require positive held-out deviance skill and PIT calibration. The deviance skill score, equation (E5), measures whether the model is sharper than a climatology null on held-out data. Negative skill means the model is less predictive than the null and displayed confidence must be withheld. The epidemiological forecast calibration literature establishes that PIT-based recalibration reliably improves log score and that miscalibrated distributional forecasts should be held back from high-stakes decisions \cite{arxiv211206305}. The abstention loss framework \cite{arxiv210408236} formalizes the principle that a predictive system should say it does not know when skill is low, which is the design intent of the gate policy. Spatial and temporal cross-validation must account for autocorrelation; standard CV overestimates performance for geospatial data \cite{arxiv200514263}, and time-series CV requires blocking by temporal structure \cite{arxiv190511744}.

## Effective confidence gate

The effective confidence displayed on every surface is bounded by the product of gate outcomes. If any gate fails, effective confidence is reduced, and the failing integrity condition is shown alongside the metric. The gate is not a visibility switch; the forecast is always shown. This separation between gate-bounded confidence and forecast presence is the core design choice that differentiates orcast from systems that suppress low-confidence outputs.
