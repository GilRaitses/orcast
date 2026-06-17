#!/usr/bin/env python3
"""Serve recorded demo/cache responses without AWS or live ingestion."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = REPO_ROOT / "demo" / "cache"

ROUTE_FILES = {
    "/health": "health.json",
    "/api/sightings": "sightings.json",
    "/api/verified-sightings": "verified-sightings.json",
    "/api/hotspots": "hotspots.json",
    "/api/live-hydrophones": "live-hydrophones.json",
    "/api/environmental": "environmental.json",
}

POST_FILES = {
    "/forecast/quick": "forecast-quick.json",
    "/forecast/spatial": "forecast-spatial.json",
    "/api/reports/probability": "probability-report.json",
}


class DemoHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_csv(self, text: str) -> None:
        data = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/csv")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ROUTE_FILES:
            payload = json.loads((CACHE_DIR / ROUTE_FILES[path]).read_text(encoding="utf-8"))
            self._send_json(payload)
            return

        if path.startswith("/api/reports/") and path.endswith(".csv"):
            report_id = path.split("/")[-1].replace(".csv", "")
            csv_path = CACHE_DIR / "reports" / f"{report_id}.csv"
            if csv_path.exists():
                self._send_csv(csv_path.read_text(encoding="utf-8"))
                return

        if path.startswith("/api/reports/"):
            report_id = path.rsplit("/", 1)[-1]
            json_path = CACHE_DIR / "reports" / f"{report_id}.json"
            if json_path.exists():
                self._send_json(json.loads(json_path.read_text(encoding="utf-8")))
                return

        self._send_json({"status": "error", "message": f"No cached response for {path}"}, status=404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        _ = self.rfile.read(int(self.headers.get("Content-Length", 0) or 0))
        filename = POST_FILES.get(path)
        if not filename:
            self._send_json({"status": "error", "message": f"No cached POST for {path}"}, status=404)
            return
        payload = json.loads((CACHE_DIR / filename).read_text(encoding="utf-8"))
        self._send_json(payload)

    def log_message(self, format: str, *args) -> None:
        print(f"[demo-cache] {self.address_string()} {format % args}")


def main() -> None:
    if not (CACHE_DIR / "manifest.json").exists():
        raise SystemExit(f"Missing demo cache at {CACHE_DIR}. Run: bash scripts/rebuild.sh --local-only")

    server = ThreadingHTTPServer(("127.0.0.1", 8080), DemoHandler)
    print(f"ORCAST demo cache server on http://127.0.0.1:8080 ({CACHE_DIR})")
    server.serve_forever()


if __name__ == "__main__":
    main()
