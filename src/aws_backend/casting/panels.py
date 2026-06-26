"""Panel registry for UI intent validation."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Set

_REGISTRY_PATH = Path(__file__).resolve().parent / "panel_registry.json"


@lru_cache(maxsize=1)
def load_panel_registry() -> Dict[str, Dict[str, Any]]:
    data = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    panels = data.get("panels") or []
    return {str(p["id"]): dict(p) for p in panels if p.get("id")}


def panel_ids() -> List[str]:
    return sorted(load_panel_registry().keys())


def validate_panels(
    panel_specs: List[Dict[str, Any]],
    *,
    allowed: Set[str] | None = None,
) -> None:
    registry = load_panel_registry()
    invalid: List[str] = []
    blocked: List[str] = []
    for spec in panel_specs:
        pid = str(spec.get("id") or "")
        if pid not in registry:
            invalid.append(pid or "<missing>")
            continue
        if allowed is not None and pid not in allowed:
            blocked.append(pid)
    if invalid:
        raise ValueError(f"invalid_panels:{','.join(invalid)}")
    if blocked:
        raise ValueError(f"panel_not_allowed:{','.join(blocked)}")
