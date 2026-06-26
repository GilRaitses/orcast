"""Managed agent registry CRUD (Central Casting control plane)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import require_api_key
from ..casting.models import ManagedAgent, ManagedAgentPolicy
from ..casting.registry import build_managed_agent_store

router = APIRouter()
_store = build_managed_agent_store()


class ManagedAgentPayload(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    version: str = Field(..., min_length=1, max_length=32)
    instructions: str = Field(..., min_length=1, max_length=8000)
    skills: list[str] = Field(default_factory=list)
    data_bindings: Dict[str, str] = Field(default_factory=dict)
    model: Dict[str, str] = Field(default_factory=dict)
    policy: Dict[str, Any] = Field(default_factory=dict)
    active: bool = True


def _payload_to_agent(payload: ManagedAgentPayload) -> ManagedAgent:
    policy_raw = payload.policy or {}
    return ManagedAgent(
        id=payload.id,
        version=payload.version,
        instructions=payload.instructions,
        skills=payload.skills,
        data_bindings=payload.data_bindings,
        model=payload.model,
        policy=ManagedAgentPolicy(
            write_tools=bool(policy_raw.get("write_tools", False)),
            allowed_deep_links=list(
                policy_raw.get("allowed_deep_links") or ["/gates", "/explore", "/"]
            ),
            allowed_panels=list(policy_raw.get("allowed_panels") or []),
            planner_mode=bool(policy_raw.get("planner_mode", False)),
        ),
        active=payload.active,
    )


@router.get("/api/managed-agents", dependencies=[Depends(require_api_key)])
def list_managed_agents() -> Dict[str, Any]:
    return {"status": "success", "agents": _store.list_agents()}


@router.get("/api/managed-agents/{agent_id}", dependencies=[Depends(require_api_key)])
def get_managed_agent(
    agent_id: str,
    version: Optional[str] = None,
) -> Dict[str, Any]:
    agent = _store.get(agent_id, version=version)
    if agent is None:
        raise HTTPException(status_code=404, detail="Managed agent not found")
    return {"status": "success", "agent": agent.to_dict()}


@router.post("/api/managed-agents", dependencies=[Depends(require_api_key)])
def upsert_managed_agent(payload: ManagedAgentPayload) -> Dict[str, Any]:
    agent = _payload_to_agent(payload)
    _store.put(agent)
    return {"status": "success", "agent": agent.to_dict()}
