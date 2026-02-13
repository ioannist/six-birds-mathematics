#!/usr/bin/env python3
"""Generate a results dashboard from snapshot-visible notes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(".")

INPUTS = {
    "stencil_flow": Path("notes/stencil_flow_last_run.json"),
    "stencil_leibniz": Path("notes/stencil_flow_leibniz_last_run.json"),
    "false_positives": Path("notes/stencil_flow_false_positives.json"),
    "holonomy": Path("notes/holonomy_rm_last_run.json"),
    "prime_closure": Path("notes/prime_closure_rm_last_run.json"),
    "passivity": Path("notes/passivity_toy_last_run.json"),
    "integration": Path("notes/integration_closure_last_run.json"),
    "framework_summary": Path("notes/framework_index_summary.md"),
}


def read_json(path: Path) -> Tuple[bool, Any, str]:
    if not path.exists():
        return False, None, "missing"
    try:
        return True, json.loads(path.read_text()), "ok"
    except Exception as exc:  # noqa: BLE001
        return False, None, f"error parsing: {exc}"


def render_table(headers: List[str], rows: List[List[Any]]) -> List[str]:
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return lines


def parse_framework_summary(text: str) -> Tuple[str, str]:
    total = "(unknown)"
    env_line = "(unknown)"
    for line in text.splitlines():
        if line.startswith("- Total labels:"):
            total = line.split(":", 1)[1].strip()
        if line.startswith("| env_class"):
            # next lines contain table; summarize counts line
            continue
    # crude parse: collect rows until blank after env_class table
    lines = text.splitlines()
    env_rows = []
    in_table = False
    for line in lines:
        if line.strip().startswith("| env_class"):
            in_table = True
            continue
        if in_table:
            if not line.strip().startswith("|"):
                break
            if line.strip().startswith("| ---"):
                continue
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            if len(parts) >= 2:
                env_rows.append(f"{parts[0]}: {parts[1]}")
    if env_rows:
        env_line = ", ".join(env_rows)
    return total, env_line


def main() -> int:
    lines: List[str] = []
    read_ok: List[str] = []

    data: Dict[str, Any] = {}
    for key, path in INPUTS.items():
        if path.suffix == ".json":
            ok, obj, status = read_json(path)
            if ok:
                data[key] = obj
                read_ok.append(path.as_posix())
            else:
                data[key] = {"_status": status}
        else:
            if path.exists():
                data[key] = path.read_text()
                read_ok.append(path.as_posix())
            else:
                data[key] = None

    lines.append("# Results dashboard")
    lines.append("")
    lines.append("## Build status")
    lines.append("- Lean: (not checked by script)")
    lines.append("- Pytest: (not checked by script)")
    lines.append("")
    lines.append("## Exhibit A: Calculus closure")
    lines.append("")
    lines.append("### Finite difference Leibniz identity (Python)")
    lines.append("- python/sbt_math/diffops.py")
    lines.append("")
    lines.append("### Stencil flow (stability only)")
    sf = data.get("stencil_flow", {})
    if "_status" in sf:
        lines.append(f"- {sf['_status']}")
    else:
        lines.append(
            f"- generated_total: {sf.get('generated_total')}, survivors_total: {sf.get('survivors_total')}"
        )
        lines.append(f"- survivors_by_best_fit_k: {sf.get('survivors_by_best_fit_k')}")
        lines.append(f"- output_path: {sf.get('output_path')}")
    lines.append("")
    lines.append("### Stencil flow (Leibniz-gated)")
    sl = data.get("stencil_leibniz", {})
    if "_status" in sl:
        lines.append(f"- {sl['_status']}")
    else:
        counts = sl.get("survivors_by_best_fit_k")
        lines.append(f"- survivors_total: {sl.get('survivors_total')}")
        lines.append(f"- survivors_by_best_fit_k: {counts}")
        lines.append(f"- figure: {sl.get('figure_path', 'figures/stencil_flow_leibniz_last_run.svg')}")
        lines.append(f"- figure_png: {sl.get('figure_png_path', 'figures/stencil_flow_leibniz_last_run.png')}")
    lines.append("")
    lines.append("### Integration closure")
    integ = data.get("integration", {})
    if "_status" in integ:
        lines.append(f"- {integ['_status']}")
    else:
        lines.append(f"- output_path: {integ.get('output_path')}")
        lines.append(f"- figure_svg: {integ.get('figure_svg', 'figures/integration_closure_last_run.svg')}")
        lines.append(f"- figure_png: {integ.get('figure_png', 'figures/integration_closure_last_run.png')}")
        fits = integ.get("results", {}).get("fits", {})
        rm_fit = fits.get("rm_max", {})
        ft_fit = fits.get("ft_trap_max", {})
        lines.append(f"- rm exponent: {rm_fit.get('slope')}, rm r2: {rm_fit.get('r2')}")
        lines.append(f"- ft(trap) exponent: {ft_fit.get('slope')}, ft(trap) r2: {ft_fit.get('r2')}")
    lines.append("")
    lines.append("### False-positive hunt")
    fp = data.get("false_positives", {})
    if "_status" in fp:
        lines.append(f"- {fp['_status']}")
    else:
        counts = fp.get("counts", {})
        lines.append(f"- false_positive_total: {counts.get('false_positive_total')}")
        lines.append(f"- passed_leibniz_total: {counts.get('passed_leibniz_total')}")
    lines.append("")
    lines.append("## Exhibit A: Protocol holonomy")
    hol = data.get("holonomy", {})
    if "_status" in hol:
        lines.append(f"- {hol['_status']}")
    else:
        lines.append(f"- fit_p: {hol.get('fit_p')}")
        lines.append(f"- output_path: {hol.get('output_path')}")
        lines.append(f"- figure: {hol.get('figure_path', 'figures/holonomy_rm_last_run.svg')}")
        lines.append(f"- figure_png: {hol.get('figure_png_path', 'figures/holonomy_rm_last_run.png')}")
    lines.append("")
    lines.append("## Exhibit B: Prime closure diagnostics")
    pc = data.get("prime_closure", {})
    if "_status" in pc:
        lines.append(f"- {pc['_status']}")
    else:
        lines.append(f"- figure: {pc.get('figure_path', 'figures/prime_closure_rm_last_run.svg')}")
        lines.append(f"- figure_png: {pc.get('figure_png_path', 'figures/prime_closure_rm_last_run.png')}")
        lines.append(f"- trend_summary: {pc.get('trend_summary')}")
        lines.append("")
        lines.append("conv_table:")
        conv_table = pc.get("conv_table", [])
        if conv_table:
            lines.extend(render_table(["N", "rm2", "errS2", "errP2"], conv_table))
        else:
            lines.append("- (missing)")
        lines.append("")
        lines.append("strip_table:")
        strip_table = pc.get("strip_table", [])
        if strip_table:
            lines.extend(render_table(["N", "rm2", "errS2", "errP2"], strip_table))
        else:
            lines.append("- (missing)")
    lines.append("")
    lines.append("## Exhibit B: Passivity toy")
    pt = data.get("passivity", {})
    if "_status" in pt:
        lines.append(f"- {pt['_status']}")
    else:
        lines.append(f"- figure: {pt.get('figure_path', 'figures/passivity_toy_last_run.svg')}")
        lines.append(f"- figure_png: {pt.get('figure_png_path', 'figures/passivity_toy_last_run.png')}")
        table = pt.get("table", [])
        if table:
            lines.extend(render_table(["lambda", "mean_dev", "max_dev"], table))
        else:
            lines.append("- (missing)")
    lines.append("")
    lines.append("## Framework index")
    summary_text = data.get("framework_summary")
    if summary_text:
        total, env_line = parse_framework_summary(summary_text)
        lines.append(f"- total labels: {total}")
        lines.append(f"- env counts: {env_line}")
        lines.append("- notes/framework_index_summary.md")
    else:
        lines.append("- notes/framework_index_summary.md (missing)")
    lines.append("")
    lines.append("## Reproduction commands")
    lines.append("- python experiments/stencil_flow/run.py")
    lines.append("- python experiments/stencil_flow/leibniz_gate.py")
    lines.append("- python experiments/stencil_flow/hunt_false_positives.py")
    lines.append("- python experiments/holonomy_rm/run.py")
    lines.append("- python experiments/integration_closure/run.py")
    lines.append("- python experiments/prime_closure_rm/run.py")
    lines.append("- python experiments/passivity_toy/run.py")

    out_path = Path("notes/results_dashboard.md")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("read_ok:")
    for path in read_ok:
        print(path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
