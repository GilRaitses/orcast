from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from pydantic import BaseModel

from ..models import NormalizedSighting, SourceStatus


class SourceFetchResult(BaseModel):
    source: str
    available: bool
    raw: Any = None
    status_code: Optional[int] = None
    content_type: Optional[str] = None
    error: Optional[str] = None
    skipped_count: int = 0


class SourceAdapter(ABC):
    source_name: str
    enabled: bool = True
    reliability: float = 0.5

    @abstractmethod
    def fetch(self) -> SourceFetchResult:
        ...

    @abstractmethod
    def normalize(self, result: SourceFetchResult) -> List[NormalizedSighting]:
        ...

    def status(self, result: SourceFetchResult, record_count: int) -> SourceStatus:
        return SourceStatus(
            source=self.source_name,
            enabled=self.enabled,
            available=result.available,
            record_count=record_count,
            skipped_count=result.skipped_count,
            error=result.error,
        )

