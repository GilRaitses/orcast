"""M-L0: instrument characterization.

Per CALIBRATION_STUDIES.md Level 0: know the detector and the effort before modeling
presence. Computes per-station effort (record counts + temporal span) and the OrcaHello
detector outcome mix (confirmed / false_positive / unreviewed) from the cached index.

Honesty: full detector ROC AUC needs per-detection confidence scores paired with labels.
The base cached index does not carry confidence, so this study reads an auxiliary
confidence cache when present; otherwise the ROC portion stays `withheld`.
"""
from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Dict, List, Optional, Sequence, Tuple

from .common import (
    GATE_INSUFFICIENT,
    GATE_PASS,
    GATE_WITHHELD,
    CAND_HOME,
    GateResult,
    load_orcahello_index,
    parse_dt,
    span_days,
    write_report,
)

CONFIDENCE_CACHE = CAND_HOME / "orcahello_index.confidence.cache.json"


def _load_confidence_pairs() -> List[Tuple[str, bool, float]]:
    """Return [(station_key, is_confirmed, confidence)] from the confidence cache."""
    if not CONFIDENCE_CACHE.exists():
        return []
    try:
        raw = json.loads(CONFIDENCE_CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []

    pairs: List[Tuple[str, bool, float]] = []
    for row in raw.get("records", []):
        if not isinstance(row, dict):
            continue
        # Keep timestamp parse as a basic schema guard; skip unparseable rows.
        if parse_dt(row.get("t")) is None:
            continue
        outcome = str(row.get("outcome", "")).strip().lower()
        if outcome not in {"confirmed", "false_positive"}:
            continue
        confidence_raw = row.get("confidence")
        try:
            confidence = float(confidence_raw)
        except (TypeError, ValueError):
            continue
        confidence = max(0.0, min(1.0, confidence))
        key = str(row.get("key", "")).strip() or "unknown"
        pairs.append((key, outcome == "confirmed", confidence))
    return pairs


def _auc_from_scores(scores: Sequence[float], labels: Sequence[bool]) -> Optional[float]:
    """Mann-Whitney/rank AUC with average ranks for ties."""
    n = len(scores)
    if n == 0 or n != len(labels):
        return None
    n_pos = sum(1 for y in labels if y)
    n_neg = n - n_pos
    if n_pos == 0 or n_neg == 0:
        return None

    pairs = sorted(zip(scores, labels), key=lambda item: item[0])
    rank = 1
    sum_ranks_positive = 0.0
    i = 0
    while i < n:
        j = i + 1
        while j < n and pairs[j][0] == pairs[i][0]:
            j += 1
        tie_count = j - i
        avg_rank = (2 * rank + tie_count - 1) / 2.0
        pos_in_tie = sum(1 for _, y in pairs[i:j] if y)
        sum_ranks_positive += avg_rank * pos_in_tie
        rank += tie_count
        i = j

    auc = (sum_ranks_positive - (n_pos * (n_pos + 1) / 2.0)) / (n_pos * n_neg)
    return max(0.0, min(1.0, auc))


def _quantile(sorted_values: Sequence[float], q: float) -> float:
    if not sorted_values:
        return float("nan")
    if q <= 0:
        return sorted_values[0]
    if q >= 1:
        return sorted_values[-1]
    pos = (len(sorted_values) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return sorted_values[lo]
    frac = pos - lo
    return sorted_values[lo] * (1.0 - frac) + sorted_values[hi] * frac


def _bootstrap_auc_ci(
    pos_scores: Sequence[float],
    neg_scores: Sequence[float],
    n_boot: int = 1000,
    seed: int = 20260627,
) -> Optional[Tuple[float, float]]:
    if not pos_scores or not neg_scores:
        return None
    rng = random.Random(seed)
    aucs: List[float] = []
    n_pos = len(pos_scores)
    n_neg = len(neg_scores)
    for _ in range(n_boot):
        boot_pos = [pos_scores[rng.randrange(n_pos)] for _ in range(n_pos)]
        boot_neg = [neg_scores[rng.randrange(n_neg)] for _ in range(n_neg)]
        scores = boot_pos + boot_neg
        labels = [True] * n_pos + [False] * n_neg
        auc = _auc_from_scores(scores, labels)
        if auc is not None:
            aucs.append(auc)
    if not aucs:
        return None
    aucs.sort()
    return _quantile(aucs, 0.025), _quantile(aucs, 0.975)


def _inv_norm_cdf(p: float) -> float:
    """Acklam rational approximation of N(0,1)^-1, pure stdlib."""
    if p <= 0.0:
        return float("-inf")
    if p >= 1.0:
        return float("inf")
    a = [
        -3.969683028665376e01,
        2.209460984245205e02,
        -2.759285104469687e02,
        1.383577518672690e02,
        -3.066479806614716e01,
        2.506628277459239e00,
    ]
    b = [
        -5.447609879822406e01,
        1.615858368580409e02,
        -1.556989798598866e02,
        6.680131188771972e01,
        -1.328068155288572e01,
    ]
    c = [
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e00,
        -2.549732539343734e00,
        4.374664141464968e00,
        2.938163982698783e00,
    ]
    d = [
        7.784695709041462e-03,
        3.224671290700398e-01,
        2.445134137142996e00,
        3.754408661907416e00,
    ]
    p_low = 0.02425
    p_high = 1.0 - p_low
    if p < p_low:
        q = math.sqrt(-2.0 * math.log(p))
        x = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
        )
    elif p <= p_high:
        q = p - 0.5
        r = q * q
        x = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (
            (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0)
        )
    else:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        x = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0)
        )
    return x


