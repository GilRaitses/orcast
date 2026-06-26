from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_api_key, reviewer_identity
from ..config import settings
from ..config import settings
from ..kernel_model.serve import load_fitted_kernels, load_pending_approval, load_promotion
from ..storage import model_to_dict
from ..state import storage
from .kernel import _build_caveats, _load_fit_report, _public_pending_approval, effective_confidence

router = APIRouter()


def _canonical_hash(payload: Any) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def _latest_decision_for_kernel(kernel_version: Optional[str]) -> Optional[Dict[str, Any]]:
    records = [model_to_dict(r) for r in storage.list_decision_records(limit=200)]
    for record in records:
        record.pop("task_token", None)
    if not records:
        return None
    if kernel_version:
        for record in records:
            if record.get("kernel_version") == kernel_version:
                return record
    return records[0]


def _artifact_refs(report: Dict[str, Any], pending: Optional[Dict[str, Any]], promotion: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    refs = dict(report.get("artifact_uris") or {})
    refs.setdefault("fit_report", "models/fit_report.json")
    refs.setdefault("fitted_kernels", "models/fitted_kernels.json")
    refs.setdefault("promotion", "models/promotion.json" if promotion else None)
    refs.setdefault("pending_approval", "models/pending_approval.json" if pending else None)
    refs.setdefault("fit_plan", report.get("fit_plan_uri"))
    refs.setdefault("snapshot_manifest", report.get("snapshot_manifest_uri"))
    return refs


def build_review_dossier() -> Dict[str, Any]:
    report = _load_fit_report()
    if not report:
        raise HTTPException(status_code=404, detail="No fit report available")

    promotion = load_promotion()
    pending_raw = load_pending_approval()
    pending_public = _public_pending_approval(pending_raw)
    fit = load_fitted_kernels()
    kernel_version = report.get("repr_id") or report.get("kernel_version") or report.get("version") or report.get("generated_at")
    human_decision = _latest_decision_for_kernel(str(kernel_version) if kernel_version else None)
    supervisor = (pending_public or {}).get("recommendation") or (
        human_decision or {}
    ).get("supervisor_recommendation")

    artifact_refs = _artifact_refs(report, pending_public, promotion)
    dossier: Dict[str, Any] = {
        "schema_version": "orcast/review_dossier/v1",
        "workflow_stage": "promoted" if promotion and promotion.get("promoted") else ("decided" if human_decision else "awaiting_human"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provenance": {
            "snap_id": report.get("dataset_snapshot_id"),
            "repr_id": report.get("repr_id"),
            "run_id": report.get("run_id"),
            "fit_plan_id": report.get("fit_plan_id"),
            "dec_id": (human_decision or {}).get("dec_id") or (human_decision or {}).get("id"),
            "f_map_id": (promotion or {}).get("f_map_id"),
            "kernel_version": kernel_version,
            "artifact_refs": artifact_refs,
        },
        "model_card": {
            "model_name": "ORCAST kernel forecast",
            "model_family": report.get("family") or (fit.family if hasattr(fit, "family") else "negbin_glm_lnp"),
            "intended_use": "San Juan Islands pilot forecast confidence review",
            "out_of_scope_use": ["Operational navigation", "locations outside the pilot region"],
            "pilot_region": "San Juan Islands",
            "modeled_dimensions": ["temporal acoustic encounter intensity"],
            "unmodeled_dimensions": ["spatial habitat surface", "visual encounter probability"],
            "covariates_fit": report.get("covariates_fit") or [],
            "covariates_excluded": report.get("covariates_excluded") or {},
            "metrics": report.get("metrics") or {},
            "confidence_raw": report.get("confidence"),
            "confidence_effective": effective_confidence(report, promotion),
            "promoted": bool(promotion and promotion.get("promoted")),
            "caveats": _build_caveats(report),
        },
        "gate_decision": {
            "data_inventory": {
                "n_stations_acoustic": report.get("n_stations_acoustic"),
                "n_detections": report.get("n_detections"),
                "acoustic_span": report.get("acoustic_span"),
                "currents_span": report.get("currents_span"),
                "tide_overlaps_acoustic": report.get("tide_overlaps_acoustic"),
                "effort_assumed_continuous": report.get("effort_assumed_continuous"),
            },
            "gates": {
                "level1_psth": report.get("level1_psth"),
                "cross_validation": report.get("cv"),
                "time_rescaling": report.get("time_rescaling"),
                "pit": report.get("pit"),
                "consistency": report.get("consistency") or report.get("psth_vs_kernel_diagnostic"),
            },
            "gate_pass_eligible": bool(report.get("status") == "fitted" and (report.get("confidence") or 0) >= 0.6),
            "configured_threshold": 0.6,
            "recommendation_basis": ["confidence", "held-out gates", "server-derived caveats"],
        },
        "supervisor_recommendation": supervisor,
        "human_decision": human_decision,
        "provenance_sample": None,
        "source_sheets": [
            {"source": "OrcaHello", "reliability": None, "license": None, "collection_process": "Acoustic detector candidates", "limitations": ["unreviewed candidates"], "maintenance": None},
            {"source": "NOAA CO-OPS", "reliability": None, "license": None, "collection_process": "Tide/current observations", "limitations": ["must overlap acoustic window"], "maintenance": None},
            {"source": "Community reports", "reliability": 0.35, "license": None, "collection_process": "Moderated shore sightings", "limitations": ["presence-only", "human effort bias"], "maintenance": None},
        ],
        "replay": {
            "replay_check_uri": None,
            "replay_status": "not_run",
            "replay_checked_at": None,
        },
    }
    dossier["dossier_id"] = f"dossier_{_canonical_hash({
        'provenance': dossier['provenance'],
        'gate_decision': dossier['gate_decision'],
        'human_decision': dossier['human_decision'],
    })}"
    dossier["prov"] = _prov_graph(dossier)
    return dossier


