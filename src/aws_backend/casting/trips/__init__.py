"""Trips reasoning package for the console journey planner.

Phase-A producer surface. Today it exports the connections planner, which
assembles a connection feasibility plan (ferry / flight / seaplane) from the
W2 source clients, the corridor traffic model, and the flight/seaplane
adapters, attaching per-leg honesty labels, a composite label, and a freshness
stamp. The phase-B planner branch (``planner.py``) imports
:func:`plan_connection` and attaches its output to the ``connections_plan``
panel props.
"""

from __future__ import annotations

from .connections import ConnectionClients, plan_connection

__all__ = ["plan_connection", "ConnectionClients"]
