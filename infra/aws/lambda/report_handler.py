import json
import os
import urllib.error
import urllib.request


def _post(base: str, path: str, payload: dict | None = None) -> tuple[int, str]:
    url = f"{base.rstrip('/')}{path}"
    data = json.dumps(payload or {}).encode()
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.status, resp.read().decode()


def handler(event, context):
    base = os.environ["BACKEND_URL"]
    try:
        recompute_status, recompute_body = _post(base, "/api/hotspots/recompute")
        report_status, report_body = _post(
            base,
            "/api/reports/probability",
            {"region": "san_juan_islands", "min_confidence": 0, "report_format": "json"},
        )
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "recompute": {"status": recompute_status, "body": recompute_body},
                    "report": {"status": report_status, "body": report_body},
                }
            ),
        }
    except urllib.error.HTTPError as exc:
        return {"statusCode": exc.code, "body": exc.read().decode()}
