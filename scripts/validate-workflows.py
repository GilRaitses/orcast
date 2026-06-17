#!/usr/bin/env python3
"""Validate GitHub workflow files and log findings for CI debug session."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

LOG_PATH = Path("/Users/gilraitses/orcast/.cursor/debug-38fb92.log")
SESSION_ID = "38fb92"
WORKFLOWS = [
    Path("/Users/gilraitses/orcast/.github/workflows/firebase-hosting-merge.yml"),
    Path("/Users/gilraitses/orcast/.github/workflows/cloudflare-deploy.yml"),
]

SECRET_IN_JOB_IF = re.compile(r"^\s*if:\s*\$\{\{\s*.*secrets\.", re.MULTILINE)


def log(hypothesis_id: str, location: str, message: str, data: dict, run_id: str = "pre-fix") -> None:
    entry = {
        "sessionId": SESSION_ID,
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def main() -> int:
    run_id = __import__("os").environ.get("VALIDATE_RUN_ID", "pre-fix")
    failures = 0

    for path in WORKFLOWS:
        text = path.read_text(encoding="utf-8")

        # H1: secrets referenced in job-level if (GitHub rejects workflow)
        job_if_matches = []
        in_jobs = False
        job_indent = None
        for i, line in enumerate(text.splitlines(), 1):
            if line.startswith("jobs:"):
                in_jobs = True
                continue
            if in_jobs and line and not line.startswith(" ") and not line.startswith("\t"):
                in_jobs = False
            if in_jobs and re.match(r"^  \w", line) and not line.startswith("    "):
                job_indent = line[: len(line) - len(line.lstrip())]
            if "if:" in line and "secrets." in line:
                stripped = line.lstrip()
                if stripped.startswith("if:") and (job_indent is None or line.startswith(job_indent + "  ")):
                    # job-level or nested - flag any if with secrets at job level (2-space job, 4-space if)
                    if re.match(r"^  \S.+:\s*$", line) or re.match(r"^    if:", line):
                        job_if_matches.append({"line": i, "content": line.strip()})

        # simpler: any line with if: and secrets. under jobs section at 4-space indent (job if)
        job_if_simple = []
        for i, line in enumerate(text.splitlines(), 1):
            if re.match(r"^    if:.*secrets\.", line):
                job_if_simple.append({"line": i, "content": line.strip()})

        if job_if_simple:
            failures += 1
            log(
                "H1",
                f"{path}:job-if-secrets",
                "Job-level if references secrets context (invalid in GitHub Actions)",
                {"matches": job_if_simple, "file": str(path)},
                run_id,
            )
        else:
            log("H1", f"{path}:job-if-secrets", "No job-level secrets in if", {"file": str(path)}, run_id)

        # H2: basic YAML structure
        if "jobs:" not in text or "runs-on:" not in text:
            failures += 1
            log("H2", f"{path}:yaml", "Missing jobs or runs-on", {"file": str(path)}, run_id)

        # H3: duplicate job ids
        job_ids = re.findall(r"^  (\S+):\s*$", text, re.MULTILINE)
        dupes = [j for j in job_ids if job_ids.count(j) > 1]
        if dupes:
            failures += 1
            log("H3", f"{path}:jobs", "Duplicate job ids", {"dupes": dupes}, run_id)

    log("SUMMARY", "validate-workflows.py", "Validation complete", {"failures": failures}, run_id)
    print(f"failures={failures} log={LOG_PATH}")
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
