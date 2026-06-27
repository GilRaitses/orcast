"""MLM covariate-modeling studies (Levels 0-3).

Each level is a go/no-go on held-out data per docs/methodology/CALIBRATION_STUDIES.md.
Pure stdlib so the ladder runs in any environment. Studies degrade to insufficient_data
or withheld rather than crash, and never promote confidence without a passing gate.
"""
