"""Promotion + orchestration endpoints.

* ``POST /api/promotion/draft``   -- supervisor drafts a promote/hold recommendation
                                     over the current (or supplied) gate report.
* ``POST /api/promotion/apply``   -- record an approved promotion marker so the
                                     served confidence reflects the human verdict.
* ``POST /api/orchestrator/run``  -- start a Step Functions execution (the UI
                                     "Re-fit" button), if a state machine is wired.

All are API-keyed. The draft endpoint is invoked by the orchestrator's
``DraftPromotion`` stage; apply is invoked by ``ApplyPromotion`` after human
sign-off; run is the manual/refresh trigger.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException

from ..auth import ReviewerIdentity, require_api_key, require_trusted_reviewer
from ..config import settings
from ..kernel_model.serve import DEFAULT_PROMOTION_PATH, PROMOTION_S3_KEY
from ..promotion.supervisor import draft_decision
from .kernel import _load_fit_report
from ..state import storage

router = APIRouter()


@router.post("/api/promotion/draft", dependencies=[Depends(require_api_key)])
def promotion_draft(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Draft a promote/hold recommendation from the gate report (Bedrock or rule)."""
    report = (payload or {}).get("report") or _load_fit_report()
    if not report:
        raise HTTPException(status_code=404, detail="No fit report available to evaluate")
    return {"status": "success", "recommendation": draft_decision(report)}


@router.post("/api/promotion/apply", dependencies=[Depends(require_api_key)])
def promotion_apply(
    payload: Dict[str, Any],
    identity: ReviewerIdentity = Depends(require_trusted_reviewer),
) -> Dict[str, Any]:
    """Persist an approved promotion marker (served confidence reflects it)."""
    decision_id = payload.get("decision_id")
    record = storage.get_decision_record(decision_id) if decision_id else None
    if decision_id and record is None:
        raise HTTPException(status_code=404, detail="Decision record not found")

    report = _load_fit_report() or {}
    kernel_version = (
        record.kernel_version
        if record and record.kernel_version
        else report.get("version") or report.get("generated_at") or payload.get("kernel_version")
    )
    reviewer = record.reviewer if record else payload.get("reviewer")
    marker = {
        "promoted": True,
        "kernel_version": kernel_version,
        "repr_id": report.get("repr_id"),
        "run_id": report.get("run_id"),
        "effective_confidence": float(payload.get("effective_confidence", 1.0)),
        "decision_id": decision_id,
        "reviewer": reviewer,
        "applied_at": datetime.now(timezone.utc).isoformat(),
    }
    _write_promotion(marker)
    return {"status": "success", "promotion": marker}


@router.post("/api/orchestrator/run", dependencies=[Depends(require_api_key)])
def orchestrator_run(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Start a Step Functions execution of the forecast orchestrator."""
    if not settings.state_machine_arn:
        raise HTTPException(status_code=400, detail="No ORCAST_STATE_MACHINE_ARN configured")
    try:
        import boto3
        sfn = boto3.client("stepfunctions", region_name=settings.aws_region)
        execution = sfn.start_execution(
            stateMachineArn=settings.state_machine_arn,
            name=f"orcast-run-{uuid.uuid4().hex[:12]}",
            input=json.dumps((payload or {}).get("input", {})),
        )
        return {"status": "success", "execution_arn": execution["executionArn"]}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to start execution: {exc}")


def apply_promotion_marker(
    *,
    decision_id: str,
    kernel_version: Optional[str],
    run_id: Optional[str],
    repr_id: Optional[str],
    reviewer: str,
    effective_confidence: float,
) -> Dict[str, Any]:
    marker = {
        "promoted": True,
        "kernel_version": kernel_version,
        "repr_id": repr_id,
        "run_id": run_id,
        "effective_confidence": effective_confidence,
        "decision_id": decision_id,
        "reviewer": reviewer,
        "applied_at": datetime.now(timezone.utc).isoformat(),
    }
    _write_promotion(marker)
    return marker


def _write_promotion(marker: Dict[str, Any]) -> None:
    body = json.dumps(marker, indent=2)
    if settings.storage_backend.lower() == "aws":
        import boto3
        s3 = boto3.client("s3", region_name=settings.aws_region)
        s3.put_object(
            Bucket=settings.models_bucket, Key=PROMOTION_S3_KEY,
            Body=body.encode(), ContentType="application/json",
        )
        return
    path = Path(DEFAULT_PROMOTION_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
