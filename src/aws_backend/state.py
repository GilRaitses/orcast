from __future__ import annotations

import uuid
from typing import Any, List, Optional

from .config import settings
from .models import IngestionRun, SourceStatus
from .scoring import generate_hotspots
from .sources.community import CommunitySubmissionAdapter
from .sources.inaturalist import INaturalistAdapter
from .sources.local_obis import LocalObisAdapter
from .sources.noaa import NoaaAdapter
from .sources.orcahello import OrcaHelloAdapter
from .sources.orcasound import OrcasoundHydrophoneAdapter
from .storage import StorageBackend, build_storage
from .validation import cross_validate_sightings, deduplicate_sightings

storage: StorageBackend = build_storage(settings)
noaa = NoaaAdapter()
hydrophones = OrcasoundHydrophoneAdapter()
latest_ingestion_run: Optional[IngestionRun] = None


def get_latest_ingestion_run() -> Optional[IngestionRun]:
    return latest_ingestion_run


def ensure_hotspots() -> List[Any]:
    hotspots = storage.list_hotspots(limit=100)
    if hotspots:
        return hotspots
    hotspots = generate_hotspots(storage.list_sightings(limit=10_000))
    storage.put_hotspots(hotspots)
    return hotspots


def run_ingestion(include_live: bool = True) -> IngestionRun:
    global latest_ingestion_run
    run = IngestionRun(run_id=f"ingest_{uuid.uuid4().hex[:12]}")
    adapters = [LocalObisAdapter()]
    if include_live and settings.enable_live_inaturalist:
        adapters.append(INaturalistAdapter())
    if include_live and settings.enable_orcahello:
        adapters.append(OrcaHelloAdapter())
    if settings.enable_community:
        adapters.append(CommunitySubmissionAdapter())

    all_sightings = []
    statuses: List[SourceStatus] = []
    for adapter in adapters:
        result = adapter.fetch()
        raw_payload_ref = None
        if result.raw is not None:
            raw_payload_ref = storage.put_raw_payload(adapter.source_name, result.raw, run.run_id)
        normalized = adapter.normalize(result)
        if raw_payload_ref:
            for sighting in normalized:
                for evidence in sighting.evidence:
                    evidence.raw_payload_ref = raw_payload_ref
        statuses.append(adapter.status(result, len(normalized)))
        all_sightings.extend(normalized)
        if result.error:
            run.errors.append(f"{adapter.source_name}: {result.error}")

    deduped = deduplicate_sightings(all_sightings)
    validated = cross_validate_sightings(deduped)
    storage.put_sightings(validated)
    hotspots = generate_hotspots(validated)
    storage.put_hotspots(hotspots)

    run.statuses = statuses
    run.sightings_ingested = len(all_sightings)
    run.sightings_stored = len(validated)
    from datetime import datetime, timezone

    run.completed_at = datetime.now(timezone.utc)
    storage.put_ingestion_run(run)
    latest_ingestion_run = run
    return run
