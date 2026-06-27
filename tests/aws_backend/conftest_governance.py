"""Shared headers for governance endpoint tests."""

from __future__ import annotations

import os
from typing import Dict


def governance_headers(**extra: str) -> Dict[str, str]:
    headers = {
        "X-ORCAST-Reviewer-Id": extra.pop("reviewer_id", "user_test"),
        "X-ORCAST-Reviewer-Email": extra.pop("reviewer_email", "reviewer@example.com"),
        "X-ORCAST-Reviewer-Role": extra.pop("reviewer_role", "reviewer"),
    }
    if os.environ.get("ORCAST_API_KEY"):
        headers["X-ORCAST-Trusted-Proxy"] = "vercel"
        headers["X-ORCAST-Key"] = os.environ["ORCAST_API_KEY"]
    headers.update(extra)
    return headers
