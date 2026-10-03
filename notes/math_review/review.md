# Mathematical review and repaired statements

Review date: 2026-10-03. Baseline: `9410bce`, the requested commit of all existing
changes before mathematical work. This is a self-review, including a separate
adversarial pass, not an independent review. No external agent was used.

## Outcome and coverage

The two principal algebraic anchors are correct at their stated strength: the
finite-difference product identity over a field and the linear equivalence for
derivations of a polynomial ring over a commutative semiring. No downgrade of
these results or the mathematics-instantiation title is needed. The surrounding
closure narrative needs explicit hypotheses and the stencil evidence needed a
noncircular experiment. These repairs are supplied below and in Lean/Python.

The review covered every current math-instantiation section, its abstract, both
Lean source modules and their imported mathlib derivation implementation, all
seven original experiment entry points, the finite-difference library and tests,
the stored numerical pointers, the exporter, and the bundled framework's
mathematical statements and proofs (36 theorem/lemma/corollary environments,
plus the relevant definitions, examples, and toolkit remarks). Archived v1 is
historical; its shared mathematical claims are covered by the current-section
review. The bundled framework is an imported manuscript, not this repository's
original formal development; its `formal/` and Markov-harness pointers refer to
its companion repository, not to local mechanization. No claim of a fresh build
of those external artifacts is made here.

The mathematical authority for the repaired code is the proof statements here,
the current Lean declarations, and `verification.json`. Original paper sources,
generated TeX, canonical figures, and historical `notes/*_last_run.json` files
are intentionally preserved. They still describe the historical run and must
receive the editorial corrections listed below in the later paper phase.

## 1. Algebraic and analytic calculus

### Exact finite differences

For a field F, h≠0, and arbitrary f,g:F→F, put
δ_h f(x)=(f(x+h)−f(x))/h. Expand

    f(x+h)g(x+h)−f(x)g(x)
      = (f(x+h)−f(x))g(x) + f(x)(g(x+h)−g(x))
        + (f(x+h)−f(x))(g(x+h)−g(x)).

Dividing by h gives exactly the paper's identity. This is an algebraic statement,
not an asymptotic argument or a characteristic-zero theorem. The Lean field
hypothesis and nonzero-step hypothesis match it. `delta_add`, `delta_const_mul`,
and `delta_const` additionally establish linearity and constant annihilation.
The Python periodic-array version has the same product identity because its
shift preserves pointwise multiplication; boundary wrap changes the sampled
function, not this algebraic identity. The clipped experiments use interior
samples and do not inherit a periodic-boundary convergence claim.

### A correct product-limit bridge

Let l be a filter, h_i→0, and h_i≠0 eventually. Suppose, at a fixed x,
δ_{h_i}f(x)→a and δ_{h_i}g(x)→b. Then the identity implies

    δ_{h_i}(fg)(x) → a g(x) + f(x)b,

because h_i δ_{h_i}f(x) δ_{h_i}g(x)→0 by continuity of multiplication.
Importantly, convergence of the product quotient is **derived**, not assumed.
This is `Diff.tendsto_delta_mul`. If l is nontrivial and a supplied product limit
is c, uniqueness of limits gives c=a g(x)+f(x)b; this is
`Diff.leibniz_of_tendsto_delta`. The nontrivial-filter hypothesis is required for
that equality: the bottom filter has every value as a limit.

Pointwise limits of the finite-difference addition/scalar identities give
linearity of D on any function algebra for which these limits exist. Product
closure follows from the new product-limit theorem. The codomain can be a
module of functions containing the outputs; it need not be the same regularity
class as the inputs. For example, differentiation of C¹ functions takes values
in C⁰, whereas polynomials are closed under formal differentiation.

Boundedness of the two quotients is enough to make the remainder small, but does
not construct their limits. An explicit counterexample is

    f(0)=0; f(x)=x sin(log|x|) for x≠0.

At x=0, δ_h f(0)=sin(log|h|) is bounded but has no limit as h→0. With g=f the
remainder h sin²(log|h|) vanishes, yet Df(0) does not exist. Accordingly, no theorem
in the repaired development infers derivative existence from a shrinking ledger
alone. A limit along a sampled sequence also does not establish a derivative
along every step size. The filter and the mode of convergence must be stated.

