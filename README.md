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

- **Lean/mathlib anchors**: machine-checked statements that pin key parts of the narrative (finite-difference Leibniz identity with explicit remainder term; derivations on polynomial rings determined by the value on X)
- **Stencil selection experiments**: stability and Leibniz-defect gates under refinement, showing derivative-like closures emerge when both constraints are applied
- **Route-mismatch diagnostics**: holonomy/protocol mismatch decay under coordinate change with power-law fits
- **Prime closure route mismatch**: comparing staged additive vs multiplicative micro-descriptions across convergence control vs critical strip regimes
- **Passivity toy model**: demonstrating "feasibility/positivity tightening implies zero confinement to a symmetry locus"
- **Artifact contract**: paper numbers/tables/figures are generated from snapshot-visible JSON pointers; TeX imports generated macros so the PDF stays consistent with repository state

See also: [six-birds-neural](https://github.com/anthropics/six-birds-neural) for the neural/meta-layer substrate.

## Scope and limitations

The paper is explicit about what it does and does not establish:

- Exhibits are diagnostic and controlled; they do not prove theorems about zeta zeros or settle classical conjectures
- Route mismatch is a computable defect for stress-testing closure claims, not a geometric proof
- The passivity toy illustrates a pattern (positivity constraint implies zero confinement) but does not claim generality
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
bash scripts/build_math_paper.sh
```

## Generate dashboard

```bash
python scripts/make_dashboard.py
```