def _prov_graph(dossier: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    prov = dossier["provenance"]
    entities = [
        {"id": prov.get("snap_id") or "snapshot_current", "type": "Dataset", "label": "Frozen or current fit inputs", "uri": prov["artifact_refs"].get("snapshot_manifest"), "sha256": None},
        {"id": prov.get("repr_id") or "representation_current", "type": "Representation", "label": "Fitted kernel representation", "uri": prov["artifact_refs"].get("fitted_kernels"), "sha256": None},
        {"id": prov.get("run_id") or "run_current", "type": "Run", "label": "Fit and gate run", "uri": prov["artifact_refs"].get("fit_report"), "sha256": None},
    ]
    if prov.get("dec_id"):
        entities.append({"id": prov["dec_id"], "type": "HumanDecision", "label": "Human decision", "uri": None, "sha256": None})
    activities = [
        {"id": "fit_model", "type": "FitModel", "started_at": None, "ended_at": None},
        {"id": "evaluate_gates", "type": "EvaluateGates", "started_at": None, "ended_at": None},
    ]
    agents = [{"id": "orcast_system", "type": "System", "label": "ORCAST"}]
    if dossier.get("human_decision"):
        reviewer = dossier["human_decision"].get("reviewer_email") or dossier["human_decision"].get("reviewer") or "reviewer"
        agents.append({"id": reviewer, "type": "Reviewer", "label": reviewer})
    edges = [
        {"subject": prov.get("repr_id") or "representation_current", "predicate": "wasGeneratedBy", "object": "fit_model"},
        {"subject": prov.get("run_id") or "run_current", "predicate": "wasGeneratedBy", "object": "evaluate_gates"},
        {"subject": prov.get("run_id") or "run_current", "predicate": "used", "object": prov.get("snap_id") or "snapshot_current"},
    ]
    if prov.get("dec_id") and len(agents) > 1:
        edges.append({"subject": prov["dec_id"], "predicate": "wasAttributedTo", "object": agents[-1]["id"]})
    return {"entities": entities, "activities": activities, "agents": agents, "edges": edges}


@router.get("/api/review-dossier/latest", dependencies=[Depends(require_api_key)])
def latest_review_dossier() -> Dict[str, Any]:
    return {"status": "success", "dossier": build_review_dossier()}


@router.get("/api/review-dossier/{dossier_id}", dependencies=[Depends(require_api_key)])
def get_review_dossier(dossier_id: str) -> Dict[str, Any]:
    dossier = build_review_dossier()
    if dossier["dossier_id"] != dossier_id and dossier_id != "latest":
        raise HTTPException(status_code=404, detail="Dossier not found")
    return {"status": "success", "dossier": dossier}


_EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def _redact_pii(value: Any) -> Any:
    """Strip reviewer emails and free-text reasons from audit exports."""
    if isinstance(value, str):
        if _EMAIL_RE.search(value):
            return "[redacted]"
        return value
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for key, item in value.items():
            if key in {"reviewer_email", "email", "review_reason", "reason", "notes", "body"}:
                continue
            if key == "reviewer" and isinstance(item, str) and "@" in item:
                continue
            out[key] = _redact_pii(item)
        return out
    if isinstance(value, list):
        return [_redact_pii(item) for item in value]
    return value


@router.get("/api/review-dossier/{dossier_id}/export", dependencies=[Depends(require_api_key)])
def export_review_dossier(
    dossier_id: str,
    redact_pii: bool = True,
    identity=Depends(reviewer_identity),
) -> Dict[str, Any]:
    if not redact_pii:
        if settings.env not in ("local", "test", "development") or settings.api_key:
            if not identity.reviewer_id:
                raise HTTPException(status_code=401, detail="Sign in required for unredacted export")
    dossier = build_review_dossier()
    if dossier["dossier_id"] != dossier_id and dossier_id != "latest":
        raise HTTPException(status_code=404, detail="Dossier not found")
    records = [model_to_dict(r) for r in storage.list_decision_records(limit=200)]
    for record in records:
        record.pop("task_token", None)
    export = {
        "export_version": "1",
        "export_type": "audit_packet",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "exported_by": None,
        "pii_redacted": redact_pii,
        "manifest": {
            "context": "orcast/audit/v1",
            "has_part": [
                {"id": "review_dossier", "uri": f"orcast://review-dossier/{dossier['dossier_id']}", "sha256": _canonical_hash(dossier), "media_type": "application/json"}
            ],
        },
        "dossiers": [dossier],
        "decision_records": records,
        "promotion_markers": [dossier["provenance"].get("artifact_refs", {}).get("promotion")],
        "prov_graph": dossier["prov"],
        "replay_status": {
            "run_id": dossier["provenance"].get("run_id"),
            "replay_check_passed": None,
            "replay_check_at": None,
        },
        "integrity": {
            "content_hashes": {"dossier": _canonical_hash(dossier)},
            "git_sha": None,
            "dependency_hash": None,
        },
    }
    if redact_pii:
        export = _redact_pii(export)
    return {"status": "success", "export": export}
