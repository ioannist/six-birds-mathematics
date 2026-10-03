#!/usr/bin/env bash
# Recheck mathematics without regenerating or building any paper sources.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -n "${SBT_MATH_PYTHON:-}" ]]; then
  review_python="$SBT_MATH_PYTHON"
elif [[ -x .venv/bin/python ]]; then
  review_python=.venv/bin/python
else
  review_python=python3
fi
mkdir -p notes/math_review logs/math_review figures/tmp/math_review
"$review_python" -m pytest -q | tee logs/math_review/pytest.log
(cd lean && lake build) > logs/math_review/lean-build.log 2>&1
(cd lean && lake env lean Main.lean) > logs/math_review/lean-axioms.log 2>&1
"$review_python" experiments/stencil_flow/run.py \
  --out notes/math_review/stencil_baseline_run.json \
  --notes-out notes/math_review/stencil_baseline_pointer.json > logs/math_review/stencil-baseline.log 2>&1
"$review_python" experiments/stencil_flow/leibniz_gate.py \
  --out notes/math_review/stencil_leibniz_run.json \
  --notes-out notes/math_review/stencil_leibniz_pointer.json \
  --fig-out figures/tmp/math_review/stencil.svg > logs/math_review/stencil-leibniz.log 2>&1
"$review_python" experiments/stencil_flow/matched_controls.py > logs/math_review/stencil-matched.log 2>&1
"$review_python" experiments/stencil_flow/hunt_false_positives.py \
  --out notes/math_review/stencil_false_positives.json > logs/math_review/stencil-hunt.log 2>&1
for exhibit in holonomy_rm integration_closure prime_closure_rm passivity_toy; do
  case "$exhibit" in
    holonomy_rm) stem=holonomy ;;
    integration_closure) stem=integration ;;
    prime_closure_rm) stem=prime ;;
    passivity_toy) stem=passivity ;;
  esac
  "$review_python" "experiments/$exhibit/run.py" \
    --out "notes/math_review/${stem}_run.json" \
    --notes-out "notes/math_review/${stem}_pointer.json" \
    --fig-out "figures/tmp/math_review/${stem}.svg" > "logs/math_review/${stem}.log" 2>&1
done
"$review_python" scripts/audit_math.py | tee logs/math_review/artifact-audit.log