The stronger **quotient-valued** interpretation can be preserved without
constructing a real limit. Let A be the real algebra of bounded Lipschitz
functions on ℝ and B the algebra of bounded functions with the uniform norm.
Let Q=ℓ∞(ℕ;B)/c₀(ℕ;B), and embed each f∈A as a constant sequence in Q. For
h_n≠0 tending to zero, set D(f)=[(δ_{h_n}f)]. The family is bounded since
‖δ_{h_n}f‖∞≤Lip(f). Linearity and constant annihilation follow from their exact
finite identities. Moreover

    ‖h_n δ_{h_n}f δ_{h_n}g‖∞ ≤ |h_n| Lip(f) Lip(g) → 0.

Thus the remainder lies in the ideal c₀ and D(fg)=D(f)g+fD(g) **in Q**.
This gives an actual real derivation A→Q, with Q regarded as an A-module.
It does not require the quotients to converge and does not pretend Q is ℝ or
an algebra of classical derivatives. The construction is on fixed functions
of A; it does not assert descent under equivalence of arbitrary varying C⁰
input families. This direct mathematical construction preserves the packaged
derivation motif under the bounded-ledger hypothesis. The additional Lean
limit bridge handles the separate identification with ordinary pointwise limits.

### Polynomial derivations

For a commutative semiring R, an R-derivation of R[X] is R-linear and satisfies
the product rule. It kills scalar coefficients. Iterating the product rule on
Xⁿ gives D(Xⁿ)=nXⁿ⁻¹D(X), so by R-linearity

    D(q)=q′ D(X).

This requires neither division nor characteristic zero. Evaluation at X is
therefore an R-linear equivalence with R[X], with inverse p↦(q↦p q′).
The existing implementation imports mathlib's actual proved equivalence; it
does not assume an arbitrary derivation is already this formula.
`polynomialDerivationEquiv_symm_apply` now exposes the inverse on every polynomial,
and `derivation_eq_derivative_of_X_eq_one` proves the normalized consequence.

This is rigidity of an algebraic family, not finite-dimensionality over R:
R[X] itself need not be finite-dimensional. Nor does it classify arbitrary
operators on all real functions. The reviewed Lean types preserve those boundaries.

## 2. Packaging and descent

### Equivalence requires more than a nonnegative diagnostic

The working relation “defect tends to zero” is not automatically an equivalence
for an arbitrary nonnegative defect. On three points a,b,c, take constant
stage-independent defects d(a,b)=d(b,c)=0 and d(a,c)=1, with symmetry and zero
diagonal. The induced relation fails transitivity.

A sufficient repair is a shared comparison pseudometric d. For sequences a_n,b_n
define a∼b iff d(a_n,b_n)→0. Reflexivity and symmetry follow from the pseudometric
laws. For transitivity use

    0 ≤ d(a_n,c_n) ≤ d(a_n,b_n)+d(b_n,c_n) → 0.

This complete argument is mechanized in `Closure.vanishingDistSetoid`. More
general stage-dependent comparison spaces are possible, but need the same
uniform triangle/compatibility control; they are not supplied just by naming a
ledger. Multiple defect coordinates can be handled with a proved joint metric
or a conjunction of proved equivalence relations.

### Quotient, completion, and operator descent are different obligations

A quotient of arbitrary sequences is not a construction of a real limit.
For a Cauchy completion, restrict to Cauchy sequences and prove completeness of
the resulting metric space. If the target is an existing complete space, actual
convergence must be constructed there. For example, bounded oscillating scalar
sequences survive in ℓ∞/c₀ but need not represent a real limit.

Similarly, a quotient of unbounded scalar sequences does not automatically
inherit multiplication. The sequences n and n+1/n differ by o(1), but their
squares differ by 2+1/n². Restriction to uniformly bounded families repairs this
algebraic descent: |ab−a′b′|≤|a||b−b′|+|b′||a−a′|.

For an operator family F_n:X→Y, a uniform estimate

    d_Y(F_n(x),F_n(y)) ≤ K d_X(x,y),   K independent of n,

proves that equivalent inputs give equivalent outputs. This is
`Closure.stage_operator_respects_vanishing_dist`, followed by the usual quotient
lift. It is a sufficient criterion, not a universal theorem about the paper's
unspecified operator family.

