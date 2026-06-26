# 3. Acoustic grounding: PSTH and Level 0 QC

Passive acoustic monitoring is the primary temporal instrument in orcast because acoustic detectors run continuously and their effort does not track human activity cycles. This makes them suitable for fitting temporal kernels without the effort-confounding that affects visual sightings.

The central instrument in the pilot is the OrcaHello hydrophone network at Haro Strait, which produces acoustic candidate detections from an ML classifier. These candidates are the raw data for the temporal kernel fits. Before any detection can enter a model fit or influence a displayed confidence score, it must pass through explicit Level 0 QC quarantine.

## Peristimulus time histogram kernel estimation

The PSTH method aligns detections to a repeating stimulus onset, diel sunrise, flood-current onset, lunar new moon, and bins by phase. The binned counts, divided by station effort and smoothed with a periodic spline, produce a first kernel estimate. The neuroscience literature establishes the theoretical basis: the hydrophone is a detector unit, the detection times are the spike train, and the environmental cycles are the stimulus. The Poisson point-process machinery developed for sensory neuroscience \cite{arxiv201004875,arxiv150602361} applies directly to this setting.

## False-positive rates and quarantine

Deep learning bioacoustic classifiers deployed in the field exhibit non-trivial false-positive rates. The comprehensive review of computational bioacoustics \cite{arxiv211206725} documents this as a known, widespread problem: performance degrades in field conditions relative to held-out test sets, and variance across noise conditions remains high. The North Atlantic right whale upcall detector \cite{arxiv200109127} demonstrates this concretely for a marine mammal application: a ResNet classifier trained on thousands of examples achieves high test accuracy but requires careful validation under variable acoustic conditions before field deployment. Robust sound event detection in bioacoustic networks \cite{arxiv190508352} characterizes the variability in ambient noise as the primary driver of detection unreliability across sensors.

For orcast, the consequence is that unreviewed OrcaHello candidates cannot enter a model fit directly. The platform enforces a Level 0 QC gate: candidates are quarantined in a separate data stream, and the integrity condition exposed alongside every confidence-bearing surface reports explicitly that the acoustic data underlying the temporal kernels consists of unreviewed candidates with known false-positive rates. The effective confidence gate (Section 2) prevents confidence from rising above a threshold while this condition holds.

This is not a deficit of the data source; it is an honest accounting of the evidence available at pilot scale. The integrity condition is part of the forecast, not a reason to hide it.
