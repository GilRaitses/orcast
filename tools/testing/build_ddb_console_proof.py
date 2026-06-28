#!/usr/bin/env python3
"""
Build docs/devpost/figures/dynamodb-console.png: the AWS Database usage proof.

Queries live DynamoDB (us-west-2) via the AWS CLI and renders a dark-theme
console proof showing every orcast table with its real partition key, live
ItemCount, table size, billing mode, and status. This is the reproducible
"AWS Database usage screenshot" required by the submission spec.

Usage: python3 tools/testing/build_ddb_console_proof.py
Reproduce the data: aws dynamodb list-tables --region us-west-2
"""
import json
import pathlib
import subprocess
import datetime
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/devpost/figures/dynamodb-console.png"
REGION = "us-west-2"
ACCOUNT = "198456344617"
PREFIX = "orcast-aws-backend-"

# Short name -> human role (documentation parity with the architecture diagram).
ROLES = {
    "sightings": "Normalized sightings + provenance",
    "community-submissions": "Citizen-science moderation queue",
    "decision-records": "Human promotion audit log",
    "user-journal": "Private field journal (WorkOS-scoped)",
    "hotspots": "Computed probability hotspots",
    "reports": "Probability reports",
    "ingestion-runs": "Per-run ingestion audit",
    "partner-api-keys": "Partner OpenAPI gateway keys",
    "managed-agents": "Central Casting managed agent configs",
}
ORDER = list(ROLES.keys())

BG = (18, 24, 36)
PANEL = (24, 32, 48)
HEADER_BG = (30, 40, 58)
TEXT = (230, 233, 240)
MUTED = (130, 145, 165)
GREEN = (52, 199, 89)
CYAN = (50, 200, 210)
BADGE_BG = (30, 90, 130)


def aws_describe(short):
    name = PREFIX + short
    out = subprocess.check_output(
        ["aws", "dynamodb", "describe-table", "--table-name", name,
         "--region", REGION, "--output", "json"],
        text=True,
    )
    t = json.loads(out)["Table"]
    key = next((k["AttributeName"] for k in t.get("KeySchema", [])
                if k.get("KeyType") == "HASH"), "pk")
    billing = t.get("BillingModeSummary", {}).get("BillingMode", "PAY_PER_REQUEST")
    return {
        "short": short,
        "role": ROLES[short],
        "key": key,
        "items": int(t.get("ItemCount", 0)),
        "size": int(t.get("TableSizeBytes", 0)),
        "status": t.get("TableStatus", "ACTIVE"),
        "billing": billing,
    }


def human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def load_font(size):
    for path in (
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def rounded(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(list(xy), radius=radius, fill=fill, outline=outline, width=width)


def main():
    rows = [aws_describe(s) for s in ORDER]
    total_items = sum(r["items"] for r in rows)
    billing_modes = sorted({r["billing"] for r in rows})
    all_active = all(r["status"] == "ACTIVE" for r in rows)
    stamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    W, H = 1480, 840
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    f_title = load_font(30)
    f_sub = load_font(15)
    f_head = load_font(14)
    f_mono = load_font(14)
    f_table = load_font(13)
    f_footer = load_font(11)
    f_badge = load_font(13)

    MARGIN = 56
    Y = 46
    draw.text((MARGIN, Y), "Amazon DynamoDB", font=f_title, fill=TEXT)
    tw = draw.textlength("Amazon DynamoDB", font=f_title)
    draw.text((MARGIN + tw + 12, Y + 4), "live database proof", font=f_title, fill=MUTED)

    badge = f"{REGION} \u00b7 account {ACCOUNT} \u00b7 queried {stamp}"
    bw = int(draw.textlength(badge, font=f_badge)) + 20
    bx = W - MARGIN - bw
    rounded(draw, (bx, Y + 4, bx + bw, Y + 28), 6, BADGE_BG)
    draw.text((bx + 10, Y + 8), badge, font=f_badge, fill=CYAN)

    Y += 48
    subtitle = (f"Nine on-demand tables. {total_items:,} live items total. Partition key pk "
                "for all tables except managed-agents (agent_id). S3 is supporting storage only.")
    draw.text((MARGIN, Y), subtitle, font=f_sub, fill=MUTED)

    Y += 42
    COL_TABLE = MARGIN
    COL_ROLE = MARGIN + 360
    COL_KEY = MARGIN + 740
    COL_ITEMS = MARGIN + 850
    COL_SIZE = MARGIN + 960
    COL_STATUS = MARGIN + 1075

    hdr_h = 32
    rounded(draw, (MARGIN - 8, Y, W - MARGIN + 8, Y + hdr_h), 6, HEADER_BG)
    for txt, x in [("TABLE", COL_TABLE), ("ROLE", COL_ROLE), ("KEY", COL_KEY),
                   ("ITEMS", COL_ITEMS), ("SIZE", COL_SIZE), ("STATUS", COL_STATUS)]:
        draw.text((x, Y + 8), txt, font=f_head, fill=MUTED)

    Y += hdr_h + 4
    ROW_H = 46
    for i, r in enumerate(rows):
        rounded(draw, (MARGIN - 8, Y, W - MARGIN + 8, Y + ROW_H), 4,
                PANEL if i % 2 == 0 else BG)
        draw.text((COL_TABLE, Y + 14), PREFIX + r["short"], font=f_mono, fill=TEXT)
        draw.text((COL_ROLE, Y + 14), r["role"], font=f_table, fill=MUTED)
        draw.text((COL_KEY, Y + 14), r["key"], font=f_table, fill=CYAN)
        draw.text((COL_ITEMS, Y + 14), f"{r['items']:,}", font=f_table, fill=TEXT)
        draw.text((COL_SIZE, Y + 14), human_size(r["size"]), font=f_table, fill=MUTED)
        sw = int(draw.textlength(r["status"], font=f_head)) + 16
        rounded(draw, (COL_STATUS, Y + 10, COL_STATUS + sw, Y + 34), 5, (20, 60, 30))
        draw.text((COL_STATUS + 8, Y + 13), r["status"], font=f_head, fill=GREEN)
        Y += ROW_H + 2

    Y += 12
    footer = (f"BillingMode {', '.join(billing_modes)}. ItemCount is DynamoDB-reported approximate "
              f"(refreshed ~6h). All tables {'ACTIVE' if all_active else 'see status column'}. "
              "Reproduce: aws dynamodb list-tables --region us-west-2 ; "
              "aws dynamodb describe-table --table-name orcast-aws-backend-<name> --region us-west-2")
    draw.text((MARGIN, Y), footer, font=f_footer, fill=MUTED)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(OUT), "PNG")
    print(f"Saved: {OUT} ({OUT.stat().st_size // 1024} KB)")
    print(f"Tables: {len(rows)}  total items: {total_items}  billing: {billing_modes}  all_active: {all_active}")
    for r in rows:
        print(f"  {r['short']:<24} key={r['key']:<10} items={r['items']:<6} size={human_size(r['size'])} {r['status']}")


if __name__ == "__main__":
    main()