Difference quotients do **not** satisfy this estimate on a C⁰ value quotient.
Take h_n=1/n and f_n(x)=h_n sin(x/h_n), g_n=0. Then
‖f_n−g_n‖∞≤h_n→0, while δ_{h_n}f_n(0)=sin(1)≠0. The difference operator's C⁰
Lipschitz constant is of order 1/h_n, so the formal descent obligation fails.
A useful repair is a richer input norm: on C¹, the fundamental theorem of
calculus gives ‖δ_h(f−g)‖∞≤‖f′−g′‖∞ on an interior domain. Thus C¹ equivalence
descends to C⁰ output equivalence. Convergence of δ_h f→f′ is separately ensured
by uniform continuity of f′ on the relevant compact neighborhood. For an
endomorphism of a function algebra use a derivative-closed domain such as
polynomials or smooth functions with appropriate derivative seminorms.

### Framework interpretation

For a genuine equivalence relation, saturation A↦Π⁻¹(Π(A)) is extensive, monotone,
and idempotent. Π itself has type P→P/∼ and is not an endomap to which an
idempotence equation applies. Partition refinement makes this saturation weaker,
whereas stronger order-closure operators have fewer fixed points; these are
different ordered constructions and should not be conflated.

Refinement orders can induce information monotones. They do not automatically
make arbitrary approximation errors monotone: the shrinking-error requirement
in this instantiation is an independently tested gate. The main dictionary is
an adopted vocabulary with supplied carrier, lens, completion, and audit data.
It does not derive those data from the six labels. In particular, the bundled
framework's bounded-interface assumption and compatibility slots are not
automatically verified by these numerical experiments.

## 3. Stencils: repaired evidence rather than an encoded conclusion

### Identified circularity and repair

The original `leibniz_gate.py` admitted a candidate only if its fitted order was 1.
Thus “all survivors are order 1” could not test that outcome. The fit predicate
has been removed. Fit labels are now recorded after acceptance, including the
possibility of labels 0 or 2. A regression forces a passing candidate's label to
0 and verifies that it survives. The baseline `run.py` also contained a hidden
Leibniz gate for fitted-order-1 candidates despite being described as
stability-only; that gate has been removed.

The corrected default legacy run still yields 50 order-1 survivors after testing
503 candidates. However, all 503 candidates fit order 1 before either gate, and
the same-population stability-only ablation retains the same 50. Enforcing
M₀=0,M₁=1,M₂=M₃=0 already constructs first-derivative consistency. Taylor's theorem
for a fixed stencil and a C⁴ function gives

    h⁻¹ Σ_j c_j f(x+jh) = f′(x) + O(h³),

with explicit remainder bound h³‖f⁽⁴⁾‖∞ Σ_j|c_j||j|⁴/24. This bound depends on
the stencil coefficients. The legacy comparison therefore cannot establish
that adding the Leibniz gate caused a change of order inside that normalized
class, even after the circular fit gate is removed.

### A matched population that actually distinguishes the mathematical factors

`matched_controls.py` uses a fixed population of 100 candidates in each of three
declared scale orders k=0,1,2. The same candidate is evaluated before and after
adding the Leibniz gate. Four moments are projected to k! times the kth unit
vector. The factor h⁻ᵏ is declared at generation; a fit label never chooses the
candidate's acceptance or scaling. Smooth-function outputs are compared on
aligned interior centers. The normalization of the Leibniz residual uses the
RMS norms of all three terms, avoiding pointwise division at stationary points.

| Fit order | Stability only | Stability and Leibniz |
| --- | ---: | ---: |
| 0 | 100 | 0 |
| 1 | 100 | 100 |
| 2 | 81 | 0 |

These are the frozen seed-0 finite results, not a statement about every stencil.
The mechanism is independent of fit labels: identity multiplication has product
defect −fg; first differentiation has zero limiting defect; second
differentiation has defect 2f′g′. Explicit identity, first-difference,
second-difference, and zero controls exercise the actual gate. The zero operator
is excluded by the nontriviality requirement; exact zero stability mismatch is
accepted rather than rejected for failing strict decrease.

Moment projection with m=1 previously silently returned unconstrained coefficients
when four independent moment conditions could not be solved: j³=j on {−1,0,1}
makes M₁=1,M₃=0 impossible. It now rejects that case. Clipped-stencil widths and
coefficient counts are validated, and a failed moment sampler raises instead
of returning an invalid purported witness.

