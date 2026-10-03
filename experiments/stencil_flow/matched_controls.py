#!/usr/bin/env python3
"""Matched stability/Leibniz comparison; fit labels never enter acceptance.

The same fixed population mixes normalized order-0/1/2 stencils. Each candidate
has a declared h^{-k} scaling, not a scaling selected by a fit on the final grid.
This is a controlled diagnostic, not an exhaustive search or a uniqueness proof.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from experiments.stencil_flow.leibniz_gate import apply_stencil_clipped, build_families, fit_error


def passes_gates(metrics: dict, leibniz: bool = True) -> bool:
    """Classification is an output only. This function accepts metric controls too."""
    stable = ((metrics["E12"] < metrics["E01"] or metrics["E12"] < 1e-8)
              and metrics["E12"] < 0.25)
    coherent = (metrics["D2"] < 0.05 and metrics["D2"] < 0.85 * metrics["D1"]
                and metrics["D1"] < 0.85 * metrics["D0"])
    return bool(metrics["nontrivial"] and stable and (coherent or not leibniz))


def evaluate(coeffs: np.ndarray, m: int, k: int, n0: int = 64) -> dict:
    families, outputs, hs = [], [], []
    pairs = [(1, 2), (3, 4), (2, 4), (0, 4)]
    defects = []
    rms = lambda a: float(np.sqrt(np.mean(a * a)))
    for n in [n0, 2 * n0, 4 * n0]:
        h = 1 / n
        hs.append(h)
        fams = build_families(np.arange(n) * h)
        families.append(fams)
        out = [apply_stencil_clipped(f.values, coeffs, m)[0] / h**k for f in fams]
        outputs.append(out)
        pair_defects = []
        for i, j in pairs:
            fg = apply_stencil_clipped(fams[i].values * fams[j].values, coeffs, m)[0] / h**k
            term1 = out[i] * fams[j].values[m:-m]
            term2 = fams[i].values[m:-m] * out[j]
            pair_defects.append(rms(fg - term1 - term2) /
                                (rms(fg) + rms(term1) + rms(term2) + 1e-12))
        defects.append(max(pair_defects))
    mismatches = []
    for level in [0, 1]:
        n = len(families[level][0].values)
        pos = 2 * np.arange(m, n - m) - m
        mismatches.append(max(rms(coarse - fine[pos]) / (rms(coarse) + 1e-8)
                              for coarse, fine in zip(outputs[level], outputs[level+1])))
    y = np.concatenate(outputs[-1])
    errors = {}
    for order in [0, 1, 2]:
        target = np.concatenate([getattr(f, ["values", "d1", "d2"][order])[m:-m]
                                 for f in families[-1]])
        errors[order] = fit_error(y, target, 1e-12)
    return {"E01": mismatches[0], "E12": mismatches[1],
            "D0": defects[0], "D1": defects[1], "D2": defects[2],
            "nontrivial": rms(y) > 1e-6,
            "best_fit_k": min(errors, key=errors.get), "fit_errors": errors}


def run(seed: int = 0, num_per_order: int = 100, m: int = 3) -> dict:
    rng = np.random.default_rng(seed)
    j = np.arange(-m, m+1, dtype=float)
    M = np.vstack([j**p for p in range(4)])
    records = []
    before, after = Counter(), Counter()
    for k in [0, 1, 2]:
        target = np.zeros(4)
        target[k] = math.factorial(k)
        for _ in range(num_per_order):
            raw = rng.standard_normal(len(j))
            coeffs = raw + M.T @ np.linalg.solve(M @ M.T, target - M @ raw)
            metrics = evaluate(coeffs, m, k)
            stable = passes_gates(metrics, leibniz=False)
            coherent = passes_gates(metrics)
            if stable:
                before[metrics["best_fit_k"]] += 1
            if coherent:
                after[metrics["best_fit_k"]] += 1
            records.append({"scale_order": k, "coeffs": coeffs.tolist(), **metrics,
                            "stability_pass": stable, "leibniz_pass": coherent})
    return {"params": {"seed": seed, "num_per_order": num_per_order, "m": m,
                        "N0": 64, "stability_floor": 1e-8,
                        "defect_norm": "relative RMS against all three Leibniz terms",
                        "D2_max": 0.05, "ratio_max": 0.85,
                        "moment_constraints": "M0..M3 = k! times the kth unit vector"},
            "generated_total": len(records), "classification_used_as_gate": False,
            "stability_only_by_best_fit_k": {str(k): before[k] for k in range(3)},
            "stability_and_leibniz_by_best_fit_k": {str(k): after[k] for k in range(3)},
            "records": records}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--num-per-order", type=int, default=100)
    parser.add_argument("--out", default="notes/math_review/stencil_matched_controls.json")
    args = parser.parse_args()
    payload = run(args.seed, args.num_per_order)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print({k: v for k, v in payload.items() if k != "records"})


if __name__ == "__main__":
    main()
