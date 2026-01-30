#!/usr/bin/env python3
"""Leibniz-gated stencil selection experiment."""

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
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


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


def moment1_project(c: np.ndarray, m: int) -> Tuple[np.ndarray, float]:
    c = c - np.mean(c)
    idx = np.arange(-m, m + 1, dtype=float)
    m1 = float(np.dot(idx, c))
    if abs(m1) < 1e-12:
        return c, m1
    c = c / m1
    return c, m1


def project_high_order(c: np.ndarray, m: int) -> np.ndarray:
    """Enforce moments: sum=0, M1=1, M2=0, M3=0 via a linear correction."""
    idx = np.arange(-m, m + 1, dtype=float)
    basis = np.vstack([np.ones_like(idx), idx, idx**2, idx**3]).T
    M = basis.T
    target = np.array([0.0, 1.0, 0.0, 0.0])
    current = M @ c
    try:
        alpha = np.linalg.solve(M @ basis, target - current)
        return c + basis @ alpha
    except np.linalg.LinAlgError:
        return c


def build_base(m: int) -> np.ndarray:
    idx = np.arange(-m, m + 1, dtype=float)
    base = idx.copy()
    base, _ = moment1_project(base, m)
    return base


def evaluate_candidate(
    coeffs: np.ndarray,
    m: int,
    families_by_res: List[List[FunctionFamily]],
    hs: List[float],
    eps: float,
) -> Tuple[Dict[int, float], Dict[int, float], Dict[int, float], float, float, float, bool]:
    h0, h1, h2 = hs
    outs: Dict[int, List[np.ndarray]] = {0: [], 1: [], 2: []}
    outs1: Dict[int, List[np.ndarray]] = {0: [], 1: [], 2: []}
    outs2: Dict[int, List[np.ndarray]] = {0: [], 1: [], 2: []}

    for fam0, fam1, fam2 in zip(
        families_by_res[0], families_by_res[1], families_by_res[2]
    ):
        out0, _ = apply_stencil_clipped(fam0.values, coeffs, m)
        out1, _ = apply_stencil_clipped(fam1.values, coeffs, m)
        out2, _ = apply_stencil_clipped(fam2.values, coeffs, m)

        outs[0].append(out0)
        outs1[0].append(out1)
        outs2[0].append(out2)
        outs[1].append(out0 / h0)
        outs1[1].append(out1 / h1)
        outs2[1].append(out2 / h2)
        outs[2].append(out0 / (h0**2))
        outs1[2].append(out1 / (h1**2))
        outs2[2].append(out2 / (h2**2))

    n0 = len(families_by_res[0][0].values)
    n1 = len(families_by_res[1][0].values)
    centers0 = np.arange(m, n0 - m, dtype=int)
    centers1 = np.arange(m, n1 - m, dtype=int)
    pos01 = (2 * centers0) - m
    pos12 = (2 * centers1) - m

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
        f_errors[k] = fit_error(y, t, eps)

    pairs_idx = [(1, 2), (3, 4), (2, 4)]
    pairs0 = [(families_by_res[0][i], families_by_res[0][j]) for i, j in pairs_idx]
    pairs1 = [(families_by_res[1][i], families_by_res[1][j]) for i, j in pairs_idx]
    pairs2 = [(families_by_res[2][i], families_by_res[2][j]) for i, j in pairs_idx]

    d0 = compute_leibniz_defect(coeffs, m, h0, pairs0, eps)
    d1 = compute_leibniz_defect(coeffs, m, h1, pairs1, eps)
    d2 = compute_leibniz_defect(coeffs, m, h2, pairs2, eps)

    nontrivial = any(np.linalg.norm(out) > 1e-6 for out in outs2[1])

    return e01_k, e12_k, f_errors, d0, d1, d2, nontrivial


