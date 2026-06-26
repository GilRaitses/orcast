from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .config import Settings, settings
from .models import (
    CommunitySubmission,
    CommunitySubmissionStatus,
    DecisionRecord,
    Hotspot,
    IngestionRun,
    NormalizedSighting,
    ProbabilityReport,
    utc_now,
)


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

    @abstractmethod
    def put_community_submission(self, sub: CommunitySubmission) -> None:
        ...

    @abstractmethod
    def list_community_submissions(self, status: Optional[str] = None) -> List[CommunitySubmission]:
        ...

    @abstractmethod
    def get_community_submission(self, submission_id: str) -> Optional[CommunitySubmission]:
        ...

    @abstractmethod
    def update_community_submission_status(
        self,
        submission_id: str,
        status: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        reviewed_by: Optional[str] = None,
        reviewer_email: Optional[str] = None,
        review_reason: Optional[str] = None,
    ) -> Optional[CommunitySubmission]:
        ...

    @abstractmethod
    def put_decision_record(self, record: DecisionRecord) -> None:
        ...

    @abstractmethod
    def list_decision_records(self, limit: int = 200) -> List[DecisionRecord]:
        ...

    @abstractmethod
    def get_decision_record(self, record_id: str) -> Optional[DecisionRecord]:
        ...


class MemoryStorage(StorageBackend):
    def __init__(self) -> None:
        self.sightings: Dict[str, NormalizedSighting] = {}
        self.hotspots: Dict[str, Hotspot] = {}
        self.reports: Dict[str, ProbabilityReport] = {}
        self.ingestion_runs: Dict[str, IngestionRun] = {}
        self.raw_payloads: Dict[str, Any] = {}
        self.community_submissions: Dict[str, CommunitySubmission] = {}
        self.decision_records: Dict[str, DecisionRecord] = {}

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

    def put_community_submission(self, sub: CommunitySubmission) -> None:
        self.community_submissions[sub.id] = sub

    def list_community_submissions(self, status: Optional[str] = None) -> List[CommunitySubmission]:
        submissions = list(self.community_submissions.values())
        if status is not None:
            submissions = [s for s in submissions if s.status.value == status]
        return sorted(submissions, key=lambda s: s.submitted_at, reverse=True)

    def get_community_submission(self, submission_id: str) -> Optional[CommunitySubmission]:
        return self.community_submissions.get(submission_id)

    def update_community_submission_status(
        self,
        submission_id: str,
        status: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        reviewed_by: Optional[str] = None,
        reviewer_email: Optional[str] = None,
        review_reason: Optional[str] = None,
    ) -> Optional[CommunitySubmission]:
        submission = self.community_submissions.get(submission_id)
        if submission is None:
            return None
        if submission.status != CommunitySubmissionStatus.PENDING:
            return submission
        submission.status = CommunitySubmissionStatus(status)
        submission.reviewed_at = utc_now()
        if latitude is not None:
            submission.latitude = latitude
        if longitude is not None:
            submission.longitude = longitude
        submission.reviewed_by = reviewed_by
        submission.reviewer_email = reviewer_email
        submission.review_reason = review_reason
        self.community_submissions[submission_id] = submission
        return submission

    def put_decision_record(self, record: DecisionRecord) -> None:
        self.decision_records[record.id] = record

    def list_decision_records(self, limit: int = 200) -> List[DecisionRecord]:
        return sorted(self.decision_records.values(), key=lambda r: r.created_at, reverse=True)[:limit]

    def get_decision_record(self, record_id: str) -> Optional[DecisionRecord]:
        return self.decision_records.get(record_id)


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
        self.community_table = self.dynamodb.Table(cfg.community_table)
        self.decision_records_table = self.dynamodb.Table(cfg.decision_records_table)

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

    def put_community_submission(self, sub: CommunitySubmission) -> None:
        item = _decimalize(model_to_dict(sub))
        item["pk"] = sub.id
        item["status"] = sub.status.value
        self.community_table.put_item(Item=item)

    def list_community_submissions(self, status: Optional[str] = None) -> List[CommunitySubmission]:
        response = self.community_table.scan()
        submissions = [CommunitySubmission(**item) for item in response.get("Items", [])]
        if status is not None:
            submissions = [s for s in submissions if s.status.value == status]
        return sorted(submissions, key=lambda s: s.submitted_at, reverse=True)

    def get_community_submission(self, submission_id: str) -> Optional[CommunitySubmission]:
        response = self.community_table.get_item(Key={"pk": submission_id})
        item = response.get("Item")
        return CommunitySubmission(**item) if item else None

    def update_community_submission_status(
        self,
        submission_id: str,
        status: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        reviewed_by: Optional[str] = None,
        reviewer_email: Optional[str] = None,
        review_reason: Optional[str] = None,
    ) -> Optional[CommunitySubmission]:
        submission = self.get_community_submission(submission_id)
        if submission is None:
            return None
        if submission.status != CommunitySubmissionStatus.PENDING:
            return submission
        submission.status = CommunitySubmissionStatus(status)
        submission.reviewed_at = utc_now()
        if latitude is not None:
            submission.latitude = latitude
        if longitude is not None:
            submission.longitude = longitude
        submission.reviewed_by = reviewed_by
        submission.reviewer_email = reviewer_email
        submission.review_reason = review_reason
        item = _decimalize(model_to_dict(submission))
        item["pk"] = submission_id
        item["status"] = status
        try:
            from botocore.exceptions import ClientError

            self.community_table.put_item(
                Item=item,
                ConditionExpression="#st = :pending",
                ExpressionAttributeNames={"#st": "status"},
                ExpressionAttributeValues={":pending": CommunitySubmissionStatus.PENDING.value},
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return self.get_community_submission(submission_id)
            raise
        return submission

    def put_decision_record(self, record: DecisionRecord) -> None:
        item = _decimalize(model_to_dict(record))
        item["pk"] = record.id
        item["verdict"] = record.verdict.value
        # Audit records are write-once: refuse to overwrite an existing pk so a
        # promotion decision can never be silently rewritten.
        self.decision_records_table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(pk)",
        )

    def list_decision_records(self, limit: int = 200) -> List[DecisionRecord]:
        response = self.decision_records_table.scan()
        records = [DecisionRecord(**item) for item in response.get("Items", [])]
        return sorted(records, key=lambda r: r.created_at, reverse=True)[:limit]

    def get_decision_record(self, record_id: str) -> Optional[DecisionRecord]:
        response = self.decision_records_table.get_item(Key={"pk": record_id})
        item = response.get("Item")
        return DecisionRecord(**item) if item else None


def build_storage(cfg: Settings = settings) -> StorageBackend:
    if cfg.storage_backend.lower() == "aws":
        return AwsStorage(cfg)
    return MemoryStorage()

