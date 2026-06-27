"""M-L0: instrument characterization.

Per CALIBRATION_STUDIES.md Level 0: know the detector and the effort before modeling
presence. Computes per-station effort (record counts + temporal span) and the OrcaHello
detector outcome mix (confirmed / false_positive / unreviewed) from the cached index.

Honesty: full detector ROC AUC needs per-detection confidence scores paired with labels,
which the cached index does not carry. That portion is reported `withheld` with the reason,
so the gate does not claim a characterization it cannot compute here.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from .common import (
    GATE_INSUFFICIENT,
    GATE_PASS,
    GATE_WITHHELD,
    GateResult,
    load_orcahello_index,
    span_days,
    write_report,
)


def run() -> GateResult:
    records = load_orcahello_index()
    if not records:
        return GateResult(
            level=0,
            name="detector",
            status=GATE_INSUFFICIENT,
            reason="No cached OrcaHello index. Run the CAND build (live) to populate it.",
        )

    by_station: Dict[str, List] = defaultdict(list)
    outcomes: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in records:
        key = str(r["key"])
        by_station[key].append(r["t"])
        outcomes[key][str(r["outcome"])] += 1

    effort = {}
    total_confirmed = total_false_pos = total_reviewed = 0
    for key, times in by_station.items():
        o = outcomes[key]
        confirmed = o.get("confirmed", 0)
        false_pos = o.get("false_positive", 0)
        reviewed = confirmed + false_pos
        total_confirmed += confirmed
        total_false_pos += false_pos
        total_reviewed += reviewed
        effort[key] = {
            "records": len(times),
            "span_days": round(span_days(times), 1),
            "confirmed": confirmed,
            "false_positive": false_pos,
            "unreviewed": o.get("unreviewed", 0),
            "precision": round(confirmed / reviewed, 4) if reviewed else None,
        }

    precision = round(total_confirmed / total_reviewed, 4) if total_reviewed else None
    metrics = {
        "stations": len(by_station),
        "total_records": len(records),
        "per_station_effort": effort,
        "detector_precision_overall": precision,
        "roc_auc": None,
        "roc_status": "withheld: needs per-detection confidence scores paired with labels (not in cached index)",
    }

    # Effort series are known per station. ROC AUC is withheld, so the Level 0 gate as
    # defined (effort known AND ROC AUC reported) is partially met -> withheld overall.
    if total_reviewed == 0:
        return GateResult(
            level=0,
            name="detector",
            status=GATE_WITHHELD,
            metrics=metrics,
            reason="Per-station effort computed, but no reviewed labels in cache to characterize the detector.",
        )
    return GateResult(
        level=0,
        name="detector",
        status=GATE_WITHHELD,
        metrics=metrics,
        reason=(
            "Per-station effort and detector precision computed; ROC AUC withheld until the "
            "confidence-scored detection feed is paired with labels. Effort portion is satisfied."
        ),
    )


if __name__ == "__main__":
    res = run()
    path = write_report(res)
    print(f"M-L0 detector: {res.status} ({res.metrics.get('total_records')} records, "
          f"{res.metrics.get('stations')} stations) -> {path}")
    print(f"  {res.reason}")
