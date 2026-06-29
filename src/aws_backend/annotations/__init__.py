"""DTAG annotation persistence (studio-live-persistence, STU-B).

A net-new write store for community-authored, provenance-tagged annotations
against the partnership-gated, simulated DTAG deployments. Mirrors the
per-domain store pattern used by ``journal/store.py``: an abstract base, a
memory impl for offline tests, an AWS DynamoDB impl, and a build factory keyed
on ``storage_backend``.
"""

from __future__ import annotations

from .store import (
    AnnotationStore,
    AwsAnnotationStore,
    MemoryAnnotationStore,
    StoredAnnotation,
    build_annotation_store,
)

__all__ = [
    "AnnotationStore",
    "AwsAnnotationStore",
    "MemoryAnnotationStore",
    "StoredAnnotation",
    "build_annotation_store",
]