The final-grid least-squares fit is only a shape diagnostic. Since it permits an
overall scalar, multiplying an output by h⁻ᵏ at that one grid cannot determine
its refinement normalization. This is why the matched experiment declares k
and checks refinement separately.

The original false-positive hunt was rerun at its full budget: 20000 candidates,
10000 in each sampling mode. Six pass the relaxed gate; none has minF>0.35.
Its threshold relaxation from (0.10,0.75) to (0.20,0.85) is disclosed in the
artifact. This is a reproducible sampled negative result, not exhaustive
classification or proof of uniqueness. A three-grid stability gate likewise
does not prove bounded operator norms on an entire function space.

## 4. Coordinate and integration protocols

### Coordinate mismatch

Both routes in `holonomy_rm/run.py` estimate g′(φ(x)), after the second route
divides its x-coordinate derivative by φ′. They are not compared with different
units or at different centers. The map φ(x)=x+εx² is valid on [0,1] when ε>−1/2,
which is now enforced. The target grid now covers the full image so interpolation
cannot silently clamp its tail. Tests verify the identity-map null and actual
convergence of both routes to the analytic g′.

The default finite-grid mismatch fit is p=1.4638055029, R²=0.9878080057; all
recorded mismatches decrease. Smoothness and piecewise-linear interpolation give
a first-order error bound away from the boundary, but this four-point fitted
exponent is not a universal asymptotic convergence order. The identity-map null
calibrates alignment; it does not by itself prove that all effects of nonlinear
interpolation have been eliminated. Route dependence is precisely the diagnostic
being measured. No curvature or time-direction theorem follows.
The zero-mismatch case no longer receives a fabricated power law by adding a
small constant before taking logarithms; its fit is explicitly unavailable.

### Integration identities and true convergence

With x_i=ih on [0,1], the left and trapezoid cumulative rules satisfy exactly

    δ_h I_h(f)(x_i)=f_i,
    δ_h T_h(f)(x_i)=(f_i+f_{i+1})/2,
    T_h(f)(x_i)−I_h(f)(x_i)=h(f_i−f_0)/2.

Split additivity is also exact. Their tiny floating residuals measure roundoff,
not a nonzero analytical error. The old fitted slope for the left FT residual
has been removed and replaced with an explicit algebraic-zero status.

For f∈C¹ with ‖f′‖∞≤M, the trapezoid FT pointwise defect is at most Mh/2. Its
unweighted discrete ℓ² norm is O(√N h)=O(h¹ᐟ²). A norm weighted by √h is O(h).
For a fixed nonzero antiderivative, the *relative* route mismatch is O(h), because
the grid-size factor cancels between numerator and denominator. The paper's
normalization must be understood this way; the raw-ℓ² explanation does not
change the relative mismatch order.

Left quadrature has uniform O(h) error for C¹ functions. Trapezoid quadrature
has O(h²) error for C² functions. Direct comparison against exact antiderivatives
has now been added: mere agreement of two cumulative routes would not suffice
to establish that either computes the intended integral. At N=1024 the maximal
weighted truth errors are 4.2543831e-4 (left) and 6.1156780e-7 (trapezoid), both
decreasing. The route and raw trapezoid FT fits are respectively 1.00009099 and
0.49995451. Quadratic tests verify the exact trapezoid error x_i h²/6.

## 5. Prime protocols

The code's additive and logarithmic Euler smoothings match the current displayed
definitions: the Euler weights act on logarithms, not on individual integer
terms. For σ≥σ₀>1 on a compact set, |n⁻ˢ|≤n⁻σ₀ is summable; the weights lie in
[0,1] and tend to 1 at each fixed n. Dominated convergence gives uniform
convergence of the smoothed Dirichlet truncations on that compact set.

For primes, |p⁻ˢ|≤p⁻σ₀<1, so the principal logarithm has its power-series value,
and

    |−log(1−p⁻ˢ)| ≤ p⁻σ₀/(1−2⁻σ₀).

This summable bound proves uniform convergence of the weighted log sums.
Exponentiation is continuous on the bounded limiting range, giving the usual
Euler product. The common limiting object is the classical ζ in Re(s)>1.
Multiplication by the analytic completion factor preserves convergence on
compact sets avoiding its singularities. This is a genuine analytical
justification of the control regime, beyond the finite trend.

