from __future__ import annotations

import hashlib
import math
from datetime import datetime
from typing import Iterable, List

from .models import CrossValidationResult, NormalizedSighting, SourceEvidence, ValidationStatus


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius_km * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def valid_coordinates(latitude: float, longitude: float) -> bool:
    return -90 <= latitude <= 90 and -180 <= longitude <= 180 and not (latitude == 0 and longitude == 0)


def time_score(left: datetime, right: datetime, max_hours: float = 24.0) -> float:
    delta_hours = abs((left - right).total_seconds()) / 3600.0
    if delta_hours >= max_hours:
        return 0.0
    return 1.0 - (delta_hours / max_hours)


def stable_canonical_id(sighting: NormalizedSighting, spatial_precision: int = 2) -> str:
    key = "|".join(
        [
            f"{round(sighting.latitude, spatial_precision):.{spatial_precision}f}",
            f"{round(sighting.longitude, spatial_precision):.{spatial_precision}f}",
            sighting.timestamp.strftime("%Y-%m-%d"),
            sighting.common_name.lower(),
        ]
    )
    return "canon_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def deduplicate_sightings(
    sightings: Iterable[NormalizedSighting],
    spatial_radius_km: float = 5.0,
    temporal_window_hours: float = 24.0,
) -> List[NormalizedSighting]:
    deduped: List[NormalizedSighting] = []
    by_source = {}

    for sighting in sightings:
        if not valid_coordinates(sighting.latitude, sighting.longitude):
            sighting.cross_validation = CrossValidationResult(
                status=ValidationStatus.REJECTED,
                score=0.0,
                reasons=["invalid_coordinates"],
            )
            continue

        source_key = f"{sighting.source}:{sighting.source_id}"
        if source_key in by_source:
            continue
        by_source[source_key] = sighting

        matched = None
        for existing in deduped:
            distance = haversine_km(
                sighting.latitude,
                sighting.longitude,
                existing.latitude,
                existing.longitude,
            )
            temporal_score = time_score(sighting.timestamp, existing.timestamp, temporal_window_hours)
            if distance <= spatial_radius_km and temporal_score > 0:
                matched = existing
                break

        if matched:
            matched.evidence.extend(sighting.evidence)
            matched.confidence = max(matched.confidence, sighting.confidence)
            matched.source_reliability = max(matched.source_reliability, sighting.source_reliability)
            if sighting.source not in {e.source for e in matched.evidence}:
                matched.evidence.append(
                    sighting.evidence[0]
                    if sighting.evidence
                    else SourceEvidence(
                        source=sighting.source,
                        source_id=sighting.source_id,
                        reliability=sighting.source_reliability,
                    )
                )
        else:
            sighting.canonical_id = stable_canonical_id(sighting)
            deduped.append(sighting)

    return deduped


def cross_validate_sightings(
    sightings: List[NormalizedSighting],
    spatial_radius_km: float = 10.0,
    temporal_window_hours: float = 48.0,
) -> List[NormalizedSighting]:
    for sighting in sightings:
        independent_sources = {sighting.source}
        spatial_matches = 0
        temporal_matches = 0
        matched_ids: List[str] = []

        for other in sightings:
            if other.sighting_id == sighting.sighting_id:
                continue
            distance = haversine_km(sighting.latitude, sighting.longitude, other.latitude, other.longitude)
            temporal = time_score(sighting.timestamp, other.timestamp, temporal_window_hours)
            if distance <= spatial_radius_km:
                spatial_matches += 1
            if temporal > 0:
                temporal_matches += 1
            if distance <= spatial_radius_km and temporal > 0:
                independent_sources.add(other.source)
                matched_ids.append(other.sighting_id)

        evidence_score = min(1.0, (len(sighting.evidence) * 0.2) + sighting.confidence * 0.5 + sighting.source_reliability * 0.3)
        source_score = min(1.0, len(independent_sources) / 3.0)
        match_score = min(1.0, (spatial_matches + temporal_matches) / 6.0)
        environmental_score = 0.65 if sighting.environmental else 0.45
        score = min(1.0, source_score * 0.35 + match_score * 0.25 + evidence_score * 0.3 + environmental_score * 0.1)

        if score >= 0.8:
            status = ValidationStatus.VERIFIED
        elif score >= 0.6:
            status = ValidationStatus.LIKELY
        elif score >= 0.35:
            status = ValidationStatus.TENTATIVE
        else:
            status = ValidationStatus.REJECTED

        reasons = [
            f"{len(independent_sources)} independent source(s)",
            f"{spatial_matches} spatial match(es)",
            f"{temporal_matches} temporal match(es)",
            f"evidence score {evidence_score:.2f}",
        ]

        sighting.cross_validation = CrossValidationResult(
            status=status,
            score=round(score, 3),
            independent_source_count=len(independent_sources),
            spatial_matches=spatial_matches,
            temporal_matches=temporal_matches,
            evidence_score=round(evidence_score, 3),
            environmental_score=round(environmental_score, 3),
            matched_sighting_ids=matched_ids,
            reasons=reasons,
        )

    return sightings

