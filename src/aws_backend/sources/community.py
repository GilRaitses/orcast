from __future__ import annotations

from typing import List

from ..geo_region import filter_and_snap
from ..models import NormalizedSighting, SourceEvidence
from ..storage import model_to_dict
from .base import SourceAdapter, SourceFetchResult


class CommunitySubmissionAdapter(SourceAdapter):
    source_name = "community"
    reliability = 0.35

    def fetch(self) -> SourceFetchResult:
        from ..state import storage

        approved = storage.list_community_submissions(status="approved")
        raw = [model_to_dict(submission) for submission in approved]
        return SourceFetchResult(source=self.source_name, available=True, raw=raw)

    def normalize(self, result: SourceFetchResult) -> List[NormalizedSighting]:
        if not result.available or not isinstance(result.raw, list):
            return []

        sightings: List[NormalizedSighting] = []
        skipped = 0
        for item in result.raw:
            latitude = item.get("latitude")
            longitude = item.get("longitude")
            if latitude is None or longitude is None:
                skipped += 1
                continue
            snapped = filter_and_snap(float(latitude), float(longitude))
            if snapped is None:
                skipped += 1
                continue
            latitude, longitude = snapped
            submission_id = item.get("id")
            evidence = SourceEvidence(
                source=self.source_name,
                source_id=str(submission_id),
                reliability=self.reliability,
                quality_grade="community",
                notes="Community-submitted, moderated",
            )
            sightings.append(
                NormalizedSighting(
                    sighting_id=f"community:{submission_id}",
                    source=self.source_name,
                    source_id=str(submission_id),
                    timestamp=item.get("observed_at"),
                    latitude=float(latitude),
                    longitude=float(longitude),
                    location_name=item.get("place"),
                    behavior=item.get("behavior", "unknown"),
                    count=item.get("count"),
                    confidence=0.5,
                    source_reliability=self.reliability,
                    evidence=[evidence],
                )
            )
        result.skipped_count = skipped
        return sightings