The code previously formed −n/N and −p/N as binary floats before handing them to
mpmath, limiting the smoothing weights' input accuracy despite the 50-digit
working precision. Ratios and exponentials now use mpmath throughout. The test
against an exact finite formula at 70 digits detects the old error. Results are
still deliberately stored as binary64 diagnostic summaries; that storage is
not a 50-digit numerical certificate.

The full default grid was independently rerun at 80 digits. Every reported
RM₂, RM∞, ErrS₂, and ErrP₂ value agrees with the 50-digit output at binary64
precision. At N=800, convergence-region RM₂ is 0.05239908160 and critical-strip
RM₂ is 5.008084386e12. The decreasing/increasing trends of all three principal
metrics reproduce on the five stated cutoffs.

No analytic continuation or statement about ζ zeros is derived. The strip run
uses a symmetrized mode while the control uses one-sided completion, as disclosed
in the paper. Thus the experiment compares staging/packaging pairs, not a
single isolated variable. In particular, evaluations at real s∈(0,1) supply an
ordinary source of divergence: the smoothed additive sums grow like N¹⁻ˢ, and
the logarithmic Euler sums grow because the weighted prime inverse-power sums
diverge. Applying a completion prototype or symmetry projection does not cure
invalid truncation formulas. The measured finite mismatch is not a theorem of
blow-up at every point of the strip or a condition on the zero set.

## 6. Ising positivity toy

