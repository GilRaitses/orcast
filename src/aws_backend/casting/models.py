"""Managed agent configuration models."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ManagedAgentPolicy:
    write_tools: bool = False
    allowed_deep_links: List[str] = field(default_factory=lambda: ["/gates", "/explore", "/"])
    allowed_panels: List[str] = field(default_factory=list)
    planner_mode: bool = False


@dataclass
class ManagedAgent:
    id: str
    version: str
    instructions: str
    skills: List[str]
    policy: ManagedAgentPolicy
    data_bindings: Dict[str, str] = field(default_factory=dict)
    model: Dict[str, str] = field(default_factory=dict)
    active: bool = True

    def spec_hash(self) -> str:
        payload = {
            "id": self.id,
            "version": self.version,
            "instructions": self.instructions,
            "skills": sorted(self.skills),
            "data_bindings": self.data_bindings,
            "model": self.model,
            "policy": {
                "write_tools": self.policy.write_tools,
                "allowed_deep_links": sorted(self.policy.allowed_deep_links),
                "allowed_panels": sorted(self.policy.allowed_panels),
                "planner_mode": self.policy.planner_mode,
            },
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "instructions": self.instructions,
            "skills": self.skills,
            "data_bindings": self.data_bindings,
            "model": self.model,
            "policy": {
                "write_tools": self.policy.write_tools,
                "allowed_deep_links": self.policy.allowed_deep_links,
                "allowed_panels": self.policy.allowed_panels,
                "planner_mode": self.policy.planner_mode,
            },
            "active": self.active,
            "spec_hash": self.spec_hash(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ManagedAgent":
        policy_raw = data.get("policy") or {}
        return cls(
            id=str(data["id"]),
            version=str(data["version"]),
            instructions=str(data["instructions"]),
            skills=[str(s) for s in (data.get("skills") or [])],
            data_bindings=dict(data.get("data_bindings") or {}),
            model=dict(data.get("model") or {}),
            policy=ManagedAgentPolicy(
                write_tools=bool(policy_raw.get("write_tools", False)),
                allowed_deep_links=list(
                    policy_raw.get("allowed_deep_links") or ["/gates", "/explore", "/"]
                ),
                allowed_panels=list(policy_raw.get("allowed_panels") or []),
                planner_mode=bool(policy_raw.get("planner_mode", False)),
            ),
            active=bool(data.get("active", True)),
        )


def load_seed_agent(name: str) -> ManagedAgent:
    from pathlib import Path

    path = Path(__file__).resolve().parent / "seeds" / f"{name}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return ManagedAgent.from_dict(data)
