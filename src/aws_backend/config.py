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
    decision_records_table: str = os.getenv("ORCAST_DECISION_RECORDS_TABLE", "orcast-decision-records")
    journal_table: str = os.getenv("ORCAST_JOURNAL_TABLE", "orcast-user-journal")
    partner_keys_table: str = os.getenv("ORCAST_PARTNER_KEYS_TABLE", "orcast-partner-api-keys")
    managed_agents_table: str = os.getenv("ORCAST_MANAGED_AGENTS_TABLE", "")
    raw_payload_bucket: str = os.getenv("ORCAST_RAW_PAYLOAD_BUCKET", "orcast-raw-payloads")
    reports_bucket: str = os.getenv("ORCAST_REPORTS_BUCKET", "orcast-probability-reports")
    # Where fitted kernel coefficients + gate report live. Empty == reuse the
    # raw-payload bucket under a ``models/`` prefix (see models_bucket property).
    models_bucket_raw: str = os.getenv("ORCAST_MODELS_BUCKET", "")
    enable_live_obis: bool = os.getenv("ORCAST_ENABLE_LIVE_OBIS", "true").lower() == "true"
    enable_live_inaturalist: bool = os.getenv("ORCAST_ENABLE_LIVE_INATURALIST", "true").lower() == "true"
    enable_live_noaa: bool = os.getenv("ORCAST_ENABLE_LIVE_NOAA", "true").lower() == "true"
    enable_orcahello: bool = os.getenv("ORCAST_ENABLE_ORCAHELLO", "true").lower() == "true"
    enable_onc: bool = os.getenv("ORCAST_ENABLE_ONC", "false").lower() == "true"
    enable_community: bool = os.getenv("ORCAST_ENABLE_COMMUNITY", "true").lower() == "true"
    enable_bedrock: bool = os.getenv("ORCAST_ENABLE_BEDROCK", "false").lower() == "true"
    bedrock_model_id: str = os.getenv("ORCAST_BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0")
    bedrock_sighting_model_id: str = os.getenv(
        "ORCAST_BEDROCK_SIGHTING_MODEL",
        "global.anthropic.claude-haiku-4-5-20251001-v1:0",
    )
    llm_enabled: bool = os.getenv("ORCAST_LLM_ENABLED", "false").lower() == "true"
    llm_base_url: str = os.getenv("ORCAST_LLM_BASE_URL", "http://127.0.0.1:11434")
    llm_model: str = os.getenv("ORCAST_LLM_MODEL", "phi3:mini")
    llm_timeout_seconds: int = int(os.getenv("ORCAST_LLM_TIMEOUT", "45"))
    llm_max_tokens: int = int(os.getenv("ORCAST_LLM_MAX_TOKENS", "512"))
    llm_temperature: float = float(os.getenv("ORCAST_LLM_TEMPERATURE", "0.3"))
    state_machine_arn: str = os.getenv("ORCAST_STATE_MACHINE_ARN", "")
    database_url: str = os.getenv("ORCAST_DATABASE_URL", "")
    explore_max_sessions_per_ip_day: int = int(os.getenv("ORCAST_EXPLORE_MAX_SESSIONS_PER_IP_DAY", "20"))
    explore_max_turns_per_session: int = int(os.getenv("ORCAST_EXPLORE_MAX_TURNS_PER_SESSION", "30"))
    explore_retention_days: int = int(os.getenv("ORCAST_EXPLORE_RETENTION_DAYS", "30"))
    cors_origins_raw: str = os.getenv("ORCAST_CORS_ORIGINS", "*")
    repo_root: Path = Path(os.getenv("ORCAST_REPO_ROOT", Path(__file__).resolve().parents[2]))

    @property
    def api_key(self) -> str:
        return os.getenv("ORCAST_API_KEY", "")

    @property
    def onc_api_token(self) -> str:
        """Ocean Networks Canada Oceans 3.0 token — env/secret only, never logged
        or written to a tracked file (HANDOFF_CHARTER B5)."""
        return os.getenv("ONC_API_TOKEN", "")

    @property
    def models_bucket(self) -> str:
        """Bucket holding fitted kernel artifacts (defaults to raw-payload bucket)."""
        return self.models_bucket_raw or self.raw_payload_bucket

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

