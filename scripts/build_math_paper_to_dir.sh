#!/usr/bin/env bash
set -euo pipefail

root_dir=$(cd "$(dirname "$0")/.." && pwd)
paper_dir="$root_dir/tex/math_instantiation"
out_dir="${1:-$paper_dir/build}"

mkdir -p "$out_dir"

if command -v latexmk >/dev/null 2>&1; then
  (cd "$paper_dir" && latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir="$out_dir" main.tex)
elif command -v pdflatex >/dev/null 2>&1; then
  (cd "$paper_dir" && pdflatex -interaction=nonstopmode -halt-on-error -output-directory "$out_dir" main.tex)
  (cd "$out_dir" && bibtex main)
  (cd "$paper_dir" && pdflatex -interaction=nonstopmode -halt-on-error -output-directory "$out_dir" main.tex)
  (cd "$paper_dir" && pdflatex -interaction=nonstopmode -halt-on-error -output-directory "$out_dir" main.tex)
else
  echo "Neither latexmk nor pdflatex found; cannot build." >&2
  exit 1
fi

if [ ! -f "$out_dir/main.pdf" ]; then
  echo "Build failed: $out_dir/main.pdf not found" >&2
  exit 1
fi

echo "Built PDF: $out_dir/main.pdf"
