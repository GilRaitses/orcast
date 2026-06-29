"""Policy and skill catalog tests for Central Casting."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from src.aws_backend.casting.manifest import enabled_skill_ids, load_manifest
from src.aws_backend.casting.models import load_seed_agent
from src.aws_backend.casting.policy import filter_deep_links, validate_skills
from src.aws_backend.casting.skills import SKILL_CATALOG


def test_skill_catalog_matches_manifest_enabled():
    manifest = load_manifest()
    assert set(SKILL_CATALOG.keys()) == set(enabled_skill_ids())
    public_enabled = [sid for sid in enabled_skill_ids() if manifest[sid].tier in ("T0", "T1")]
    assert len(public_enabled) == 9
    assert len(SKILL_CATALOG) == 15


def test_manifest_public_skills_are_t0_t1():
    manifest = load_manifest()
    for sid in enabled_skill_ids():
        spec = manifest[sid]
        if spec.auth == "public":
            assert spec.tier in ("T0", "T1"), sid
            assert spec.auth == "public", sid


def test_manifest_keyed_skills_are_t2_t3():
    manifest = load_manifest()
    keyed = [sid for sid in enabled_skill_ids() if manifest[sid].auth == "keyed"]
    assert len(keyed) == 6
    for sid in keyed:
        assert manifest[sid].tier in ("T2", "T3"), sid


def test_validate_skills_rejects_unknown():
    agent = load_seed_agent("explore-guide-v1")
    agent.skills = ["fetch_gates", "approve_promotion"]
    with pytest.raises(HTTPException) as exc:
        validate_skills(agent)
    assert exc.value.status_code == 400


def test_validate_skills_rejects_t2_skill_on_public_route():
    agent = load_seed_agent("explore-guide-v1")
    agent.skills = ["fetch_gates", "fetch_review_dossier_summary"]
    with pytest.raises(HTTPException) as exc:
        validate_skills(agent, public_route=True)
    assert exc.value.status_code == 400
    assert exc.value.detail.get("error") == "tier_blocked"


def test_validate_agent_skills_blocks_t2_tier_on_public_route(monkeypatch):
    from src.aws_backend.casting import manifest as manifest_mod

    fake = manifest_mod.SkillSpec(
        id="fetch_fake_t2",
        tier="T2",
        truth_label="live",
        geo_required=False,
        auth="keyed",
        enabled=True,
        wraps="exploration.tools.fetch_gates",
        produces_annotations=[],
        data_bindings=[],
        orchestrator_step=None,
    )
    monkeypatch.setattr(manifest_mod, "load_manifest", lambda: {"fetch_fake_t2": fake})
    with pytest.raises(ValueError, match="tier_blocked"):
        manifest_mod.validate_agent_skills(["fetch_fake_t2"], public_route=True)


def test_filter_deep_links_respects_policy():
    agent = load_seed_agent("explore-guide-v1")
    links = [
        {"label": "Gates", "href": "/gates"},
        {"label": "Evil", "href": "/admin"},
    ]
    filtered = filter_deep_links(agent, links)
    assert any(l["href"] == "/gates" for l in filtered)


def test_seed_agent_spec_hash_stable():
    a = load_seed_agent("explore-guide-v1")
    b = load_seed_agent("explore-guide-v1")
    assert a.spec_hash() == b.spec_hash()
