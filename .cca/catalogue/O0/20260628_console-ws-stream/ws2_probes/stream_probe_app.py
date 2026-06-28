"""WS2 throwaway transport probe — minimal FastAPI SSE endpoint.

PURPOSE
  Prove whether a byte stream survives the prod chain unbuffered, BEFORE any
  Bedrock streaming is built. This is a scratch artifact authored by the
  WS-STREAM sub-orchestrator. It is NOT wired into src/aws_backend and must NOT
  be merged. O0 deploys it behind cloudflared, measures, then discards it.

WHAT IT DOES
  GET/POST /__stream_probe emits one `event: meta` frame, then ~20 timestamped
  `event: token` frames at a fixed interval (default 150 ms), then one
  `event: done` frame. The SSE framing (meta|token|done) and the exact
  StreamingResponse headers mirror what T4 narration streaming will use, so a
  PASS here means the real endpoint should stream too.

KEY DETAIL (from WS1 R2)
  The generator is a SYNC `def` generator. Starlette runs it via
  iterate_in_threadpool(), so the per-frame time.sleep() does not block the event
  loop. This matches the real path where boto3 is sync. Do NOT convert to
  `async def` with a blocking sleep.

RUN (operator / O0 only; see BENCHMARK_PLAN.md):
  python -m venv .ws2venv && . .ws2venv/bin/activate
  pip install fastapi "uvicorn[standard]"
  uvicorn stream_probe_app:app --host 127.0.0.1 --port 8099
  # then expose 127.0.0.1:8099 via the cloudflared tunnel (see runbook)

TUNABLES via query params or env:
  count    number of token frames        (default 20,  env PROBE_COUNT)
  interval seconds between token frames   (default 0.15, env PROBE_INTERVAL)
"""

from __future__ import annotations

import json
import os
import time
from typing import Iterator

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

app = FastAPI(title="ws2-stream-probe", docs_url=None, redoc_url=None)

# Exact anti-buffering headers WS1 R2 named. These are re-asserted at the Next
# layer too; setting them at the origin is the first line of defense.
SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
    # Content-Type is set by StreamingResponse media_type below; do NOT also set
    # Content-Length (chunked transfer is what we want).
}


def _frame(event: str, data: dict) -> str:
    """One SSE frame: an `event:` line, a `data:` line, and a blank separator."""
    return f"event: {event}\ndata: {json.dumps(data, separators=(',', ':'))}\n\n"


def _probe_stream(count: int, interval: float) -> Iterator[str]:
    server_start = time.time()
    # meta first — in the real path this carries interaction_id + citations +
    # deep_links + provenance from the prefetched plan, before any token.
    yield _frame(
        "meta",
        {
            "probe": "ws2-stream-probe",
            "server_ts": server_start,
            "count": count,
            "interval_s": interval,
            "note": "framing mirrors T4 meta|token|done",
        },
    )
    for i in range(count):
        time.sleep(interval)
        yield _frame(
            "token",
            {
                "i": i,
                # server-side emit timestamp; the harness compares this to its own
                # client-side arrival timestamp to detect incremental vs all-at-once.
                "server_ts": time.time(),
                "text": f"tok{i:02d} ",
            },
        )
    yield _frame(
        "done",
        {"server_ts": time.time(), "elapsed_s": round(time.time() - server_start, 4)},
    )


def _resolve(request: Request) -> tuple[int, float]:
    qp = request.query_params
    count = int(qp.get("count") or os.getenv("PROBE_COUNT") or 20)
    interval = float(qp.get("interval") or os.getenv("PROBE_INTERVAL") or 0.15)
    return count, interval


@app.get("/__stream_probe")
@app.post("/__stream_probe")
async def stream_probe(request: Request) -> StreamingResponse:
    count, interval = _resolve(request)
    return StreamingResponse(
        _probe_stream(count, interval),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@app.get("/__stream_probe/health")
async def health() -> dict:
    return {"status": "ok", "probe": "ws2-stream-probe"}
