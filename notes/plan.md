

---

review the response and whether the changes landed on the repo (attached zip) as expected. if  not, fold a revision request into the next ticket. proceed with drafting the repo agent ticket for:

### Task 0.3 — Python environment scaffolding

**Repo agent actions**

* Create either:

  * `requirements.txt`, or
  * `pyproject.toml` (preferred if you’re comfortable)
* Include at least: `numpy`, `scipy`, `sympy`, `mpmath`, `matplotlib`, `pandas`, `pytest`.
* Create `python/` package skeleton:

  * `python/sbt_math/__init__.py`
  * `python/sbt_math/utils.py`
* Add a minimal `pytest` sanity test.

**Pass criteria**

* `python -c "import numpy, mpmath, sympy"` works in your environment.
* `pytest -q` runs and passes.

**Repo agent response guidance**

* Return: `pytest -q` result line and list of created files (paths only).





---

review the response and whether the changes landed on the repo (attached zip) as expected. if  not, fold a revision request into the next ticket. proceed with drafting the repo agent ticket for:

## Milestone 1 — Extract and index the framework preprint (to reuse precisely)

### Task 1.1 — TeX label + environment indexer

**Repo agent actions**

* Write `scripts/extract_tex_index.py`:

  * Input: path to `six-birds-paper.tex` (or `paper.tex` if that’s the actual filename—detect automatically)
  * Output:

    * `notes/framework_index.json` containing all `\label{...}` with:

      * nearest section/subsection heading (best-effort)
      * environment type if detectable (`definition`, `theorem`, `lemma`, `remark`, `equation`, etc.)
      * line number
    * `notes/framework_index_summary.md` with counts by type and top-level section distribution.
* Run it once and commit outputs.

**Pass criteria**

* `notes/framework_index.json` exists and is nontrivial (≥ 50 labels expected).
* Summary markdown lists counts (defs/lems/thms/remarks/eqs).

**Repo agent response guidance**

* Return: counts by environment type and the detected TeX filename used.
* Provide file paths created.






---

review the response and whether the changes landed on the repo (attached zip) as expected. if  not, fold a revision request into the next ticket. proceed with drafting the repo agent ticket for:

### Task 1.2 — “Claim ledger” skeleton for validation (no prose yet)

**Repo agent actions**

* Create `notes/claim_ledger.md` skeleton with headings only:

  * “Track B: Calculus closure claims”
  * “Track B: Holonomy/geometry claims”
  * “Track C: Prime closure claims”
  * “Assumption audit checklist”
* Do not fill content beyond headings and bullet placeholders.

**Pass criteria**

* File exists with the section scaffolding.

**Repo agent response guidance**

* Return: file path only.





---

review the response and whether the changes landed on the repo (attached zip) as expected. if  not, fold a revision request into the next ticket. proceed with drafting the repo agent ticket for:

## Milestone 2 — Calculus closure: discrete → packaged laws (Python falsification first)

### Task 2.1 — Implement finite-difference operators + Leibniz defect checker

**Repo agent actions**

* Create `python/sbt_math/diffops.py` with:

  * `shift(f, h)` for arrays on a grid (periodic or clipped—choose and document)
  * `delta(f, h)` and `scaled_delta(f, h)=delta/h`
  * `leibniz_identity_residual(f, g, h)` verifying:
    [
    \delta_h(fg) - (\delta_h f),g - f,(\delta_h g) - h(\delta_h f)(\delta_h g) = 0
    ]
    in discrete array form.
* Add `pytest` tests that the residual is exactly zero (up to floating error) for random arrays.

**Pass criteria**

* `pytest -q` passes and includes this test.
* Residual norm is near machine epsilon on random inputs.

**Repo agent response guidance**

* Return: maximum residual observed across tests (a single number) and file paths created.





---

review the response and whether the changes landed on the repo (attached zip) as expected. if  not, fold a revision request into the next ticket. proceed with drafting the repo agent ticket for:

### Task 2.2 — Stencil operator population + feasibility filter (first working experiment)

**Repo agent actions**

