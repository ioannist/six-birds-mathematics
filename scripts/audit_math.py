#!/usr/bin/env python3
"""Verify the separate review artifacts and record fresh precision controls."""
from __future__ import annotations

import importlib.util
import importlib.metadata
import hashlib
import json
from pathlib import Path
import re
import sys

import mpmath as mp
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from scipy.optimize import linear_sum_assignment

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "notes/math_review"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def read(name):
    return json.loads((REVIEW / name).read_text())


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def mp_partition(n, beta, edges, couplings):
    """Independent scalar enumeration, without NumPy's coefficient summation."""
    coeffs = [mp.mpf(0) for _ in range(n+1)]
    for bits in range(1 << n):
        spins = [1-2*((bits >> i) & 1) for i in range(n)]
        energy = sum(j*spins[i]*spins[k] for (i, k), j in zip(edges, couplings))
        coeffs[bits.bit_count()] += mp.exp(beta * energy)
    return coeffs


def passivity_precision():
    toy = load("audit_passivity", "experiments/passivity_toy/run.py")
    run = read("passivity_run.json")
    n = run["params"]["n"]
    edges = toy.build_edges_cycle(n)
    J = np.random.default_rng(run["params"]["seed"]).normal(
        0., run["params"]["J_scale"], len(edges))
    checks = []
    for lam in [1., 0.]:
        couplings = np.maximum(J, 0) + lam * np.minimum(J, 0)
        graph = np.zeros((n, n), dtype=int)
        for (i, j), coupling in zip(edges, couplings):
            if coupling != 0:
                graph[i, j] = graph[j, i] = 1
        _, labels = connected_components(csr_matrix(graph), directed=False)
        roots = []
        with mp.workdps(80):
            for label in sorted(set(labels)):
                vertices = np.flatnonzero(labels == label).tolist()
                relabel = {v: k for k, v in enumerate(vertices)}
                sub_edges, sub_couplings = [], []
                for (i, j), coupling in zip(edges, couplings):
                    if coupling != 0 and i in relabel and j in relabel:
                        sub_edges.append((relabel[i], relabel[j]))
                        sub_couplings.append(mp.mpf(float(coupling)))
                a = mp_partition(len(vertices), mp.mpf(run["params"]["beta"]),
                                 sub_edges, sub_couplings)
                rr = mp.polyroots(a[::-1], maxsteps=2000, extraprec=100)
                require(len(rr) == len(vertices), "missing component roots")
                for z in rr:
                    residual = abs(mp.polyval(a[::-1], z)) / sum(
                        abs(coef)*abs(z)**k for k, coef in enumerate(a))
                    require(residual < mp.mpf("1e-65"), "multiprecision root residual")
                roots.extend(rr)
            mean = sum(abs(abs(z)-1) for z in roots) / n
            maximum = max(abs(abs(z)-1) for z in roots)
            if lam == 0:
                require(maximum < mp.mpf("1e-60"), "ferromagnetic endpoint root accuracy")
            row = next(r for r in run["results"] if r["lambda"] == lam)
            approx = np.array([complex(*z) for z in row["roots"]])
            precise = np.array([complex(z) for z in roots])
            distances = abs(approx[:, None]-precise[None, :])
            rows, cols = linear_sum_assignment(distances)
            discrepancy = float(max(distances[rows, cols]))
            require(discrepancy < 1e-9, "component roots differ from independent enumeration")
            checks.append({"lambda": lam, "dps": 80, "mean_dev": mp.nstr(mean, 25),
                           "max_dev": mp.nstr(maximum, 25),
                           "root_match_max_distance": discrepancy})
    return checks


def prime_precision():
    prime = load("audit_prime", "experiments/prime_closure_rm/run.py")
    run = read("prime_run.json")
    params = run["params"]
    max_relative = 0.
    with mp.workdps(80):
        for region in ["conv", "strip"]:
            points = [mp.mpc(sigma, t) for sigma in params[f"sigma_{region}_list"]
                      for t in params["t_list"]]
            rows, _ = prime.eval_region(params["N_list"], points, params[f"mode_{region}"],
                                        params["smooth"], 1e-30)
            for old, new in zip(run["results"][region], rows):
                for key in ["rm2", "rminf", "errS2", "errP2"]:
                    rel = abs(new[key]-old[key]) / max(abs(new[key]), 1e-300)
                    max_relative = max(max_relative, rel)
                    require(rel < 2e-14, f"unstable prime output {region} {key}")
    return {"compared_dps": [50, 80], "all_rows_and_metrics_max_relative_difference": max_relative,
            "scope": "stability of reported binary64 diagnostics, not an interval certificate"}


