"""Habitat spatial layers for Salish Sea ecological covariates."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

import requests

from ..geo_region import SAN_JUAN_BOUNDS

# BC ShoreZone/CRIMS public ArcGIS layer (habitat polygons).
_SHOREZONE_URL = (
    "https://maps.gov.bc.ca/arcgis/rest/services/whse/bcgw_pub_whse_fish_and_wildlife/MapServer/30/query"
)


class HabitatAdapter:
    source_name = "bc_shorezone"
    reliability = 0.8

    def __init__(self, timeout: float = 20.0) -> None:
        self.timeout = timeout

    def fetch_features(self, result_record_count: int = 100) -> List[Dict[str, object]]:
        params = {
            "where": "1=1",
            "geometry": (
                f"{SAN_JUAN_BOUNDS.min_lng},{SAN_JUAN_BOUNDS.min_lat},"
                f"{SAN_JUAN_BOUNDS.max_lng},{SAN_JUAN_BOUNDS.max_lat}"
            ),
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "FEATURE_CODE,FEATURE_LABEL,PHYSIOGRAPH,BEACH_WIDTH",
            "returnGeometry": "true",
            "resultRecordCount": result_record_count,
            "f": "json",
        }
        try:
            response = requests.get(_SHOREZONE_URL, params=params, timeout=self.timeout)
        except requests.RequestException:
            return []
        if response.status_code != 200:
            return []
        payload = response.json()
        now = datetime.now(timezone.utc).isoformat()
        records: List[Dict[str, object]] = []
        for idx, feature in enumerate(payload.get("features") or []):
            attrs = feature.get("attributes") or {}
            records.append(
                {
                    "t": now,
                    "id": f"shorezone:{idx}",
                    "feature_code": attrs.get("FEATURE_CODE"),
                    "feature_label": attrs.get("FEATURE_LABEL"),
                    "physiograph": attrs.get("PHYSIOGRAPH"),
                    "beach_width": attrs.get("BEACH_WIDTH"),
                    "geometry": feature.get("geometry"),
                    "source": self.source_name,
                    "source_url": response.url,
                }
            )
        return records
