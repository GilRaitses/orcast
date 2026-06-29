#!/usr/bin/env python3
"""Resolve arXiv IDs from whitepaper research files to published journal DOIs.

For each arXiv ID found in the research Markdown files:
1. Query Semantic Scholar (fast, returns DOI + venue) first.
2. Fall back to CrossRef if S2 has no DOI.
3. Emit @article when journaltitle + DOI found; @online otherwise.
4. Key format: arxivNNNNNNNNN (dots removed from numeric ID).

Matches the neuro whitepaper bib convention exactly.

Usage:
    python3 tools/testing/reference_audit.py
    python3 tools/testing/reference_audit.py \\
        --research-dir docs/whitepaper/research/ \\
        --bib-out     docs/whitepaper/LX/references.bib \\
        --audit-out   docs/whitepaper/LX/reference_audit.txt
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESEARCH = REPO_ROOT / "docs/whitepaper/research"
DEFAULT_BIB = REPO_ROOT / "docs/whitepaper/LX/references.bib"
DEFAULT_AUDIT = REPO_ROOT / "docs/whitepaper/LX/reference_audit.txt"

ARXIV_PAT = re.compile(
    r"(?:arxiv\.org/abs/|arXiv:)(\d{4}\.\d{4,5}|\d{7})",
    re.IGNORECASE,
)
S2_BASE = "https://api.semanticscholar.org/graph/v1/paper/arXiv:{id}"
S2_FIELDS = "title,authors,year,venue,externalIds,publicationVenue"
CR_BASE = "https://api.crossref.org/works"
SLEEP = 0.4  # polite rate limit


def extract_ids(research_dir: Path) -> list[str]:
    seen: set[str] = set()
    ids: list[str] = []
    for f in sorted(research_dir.glob("*.md")):
        for m in ARXIV_PAT.finditer(f.read_text()):
            aid = m.group(1)
            if aid not in seen:
                seen.add(aid)
                ids.append(aid)
    return ids


def bib_key(arxiv_id: str) -> str:
    return "arxiv" + arxiv_id.replace(".", "")


def query_s2(arxiv_id: str) -> dict | None:
    try:
        r = requests.get(
            S2_BASE.format(id=arxiv_id),
            params={"fields": S2_FIELDS},
            timeout=15,
        )
        if r.status_code == 200:
            return r.json()
    except requests.RequestException:
        pass
    return None


def query_crossref(title: str, author: str) -> dict | None:
    try:
        r = requests.get(
            CR_BASE,
            params={
                "query.title": title,
                "query.author": author,
                "rows": 1,
                "select": "DOI,title,author,container-title,published,type",
            },
            timeout=15,
        )
        if r.status_code == 200:
            items = r.json().get("message", {}).get("items", [])
            return items[0] if items else None
    except requests.RequestException:
        pass
    return None


def make_entry(arxiv_id: str, s2: dict | None, cr: dict | None) -> str:
    key = bib_key(arxiv_id)

    # Author list
    authors = []
    if s2 and s2.get("authors"):
        authors = [a.get("name", "") for a in s2["authors"][:6]]
    elif cr and cr.get("author"):
        for a in cr["author"][:6]:
            name = " ".join(filter(None, [a.get("given", ""), a.get("family", "")]))
            authors.append(name)
    author_str = " and ".join(authors) if authors else "Unknown"

    title = ""
    if s2:
        title = s2.get("title") or ""
    elif cr:
        t = cr.get("title") or []
        title = t[0] if t else ""

    year = ""
    if s2:
        year = str(s2.get("year") or "")
    elif cr:
        pub = cr.get("published", {}).get("date-parts", [[]])
        year = str(pub[0][0]) if pub and pub[0] else ""

    doi = ""
    if s2:
        doi = (s2.get("externalIds") or {}).get("DOI", "")
    if not doi and cr:
        doi = cr.get("DOI", "")

    journal = ""
    if s2:
        pv = s2.get("publicationVenue") or {}
        journal = pv.get("name") or s2.get("venue") or ""
    if not journal and cr:
        ct = cr.get("container-title") or []
        journal = ct[0] if ct else ""

    eprint_line = f"  eprint = {{{arxiv_id}}},\n  eprinttype = {{arxiv}},"

    if doi and journal:
        return (
            f"@article{{{key},\n"
            f"  author = {{{author_str}}},\n"
            f"  title = {{{title}}},\n"
            f"  year = {{{year}}},\n"
            f"  journaltitle = {{{journal}}},\n"
            f"  doi = {{{doi}}},\n"
            f"  {eprint_line}\n"
            f"}}"
        )
    else:
        return (
            f"@online{{{key},\n"
            f"  author = {{{author_str}}},\n"
            f"  title = {{{title}}},\n"
            f"  year = {{{year}}},\n"
            f"  {eprint_line}\n"
            f"  url = {{https://arxiv.org/abs/{arxiv_id}}}\n"
            f"}}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--research-dir", default=str(DEFAULT_RESEARCH))
    parser.add_argument("--bib-out", default=str(DEFAULT_BIB))
    parser.add_argument("--audit-out", default=str(DEFAULT_AUDIT))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    research_dir = Path(args.research_dir)
    bib_out = Path(args.bib_out)
    audit_out = Path(args.audit_out)

    ids = extract_ids(research_dir)
    print(f"Detected IDs: {len(ids)}")
    if not ids:
        print("No arXiv IDs found — check --research-dir path.", file=sys.stderr)
        return 1

    entries: list[str] = []
    resolved = 0

    for i, aid in enumerate(ids):
        print(f"  [{i+1}/{len(ids)}] {aid}", end=" ", flush=True)
        if args.dry_run:
            print("(dry run)")
            entries.append(make_entry(aid, None, None))
            continue

        s2 = query_s2(aid)
        time.sleep(SLEEP)

        cr = None
        if s2 and not ((s2.get("externalIds") or {}).get("DOI")) and s2.get("title"):
            first_author = (s2.get("authors") or [{}])[0].get("name", "")
            cr = query_crossref(s2["title"], first_author)
            time.sleep(SLEEP)

        entry = make_entry(aid, s2, cr)
        entries.append(entry)

        doi_found = ("doi" in entry and "@article" in entry)
        if doi_found:
            resolved += 1
            print("✓ journal")
        else:
            print("preprint")

    bib_out.parent.mkdir(parents=True, exist_ok=True)
    header = "% Auto-generated by tools/testing/reference_audit.py\n% Key: arxivNNNNNNNNN\n\n"
    bib_out.write_text(header + "\n\n".join(entries) + "\n")

    missing = len(ids) - resolved
    audit_lines = [
        f"Detected IDs: {len(ids)}",
        f"Resolved by CrossRef/S2: {resolved}",
        f"Missing IDs: {missing}",
    ]
    audit_out.write_text("\n".join(audit_lines) + "\n")
    print(f"\nResolved by CrossRef/S2: {resolved}")
    print(f"Missing IDs: {missing}")
    print(f"Bib: {bib_out}")
    print(f"Audit: {audit_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