* Create `experiments/stencil_flow/run.py` that:

  * Generates random stencil operators of width `m` (e.g., `m=2,3`)
  * Allows renormalization scaling by `h^{-k}` for candidate order `k∈{0,1,2}`
  * Evaluates operators on a fixed test family (polynomials + sin + exp) on grids with `h, h/2, h/4`
  * Computes:

    * stability metric across refinement (boundedness / consistency)
    * “approx Leibniz defect” on test pairs
    * fit-to-derivative error for each k (compare to analytic derivative on same grid)
  * Applies a feasibility gate: keep operators where defects decrease with refinement and stability holds.
* Output a small `data/runs/stencil_flow_<timestamp>.json` summary.

**Pass criteria**

* Script runs in <30 seconds.
* Output JSON includes:

  * number generated
  * number surviving by k
  * distribution of best-fit k among survivors

**Repo agent response guidance**

* Return: the summary counts (generated, survivors) and the output JSON path.
* Do not paste JSON.





---

review the response and whether the changes landed on the repo (attached zip) as expected. if  not, fold a revision request into the next ticket. proceed with drafting the repo agent ticket for:

### Task 2.3 — Counterexample hunt (“false positives”)

**Repo agent actions**

* Extend `experiments/stencil_flow/run.py` (or add `experiments/stencil_flow/hunt_false_positives.py`) to search for:

  * stencils that pass approximate Leibniz on the test family
  * but are *not* close (in least squares) to any low-order derivative operator (k=0,1,2)
* Save the top 10 false positives and their coefficients in a JSON artifact.

**Pass criteria**

* Produces either:

  * at least one nontrivial false positive, OR
  * a reasoned negative result: none found under current constraints, with search budget stats.

**Repo agent response guidance**

* Return: number of false positives found + artifact path + a short sentence describing what made them “false.”
* No coefficient dumps in chat; keep them in the artifact.




---

review the response and whether the changes landed on the repo (attached zip) as expected. if  not, fold a revision request into the next ticket. proceed with drafting the repo agent ticket for:

## Milestone 3 — Lean4: lock down “derivation uniqueness” in a tractable algebraic setting

### Task 3.1 — Lean: derivations on polynomial rings are determined by `X`

**Repo agent actions**

* Create `lean/Derivations/Polynomial.lean`.
* Goal lemma (or nearest mathlib lemma if it exists):

  * A derivation `D : Derivation R R[X]` is determined by `D X`.
  * Ideally prove/instantiate an equivalence:
    [
    \mathrm{Derivation}(R, R[X]) \simeq R[X]
    ]
    via `D ↦ D(X)` and inverse given by “multiply derivative by a polynomial”.
* If full equivalence is too hard, prove the “determined by X” lemma first.

**Pass criteria**

* `lake build` succeeds.
* File contains at least one lemma whose statement includes “`D X` determines D” (or an explicit `Equiv`).

**Repo agent response guidance**

* Return: the name(s) of the lemma(s) proved and their file path(s).
* Do not paste the Lean code.





---

review the response and whether the changes landed on the repo (attached zip) as expected. if  not, fold a revision request into the next ticket. proceed with drafting the repo agent ticket for:

### Task 3.2 — Lean: finite difference Leibniz identity (optional but high value)

**Repo agent actions**

* Create `lean/Diff/FiniteDifference.lean`:

  * Define `delta (h) (f) (x) := (f (x+h) - f x) / h` (field assumptions, `h≠0`)
  * Prove the exact discrete identity with the `h * delta f * delta g` remainder term.

**Pass criteria**

* `lake build` succeeds.
* Lemma compiles and is referenced by name.

**Repo agent response guidance**

* Return: lemma name + file path only.





---

review the response and whether the changes landed on the repo (attached zip) as expected. if  not, fold a revision request into the next ticket. proceed with drafting the repo agent ticket for:

## Milestone 4 — Holonomy/protocol mismatch: numeric diagnostics (P3) before any geometry claims

### Task 4.1 — Python: route mismatch under coordinate change

**Repo agent actions**

