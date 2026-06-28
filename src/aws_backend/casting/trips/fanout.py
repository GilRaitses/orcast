"""Bounded concurrent fan-out for the connection planner's I/O legs.

The connection planner assembles a plan from several independent blocking
source calls (WSF schedule / sailing space / vessel locations and the corridor
ETA adapter). Run sequentially they add up (~4 x ~100 ms); they have no data
dependency on each other, so they fan out across a small bounded thread pool and
the wall time approaches the slowest single leg instead of their sum.

This module owns NO source logic and changes NO behavior of a leg: each task is
the exact callable the sequential path used. Per-task exceptions are isolated
and surfaced as ``None`` so one failed or slow leg degrades exactly like the
sequential ``try/except -> {} / []`` path did (the caller coerces ``None`` to
its empty sentinel). Nothing here touches honesty labels.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, Mapping, Optional

logger = logging.getLogger(__name__)

_DEFAULT_MAX_WORKERS = 4


def fetch_legs_concurrently(
    tasks: Mapping[str, Callable[[], Any]],
    *,
    max_workers: int = _DEFAULT_MAX_WORKERS,
    timeout: Optional[float] = None,
) -> Dict[str, Any]:
    """Run each ``tasks[key]`` callable concurrently; return ``{key: result}``.

    A task that raises is logged and recorded as ``None`` (never propagated), so
    a single failing leg cannot fail the whole plan. The pool is bounded by
    ``min(max_workers, len(tasks))``. With zero or one task the call runs inline
    to avoid pool overhead. Results are keyed by the same keys passed in.
    """
    if not tasks:
        return {}

    if len(tasks) == 1:
        (key, fn), = tasks.items()
        return {key: _guard(key, fn)}

    results: Dict[str, Any] = {}
    workers = min(max_workers, len(tasks))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_key = {
            executor.submit(_guard, key, fn): key for key, fn in tasks.items()
        }
        for future in as_completed(future_to_key, timeout=timeout):
            key = future_to_key[future]
            # _guard never raises, but as_completed could on timeout; guard it.
            try:
                results[key] = future.result()
            except Exception as exc:  # pragma: no cover - timeout/cancellation
                logger.warning("fanout: task %s did not complete: %s", key, exc)
                results[key] = None
    return results


def _guard(key: str, fn: Callable[[], Any]) -> Any:
    """Run ``fn`` capturing any exception as ``None`` (mirrors the leg's except)."""
    try:
        return fn()
    except Exception as exc:
        logger.warning("fanout: leg %s failed: %s", key, exc)
        return None
