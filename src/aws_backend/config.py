from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class Settings:
    env: str = os.getenv("ORCAST_ENV", "local")
    aws_region: str = os.getenv("AWS_REGION", "us-west-2")
    storage_backend: str = os.getenv("ORCAST_STORAGE_BACKEND", "memory")
    sightings_table: str = os.getenv("ORCAST_SIGHTINGS_TABLE", "orcast-sightings")
    hotspots_table: str = os.getenv("ORCAST_HOTSPOTS_TABLE", "orcast-hotspots")
    reports_table: str = os.getenv("ORCAST_REPORTS_TABLE", "orcast-reports")
    ingestion_runs_table: str = os.getenv("ORCAST_INGESTION_RUNS_TABLE", "orcast-ingestion-runs")
    community_table: str = os.getenv("ORCAST_COMMUNITY_TABLE", "orcast-community-submissions")
    raw_payload_bucket: str = os.getenv("ORCAST_RAW_PAYLOAD_BUCKET", "orcast-raw-payloads")
    reports_bucket: str = os.getenv("ORCAST_REPORTS_BUCKET", "orcast-probability-reports")
    enable_live_inaturalist: bool = os.getenv("ORCAST_ENABLE_LIVE_INATURALIST", "false").lower() == "true"
    enable_live_noaa: bool = os.getenv("ORCAST_ENABLE_LIVE_NOAA", "true").lower() == "true"
    enable_orcahello: bool = os.getenv("ORCAST_ENABLE_ORCAHELLO", "true").lower() == "true"
    enable_community: bool = os.getenv("ORCAST_ENABLE_COMMUNITY", "true").lower() == "true"
    cors_origins_raw: str = os.getenv("ORCAST_CORS_ORIGINS", "*")
    repo_root: Path = Path(os.getenv("ORCAST_REPO_ROOT", Path(__file__).resolve().parents[2]))

    @property
    def api_key(self) -> str:
        return os.getenv("ORCAST_API_KEY", "")

    @property
    def cors_origins(self) -> List[str]:
        if self.cors_origins_raw.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @property
    def local_obis_path(self) -> Path:
        return self.repo_root / "archive" / "public-templates-backup-20250720" / "api" / "verified-sightings.json"

    @property
    def orcasound_hydrophones_path(self) -> Path:
        return self.repo_root / "src" / "integrations" / "orcasound_hydrophones_for_orcast.json"


settings = Settings()

