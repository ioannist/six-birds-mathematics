#!/usr/bin/env python3
"""Stencil feasibility experiment (clipped boundaries, non-periodic)."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

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
    """Apply a local stencil on the interior (no wrap)."""
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


def fit_error(y: np.ndarray, t: np.ndarray, eps: float) -> Tuple[float, float]:
    denom = float(np.dot(t, t))
    if denom == 0.0:
        return 0.0, float(np.linalg.norm(y))
    a = float(np.dot(y, t) / denom)
    fit = a * t
    err = float(np.linalg.norm(y - fit) / (np.linalg.norm(fit) + eps))
    return a, err


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Stencil feasibility filter")
    parser.add_argument("--m-values", nargs="+", type=int, default=[2, 3])
    parser.add_argument("--num", type=int, default=500)
    parser.add_argument("--N0", type=int, default=64)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=str, default=None)

    args = parser.parse_args()

    m_values = args.m_values
    num = args.num
    n0 = args.N0
    n1 = 2 * n0
    n2 = 4 * n0
    seed = args.seed
    eps = 1e-12

    print(
        f"params: m_values={m_values}, num={num}, N0={n0}, seed={seed}")

    rng = np.random.default_rng(seed)

    resolutions = [n0, n1, n2]
    hs = [1.0 / n for n in resolutions]
    families_by_res: List[List[FunctionFamily]] = []
    for n, h in zip(resolutions, hs):
        x = np.arange(n, dtype=float) * h
        families_by_res.append(build_families(x))

    pairs_idx = [(1, 2), (3, 4), (2, 4)]  # lin*quad, sin*exp, quad*exp
    test_family = [fam.name for fam in families_by_res[0]]

    survivors: List[Dict[str, object]] = []
    generated_by_m: Dict[str, int] = {}
    survivors_by_k: Counter[int] = Counter()

    for m in m_values:
        generated_by_m[str(m)] = num
        centers0 = np.arange(m, n0 - m, dtype=int)
        centers1 = np.arange(m, n1 - m, dtype=int)
        centers2 = np.arange(m, n2 - m, dtype=int)
        pos01 = (2 * centers0) - m
        pos12 = (2 * centers1) - m

        for _ in range(num):
            coeffs = rng.standard_normal(2 * m + 1)

            outs: Dict[int, List[np.ndarray]] = {0: [], 1: [], 2: []}
            outs1: Dict[int, List[np.ndarray]] = {0: [], 1: [], 2: []}
            outs2: Dict[int, List[np.ndarray]] = {0: [], 1: [], 2: []}

            for fam0, fam1, fam2 in zip(
                families_by_res[0], families_by_res[1], families_by_res[2]
            ):
                out0, _ = apply_stencil_clipped(fam0.values, coeffs, m)
                out1, _ = apply_stencil_clipped(fam1.values, coeffs, m)
                out2, _ = apply_stencil_clipped(fam2.values, coeffs, m)

                h0, h1, h2 = hs
                outs[0].append(out0)
                outs1[0].append(out1)
                outs2[0].append(out2)
                outs[1].append(out0 / h0)
                outs1[1].append(out1 / h1)
                outs2[1].append(out2 / h2)
                outs[2].append(out0 / (h0**2))
                outs1[2].append(out1 / (h1**2))
                outs2[2].append(out2 / (h2**2))

            e01_k: Dict[int, float] = {}
            e12_k: Dict[int, float] = {}
            for k in (0, 1, 2):
                max_e01 = 0.0
                max_e12 = 0.0
                for out0, out1, out2 in zip(outs[k], outs1[k], outs2[k]):
                    out1_aligned = out1[pos01]
                    out2_aligned = out2[pos12]
                    e01 = float(
                        np.linalg.norm(out0 - out1_aligned)
                        / (np.linalg.norm(out0) + eps)
                    )
                    e12 = float(
                        np.linalg.norm(out1 - out2_aligned)
                        / (np.linalg.norm(out1) + eps)
                    )
                    max_e01 = max(max_e01, e01)
                    max_e12 = max(max_e12, e12)
                e01_k[k] = max_e01
                e12_k[k] = max_e12

            d0 = d1 = d2 = None
            if True:
                pairs0 = [
                    (
                        families_by_res[0][i],
                        families_by_res[0][j],
                    )
                    for i, j in pairs_idx
                ]
                pairs1 = [
                    (
                        families_by_res[1][i],
                        families_by_res[1][j],
                    )
                    for i, j in pairs_idx
                ]
                pairs2 = [
                    (
                        families_by_res[2][i],
                        families_by_res[2][j],
                    )
                    for i, j in pairs_idx
                ]
                d0 = compute_leibniz_defect(coeffs, m, hs[0], pairs0, eps)
                d1 = compute_leibniz_defect(coeffs, m, hs[1], pairs1, eps)
                d2 = compute_leibniz_defect(coeffs, m, hs[2], pairs2, eps)

            f_errors: Dict[int, float] = {}
            for k in (0, 1, 2):
                y = np.concatenate(outs2[k])
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
                _, err = fit_error(y, t, eps)
                f_errors[k] = err

            best_fit_k = min(f_errors, key=f_errors.get)

            nontrivial = any(
                np.linalg.norm(out) > 1e-6 for out in outs2[best_fit_k]
            )

            stable = (
                e12_k[best_fit_k] < e01_k[best_fit_k]
                and e12_k[best_fit_k] < 0.25
            )

            leibniz_ok = True
            if best_fit_k == 1:
                leibniz_ok = (
                    d2 is not None
                    and d1 is not None
                    and d0 is not None
                    and d2 <= d1 + 1e-15
                    and d1 <= d0 + 1e-15
                    and d2 < d0
                    and d2 < 0.50
                )

            if stable and nontrivial and leibniz_ok:
                survivors_by_k[best_fit_k] += 1
                survivors.append(
                    {
                        "m": m,
                        "coeffs": [float(c) for c in coeffs],
                        "best_fit_k": int(best_fit_k),
                        "F_0": float(f_errors[0]),
                        "F_1": float(f_errors[1]),
                        "F_2": float(f_errors[2]),
                        "E01_k": float(e01_k[best_fit_k]),
                        "E12_k": float(e12_k[best_fit_k]),
                        "D0": float(d0) if d0 is not None else None,
                        "D1": float(d1) if d1 is not None else None,
                        "D2": float(d2) if d2 is not None else None,
                    }
                )

    generated_total = sum(generated_by_m.values())
    survivors_total = len(survivors)

    survivors.sort(key=lambda rec: rec["F_%d" % rec["best_fit_k"]])
    top_survivors = survivors[:10]

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = (
        Path(args.out)
        if args.out
        else Path("data/runs") / f"stencil_flow_{timestamp}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    survivors_by_k_full = {str(k): int(survivors_by_k.get(k, 0)) for k in (0, 1, 2)}

    payload = {
        "timestamp": timestamp,
        "params": {
            "m_values": m_values,
            "num": num,
            "N0": n0,
            "seed": seed,
            "eps": eps,
            "stability_threshold": 0.25,
            "leibniz_threshold": 0.50,
            "boundary_mode": "clipped",
            "alignment_mode": "even_index",
            "test_family": test_family,
        },
        "generated_total": generated_total,
        "generated_by_m": generated_by_m,
        "survivors_total": survivors_total,
        "survivors_by_best_fit_k": survivors_by_k_full,
        "best_fit_k_distribution_survivors": survivors_by_k_full,
        "top_survivors": top_survivors,
    }

    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    last_run = {
        "timestamp": timestamp,
        "output_path": out_path.as_posix(),
        "generated_total": generated_total,
        "survivors_total": survivors_total,
        "survivors_by_best_fit_k": survivors_by_k_full,
        "params": {
            "m_values": m_values,
            "num": num,
            "N0": n0,
            "seed": seed,
            "stability_threshold": 0.25,
            "leibniz_threshold": 0.50,
            "boundary_mode": "clipped",
            "alignment_mode": "even_index",
            "test_family": test_family,
        },
    }
    notes_path = Path("notes/stencil_flow_last_run.json")
    notes_path.write_text(json.dumps(last_run, indent=2) + "\n", encoding="utf-8")

    summary = (
        f"generated_total={generated_total}, survivors_total={survivors_total}, "
        f"survivors_by_k={{0: {survivors_by_k.get(0, 0)}, "
        f"1: {survivors_by_k.get(1, 0)}, 2: {survivors_by_k.get(2, 0)}}}"
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
