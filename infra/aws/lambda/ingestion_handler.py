import json
import os
import urllib.error
import urllib.request


def handler(event, context):
    base = os.environ["BACKEND_URL"].rstrip("/")
    path = os.environ.get("API_PATH", "/api/sightings/ingest")
    url = f"{base}{path}"
    req = urllib.request.Request(
        url,
        data=json.dumps({"include_live": True}).encode(),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode()
            return {"statusCode": resp.status, "body": body}
    except urllib.error.HTTPError as exc:
        return {"statusCode": exc.code, "body": exc.read().decode()}
