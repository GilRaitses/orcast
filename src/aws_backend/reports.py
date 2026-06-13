from __future__ import annotations

import hashlib
from collections import Counter
from datetime import datetime, timezone
from typing import List

from .models import Hotspot, IngestionRun, NormalizedSighting, ProbabilityReport, ProbabilityReportRequest, SourceStatus


def build_probability_report(
    request: ProbabilityReportRequest,
    sightings: List[NormalizedSighting],
    hotspots: List[Hotspot],
    latest_run: IngestionRun | None = None,
) -> ProbabilityReport:
    filtered_hotspots = [h for h in hotspots if h.confidence >= request.min_confidence]
    if request.include_sources:
        allowed = set(request.include_sources)
        filtered_sightings = [s for s in sightings if s.source in allowed]
    else:
        filtered_sightings = sightings

    status_counts = Counter(s.cross_validation.status.value for s in filtered_sightings)
    source_counts = Counter(s.source for s in filtered_sightings)
    behavior_counts = Counter(s.behavior for s in filtered_sightings)
    top = filtered_hotspots[0] if filtered_hotspots else None

    summary = (
        f"{len(filtered_hotspots)} hotspot(s) generated from {len(filtered_sightings)} normalized sighting(s). "
        f"Top hotspot: {top.name} with {top.probability:.0%} probability."
        if top
        else f"No hotspots met confidence threshold from {len(filtered_sightings)} sighting(s)."
    )
    report_id = _report_id(request.region, filtered_hotspots, filtered_sightings)
    warnings = []
    if not filtered_sightings:
        warnings.append("No sightings matched report filters.")
    if latest_run and latest_run.errors:
        warnings.extend(latest_run.errors[:5])
    if any(status.source == "orcahello" and not status.available for status in (latest_run.statuses if latest_run else [])):
        warnings.append("OrcaHello source unavailable or returned non-JSON content during ingestion.")

    return ProbabilityReport(
        report_id=report_id,
        generated_at=datetime.now(timezone.utc),
        region=request.region,
        summary=summary,
        hotspots=filtered_hotspots,
        source_status=latest_run.statuses if latest_run else [],
        cross_validation_summary={
            "status_counts": dict(status_counts),
            "source_counts": dict(source_counts),
            "behavior_counts": dict(behavior_counts),
            "sightings_used": len(filtered_sightings),
            "validated_sightings": status_counts.get("verified", 0) + status_counts.get("likely", 0),
        },
        environmental_summary=_environmental_summary(filtered_sightings),
        data_quality_warnings=warnings,
    )


def _report_id(region: str, hotspots: List[Hotspot], sightings: List[NormalizedSighting]) -> str:
    material = "|".join(
        [
            region,
            ",".join(h.hotspot_id for h in hotspots[:10]),
            ",".join(s.sighting_id for s in sightings[:25]),
            datetime.now(timezone.utc).strftime("%Y%m%d%H%M"),
        ]
    )
    return "report_" + hashlib.sha1(material.encode("utf-8")).hexdigest()[:16]


def _environmental_summary(sightings: List[NormalizedSighting]):
    temperatures = [s.environmental.water_temp_c for s in sightings if s.environmental and s.environmental.water_temp_c is not None]
    tides = [s.environmental.tide_height_ft for s in sightings if s.environmental and s.environmental.tide_height_ft is not None]
    return {
        "records_with_environment": len([s for s in sightings if s.environmental]),
        "avg_water_temp_c": round(sum(temperatures) / len(temperatures), 2) if temperatures else None,
        "avg_tide_height_ft": round(sum(tides) / len(tides), 2) if tides else None,
    }

