"""BSS managed HUD skills extending Central Casting.

Three net-new skills the orchestrated console can invoke, all honest about being
served from baked/derived artifacts (O0 gate 2, posture 2). They preserve the
existing skill-handler contract (return a dict with a `status` key) so they slot
into `skills.run_skills` and the `_DISPATCH` table.

  - run_tagtools_step:   serve a real tagtools pipeline step summary
  - render_poster_viz:   serve a baked poster visualization descriptor
  - capture_behavior:    serve a real-DTAG behavior-capture spec for the director
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .behavior_capture import build_capture_spec, load_fixture

_HERE = Path(__file__).resolve().parent
_ARTIFACTS_PATH = _HERE / "studio_artifacts.json"


def _load_artifacts() -> Dict[str, Any]:
    return json.loads(_ARTIFACTS_PATH.read_text(encoding="utf-8"))


def run_tagtools_step(step_id: str = "tagtools.odba", **_kw: Any) -> Dict[str, Any]:
    """Return the baked summary + provenance for one tagtools pipeline step."""
    try:
        fixture = load_fixture()
    except FileNotFoundError as exc:
        return {"status": "not_available", "message": str(exc)}
    for step in fixture.get("tagtools_steps", []):
        if step.get("step_id") == step_id:
            return {
                "status": "success",
                "step_id": step_id,
                "title": step.get("title"),
                "truth_label": step.get("truth_label"),
                "reproduces_h5_path": step.get("reproduces_h5_path"),
                "summary": step.get("summary"),
                "provenance": step.get("provenance"),
                "license": fixture.get("license"),
                "license_status": fixture.get("license_status"),
                "attribution": fixture.get("attribution"),
            }
    available = [s.get("step_id") for s in fixture.get("tagtools_steps", [])]
    return {"status": "not_found", "step_id": step_id, "available": available}


def render_poster_viz(viz_id: str = "dive_overview", **_kw: Any) -> Dict[str, Any]:
    """Return a baked poster-viz descriptor. No R/plotly runtime is invoked."""
    artifacts = _load_artifacts()
    for art in artifacts.get("artifacts", []):
        if art.get("viz_id") == viz_id:
            return {
                "status": "success",
                "viz_id": viz_id,
                "title": art.get("title"),
                "render": art.get("render"),
                "truth_label": art.get("truth_label"),
                "source_script": art.get("source_script"),
                "box_key": f"{artifacts.get('box_prefix', '')}{art.get('box_key', '')}",
                "js_port_status": art.get("js_port_status"),
                "license": artifacts.get("license"),
                "license_status": artifacts.get("license_status"),
                "attribution": artifacts.get("attribution"),
            }
    available = [a.get("viz_id") for a in artifacts.get("artifacts", [])]
    return {"status": "not_found", "viz_id": viz_id, "available": available}


def capture_behavior(prefer_behavior: Optional[str] = None, **_kw: Any) -> Dict[str, Any]:
    """Return a director capture spec for a real classified DTAG behavior."""
    try:
        return build_capture_spec(prefer_behavior=prefer_behavior)
    except FileNotFoundError as exc:
        return {"status": "not_available", "message": str(exc)}


# Handler table B3 contributes to the Central Casting dispatch (merged in skills.py).
# Registered now; the manifest keeps these enabled=false until BSS-INTEGRATE
# activates them in the public catalog and allowlists their console panels.
STUDIO_DISPATCH = {
    "run_tagtools_step": run_tagtools_step,
    "render_poster_viz": render_poster_viz,
    "capture_behavior": capture_behavior,
}


def _sandbox() -> int:
    """Direct-invocation sandbox proof (handlers run without console activation)."""
    failures = 0
    for name, fn, arg in (
        ("run_tagtools_step", run_tagtools_step, "tagtools.odba"),
        ("render_poster_viz", render_poster_viz, "dive_overview"),
        ("capture_behavior", capture_behavior, "Kick feeding"),
    ):
        out = fn(arg)
        ok = out.get("status") == "success"
        failures += 0 if ok else 1
        print(f"[studio-sandbox] {'PASS' if ok else 'FAIL'} {name}: status={out.get('status')}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_sandbox())
