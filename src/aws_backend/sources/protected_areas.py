"""Protected-area spatial layers for U.S. and Canada."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

import requests

from ..geo_region import SAN_JUAN_BOUNDS

_NOAA_MPA_URL = (
    "https://services2.arcgis.com/C8EMgrsFhRFLWSkJ/arcgis/rest/services/"
    "NOAA_Marine_Protected_Areas_Inventory_2024/FeatureServer/0/query"
)


class ProtectedAreasAdapter:
    source_name = "protected_areas"
    reliability = 0.85

    def __init__(self, timeout: float = 20.0) -> None:
        self.timeout = timeout

    def fetch_us_mpa(self, result_record_count: int = 100) -> List[Dict[str, object]]:
        params = {
            "where": "1=1",
            "geometry": (
                f"{SAN_JUAN_BOUNDS.min_lng},{SAN_JUAN_BOUNDS.min_lat},"
                f"{SAN_JUAN_BOUNDS.max_lng},{SAN_JUAN_BOUNDS.max_lat}"
            ),
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "SiteName,Designation,ProtectionLevel",
            "returnGeometry": "true",
            "resultRecordCount": result_record_count,
            "f": "json",
        }
        try:
            response = requests.get(_NOAA_MPA_URL, params=params, timeout=self.timeout)
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
                    "id": f"mpa_us:{idx}",
                    "site_name": attrs.get("SiteName"),
                    "designation": attrs.get("Designation"),
                    "protection_level": attrs.get("ProtectionLevel"),
                    "geometry": feature.get("geometry"),
                    "source": "noaa_mpa_inventory",
                    "source_url": response.url,
                }
            )
        return records

    def fetch_ca_protected(self) -> List[Dict[str, object]]:
        now = datetime.now(timezone.utc).isoformat()
        return [
            {
                "t": now,
                "id": "cpcad:placeholder",
                "site_name": "Canada CPCAD placeholder",
                "source": "canada_cpcad",
                "source_url": "https://www.canada.ca/en/environment-climate-change/services/national-wildlife-areas/protected-conserved-areas-database.html",
                "note": "Use CPCAD export for clipped pilot-region polygons.",
            }
        ]
