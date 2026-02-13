#!/usr/bin/env python3
"""Scan TeX build log and refresh notes/tex_quality_report.md."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
import sys


LOG_PATH = Path("tex/math_instantiation/build/main.log")
OUT_PATH = Path("notes/tex_quality_report.md")


def count_matches(lines: list[str], pattern: re.Pattern[str]) -> int:
    return sum(1 for line in lines if pattern.search(line))


def main() -> int:
    if not LOG_PATH.exists():
        print(f"ERROR: missing log file: {LOG_PATH}", file=sys.stderr)
        return 2

    lines = LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()

    undef_cites = count_matches(lines, re.compile(r"Citation.*undefined"))
    undef_refs = count_matches(
        lines, re.compile(r"Reference.*undefined|There were undefined references")
    )
    overfull = count_matches(lines, re.compile(r"Overfull \\\\hbox"))
    underfull = count_matches(lines, re.compile(r"Underfull \\\\hbox"))
    latex_warn = count_matches(lines, re.compile(r"LaTeX Warning:"))
    pkg_warn = count_matches(lines, re.compile(r"Package .* Warning"))

    overfull_lines = [line for line in lines if "Overfull \\hbox" in line][:10]

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report_lines: list[str] = [
        "# TeX quality report",
        "",
        f"- timestamp_utc: {timestamp}",
        f"- undefined citations: {undef_cites}",
        f"- undefined references: {undef_refs}",
        f"- overfull hboxes: {overfull}",
        f"- underfull hboxes: {underfull}",
        f"- latex warnings: {latex_warn}",
        f"- package warnings: {pkg_warn}",
        "",
        "## top_overfull_hboxes",
    ]
    if overfull_lines:
        report_lines.extend(f"- {line}" for line in overfull_lines)
    else:
        report_lines.append("- (none)")

    OUT_PATH.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
