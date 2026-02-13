#!/usr/bin/env bash
set -euo pipefail

python -c "import numpy, mpmath, sympy, matplotlib"
pytest -q
( cd lean && lake build )
if ls ./*.tex >/dev/null 2>&1; then
  python scripts/extract_tex_index.py
else
  echo "No root-level TeX framework file; skipping extract_tex_index.py"
fi
python scripts/make_dashboard.py
python -m py_compile \
  experiments/holonomy_rm/run.py \
  experiments/integration_closure/run.py \
  experiments/prime_closure_rm/run.py \
  experiments/passivity_toy/run.py \
  experiments/stencil_flow/run.py \
  experiments/stencil_flow/leibniz_gate.py \
  experiments/stencil_flow/hunt_false_positives.py \
  scripts/extract_tex_index.py \
  scripts/make_dashboard.py

if [ -f scripts/export_results_tex.py ]; then
  python -m py_compile scripts/export_results_tex.py
fi

if command -v latexmk >/dev/null 2>&1 || command -v pdflatex >/dev/null 2>&1; then
  bash scripts/build_math_paper.sh
else
  echo "TeX not available; skipping math paper build"
fi
