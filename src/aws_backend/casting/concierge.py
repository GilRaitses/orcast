"""Concierge runtime — hydrate cast role and run interaction."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..exploration.guide import compose_guide_reply
from ..exploration.models import GuideReply
from .models import ManagedAgent, ManagedAgentPolicy
from .policy import filter_deep_links, validate_skills
from .registry import ManagedAgentStore
from .skills import SkillRunResult, run_skills


@dataclass
class InteractionResult:
    guide: GuideReply
    interaction_id: str
    managed_agent_id: str
    agent_version: str
    resolved_spec_hash: str
    hydration_mode: str
    skills_invoked: List[str]
    steps: List[Dict[str, Any]] = field(default_factory=list)
    annotations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PrepareResult:
    managed_agent_id: str
    agent_version: str
    resolved_spec_hash: str
    hydration_mode: str
    context: Dict[str, Any]
    citations: List[Dict[str, str]]
    deep_links: List[Dict[str, str]]
    tools_used: List[str]
    gate_ids: List[str]
    provenance_refs: List[str]
    steps: List[Dict[str, Any]]
    annotations: List[Dict[str, Any]]


def resolve_agent(
    store: ManagedAgentStore,
    agent_id: str,
    version: Optional[str] = None,
) -> ManagedAgent:
    agent = store.get(agent_id, version=version)
    if agent is None:
        raise LookupError(f"Managed agent not found: {agent_id}")
    return agent


def resolve_inline_agent(
    inline: Dict[str, Any],
    *,
    session_id: str,
    agent_id: Optional[str] = None,
) -> ManagedAgent:
    policy_raw = inline.get("policy") or {}
    resolved_id = agent_id or f"inline-{session_id[:8]}"
    return ManagedAgent(
        id=str(resolved_id),
        version=str(inline.get("version") or "inline"),
        instructions=str(inline.get("instructions") or ""),
        skills=[str(s) for s in (inline.get("skills") or [])],
        data_bindings=dict(inline.get("data_bindings") or {}),
        model=dict(inline.get("model") or {}),
        policy=ManagedAgentPolicy(
            write_tools=bool(policy_raw.get("write_tools", False)),
            allowed_deep_links=list(
                policy_raw.get("allowed_deep_links") or ["/gates", "/explore", "/"]
            ),
            allowed_panels=list(policy_raw.get("allowed_panels") or []),
            planner_mode=bool(policy_raw.get("planner_mode", False)),
        ),
        active=True,
    )


def _resolve_cast_agent(
    store: ManagedAgentStore,
    *,
    agent_id: Optional[str],
    agent_version: Optional[str],
    inline_agent: Optional[Dict[str, Any]],
    session_id: str,
) -> tuple[ManagedAgent, str]:
    if inline_agent is not None:
        agent = resolve_inline_agent(
            inline_agent,
            session_id=session_id,
            agent_id=agent_id,
        )
        return agent, "inline"
    if not agent_id:
        raise ValueError("agent_id required when inline agent not provided")
    agent = resolve_agent(store, agent_id, agent_version)
    return agent, "by_id"


def _run_skill_phase(
    agent: ManagedAgent,
    message: str,
    *,
    viewport: Optional[Dict[str, Any]] = None,
    focus: Optional[Dict[str, Any]] = None,
) -> tuple[SkillRunResult, List[Dict[str, str]], List[Dict[str, Any]]]:
    skill_result = run_skills(
        agent.skills,
        message,
        viewport=viewport,
        focus=focus,
    )
    deep_links = filter_deep_links(agent, skill_result.deep_links)
    steps: List[Dict[str, Any]] = [
        {
            "type": "resolve_agent",
            "managed_agent_id": agent.id,
            "agent_version": agent.version,
            "resolved_spec_hash": agent.spec_hash(),
        }
    ]
    steps.extend(skill_result.step_records)
    return skill_result, deep_links, steps


def _build_annotations(
    skill_result: SkillRunResult,
    deep_links: List[Dict[str, str]],
) -> List[Dict[str, Any]]:
    annotations = list(skill_result.annotations)
    for link in deep_links:
        annotations.append(
            {
                "type": "deep_link",
                "label": link.get("label", "Link"),
                "href": link.get("href", "/"),
            }
        )
    return annotations


def prepare_interaction_with_skills(
    agent: ManagedAgent,
    message: str,
    skill_plan: List[str],
    *,
    viewport: Optional[Dict[str, Any]] = None,
    focus: Optional[Dict[str, Any]] = None,
    hydration_mode: str = "by_id",
    public_route: bool = False,
) -> PrepareResult:
    validate_skills(
        ManagedAgent(
            id=agent.id,
            version=agent.version,
            instructions=agent.instructions,
            skills=skill_plan,
            policy=agent.policy,
            data_bindings=agent.data_bindings,
            model=agent.model,
            active=agent.active,
        ),
        public_route=public_route,
    )
    skill_result = run_skills(
        skill_plan,
        message,
        viewport=viewport,
        focus=focus,
    )
    deep_links = filter_deep_links(agent, skill_result.deep_links)
    steps: List[Dict[str, Any]] = [
        {
            "type": "resolve_agent",
            "managed_agent_id": agent.id,
            "agent_version": agent.version,
            "resolved_spec_hash": agent.spec_hash(),
        }
    ]
    steps.extend(skill_result.step_records)
    annotations = _build_annotations(skill_result, deep_links)
    return PrepareResult(
        managed_agent_id=agent.id,
        agent_version=agent.version,
        resolved_spec_hash=agent.spec_hash(),
        hydration_mode=hydration_mode,
        context=skill_result.context,
        citations=skill_result.citations,
        deep_links=deep_links,
        tools_used=skill_result.tools_used,
        gate_ids=skill_result.gate_ids,
        provenance_refs=skill_result.provenance_refs,
        steps=steps,
        annotations=annotations,
    )


def prepare_interaction(
    store: ManagedAgentStore,
    *,
    session_id: str,
    agent_id: Optional[str],
    agent_version: Optional[str],
    message: str,
    viewport: Optional[Dict[str, Any]] = None,
    focus: Optional[Dict[str, Any]] = None,
    inline_agent: Optional[Dict[str, Any]] = None,
) -> PrepareResult:
    agent, hydration_mode = _resolve_cast_agent(
        store,
        agent_id=agent_id,
        agent_version=agent_version,
        inline_agent=inline_agent,
        session_id=session_id,
    )
    validate_skills(agent, public_route=True)
    return prepare_interaction_with_skills(
        agent,
        message,
        agent.skills,
        viewport=viewport,
        focus=focus,
        hydration_mode=hydration_mode,
        public_route=True,
    )


def run_interaction(
    store: ManagedAgentStore,
    *,
    session_id: str,
    agent_id: Optional[str],
    agent_version: Optional[str],
    message: str,
    viewport: Optional[Dict[str, Any]] = None,
    focus: Optional[Dict[str, Any]] = None,
    gateway_reply: Optional[str] = None,
    gateway_model: Optional[str] = None,
    inline_agent: Optional[Dict[str, Any]] = None,
) -> InteractionResult:
    agent, hydration_mode = _resolve_cast_agent(
        store,
        agent_id=agent_id,
        agent_version=agent_version,
        inline_agent=inline_agent,
        session_id=session_id,
    )
    validate_skills(agent, public_route=True)

    interaction_id = str(uuid.uuid4())
    skill_result, deep_links, steps = _run_skill_phase(
        agent,
        message,
        viewport=viewport,
        focus=focus,
    )

    guide = compose_guide_reply(
        message,
        viewport=viewport,
        focus=focus,
        gateway_reply=gateway_reply,
        gateway_model=gateway_model,
        instructions=agent.instructions,
        skills=agent.skills,
        prefetched=(
            skill_result.context,
            skill_result.citations,
            deep_links,
            skill_result.tools_used,
            skill_result.gate_ids,
            skill_result.provenance_refs,
        ),
        model_id=agent.model.get("model_id"),
    )

    annotations = _build_annotations(skill_result, deep_links)

    steps.append(
        {
            "type": "model_output",
            "provider": guide.source,
            "model": guide.model,
            "text_preview": guide.reply[:240],
            "annotations": annotations,
        }
    )

    return InteractionResult(
        guide=guide,
        interaction_id=interaction_id,
        managed_agent_id=agent.id,
        agent_version=agent.version,
        resolved_spec_hash=agent.spec_hash(),
        hydration_mode=hydration_mode,
        skills_invoked=skill_result.tools_used,
        steps=steps,
        annotations=annotations,
    )
