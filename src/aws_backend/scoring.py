from __future__ import annotations

import math
import hashlib
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Tuple

from .geo_region import in_bounds, snap_to_water
from .models import EnvironmentalSnapshot, Hotspot, NormalizedSighting, ValidationStatus
from .validation import haversine_km

MODEL_VERSION = "aws-deterministic-hotspot-v1"


def generate_hotspots(sightings: Iterable[NormalizedSighting], cell_size_degrees: float = 0.05) -> List[Hotspot]:
    usable = [
        sighting
        for sighting in sightings
        if sighting.cross_validation.status != ValidationStatus.REJECTED
    ]
    cells: Dict[Tuple[int, int], List[NormalizedSighting]] = defaultdict(list)
    for sighting in usable:
        key = (math.floor(sighting.latitude / cell_size_degrees), math.floor(sighting.longitude / cell_size_degrees))
        cells[key].append(sighting)

    hotspots: List[Hotspot] = []
    for index, (_cell, records) in enumerate(cells.items(), start=1):
        center_lat = sum(s.latitude for s in records) / len(records)
        center_lng = sum(s.longitude for s in records) / len(records)
        # Drop clusters whose centroid falls outside the pilot region, and clamp
        # in-region centroids onto water so no hotspot renders on land.
        if not in_bounds(center_lat, center_lng):
            continue
        center_lat, center_lng = snap_to_water(center_lat, center_lng)
        source_count = len({s.source for s in records})
        validated_count = sum(1 for s in records if s.cross_validation.status in {ValidationStatus.VERIFIED, ValidationStatus.LIKELY})
        behavior_distribution = Counter(s.behavior for s in records)
        avg_validation = sum(s.cross_validation.score for s in records) / len(records)
        avg_reliability = sum(s.source_reliability for s in records) / len(records)
        recency = _recency_score(records)
        density = min(1.0, len(records) / 8.0)
        behavior_score = _behavior_score(behavior_distribution)
        environmental = _environmental_summary(records)
        environmental_score = _environmental_suitability(environmental)

        probability = min(
            0.97,
            0.18
            + density * 0.22
            + recency * 0.14
            + avg_validation * 0.22
            + avg_reliability * 0.12
            + behavior_score * 0.07
            + environmental_score * 0.05,
        )
        confidence = min(0.98, 0.35 + avg_validation * 0.35 + min(0.2, source_count * 0.08) + density * 0.1)

        radius = max(
            1.0,
            max((haversine_km(center_lat, center_lng, s.latitude, s.longitude) for s in records), default=1.0),
        )
        reason_codes = [
            f"{len(records)} sighting(s) in cluster",
            f"{source_count} source(s)",
            f"validation {avg_validation:.2f}",
            f"reliability {avg_reliability:.2f}",
            f"recency {recency:.2f}",
        ]
        top_location = _most_common_location(records) or f"Hotspot {index}"
        hotspot_key = hashlib.sha1(f"{center_lat:.3f}:{center_lng:.3f}".encode("utf-8")).hexdigest()[:10]
        hotspots.append(
            Hotspot(
                hotspot_id=f"hotspot_{hotspot_key}",
                name=top_location,
                center_latitude=round(center_lat, 6),
                center_longitude=round(center_lng, 6),
                radius_km=round(radius, 3),
                probability=round(probability, 3),
                confidence=round(confidence, 3),
                detection_count=len(records),
                validated_detection_count=validated_count,
                source_count=source_count,
                behavior_distribution=dict(behavior_distribution),
                environmental_factors=environmental,
                reason_codes=reason_codes,
                evidence_sighting_ids=[s.sighting_id for s in records[:10]],
                model_version=MODEL_VERSION,
            )
        )

    return sorted(hotspots, key=lambda h: (h.probability, h.confidence, h.detection_count), reverse=True)


def probability_at_location(lat: float, lng: float, hotspots: List[Hotspot], environment: EnvironmentalSnapshot | None = None) -> Dict[str, Any]:
    if not hotspots:
        return {
            "probability": 0.12,
            "confidence": 0.35,
            "nearest_hotspot": None,
            "behavior_prediction": {"primary": "unknown", "probabilities": {"unknown": 1.0}},
            "environmental_factors": {},
            "model_version": MODEL_VERSION,
        }

    weighted_probability = 0.0
    weighted_confidence = 0.0
    total_weight = 0.0
    nearest = min(hotspots, key=lambda h: haversine_km(lat, lng, h.center_latitude, h.center_longitude))
    for hotspot in hotspots:
        distance = haversine_km(lat, lng, hotspot.center_latitude, hotspot.center_longitude)
        weight = math.exp(-distance / max(1.5, hotspot.radius_km + 2.0))
        weighted_probability += hotspot.probability * weight
        weighted_confidence += hotspot.confidence * weight
        total_weight += weight

    probability = weighted_probability / total_weight if total_weight else 0.12
    confidence = weighted_confidence / total_weight if total_weight else 0.35
    if environment:
        probability = min(0.98, probability + (_environmental_snapshot_score(environment) - 0.5) * 0.08)

    behavior_probs = _behavior_probabilities(nearest.behavior_distribution)
    primary = max(behavior_probs, key=behavior_probs.get) if behavior_probs else "unknown"
    return {
        "probability": round(probability, 3),
        "confidence": round(confidence, 3),
        "nearest_hotspot": {
            "hotspot_id": nearest.hotspot_id,
            "name": nearest.name,
            "distance_km": round(haversine_km(lat, lng, nearest.center_latitude, nearest.center_longitude), 2),
        },
        "behavior_prediction": {"primary": primary, "probabilities": behavior_probs},
        "environmental_factors": _environment_to_dict(environment) if environment else {},
        "model_version": MODEL_VERSION,
    }


