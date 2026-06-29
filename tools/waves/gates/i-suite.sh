#!/usr/bin/env bash
# I-suite — research implementation pytest subset
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

echo "== I-suite: aws_backend tests =="
PYTHONPATH=src python3 -m pytest tests/aws_backend/ -q --tb=no

echo "== I-suite: modeling tests =="
PYTHONPATH=modeling python3 -m pytest modeling/tests/ -q --tb=no

echo "I-suite gate: PASS"
