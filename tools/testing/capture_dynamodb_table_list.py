#!/usr/bin/env python3
"""Print the seven DynamoDB tables judges expect in the console screenshot."""

from __future__ import annotations

TABLES = [
    "orcast-sightings",
    "orcast-community-submissions",
    "orcast-decision-records",
    "orcast-user-journal",
    "orcast-hotspots",
    "orcast-reports",
    "orcast-ingestion-runs",
]

if __name__ == "__main__":
    print("Capture AWS Console → DynamoDB → Tables (us-west-2) showing:\n")
    for name in TABLES:
        print(f"  - {name}")
    print("\nSave screenshot to docs/devpost/figures/dynamodb-console.png")
