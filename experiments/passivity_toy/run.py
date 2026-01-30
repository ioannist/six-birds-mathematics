#!/usr/bin/env python3
"""Passivity toy: positivity vs zero confinement on unit circle."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def build_edges_cycle(n: int) -> List[Tuple[int, int]]:
    return [(i, (i + 1) % n) for i in range(n)]


def build_edges_erdos_renyi(n: int, p: float, rng: np.random.Generator) -> List[Tuple[int, int]]:
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            if rng.random() < p:
                edges.append((i, j))
    return edges


def compute_coeffs(
    n: int,
    beta: float,
    edges: List[Tuple[int, int]],
    J: np.ndarray,
) -> Tuple[np.ndarray, float, float, np.ndarray]:
    num = 1 << n
    idx = np.arange(num, dtype=np.uint32)[:, None]
    bits = ((idx >> np.arange(n, dtype=np.uint32)) & 1).astype(np.int8)
    sigma = 1 - 2 * bits
    k = bits.sum(axis=1)

    if edges:
        i_idx = np.array([i for i, _ in edges], dtype=int)
        j_idx = np.array([j for _, j in edges], dtype=int)
        prod = sigma[:, i_idx] * sigma[:, j_idx]
        energy = prod @ J
    else:
        energy = np.zeros(num, dtype=float)

    weights = np.exp(beta * energy)
    a = np.bincount(k, weights=weights, minlength=n + 1).astype(float)

    sym_err_before = float(np.max(np.abs(a - a[::-1])) / (np.max(a) + 1e-15))
    a = 0.5 * (a + a[::-1])
    sym_err_after = float(np.max(np.abs(a - a[::-1])) / (np.max(a) + 1e-15))
    return a, sym_err_before, sym_err_after, weights


def compute_roots_metrics(a: np.ndarray) -> Tuple[np.ndarray, float, float, float]:
    coef = a[::-1].astype(float)
    coef = coef / np.max(np.abs(coef))
    roots = np.roots(coef)
    radii = np.abs(roots)
    d = np.abs(radii - 1.0)
    return roots, float(np.mean(d)), float(np.median(d)), float(np.max(d))


def main() -> int:
    parser = argparse.ArgumentParser(description="Passivity toy experiment")
    parser.add_argument("--n", type=int, default=12)
    parser.add_argument("--beta", type=float, default=0.7)
    parser.add_argument("--graph", choices=["cycle", "erdos_renyi"], default="cycle")
    parser.add_argument("--p", type=float, default=0.25)
    parser.add_argument("--J-scale", type=float, default=0.5)
    parser.add_argument(
        "--lambda-list",
        nargs="+",
        type=float,
        default=[1.0, 0.7, 0.4, 0.2, 0.1, 0.0],
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=str, default=None)
    parser.add_argument("--notes-out", type=str, default="notes/passivity_toy_last_run.json")
    parser.add_argument("--fig-out", type=str, default="figures/passivity_toy_last_run.svg")
    args = parser.parse_args()

    print(
        f"params: n={args.n}, beta={args.beta}, graph={args.graph}, p={args.p}, "
        f"J_scale={args.J_scale}, lambda_list={args.lambda_list}, seed={args.seed}"
    )

    rng = np.random.default_rng(args.seed)

    if args.graph == "cycle":
        edges = build_edges_cycle(args.n)
    else:
        edges = build_edges_erdos_renyi(args.n, args.p, rng)

    J_base = rng.normal(0.0, args.J_scale, size=len(edges)) if edges else np.array([])
    J_pos = np.maximum(J_base, 0.0)
    J_neg = np.minimum(J_base, 0.0)

    results = []
    roots_by_lambda: Dict[float, np.ndarray] = {}

    for lam in args.lambda_list:
        J_lambda = J_pos + lam * J_neg
        a, sym_before, sym_after, _ = compute_coeffs(args.n, args.beta, edges, J_lambda)
        roots, mean_dev, median_dev, max_dev = compute_roots_metrics(a)
        roots_by_lambda[lam] = roots
        results.append(
            {
                "lambda": float(lam),
                "mean_dev": mean_dev,
                "median_dev": median_dev,
                "max_dev": max_dev,
                "sym_err_before": sym_before,
                "sym_err_after": sym_after,
                "roots": [[float(z.real), float(z.imag)] for z in roots],
                "coeffs": [float(x) for x in a],
            }
        )

    mean_vals = [r["mean_dev"] for r in results]
    decrease_steps = sum(
        1 for i in range(1, len(mean_vals)) if mean_vals[i] < mean_vals[i - 1]
    )

    trend_note = (
        f"mean_dev decreased in {decrease_steps}/{max(len(mean_vals)-1,1)} steps as lambda→0"
    )

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = (
        Path(args.out)
        if args.out
        else Path("data/runs") / f"passivity_toy_{timestamp}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "timestamp": timestamp,
        "params": {
            "n": args.n,
            "beta": args.beta,
            "graph": args.graph,
            "p": args.p,
            "J_scale": args.J_scale,
            "lambda_list": args.lambda_list,
            "seed": args.seed,
        },
        "edges_count": len(edges),
        "results": results,
        "trend": {
            "lambda_values": [float(l) for l in args.lambda_list],
            "mean_dev_values": mean_vals,
            "mean_dev_decrease_steps": decrease_steps,
            "mean_dev_total_steps": max(len(mean_vals) - 1, 1),
        },
    }
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # Plot roots for lambda=1 and lambda=0 if present
    fig, ax = plt.subplots(figsize=(5, 5))
    for lam in [args.lambda_list[0], args.lambda_list[-1]]:
        roots = roots_by_lambda.get(lam)
        if roots is None:
            continue
        ax.scatter(roots.real, roots.imag, s=12, label=f"lambda={lam}")
    t = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(t), np.sin(t), color="black", linewidth=1, label="|z|=1")
    ax.set_xlabel("Re(z)")
    ax.set_ylabel("Im(z)")
    ax.set_aspect("equal", "box")
    ax.legend(loc="best", fontsize=8)
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

    table = [
        [float(r["lambda"]), round(r["mean_dev"], 8), round(r["max_dev"], 8)]
        for r in results
    ]
    notes_payload = {
        "timestamp": timestamp,
        "output_path": out_path.as_posix(),
        "figure_path": fig_path.as_posix(),
        "figure_png_path": png_path.as_posix(),
        "table": table,
        "trend_summary": trend_note,
        "params": {
            "n": args.n,
            "beta": args.beta,
            "graph": args.graph,
            "p": args.p,
            "J_scale": args.J_scale,
            "lambda_list": args.lambda_list,
            "seed": args.seed,
        },
    }
    Path(args.notes_out).write_text(
        json.dumps(notes_payload, indent=2) + "\n", encoding="utf-8"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
