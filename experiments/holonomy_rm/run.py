#!/usr/bin/env python3
"""Route mismatch experiment under coordinate change."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def g_func(y: np.ndarray) -> np.ndarray:
    return np.sin(2 * np.pi * y) + 0.1 * np.cos(6 * np.pi * y) + np.exp(-y)


def interp1(u_grid: np.ndarray, u_vals: np.ndarray, query: np.ndarray) -> np.ndarray:
    return np.interp(query, u_grid, u_vals)


def central_diff(vals: np.ndarray, step: float) -> np.ndarray:
    return (vals[2:] - vals[:-2]) / (2 * step)


def fit_loglog(hs: np.ndarray, rms: np.ndarray) -> Tuple[float, float, float]:
    eps = 1e-30
    logh = np.log(hs)
    logr = np.log(rms + eps)
    p, c = np.polyfit(logh, logr, 1)
    pred = p * logh + c
    ss_res = float(np.sum((logr - pred) ** 2))
    ss_tot = float(np.sum((logr - np.mean(logr)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return float(p), float(c), float(r2)


def compute_results(eps: float, n_list: List[int]) -> List[dict]:
    results: List[dict] = []
    for n in n_list:
        h = 1.0 / n
        x = np.linspace(0.0, 1.0, n + 1)
        ymax = 1.0 + eps
        y = np.arange(0.0, ymax + 1e-12, h)

        x2 = np.linspace(0.0, 1.0, 2 * n + 1)
        y2 = np.arange(0.0, ymax + 1e-12, h / 2.0)

        g_y = g_func(y)
        g_y_ref = interp1(y, g_y, y2)

        dg_dy_y2 = central_diff(g_y_ref, h / 2.0)
        y2_mid = y2[1:-1]

        x_use = x[2:-2]
        phi_x = x_use + eps * (x_use**2)
        mask = (phi_x >= y2_mid[0]) & (phi_x <= y2_mid[-1])
        x_use = x_use[mask]
        phi_x = phi_x[mask]

        A = interp1(y2_mid, dg_dy_y2, phi_x)

        phi_x_full = x + eps * (x**2)
        g_x = interp1(y, g_y, phi_x_full)
        g_x_ref = interp1(x, g_x, x2)

        dg_dx_x2 = central_diff(g_x_ref, h / 2.0)
        x2_mid = x2[1:-1]
        phi_prime_mid = 1.0 + 2.0 * eps * x2_mid
        dg_dy_est_mid = dg_dx_x2 / phi_prime_mid

        B = interp1(x2_mid, dg_dy_est_mid, x_use)

        rm = float(np.linalg.norm(A - B) / (np.linalg.norm(A) + 1e-12))

        results.append({"N": int(n), "h": float(h), "rm": rm, "n_eval": int(len(x_use))})
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Holonomy route mismatch experiment")
    parser.add_argument("--eps", type=float, default=0.05)
    parser.add_argument("--N-list", nargs="+", type=int, default=[64, 128, 256, 512])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=str, default=None)
    parser.add_argument("--notes-out", type=str, default="notes/holonomy_rm_last_run.json")
    parser.add_argument("--fig-out", type=str, default="figures/holonomy_rm_last_run.svg")
    args = parser.parse_args()

    eps = args.eps
    n_list = args.N_list
    seed = args.seed

    print(f"params: eps={eps}, N_list={n_list}, seed={seed}")

    results = compute_results(eps, n_list)
    null_results = compute_results(0.0, n_list)

    hs = np.array([r["h"] for r in results], dtype=float)
    rms = np.array([r["rm"] for r in results], dtype=float)
    p, c, r2 = fit_loglog(hs, rms)

    print("RM table (h, rm):")
    for r in results:
        print(f"  h={r['h']:.6f}  rm={r['rm']:.6e}  n_eval={r['n_eval']}")
    print(f"fitted exponent p={p:.6f}")

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = (
        Path(args.out)
        if args.out
        else Path("data/runs") / f"holonomy_rm_{timestamp}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "timestamp": timestamp,
        "params": {"eps": eps, "N_list": n_list, "seed": seed},
        "results": results,
        "fit": {"p": p, "c": c, "r2": r2},
        "null_results": null_results,
    }
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # Figure: RM vs h
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.plot(hs, rms, marker="o")
    # fitted line in log-log space
    fit_vals = np.exp(p * np.log(hs) + c)
    ax.plot(hs, fit_vals)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("h")
    ax.set_ylabel("RM")
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

    table = [[round(r["h"], 8), round(r["rm"], 8)] for r in results[:6]]
    null_table = [[round(r["h"], 8), round(r["rm"], 12)] for r in null_results[:6]]
    null_rm_max = max(r["rm"] for r in null_results) if null_results else float("nan")
    null_rm_at_smallest_h = null_results[-1]["rm"] if null_results else float("nan")
    notes_payload = {
        "timestamp": timestamp,
        "output_path": out_path.as_posix(),
        "figure_path": fig_path.as_posix(),
        "figure_png_path": png_path.as_posix(),
        "fit_p": p,
        "fit_r2": r2,
        "table": table,
        "null_table": null_table,
        "null_rm_max": null_rm_max,
        "null_rm_at_smallest_h": null_rm_at_smallest_h,
        "params": {"eps": eps, "N_list": n_list, "seed": seed},
    }
    Path(args.notes_out).write_text(
        json.dumps(notes_payload, indent=2) + "\n", encoding="utf-8"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
