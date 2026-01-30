#!/usr/bin/env python3
"""Extract LaTeX \label entries with best-effort context."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


TOKEN_RE = re.compile(
    r"\\(?:(?P<section>section|subsection|subsubsection)\*?\s*\{|"
    r"(?P<begin>begin)\s*\{|"
    r"(?P<end>end)\s*\{|"
    r"(?P<label>label)\s*\{|"
    r"(?P<input>input)\s*\{|"
    r"(?P<include>include)\s*\{)"
)
DISPLAY_OPEN_RE = re.compile(r"(?<!\\)\\\[")
DISPLAY_CLOSE_RE = re.compile(r"(?<!\\)\\\]")

EQUATION_LIKE = {"equation", "align", "gather", "multline", "eqnarray"}
THEOREM_LIKE = {"theorem", "lemma", "corollary", "proposition"}


def strip_comments(line: str) -> str:
    out: List[str] = []
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == "%":
            backslashes = 0
            j = i - 1
            while j >= 0 and line[j] == "\\":
                backslashes += 1
                j -= 1
            if backslashes % 2 == 0:
                break
        out.append(ch)
        i += 1
    return "".join(out)


def parse_braced_arg(s: str, brace_start: int) -> Tuple[Optional[str], Optional[int]]:
    if brace_start < 0 or brace_start >= len(s) or s[brace_start] != "{":
        return None, None
    depth = 1
    i = brace_start + 1
    start = i
    while i < len(s):
        ch = s[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return s[start:i], i
        i += 1
    return None, None


def classify_env(env: Optional[str]) -> str:
    if env is None:
        return "none"
    base = env.rstrip("*")
    if base == "displaymath":
        return "equation"
    if base in THEOREM_LIKE:
        return base
    if base == "definition":
        return "definition"
    if base == "remark":
        return "remark"
    if base in EQUATION_LIKE:
        return "equation"
    return "other"


def detect_main_tex(root: Path) -> Path:
    alt = root / "six-birds-paper.tex"
    if alt.exists():
        return alt
    paper = root / "paper.tex"
    if paper.exists():
        return paper
    tex_files = sorted(root.glob("*.tex"))
    if len(tex_files) == 1:
        return tex_files[0]
    candidates = ", ".join(p.name for p in tex_files) or "(none found)"
    raise SystemExit(
        "Could not autodetect TeX main file. Candidates at repo root: "
        f"{candidates}. Use --tex to specify."
    )


def resolve_include(current: Path, target: str) -> Optional[Path]:
    target = target.strip()
    if not target:
        return None
    candidate = (current.parent / target).resolve()
    candidates = [candidate]
    if candidate.suffix == "":
        candidates.append(candidate.with_suffix(".tex"))
    for path in candidates:
        if path.exists():
            return path
    return None


def parse_file(
    path: Path,
    root: Path,
    state: Dict[str, Optional[str]],
    env_stack: List[str],
    seen: Set[Path],
    records: List[Dict[str, object]],
    include_enabled: bool,
) -> None:
    path = path.resolve()
    if path in seen:
        return
    seen.add(path)

    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        print(f"warning: missing TeX file {path}", file=sys.stderr)
        return

    rel_file = path.relative_to(root).as_posix()

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = strip_comments(raw_line)
        if not line:
            continue
        if DISPLAY_OPEN_RE.search(line):
            env_stack.append("displaymath")
        if DISPLAY_CLOSE_RE.search(line):
            if env_stack and env_stack[-1] == "displaymath":
                env_stack.pop()
        for match in TOKEN_RE.finditer(line):
            brace_start = match.end() - 1
            arg, _ = parse_braced_arg(line, brace_start)
            if arg is None:
                continue
            arg = arg.strip()

            if match.group("section"):
                cmd = match.group("section")
                if cmd == "section":
                    state["section"] = arg or None
                    state["subsection"] = None
                    state["subsubsection"] = None
                elif cmd == "subsection":
                    state["subsection"] = arg or None
                    state["subsubsection"] = None
                else:
                    state["subsubsection"] = arg or None
                continue

            if match.group("begin"):
                if arg:
                    env_stack.append(arg)
                continue

            if match.group("end"):
                if not arg:
                    continue
                if env_stack and env_stack[-1] == arg:
                    env_stack.pop()
                elif arg in env_stack:
                    idx = len(env_stack) - 1 - env_stack[::-1].index(arg)
                    env_stack.pop(idx)
                continue

            if match.group("label"):
                label = arg
                env = env_stack[-1] if env_stack else None
                records.append(
                    {
                        "label": label,
                        "file": rel_file,
                        "line": lineno,
                        "section": state.get("section"),
                        "subsection": state.get("subsection"),
                        "subsubsection": state.get("subsubsection"),
                        "environment": env,
                        "env_class": classify_env(env),
                    }
                )
                continue

            if match.group("input") or match.group("include"):
                if not include_enabled:
                    continue
                include_path = resolve_include(path, arg)
                if include_path is None:
                    print(
                        f"warning: could not resolve include '{arg}' from {path}",
                        file=sys.stderr,
                    )
                    continue
                parse_file(
                    include_path,
                    root,
                    state,
                    env_stack,
                    seen,
                    records,
                    include_enabled,
                )


def write_summary(
    out_path: Path,
    tex_main: Path,
    records: List[Dict[str, object]],
) -> None:
    total = len(records)
    env_counts = Counter(rec["env_class"] for rec in records)
    section_counts = Counter(rec["section"] for rec in records)

    def fmt_section(name: Optional[str]) -> str:
        return name if name else "(none)"

    top_sections = section_counts.most_common(10)

    lines: List[str] = []
    lines.append("# Framework Index Summary")
    lines.append(f"- TeX main: {tex_main.name}")
    lines.append(f"- Total labels: {total}")
    lines.append("")
    lines.append("## Counts by env_class")
    lines.append("| env_class | count |")
    lines.append("| --- | ---: |")
    for key in sorted(env_counts.keys()):
        lines.append(f"| {key} | {env_counts[key]} |")
    lines.append("")
    lines.append("## Top sections by label count")
    lines.append("| section | count |")
    lines.append("| --- | ---: |")
    for section, count in top_sections:
        lines.append(f"| {fmt_section(section)} | {count} |")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract LaTeX labels.")
    parser.add_argument("--tex", type=str, help="Path to main TeX file")
    parser.add_argument(
        "--out-json",
        type=str,
        default="notes/framework_index.json",
        help="Output JSON path",
    )
    parser.add_argument(
        "--out-summary",
        type=str,
        default="notes/framework_index_summary.md",
        help="Output summary markdown path",
    )
    parser.add_argument(
        "--min-labels",
        type=int,
        default=50,
        help="Fail if fewer labels are found",
    )
    parser.add_argument(
        "--no-include",
        action="store_true",
        help="Disable include/input processing",
    )

    args = parser.parse_args()

    root = Path.cwd()
    tex_main = Path(args.tex).resolve() if args.tex else detect_main_tex(root)
    if not tex_main.exists():
        raise SystemExit(f"TeX file not found: {tex_main}")

    state = {"section": None, "subsection": None, "subsubsection": None}
    env_stack: List[str] = []
    seen: Set[Path] = set()
    records: List[Dict[str, object]] = []

    parse_file(
        tex_main,
        root,
        state,
        env_stack,
        seen,
        records,
        include_enabled=not args.no_include,
    )

    records.sort(key=lambda rec: (rec["label"], rec["file"], rec["line"]))

    if len(records) < args.min_labels:
        raise SystemExit(
            f"Found {len(records)} labels, which is fewer than --min-labels={args.min_labels}"
        )

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {
            "tex_main": tex_main.name,
            "files_parsed_count": len(seen),
            "labels_count": len(records),
        },
        "records": records,
    }
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    write_summary(Path(args.out_summary), tex_main, records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
