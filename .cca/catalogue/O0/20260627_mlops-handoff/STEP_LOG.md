# STEP_LOG, forecast ML-ops lane (newest last)

Two-to-four lines per step. Detail lives in the originating transcript
(`b67452d8-e353-4eb2-b95f-48cd71b286d6`); search by keyword, do not transcribe. Earlier steps
(S01-S09) are in `.cca/catalogue/O0/20260627_orcast-handoff/STEP_LOG.md`.

S10. FIX-CI completed and pushed: the committed `test_decision_records.py` imported an untracked
`conftest_governance.py`, and `test_community.py`/`test_sources.py` were stale vs shipped source.
Added the helper + aligned the tests; origin AWS Backend CI green (`c546a31`).

S11. MLM frontier parallel waves (`d4e6b06`): M-L0 closed (ROC AUC 0.879, d' 1.62 from a live
977-record confidence cache); M-TIDE harmonic model lifts tide phase coverage 0.42 to 1.00
(R^2 0.97 on NOAA predictions); M-L3 salmon lag scan added on the climatology placeholder
(withheld). Ladder: L0 PASS, L1 PASS, L2 FAIL, L3 WITHHELD.

S12. L2 follow-up (`70526ee`): resolved the S3 bucket (`...orcast-aws-backend-raw-payloads`,
us-west-2); integrated `HarmonicTidalPhase` into the local fit; refit against S3 with the upload
disabled. k_tide enters the joint fit but held-out skill -0.047, time-rescaling fails, confidence
0%. Plus the WILDLIFE source-research waveset + register.

S13. Multi-station experiment (`79f863b`): `modeling/studies/level2_multistation.py` combines the
production haro_strait stream with the cached OrcaHello index for 3 more nodes (memory store, no
prod write) + S3 harmonic tide. 4 stations, 2089 detections, all 4 kernels; held-out skill flips
POSITIVE +0.078 (4/5 folds). Still FAIL/0%: time-rescaling KS p=0.0 and cross-station kernels not
yet consistent (corr 0.14-0.34). First time the model beats climatology out of sample.

S14. 3d-twin lane split off and handed off to its own orchestrator
(`.cca/catalogue/O0/20260627_3d-twin/`, commits `54baa44`/`88849e1`), parked at the operator
decision gate. Then rotated this forecast ML-ops lane via the orchestrator-rotation skill (this
home).

## Open / next (for the receiving thread)

- M-L2 off 0%: ingest the 3 extra Orcasound nodes into the PRODUCTION acoustic_detections stream
  (the experiment used the cache), fix per-station effort/log E so time-rescaling passes, and lift
  cross-station kernel consistency. A passing gate + a recorded supervisor decision would then
  promote confidence (not before).
- M-L3: validate the Albion/DART parsers in `src/aws_backend/sources/salmon.py` for a real Chinook
  feed, then re-run the lag scan.
- Honor the write/promotion/refit-upload rules in HANDOFF_CHARTER section B.