* Create `experiments/holonomy_rm/run.py`:

  * Choose a coordinate map `φ(x)=x+ε x^2` (ε small)
  * Define two routes for a discrete derivative approximation:

    1. refine grid then apply operator then pull back
    2. pull back then refine then apply operator
  * Measure RM(h) across h, fit scaling exponent.

**Pass criteria**

* Produces a table of RM vs h and a fitted exponent.
* Saves results to `data/runs/holonomy_rm_<timestamp>.json`.

**Repo agent response guidance**

* Return: fitted exponent and artifact path.




---

review the response and whether the changes landed on the repo (attached zip) as expected. if  not, fold a revision request into the next ticket. proceed with drafting the repo agent ticket for:

## Milestone 5 — Prime closure diagnostics (compute RM between additive/multiplicative staged closures)

### Task 5.1 — Python: truncated Dirichlet vs Euler approximants + packaging

**Repo agent actions**

* Create `experiments/prime_closure_rm/run.py` using `mpmath`:

  * Implement:

    * Dirichlet truncation `S_N(s)=∑_{n≤N} n^{-s}` (optionally smoothed)
    * Euler truncation `P_N(s)=∏_{p≤N} (1-p^{-s})^{-1}`
  * Define a “packaging” map:

    * apply a completion factor prototype (Gamma/pi factor ok)
    * enforce symmetry by `Pack(F)(s) = 0.5*(F(s)+F(1-s))`
  * Compute RM on a small compact test set K (grid in critical strip).
  * Output RM as N increases.

**Pass criteria**

* Runs without crashing.
* Outputs RM decreasing trend for at least one staging choice (even weakly) OR records that it does not decrease (useful falsification).

**Repo agent response guidance**

* Return: RM values for N list (just a small table in chat) + artifact path.





---

review the response and whether the changes landed on the repo (attached zip) as expected. if  not, fold a revision request into the next ticket. proceed with drafting the repo agent ticket for:

## Milestone 6 — “Passivity ledger” toy constraints (don’t overclaim; just test the pattern)

### Task 6.1 — Python: toy self-dual functions with positivity constraints and zero confinement

**Repo agent actions**

* Create `experiments/passivity_toy/run.py`:

  * Generate symmetric/self-dual families (e.g., `F(z)=G(z)G(-z)` or other built-in symmetry)
  * Impose a positivity/feasibility constraint (e.g., PSD constraint on a moment/Toeplitz matrix built from coefficients)
  * Numerically find zeros and test whether they lie near the symmetry axis as feasibility tightens.
* Save results and plots (optional) under `figures/` and numeric artifact under `data/runs/`.

**Pass criteria**

* Demonstrates at least one toy family where stronger positivity correlates with tighter zero confinement (even if not perfect).

**Repo agent response guidance**

* Return: one paragraph summary of what positivity constraint was used and the observed confinement metric trend + artifact paths.





---

review the response and whether the changes landed on the repo (attached zip) as expected. if  not, fold a revision request into the next ticket. proceed with drafting the repo agent ticket for:

# Project management rules for the repo agent

1. **Never paste full file contents in chat.**
2. Always return:

   * paths created/modified,
   * the single most important numeric result,
   * the command(s) executed,
   * and where artifacts were saved (`data/runs/...`, `logs/...`, `figures/...`).
3. If a task fails, stop and return:

   * error message (last ~30 lines),
   * what you tried,
   * and which step failed.



---

review the response and whether the changes landed on the repo (attached zip) as expected. if  not, fold a revision request into the next ticket. proceed with drafting the repo agent ticket for:

# Immediate next action to delegate

**Repo agent: execute Tasks 0.1 and 0.2 first** (repo skeleton + Lean project).
Return exactly:

* `tree -L 2`
* `lean --version`
* last ~20 lines of `cd lean && lake update && lake build`
* list of created file paths

Once that’s in, I’ll lock in the Lean targets (Task 3.1) and the first Python experiment target (Task 2.1) so we can start falsifying the “calculus emerges as stable closure” claim with actual numbers.
