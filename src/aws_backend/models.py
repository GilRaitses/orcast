from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ValidationStatus(str, Enum):
    VERIFIED = "verified"
    LIKELY = "likely"
    TENTATIVE = "tentative"
    REJECTED = "rejected"


class SourceEvidence(BaseModel):
    source: str
    source_id: str
    source_url: Optional[str] = None
    observed_at: Optional[datetime] = None
    reliability: float = Field(default=0.5, ge=0.0, le=1.0)
    quality_grade: Optional[str] = None
    evidence_urls: List[str] = Field(default_factory=list)
    raw_payload_ref: Optional[str] = None
    notes: Optional[str] = None


class EnvironmentalSnapshot(BaseModel):
    timestamp: datetime = Field(default_factory=utc_now)
    latitude: float
    longitude: float
    tide_height_ft: Optional[float] = None
    water_temp_c: Optional[float] = None
    salinity_ppt: Optional[float] = None
    current_speed: Optional[float] = None
    visibility_km: Optional[float] = None
    data_sources: Dict[str, str] = Field(default_factory=dict)
    quality: str = "fallback"


class CrossValidationResult(BaseModel):
    status: ValidationStatus = ValidationStatus.TENTATIVE
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    independent_source_count: int = 0
    spatial_matches: int = 0
    temporal_matches: int = 0
    evidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    environmental_score: float = Field(default=0.0, ge=0.0, le=1.0)
    matched_sighting_ids: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)


class NormalizedSighting(BaseModel):
    sighting_id: str
    canonical_id: Optional[str] = None
    source: str
    source_id: str
    source_url: Optional[str] = None
    timestamp: datetime
    latitude: float
    longitude: float
    species: str = "Orcinus orca"
    common_name: str = "Killer Whale"
    location_name: Optional[str] = None
    behavior: str = "unknown"
    pod: Optional[str] = None
    ecotype: Optional[str] = None
    count: Optional[int] = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source_reliability: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence: List[SourceEvidence] = Field(default_factory=list)
    environmental: Optional[EnvironmentalSnapshot] = None
    cross_validation: CrossValidationResult = Field(default_factory=CrossValidationResult)
    raw: Dict[str, Any] = Field(default_factory=dict)
    ingested_at: datetime = Field(default_factory=utc_now)


class SourceStatus(BaseModel):
    source: str
    enabled: bool
    available: bool
    record_count: int = 0
    skipped_count: int = 0
    error: Optional[str] = None
    checked_at: datetime = Field(default_factory=utc_now)


class IngestionRun(BaseModel):
    run_id: str
    started_at: datetime = Field(default_factory=utc_now)
    completed_at: Optional[datetime] = None
    statuses: List[SourceStatus] = Field(default_factory=list)
    sightings_ingested: int = 0
    sightings_stored: int = 0
    errors: List[str] = Field(default_factory=list)


class Hotspot(BaseModel):
    hotspot_id: str
    name: str
    center_latitude: float
    center_longitude: float
    radius_km: float
    probability: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    detection_count: int
    validated_detection_count: int
    source_count: int
    behavior_distribution: Dict[str, int] = Field(default_factory=dict)
    environmental_factors: Dict[str, Any] = Field(default_factory=dict)
    reason_codes: List[str] = Field(default_factory=list)
    evidence_sighting_ids: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=utc_now)
    model_version: str = "aws-deterministic-hotspot-v1"


class ProbabilityReportRequest(BaseModel):
    region: str = "san_juan_islands"
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    include_sources: List[str] = Field(default_factory=list)
    report_format: str = "json"
    force_refresh: bool = False


class ProbabilityReport(BaseModel):
    report_id: str
    generated_at: datetime = Field(default_factory=utc_now)
    region: str
    summary: str
    hotspots: List[Hotspot]
    source_status: List[SourceStatus] = Field(default_factory=list)
    cross_validation_summary: Dict[str, Any] = Field(default_factory=dict)
    environmental_summary: Dict[str, Any] = Field(default_factory=dict)
    data_quality_warnings: List[str] = Field(default_factory=list)
    model_version: str = "aws-probability-report-v1"
    storage_uri: Optional[str] = None


class ForecastQuickRequest(BaseModel):
    lat: float = 48.5465
    lng: float = -123.0307
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class SpatialForecastRequest(BaseModel):
    lat: float = 48.5465
    lng: float = -123.0307
    radius_km: float = 10.0
    grid_resolution: float = 0.05
    hours: int = 24

