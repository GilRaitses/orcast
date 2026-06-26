"""Ferry route effort proxies for Washington and British Columbia."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

import requests

# WSDOT Ferries routes GeoJSON (public open data).
_WSDOT_ROUTES_URL = "https://www.wsdot.wa.gov/ferries/vesselwatch/VesselWatchWebService.asmx/GetAllRoutes"


class FerryEffortAdapter:
    source_name = "ferry_effort"
    reliability = 0.7

    def __init__(self, timeout: float = 20.0) -> None:
        self.timeout = timeout

    def fetch_wa_routes(self) -> List[Dict[str, object]]:
        try:
            response = requests.get(_WSDOT_ROUTES_URL, timeout=self.timeout)
        except requests.RequestException:
            return []
        if response.status_code != 200:
            return []
        now = datetime.now(timezone.utc).isoformat()
        payload = response.text
        records: List[Dict[str, object]] = []
        # Service returns XML; store a bounded metadata record until route geometry is parsed.
        records.append(
            {
                "t": now,
                "id": "wsdot:routes_snapshot",
                "region": "washington",
                "route_count_estimate": payload.lower().count("<route"),
                "source": "wsdot_ferries",
                "source_url": _WSDOT_ROUTES_URL,
                "format": "xml",
            }
        )
        return records

    def fetch_bc_routes(self) -> List[Dict[str, object]]:
        now = datetime.now(timezone.utc).isoformat()
        return [
            {
                "t": now,
                "id": "bc:routes_placeholder",
                "region": "british_columbia",
                "source": "bc_ferries",
                "source_url": "https://www.bcferries.com/",
                "note": "BC route geometry requires manual export; metadata placeholder only.",
            }
        ]