def spatial_forecast_grid(
    center_lat: float,
    center_lng: float,
    radius_km: float,
    hotspots: List[Hotspot],
    environment: EnvironmentalSnapshot | None = None,
    step_degrees: float = 0.05,
    forecast_hours: int = 24,
) -> List[Dict[str, Any]]:
    horizon_factor = min(1.0, max(0.05, forecast_hours / 168.0))
    lat_span = radius_km / 111.0
    lng_span = radius_km / (111.0 * math.cos(math.radians(center_lat)))
    points: List[Dict[str, Any]] = []
    lat = center_lat - lat_span
    while lat <= center_lat + lat_span + 1e-9:
        lng = center_lng - lng_span
        while lng <= center_lng + lng_span + 1e-9:
            pred = probability_at_location(lat, lng, hotspots, environment)
            points.append(
                {
                    "lat": round(lat, 6),
                    "lng": round(lng, 6),
                    "probability": round(pred["probability"] * horizon_factor, 3),
                    "confidence": pred["confidence"],
                    "predicted_behavior": pred["behavior_prediction"]["primary"],
                    "model_version": MODEL_VERSION,
                    "forecast_hours": forecast_hours,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            lng += step_degrees
        lat += step_degrees
    return sorted(points, key=lambda p: p["probability"], reverse=True)


def _recency_score(records: List[NormalizedSighting]) -> float:
    now = datetime.now(timezone.utc)
    scores = []
    for record in records:
        age_days = max(0.0, (now - record.timestamp).total_seconds() / 86400.0)
        scores.append(math.exp(-age_days / 365.0))
    return sum(scores) / len(scores) if scores else 0.0


def _behavior_score(distribution: Counter) -> float:
    feeding = distribution.get("feeding", 0) + distribution.get("foraging", 0)
    social = distribution.get("socializing", 0)
    total = sum(distribution.values()) or 1
    return min(1.0, (feeding * 0.8 + social * 0.4) / total)


def _environmental_summary(records: List[NormalizedSighting]) -> Dict[str, Any]:
    temps = [s.environmental.water_temp_c for s in records if s.environmental and s.environmental.water_temp_c is not None]
    tides = [s.environmental.tide_height_ft for s in records if s.environmental and s.environmental.tide_height_ft is not None]
    return {
        "avg_water_temp_c": round(sum(temps) / len(temps), 2) if temps else None,
        "avg_tide_height_ft": round(sum(tides) / len(tides), 2) if tides else None,
        "environmental_record_count": len(temps) or len(tides),
    }


def _environmental_suitability(summary: Dict[str, Any]) -> float:
    score = 0.5
    temp = summary.get("avg_water_temp_c")
    tide = summary.get("avg_tide_height_ft")
    if temp is not None:
        score += max(0.0, 1.0 - abs(temp - 15.0) / 8.0) * 0.3
    if tide is not None:
        score += min(1.0, abs(tide) / 4.0) * 0.2
    return min(1.0, score)


def _environmental_snapshot_score(snapshot: EnvironmentalSnapshot) -> float:
    return _environmental_suitability(
        {
            "avg_water_temp_c": snapshot.water_temp_c,
            "avg_tide_height_ft": snapshot.tide_height_ft,
        }
    )


def _most_common_location(records: List[NormalizedSighting]) -> str | None:
    locations = [s.location_name for s in records if s.location_name]
    if not locations:
        return None
    return Counter(locations).most_common(1)[0][0]


def _behavior_probabilities(distribution: Dict[str, int]) -> Dict[str, float]:
    total = sum(distribution.values())
    if not total:
        return {"unknown": 1.0}
    return {behavior: round(count / total, 3) for behavior, count in distribution.items()}


def _environment_to_dict(environment: EnvironmentalSnapshot | None) -> Dict[str, Any]:
    if not environment:
        return {}
    return {
        "tide_height_ft": environment.tide_height_ft,
        "water_temp_c": environment.water_temp_c,
        "salinity_ppt": environment.salinity_ppt,
        "current_speed": environment.current_speed,
        "quality": environment.quality,
        "data_sources": environment.data_sources,
    }

