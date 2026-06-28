"""Operational corridor travel-time poller for lead-time history collection.

Polls the WSDOT TravelTimes feed for the SeaTac <-> Anacortes corridor routes on
an interval and appends each measured reading to the gitignored history log via
``wsdot_traffic.append_history``. This accrues the real travel-time history the
W3 corridor model fits on; the operator chose to start collecting now because
history needs lead time.

Honesty: measured-only. It logs exactly the routes the feed returns. The
Arlington -> Anacortes gap is never fabricated here (corridor_route_ids surfaces
only the southern I-5 routes that actually exist).

Run once for a smoke test:
    set -a && . ./.env && set +a && PYTHONPATH=. .venv/bin/python tools/corridor_poll.py --once

Run continuously (simple starter; use a durable scheduler such as cron/launchd
for real lead time):
    set -a && . ./.env && set +a && PYTHONPATH=. .venv/bin/python tools/corridor_poll.py
"""

from __future__ import annotations

import logging
import sys
import time

from src.aws_backend.sources import wsdot_traffic as wt

logging.basicConfig(level=logging.INFO, format="%(asctime)s corridor_poll %(message)s")
log = logging.getLogger("corridor_poll")

INTERVAL_S = 300


def poll_once() -> int:
    if not wt.is_configured():
        log.warning("WSDOT_ACCESS_CODE not set; skipping poll")
        return 0
    rows = wt.travel_times()
    corridor_ids = set(wt.corridor_route_ids())
    logged = 0
    for row in rows:
        if row.get("travel_time_id") in corridor_ids:
            wt.append_history(row)
            logged += 1
    log.info("logged %d corridor readings (of %d feed routes)", logged, len(rows))
    return logged


def main() -> None:
    run_once = "--once" in sys.argv
    while True:
        try:
            poll_once()
        except Exception as exc:  # operational loop must not die on a transient error
            log.exception("poll failed: %s", exc)
        if run_once:
            break
        time.sleep(INTERVAL_S)


if __name__ == "__main__":
    main()
