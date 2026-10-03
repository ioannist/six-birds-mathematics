# Mathematical claim ledger

Reviewed on 2026-10-03 against checkpoint `9410bce`. The current mathematics and
code supersede the historical experiments; the paper and its generated inputs
are deliberately unchanged. Detailed hypotheses, proofs, counterexamples, and
editorial handoff: [math_review/review.md](math_review/review.md).

| Claim | Status and exact scope | Evidence |
| --- | --- | --- |
| Finite-difference Leibniz identity | Correct over any field with nonzero step. | `Diff.delta_mul_leibniz`; fresh axiom audit |
| Difference-quotient linearity | Addition, constant multiples, constant annihilation proved. | `Diff.delta_add`, `delta_const_mul`, `delta_const` |
| Vanishing remainder gives a product rule | Bounded quotients yield a quotient-valued derivation for the explicit Lipschitz algebra/module construction. Identification with ordinary pointwise limits needs convergence; the product limit is then derived. | Quotient-valued proof in review; `Diff.tendsto_delta_mul`, `leibniz_of_tendsto_delta` |
| Polynomial derivations determined by X | Correct for a commutative semiring and R-linear derivations, not arbitrary additive maps. | `Derivations.derivation_ext_X`, `polynomialDerivationEquiv` |
| Inverse is multiplication by the formal derivative | Proved explicitly; D(X)=1 gives the usual formal derivative. | `polynomialDerivationEquiv_symm_apply`, `derivation_eq_derivative_of_X_eq_one` |
| Vanishing-defect packaging is an equivalence | Needs a comparison pseudometric or other proved equivalence laws. Nonnegativity alone is insufficient. | `Closure.vanishingDistSetoid`; three-point counterexample in review |
| Micro-operators descend | Requires a compatibility estimate. Uniform Lipschitz control is sufficient; differences do not descend from uniform-value equivalence alone. | `Closure.stage_operator_respects_vanishing_dist`; oscillatory witness in review |
| Packaging yields a real limit/completion | Requires Cauchy/convergence and completeness hypotheses. A quotient of arbitrary sequences does not supply these. | Corrected analytic contract in review |
| Stability-only stencil outcome | 913/1000 random candidates fit template order 0 in this run. | `math_review/stencil_baseline_run.json` |
| Original Leibniz stencil outcome | Circular fit gate removed; 50/503 survivors still fit order 1. All 503 candidates already fit order 1; the matched stability ablation also retains those 50. | `math_review/stencil_leibniz_run.json` |
| Leibniz gate discriminates derivatives | Restored in a matched, fixed population: stability retains orders 0/1/2 with counts 100/100/81; adding Leibniz retains 0/100/0. Fit classification is not a gate. | `math_review/stencil_matched_controls.json` |
| No stencil false positives | Only a sampled negative result: 20000 tested, 6 pass, none exceed the declared poor-fit threshold. Two-stage threshold relaxation is recorded. | `math_review/stencil_false_positives.json` |
| Coordinate route mismatch decays | Reproduced on the declared test function and grids; p=1.4638055. Identity-map control is zero; both routes also approach the analytic derivative. Not a curvature or time-direction theorem. | `math_review/holonomy_run.json` |
| Integration routes converge | Relative route mismatch order about 1; raw FT trapezoid defect order about 1/2. Truth errors and weighted norms independently decrease. | `math_review/integration_run.json`; telescoping identities in review |
| Left FT / split additivity power laws | Removed: these residuals are roundoff around exact discrete identities. | Null fit status in integration artifacts; polynomial tests |
| Smoothed prime closures agree for Re(s)>1 | Finite trends reproduce; uniform-on-compact convergence justified by absolute domination. Working-precision smoothing repaired. | `math_review/prime_run.json`; analytic argument in review |
| Critical-strip mismatch growth | Reproduced for the declared finite grid and naive protocols, not an analytic continuation or zero-location result. | `math_review/prime_run.json`; 50/80-digit comparison in `verification.json` |
| Symmetry specifies the unit circle | Reciprocal symmetry alone has fixed points ±1. For real palindromic coefficients, the combined anti-involution z↦1/conjugate(z) has fixed set the circle. | Corrected symmetry statement and counterexample in review |
| Positivity toy confinement | Sign tightening of interactions, not coefficient positivity. Component root calculation repairs repeated-root instability: endpoint mean deviation about 1.6e-15; independent 80-digit enumeration agrees. | `math_review/passivity_run.json`, `verification.json`; two-spin exact argument |
| Linear route / idempotence bounds | Proved for continuous linear maps. The background's arbitrary-map factorization is false. | `Closure.route_gain_bound`, `idempotence_factorization`, `idempotence_defect_bound` |
| Background No-Zeno / ECT | Conditional inequalities survive, with fresh-start alignment and control of the full capacity Λ(j)B(j); optimal zero capacities require care. Atom merging does not preserve a uniform atom bound automatically. | Background audit in review; no use as an unconditional theorem |
| Mechanization coverage | Existing anchors are direct algebraic proofs/imported mathlib equivalences; added bridges are direct proofs under explicit hypotheses. No stencil/prime/Ising experiment is claimed formalized. | `math_review/verification.json`; `lean/Main.lean` |

Recheck with `bash scripts/check_all.sh --math-only`. This runs the full review
pipeline without updating any paper source or historical paper pointer.
