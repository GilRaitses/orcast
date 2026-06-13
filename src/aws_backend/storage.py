from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .config import Settings, settings
from .models import Hotspot, IngestionRun, NormalizedSighting, ProbabilityReport


def model_to_dict(model: Any) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return model.dict()


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"Cannot serialize {type(value)!r}")


def _decimalize(value: Any) -> Any:
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: _decimalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_decimalize(v) for v in value]
    return value


class StorageBackend(ABC):
    @abstractmethod
    def put_sightings(self, sightings: List[NormalizedSighting]) -> None:
        ...

    @abstractmethod
    def list_sightings(self, limit: int = 500) -> List[NormalizedSighting]:
        ...

    @abstractmethod
    def put_hotspots(self, hotspots: List[Hotspot]) -> None:
        ...

    @abstractmethod
    def list_hotspots(self, limit: int = 100) -> List[Hotspot]:
        ...

    @abstractmethod
    def put_report(self, report: ProbabilityReport) -> None:
        ...

    @abstractmethod
    def get_report(self, report_id: str) -> Optional[ProbabilityReport]:
        ...

    @abstractmethod
    def put_ingestion_run(self, run: IngestionRun) -> None:
        ...

    @abstractmethod
    def put_raw_payload(self, source: str, payload: Any, run_id: str) -> str:
        ...


class MemoryStorage(StorageBackend):
    def __init__(self) -> None:
        self.sightings: Dict[str, NormalizedSighting] = {}
        self.hotspots: Dict[str, Hotspot] = {}
        self.reports: Dict[str, ProbabilityReport] = {}
        self.ingestion_runs: Dict[str, IngestionRun] = {}
        self.raw_payloads: Dict[str, Any] = {}

    def put_sightings(self, sightings: List[NormalizedSighting]) -> None:
        for sighting in sightings:
            self.sightings[sighting.sighting_id] = sighting

    def list_sightings(self, limit: int = 500) -> List[NormalizedSighting]:
        return sorted(self.sightings.values(), key=lambda s: s.timestamp, reverse=True)[:limit]

    def put_hotspots(self, hotspots: List[Hotspot]) -> None:
        self.hotspots = {hotspot.hotspot_id: hotspot for hotspot in hotspots}

    def list_hotspots(self, limit: int = 100) -> List[Hotspot]:
        return sorted(self.hotspots.values(), key=lambda h: h.probability, reverse=True)[:limit]

    def put_report(self, report: ProbabilityReport) -> None:
        self.reports[report.report_id] = report

    def get_report(self, report_id: str) -> Optional[ProbabilityReport]:
        return self.reports.get(report_id)

    def put_ingestion_run(self, run: IngestionRun) -> None:
        self.ingestion_runs[run.run_id] = run

    def put_raw_payload(self, source: str, payload: Any, run_id: str) -> str:
        ref = f"memory://raw/{run_id}/{source}/{uuid4().hex[:12]}.json"
        self.raw_payloads[ref] = payload
        return ref


class AwsStorage(StorageBackend):
    def __init__(self, cfg: Settings = settings) -> None:
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("boto3 is required for ORCAST_STORAGE_BACKEND=aws") from exc

        self.cfg = cfg
        self.dynamodb = boto3.resource("dynamodb", region_name=cfg.aws_region)
        self.s3 = boto3.client("s3", region_name=cfg.aws_region)
        self.sightings_table = self.dynamodb.Table(cfg.sightings_table)
        self.hotspots_table = self.dynamodb.Table(cfg.hotspots_table)
        self.reports_table = self.dynamodb.Table(cfg.reports_table)
        self.ingestion_runs_table = self.dynamodb.Table(cfg.ingestion_runs_table)

    def put_sightings(self, sightings: List[NormalizedSighting]) -> None:
        with self.sightings_table.batch_writer() as batch:
            for sighting in sightings:
                item = _decimalize(model_to_dict(sighting))
                item["pk"] = sighting.sighting_id
                batch.put_item(Item=item)

    def list_sightings(self, limit: int = 500) -> List[NormalizedSighting]:
        response = self.sightings_table.scan(Limit=limit)
        return [NormalizedSighting(**item) for item in response.get("Items", [])]

    def put_hotspots(self, hotspots: List[Hotspot]) -> None:
        with self.hotspots_table.batch_writer() as batch:
            for hotspot in hotspots:
                item = _decimalize(model_to_dict(hotspot))
                item["pk"] = hotspot.hotspot_id
                batch.put_item(Item=item)

    def list_hotspots(self, limit: int = 100) -> List[Hotspot]:
        response = self.hotspots_table.scan(Limit=limit)
        hotspots = [Hotspot(**item) for item in response.get("Items", [])]
        return sorted(hotspots, key=lambda h: h.probability, reverse=True)[:limit]

    def put_report(self, report: ProbabilityReport) -> None:
        body = json.dumps(model_to_dict(report), default=_json_default, indent=2)
        key = f"reports/{report.report_id}.json"
        self.s3.put_object(Bucket=self.cfg.reports_bucket, Key=key, Body=body, ContentType="application/json")
        report.storage_uri = f"s3://{self.cfg.reports_bucket}/{key}"
        item = _decimalize(model_to_dict(report))
        item["pk"] = report.report_id
        self.reports_table.put_item(Item=item)

    def get_report(self, report_id: str) -> Optional[ProbabilityReport]:
        response = self.reports_table.get_item(Key={"pk": report_id})
        item = response.get("Item")
        return ProbabilityReport(**item) if item else None

    def put_ingestion_run(self, run: IngestionRun) -> None:
        item = _decimalize(model_to_dict(run))
        item["pk"] = run.run_id
        self.ingestion_runs_table.put_item(Item=item)

    def put_raw_payload(self, source: str, payload: Any, run_id: str) -> str:
        key = f"raw/{run_id}/{source}/{uuid4().hex[:12]}.json"
        body = json.dumps(payload, default=_json_default, indent=2)
        self.s3.put_object(Bucket=self.cfg.raw_payload_bucket, Key=key, Body=body, ContentType="application/json")
        return f"s3://{self.cfg.raw_payload_bucket}/{key}"


def build_storage(cfg: Settings = settings) -> StorageBackend:
    if cfg.storage_backend.lower() == "aws":
        return AwsStorage(cfg)
    return MemoryStorage()

