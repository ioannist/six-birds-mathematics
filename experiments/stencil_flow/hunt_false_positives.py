#!/usr/bin/env python3
"""Search for k=1 Leibniz passers that are not low-order fits."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np


@dataclass
class FunctionFamily:
    name: str
    values: np.ndarray
    d1: np.ndarray
    d2: np.ndarray


def apply_stencil_clipped(
    f: np.ndarray, coeffs: np.ndarray, m: int
) -> Tuple[np.ndarray, np.ndarray]:
    f_arr = np.asarray(f)
    if f_arr.ndim != 1:
        raise ValueError("apply_stencil_clipped expects 1D arrays")
    n = f_arr.shape[0]
    if n < 2 * m + 1:
        raise ValueError("array too short for stencil width")
    out = np.zeros(n - 2 * m, dtype=float)
    for idx, c in enumerate(coeffs):
        j = idx - m
        out += float(c) * f_arr[m + j : n - m + j]
    centers = np.arange(m, n - m, dtype=int)
    return out, centers


def build_families(x: np.ndarray) -> List[FunctionFamily]:
    two_pi = 2.0 * math.pi
    f_const = np.ones_like(x)
    f_lin = x
    f_quad = x**2
    f_sin = np.sin(two_pi * x)
    f_exp = np.exp(x)
    return [
        FunctionFamily("const", f_const, np.zeros_like(x), np.zeros_like(x)),
        FunctionFamily("lin", f_lin, np.ones_like(x), np.zeros_like(x)),
        FunctionFamily("quad", f_quad, 2.0 * x, 2.0 * np.ones_like(x)),
        FunctionFamily("sin", f_sin, two_pi * np.cos(two_pi * x), -(two_pi**2) * f_sin),
        FunctionFamily("exp", f_exp, f_exp, f_exp),
    ]


def fit_error(y: np.ndarray, t: np.ndarray, eps: float) -> float:
    denom = float(np.dot(t, t))
    if denom == 0.0:
        return float(np.linalg.norm(y))
    a = float(np.dot(y, t) / denom)
    fit = a * t
    return float(np.linalg.norm(y - fit) / (np.linalg.norm(fit) + eps))


def compute_leibniz_defect(
    coeffs: np.ndarray,
    m: int,
    h: float,
    pairs: Sequence[Tuple[FunctionFamily, FunctionFamily]],
    eps: float,
) -> float:
    worst = 0.0
    for f, g in pairs:
        fg = f.values * g.values
        l_fg, _ = apply_stencil_clipped(fg, coeffs, m)
        l_f, _ = apply_stencil_clipped(f.values, coeffs, m)
        l_g, _ = apply_stencil_clipped(g.values, coeffs, m)
        l_fg = l_fg / h
        l_f = l_f / h
        l_g = l_g / h
        f_center = f.values[m:-m]
        g_center = g.values[m:-m]
        num = np.abs(l_fg - l_f * g_center - f_center * l_g)
        denom = np.abs(l_fg) + eps
        worst = max(worst, float(np.max(num / denom)))
    return worst


def sample_unconstrained(rng: np.random.Generator, m: int) -> Tuple[np.ndarray, int]:
    coeffs = rng.standard_normal(2 * m + 1)
    return coeffs, 0


def sample_moment1(
    rng: np.random.Generator, m: int, tol: float = 1e-6
) -> Tuple[np.ndarray, int]:
    resamples = 0
    while True:
        coeffs = rng.standard_normal(2 * m + 1)
        coeffs = coeffs - np.mean(coeffs)
        idx = np.arange(-m, m + 1, dtype=float)
        m1 = float(np.dot(idx, coeffs))
        if abs(m1) < tol:
            resamples += 1
            if resamples > 1000:
                return coeffs, resamples
            continue
        coeffs = coeffs / m1
        return coeffs, resamples


def evaluate_candidate(
    coeffs: np.ndarray,
    m: int,
    families_by_res: List[List[FunctionFamily]],
    hs: List[float],
    eps: float,
) -> Dict[str, float]:
    n2 = len(families_by_res[2][0].values)
    h2 = hs[2]

    outs2_k: Dict[int, List[np.ndarray]] = {0: [], 1: [], 2: []}
    for fam in families_by_res[2]:
        out, _ = apply_stencil_clipped(fam.values, coeffs, m)
        outs2_k[0].append(out)
        outs2_k[1].append(out / h2)
        outs2_k[2].append(out / (h2**2))

    f_errors: Dict[int, float] = {}
    for k in (0, 1, 2):
        y = np.concatenate(outs2_k[k])
        t_parts = []
        for fam in families_by_res[2]:
            if k == 0:
                t = fam.values
            elif k == 1:
                t = fam.d1
            else:
                t = fam.d2
            t_parts.append(t[m:-m])
        t = np.concatenate(t_parts)
        f_errors[k] = fit_error(y, t, eps)

    nontrivial = any(np.linalg.norm(out) > 1e-6 for out in outs2_k[1])

    pairs_idx = [(1, 2), (3, 4), (2, 4)]
    pairs0 = [(families_by_res[0][i], families_by_res[0][j]) for i, j in pairs_idx]
    pairs1 = [(families_by_res[1][i], families_by_res[1][j]) for i, j in pairs_idx]
    pairs2 = [(families_by_res[2][i], families_by_res[2][j]) for i, j in pairs_idx]

    d0 = compute_leibniz_defect(coeffs, m, hs[0], pairs0, eps)
    d1 = compute_leibniz_defect(coeffs, m, hs[1], pairs1, eps)
    d2 = compute_leibniz_defect(coeffs, m, hs[2], pairs2, eps)

    return {
        "F0": float(f_errors[0]),
        "F1": float(f_errors[1]),
        "F2": float(f_errors[2]),
        "minF": float(min(f_errors.values())),
        "D0": float(d0),
        "D1": float(d1),
        "D2": float(d2),
        "nontrivial": nontrivial,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Hunt false positives")
    parser.add_argument("--m", type=int, default=3)
    parser.add_argument("--num", type=int, default=20000)
    parser.add_argument("--N0", type=int, default=64)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--mode",
        choices=["unconstrained", "moment1", "both"],
        default="both",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="notes/stencil_flow_false_positives.json",
    )
    args = parser.parse_args()

    m = args.m
    num = args.num
    n0 = args.N0
    n1 = 2 * n0
    n2 = 4 * n0
    seed = args.seed
    eps = 1e-12

    print(
        f"params: m={m}, num={num}, N0={n0}, seed={seed}, mode={args.mode}")

    rng = np.random.default_rng(seed)
    hs = [1.0 / n for n in (n0, n1, n2)]
    families_by_res = []
    for n, h in zip((n0, n1, n2), hs):
        x = np.arange(n, dtype=float) * h
        families_by_res.append(build_families(x))

    if args.mode == "both":
        num_unconstrained = num // 2
        num_moment1 = num - num_unconstrained
        modes = [("unconstrained", num_unconstrained), ("moment1", num_moment1)]
    else:
        modes = [(args.mode, num)]

    candidates: List[Dict[str, object]] = []
    tested_by_mode: Counter[str] = Counter()
    resample_count = 0

    for mode, count in modes:
        for _ in range(count):
            if mode == "unconstrained":
                coeffs, resamples = sample_unconstrained(rng, m)
            else:
                coeffs, resamples = sample_moment1(rng, m)
                resample_count += resamples
            metrics = evaluate_candidate(coeffs, m, families_by_res, hs, eps)
            tested_by_mode[mode] += 1
            candidates.append(
                {
                    "mode": mode,
                    "m": m,
                    "coeffs": [float(c) for c in coeffs],
                    "F0": metrics["F0"],
                    "F1": metrics["F1"],
                    "F2": metrics["F2"],
                    "minF": metrics["minF"],
                    "D0": metrics["D0"],
                    "D1": metrics["D1"],
                    "D2": metrics["D2"],
                    "nontrivial": metrics["nontrivial"],
                }
            )

    thresholds = {
        "D2_max": 0.10,
        "ratio": 0.75,
        "minF": 0.35,
    }

    def passes_leibniz(cand: Dict[str, object], th: Dict[str, float]) -> bool:
        if not cand["nontrivial"]:
            return False
        return (
            cand["D2"] < th["D2_max"]
            and cand["D2"] < th["ratio"] * cand["D1"]
            and cand["D1"] < th["ratio"] * cand["D0"]
        )

    passed_leibniz = [c for c in candidates if passes_leibniz(c, thresholds)]
    if len(passed_leibniz) == 0:
        thresholds["D2_max"] = 0.20
        thresholds["ratio"] = 0.85
        passed_leibniz = [c for c in candidates if passes_leibniz(c, thresholds)]

    passed_leibniz_by_mode: Counter[str] = Counter(c["mode"] for c in passed_leibniz)

    false_positives = [
        c for c in passed_leibniz if c["minF"] > thresholds["minF"]
    ]

    false_positives.sort(key=lambda c: (c["D2"], -c["minF"]))
    top_false = false_positives[:10]

    false_positive_by_mode: Counter[str] = Counter(c["mode"] for c in false_positives)

    note = "false positives found"
    near_misses = []
    if len(false_positives) == 0:
        note = (
            "none found; no candidates met both the Leibniz gate and minF threshold"
        )
        near_misses = sorted(
            [c for c in candidates if c["minF"] > 0.2], key=lambda c: c["D2"]
        )[:10]

    output = {
        "params": {
            "m": m,
            "N0": n0,
            "seed": seed,
            "mode": args.mode,
            "num": num,
            "thresholds": thresholds,
        },
        "counts": {
            "tested_total": len(candidates),
            "tested_by_mode": dict(tested_by_mode),
            "passed_leibniz_total": len(passed_leibniz),
            "passed_leibniz_by_mode": dict(passed_leibniz_by_mode),
            "false_positive_total": len(false_positives),
            "false_positive_by_mode": dict(false_positive_by_mode),
            "resample_count_moment1": resample_count,
        },
        "false_positives_top10": top_false,
        "note": note,
    }

    if near_misses:
        output["near_misses_top10"] = near_misses

    Path(args.out).write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

    summary = (
        f"tested_total={len(candidates)}, passed_leibniz={len(passed_leibniz)}, "
        f"false_positive_total={len(false_positives)}, thresholds={thresholds}"
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
