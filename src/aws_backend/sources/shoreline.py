from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests


_CUSP_QUERY_URL = (
    "https://services2.arcgis.com/okXm0pb6aWH6XOGI/arcgis/rest/services/"
    "NOAA_CUSP/FeatureServer/0/query"
)


class ShorelineAdapter:
    """NOAA CUSP shoreline metadata snapshot for spatial integrity covariates."""

    source_name = "noaa_cusp_shoreline"
    reliability = 0.9

    def __init__(self, timeout: float = 20.0) -> None:
        self.timeout = timeout

    def fetch_features(
        self,
        result_record_count: int = 100,
        bbox: Optional[tuple[float, float, float, float]] = None,
    ) -> List[Dict[str, object]]:
        params: Dict[str, object] = {
            "where": "1=1",
            "outFields": "SOURCE_ID,SRC_DATE,HOR_ACC,VER_DATE,SRC_RESOLU,DATA_SOURC",
            "returnGeometry": "true",
            "resultRecordCount": result_record_count,
            "f": "json",
        }
        if bbox:
            xmin, ymin, xmax, ymax = bbox
            params.update({
                "geometry": f"{xmin},{ymin},{xmax},{ymax}",
                "geometryType": "esriGeometryEnvelope",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
            })
        response = requests.get(_CUSP_QUERY_URL, params=params, timeout=self.timeout)
        if response.status_code != 200:
            return []
        payload = response.json()
        now = datetime.now(timezone.utc).isoformat()
        features: List[Dict[str, object]] = []
        for idx, feature in enumerate(payload.get("features") or []):
            attrs = feature.get("attributes") or {}
            features.append({
                "t": now,
                "id": f"{attrs.get('SOURCE_ID') or 'shore'}:{idx}",
                "source": "noaa_cusp",
                "source_url": response.url,
                "source_id": attrs.get("SOURCE_ID"),
                "source_date": attrs.get("SRC_DATE"),
                "horizontal_accuracy": attrs.get("HOR_ACC"),
                "verification_date": attrs.get("VER_DATE"),
                "source_resolution": attrs.get("SRC_RESOLU"),
                "data_source": attrs.get("DATA_SOURC"),
                "geometry": feature.get("geometry"),
            })
        return features
