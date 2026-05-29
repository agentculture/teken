#!/usr/bin/env python3
"""Render coverage.xml as a sticky PR comment.

Reads a Cobertura ``coverage.xml`` (produced by ``pytest --cov-report=xml``),
builds a Markdown summary, and posts it as a single update-in-place comment on
the pull request — so re-runs refresh the same comment instead of spamming new
ones. The update-in-place trick mirrors the ``version-check`` job in
``tests.yml``: find a comment carrying a hidden marker, ``PATCH`` it if present,
otherwise ``POST`` a new one.

Usage:
    coverage_comment.py [coverage.xml]

Environment (only needed to actually post; absent → print to stdout):
    GITHUB_REPOSITORY   owner/repo
    PR_NUMBER           pull-request number
    GH_TOKEN            token for the ``gh`` CLI (set by the workflow)
"""

from __future__ import annotations

import os
import subprocess  # noqa: S404 - we only ever invoke the trusted `gh` CLI
import sys
import xml.etree.ElementTree as ET  # noqa: S405 - trusted CI coverage.xml, not user input

MARKER = "<!-- coverage-report -->"
MAX_ROWS = 25


def _pct(rate: str | float) -> float:
    return float(rate) * 100.0


def build_comment(xml_text: str) -> str:
    """Build the Markdown comment body from Cobertura XML text."""
    root = ET.fromstring(xml_text)  # noqa: S314 - our own CI artifact, trusted

    line_pct = _pct(root.get("line-rate", "0"))
    lines_covered = int(root.get("lines-covered", "0"))
    lines_valid = int(root.get("lines-valid", "0"))
    branches_valid = int(root.get("branches-valid", "0"))
    branch_pct = _pct(root.get("branch-rate", "0"))

    icon = "🟢" if line_pct >= 80 else "🟡" if line_pct >= 60 else "🔴"

    out = [
        f"## {icon} Coverage report",
        "",
        f"**Line coverage: {line_pct:.1f}%** &nbsp;({lines_covered}/{lines_valid} lines)",
    ]
    if branches_valid:
        out.append(f"**Branch coverage: {branch_pct:.1f}%** &nbsp;({branches_valid} branches)")
    out.append("")

    # Per-file rows for anything below 100% line coverage, worst first.
    rows = []
    for cls in root.iter("class"):
        filename = cls.get("filename", "?")
        rate = float(cls.get("line-rate", "0"))
        if rate >= 1.0:
            continue
        missing = sum(1 for ln in cls.iter("line") if ln.get("hits") == "0")
        rows.append((rate, filename, missing))
    rows.sort(key=lambda r: (r[0], r[1]))

    if rows:
        out.append("<details><summary>Files below 100% line coverage</summary>")
        out.append("")
        out.append("| File | Coverage | Uncovered lines |")
        out.append("|------|---------:|----------------:|")
        for rate, filename, missing in rows[:MAX_ROWS]:
            out.append(f"| `{filename}` | {rate * 100:.0f}% | {missing} |")
        if len(rows) > MAX_ROWS:
            out.append(f"| … | | _+{len(rows) - MAX_ROWS} more files_ |")
        out.append("")
        out.append("</details>")
    else:
        out.append("All measured files are fully covered. 🎉")

    out.append("")
    out.append(f"<sub>Generated from `coverage.xml` by `pytest --cov`. {MARKER}</sub>")
    return "\n".join(out)


def _gh(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    # `gh` is resolved from PATH in the GitHub Actions runner; args are static.
    return subprocess.run(  # noqa: S603,S607
        ["gh", *args], capture_output=True, text=True, check=check
    )


def post_comment(repo: str, pr: str, body: str) -> None:
    """Create or update the sticky coverage comment on the PR."""
    found = _gh(
        "api",
        f"repos/{repo}/issues/{pr}/comments",
        "--paginate",
        "--jq",
        f'.[] | select(.body | contains("{MARKER}")) | .id',
    )
    existing = [line for line in found.stdout.splitlines() if line.strip()]
    if existing:
        _gh(
            "api",
            f"repos/{repo}/issues/comments/{existing[0]}",
            "-X",
            "PATCH",
            "-f",
            f"body={body}",
        )
    else:
        _gh("api", f"repos/{repo}/issues/{pr}/comments", "-f", f"body={body}")


def main(argv: list[str]) -> int:
    xml_path = argv[1] if len(argv) > 1 else "coverage.xml"
    try:
        with open(xml_path, encoding="utf-8") as handle:
            body = build_comment(handle.read())
    except (OSError, ET.ParseError) as exc:
        print(f"coverage_comment: could not read {xml_path}: {exc}", file=sys.stderr)
        return 1

    repo = os.environ.get("GITHUB_REPOSITORY")
    pr = os.environ.get("PR_NUMBER")
    if repo and pr:
        post_comment(repo, pr, body)
        print(f"Posted coverage comment to {repo}#{pr}")
    else:
        # Local / non-PR run: just print the rendered comment.
        print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
