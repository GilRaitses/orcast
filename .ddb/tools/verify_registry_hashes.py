#!/usr/bin/env python3
"""Verify that each active entry in .ddb/registry.json has artifact_hash equal to
the recomputed sha256 of its artifact file. Exit 1 on any mismatch or missing file."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / ".ddb" / "registry.json"


def canonical_text_bytes(text: str) -> bytes:
    normalized = "\n".join(
        line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    )
    return normalized.encode("utf-8")


def sha256_file(path: Path) -> str:
    data = path.read_bytes()
    if path.suffix == ".json":
        obj = json.loads(data.decode("utf-8"))
        canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()
    return hashlib.sha256(canonical_text_bytes(data.decode("utf-8"))).hexdigest()


def main() -> int:
    if not REGISTRY_PATH.exists():
        print("Registry not found:", REGISTRY_PATH, file=sys.stderr)
        return 1
    registry = json.loads(REGISTRY_PATH.read_text())
    path_to_hashes: dict[str, list[str]] = {}
    for e in registry.get("entries", []):
        if e.get("status") != "active":
            continue
        art_path = e.get("artifact_path")
        if not art_path:
            continue
        path_to_hashes.setdefault(art_path, []).append(e.get("artifact_hash", ""))

    failed = []
    for art_path, expected_hashes in path_to_hashes.items():
        full = ROOT / art_path
        if not full.exists():
            failed.append((art_path, expected_hashes[0], "file missing"))
            continue
        try:
            computed = sha256_file(full)
        except Exception as err:  # noqa: BLE001
            failed.append((art_path, expected_hashes[0], str(err)))
            continue
        if len(set(expected_hashes)) != 1 or expected_hashes[0] != computed:
            failed.append((art_path, expected_hashes[0], computed))

    if failed:
        for path, expected, got in failed:
            print(f"MISMATCH: {path} expected={expected} got={got}", file=sys.stderr)
        return 1
    print(f"verify ok: {len(path_to_hashes)} active artifact(s) match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