def main():
    summary = {}
    sources = []
    for pattern in ["lean/*.lean", "lean/*/*.lean", "lean/lean-toolchain", "lean/lake-manifest.json",
                    "experiments/*/*.py", "python/sbt_math/*.py", "python/tests/*.py",
                    "scripts/audit_math.py", "scripts/check_math.sh", "scripts/check_all.sh"]:
        sources.extend(ROOT.glob(pattern))
    summary["provenance"] = {
        "baseline_commit": "9410bce",
        "python": sys.version,
        "packages": {name: importlib.metadata.version(name) for name in
                     ["numpy", "scipy", "sympy", "mpmath", "matplotlib", "pandas", "pytest"]},
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted(set(sources))},
    }
    pytest_log = (ROOT / "logs/math_review/pytest.log").read_text()
    passed = re.search(r"(\d+) passed", pytest_log)
    require(passed is not None and "failed" not in pytest_log, "missing successful test evidence")
    summary["tests_passed"] = int(passed.group(1))
    # Each export gets a fresh transitive axiom print, not just a text-hole scan.
    axiom_log = (ROOT / "logs/math_review/lean-axioms.log").read_text()
    printed = re.findall(r"'([^']+)' depends on axioms: \[([^\]]*)\]", axiom_log)
    expected = re.findall(r"^#print axioms (\S+)", (ROOT / "lean/Main.lean").read_text(), re.M)
    require([name for name, _ in printed] == expected, "missing current Lean export audit")
    allowed = {"propext", "Classical.choice", "Quot.sound"}
    for name, axioms in printed:
        require(set(filter(None, map(str.strip, axioms.split(',')))) <= allowed,
                f"unexpected axiom in {name}: {axioms}")
    summary["lean"] = {"audited_exports": expected, "allowed_axioms": sorted(allowed)}

    baseline = read("stencil_baseline_run.json")
    leibniz = read("stencil_leibniz_run.json")
    matched = read("stencil_matched_controls.json")
    hunt = read("stencil_false_positives.json")
    require(leibniz["classification_used_as_gate"] is False, "circular legacy gate")
    require(matched["classification_used_as_gate"] is False, "circular matched gate")
    require(matched["stability_and_leibniz_by_best_fit_k"] == {"0": 0, "1": 100, "2": 0},
            "matched stencil claim does not reproduce")
    require(all(matched["stability_only_by_best_fit_k"][str(k)] > 0 for k in range(3)),
            "missing matched non-derivation controls")
    summary["stencils"] = {"baseline_survivors": baseline["survivors_total"],
                           "legacy_survivors": leibniz["counts"]["survivors_total"],
                           "legacy_same_population_ablation": leibniz["ablation_same_candidates"],
                           "matched_stability": matched["stability_only_by_best_fit_k"],
                           "matched_leibniz": matched["stability_and_leibniz_by_best_fit_k"],
                           "false_positive_search": hunt["counts"]}

    integral = read("integration_run.json")["results"]
    rows = integral["rows"]
    for key in ["rm_max", "ft_trap_max", "integral_left_weighted_l2_error_max",
                "integral_trap_weighted_l2_error_max", "ft_trap_weighted_l2_max"]:
        require(all(b[key] < a[key] for a, b in zip(rows, rows[1:])), f"integration {key}")
    require(integral["fits"]["ft_left_max"]["slope"] is None, "spurious roundoff power law")
    summary["integration"] = {"rm_fit": integral["fits"]["rm_max"],
                              "ft_trap_fit": integral["fits"]["ft_trap_max"],
                              "finest_truth_errors": {k: v for k, v in rows[-1].items() if "error" in k}}

    holonomy = read("holonomy_run.json")
    require(max(r["rm"] for r in holonomy["null_results"]) < 1e-13, "identity map mismatch")
    for key in ["rm", "route_A_rms_error", "route_B_rms_error"]:
        require(all(b[key] < a[key] for a, b in zip(holonomy["results"], holonomy["results"][1:])),
                f"coordinate route {key}")
    summary["holonomy"] = holonomy["fit"]

    prime = read("prime_run.json")
    for key in ["rm2", "errS2", "errP2"]:
        for region, direction in [("conv", 1), ("strip", -1)]:
            rows = prime["results"][region]
            require(all(direction*(a[key]-b[key]) > 0 for a, b in zip(rows, rows[1:])),
                    f"prime trend {region} {key}")
    summary["prime"] = {"finest_conv": prime["results"]["conv"][-1],
                        "finest_strip": prime["results"]["strip"][-1],
                        "precision": prime_precision()}
    summary["passivity"] = passivity_precision()
    summary["assessment"] = "Finite diagnostic claims reproduced; conditional formal bridges checked."
    (REVIEW / "verification.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("Mathematics artifact and precision audit passed.")


if __name__ == "__main__":
    main()
