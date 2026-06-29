"""Storage for DTAG annotations.

The stored record carries the full 10-field provenance the client reads back,
plus server-only bookkeeping (``dedup_key`` for idempotency, ``simulated`` for
the honesty label). The wire reshaping into the client ``Annotation`` shape is
done in the router, not here.

Idempotency is content-key dedup. The AWS impl keys an item by
``pk=deployment_id`` and ``sk=annotation#{dedup_key}`` and writes with
``attribute_not_exists(sk)``, so a replayed create (for example a proxy 503
retry) collapses to the first writer's record instead of duplicating it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel

from ..config import Settings, settings


class StoredAnnotation(BaseModel):
    id: str
    deployment_id: str
    dedup_key: str
    simulated: bool
    target: Dict[str, Any]
    behavior: str
    state: Optional[str] = None
    confidence: Optional[float] = None
    notes: Optional[str] = None
    provenance: Dict[str, Any]
    created_at: str


class AnnotationStore(ABC):
    @abstractmethod
    def create(self, record: StoredAnnotation) -> Tuple[StoredAnnotation, bool]:
        """Persist a record idempotently.

        Returns the stored record and ``True`` when it was newly written, or the
        existing record and ``False`` when a record with the same ``dedup_key``
        was already present.
        """
        ...

    @abstractmethod
    def list_for_deployment(self, deployment_id: str, limit: int = 100) -> List[StoredAnnotation]:
        ...

    @abstractmethod
    def get(self, annotation_id: str) -> Optional[StoredAnnotation]:
        ...


class MemoryAnnotationStore(AnnotationStore):
    def __init__(self) -> None:
        self._by_id: Dict[str, StoredAnnotation] = {}
        self._by_dedup: Dict[str, str] = {}

    def create(self, record: StoredAnnotation) -> Tuple[StoredAnnotation, bool]:
        existing_id = self._by_dedup.get(record.dedup_key)
        if existing_id is not None:
            return self._by_id[existing_id], False
        self._by_id[record.id] = record
        self._by_dedup[record.dedup_key] = record.id
        return record, True

    def list_for_deployment(self, deployment_id: str, limit: int = 100) -> List[StoredAnnotation]:
        rows = [r for r in self._by_id.values() if r.deployment_id == deployment_id]
        return sorted(rows, key=lambda r: r.created_at, reverse=True)[:limit]

    def get(self, annotation_id: str) -> Optional[StoredAnnotation]:
        return self._by_id.get(annotation_id)


class AwsAnnotationStore(AnnotationStore):
    def __init__(self, cfg: Settings = settings) -> None:
        import boto3

        from ..storage import _decimalize, model_to_dict

        self._decimalize = _decimalize
        self._model_to_dict = model_to_dict
        self.table = boto3.resource("dynamodb", region_name=cfg.aws_region).Table(
            cfg.dtag_annotations_table
        )

    def create(self, record: StoredAnnotation) -> Tuple[StoredAnnotation, bool]:
        from botocore.exceptions import ClientError

        item = self._decimalize(self._model_to_dict(record))
        item["pk"] = record.deployment_id
        item["sk"] = f"annotation#{record.dedup_key}"
        try:
            # Content-key write-once: a replayed create cannot duplicate a record.
            self.table.put_item(Item=item, ConditionExpression="attribute_not_exists(sk)")
            return record, True
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                response = self.table.get_item(
                    Key={"pk": record.deployment_id, "sk": f"annotation#{record.dedup_key}"}
                )
                existing = response.get("Item")
                if existing:
                    return StoredAnnotation(**existing), False
                return record, False
            raise

    def list_for_deployment(self, deployment_id: str, limit: int = 100) -> List[StoredAnnotation]:
        from boto3.dynamodb.conditions import Key

        response = self.table.query(
            KeyConditionExpression=Key("pk").eq(deployment_id) & Key("sk").begins_with("annotation#"),
            Limit=limit,
        )
        rows = [StoredAnnotation(**item) for item in response.get("Items", [])]
        return sorted(rows, key=lambda r: r.created_at, reverse=True)[:limit]

    def get(self, annotation_id: str) -> Optional[StoredAnnotation]:
        # Get-by-id without the partition key uses a filtered scan. The annotation
        # set per simulated deployment is tiny; a GSI on `id` is the scale path.
        from boto3.dynamodb.conditions import Attr

        response = self.table.scan(FilterExpression=Attr("id").eq(annotation_id), Limit=1)
        items = response.get("Items", [])
        return StoredAnnotation(**items[0]) if items else None


def build_annotation_store(cfg: Settings = settings) -> AnnotationStore:
    if cfg.storage_backend.lower() == "aws":
        return AwsAnnotationStore(cfg)
    return MemoryAnnotationStore()
