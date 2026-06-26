"""Load and validate the Central Casting skills manifest."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

_MANIFEST_PATH = Path(__file__).resolve().parent / "skills_manifest.json"


@dataclass(frozen=True)
class SkillSpec:
    id: str
    tier: str
    truth_label: str
    geo_required: bool
    auth: str
    enabled: bool
    wraps: str
    produces_annotations: List[str]
    data_bindings: List[str]
    orchestrator_step: Optional[str]


def _parse_skill(raw: dict) -> SkillSpec:
    return SkillSpec(
        id=str(raw["id"]),
        tier=str(raw.get("tier", "T0")),
        truth_label=str(raw.get("truth_label", "live")),
        geo_required=bool(raw.get("geo_required", False)),
        auth=str(raw.get("auth", "public")),
        enabled=bool(raw.get("enabled", True)),
        wraps=str(raw.get("wraps", "")),
        produces_annotations=list(raw.get("produces_annotations") or []),
        data_bindings=list(raw.get("data_bindings") or []),
        orchestrator_step=raw.get("orchestrator_step"),
    )


@lru_cache(maxsize=1)
def load_manifest() -> Dict[str, SkillSpec]:
    data = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    specs = [_parse_skill(raw) for raw in data.get("skills", [])]
    return {spec.id: spec for spec in specs}


def get_skill(skill_id: str) -> Optional[SkillSpec]:
    return load_manifest().get(skill_id)


def enabled_skill_ids() -> List[str]:
    return [sid for sid, spec in load_manifest().items() if spec.enabled]


def validate_agent_skills(skill_ids: List[str], *, public_route: bool = True) -> None:
    manifest = load_manifest()
    unknown: List[str] = []
    disabled: List[str] = []
    tier_blocked: List[str] = []
    for sid in skill_ids:
        spec = manifest.get(sid)
        if spec is None:
            unknown.append(sid)
            continue
        if not spec.enabled:
            disabled.append(sid)
            continue
        if public_route and spec.tier in ("T2", "T3"):
            tier_blocked.append(sid)
    if unknown:
        raise ValueError(f"unknown_skills:{','.join(unknown)}")
    if disabled:
        raise ValueError(f"disabled_skills:{','.join(disabled)}")
    if tier_blocked:
        raise ValueError(f"tier_blocked:{','.join(tier_blocked)}")
