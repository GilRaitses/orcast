#!/usr/bin/env python3
"""WS7 end-to-end streaming acceptance probe against the App Runner lane.

Drives the real flow (create session -> plan -> narrate/stream) and measures
first-token latency + incremental delivery of the SSE narration stream.
Bypasses the cloudflared/api-be path (which currently 503s on the DB) by
talking straight to the App Runner native URL.
"""
import json
import os
import sys
import time
import urllib.request

BASE = os.environ.get("WS7_BASE", "https://pjrftm3bkv.us-west-2.awsapprunner.com")
KEY = os.environ["WS7_KEY"]

PLANNER_SPEC = {
    "instructions": "You are the ORCAST public explore planner. Allocate read-only panels and public skills for anonymous users. Prefer gates + provenance + trace panels.",
    "skills": [
        "fetch_gates", "fetch_hotspots", "fetch_provenance",
        "fetch_environmental", "fetch_live_hydrophones", "fetch_verified_sightings",
    ],
    "version": "public-2",
    "policy": {
        "write_tools": False,
        "planner_mode": True,
        "allowed_deep_links": ["/gates", "/explore", "/glossary", "/"],
        "allowed_panels": [
            "map_viewport", "explore_trace", "gates_summary", "provenance_pin",
            "provenance_graph", "hydrophone_signal",
        ],
    },
}
MESSAGE = "What gates are currently passing and why?"


def post(path, payload):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "X-ORCAST-Key": KEY},
        method="POST",
    )
    return urllib.request.urlopen(req, timeout=60)


def main():
    # 1) session
    t = time.time()
    sess = json.loads(post("/api/explore/sessions", {"title": "ws7 probe"}).read())
    sid = sess["session_id"]
    print(f"[session] {sid}  ({time.time()-t:.2f}s)")

    # 2) plan (panels-first, no narration)
    t = time.time()
    plan = json.loads(post("/api/interactions/plan", {
        "session_id": sid, "message": MESSAGE, "agent": PLANNER_SPEC, "narrate": False,
    }).read())
    prep = plan.get("prepare", {})
    print(f"[plan] ok  panels={len(plan.get('ui_intent',{}).get('panel_plan',[]) or [])}  "
          f"citations={len(prep.get('citations',[]) or [])}  ({time.time()-t:.2f}s)")

    # 3) narrate/stream — measure first token + incremental gaps
    body = {
        "session_id": sid, "message": MESSAGE, "agent": PLANNER_SPEC,
        "skill_plan": plan.get("ui_intent", {}).get("skill_plan", []) or [],
        "context": prep.get("context", {}) or {},
        "citations": prep.get("citations", []) or [],
        "deep_links": prep.get("deep_links", []) or [],
        "tools_used": prep.get("tools_used", []) or [],
        "gate_ids": prep.get("gate_ids", []) or [],
        "provenance_refs": prep.get("provenance_refs", []) or [],
    }
    # Optionally stream via the public Vercel route (full prod chain,
    # browser -> Vercel -> App Runner). The route injects the key server-side,
    # so no X-ORCAST-Key is sent here.
    stream_url = os.environ.get("WS7_STREAM_URL")
    t0 = time.time()
    if stream_url:
        req = urllib.request.Request(
            stream_url, data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=60)
        print(f"[stream-via] {stream_url}")
    else:
        resp = post("/api/interactions/narrate/stream", body)
    print(f"[stream] HTTP {resp.status}  content-type={resp.headers.get('Content-Type')}")
    first_token_at = None
    token_times = []
    events = {"meta": 0, "token": 0, "done": 0, "error": 0}
    assembled = []
    cur_event = None
    for raw in resp:
        line = raw.decode("utf-8", "replace").rstrip("\n")
        if line.startswith("event:"):
            cur_event = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            data = line.split(":", 1)[1].strip()
            if cur_event in events:
                events[cur_event] += 1
            if cur_event == "token":
                now = time.time()
                if first_token_at is None:
                    first_token_at = now - t0
                token_times.append(now - t0)
                try:
                    assembled.append(json.loads(data).get("text", ""))
                except Exception:
                    pass
            elif cur_event == "meta":
                try:
                    m = json.loads(data)
                    print(f"[meta] source={m.get('source')} model={m.get('model')} "
                          f"citations={len(m.get('citations',[]) or [])} "
                          f"deep_links={len(m.get('deep_links',[]) or [])}")
                except Exception:
                    pass
            elif cur_event == "error":
                print(f"[error] {data}")
    total = time.time() - t0
    reply = "".join(assembled)
    print("--- RESULT ---")
    print(f"first_token_latency = {first_token_at:.2f}s" if first_token_at else "first_token_latency = NONE")
    print(f"token_events={events['token']}  meta={events['meta']}  done={events['done']}  error={events['error']}")
    print(f"incremental = {events['token'] > 1 and (token_times[-1]-token_times[0] > 0.1 if len(token_times)>1 else False)}")
    print(f"total_stream_time = {total:.2f}s   reply_chars = {len(reply)}")
    print(f"reply_preview = {reply[:180]!r}")


if __name__ == "__main__":
    main()
