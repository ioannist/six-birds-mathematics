#!/usr/bin/env python3
"""Build Qeios-ready PDF + source bundle for the math paper."""

from __future__ import annotations

import re
import shutil
import subprocess
import textwrap
from datetime import datetime, timezone
from pathlib import Path


def _extract_command_arg(tex: str, command: str) -> str:
    needle = f"\\{command}" + "{"
    start = tex.find(needle)
    if start < 0:
        raise SystemExit(f"[build_qeios_package] ERROR: missing \\{command}{{...}} in main.tex")

    i = start + len(needle)
    depth = 1
    while i < len(tex) and depth > 0:
        ch = tex[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        i += 1
    if depth != 0:
        raise SystemExit(f"[build_qeios_package] ERROR: unbalanced braces in \\{command} argument")
    return tex[start + len(needle) : i - 1].strip()


def _resolve_input(base_file: Path, include_name: str, paper_dir: Path) -> Path:
    raw = include_name.strip()
    candidates = []
    p = Path(raw)
    if p.suffix:
        candidates.extend([base_file.parent / p, paper_dir / p])
    else:
        candidates.extend([base_file.parent / f"{raw}.tex", paper_dir / f"{raw}.tex"])
    for c in candidates:
        if c.exists():
            return c.resolve()
    raise SystemExit(f"[build_qeios_package] ERROR: could not resolve \\input{{{include_name}}} from {base_file}")


def _expand_inputs(path: Path, paper_dir: Path, stack: list[Path] | None = None) -> str:
    stack = stack or []
    if path in stack:
        cycle = " -> ".join(str(p) for p in stack + [path])
        raise SystemExit(f"[build_qeios_package] ERROR: cyclic \\input detected: {cycle}")
    stack = stack + [path]
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r"\\input\{([^}]+)\}")
    out = []
    pos = 0
    for m in pattern.finditer(text):
        out.append(text[pos : m.start()])
        inc = _resolve_input(path, m.group(1), paper_dir)
        out.append(f"\n% --- begin inlined: {inc.relative_to(paper_dir)} ---\n")
        out.append(_expand_inputs(inc, paper_dir, stack))
        out.append(f"\n% --- end inlined: {inc.relative_to(paper_dir)} ---\n")
        pos = m.end()
    out.append(text[pos:])
    return "".join(out)


