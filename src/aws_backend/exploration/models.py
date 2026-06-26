"""Pydantic-ish dataclasses for exploration turns."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ExplorationTurn:
    role: str
    content: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    gate_ids: List[str] = field(default_factory=list)
    provenance_refs: List[str] = field(default_factory=list)
    model: Optional[str] = None
    source: Optional[str] = None
    interaction_id: Optional[str] = None
    managed_agent_id: Optional[str] = None
    agent_version: Optional[str] = None
    resolved_spec_hash: Optional[str] = None
    hydration_mode: Optional[str] = None
    skills_invoked: List[str] = field(default_factory=list)
    interaction_steps: Optional[List[Dict[str, Any]]] = None


@dataclass
class GuideReply:
    reply: str
    citations: List[Dict[str, str]]
    deep_links: List[Dict[str, str]]
    source: str
    model: Optional[str]
    tools_used: List[str]
    gate_ids: List[str] = field(default_factory=list)
    provenance_refs: List[str] = field(default_factory=list)
    llm_error: Optional[str] = None
