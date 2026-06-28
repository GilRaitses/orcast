#!/usr/bin/env python3
"""
Build web/public/demo-slides/dynamodb-proof.png showing all 9 DynamoDB tables.
Uses live item counts from DynamoDB and renders a dark-theme proof slide.

Usage: python3 tools/testing/build_ddb_proof_slide.py
"""
import pathlib, textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "web/public/demo-slides/dynamodb-proof.png"

# ── Colours (dark theme matching existing slide) ──────────────────────────
BG = (18, 24, 36)
PANEL = (24, 32, 48)
HEADER_BG = (30, 40, 58)
BORDER = (45, 60, 85)
TEXT = (230, 233, 240)
MUTED = (130, 145, 165)
GREEN = (52, 199, 89)
CYAN = (50, 200, 210)
BADGE_BG = (30, 90, 130)

# ── Table data (live counts from DynamoDB 2026-06-25) ─────────────────────
TABLES = [
    ("orcast-aws-backend-sightings",             "Normalized sightings + provenance",       "pk", 229,  "ACTIVE"),
    ("orcast-aws-backend-community-submissions",  "Citizen-science moderation queue",        "pk",  28,  "ACTIVE"),
    ("orcast-aws-backend-decision-records",       "Human promotion audit log",               "pk",   3,  "ACTIVE"),
    ("orcast-aws-backend-user-journal",           "Private field journal (WorkOS-scoped)",   "pk",  26,  "ACTIVE"),
    ("orcast-aws-backend-hotspots",               "Computed probability hotspots",           "pk", 113,  "ACTIVE"),
    ("orcast-aws-backend-reports",                "Probability reports",                     "pk", 302,  "ACTIVE"),
    ("orcast-aws-backend-ingestion-runs",         "Per-run ingestion audit",                 "pk", 554,  "ACTIVE"),
    ("orcast-aws-backend-partner-api-keys",       "API key registry",                        "pk",   1,  "ACTIVE"),
    ("orcast-aws-backend-managed-agents",         "Central Casting configs",                 "pk",   4,  "ACTIVE"),
]

W, H = 1440, 810

def load_font(size: int, bold: bool = False):
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()

def rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

# ── Fonts ─────────────────────────────────────────────────────────────────
f_title = load_font(28, bold=True)
f_badge = load_font(13)
f_head  = load_font(14)
f_table = load_font(13)
f_mono  = load_font(13)
f_sub   = load_font(15)
f_footer= load_font(11)

# ── Header ─────────────────────────────────────────────────────────────────
MARGIN = 56
Y = 48

draw.text((MARGIN, Y), "Amazon DynamoDB", font=f_title, fill=TEXT)
title_w = draw.textlength("Amazon DynamoDB", font=f_title)
draw.text((MARGIN + title_w + 8, Y + 2), "—  primary database", font=f_title, fill=MUTED)

# Account badge
badge_txt = "orcast · us-west-2 · account 198456344617"
bw = int(draw.textlength(badge_txt, font=f_badge)) + 20
bx = W - MARGIN - bw
by = Y + 2
rounded_rect(draw, (bx, by, bx+bw, by+22), 6, BADGE_BG)
draw.text((bx+10, by+4), badge_txt, font=f_badge, fill=CYAN)

Y += 46
draw.text((MARGIN, Y), "Nine on-demand tables, partition key pk, accessed via the AwsStorage backend. S3 is supporting storage only.", font=f_sub, fill=MUTED)

# ── Table ─────────────────────────────────────────────────────────────────
Y += 44
COL_TABLE   = MARGIN
COL_ROLE    = MARGIN + 390
COL_KEY     = MARGIN + 760
COL_ITEMS   = MARGIN + 820
COL_STATUS  = MARGIN + 900

# Header row
hdr_h = 32
rounded_rect(draw, (MARGIN - 8, Y, W - MARGIN + 8, Y + hdr_h), 6, HEADER_BG)
for txt, x in [("TABLE", COL_TABLE), ("ROLE", COL_ROLE), ("KEY", COL_KEY), ("ITEMS", COL_ITEMS), ("STATUS", COL_STATUS)]:
    draw.text((x, Y + 8), txt, font=f_head, fill=MUTED)

Y += hdr_h + 4

ROW_H = 46
for i, (tbl, role, key, items, status) in enumerate(TABLES):
    row_bg = PANEL if i % 2 == 0 else BG
    rounded_rect(draw, (MARGIN - 8, Y, W - MARGIN + 8, Y + ROW_H), 4, row_bg)

    short = tbl.replace("orcast-aws-backend-", "")
    draw.text((COL_TABLE, Y + 14), short, font=f_mono, fill=TEXT)
    draw.text((COL_ROLE,  Y + 14), role,  font=f_table, fill=MUTED)
    draw.text((COL_KEY,   Y + 14), key,   font=f_table, fill=MUTED)
    draw.text((COL_ITEMS, Y + 14), str(items), font=f_table, fill=TEXT)

    sw = int(draw.textlength(status, font=f_head)) + 16
    rounded_rect(draw, (COL_STATUS, Y+10, COL_STATUS+sw, Y+10+24), 5, (20, 60, 30))
    draw.text((COL_STATUS+8, Y+13), status, font=f_head, fill=GREEN)

    Y += ROW_H + 2

# ── Footer ─────────────────────────────────────────────────────────────────
Y += 10
footer = (
    "BillingMode PAY_PER_REQUEST. Item counts are DynamoDB-reported approximate ItemCount (refreshed ~6h). "
    "Reproduce: aws dynamodb list-tables --region us-west-2"
)
draw.text((MARGIN, Y), footer, font=f_footer, fill=MUTED)

# ── Save ──────────────────────────────────────────────────────────────────
OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(str(OUT), "PNG")
print(f"Saved: {OUT}  ({OUT.stat().st_size//1024} KB)")
