#!/usr/bin/env python3
"""Record ORCAST API responses into demo/cache for offline replay."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = REPO_ROOT / "demo" / "cache"

ENDPOINTS: list[Tuple[str, str, Dict[str, Any] | None, str]] = [
    ("GET", "/health", None, "health.json"),
    ("GET", "/api/sightings", None, "sightings.json"),
    ("GET", "/api/verified-sightings", None, "verified-sightings.json"),
    ("GET", "/api/hotspots", None, "hotspots.json"),
    ("GET", "/api/live-hydrophones", None, "live-hydrophones.json"),
    ("GET", "/api/environmental", None, "environmental.json"),
    ("POST", "/forecast/quick", {"lat": 48.5158, "lng": -123.1526}, "forecast-quick.json"),
    (
        "POST",
        "/forecast/spatial",
        {"lat": 48.5158, "lng": -123.1526, "radius_km": 3, "grid_resolution": 0.05},
        "forecast-spatial.json",
    ),
    (
        "POST",
        "/api/reports/probability",
        {"region": "san_juan_islands", "min_confidence": 0, "report_format": "json"},
        "probability-report.json",
    ),
]


def slugify(path: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", path.strip("/")) or "root"


def main() -> int:
    parser = argparse.ArgumentParser(description="Record ORCAST demo API cache.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    reports_dir = CACHE_DIR / "reports"
    reports_dir.mkdir(exist_ok=True)

    manifest: Dict[str, Any] = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "source_url": base,
        "files": [],
    }

    report_id = None
    for method, path, payload, filename in ENDPOINTS:
        response = requests.request(method, f"{base}{path}", json=payload, timeout=60)
        response.raise_for_status()
        body = response.json()
        out = CACHE_DIR / filename
        out.write_text(json.dumps(body, indent=2), encoding="utf-8")
        manifest["files"].append({"method": method, "path": path, "file": filename})
        print(f"cached {method} {path} -> {filename}")

        if path == "/api/reports/probability":
            report_id = body["report"]["report_id"]

    if report_id:
        report_json = requests.get(f"{base}/api/reports/{report_id}", timeout=60)
        report_json.raise_for_status()
        json_name = f"{report_id}.json"
        (reports_dir / json_name).write_text(report_json.text, encoding="utf-8")
        manifest["files"].append({"method": "GET", "path": f"/api/reports/{report_id}", "file": f"reports/{json_name}"})

        report_csv = requests.get(f"{base}/api/reports/{report_id}.csv", timeout=60)
        report_csv.raise_for_status()
        csv_name = f"{report_id}.csv"
        (reports_dir / csv_name).write_text(report_csv.text, encoding="utf-8")
        manifest["files"].append({"method": "GET", "path": f"/api/reports/{report_id}.csv", "file": f"reports/{csv_name}"})
        manifest["sample_report_id"] = report_id

    (CACHE_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Demo cache written to {CACHE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
