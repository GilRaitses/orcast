"""Run the MLM study ladder (Levels 0-3) and print the gate ladder.

Each level reports an honest status (pass / fail / withheld / insufficient_data) and writes a
report under modeling/studies/reports/. The ladder is informational: per
CALIBRATION_STUDIES.md a level must pass before the next is built, so the first non-pass is
the current frontier. No confidence is promoted here.

Usage: python -m modeling.studies.run_studies   (from repo root)
"""
from __future__ import annotations

import sys

from . import level0_detector, level1_psth, level2_joint, level3_prey_space
from .common import GATE_PASS, write_report


def main() -> int:
    levels = [level0_detector, level1_psth, level2_joint, level3_prey_space]
    print("MLM study ladder (docs/methodology/CALIBRATION_STUDIES.md)\n")
    frontier_marked = False
    for mod in levels:
        res = mod.run()
        write_report(res)
        mark = ""
        if not frontier_marked and res.status != GATE_PASS:
            mark = "   <- current frontier (build stops here until it passes)"
            frontier_marked = True
        print(f"L{res.level} {res.name:16s} [{res.status}]{mark}")
        print(f"    {res.reason}")
    print("\nReports written to modeling/studies/reports/. Effective confidence unchanged (gates govern promotion).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
