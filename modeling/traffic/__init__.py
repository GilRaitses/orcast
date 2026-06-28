"""Corridor traffic modeling for the Trips planner (offline, sparse-data-robust).

The WSDOT Traveler API serves realtime travel times only; it has NO historical
endpoint. So future-departure corridor ETAs are MODELED from a self-collected
history log (``data/external/traffic_corridor/seatac_anacortes.jsonl``, accrued by
``tools/corridor_poll.py`` via ``wsdot_traffic.append_history``).

``corridor.predict_eta`` fits a transparent day-of-week x time-of-bin median model
over that log per measured route and predicts a future-departure ETA with a
prediction interval, falling back to the latest measured travel time when a bin is
empty. Every prediction is labeled MODELED and carries its basis (sample count /
fallback) so the connections planner never overstates it as measured.
"""

from modeling.traffic.corridor import predict_eta

__all__ = ["predict_eta"]
