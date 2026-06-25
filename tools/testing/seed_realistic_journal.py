#!/usr/bin/env python3
"""
Seed realistic journal entries and clear smoke test + malformed entries.

Usage: python3 tools/testing/seed_realistic_journal.py
"""
import boto3, uuid, datetime, sys
from decimal import Decimal

TABLE = "orcast-aws-backend-user-journal"
AGENT_USER = "agent_orcast_automation"

ddb = boto3.resource("dynamodb", region_name="us-west-2")
table = ddb.Table(TABLE)

# ── 1. Remove all entries for agent user (smoke test + any malformed) ─────
print("Scanning for agent user entries...")
resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key("pk").eq(AGENT_USER)
)
items = resp.get("Items", [])
deleted = 0
for item in items:
    table.delete_item(Key={"pk": item["pk"], "sk": item["sk"]})
    deleted += 1
print(f"  Deleted {deleted} existing entries for {AGENT_USER}")

# ── 2. Seed properly structured realistic entries ─────────────────────────
now = datetime.datetime.now(datetime.timezone.utc)

def make_entry(kind, title, place, lat, lng, body, behavior, count, hours_ago):
    ts = (now - datetime.timedelta(hours=hours_ago)).isoformat()
    entry_id = uuid.uuid4().hex
    return {
        "pk": AGENT_USER,
        "sk": f"entry#{entry_id}",
        "id": entry_id,
        "user_id": AGENT_USER,
        "user_email": "agent@orcast.dev",
        "kind": kind,
        "title": title,
        "place": place,
        "latitude": Decimal(str(lat)),
        "longitude": Decimal(str(lng)),
        "body": body,
        "behavior": behavior,
        "count": count,
        "observed_at": ts,
        "created_at": ts,
        "updated_at": ts,
        "published": False,
    }

entries = [
    make_entry(
        kind="observation",
        title="J pod transiting Lime Kiln",
        place="Lime Kiln Point",
        lat=48.516, lng=-123.152,
        body="3 animals transiting northbound off Lime Kiln Point — possible J pod. Very close to shore, within 50m. Distinct saddle patches visible on the large male.",
        behavior="traveling", count=3, hours_ago=2,
    ),
    make_entry(
        kind="observation",
        title="Foraging group near kelp beds",
        place="Haro Strait",
        lat=48.519, lng=-123.157,
        body="Heard clear echolocation pings on the Lime Kiln hydrophone at 11:30 UTC. Visual confirms 6+ animals in kelp bed formation. Surface active, fluking repeatedly. Stayed in area for ~40 minutes.",
        behavior="foraging", count=6, hours_ago=1,
    ),
    make_entry(
        kind="note",
        title="Unconfirmed dorsal fin — Active Pass crossing",
        place="Active Pass",
        lat=48.882, lng=-123.288,
        body="Black dorsal fin visible from ferry deck, brief surface. Fin shape consistent with orca but triangular (~1.2m). Could not confirm species — common misID: harbor porpoise or juvenile orca. Logging for review by reviewer.",
        behavior="unknown", count=1, hours_ago=0.75,
    ),
]

for entry in entries:
    table.put_item(Item=entry)
    print(f"  Seeded: {entry['kind']} — {entry['title']}")

print(f"Done. {len(entries)} realistic entries added.")