def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    paper_dir = repo_root / "tex" / "math_instantiation"
    build_dir = paper_dir / "build"
    qeios_dir = build_dir / "qeios_single"
    bundle_zip = build_dir / "qeios_source_bundle.zip"
    out_pdf = build_dir / "qeios_submission.pdf"

    # Ensure main paper + artifacts are up to date.
    _run(["bash", "scripts/build_math_paper.sh"], repo_root)

    main_tex = (paper_dir / "main.tex").read_text(encoding="utf-8")
    title = _extract_command_arg(main_tex, "Title")
    abstract = _extract_command_arg(main_tex, "abstract")
    keywords = _extract_command_arg(main_tex, "keyword")
    doi_match = re.search(r"(10\.5281/zenodo\.\d+)", main_tex)
    doi = doi_match.group(1) if doi_match else "10.5281/zenodo.18402004"
    orcid_match = re.search(r"\\newcommand\{\\orcidauthorA\}\{([^}]+)\}", main_tex)
    orcid = orcid_match.group(1).strip() if orcid_match else "0009-0009-7659-5964"

    section_inputs = re.findall(r"\\input\{(sections/[^}]+)\}", main_tex)
    if not section_inputs:
        raise SystemExit("[build_qeios_package] ERROR: no section inputs found in main.tex")

    macros_path = _resolve_input(paper_dir / "main.tex", "generated/macros", paper_dir)
    expanded_macros = _expand_inputs(macros_path, paper_dir)
    expanded_sections = []
    for sec in section_inputs:
        sec_path = _resolve_input(paper_dir / "main.tex", sec, paper_dir)
        expanded_sections.append(_expand_inputs(sec_path, paper_dir))

    if qeios_dir.exists():
        shutil.rmtree(qeios_dir)
    qeios_dir.mkdir(parents=True, exist_ok=True)

    qeios_tex = textwrap.dedent(
        f"""\
        \\documentclass[11pt]{{article}}

        \\usepackage[T1]{{fontenc}}
        \\usepackage{{lmodern}}
        \\usepackage{{amsmath}}
        \\usepackage{{amssymb}}
        \\usepackage{{amsthm}}
        \\usepackage{{mathtools}}
        \\usepackage{{microtype}}
        \\usepackage{{graphicx}}
        \\usepackage{{booktabs}}
        \\usepackage{{array}}
        \\usepackage{{tabularx}}
        \\usepackage{{multirow}}
        \\usepackage{{enumitem}}
        \\usepackage{{xcolor}}
        \\usepackage{{fancyhdr}}
        % orcidlink: use package if available, else provide a fallback
        \\IfFileExists{{orcidlink.sty}}{{\\usepackage{{orcidlink}}}}{{%
          \\newcommand{{\\orcidlink}}[1]{{\\textsuperscript{{\\href{{https://orcid.org/#1}}{{ORCID}}}}}}%
        }}
        \\usepackage[margin=1in]{{geometry}}
        \\usepackage{{float}}
        \\usepackage[section]{{placeins}}
        \\usepackage{{caption}}
        \\usepackage{{xurl}}
        \\usepackage{{hyperref}}
        \\hypersetup{{
          colorlinks=true,
          linkcolor=blue!70!black,
          citecolor=green!50!black,
          urlcolor=blue!80!black,
          bookmarksnumbered=true,
          pdfauthor={{Ioannis Tsiokos}},
          pdftitle={{{title}}}
        }}
        \\usepackage{{cleveref}}
        \\crefname{{section}}{{section}}{{sections}}
        \\crefname{{table}}{{table}}{{tables}}
        \\crefname{{figure}}{{figure}}{{figures}}
        \\usepackage{{natbib}}

        \\graphicspath{{{{figures/}}}}

        \\widowpenalty=10000
        \\clubpenalty=10000
        \\raggedbottom

        \\newtheorem{{definition}}{{Definition}}
        \\newtheorem{{theorem}}{{Theorem}}
        \\newtheorem{{lemma}}{{Lemma}}
        \\newtheorem{{corollary}}{{Corollary}}
        \\newtheorem{{remark}}{{Remark}}

        \\newcommand{{\\SBT}}{{\\textsc{{SBT}}}}
        \\newcommand{{\\Pone}}{{\\textbf{{P1}}}}
        \\newcommand{{\\Ptwo}}{{\\textbf{{P2}}}}
        \\newcommand{{\\Pthree}}{{\\textbf{{P3}}}}
        \\newcommand{{\\Pfour}}{{\\textbf{{P4}}}}
        \\newcommand{{\\Pfive}}{{\\textbf{{P5}}}}
        \\newcommand{{\\Psix}}{{\\textbf{{P6}}}}

        \\fancypagestyle{{firstpage}}{{\\fancyhf{{}}
          \\fancyfoot[C]{{\\scriptsize Automorph Inc., Wilmington, DE, USA \\quad \\texttt{{ioannis@automorph.io}} \\quad Zenodo DOI: \\href{{https://doi.org/{doi}}}{{{doi}}} \\quad \\textcopyright\\ 2026 \\quad CC-BY 4.0}}
          \\renewcommand{{\\headrulewidth}}{{0pt}}
          \\renewcommand{{\\footrulewidth}}{{0pt}}
        }}

        \\title{{{title}}}
        \\author{{Ioannis Tsiokos\\,\\orcidlink{{{orcid}}}}}
        \\date{{28 January 2026\\\\[4pt]{{\\small Zenodo preprint: \\href{{https://doi.org/{doi}}}{{{doi}}}}}}}

        \\newcommand{{\\printaffiliation}}{{\\begin{{center}}\\small \\end{{center}}}}

        \\begin{{document}}
        \\maketitle
        \\thispagestyle{{firstpage}}
        \\printaffiliation

        \\begin{{abstract}}
        {abstract}
        \\end{{abstract}}

        \\vspace{{1ex}}
        \\noindent\\textbf{{keywords:}} {keywords}

        % --- begin inlined: generated/macros.tex ---
        {expanded_macros}
        % --- end inlined: generated/macros.tex ---

        {"".join(expanded_sections)}

        \\bibliographystyle{{plainnat}}
        \\bibliography{{refs}}

        \\end{{document}}
        """
    )

    qeios_tex_path = qeios_dir / "qeios_single.tex"
    qeios_tex_path.write_text(qeios_tex, encoding="utf-8")

    # Copy bibliography.
    refs_src = paper_dir / "bib" / "refs.bib"
    shutil.copy2(refs_src, qeios_dir / "refs.bib")

    # Copy only referenced figures.
    fig_dir = qeios_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    fig_names = []
    for raw in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", qeios_tex):
        name = Path(raw).name
        if name and name not in fig_names:
            fig_names.append(name)
    for name in fig_names:
        src = repo_root / "figures" / name
        if not src.exists():
            raise SystemExit(f"[build_qeios_package] ERROR: referenced figure missing: {src}")
        shutil.copy2(src, fig_dir / name)

    # Build qeios_single.tex
    latexmk = shutil.which("latexmk")
    pdflatex = shutil.which("pdflatex")
    if latexmk:
        _run([latexmk, "-pdf", "-g", "-interaction=nonstopmode", "-halt-on-error", "qeios_single.tex"], qeios_dir)
    elif pdflatex:
        _run([pdflatex, "-interaction=nonstopmode", "-halt-on-error", "qeios_single.tex"], qeios_dir)
        _run([shutil.which("bibtex") or "bibtex", "qeios_single"], qeios_dir)
        _run([pdflatex, "-interaction=nonstopmode", "-halt-on-error", "qeios_single.tex"], qeios_dir)
        _run([pdflatex, "-interaction=nonstopmode", "-halt-on-error", "qeios_single.tex"], qeios_dir)
    else:
        raise SystemExit("[build_qeios_package] ERROR: missing latexmk/pdflatex")

    pdf_src = qeios_dir / "qeios_single.pdf"
    if not pdf_src.exists():
        raise SystemExit("[build_qeios_package] ERROR: qeios_single.pdf was not produced")
    shutil.copy2(pdf_src, out_pdf)

    # Build zip bundle.
    if bundle_zip.exists():
        bundle_zip.unlink()
    subprocess.run(["zip", "-r", str(bundle_zip), "."], cwd=qeios_dir, check=True, stdout=subprocess.DEVNULL)

    # Companion notes/readme (same outputs style as six-birds-time).
    notes_path = build_dir / "Qeios_Submission_Notes.md"
    notes_text = textwrap.dedent(
        f"""\
        # Qeios Submission Notes

        **Title:** {title}
        **Author:** Ioannis Tsiokos
        **Corresponding email:** ioannis@automorph.io

        ## Upload files
        - Preferred source: `tex/math_instantiation/build/qeios_single/qeios_single.tex`
        - Source bundle: `tex/math_instantiation/build/qeios_source_bundle.zip`
        - Pre-built PDF: `tex/math_instantiation/build/qeios_submission.pdf`

        ## Links
        - Zenodo DOI: https://doi.org/{doi}
        - GitHub repository: https://github.com/ioannist/six-birds-mathematics

        Generated UTC timestamp: {datetime.now(timezone.utc).isoformat(timespec="seconds")}
        """
    )
    notes_path.write_text(notes_text, encoding="utf-8")

    readme_path = build_dir / "README_BUILD.txt"
    readme_text = textwrap.dedent(
        """\
        README_BUILD.txt
        ================
        Qeios package build instructions

        Single-file build:
            pdflatex qeios_single.tex
            bibtex qeios_single
            pdflatex qeios_single.tex
            pdflatex qeios_single.tex

        Or:
            latexmk -pdf -interaction=nonstopmode -halt-on-error qeios_single.tex

        Files:
          qeios_single/qeios_single.tex
          qeios_single/qeios_single.pdf
          qeios_source_bundle.zip
          qeios_submission.pdf
          Qeios_Submission_Notes.md
        """
    )
    readme_path.write_text(readme_text, encoding="utf-8")

    print(f"[build_qeios_package] Wrote {out_pdf}")
    print(f"[build_qeios_package] Wrote {bundle_zip}")
    print(f"[build_qeios_package] Wrote {qeios_tex_path}")
    print(f"[build_qeios_package] Wrote {notes_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
