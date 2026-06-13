#!/usr/bin/env python3
"""
ORCAST AWS backend smoke test.

Runs the end-to-end API checks required by the AWS migration plan against a
running backend. Defaults to http://localhost:8080 so it can validate the local
in-memory backend, but accepts any deployed App Runner URL.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, Dict, Tuple

import requests


def request_json(method: str, base_url: str, path: str, payload: Dict[str, Any] | None = None) -> Tuple[int, Dict[str, Any]]:
    response = requests.request(method, f"{base_url.rstrip('/')}{path}", json=payload, timeout=30)
    response.raise_for_status()
    return response.status_code, response.json()


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test an ORCAST AWS backend deployment.")
    parser.add_argument("--base-url", default="http://localhost:8080", help="Backend base URL")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    checks = [
        ("GET", "/health", None),
        ("GET", "/api/sightings", None),
        ("GET", "/api/hotspots", None),
        ("GET", "/api/live-hydrophones", None),
        ("GET", "/api/environmental", None),
        ("POST", "/forecast/quick", {"lat": 48.5158, "lng": -123.1526}),
        ("POST", "/forecast/spatial", {"lat": 48.5158, "lng": -123.1526, "radius_km": 3, "grid_resolution": 0.05}),
        ("POST", "/api/reports/probability", {"min_confidence": 0}),
    ]

    report_id = None
    for method, path, payload in checks:
        status_code, body = request_json(method, base_url, path, payload)
        print(f"{method} {path}: {status_code}")

        if path == "/health":
            assert body["status"] == "healthy"
            assert body["sightings_loaded"] > 0
            print(f"  sightings_loaded={body['sightings_loaded']}")
        elif path == "/api/sightings":
            assert body["total_count"] > 0
            print(f"  sightings={body['total_count']}")
        elif path == "/api/hotspots":
            assert body["total_count"] > 0
            assert 0 <= body["hotspots"][0]["probability"] <= 1
            print(f"  hotspots={body['total_count']}")
        elif path == "/api/live-hydrophones":
            assert body["total_count"] > 0
            print(f"  hydrophones={body['total_count']}")
        elif path == "/api/environmental":
            assert "environmental_data" in body
            print(f"  environmental_quality={body['environmental_data'].get('quality')}")
        elif path == "/forecast/quick":
            assert 0 <= body["prediction"]["probability"] <= 1
            print(f"  probability={body['prediction']['probability']}")
        elif path == "/forecast/spatial":
            assert body["total_points"] > 0
            print(f"  points={body['total_points']}")
        elif path == "/api/reports/probability":
            report_id = body["report"]["report_id"]
            assert report_id.startswith("report_")
            assert body["report"]["hotspots"]
            print(f"  report_id={report_id}")

    if not report_id:
        raise AssertionError("Report generation did not return a report ID")

    status_code, report_body = request_json("GET", base_url, f"/api/reports/{report_id}")
    assert report_body["report"]["report_id"] == report_id
    print(f"GET /api/reports/{report_id}: {status_code}")

    csv_response = requests.get(f"{base_url}/api/reports/{report_id}.csv", timeout=30)
    csv_response.raise_for_status()
    assert "hotspot_id,name,center_latitude" in csv_response.text
    print(f"GET /api/reports/{report_id}.csv: {csv_response.status_code}")

    print("ORCAST AWS backend smoke test passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Smoke test failed: {exc}", file=sys.stderr)
        raise

