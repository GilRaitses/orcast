"""Source readers for the tagtools studio.

Inputs are the REAL DTAG products from the operator's whale-behavior-analysis
repo (humpback mn09_203a, contrast/reference only). The h5 itself is a heavy
asset that lives in the box; this loader consumes the two committed CSV products
(raw sensor + expert annotation log) and the flat schema, so the pipeline is
reproducible offline without the R runtime or the full h5.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

# Default location of the real source data. Overridable via env so the bake is
# reproducible on any host that has re-fetched the box asset.
DEFAULT_SOURCE_ROOT = os.environ.get(
    "BSS_DTAG_SOURCE_ROOT",
    str(Path.home() / "whale-behavior-analysis"),
)

SENSOR_CSV_REL = "Visualization_Poster_Appendix/data/mn09_203a.csv"
LOG_CSV_REL = "Visualization_Poster_Appendix/data/log_mn09_203a.csv"

# License cleared by O0: humpback DTAG mn09_203a is CC-BY-NC, covered by the
# SIGN_OFF NC authorization (decision 1). Non-commercial use only.
LICENSE = "CC-BY-NC-4.0"
LICENSE_STATUS = "CC-BY-NC-4.0, non-commercial, authorized per O0 SIGN_OFF decision 1"
ATTRIBUTION = (
    "Humpback DTAG mn09_203a, whale-behavior-analysis dataset. "
    "Non-commercial use under CC-BY-NC, authorized by O0 SIGN_OFF decision 1."
)
SOURCE_POINTER = (
    "whale-behavior-analysis/Visualization_Poster_Appendix/data/dive_analysis.h5"
)

# Column order in the raw sensor CSV (verified against the file header).
SENSOR_COLUMNS = [
    "s", "fs", "p", "tempr",
    "M.1", "M.2", "M.3",
    "A.1", "A.2", "A.3",
    "Aw.1", "Aw.2", "Aw.3",
    "Mw.1", "Mw.2", "Mw.3",
    "pitch", "roll", "head",
]


@dataclass
class SensorData:
    """Real DTAG sensor time series for one tag deployment."""

    deployment_id: str
    sample_rate_hz: float
    n_samples: int
    columns: Dict[str, np.ndarray]
    source_path: str

    def col(self, name: str) -> np.ndarray:
        return self.columns[name]

    @property
    def depth_m(self) -> np.ndarray:
        # Pressure in dbar is ~1:1 with depth in meters for these shallow dives.
        return self.columns["p"]

    @property
    def whale_frame_accel(self) -> np.ndarray:
        return np.stack(
            [self.columns["Aw.1"], self.columns["Aw.2"], self.columns["Aw.3"]],
            axis=1,
        )


@dataclass
class ExpertAnnotation:
    whale_id: str
    whale_name: str
    sample_hz: int
    event_start: int
    event_end: int
    state: str
    event: str


@dataclass
class SourceBundle:
    sensor: SensorData
    annotations: List[ExpertAnnotation]
    source_root: str
    provenance: Dict[str, str] = field(default_factory=dict)


def _resolve(source_root: Optional[str], rel: str) -> Path:
    root = Path(source_root or DEFAULT_SOURCE_ROOT)
    return root / rel


def load_sensor_csv(source_root: Optional[str] = None) -> SensorData:
    path = _resolve(source_root, SENSOR_CSV_REL)
    if not path.exists():
        raise FileNotFoundError(
            f"sensor CSV not found at {path}. Set BSS_DTAG_SOURCE_ROOT or re-fetch "
            f"the boxed DTAG asset (see infra/tagtools/BOX_MANIFEST.md)."
        )
    raw = np.loadtxt(path, delimiter=",", skiprows=1)
    columns = {name: raw[:, i] for i, name in enumerate(SENSOR_COLUMNS)}
    fs = float(columns["fs"][0]) if columns["fs"].size else 5.0
    deployment_id = path.stem
    return SensorData(
        deployment_id=deployment_id,
        sample_rate_hz=fs,
        n_samples=int(raw.shape[0]),
        columns=columns,
        source_path=str(path),
    )


def load_annotations_csv(source_root: Optional[str] = None) -> List[ExpertAnnotation]:
    path = _resolve(source_root, LOG_CSV_REL)
    if not path.exists():
        raise FileNotFoundError(
            f"annotation log not found at {path}. Set BSS_DTAG_SOURCE_ROOT or "
            f"re-fetch the boxed DTAG asset (see infra/tagtools/BOX_MANIFEST.md)."
        )
    out: List[ExpertAnnotation] = []
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            out.append(
                ExpertAnnotation(
                    whale_id=row["whaleID"],
                    whale_name=row["whaleName"],
                    sample_hz=int(float(row["sampleHz"])),
                    event_start=int(float(row["eventStart"])),
                    event_end=int(float(row["eventEnd"])),
                    state=row["state"],
                    event=row["event"],
                )
            )
    return out


def load_source_bundle(source_root: Optional[str] = None) -> SourceBundle:
    root = source_root or DEFAULT_SOURCE_ROOT
    sensor = load_sensor_csv(root)
    annotations = load_annotations_csv(root)
    return SourceBundle(
        sensor=sensor,
        annotations=annotations,
        source_root=root,
        provenance={
            "dataset": "whale-behavior-analysis/dive_analysis (humpback mn09_203a)",
            "role": "contrast/reference only; never drives an orca",
            "sensor_csv": sensor.source_path,
            "annotation_count": str(len(annotations)),
            "license": LICENSE,
            "license_status": LICENSE_STATUS,
            "attribution": ATTRIBUTION,
            "source": SOURCE_POINTER,
        },
    )
