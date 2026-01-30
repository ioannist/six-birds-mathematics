#!/usr/bin/env bash
set -euo pipefail

root_dir=$(cd "$(dirname "$0")/.." && pwd)
paper_dir="$root_dir/tex/math_instantiation"
out_dir="$paper_dir/build"

mkdir -p "$out_dir"
cd "$paper_dir"

if command -v latexmk >/dev/null 2>&1; then
  latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir="$out_dir" main.tex
elif command -v pdflatex >/dev/null 2>&1; then
  pdflatex -interaction=nonstopmode -halt-on-error -output-directory "$out_dir" main.tex
  (cd "$out_dir" && bibtex main)
  pdflatex -interaction=nonstopmode -halt-on-error -output-directory "$out_dir" main.tex
  pdflatex -interaction=nonstopmode -halt-on-error -output-directory "$out_dir" main.tex
else
  echo "Error: latexmk or pdflatex not found" >&2
  exit 1
fi

if [ ! -f "$out_dir/main.pdf" ]; then
  echo "Error: $out_dir/main.pdf not generated" >&2
  exit 1
fi

echo "Built PDF: $out_dir/main.pdf"
