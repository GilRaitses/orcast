#!/usr/bin/env python3
"""WS-COLDSTART CS4 gap poller (R4 harness).

Measures the user-visible cold-start gap during an App Runner instance transition.

Gap metric (R4): gap_while_health_up_ms = the max contiguous duration where a real
user call (GET /api/explore/status, which exercises the DB readiness path) returns
non-2xx while GET /health returns 2xx. Target = 0. /api/explore/status returns 200
even when the DB is unreachable (body aurora_connected=false), so a non-2xx there
during a transition is an App Runner edge-handover artifact, exactly what we want
to catch. A sparse POST /api/explore/sessions is logged too, but throttled to
respect the backend 20/IP/day session quota.

Read-only against the public service URL; no infra mutation here. Usage:
  python3 tools/testing/coldstart_gap_probe.py --base https://<host> --seconds 600
  python3 tools/testing/coldstart_gap_probe.py --base https://<vercel>/api/be --seconds 600  # via Vercel (tests M4)
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone


def _get(url: str, timeout: float = 4.0) -> tuple[int, float]:
    start = time.monotonic()
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, (time.monotonic() - start) * 1000.0
    except urllib.error.HTTPError as exc:
        return exc.code, (time.monotonic() - start) * 1000.0
    except Exception:
        return 0, (time.monotonic() - start) * 1000.0


def _post_session(url: str, timeout: float = 6.0) -> int:
    body = json.dumps({"title": "coldstart gap probe"}).encode("utf-8")
    try:
        req = urllib.request.Request(
            url, data=body, method="POST", headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:
        return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="base URL, e.g. https://host (no trailing slash)")
    ap.add_argument("--seconds", type=int, default=600)
    ap.add_argument("--cadence-ms", type=int, default=500)
    ap.add_argument("--session-every-s", type=int, default=20, help="sparse session-create cadence (quota-aware)")
    ap.add_argument("--out", default=None, help="optional path to write the JSON summary")
    args = ap.parse_args()

    base = args.base.rstrip("/")
    health_url = f"{base}/health"
    status_url = f"{base}/api/explore/status"
    session_url = f"{base}/api/explore/sessions"

    deadline = time.monotonic() + args.seconds
    cadence = args.cadence_ms / 1000.0

    samples = 0
    health_up = 0
    status_2xx = 0
    gap_events: list[dict] = []  # contiguous windows: health up while status non-2xx
    cur_gap_start: float | None = None
    cur_gap_first_status: int | None = None
    max_gap_ms = 0.0
    session_attempts = 0
    session_2xx = 0
    session_nonidempotent_log: list[dict] = []
    last_session = 0.0

    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    print(f"[{now_iso()}] gap probe start base={base} seconds={args.seconds}", flush=True)

    while time.monotonic() < deadline:
        tick = time.monotonic()
        hs, _ = _get(health_url)
        ss, _ = _get(status_url)
        samples += 1
        h_ok = 200 <= hs < 300
        s_ok = 200 <= ss < 300
        if h_ok:
            health_up += 1
        if s_ok:
            status_2xx += 1

        # Gap = real user call (status) non-2xx while health is up.
        if h_ok and not s_ok:
            if cur_gap_start is None:
                cur_gap_start = tick
                cur_gap_first_status = ss
                print(f"[{now_iso()}] GAP open: status={ss} health={hs}", flush=True)
        else:
            if cur_gap_start is not None:
                dur = (tick - cur_gap_start) * 1000.0
                max_gap_ms = max(max_gap_ms, dur)
                gap_events.append(
                    {"start": cur_gap_start, "duration_ms": round(dur, 1), "first_status": cur_gap_first_status}
                )
                print(f"[{now_iso()}] GAP close: duration_ms={round(dur,1)}", flush=True)
                cur_gap_start = None
                cur_gap_first_status = None

        if tick - last_session >= args.session_every_s:
            last_session = tick
            code = _post_session(session_url)
            session_attempts += 1
            if 200 <= code < 300:
                session_2xx += 1
            else:
                session_nonidempotent_log.append({"t": now_iso(), "status": code})
            print(f"[{now_iso()}] session-create -> {code} (health={hs} status={ss})", flush=True)

        elapsed = time.monotonic() - tick
        if elapsed < cadence:
            time.sleep(cadence - elapsed)

    if cur_gap_start is not None:
        dur = (time.monotonic() - cur_gap_start) * 1000.0
        max_gap_ms = max(max_gap_ms, dur)
        gap_events.append({"start": cur_gap_start, "duration_ms": round(dur, 1), "first_status": cur_gap_first_status})

    summary = {
        "base": base,
        "samples": samples,
        "health_up_pct": round(100.0 * health_up / max(samples, 1), 2),
        "status_2xx_pct": round(100.0 * status_2xx / max(samples, 1), 2),
        "max_gap_while_health_up_ms": round(max_gap_ms, 1),
        "gap_event_count": len(gap_events),
        "gap_events": gap_events,
        "session_attempts": session_attempts,
        "session_2xx": session_2xx,
        "session_non2xx": session_nonidempotent_log,
        "finished": now_iso(),
    }
    print("=== SUMMARY ===", flush=True)
    print(json.dumps(summary, indent=2), flush=True)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
