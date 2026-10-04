# Six Birds: Mathematics Instantiation

This repository contains the **mathematics instantiation** for the paper:

> **To Count a Stone with Six Birds: A Mathematics is A Theory**
>
> Archived at: https://zenodo.org/records/18402004
>
> DOI: https://doi.org/10.5281/zenodo.18402004

This paper is the mathematics-focused instantiation of the emergence calculus introduced in *Six Birds: Foundations of Emergence Calculus*. It demonstrates how "higher" mathematical objects (limits, completions, analytic continuations) can be viewed as closure pipelines, and provides falsification-first diagnostics for testing when discrete protocols admit stable continuous closures.

## What this repository provides

The mathematics instantiation implements:

- **Lean/mathlib anchors**: machine-checked statements (17 exported declarations, axiom-audited) for the finite-difference Leibniz identity and linearity, a limit bridge to the Leibniz rule, the classification of derivations of R[X], and the packaging, descent, and linear route-bound contracts
- **Matched stencil experiment**: in a fixed population of order-0/1/2 stencils, a stability gate keeps all three orders while adding a shrinking Leibniz defect keeps only first-derivative stencils
- **Integration diagnostics**: left/trapezoid route mismatch, fundamental-theorem defects, and errors against exact antiderivatives
- **Route-mismatch diagnostics**: mismatch between two derivative routes under a coordinate change, with an identity-chart null control and truth checks
- **Prime closure route mismatch**: staged additive vs multiplicative descriptions of zeta in a provably convergent control regime vs the critical strip
- **Positivity toy model**: Ising partition polynomial whose zeros move onto the unit circle as negative couplings are removed (Lee–Yang at the endpoint)
- **Artifact contract**: paper numbers, tables, and figures are generated from the reviewed JSON artifacts in `notes/math_review/`

## Scope and limitations

The paper is explicit about what it does and does not establish:

- Exhibits are diagnostic and controlled; they do not prove theorems about zeta zeros or settle classical conjectures
- Route mismatch is a computable defect for stress-testing closure claims, not a geometric proof
- The positivity toy's endpoint is the Lee–Yang theorem; its intermediate trend is one sampled system, not a general result
- Prime closure diagnostics separate regimes but treat critical-strip mismatch growth as staging/packaging feasibility failure, not as a theorem about the Riemann zeta function

## Install

```bash
pip install -r requirements.txt
cd lean && lake build
```

## Test

```bash
pytest -q
bash scripts/check_all.sh
```

## Run experiments

```bash
python experiments/stencil_flow/run.py
python experiments/holonomy_rm/run.py
python experiments/prime_closure_rm/run.py
python experiments/passivity_toy/run.py
```

## Build paper

```bash
bash scripts/check_all.sh --math-only   # rerun tests, Lean, experiments, audits
python scripts/export_results_tex.py     # macros and tables from notes/math_review/
python scripts/make_paper_figures.py     # figures/paper/
bash scripts/build_math_paper.sh
```

## Generate dashboard

```bash
python scripts/make_dashboard.py
```