The enumerated polynomial is exactly

    Z(z)=Σ_{σ∈{−1,1}ⁿ} exp(βΣ_e J_e σ_iσ_j) z^{# down spins}.

Global spin reversal leaves the interaction energy unchanged and exchanges k
with n−k. Hence a_k=a_{n−k} already holds mathematically; numerical
palindromization removes summation asymmetry rather than supplying a missing
physical symmetry. All coefficients are positive for **either sign** of J.
Coefficient positivity alone cannot confine roots: 1+3z+z² has two reciprocal
real roots off the circle.

The fixed points of z↦1/z are ±1. With real coefficients, conjugation is also a
root-set symmetry, so the combined anti-involution z↦1/conjugate(z) preserves
the roots and has fixed set |z|=1. This is the correct symmetry-locus statement.
Neither of these symmetries forces every root to lie on that locus.

The feasibility variable changes interactions:
J_e(λ)=max(J_e,0)+λ min(J_e,0). It is not an independently verified frequency-
domain passivity condition. Its exact endpoint has nonnegative effective
couplings βJ_e when β≥0. The classical Lee–Yang theorem applies to this finite
Ising polynomial at that endpoint, including disconnected components and zero
edges; this is an imported theorem, not a novel numerical proof.
See the [original Lee–Yang paper](https://journals.aps.org/pr/abstract/10.1103/PhysRev.87.410)
and the finite/nonuniform-coupling statement on page 2 of
[Matveev–Shrock, arXiv:cond-mat/9512149v2](https://arxiv.org/pdf/cond-mat/9512149).

A self-contained two-spin instance illustrates the same distinction. For one
edge K=βJ the polynomial, up to a positive scalar, is

    z² + 2e⁻²ᴷ z + 1.

If K≥0, its middle coefficient is in (0,2] and the conjugate reciprocal roots
have modulus 1. If K<0, the middle coefficient exceeds 2, and the two negative
real reciprocal roots lie strictly inside/outside the circle. Removing the
negative interaction moves that coefficient toward 2 and the roots toward −1.
This exact small instance supplies the claimed “can confine” motif; a universal
monotonicity theorem for arbitrary clipped graph families is not asserted.

### Numerical repair

At λ=0 in the default cycle the nonzero-interaction components have degrees
3,3,4,1,1. Disconnected partition sums multiply, so an isolated spin contributes
exactly 1+z and the two isolates create a repeated root −1. Full-degree NumPy
root finding split that repeated root numerically, producing the historical
mean deviation 3.0292e-4 and max deviation 9.0919e-4. A tiny backward polynomial
residual alone does not control the forward location of a repeated root.

The code now solves each component polynomial separately, preserving every root
with multiplicity. Edges are removed only at exactly zero coupling; no tolerance
silently changes the model. At β=0 all interactions disappear as well. The
factor product is checked against full enumeration, and root residuals are
recorded with their correct interpretation as backward errors.

The corrected default endpoint has mean radial deviation 1.5543122e-15 and max
5.9952043e-15. Independent scalar enumeration and root finding at 80 digits,
using a separate connected-components implementation, confirms the endpoint
and the λ=1 roots. The largest matching difference is 4.86e-12 at λ=1 and
6.00e-15 at λ=0. The high-precision control is not an interval root certificate;
the exact endpoint theorem is justified by the hypotheses above. All six
default mean deviations still decrease, from about 0.87169354 to roundoff.

## 7. Bundled framework audit

The following inventory accounts for all 36 proof environments. Line numbers
refer to the unchanged `six-birds-paper.tex` in checkpoint `9410bce`.

| Lines | Statements | Assessment |
| --- | --- | --- |
| 382,397,410 | Fixed points antitone; one-step iterate stabilization; saturation | Valid using extensiveness, pointwise comparison, antisymmetry, and idempotence. |
| 482 | Idempotents split | Valid; image is fixed-point subtype. |
| 600 | Retention implies prototype stability and small idempotence defect | Valid on a nonempty finite probability carrier with normalized prototypes. The lift with disjoint fibers is even a TV isometry, so prototype stability equals retention error. |
| 658 | Refinement can reveal or destroy stable prototypes | Existential claim valid; supplied sketch confuses first exit and final occupancy. Exact replacements below. |
| 775,790,816 | Exact forms have zero cycles; cycle criterion; null detailed balance | Valid on bidirected support. Tree-potential construction works per component; π∝exp(Φ) has the displayed correct sign. |
| 895,916 | Path reversal DPI and no false positives | Valid for path measures; coordinatewise observation commutes with reversal. Markovity of the observed process and stationarity are not needed for DPI. |
| 946,973 | Protocol trap; no steady-state arrow without affinity | Reversibility proof valid for the stated common stationary measure. Do not extend zero asymmetry to nonstationary initial laws or treat two-state phase bias as a cycle affinity. |
| 1026,1046,1060,1081 | Definable counts; finite forcing; block splitting; strict extension | Valid with the source's explicit convention X=f(Z), nonempty blocks, and independent fair bits. No logical/set-theoretic independence conclusion. |
| 1129 | Self-generated primitives | Conditional naming/construction theorem. Bounded-interface and compatibility slots are actual assumptions. Π is not itself idempotent and the exact quotient-descent square has zero mismatch. |
| 1294,1313 | Edge deletion shrinks cycle rank; rewrites change rank/gap | Valid. A deletion changes |E| by −1 and component count by 0 or 1. Two-state lazy kernels with transition probabilities a∈(0,1/2] have gaps 2a, giving exact gap-increase/decrease witnesses. |
| 1696,1733,1762 | WORK from storage; latency; No-Zeno | Valid with positive θ, monotone running supremum/right continuity, local integrability, ALIGN, ICAP, and FEAS. The reciprocal series concerns Λ(j)B(j). |
| 1922 | Route mismatch bounds gain | Valid for bounded linear operators and absolute operator-norm RM, not the relative diagnostic RM of the instantiation without rescaling. Now also anchored in `Closure.route_gain_bound`. |
| 2022,2033 | Causal composition; parallel storage/ICAP sum | Valid. Positive-part inequality avoids signed cancellation. Passivity of a serial composition is not automatic. |
| 2079,2261 | ECT summary; mechanical mode-count capacity | Linear upper bound valid for a single decomposition satisfying both mode and uniform atom bounds. Zero best capacities and the feasibility budget need the corrections below for DIV/No-Zeno language. |
| 2181,2205,2236 | Balanced kernel mass; finite-memory ICAP; balanced atom corollary | Valid via norm submultiplicativity, exponential integration, Young and Cauchy–Schwarz for truncated inputs. No uncontrolled prehistory is hidden. |
| 2331,2354 | Feasible coercivity; depth-scaled coercivity | Correct conditional implications. The first is a restatement of a supplied positive domination, not a proof of that domination from kernel equality alone. |
| 2405,2434,2444 | Sector merge/count; quantized count; mode bound | Count inequalities valid when the decomposition exists, zero atoms may be discarded, and the index map is injective. A per-atom ICAP bound does not survive merging for free. |

Additional corrections to definitions, examples, and toolkit claims:

1. **Retention versus first exit (658–698).** For the two-state symmetric kernel
   P=[[1−p,p],[p,1−p]], final cross-block probability after τ steps is
   (1−(1−2p)^τ)/2, not 1−(1−p)^τ. At p=1,τ=2 it is zero although a first exit is
   certain. Exact witnesses preserving the theorem: take τ=1,ε=1/4, uniform
   coarse prototype (one stable object), and singleton fine prototypes. At
   p=1/10 both fine prototypes are stable (count 2); at p=1/2 neither is stable
   (count 0). These replace the sketch without weakening the existential claim.

2. **Two phases cannot have a stationary cycle drive (example around 1400).**
   A two-state chain with jump probabilities a,b>0 has stationary weights
   b/(a+b),a/(a+b), and detailed balance holds identically. Unequal jump rates
   therefore do not create stationary phase affinity. Use three phases with
   clockwise/counterclockwise probabilities p≠q>0 and a positive random-scan
   phase probability α. Then the phase cycle affinity is 3 log(p/q), and the
   stationary phase contribution to entropy production is
   α(p−q)log(p/q)>0. This repairs the example while preserving the conditional
   protocol theorem. For row-vector updates, applying K₀ then K₁ gives K₀K₁;
   the displayed rounded kernels also need exact fractions or stochastic
   renormalization to have exact row sums. Noncommutativity itself is unaffected.

3. **Full effective capacity (2079–2113).** A linear bridge ICAP bound Λ_j≤C(j+1)
   yields a No-Zeno latency bound only with appropriate control of B_j.
   For example B_j≤B gives Δt_j≥θ/[CB(j+1)], whose sum diverges. More generally
   require Σ_j 1/(Λ_jB_j)=∞, exactly as the main No-Zeno theorem states. If
   Λ_j=j+1 and B_j=2^j, the sum of reciprocal bridge capacities diverges but the
   effective reciprocal sum converges. This gap is not repaired by naming FEAS.

4. **Realizable Zeno witness (Appendix D).** The numerical work assignments in
   the sketch can be implemented: take the memoryless scalar bridge
   Z_j[u]=Λ_j u with storage derivative S′_j=Λ_j u², fresh initial storage, input
   of squared amplitude B_j, and crossing duration θ/(Λ_jB_j). It is passive,
   satisfies ICAP for every truncated input, and achieves WORK and FEAS with
   equality. Thus the exponential effective-capacity example is a genuine
   admissible model, not merely a formal list of scalar costs.

5. **Best capacity may be zero (2166 onward).** The infimum over positive ICAP
   constants can be zero; the zero bridge is an example. Division by that best
   constant in an ordinary real expression is then undefined. Use the explicit
   positive upper constants m_jΛ₀ (or max(1,m_j)Λ₀), or prove positive capacity
   on every actually crossed boundary before taking reciprocals. A positive
   WORK crossing with finite input energy forces positive capacity. Infimum
   passage to the optimal inequality is justified by approaching constants and
   taking the limit for each fixed input/window, not by assuming attainment.

6. **Merging loses uniform atom bounds.** In one sector, k copies of the identity
   each have ICAP constant 1. Merging produces k·Id, whose constant is k. Thus
   the sector-count bound and per-atom bound must hold for the **same returned
   decomposition**. The ECT theorem is valid when both slots are supplied; the
   sector-minimal count alone cannot supply uniform post-merge capacity.

7. **Coercivity domain (2313–2377).** For a bounded positive self-adjoint G,
   Ran(G) intersects ker(G) only at zero, so the full-horizon quadratic energy
   defines a norm on feasible L² signals. A proper-window energy is a seminorm
   on full-horizon signals (a feasible signal can vanish on that window); call
   it a norm only after restricting/quotienting to the window. Equality of the
   lossless kernel and ker(G) does not itself establish the supplied domination
   inequality. No uniform positive lower spectral bound follows merely from
   excluding the kernel in infinite dimension.

8. **Operator toolkit (last section).** The composition perturbation and
   idempotence factorization require linear maps, or explicit Lipschitz and
   affine corrections for more general maps. The unit-gain nonlinear map
   E(x)=|x| gives E²−E=0 but E(E−Id)(−1)=2, refuting the arbitrary-map
   factorization. The repaired linear factorization and norm bound are now
   Lean theorems. Gain submultiplicativity is valid for linear maps; the
   *optimal positive-work ICAP capacities* need not be submultiplicative:
   −Id has best positive-work capacity 0, while (−Id)²=Id has capacity 1.
   Chosen operator-norm upper constants can be multiplied; the optimal
   capacity cannot be substituted without an additional result.

9. **Zero/small route defect does not control all depth growth.** The exact
   two-step inequality remains valid, but even zero route mismatch permits
   gains 2^{k−j} when each one-step gain is 2. Long-depth growth control needs
   bounds on the baseline gain products and on propagated residuals. Neither
   summability of a local mismatch nor its relative normalization supplies
   those bounds by itself.

10. **Extended KL audit subtraction.** If an audit can be +∞, max(0,A_coarse−A_fine)
    is not defined when both are +∞ in ordinary extended-real arithmetic.
    Restrict subtraction-based defect diagnostics to finite audits or use an
    order/inequality-based formulation. The finite/infinite DPI itself remains
    valid. Probability maxima also require a nonempty carrier; the counting
    statements on empty sets are still well-defined but the empirical
    probability-prototype maxima are not.

None of these background repairs is used to assert a new unconditional
No-Zeno or analytic theorem in the mathematics instantiation. They identify the
actual premises at the framework boundary and prevent importing a stronger
interpretation than the supplied mathematics supports.

## 8. Mechanization, numerical evidence, and editorial handoff

`lean-toolchain` pins the original toolchain label v4.9.1; the upstream release
prints Lean version 4.9.0. The mathlib commit in `lake-manifest.json` remains
09d33efc68d3ad52db77b731d7253675395a14aa. The review fetched its official build
cache and performed a fresh local build of every repository module. Imports
are narrowed to their actual dependencies rather than all of mathlib.

The current exported anchors/bridges are audited with fresh `#print axioms`
output. Their only transitive axioms are `propext`, `Classical.choice`, and
`Quot.sound`; no `sorryAx`, custom analytic axiom, or unproved declaration occurs.
The audit checks that every declaration listed in `Main.lean` appears in the
fresh output, and rejects any extra axiom. Explicit hypotheses remain visible:
the limit bridge consumes factor convergence; the packaging theorem consumes a
pseudometric; descent consumes uniform operator control. Those statements do
not mechanize the numerical conjectures or prove those hypotheses in arbitrary
function spaces.

The complete reproducible review gate is

    bash scripts/check_all.sh --math-only

It runs mathematical regression tests, `lake build`, a direct current Lean
axiom print, all original experiments at their default budgets, the new matched
control, analytical-truth checks, and independent high-precision comparisons.
Logs are under `logs/math_review/`; commit-visible run/summary artifacts are
under `notes/math_review/`. Review figures are under ignored
`figures/tmp/math_review/`, and can be regenerated by that command. The original
paper pointers are never changed by it. `verification.json` records the final
results, precisions, counts, and limitations. Numerical outputs remain
diagnostics, not interval or exhaustive proofs.

Required later paper edits, deliberately not made in this task:

- State the comparison metric, the Cauchy/convergence domain, and the operator
  descent contract; use a C¹/graph comparison or a derivative-closed algebra
  when interpreting difference quotients as a well-defined packaged operation.
- Cite the actual limit bridge, including linearity, rather than infer
  convergence from boundedness alone.
- Replace the claimed causal interpretation of the original stencil comparison
  with the new matched-population evidence. Keep moment normalization and
  finite-sample/finite-grid limitations explicit.
- Correct the inversion fixed-set statement to the combined anti-involution;
  update endpoint metrics to the component result and distinguish interaction
  sign constraints from mere positive coefficients or abstract passivity.
- Suppress roundoff-only integration power laws; clarify raw versus weighted
  norms and relative route normalization. Include the antiderivative truth check.
- Retain the prime packaging-mode disclosure and diagnostic scope; do not
  present binary64 summary values as 50-digit or interval certificates.
- Apply the separately listed framework scope/example corrections if that
  imported manuscript is revised; do not silently treat its external file
  pointers as local Lean or numerical coverage.

These edits preserve the substantive algebraic results and the controlled
diagnostic findings. They make the hypotheses and experimental provenance
accurate; they do not claim that the unchanged paper is already corrected.
