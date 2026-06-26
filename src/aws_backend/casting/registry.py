"""Managed agent registry — DynamoDB or in-memory for local dev."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from ..config import Settings, settings
from .models import ManagedAgent, ManagedAgentPolicy, load_seed_agent


class ManagedAgentStore(ABC):
    @abstractmethod
    def get(self, agent_id: str, version: Optional[str] = None) -> Optional[ManagedAgent]:
        ...

    @abstractmethod
    def list_agents(self) -> List[Dict[str, str]]:
        ...

    @abstractmethod
    def put(self, agent: ManagedAgent) -> None:
        ...


_SEED_AGENTS = (
    "explore-guide-v1",
    "surface-planner-v1",
    "dossier-explainer-v1",
    "promotion-clerk-v1",
)


class MemoryManagedAgentStore(ManagedAgentStore):
    def __init__(self) -> None:
        self._agents: Dict[tuple[str, str], ManagedAgent] = {}
        for seed_name in _SEED_AGENTS:
            try:
                seed = load_seed_agent(seed_name)
                self._agents[(seed.id, seed.version)] = seed
            except FileNotFoundError:
                continue

    def get(self, agent_id: str, version: Optional[str] = None) -> Optional[ManagedAgent]:
        if version:
            return self._agents.get((agent_id, version))
        matches = [a for (aid, _), a in self._agents.items() if aid == agent_id and a.active]
        if not matches:
            return None
        return sorted(matches, key=lambda a: a.version, reverse=True)[0]

    def list_agents(self) -> List[Dict[str, str]]:
        seen: Dict[str, ManagedAgent] = {}
        for (aid, _), agent in self._agents.items():
            if not agent.active:
                continue
            if aid not in seen or agent.version > seen[aid].version:
                seen[aid] = agent
        return [{"id": a.id, "version": a.version} for a in sorted(seen.values(), key=lambda x: x.id)]

    def put(self, agent: ManagedAgent) -> None:
        self._agents[(agent.id, agent.version)] = agent


class AwsManagedAgentStore(ManagedAgentStore):
    def __init__(self, cfg: Settings = settings) -> None:
        import boto3

        self.table_name = cfg.managed_agents_table
        self.table = boto3.resource("dynamodb", region_name=cfg.aws_region).Table(self.table_name)

    def get(self, agent_id: str, version: Optional[str] = None) -> Optional[ManagedAgent]:
        if version:
            response = self.table.get_item(Key={"agent_id": agent_id, "version": version})
            item = response.get("Item")
            if not item or not item.get("active", True):
                return None
            return _item_to_agent(item)

        from boto3.dynamodb.conditions import Key

        response = self.table.query(
            KeyConditionExpression=Key("agent_id").eq(agent_id),
        )
        items = [i for i in response.get("Items", []) if i.get("active", True)]
        if not items:
            return None
        latest = sorted(items, key=lambda i: str(i.get("version", "")), reverse=True)[0]
        return _item_to_agent(latest)

    def list_agents(self) -> List[Dict[str, str]]:
        response = self.table.scan()
        seen: Dict[str, Dict[str, str]] = {}
        for item in response.get("Items", []):
            if not item.get("active", True):
                continue
            aid = str(item["agent_id"])
            ver = str(item.get("version", ""))
            if aid not in seen or ver > seen[aid]["version"]:
                seen[aid] = {"id": aid, "version": ver}
        return sorted(seen.values(), key=lambda x: x["id"])

    def put(self, agent: ManagedAgent) -> None:
        self.table.put_item(
            Item={
                "agent_id": agent.id,
                "version": agent.version,
                "instructions": agent.instructions,
                "skills": agent.skills,
                "data_bindings": agent.data_bindings,
                "model": agent.model,
                "policy": {
                    "write_tools": agent.policy.write_tools,
                    "allowed_deep_links": agent.policy.allowed_deep_links,
                    "allowed_panels": agent.policy.allowed_panels,
                    "planner_mode": agent.policy.planner_mode,
                },
                "active": agent.active,
                "spec_hash": agent.spec_hash(),
            }
        )


def _item_to_agent(item: dict) -> ManagedAgent:
    policy = item.get("policy") or {}
    return ManagedAgent(
        id=str(item["agent_id"]),
        version=str(item["version"]),
        instructions=str(item.get("instructions", "")),
        skills=[str(s) for s in (item.get("skills") or [])],
        data_bindings=dict(item.get("data_bindings") or {}),
        model=dict(item.get("model") or {}),
        policy=ManagedAgentPolicy(
            write_tools=bool(policy.get("write_tools", False)),
            allowed_deep_links=list(policy.get("allowed_deep_links") or []),
            allowed_panels=list(policy.get("allowed_panels") or []),
            planner_mode=bool(policy.get("planner_mode", False)),
        ),
        active=bool(item.get("active", True)),
    )


def build_managed_agent_store(cfg: Settings = settings) -> ManagedAgentStore:
    if cfg.storage_backend.lower() == "aws" and cfg.managed_agents_table:
        return AwsManagedAgentStore(cfg)
    return MemoryManagedAgentStore()
