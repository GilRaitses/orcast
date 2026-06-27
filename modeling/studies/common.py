"""Shared loaders, the gate contract, and report writing for MLM studies.

Pure stdlib. Reuses the cached OrcaHello index and the CAND candidate set produced by the
forecast-candidate waveset, so the studies run without hitting the intermittent OrcaHello
API. All math (phases, permutation null, rank-AUC) is implemented here without numpy.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]
CAND_HOME = REPO / ".cca" / "catalogue" / "O0" / "20260627_forecast-candidates"
ORCAHELLO_CACHE = CAND_HOME / "orcahello_index.cache.json"
CANDIDATES = CAND_HOME / "candidates.targets.json"
REPORTS_DIR = Path(__file__).resolve().parent / "reports"
FIT_REPORT = REPO / "data" / "models" / "fit_report.json"

# In-region hydrophone coordinates (match the CAND waveset and Orcasound catalog).
STATION_COORDS: Dict[str, Tuple[float, float]] = {
    "orcasound_lab": (48.5583362, -123.1735774),
    "north_san_juan_channel": (48.591294, -123.058779),
    "andrews_bay": (48.5500299, -123.1666492),
    "haro_strait": (48.516, -123.152),
}

GATE_PASS = "pass"
GATE_FAIL = "fail"
GATE_WITHHELD = "withheld"  # method valid, data coverage insufficient
GATE_INSUFFICIENT = "insufficient_data"  # not enough records to run at all


@dataclass
class GateResult:
    level: int
    name: str
    status: str
    metrics: Dict[str, object] = field(default_factory=dict)
    reason: str = ""

    def passed(self) -> bool:
        return self.status == GATE_PASS


def parse_dt(value: object) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        s = value.strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(s)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def load_orcahello_index() -> List[Dict[str, object]]:
    """Return cached OrcaHello records as [{t: datetime, key, outcome}]."""
    if not ORCAHELLO_CACHE.exists():
        return []
    try:
        raw = json.loads(ORCAHELLO_CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out: List[Dict[str, object]] = []
    for row in raw.get("records", []):
        ts = parse_dt(row.get("t"))
        if ts is None:
            continue
        out.append({"t": ts, "key": str(row.get("key", "")), "outcome": str(row.get("outcome", "unreviewed"))})
    return out


def load_candidates() -> List[Dict[str, object]]:
    if not CANDIDATES.exists():
        return []
    try:
        return json.loads(CANDIDATES.read_text(encoding="utf-8")).get("candidates", [])
    except (OSError, ValueError):
        return []


def load_fit_report() -> Optional[Dict[str, object]]:
    if not FIT_REPORT.exists():
        return None
    try:
        return json.loads(FIT_REPORT.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def diel_phase(dt: datetime, lng: float) -> float:
    """Local mean-solar day fraction in [0,1). Matches src/aws_backend/covariates.py."""
    minutes_utc = dt.hour * 60 + dt.minute + dt.second / 60.0
    return ((minutes_utc + 4.0 * lng) % 1440.0) / 1440.0


def lunar_phase(dt: datetime) -> float:
    """Moon phase in [0,1) (0 new, 0.5 full). Mean-synodic-month approximation."""
    # Julian day
    a = (14 - dt.month) // 12
    y = dt.year + 4800 - a
    m = dt.month + 12 * a - 3
    jdn = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    jd = jdn + (dt.hour - 12) / 24.0 + dt.minute / 1440.0
    synodic = 29.53058867
    new_moon_epoch = 2451550.1
    return ((jd - new_moon_epoch) % synodic) / synodic


def span_days(times: List[datetime]) -> float:
    if len(times) < 2:
        return 0.0
    return (max(times) - min(times)).total_seconds() / 86400.0


def write_report(result: GateResult) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"level{result.level}_{result.name}.json"
    payload = asdict(result)
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def binned_rate(phases: List[float], n_bins: int) -> List[int]:
    counts = [0] * n_bins
    for p in phases:
        idx = min(n_bins - 1, int(p * n_bins))
        counts[idx] += 1
    return counts


def modulation_index(counts: List[int]) -> float:
    """Peak-to-mean modulation of a binned rate; 0 means flat."""
    if not counts:
        return 0.0
    mean = sum(counts) / len(counts)
    if mean <= 0:
        return 0.0
    return (max(counts) - mean) / mean
