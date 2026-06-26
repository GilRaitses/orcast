"""Per-user field journal storage (WorkOS user scoped)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from ..config import Settings, settings
from ..models import JournalEntry


class JournalStore(ABC):
    @abstractmethod
    def put_entry(self, entry: JournalEntry) -> None:
        ...

    @abstractmethod
    def list_entries(self, user_id: str, limit: int = 100) -> List[JournalEntry]:
        ...

    @abstractmethod
    def get_entry(self, user_id: str, entry_id: str) -> Optional[JournalEntry]:
        ...

    @abstractmethod
    def update_entry(self, entry: JournalEntry) -> None:
        ...


class MemoryJournalStore(JournalStore):
    def __init__(self) -> None:
        self._entries: dict[tuple[str, str], JournalEntry] = {}

    def put_entry(self, entry: JournalEntry) -> None:
        self._entries[(entry.user_id, entry.id)] = entry

    def list_entries(self, user_id: str, limit: int = 100) -> List[JournalEntry]:
        rows = [e for (uid, _), e in self._entries.items() if uid == user_id]
        return sorted(rows, key=lambda e: e.created_at, reverse=True)[:limit]

    def get_entry(self, user_id: str, entry_id: str) -> Optional[JournalEntry]:
        return self._entries.get((user_id, entry_id))

    def update_entry(self, entry: JournalEntry) -> None:
        self.put_entry(entry)


class AwsJournalStore(JournalStore):
    def __init__(self, cfg: Settings = settings) -> None:
        import boto3

        from ..storage import _decimalize, model_to_dict

        self._decimalize = _decimalize
        self._model_to_dict = model_to_dict
        self.table = boto3.resource("dynamodb", region_name=cfg.aws_region).Table(
            cfg.journal_table
        )

    def put_entry(self, entry: JournalEntry) -> None:
        item = self._decimalize(self._model_to_dict(entry))
        item["pk"] = entry.user_id
        item["sk"] = f"entry#{entry.id}"
        self.table.put_item(Item=item)

    def list_entries(self, user_id: str, limit: int = 100) -> List[JournalEntry]:
        from boto3.dynamodb.conditions import Key

        response = self.table.query(
            KeyConditionExpression=Key("pk").eq(user_id),
            ScanIndexForward=False,
            Limit=limit,
        )
        return [JournalEntry(**item) for item in response.get("Items", [])]

    def get_entry(self, user_id: str, entry_id: str) -> Optional[JournalEntry]:
        response = self.table.get_item(Key={"pk": user_id, "sk": f"entry#{entry_id}"})
        item = response.get("Item")
        return JournalEntry(**item) if item else None

    def update_entry(self, entry: JournalEntry) -> None:
        self.put_entry(entry)


def build_journal_store(cfg: Settings = settings) -> JournalStore:
    if cfg.storage_backend.lower() == "aws":
        return AwsJournalStore(cfg)
    return MemoryJournalStore()
