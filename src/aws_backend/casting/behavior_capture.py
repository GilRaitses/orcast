"""Behavior-capture automation for the BSS studio.

Layers a capture spec on the demo-production director process (block, camera
test, screen test). It pulls a REAL classified behavior from a REAL DTAG example
in the baked fixture and turns it into a director capture spec the existing
camera director (web/lib/scene/camera/director.ts: descendTo, followPath, orbit)
can run. No scripted fakes: the behavior, the dive window, and the depth come
from the real humpback DTAG mn09_203a products.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_FIXTURE = _REPO_ROOT / "web" / "lib" / "annotation" / "fixtures" / "dtag_mn09_203a.json"


def _fixture_path() -> Path:
    return Path(os.environ.get("BSS_DTAG_FIXTURE", str(_DEFAULT_FIXTURE)))


def load_fixture() -> Dict[str, Any]:
    path = _fixture_path()
    if not path.exists():
        raise FileNotFoundError(
            f"baked DTAG fixture not found at {path}; run infra/tagtools/bake.py first"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _pick_classified_dive(
    fixture: Dict[str, Any], prefer_behavior: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    classified = [d for d in fixture.get("dives", []) if d.get("classified_behavior")]
    if not classified:
        return None
    if prefer_behavior:
        for d in classified:
            if d["classified_behavior"] == prefer_behavior:
                return d
    # Otherwise pick the deepest classified dive for a legible capture.
    return max(classified, key=lambda d: d.get("max_depth_m", 0.0))


def build_capture_spec(
    prefer_behavior: Optional[str] = None,
    fixture: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    fx = fixture or load_fixture()
    dive = _pick_classified_dive(fx, prefer_behavior)
    if dive is None:
        return {
            "status": "no_classified_example",
            "message": "no dive in the fixture carries a classified behavior",
        }

    fs = float(fx["meta"]["sample_rate_hz"])
    start_s = dive["start_sample"] / fs
    end_s = dive["end_sample"] / fs
    max_depth = float(dive["max_depth_m"])

    # Block / camera-test / screen-test stages on the demo-production director.
    stages: List[Dict[str, Any]] = [
        {
            "stage": "block",
            "intent": "place the modeled animal on the real dive path",
            "director_call": "followPath",
            "params": {
                "from_time_s": round(start_s, 2),
                "to_time_s": round(end_s, 2),
                "depth_target_m": round(max_depth, 2),
            },
        },
        {
            "stage": "camera_test",
            "intent": "descend the camera to the deepest point of the dive",
            "director_call": "descendTo",
            "params": {"depth_m": round(max_depth, 2), "at_time_s": round(
                dive["max_depth_sample"] / fs, 2
            )},
        },
        {
            "stage": "screen_test",
            "intent": "orbit the classified behavior window for review",
            "director_call": "orbit",
            "params": {"window_s": [round(start_s, 2), round(end_s, 2)]},
        },
    ]

    return {
        "status": "success",
        "truth_label": "measured-behavior-modeled-camera",
        "deployment_id": fx["meta"]["deployment_id"],
        "species": fx["meta"]["species"],
        "behavior": dive["classified_behavior"],
        "dive_id": dive["dive_id"],
        "dive_window_s": [round(start_s, 2), round(end_s, 2)],
        "max_depth_m": round(max_depth, 2),
        "director_process": "demo-production (.cca/catalogue/O0/20260628_demo-production)",
        "stages": stages,
        "honesty": (
            "behavior and dive geometry are measured from the real DTAG; the animal mesh "
            "and camera move are modeled. The humpback example is contrast/reference only "
            "and never drives an orca."
        ),
        "provenance": fx.get("provenance", {}),
        "license": fx.get("license", "CC-BY-NC-4.0"),
        "license_status": fx.get("license_status", "CC-BY-NC-4.0, non-commercial"),
        "attribution": fx.get("attribution", ""),
    }


if __name__ == "__main__":
    print(json.dumps(build_capture_spec(prefer_behavior="Kick feeding"), indent=2))
