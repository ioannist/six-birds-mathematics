# Mathematics checks

Run `bash scripts/check_all.sh --math-only` for the mathematical review gate.
It uses `.venv/bin/python` when available, or `SBT_MATH_PYTHON` when explicitly
set. Install `requirements.txt` in that environment first.

The gate checks Python regressions, builds Lean, audits the exported declarations'
transitive axioms, reruns every mathematical experiment into
`notes/math_review/`, and compares prime and Ising diagnostics at higher
precision. `scripts/audit_math.py` checks the resulting artifacts and records
package versions and source hashes in `notes/math_review/verification.json`.

This mode does not regenerate paper files or overwrite historical paper pointers.
The detailed mathematical corrections and later editorial handoff are in
`notes/math_review/review.md` and `notes/claim_ledger.md`.
