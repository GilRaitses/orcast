#!/usr/bin/env python3
"""Register orcast .sst system-state artifacts into .ddb/registry.json deterministically.

Adapted from the pax .ddb registrar, trimmed to orcast's needs. Scans .sst/*.json
and .sst/*.md, derives a deterministic decision_id from (kind, scope,
identity_fields), computes a canonical artifact hash, and maintains at most one
`active` entry per (kind, scope) and per artifact_path (older differing hashes are
marked `superseded`).

JSON artifacts must carry a top-level `decisiondb_identity_fields` object (the
stable identity of the decision) and may carry a `decision_identity` object with
`artifact_kind` and `scope`. Markdown artifacts use an HTML-comment header with
DECISION_IDENTITY_FIELDS_JSON / DECISION_KIND / DECISION_SCOPE_* keys.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SST_DIR = ROOT / ".sst"
REGISTRY_PATH = ROOT / ".ddb" / "registry.json"


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_text_bytes(text: str) -> bytes:
    normalized = "\n".join(
        line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    )
    return normalized.encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class ArtifactDecision:
    artifact_path: str
    artifact_hash: str
    kind: str
    scope: dict[str, Any]
    identity_fields: dict[str, Any]
    equivalence_policy: dict[str, Any]
    provenance_inputs: list[dict[str, Any]]


def parse_md_header(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()
    if not stripped.startswith("<!--"):
        return {}
    start = text.find("<!--")
    end = text.find("-->", start + 4)
    if end == -1:
        return {}
    out: dict[str, str] = {}
    for raw in text[start + 4 : end].splitlines():
        line = raw.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        out[key.strip()] = value.strip()
    return out


def parse_json_artifact(path: Path) -> ArtifactDecision | None:
    data = json.loads(path.read_text(encoding="utf-8"))
    identity_fields = data.get("decisiondb_identity_fields")
    if not isinstance(identity_fields, dict) or not identity_fields:
        return None
    ident = data.get("decision_identity", {}) if isinstance(data.get("decision_identity"), dict) else {}
    kind = ident.get("artifact_kind", path.stem)
    scope = ident.get("scope") if isinstance(ident.get("scope"), dict) else {"artifact": path.stem}
    lifecycle_id = ident.get("lifecycle_id") or data.get("lifecycle_id")
    if lifecycle_id:
        scope = {**scope, "lifecycle_id": lifecycle_id}
    return ArtifactDecision(
        artifact_path=str(path.relative_to(ROOT)),
        artifact_hash=sha256_bytes(canonical_json_bytes(data)),
        kind=kind,
        scope=scope,
        identity_fields=identity_fields,
        equivalence_policy={
            "policy_name": "canonical_json_sha256",
            "canonicalization": "JSON key sort with compact separators then sha256.",
            "compare_fields": ["__full_json__"],
        },
        provenance_inputs=data.get("input_provenance", []) if isinstance(data.get("input_provenance"), list) else [],
    )


def parse_md_artifact(path: Path) -> ArtifactDecision | None:
    header = parse_md_header(path)
    if "DECISION_IDENTITY_FIELDS_JSON" not in header:
        return None
    identity_fields = json.loads(header["DECISION_IDENTITY_FIELDS_JSON"])
    if not isinstance(identity_fields, dict) or not identity_fields:
        return None
    scope = {"artifact": header.get("DECISION_SCOPE", path.stem)}
    return ArtifactDecision(
        artifact_path=str(path.relative_to(ROOT)),
        artifact_hash=sha256_bytes(canonical_text_bytes(path.read_text(encoding="utf-8"))),
        kind=header.get("DECISION_KIND", path.stem),
        scope=scope,
        identity_fields=identity_fields,
        equivalence_policy={
            "policy_name": "canonical_lf_trim_trailing_ws_sha256",
            "canonicalization": "LF line endings with trailing whitespace trimmed per line; UTF-8",
            "compare_fields": ["__full_text__"],
        },
        provenance_inputs=[],
    )


def parse_artifact(path: Path) -> ArtifactDecision | None:
    if path.suffix == ".json":
        return parse_json_artifact(path)
    if path.suffix == ".md":
        return parse_md_artifact(path)
    return None


def load_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {"schema_version": "0.1", "entries": []}
    data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if "entries" not in data or not isinstance(data["entries"], list):
        raise ValueError("Invalid .ddb/registry.json format")
    return data


def decision_id_for(kind: str, scope: dict[str, Any], identity_fields: dict[str, Any]) -> str:
    basis = {"kind": kind, "scope": scope, "identity_fields": identity_fields}
    return sha256_bytes(canonical_json_bytes(basis))


def build_entries() -> list[ArtifactDecision]:
    out: list[ArtifactDecision] = []
    if SST_DIR.exists():
        for path in sorted(SST_DIR.glob("*")):
            if not path.is_file() or path.suffix not in {".json", ".md"}:
                continue
            artifact = parse_artifact(path)
            if artifact is not None:
                out.append(artifact)
    return out


def main() -> int:
    artifacts = build_entries()
    registry = load_registry()
    entries: list[dict[str, Any]] = registry["entries"]
    created: list[str] = []

    for artifact in artifacts:
        decision_id = decision_id_for(artifact.kind, artifact.scope, artifact.identity_fields)
        same_id = [e for e in entries if e.get("decision_id") == decision_id]
        if same_id and any(e.get("artifact_hash") == artifact.artifact_hash for e in same_id):
            continue

        active_same_scope = [
            e for e in entries
            if e.get("kind") == artifact.kind and e.get("scope") == artifact.scope and e.get("status") == "active"
        ]
        active_same_path = [
            e for e in entries
            if e.get("artifact_path") == artifact.artifact_path and e.get("status") == "active"
        ]
        superseded_ids = {
            e["decision_id"]
            for e in active_same_scope + active_same_path
            if e.get("artifact_hash") != artifact.artifact_hash
        }
        for entry in entries:
            if entry.get("decision_id") in superseded_ids:
                entry["status"] = "superseded"

        new_entry = {
            "decision_id": decision_id,
            "kind": artifact.kind,
            "scope": artifact.scope,
            "identity_fields": artifact.identity_fields,
            "artifact_path": artifact.artifact_path,
            "artifact_hash": artifact.artifact_hash,
            "equivalence_policy": artifact.equivalence_policy,
            "provenance": {
                "inputs": artifact.provenance_inputs,
                "generator": {"tool": ".ddb/tools/register_sst.py", "version": "0.1.0"},
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            },
            "status": "active",
        }
        if superseded_ids:
            new_entry["supersedes"] = sorted(superseded_ids)
        entries.append(new_entry)
        created.append(decision_id)

    registry["entries"] = entries
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if created:
        print("new_decision_ids:")
        for decision_id in created:
            print(decision_id)
    else:
        print("new_decision_ids: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
