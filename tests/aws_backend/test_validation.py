from datetime import datetime, timezone

from src.aws_backend.models import NormalizedSighting, SourceEvidence, ValidationStatus
from src.aws_backend.validation import cross_validate_sightings, deduplicate_sightings, haversine_km


def _sighting(source: str, source_id: str, lat: float, lng: float, confidence: float = 0.8):
    return NormalizedSighting(
        sighting_id=f"{source}:{source_id}",
        source=source,
        source_id=source_id,
        timestamp=datetime(2024, 6, 15, 14, 30, tzinfo=timezone.utc),
        latitude=lat,
        longitude=lng,
        confidence=confidence,
        source_reliability=confidence,
        evidence=[SourceEvidence(source=source, source_id=source_id, reliability=confidence)],
    )


def test_haversine_san_juan_short_distance():
    distance = haversine_km(48.5158, -123.1526, 48.5160, -123.1530)
    assert 0 < distance < 0.1


def test_cross_source_validation_scores_higher_than_single_source():
    obis = _sighting("obis_verified", "1", 48.5158, -123.1526, 0.96)
    inat = _sighting("inaturalist", "1", 48.5160, -123.1530, 0.82)
    low = _sighting("unknown_blog", "1", 48.7, -123.3, 0.35)

    validated = cross_validate_sightings([obis, inat, low])
    by_id = {s.sighting_id: s for s in validated}

    assert by_id["obis_verified:1"].cross_validation.score > by_id["unknown_blog:1"].cross_validation.score
    assert by_id["obis_verified:1"].cross_validation.independent_source_count == 2
    assert by_id["unknown_blog:1"].cross_validation.status in {ValidationStatus.TENTATIVE, ValidationStatus.REJECTED}


def test_deduplicate_keeps_one_nearby_canonical_sighting():
    obis = _sighting("obis_verified", "1", 48.5158, -123.1526, 0.96)
    inat = _sighting("inaturalist", "1", 48.5160, -123.1530, 0.82)

    deduped = deduplicate_sightings([obis, inat], spatial_radius_km=1, temporal_window_hours=24)

    assert len(deduped) == 1
    assert deduped[0].canonical_id
    assert len(deduped[0].evidence) >= 2