def _d_prime(pos_scores: Sequence[float], neg_scores: Sequence[float], threshold: float) -> Optional[float]:
    n_pos = len(pos_scores)
    n_neg = len(neg_scores)
    if n_pos == 0 or n_neg == 0:
        return None
    hits = sum(1 for s in pos_scores if s >= threshold)
    fas = sum(1 for s in neg_scores if s >= threshold)
    # Log-linear correction avoids infinite z at rates 0 or 1.
    hit_rate = (hits + 0.5) / (n_pos + 1.0)
    fa_rate = (fas + 0.5) / (n_neg + 1.0)
    return _inv_norm_cdf(hit_rate) - _inv_norm_cdf(fa_rate)


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
    confidence_pairs = _load_confidence_pairs()
    pos_scores = [score for _key, is_pos, score in confidence_pairs if is_pos]
    neg_scores = [score for _key, is_pos, score in confidence_pairs if not is_pos]
    auc = _auc_from_scores(pos_scores + neg_scores, [True] * len(pos_scores) + [False] * len(neg_scores))
    auc_ci = _bootstrap_auc_ci(pos_scores, neg_scores, n_boot=1000) if auc is not None else None
    threshold = median(pos_scores + neg_scores) if (pos_scores or neg_scores) else None
    d_prime_value = _d_prime(pos_scores, neg_scores, threshold) if (auc is not None and threshold is not None) else None

    metrics = {
        "stations": len(by_station),
        "total_records": len(records),
        "per_station_effort": effort,
        "detector_precision_overall": precision,
        "confidence_cache_path": str(CONFIDENCE_CACHE.relative_to(Path(__file__).resolve().parents[2])),
        "confidence_pairs_total": len(confidence_pairs),
        "confidence_pairs_confirmed": len(pos_scores),
        "confidence_pairs_false_positive": len(neg_scores),
        "roc_auc": round(auc, 6) if auc is not None else None,
        "roc_auc_ci95": [round(auc_ci[0], 6), round(auc_ci[1], 6)] if auc_ci else None,
        "roc_bootstrap_samples": 1000 if auc_ci else 0,
        "roc_status": (
            "computed: confidence cache paired with confirmed/false_positive labels"
            if auc is not None and auc_ci is not None
            else "withheld: needs per-detection confidence scores paired with labels (not in cached index)"
        ),
        "d_prime": round(d_prime_value, 6) if d_prime_value is not None else None,
        "d_prime_threshold": round(threshold, 6) if threshold is not None else None,
        "d_prime_threshold_rule": "median confidence of confirmed+false_positive rows; score >= threshold counts as detector-positive",
    }

    # Level 0 gate is pass only when per-station effort is known and ROC AUC has a CI.
    if auc is None or auc_ci is None:
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
    return GateResult(
        level=0,
        name="detector",
        status=GATE_PASS,
        metrics=metrics,
        reason="Per-station effort is known and detector ROC AUC is reported with a bootstrap 95% CI.",
    )


if __name__ == "__main__":
    res = run()
    path = write_report(res)
    print(f"M-L0 detector: {res.status} ({res.metrics.get('total_records')} records, "
          f"{res.metrics.get('stations')} stations) -> {path}")
    print(f"  {res.reason}")
