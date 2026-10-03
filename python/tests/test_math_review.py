"""Analytic controls and regressions for the repaired mathematical diagnostics."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import mpmath as mp
import numpy as np
import pytest

from sbt_math.diffops import scaled_delta

ROOT = Path(__file__).resolve().parents[2]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


stencil = load("review_stencil", "experiments/stencil_flow/leibniz_gate.py")
matched = load("review_matched", "experiments/stencil_flow/matched_controls.py")
integral = load("review_integral", "experiments/integration_closure/run.py")
holonomy = load("review_holonomy", "experiments/holonomy_rm/run.py")
prime = load("review_prime", "experiments/prime_closure_rm/run.py")
passivity = load("review_passivity", "experiments/passivity_toy/run.py")


@pytest.mark.parametrize("h", [0, np.inf, -np.inf, np.nan])
def test_scaled_delta_requires_a_legal_step(h):
    with pytest.raises(ValueError):
        scaled_delta(np.array([1., 2.]), h)


def test_clipped_stencil_on_polynomials_and_invalid_width():
    x = np.arange(20) / 20
    out, centers = stencil.apply_stencil_clipped(x**2, np.array([1., -2., 1.]), 1)
    np.testing.assert_allclose(out / (1/20)**2, 2, atol=1e-12)
    np.testing.assert_array_equal(centers, np.arange(1, 19))
    with pytest.raises(ValueError):
        stencil.apply_stencil_clipped(x, np.ones(2), 1)


def test_impossible_moment_constraints_are_rejected():
    with pytest.raises(ValueError):
        stencil.project_high_order(np.ones(3), 1)
    c = stencil.project_high_order(np.arange(7.), 3)
    j = np.arange(-3, 4.)
    np.testing.assert_allclose(np.array([j**k @ c for k in range(4)]), [0, 1, 0, 0], atol=1e-12)


def test_fit_classification_is_not_an_acceptance_condition(monkeypatch, tmp_path):
    # Force an otherwise passing candidate to have label 0: it must survive.
    monkeypatch.setattr(stencil, "evaluate_candidate", lambda *args:
                        ({1: .1}, {1: .01}, {0: 0., 1: 1., 2: 2.}, .1, .01, .001, True))
    out = tmp_path / "run.json"
    monkeypatch.setattr(sys, "argv", ["run", "--max-tries", "1", "--target-survivors", "1",
                                      "--out", str(out), "--notes-out", str(tmp_path / "pointer.json"),
                                      "--fig-out", str(tmp_path / "fig.svg")])
    assert stencil.main() == 0
    data = json.loads(out.read_text())
    assert data["survivors_by_best_fit_k"] == {"0": 1}
    assert data["classification_used_as_gate"] is False


def test_leibniz_gate_separates_known_operators_and_rejects_zero():
    controls = {
        "identity": (np.array([0., 0., 1., 0., 0.]), 0),
        "first": (np.array([0., 0., -1., 1., 0.]), 1),
        "second": (np.array([0., 1., -2., 1., 0.]), 2),
        "zero": (np.zeros(5), 1),
    }
    results = {name: matched.evaluate(c, 2, k) for name, (c, k) in controls.items()}
    assert matched.passes_gates(results["identity"], leibniz=False)
    assert matched.passes_gates(results["second"], leibniz=False)
    assert matched.passes_gates(results["first"])
    assert not matched.passes_gates(results["identity"])
    assert not matched.passes_gates(results["second"])
    assert not matched.passes_gates(results["zero"])


def test_cumulative_protocols_exact_identities_and_quadrature_truth():
    for n in [32, 64, 128]:
        h = 1/n
        x = np.linspace(0, 1, n+1)
        f = x**2
        left = integral.left_cumulative_sum(f, h)
        trap = integral.trapezoid_cumulative_sum(f, h)
        np.testing.assert_allclose(trap-left, h/2*(f-f[0]), atol=2e-15)
        np.testing.assert_allclose(integral.scaled_forward_diff(left, h), f[:-1], atol=2e-14)
        np.testing.assert_allclose(integral.scaled_forward_diff(trap, h), (f[:-1]+f[1:])/2, atol=2e-14)
        # Quadratic trapezoid error is exactly x_i*h^2/6.
        np.testing.assert_allclose(trap-x**3/3, x*h*h/6, atol=2e-15)


def test_coordinate_routes_match_identity_and_approach_true_derivative():
    ns = [64, 128, 256, 512]
    assert max(r["rm"] for r in holonomy.compute_results(0., ns)) < 1e-13
    rows = holonomy.compute_results(.05, ns)
    for key in ["rm", "route_A_rms_error", "route_B_rms_error"]:
        assert all(b[key] < a[key] for a, b in zip(rows, rows[1:]))
    with pytest.raises(ValueError):
        holonomy.compute_results(-.5, ns)
    assert holonomy.fit_loglog(np.array([.1, .05]), np.zeros(2)) == (None, None, None)


def test_prime_truncations_against_exact_finite_formulas():
    with mp.workdps(70):
        s = mp.mpc(2, 1)
        assert abs(prime.S_N(s, 3, "none") - (1 + 2**(-s) + 3**(-s))) < mp.mpf("1e-65")
        expected = 1 / ((1-2**(-s))*(1-3**(-s)))
        assert abs(prime.P_N(s, 3, "none", [2, 3, 5]) - expected) < mp.mpf("1e-65")
        # This threshold catches the original binary-float smoothing weights.
        expected = sum(mp.exp(-mp.mpf(n)/3) * n**(-s) for n in range(1, 4))
        assert abs(prime.S_N(s, 3, "exp") - expected) < mp.mpf("1e-65")
        F = lambda z: prime.S_N(z, 10, "exp")
        assert abs(prime.apply_mode_sym(F, s, "sym") -
                   prime.apply_mode_sym(F, 1-s, "sym")) < mp.mpf("1e-65")


def test_positive_reciprocal_coefficients_do_not_force_circle_roots():
    _, mean, _, maximum = passivity.compute_roots_metrics(np.array([1., 3., 1.]))
    assert mean > .5 and maximum > 1


def test_component_factorization_preserves_polynomial_and_root_multiplicity():
    n, beta = 6, .7
    edges = passivity.build_edges_cycle(n)
    J = np.array([.2, .3, 0, .4, 0, 0])
    full, _, _, _ = passivity.compute_coeffs(n, beta, edges, J)
    factors = passivity.component_factors(n, beta, edges, J)
    reconstructed = np.array([1.])
    for a in factors:
        reconstructed = np.convolve(reconstructed, a)
    np.testing.assert_allclose(reconstructed, full, rtol=2e-14)
    roots, mean, _, maximum, residual = passivity.factored_roots_metrics(factors)
    assert len(roots) == n
    assert maximum < 1e-12 and residual < 1e-14
    # At beta=0 the graph disappears and all n roots are exactly -1.
    factors = passivity.component_factors(n, 0, edges, np.ones(n))
    roots, *_ = passivity.factored_roots_metrics(factors)
    np.testing.assert_array_equal(roots, -np.ones(n))


def test_background_repairs_have_concrete_counterexamples():
    # A nonnegative ledger with zero diagonal can still fail transitivity.
    ledger = np.array([[0, 0, 1], [0, 0, 0], [1, 0, 0]])
    assert ledger[0, 1] == ledger[1, 2] == 0 and ledger[0, 2] != 0
    # Vanishing input defect does not descend through the difference quotient.
    for n in [16, 32, 64]:
        h = 1/n
        f = lambda x: h*np.sin(x/h)
        assert abs((f(h)-f(0))/h-np.sin(1)) < 1e-15
    # Nonlinear E(x)=|x| has unit gain but violates the asserted factorization.
    E = abs
    x = -1
    assert E(E(x))-E(x) == 0 and E(E(x)-x) == 2
    # Optimal positive-work capacity is not submultiplicative: (-I)^2=I.
    u = np.array([1., 2., 3.])
    assert np.maximum(u*(-u), 0).sum() == 0
    assert np.maximum(u*u, 0).sum() > 0
    # Retention concerns final occupancy, not probability of ever leaving a block.
    switch = np.array([[0, 1], [1, 0]])
    assert (switch @ switch)[0, 0] == 1
