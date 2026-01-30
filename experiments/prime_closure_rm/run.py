#!/usr/bin/env python3
"""Prime closure RM experiment with convergence control region."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import mpmath as mp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def primes_upto(n: int) -> List[int]:
    if n < 2:
        return []
    sieve = bytearray(b"\x01") * (n + 1)
    sieve[0:2] = b"\x00\x00"
    p = 2
    while p * p <= n:
        if sieve[p]:
            step = p
            start = p * p
            sieve[start : n + 1 : step] = b"\x00" * ((n - start) // step + 1)
        p += 1
    return [i for i in range(2, n + 1) if sieve[i]]


def S_N(s: mp.mpc, N: int, smooth: str) -> mp.mpc:
    total = mp.mpc(0)
    if smooth == "none":
        for n in range(1, N + 1):
            total += mp.power(n, -s)
    else:
        for n in range(1, N + 1):
            total += mp.e ** (-n / N) * mp.power(n, -s)
    return total


def P_N(s: mp.mpc, N: int, smooth: str, primes: List[int]) -> mp.mpc:
    logp = mp.mpc(0)
    if smooth == "none":
        for p in primes:
            logp += -mp.log(1 - mp.power(p, -s))
    else:
        for p in primes:
            logp += mp.e ** (-p / N) * (-mp.log(1 - mp.power(p, -s)))
    return mp.e ** (logp)


def C_factor(s: mp.mpc) -> mp.mpc:
    return (
        mp.mpf("0.5")
        * s
        * (s - 1)
        * mp.power(mp.pi, -s / 2)
        * mp.gamma(s / 2)
    )


def apply_mode(valF: mp.mpc, s: mp.mpc, mode: str) -> mp.mpc:
    if mode == "raw":
        return valF
    if mode == "comp":
        return C_factor(s) * valF
    raise ValueError(f"unsupported mode: {mode}")


def apply_mode_sym(F, s: mp.mpc, mode: str) -> mp.mpc:
    if mode == "sym":
        return mp.mpf("0.5") * (C_factor(s) * F(s) + C_factor(1 - s) * F(1 - s))
    return apply_mode(F(s), s, mode)


def apply_true(s: mp.mpc, mode: str) -> mp.mpc:
    z = mp.zeta(s)
    if mode == "sym":
        z1 = mp.zeta(1 - s)
        return mp.mpf("0.5") * (C_factor(s) * z + C_factor(1 - s) * z1)
    if mode == "comp":
        return C_factor(s) * z
    return z


def trend_counts(values: List[float]) -> Dict[str, object]:
    steps = 0
    for i in range(1, len(values)):
        if values[i] < values[i - 1]:
            steps += 1
    return {"decrease_steps": steps, "any_decrease": steps > 0}


def eval_region(
    N_list: List[int],
    points: List[mp.mpc],
    mode: str,
    smooth: str,
    eps: float,
) -> Tuple[List[Dict[str, float]], Dict[str, Dict[str, object]]]:
    results: List[Dict[str, float]] = []
    rm2_vals: List[float] = []
    errS_vals: List[float] = []
    errP_vals: List[float] = []

    for N in N_list:
        primes = primes_upto(N)

        def F_S(s: mp.mpc) -> mp.mpc:
            return S_N(s, N, smooth)

        def F_P(s: mp.mpc) -> mp.mpc:
            return P_N(s, N, smooth, primes)

        S_vals = []
        P_vals = []
        T_vals = []
        for s in points:
            if mode == "sym":
                S_vals.append(apply_mode_sym(F_S, s, mode))
                P_vals.append(apply_mode_sym(F_P, s, mode))
            else:
                S_vals.append(apply_mode(F_S(s), s, mode))
                P_vals.append(apply_mode(F_P(s), s, mode))
            T_vals.append(apply_true(s, mode))

        diffs = [abs(a - b) for a, b in zip(S_vals, P_vals)]
        normS2 = mp.sqrt(sum(abs(a) ** 2 for a in S_vals))
        normT2 = mp.sqrt(sum(abs(a) ** 2 for a in T_vals))
        normSinf = max(abs(a) for a in S_vals)
        rm2 = float(mp.sqrt(sum(d * d for d in diffs)) / (normS2 + eps))
        rminf = float(max(diffs) / (normSinf + eps))

        errS2 = float(
            mp.sqrt(sum(abs(a - b) ** 2 for a, b in zip(S_vals, T_vals)))
            / (normT2 + eps)
        )
        errP2 = float(
            mp.sqrt(sum(abs(a - b) ** 2 for a, b in zip(P_vals, T_vals)))
            / (normT2 + eps)
        )

        results.append(
            {
                "N": int(N),
                "rm2": rm2,
                "rminf": rminf,
                "errS2": errS2,
                "errP2": errP2,
            }
        )
        rm2_vals.append(rm2)
        errS_vals.append(errS2)
        errP_vals.append(errP2)

    trends = {
        "rm2": trend_counts(rm2_vals),
        "errS2": trend_counts(errS_vals),
        "errP2": trend_counts(errP_vals),
    }
    return results, trends


def main() -> int:
    parser = argparse.ArgumentParser(description="Prime closure RM experiment (control)")
    parser.add_argument("--N-list", nargs="+", type=int, default=[50, 100, 200, 400, 800])
    parser.add_argument("--t-list", nargs="+", type=float, default=[0.0, 2.0, 4.0, 6.0])
    parser.add_argument("--sigma-conv-list", nargs="+", type=float, default=[1.25, 1.50])
    parser.add_argument("--sigma-strip-list", nargs="+", type=float, default=[0.75, 0.50])
    parser.add_argument("--compute-strip", dest="compute_strip", action="store_true")
    parser.add_argument("--no-compute-strip", dest="compute_strip", action="store_false")
    parser.set_defaults(compute_strip=True)
    parser.add_argument("--compute-conv", dest="compute_conv", action="store_true")
    parser.add_argument("--no-compute-conv", dest="compute_conv", action="store_false")
    parser.set_defaults(compute_conv=True)
    parser.add_argument("--mode-conv", choices=["raw", "comp"], default="comp")
    parser.add_argument("--mode-strip", choices=["raw", "comp", "sym"], default="sym")
    parser.add_argument("--smooth", choices=["none", "exp"], default="exp")
    parser.add_argument("--dps", type=int, default=50)
    parser.add_argument("--eps", type=float, default=1e-30)
    parser.add_argument("--out", type=str, default=None)
    parser.add_argument("--notes-out", type=str, default="notes/prime_closure_rm_last_run.json")
    parser.add_argument("--fig-out", type=str, default="figures/prime_closure_rm_last_run.svg")
    args = parser.parse_args()

    mp.mp.dps = args.dps

    print(
        "params: N_list={N_list}, sigma_conv={sigma_conv}, sigma_strip={sigma_strip}, "
        "t_list={t_list}, smooth={smooth}, dps={dps}, mode_conv={mode_conv}, mode_strip={mode_strip}".format(
            N_list=args.N_list,
            sigma_conv=args.sigma_conv_list,
            sigma_strip=args.sigma_strip_list,
            t_list=args.t_list,
            smooth=args.smooth,
            dps=args.dps,
            mode_conv=args.mode_conv,
            mode_strip=args.mode_strip,
        )
    )

    K_conv: List[Dict[str, float]] = []
    K_strip: List[Dict[str, float]] = []
    points_conv: List[mp.mpc] = []
    points_strip: List[mp.mpc] = []

    for sigma in args.sigma_conv_list:
        for t in args.t_list:
            K_conv.append({"sigma": float(sigma), "t": float(t)})
            points_conv.append(mp.mpc(sigma, t))

    for sigma in args.sigma_strip_list:
        for t in args.t_list:
            K_strip.append({"sigma": float(sigma), "t": float(t)})
            points_strip.append(mp.mpc(sigma, t))

    results: Dict[str, List[Dict[str, float]]] = {}
    trend: Dict[str, Dict[str, Dict[str, object]]] = {}

    if args.compute_conv:
        conv_results, conv_trend = eval_region(
            args.N_list, points_conv, args.mode_conv, args.smooth, args.eps
        )
        results["conv"] = conv_results
        trend["conv"] = conv_trend

    if args.compute_strip:
        strip_results, strip_trend = eval_region(
            args.N_list, points_strip, args.mode_strip, args.smooth, args.eps
        )
        results["strip"] = strip_results
        trend["strip"] = strip_trend

    print("RM table (conv):")
    if "conv" in results:
        for row in results["conv"]:
            print(
                f"  N={row['N']}: rm2={row['rm2']:.6e}, errS2={row['errS2']:.6e}, errP2={row['errP2']:.6e}"
            )
    print("RM table (strip):")
    if "strip" in results:
        for row in results["strip"]:
            print(
                f"  N={row['N']}: rm2={row['rm2']:.6e}, errS2={row['errS2']:.6e}, errP2={row['errP2']:.6e}"
            )

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = (
        Path(args.out)
        if args.out
        else Path("data/runs") / f"prime_closure_rm_control_{timestamp}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "timestamp": timestamp,
        "params": {
            "N_list": args.N_list,
            "sigma_conv_list": args.sigma_conv_list,
            "sigma_strip_list": args.sigma_strip_list,
            "t_list": args.t_list,
            "smooth": args.smooth,
            "dps": args.dps,
            "mode_conv": args.mode_conv,
            "mode_strip": args.mode_strip,
        },
        "K_conv": K_conv,
        "K_strip": K_strip,
        "results": results,
        "trend": trend,
    }
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # Figure: RM2 curves
    fig, ax = plt.subplots(figsize=(5, 3))
    if "conv" in results:
        ax.plot(
            [row["N"] for row in results["conv"]],
            [row["rm2"] for row in results["conv"]],
            label="conv",
        )
    if "strip" in results:
        ax.plot(
            [row["N"] for row in results["strip"]],
            [row["rm2"] for row in results["strip"]],
            label="strip",
        )
    ax.set_xlabel("N")
    ax.set_ylabel("RM2")
    ax.set_xscale("log")
    ax.set_yscale("log")
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

    conv_table = []
    strip_table = []
    if "conv" in results:
        conv_table = [
            [row["N"], round(row["rm2"], 8), round(row["errS2"], 8), round(row["errP2"], 8)]
            for row in results["conv"]
        ]
    if "strip" in results:
        strip_table = [
            [row["N"], round(row["rm2"], 8), round(row["errS2"], 8), round(row["errP2"], 8)]
            for row in results["strip"]
        ]

    trend_summary = ""
    if "conv" in trend:
        trend_summary += (
            f"conv rm2 decreases: {trend['conv']['rm2']['decrease_steps']}; "
        )
    if "strip" in trend:
        trend_summary += (
            f"strip rm2 decreases: {trend['strip']['rm2']['decrease_steps']}"
        )
    trend_summary = trend_summary.strip()

    notes_payload = {
        "timestamp": timestamp,
        "output_path": out_path.as_posix(),
        "figure_path": fig_path.as_posix(),
        "figure_png_path": png_path.as_posix(),
        "conv_table": conv_table,
        "strip_table": strip_table,
        "trend_summary": trend_summary,
        "params": {
            "N_list": args.N_list,
            "sigma_conv_list": args.sigma_conv_list,
            "sigma_strip_list": args.sigma_strip_list,
            "t_list": args.t_list,
            "mode_conv": args.mode_conv,
            "mode_strip": args.mode_strip,
            "smooth": args.smooth,
            "dps": args.dps,
        },
    }
    Path(args.notes_out).write_text(json.dumps(notes_payload, indent=2) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
