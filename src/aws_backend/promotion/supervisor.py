"""Promotion supervisor: recommend promote/hold from the fitness-gate record.

This is the agentic, non-conversational reasoning component: given the gate
report from a fit, it produces a structured recommendation (promote or hold)
with a rationale and the gates it cited. A human still makes the final call; the
supervisor only drafts the recommendation.

Two backends:
* Bedrock (``settings.enable_bedrock``): a structured-output prompt to a Claude
  model on Amazon Bedrock that must return strict JSON.
* Deterministic fallback (default, and whenever Bedrock is disabled or fails): a
  transparent rule over confidence + per-gate pass. The fallback guarantees the
  orchestrator always completes, on the request path or off it.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from ..config import settings

# Confidence at/above which promotion is even eligible (mirrors the ASL Choice).
_PROMOTE_CONFIDENCE = 0.6


def _summarize_gates(report: Dict[str, Any]) -> Dict[str, Any]:
    cv = report.get("cv") or {}
    tr = report.get("time_rescaling") or {}
    pit = report.get("pit") or {}
    level1 = report.get("level1_psth") or {}
    metrics = report.get("metrics") or {}
    return {
        "confidence": report.get("confidence", 0.0),
        "cv_gate_pass": cv.get("gate_pass"),
        "cv_mean_skill": cv.get("mean_deviance_skill"),
        "time_rescaling_pass": tr.get("pooled_pass_exp"),
        "pit_calibrated": pit.get("calibrated"),
        "level1_beats_null": [name for name, v in level1.items() if v.get("beats_null")],
        "mcfadden_r2": metrics.get("mcfadden_r2"),
        "n_detections": report.get("n_detections"),
        "tide_overlaps_acoustic": report.get("tide_overlaps_acoustic"),
    }


def _deterministic_decision(report: Dict[str, Any]) -> Dict[str, Any]:
    """Transparent rule: promote only when the evidence clearly earns it."""
    g = _summarize_gates(report)
    cited: List[str] = []
    confidence = float(g.get("confidence") or 0.0)

    passes_core = bool(g.get("cv_gate_pass")) and bool(g.get("pit_calibrated"))
    eligible = confidence >= _PROMOTE_CONFIDENCE
    recommend = "promote" if (eligible and passes_core) else "hold"

    if g.get("cv_gate_pass"):
        cited.append("held-out CV beats climatology")
    else:
        cited.append("held-out CV does NOT beat climatology")
    if g.get("pit_calibrated"):
        cited.append("PIT calibration holds")
    else:
        cited.append("PIT calibration fails (likely overdispersion)")
    if g.get("time_rescaling_pass"):
        cited.append("time-rescaling GOF passes")
    else:
        cited.append("time-rescaling GOF fails")
    if g.get("level1_beats_null"):
        cited.append("Level-1 null beaten by: " + ", ".join(g["level1_beats_null"]))

    rationale = (
        f"Confidence {confidence:.2f} ({'>=' if eligible else '<'} {_PROMOTE_CONFIDENCE} threshold). "
        f"Core gates (CV + calibration) {'pass' if passes_core else 'do not pass'}. "
        f"Recommend {recommend.upper()}."
    )
    return {
        "recommendation": recommend,
        "rationale": rationale,
        "cited_gates": cited,
        "gates_summary": g,
        "source": "deterministic",
    }


def _bedrock_decision(report: Dict[str, Any]) -> Dict[str, Any]:
    """Ask a Bedrock model for a structured promote/hold recommendation."""
    import boto3

    g = _summarize_gates(report)
    prompt = (
        "You are a forecasting promotion reviewer. Given the fitness-gate summary "
        "for a kernel-based wildlife forecast, decide whether to PROMOTE (raise the "
        "displayed confidence) or HOLD (keep it broad). Promote only when held-out "
        "cross-validation beats climatology AND probabilistic calibration holds. Be "
        "conservative: when evidence is thin, hold.\n\n"
        f"Gate summary (JSON):\n{json.dumps(g, default=str)}\n\n"
        'Respond with STRICT JSON only: {"recommendation": "promote"|"hold", '
        '"rationale": string, "cited_gates": [string, ...]}.'
    )
    client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
    response = client.invoke_model(
        modelId=settings.bedrock_model_id,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 600,
            "messages": [{"role": "user", "content": prompt}],
        }),
    )
    payload = json.loads(response["body"].read())
    text = payload["content"][0]["text"]
    parsed = json.loads(text)
    rec = str(parsed.get("recommendation", "hold")).lower()
    if rec not in {"promote", "hold"}:
        rec = "hold"
    return {
        "recommendation": rec,
        "rationale": parsed.get("rationale", ""),
        "cited_gates": parsed.get("cited_gates", []),
        "gates_summary": g,
        "source": "bedrock",
    }


def draft_decision(report: Dict[str, Any]) -> Dict[str, Any]:
    """Draft a promote/hold recommendation; Bedrock if enabled, else deterministic."""
    if settings.enable_bedrock:
        try:
            return _bedrock_decision(report)
        except Exception as exc:  # fall back transparently, never block the loop
            fallback = _deterministic_decision(report)
            fallback["bedrock_error"] = str(exc)
            return fallback
    return _deterministic_decision(report)
