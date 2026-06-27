#!/usr/bin/env python3
"""Fail-fast preflight for the orcast co-tenant backend on the shared self-host.

Verifies critical Python imports, the uvicorn entrypoint module, required runtime
files, and that the required env var NAMES from host_manifest.yaml are present in
the process environment (values not inspected). Run inside the orcast venv, with
the service env file already sourced, before starting orcast-api.service.

Exit non-zero on any critical failure so provision_orcast.sh refuses to start a
broken service.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get("ORCAST_DIR", "/opt/orcast"))

CRITICAL_IMPORTS = ["fastapi", "uvicorn", "multipart", "pydantic", "boto3", "requests"]
FUNCTIONAL_IMPORTS = ["psycopg"]

CRITICAL_FILES = [
    "src/aws_backend/main.py",
]
FUNCTIONAL_FILES = [
    "data/geo",
    "src/integrations/orcasound_hydrophones_for_orcast.json",
    "archive/public-templates-backup-20250720/api/verified-sightings.json",
]

REQUIRED_ENV = [
    "AWS_REGION",
    "ORCAST_ENV",
    "ORCAST_STORAGE_BACKEND",
    "ORCAST_API_KEY",
    "ORCAST_SIGHTINGS_TABLE",
    "ORCAST_HOTSPOTS_TABLE",
    "ORCAST_REPORTS_TABLE",
    "ORCAST_REPORTS_BUCKET",
    "ORCAST_RAW_PAYLOAD_BUCKET",
]


def main() -> int:
    failures: list[str] = []
    warnings: list[str] = []

    for mod in CRITICAL_IMPORTS:
        try:
            importlib.import_module(mod)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"import {mod}: {exc}")
    for mod in FUNCTIONAL_IMPORTS:
        try:
            importlib.import_module(mod)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"import {mod} (functional): {exc}")

    for rel in CRITICAL_FILES:
        if not (ROOT / rel).exists():
            failures.append(f"missing critical file: {rel}")
    for rel in FUNCTIONAL_FILES:
        if not (ROOT / rel).exists():
            warnings.append(f"missing functional file: {rel}")

    for key in REQUIRED_ENV:
        if not os.environ.get(key):
            failures.append(f"missing required env: {key}")

    # Entrypoint import (catches src-layout / PYTHONPATH problems early).
    sys.path.insert(0, str(ROOT))
    try:
        importlib.import_module("src.aws_backend.main")
    except Exception as exc:  # noqa: BLE001
        failures.append(f"import src.aws_backend.main: {exc}")

    for w in warnings:
        print(f"[preflight][warn] {w}")
    if failures:
        for f in failures:
            print(f"[preflight][FAIL] {f}")
        return 1
    print("[preflight] ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
