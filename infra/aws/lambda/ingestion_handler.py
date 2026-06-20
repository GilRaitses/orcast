import json
import os
import urllib.error
import urllib.request


def _body_for_path(path):
    # Sighting ingest needs the live flag; time-series refresh takes no body.
    if "refresh" in path:
        return b""
    return json.dumps({"include_live": True}).encode()


def _post(url, data, headers):
    req = urllib.request.Request(url, data=data, method="POST", headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.status, resp.read().decode()


def handler(event, context):
    base = os.environ["BACKEND_URL"].rstrip("/")
    raw_paths = os.environ.get("API_PATH", "/api/sightings/ingest")
    paths = [p.strip() for p in raw_paths.split(",") if p.strip()]

    headers = {"Content-Type": "application/json"}
    api_key = os.environ.get("ORCAST_API_KEY", "")
    if api_key:
        headers["X-ORCAST-Key"] = api_key

    results = []
    for path in paths:
        url = f"{base}{path}"
        data = _body_for_path(path)
        try:
            status, body = _post(url, data, headers)
            results.append({"path": path, "statusCode": status, "body": body})
        except urllib.error.HTTPError as exc:
            results.append({"path": path, "statusCode": exc.code, "body": exc.read().decode()})
        except Exception as exc:  # tolerate per-path failures and continue
            results.append({"path": path, "statusCode": None, "error": str(exc)})

    overall = 200 if all(r.get("statusCode") == 200 for r in results) else 207
    return {"statusCode": overall, "body": json.dumps({"results": results})}
