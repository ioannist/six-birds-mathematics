#!/usr/bin/env python3
"""Integration closure diagnostics under refinement."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def left_cumulative_sum(f: np.ndarray, h: float) -> np.ndarray:
    """I_h(f)(x_i) = h * sum_{j<i} f(x_j)."""
    return np.concatenate(([0.0], h * np.cumsum(f[:-1])))


def trapezoid_cumulative_sum(f: np.ndarray, h: float) -> np.ndarray:
    """T_h(f)(x_i) = h * sum_{j<i} (f_j + f_{j+1}) / 2."""
    return np.concatenate(([0.0], h * np.cumsum((f[:-1] + f[1:]) * 0.5)))


def scaled_forward_diff(g: np.ndarray, h: float) -> np.ndarray:
    """delta_h g(x_i) = (g_{i+1} - g_i) / h for i = 0..N-1."""
    return (g[1:] - g[:-1]) / h


def l2_norm(arr: np.ndarray) -> float:
    return float(np.linalg.norm(arr, ord=2))


def fit_loglog(h_vals: np.ndarray, y_vals: np.ndarray, eps: float) -> Tuple[float, float, float]:
    logh = np.log(h_vals)
    logy = np.log(y_vals + eps)
    slope, intercept = np.polyfit(logh, logy, 1)
    pred = slope * logh + intercept
    ss_res = float(np.sum((logy - pred) ** 2))
    ss_tot = float(np.sum((logy - np.mean(logy)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return float(slope), float(intercept), float(r2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Integration as stable closure diagnostics")
    parser.add_argument("--N-list", nargs="+", type=int, default=[128, 256, 512, 1024])
    parser.add_argument("--eps0", type=float, default=1e-12)
    parser.add_argument("--out", type=str, default=None)
    parser.add_argument("--notes-out", type=str, default="notes/integration_closure_last_run.json")
    parser.add_argument("--fig-out", type=str, default="figures/integration_closure_last_run.svg")
    args = parser.parse_args()

    funcs: Dict[str, Callable[[np.ndarray], np.ndarray]] = {
        "sin2pi": lambda x: np.sin(2.0 * np.pi * x),
        "exp": lambda x: np.exp(x),
        "const1": lambda x: np.ones_like(x),
        "x": lambda x: x,
        "x2": lambda x: x**2,
    }
    test_family = list(funcs.keys())

    print(f"params: N_list={args.N_list}, test_family={test_family}, eps0={args.eps0}")

    per_n_rows: List[Dict[str, float]] = []
    per_n_details: List[Dict[str, object]] = []
    h_vals: List[float] = []
    rm_vals: List[float] = []
    ft_left_vals: List[float] = []
    ft_trap_vals: List[float] = []
    add_left_vals: List[float] = []
    add_trap_vals: List[float] = []

    for n in args.N_list:
        h = 1.0 / float(n)
        x = np.linspace(0.0, 1.0, n + 1)
        k = n // 2
        per_func: List[Dict[str, float]] = []

        rm_max = 0.0
        ft_left_max = 0.0
        ft_trap_max = 0.0
        add_left_max = 0.0
        add_trap_max = 0.0

        for name, fn in funcs.items():
            f = fn(x)
            I = left_cumulative_sum(f, h)
            T = trapezoid_cumulative_sum(f, h)

            dI = scaled_forward_diff(I, h)
            dT = scaled_forward_diff(T, h)
            f_aligned = f[:-1]

            ft_left = l2_norm(dI - f_aligned)
            ft_trap = l2_norm(dT - f_aligned)
            rm = l2_norm(I - T) / (l2_norm(T) + args.eps0)

            full_left = I[-1]
            split_left = h * np.sum(f[:k]) + h * np.sum(f[k:n])
            full_trap = T[-1]
            split_trap = h * np.sum((f[:k] + f[1 : k + 1]) * 0.5) + h * np.sum(
                (f[k:n] + f[k + 1 : n + 1]) * 0.5
            )
            add_left = float(abs(full_left - split_left))
            add_trap = float(abs(full_trap - split_trap))

            per_func.append(
                {
                    "name": name,
                    "rm": float(rm),
                    "ft_left": float(ft_left),
                    "ft_trap": float(ft_trap),
                    "add_left": add_left,
                    "add_trap": add_trap,
                }
            )

            rm_max = max(rm_max, float(rm))
            ft_left_max = max(ft_left_max, float(ft_left))
            ft_trap_max = max(ft_trap_max, float(ft_trap))
            add_left_max = max(add_left_max, add_left)
            add_trap_max = max(add_trap_max, add_trap)

        row = {
            "N": int(n),
            "h": float(h),
            "rm_max": rm_max,
            "ft_left_max": ft_left_max,
            "ft_trap_max": ft_trap_max,
            "add_left_max": add_left_max,
            "add_trap_max": add_trap_max,
        }
        per_n_rows.append(row)
        per_n_details.append({"N": int(n), "per_function": per_func})

        h_vals.append(float(h))
        rm_vals.append(rm_max)
        ft_left_vals.append(ft_left_max)
        ft_trap_vals.append(ft_trap_max)
        add_left_vals.append(add_left_max)
        add_trap_vals.append(add_trap_max)

    h_arr = np.array(h_vals, dtype=float)
    rm_arr = np.array(rm_vals, dtype=float)
    ft_left_arr = np.array(ft_left_vals, dtype=float)
    ft_trap_arr = np.array(ft_trap_vals, dtype=float)
    add_left_arr = np.array(add_left_vals, dtype=float)
    add_trap_arr = np.array(add_trap_vals, dtype=float)

    rm_slope, rm_intercept, rm_r2 = fit_loglog(h_arr, rm_arr, args.eps0)
    ft_left_slope, ft_left_intercept, ft_left_r2 = fit_loglog(h_arr, ft_left_arr, args.eps0)
    ft_trap_slope, ft_trap_intercept, ft_trap_r2 = fit_loglog(h_arr, ft_trap_arr, args.eps0)
    add_left_slope, add_left_intercept, add_left_r2 = fit_loglog(h_arr, add_left_arr, args.eps0)
    add_trap_slope, add_trap_intercept, add_trap_r2 = fit_loglog(h_arr, add_trap_arr, args.eps0)

    print("integration closure table:")
    for row in per_n_rows:
        print(
            "  N={N} h={h:.8f} rm_max={rm_max:.6e} ft_left_max={ft_left_max:.6e} ft_trap_max={ft_trap_max:.6e}".format(
                **row
            )
        )
    print(f"fits: rm_slope={rm_slope:.6f}, ft_trap_slope={ft_trap_slope:.6f}")

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = (
        Path(args.out)
        if args.out
        else Path("data/runs") / f"integration_closure_{timestamp}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    run_payload = {
        "timestamp": timestamp,
        "params": {
            "N_list": args.N_list,
            "test_family": test_family,
            "norm": "l2",
            "epsilon0": args.eps0,
            "domain": [0.0, 1.0],
            "operators": {
                "integrators": ["left_riemann_cumulative", "trapezoid_cumulative"],
                "derivative": "forward_difference_scaled",
            },
        },
        "results": {
            "rows": per_n_rows,
            "per_function": per_n_details,
            "fits": {
                "rm_max": {"slope": rm_slope, "intercept": rm_intercept, "r2": rm_r2},
                "ft_left_max": {
                    "slope": ft_left_slope,
                    "intercept": ft_left_intercept,
                    "r2": ft_left_r2,
                },
                "ft_trap_max": {
                    "slope": ft_trap_slope,
                    "intercept": ft_trap_intercept,
                    "r2": ft_trap_r2,
                },
                "add_left_max": {
                    "slope": add_left_slope,
                    "intercept": add_left_intercept,
                    "r2": add_left_r2,
                },
                "add_trap_max": {
                    "slope": add_trap_slope,
                    "intercept": add_trap_intercept,
                    "r2": add_trap_r2,
                },
            },
        },
    }
    out_path.write_text(json.dumps(run_payload, indent=2) + "\n", encoding="utf-8")

    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    ax.plot(h_arr, rm_arr, marker="o", label="RM(h): left vs trapezoid")
    ax.plot(h_arr, ft_trap_arr, marker="s", label="FT defect: trapezoid")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("h")
    ax.set_ylabel("defect")
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()

    fig_svg = Path(args.fig_out)
    fig_svg.parent.mkdir(parents=True, exist_ok=True)
    fig_png = fig_svg.with_suffix(".png")
    fig.savefig(fig_svg, format="svg")
    fig.savefig(fig_png, format="png", dpi=200)
    plt.close(fig)

    notes_payload = {
        "timestamp": timestamp,
        "output_path": out_path.as_posix(),
        "figure_svg": fig_svg.as_posix(),
        "figure_png": fig_png.as_posix(),
        "params": {
            "N_list": args.N_list,
            "test_family": test_family,
            "norm": "l2",
            "epsilon0": args.eps0,
        },
        "results": {
            "rows": [
                [
                    int(r["N"]),
                    float(r["h"]),
                    float(r["rm_max"]),
                    float(r["ft_left_max"]),
                    float(r["ft_trap_max"]),
                ]
                for r in per_n_rows
            ],
            "fits": {
                "rm_max": {"slope": rm_slope, "r2": rm_r2},
                "ft_left_max": {"slope": ft_left_slope, "r2": ft_left_r2},
                "ft_trap_max": {"slope": ft_trap_slope, "r2": ft_trap_r2},
            },
            "rm_smallest_h": float(rm_arr[np.argmin(h_arr)]),
        },
    }
    notes_path = Path(args.notes_out)
    notes_path.parent.mkdir(parents=True, exist_ok=True)
    notes_path.write_text(json.dumps(notes_payload, indent=2) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