def main() -> int:
    parser = argparse.ArgumentParser(description="Leibniz-gated stencil selection")
    parser.add_argument("--m", type=int, default=3)
    parser.add_argument("--max-tries", type=int, default=5000)
    parser.add_argument("--target-survivors", type=int, default=50)
    parser.add_argument("--N0", type=int, default=64)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--noise", type=float, default=0.30)
    parser.add_argument("--gate-D2", type=float, default=0.20)
    parser.add_argument("--gate-ratio", type=float, default=0.85)
    parser.add_argument("--out", type=str, default=None)
    parser.add_argument(
        "--notes-out",
        type=str,
        default="notes/stencil_flow_leibniz_last_run.json",
    )
    parser.add_argument(
        "--fig-out",
        type=str,
        default="figures/stencil_flow_leibniz_last_run.svg",
    )
    args = parser.parse_args()

    print(
        "params: m={m}, max_tries={max_tries}, target_survivors={target_survivors}, "
        "N0={N0}, seed={seed}, noise={noise}, gate_D2={gate_D2}, gate_ratio={gate_ratio}".format(
            **vars(args)
        )
    )

    rng = np.random.default_rng(args.seed)

    n0 = args.N0
    n1 = 2 * n0
    n2 = 4 * n0
    hs = [1.0 / n for n in (n0, n1, n2)]

    families_by_res = []
    for n, h in zip((n0, n1, n2), hs):
        x = np.arange(n, dtype=float) * h
        families_by_res.append(build_families(x))
    test_family = [fam.name for fam in families_by_res[0]]

    base = build_base(args.m)

    survivors: List[Dict[str, object]] = []
    tested_by_mode: Counter[str] = Counter()
    survivors_by_k: Counter[int] = Counter()
    resample_count = 0

    for _ in range(args.max_tries):
        if len(survivors) >= args.target_survivors:
            break

        mode = "perturbed" if rng.random() < 0.5 else "random"
        if mode == "perturbed":
            coeffs = base + args.noise * rng.standard_normal(2 * args.m + 1)
            coeffs, _ = moment1_project(coeffs, args.m)
            coeffs = project_high_order(coeffs, args.m)
        else:
            while True:
                coeffs = rng.standard_normal(2 * args.m + 1)
                coeffs, m1 = moment1_project(coeffs, args.m)
                if abs(m1) < 1e-8:
                    resample_count += 1
                    continue
                break
            coeffs = project_high_order(coeffs, args.m)

        tested_by_mode[mode] += 1

        e01_k, e12_k, f_errors, d0, d1, d2, nontrivial = evaluate_candidate(
            coeffs, args.m, families_by_res, hs, 1e-12
        )

        best_fit_k = min(f_errors, key=f_errors.get)

        stable = e12_k[1] < e01_k[1] and e12_k[1] < 0.25
        leibniz_ok = (
            d2 < args.gate_D2
            and d2 < args.gate_ratio * d1
            and d1 < args.gate_ratio * d0
        )
        derivative_like = best_fit_k == 1

        if stable and leibniz_ok and derivative_like and nontrivial:
            survivors_by_k[best_fit_k] += 1
            survivors.append(
                {
                    "coeffs": [float(c) for c in coeffs],
                    "E01_1": float(e01_k[1]),
                    "E12_1": float(e12_k[1]),
                    "D0": float(d0),
                    "D1": float(d1),
                    "D2": float(d2),
                    "F0": float(f_errors[0]),
                    "F1": float(f_errors[1]),
                    "F2": float(f_errors[2]),
                }
            )

    survivors.sort(key=lambda rec: rec["D2"])
    top_survivors = survivors[:10]

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = (
        Path(args.out)
        if args.out
        else Path("data/runs") / f"stencil_flow_leibniz_{timestamp}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "timestamp": timestamp,
        "params": {
            "m": args.m,
            "max_tries": args.max_tries,
            "target_survivors": args.target_survivors,
            "N0": args.N0,
            "seed": args.seed,
            "noise": args.noise,
            "gate_D2": args.gate_D2,
            "gate_ratio": args.gate_ratio,
        },
        "counts": {
            "tested_total": int(sum(tested_by_mode.values())),
            "tested_by_mode": dict(tested_by_mode),
            "resample_count": int(resample_count),
            "survivors_total": len(survivors),
        },
        "survivors_by_best_fit_k": {str(k): int(v) for k, v in survivors_by_k.items()},
        "top_survivors": top_survivors,
    }
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # Figure: bar chart of survivors by k
    fig, ax = plt.subplots(figsize=(4, 3))
    ks = [0, 1, 2]
    counts = [survivors_by_k.get(k, 0) for k in ks]
    ax.bar([str(k) for k in ks], counts)
    ax.set_xlabel("best_fit_k")
    ax.set_ylabel("survivors")
    fig.tight_layout()

    fig_path = Path(args.fig_out)
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(fig_path, format="svg")
    if fig_path.suffix == ".svg":
        png_path = fig_path.with_suffix(".png")
        fig.savefig(png_path, format="png", dpi=200)
    else:
        png_path = fig_path
    plt.close(fig)

    table = []
    for idx, rec in enumerate(top_survivors, start=1):
        table.append([idx, rec["D2"], rec["F1"], rec["E12_1"]])

    notes_payload = {
        "timestamp": timestamp,
        "output_path": out_path.as_posix(),
        "figure_path": fig_path.as_posix(),
        "figure_png_path": png_path.as_posix(),
        "survivors_total": len(survivors),
        "survivors_by_best_fit_k": {str(k): int(v) for k, v in survivors_by_k.items()},
        "table": table,
        "params": {
            "m": args.m,
            "N0": args.N0,
            "seed": args.seed,
            "noise": args.noise,
            "max_tries": args.max_tries,
            "target_survivors": args.target_survivors,
            "gate_D2": args.gate_D2,
            "gate_ratio": args.gate_ratio,
            "moment_projection": True,
            "moment_constraints": "sum=0, M1=1, M2≈0, M3≈0",
            "boundary_mode": "clipped",
            "test_family": test_family,
        },
    }
    Path(args.notes_out).write_text(
        json.dumps(notes_payload, indent=2) + "\n", encoding="utf-8"
    )

    print(
        "tested_total={tested}, survivors_total={surv}, survivors_by_k={byk}".format(
            tested=sum(tested_by_mode.values()),
            surv=len(survivors),
            byk={k: int(v) for k, v in survivors_by_k.items()},
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
