from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Tuple

from .config import Settings, settings


def _sanitize(value: str) -> str:
    """Reduce an arbitrary string to a safe key segment."""
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "unknown"


def _parse_t(record: Dict[str, Any]) -> datetime:
    raw = record["t"]
    if isinstance(raw, datetime):
        return raw
    # datetime.fromisoformat does not accept a trailing 'Z' before 3.11.
    text = raw.replace("Z", "+00:00") if isinstance(raw, str) else raw
    return datetime.fromisoformat(text)


def _record_key(record: Dict[str, Any]) -> Tuple[str, str]:
    """Stable identity for dedupe: ISO 't' plus an optional 'id'."""
    return (str(record.get("t")), str(record.get("id", "")))


def _merge_records(existing: List[Dict[str, Any]], incoming: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Union existing + incoming by (t, id), incoming wins, sorted by t."""
    merged: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for record in existing:
        merged[_record_key(record)] = record
    for record in incoming:
        merged[_record_key(record)] = record
    return sorted(merged.values(), key=_parse_t)


class TimeSeriesStore(ABC):
    @abstractmethod
    def put_series(self, stream: str, station: str, records: List[Dict[str, Any]]) -> int:
        ...

    @abstractmethod
    def get_series(self, stream: str, station: str, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    def list_stations(self, stream: str) -> List[str]:
        ...


class MemoryTimeSeriesStore(TimeSeriesStore):
    def __init__(self) -> None:
        self._series: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)

    def put_series(self, stream: str, station: str, records: List[Dict[str, Any]]) -> int:
        if not records:
            return 0
        key = (stream, _sanitize(station))
        self._series[key] = _merge_records(self._series.get(key, []), records)
        return len(records)

    def get_series(self, stream: str, station: str, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        key = (stream, _sanitize(station))
        records = self._series.get(key, [])
        in_range = [r for r in records if start <= _parse_t(r) <= end]
        return sorted(in_range, key=_parse_t)

    def list_stations(self, stream: str) -> List[str]:
        stations = {station for (s, station) in self._series if s == stream and self._series[(s, station)]}
        return sorted(stations)


class S3TimeSeriesStore(TimeSeriesStore):
    def __init__(self, cfg: Settings = settings) -> None:
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("boto3 is required for ORCAST_STORAGE_BACKEND=aws") from exc

        self.cfg = cfg
        self.bucket = cfg.raw_payload_bucket
        self.s3 = boto3.client("s3", region_name=cfg.aws_region)

    def _prefix(self, stream: str, station: str) -> str:
        return f"timeseries/{stream}/{_sanitize(station)}/"

    def _key(self, stream: str, station: str, year: int, month: int) -> str:
        return f"{self._prefix(stream, station)}{year:04d}/{month:02d}.ndjson"

    def _read_partition(self, key: str) -> List[Dict[str, Any]]:
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
        except self.s3.exceptions.NoSuchKey:
            return []
        body = response["Body"].read().decode("utf-8")
        return [json.loads(line) for line in body.splitlines() if line.strip()]

    def _write_partition(self, key: str, records: List[Dict[str, Any]]) -> None:
        body = "\n".join(json.dumps(record) for record in records)
        if body:
            body += "\n"
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=body.encode("utf-8"),
            ContentType="application/x-ndjson",
        )

    def put_series(self, stream: str, station: str, records: List[Dict[str, Any]]) -> int:
        if not records:
            return 0
        by_month: Dict[Tuple[int, int], List[Dict[str, Any]]] = defaultdict(list)
        for record in records:
            t = _parse_t(record)
            by_month[(t.year, t.month)].append(record)

        for (year, month), incoming in by_month.items():
            key = self._key(stream, station, year, month)
            merged = _merge_records(self._read_partition(key), incoming)
            self._write_partition(key, merged)
        return len(records)

    def _list_partition_keys(self, prefix: str) -> List[str]:
        keys: List[str] = []
        token = None
        while True:
            kwargs: Dict[str, Any] = {"Bucket": self.bucket, "Prefix": prefix}
            if token:
                kwargs["ContinuationToken"] = token
            response = self.s3.list_objects_v2(**kwargs)
            for obj in response.get("Contents", []):
                if obj["Key"].endswith(".ndjson"):
                    keys.append(obj["Key"])
            if response.get("IsTruncated"):
                token = response.get("NextContinuationToken")
            else:
                break
        return keys

    def get_series(self, stream: str, station: str, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        prefix = self._prefix(stream, station)
        results: List[Dict[str, Any]] = []
        for key in self._list_partition_keys(prefix):
            match = re.search(r"/(\d{4})/(\d{2})\.ndjson$", key)
            if not match:
                continue
            year, month = int(match.group(1)), int(match.group(2))
            if (year, month) < (start.year, start.month) or (year, month) > (end.year, end.month):
                continue
            for record in self._read_partition(key):
                if start <= _parse_t(record) <= end:
                    results.append(record)
        return sorted(results, key=_parse_t)

    def list_stations(self, stream: str) -> List[str]:
        prefix = f"timeseries/{stream}/"
        stations: List[str] = []
        token = None
        while True:
            kwargs: Dict[str, Any] = {"Bucket": self.bucket, "Prefix": prefix, "Delimiter": "/"}
            if token:
                kwargs["ContinuationToken"] = token
            response = self.s3.list_objects_v2(**kwargs)
            for entry in response.get("CommonPrefixes", []):
                station = entry["Prefix"][len(prefix):].rstrip("/")
                if station:
                    stations.append(station)
            if response.get("IsTruncated"):
                token = response.get("NextContinuationToken")
            else:
                break
        return sorted(stations)


def build_timeseries_store(cfg: Settings = settings) -> TimeSeriesStore:
    if cfg.storage_backend.lower() == "aws":
        return S3TimeSeriesStore(cfg)
    return MemoryTimeSeriesStore()
