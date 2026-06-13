from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from ..config import settings
from .base import SourceAdapter, SourceFetchResult


class OrcasoundHydrophoneAdapter(SourceAdapter):
    source_name = "orcasound_hydrophones"
    reliability = 0.85

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings.orcasound_hydrophones_path

    def fetch(self) -> SourceFetchResult:
        if not self.path.exists():
            return SourceFetchResult(source=self.source_name, available=False, error=f"Missing {self.path}")
        with self.path.open("r", encoding="utf-8") as file:
            return SourceFetchResult(source=self.source_name, available=True, raw=json.load(file))

    def normalize(self, result: SourceFetchResult):
        return []

    def hydrophones(self) -> List[Dict[str, Any]]:
        result = self.fetch()
        if not result.available or not isinstance(result.raw, dict):
            return []
        records = result.raw.get("all_hydrophones") or result.raw.get("hydrophones") or []
        hydrophones: List[Dict[str, Any]] = []
        for record in records:
            latitude = record.get("latitude")
            longitude = record.get("longitude")
            if latitude is None or longitude is None:
                coordinates = record.get("coordinates") or [None, None]
                longitude, latitude = coordinates[0], coordinates[1]
            if latitude is None or longitude is None:
                continue
            visible = bool(record.get("visible", True))
            hydrophones.append(
                {
                    "id": record.get("id"),
                    "name": record.get("name"),
                    "location": record.get("name"),
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                    "status": "online" if visible else "offline",
                    "detecting": False,
                    "lastDetection": None,
                    "streamUrl": f"https://live.orcasound.net/listen/{record.get('slug')}" if record.get("slug") else None,
                    "source": "Orcasound",
                    "imageUrl": record.get("image_url"),
                }
            )
        return hydrophones

