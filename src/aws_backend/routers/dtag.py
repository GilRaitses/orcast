"""Whale-tagger read API (B-side build order, step 1).

FastAPI surface over the dtag behavioral analysis, mirroring the orcast Central
Casting honesty pattern. This is a cache-backed READ path: it serves deployments
from ``dtag_cache/deployments/{id}/`` when present, plus the one bundled example
analysis (``data/dtag_analysis_results.json``), which is a SIMULATED Cascadia
deployment and is flagged ``simulated: true``.

Honesty constraints (locked, see ORCAST_BSIDE_DESIGN.md and WHALE_TAGGER_API_DESIGN.md):
- DTAG data is partnership-gated. Real deployments require a data-sharing
  agreement; until then the only deployment is the simulated example.
- The feeding-strategy classifier has no trained weights in-repo, so it returns
  ``model_state: not_trained`` with the uniform-probability caveat, mirroring the
  way the forecast reports 0% effective confidence with a gate caveat.
- Acoustic and dive analysis here is biologging-style telemetry, distinct from the
  acoustic hydrophone context and from visual sightings.

Supersedes the deprecated 410 ``/api/dtag-data`` with honest, structured reads.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter

from ..config import settings

router = APIRouter()

# Taxonomy is not yet ratified into a single versioned registry (see
# WHALE_TAGGER_API_DESIGN.md section 9 open decisions). Report it honestly.
TAXONOMY_VERSION = "unratified-0"

_BUNDLED_EXAMPLE = ("data", "dtag_analysis_results.json")


def _repo_root() -> Path:
    root = Path(settings.repo_root)
    if root.exists():
        return root
    return Path(__file__).resolve().parents[3]


def _cache_dir() -> Path:
    return _repo_root() / "dtag_cache" / "deployments"


def _safe_load(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


@lru_cache(maxsize=1)
def _load_deployments() -> Dict[str, Dict[str, Any]]:
    """Return {deployment_id: {results, simulated, source}}.

    The bundled example is always SIMULATED. Cache deployments under
    ``dtag_cache/deployments/{id}/deployment.json`` are served as supplied; a
    deployment is treated as real only when its payload does not flag simulated.
    """
    out: Dict[str, Dict[str, Any]] = {}

    example_path = _repo_root().joinpath(*_BUNDLED_EXAMPLE)
    results = _safe_load(example_path)
    if results and results.get("deployment_id"):
        out[str(results["deployment_id"])] = {
            "results": results,
            "simulated": True,
            "source": "bundled_example",
        }

    cache = _cache_dir()
    if cache.exists():
        for child in sorted(cache.iterdir()):
            if not child.is_dir():
                continue
            payload = _safe_load(child / "deployment.json") or _safe_load(child / "analysis.json")
            if not payload:
                continue
            dep_id = str(payload.get("deployment_id") or child.name)
            out[dep_id] = {
                "results": payload,
                "simulated": bool(payload.get("simulated", False)),
                "source": "dtag_cache",
            }
    return out


def _deployment_summary(dep_id: str, entry: Dict[str, Any]) -> Dict[str, Any]:
    results = entry["results"]
    dive = results.get("dive_analysis", {}) or {}
    return {
        "deployment_id": dep_id,
        "simulated": entry["simulated"],
        "source": entry["source"],
        "methodology": results.get("methodology"),
        "data_summary": results.get("data_summary", {}),
        "total_dives": dive.get("total_dives", 0),
        "dive_types": dive.get("dive_types", []),
        "behavioral_patterns": results.get("behavioral_patterns", {}),
        "taxonomy_version": TAXONOMY_VERSION,
        "partnership_gated": True,
    }


def _not_available(deployment_id: str) -> Dict[str, Any]:
    return {
        "status": "not_available",
        "deployment_id": deployment_id,
        "reason": "No cached deployment with this id. DTAG data is partnership-gated.",
        "available_deployments": sorted(_load_deployments().keys()),
    }


@router.get("/api/dtag/deployments")
def list_deployments() -> Dict[str, Any]:
    deployments = _load_deployments()
    return {
        "status": "success",
        "count": len(deployments),
        "partnership_gated": True,
        "taxonomy_version": TAXONOMY_VERSION,
        "deployments": [_deployment_summary(dep_id, entry) for dep_id, entry in sorted(deployments.items())],
    }


@router.get("/api/dtag/deployments/{deployment_id}")
def get_deployment(deployment_id: str) -> Dict[str, Any]:
    entry = _load_deployments().get(deployment_id)
    if not entry:
        return _not_available(deployment_id)
    summary = _deployment_summary(deployment_id, entry)
    summary["status"] = "success"
    summary["surface_analysis"] = entry["results"].get("surface_analysis", {})
    summary["energetic_model"] = entry["results"].get("energetic_model", {})
    summary["key_insights"] = entry["results"].get("key_insights", [])
    return summary


@router.get("/api/dtag/dives/{deployment_id}")
def get_dives(deployment_id: str) -> Dict[str, Any]:
    entry = _load_deployments().get(deployment_id)
    if not entry:
        return _not_available(deployment_id)
    dive = entry["results"].get("dive_analysis", {}) or {}
    dives: List[Dict[str, Any]] = dive.get("dive_events", []) or []
    return {
        "status": "success",
        "deployment_id": deployment_id,
        "simulated": entry["simulated"],
        "total_dives": dive.get("total_dives", len(dives)),
        "dives": dives,
    }


@router.get("/api/dtag/feeding/{deployment_id}")
def get_feeding(deployment_id: str) -> Dict[str, Any]:
    """Feeding-strategy classification.

    There are no trained classifier weights in-repo (the minGRU is documented
    only; the honest near-term path is a Random Forest over engineered features,
    not yet wired). Report ``not_trained`` with the uniform-probability caveat,
    the same honesty contract as the 0% forecast confidence.
    """
    entry = _load_deployments().get(deployment_id)
    if not entry:
        return _not_available(deployment_id)
    dive = entry["results"].get("dive_analysis", {}) or {}
    dives: List[Dict[str, Any]] = dive.get("dive_events", []) or []
    return {
        "status": "success",
        "deployment_id": deployment_id,
        "simulated": entry["simulated"],
        "model_state": "not_trained",
        "taxonomy_version": TAXONOMY_VERSION,
        "caveat": (
            "No trained feeding classifier is wired. Under annotation scarcity the "
            "minGRU collapses to uniform probability (ROC-AUC about 0.51); the honest "
            "near-term path is a Random Forest over engineered features (84.38% in the "
            "manuscript), not yet wired. Treat outputs as not_trained."
        ),
        "uniform_probability": True,
        "segments": [
            {
                "dive_id": d.get("dive_id"),
                "rule_based_dive_type": d.get("dive_type", "unknown"),
                "foraging_intensity": (d.get("foraging_indicators", {}) or {}).get("foraging_intensity"),
                "model_probability": None,
            }
            for d in dives
        ],
    }
