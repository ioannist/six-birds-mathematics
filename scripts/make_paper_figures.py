#!/usr/bin/env python3
"""Build the paper's data figures from the reviewed artifacts in notes/math_review/.

Outputs vector PDFs (TrueType-embedded fonts) under figures/paper/. Every plotted
value is read from a commit-visible JSON artifact; nothing is recomputed here
except medians/ranges over the stored stencil records.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REVIEW = Path("notes/math_review")
OUT = Path("figures/paper")

# Validated categorical slots (light mode), assigned in fixed order.
C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"

plt.rcParams.update({
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "font.family": "DejaVu Sans",
    "font.size": 8.5,
    "axes.labelsize": 8.5,
    "axes.titlesize": 9,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK2,
    "axes.linewidth": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.5,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.minor.width": 0.4,
    "ytick.minor.width": 0.4,
    "lines.linewidth": 1.5,
    "lines.markersize": 4.5,
    "legend.frameon": False,
    "legend.fontsize": 8,
    "text.color": INK,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.03,
})


def load(name: str) -> dict:
    return json.loads((REVIEW / name).read_text())


def label_end(ax, x, y, text, color=INK2, dx=4, dy=0, ha="left"):
    ax.annotate(text, (x, y), xytext=(dx, dy), textcoords="offset points",
                color=color, fontsize=7.5, va="center", ha=ha)


def save(fig, name: str) -> None:
    fig.savefig(OUT / f"{name}.pdf")
    fig.savefig(OUT / f"{name}.png", dpi=200)
    plt.close(fig)


def stencil() -> None:
    d = load("stencil_matched_controls.json")
    recs = d["records"]
    n0 = d["params"]["N0"]
    hs = np.array([1 / n0, 1 / (2 * n0), 1 / (4 * n0)])
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(6.6, 2.6), gridspec_kw={"width_ratios": [1.25, 1]})
    colors = [C1, C2, C3]
    markers = ["o", "s", "^"]
    names = ["order 0 (identity-like)", "order 1 (first derivative)", "order 2 (second derivative)"]
    for k in range(3):
        D = np.array([[r["D0"], r["D1"], r["D2"]] for r in recs if r["scale_order"] == k])
        med = np.median(D, axis=0)
        ax.fill_between(hs, D.min(axis=0), D.max(axis=0), color=colors[k], alpha=0.15, lw=0)
        ax.plot(hs, med, color=colors[k], marker=markers[k])
    ax.axhline(d["params"]["D2_max"], color=MUTED, lw=0.8, ls="--")
    ax.text(hs[0], d["params"]["D2_max"] * 0.8, "Leibniz gate (finest grid)", color=INK2,
            fontsize=7, ha="right", va="top")
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xlim(hs[-1] / 1.15, hs[0] * 1.15)
    ax.set_xticks(hs, [f"1/{round(1 / v)}" for v in hs])
    ax.minorticks_off()
    ax.set_xlabel("grid step $h$")
    ax.set_ylabel("normalized Leibniz defect")
    ax.set_title("(a) Leibniz defect under refinement")
    ax.set_ylim(3e-8, 3)
    ax.text(hs[1], 0.75, "order 2: stays at 1/2", color=INK2, fontsize=7, ha="center", va="bottom")
    ax.text(hs[1], 0.24, "order 0: stays at 1/3", color=INK2, fontsize=7, ha="center", va="top")
    ax.text(hs[1], 1.1e-6, "order 1: decays like $h^3$", color=INK2, fontsize=7, ha="center", va="top")
    ax.grid(True, which="major")

    before = d["stability_only_by_best_fit_k"]
    after = d["stability_and_leibniz_by_best_fit_k"]
    x = np.arange(3)
    w = 0.36
    for k in range(3):
        b, a = before[str(k)], after[str(k)]
        bx.bar(x[k] - w / 2 - 0.01, b, w, color=colors[k], alpha=0.35, lw=0)
        bx.bar(x[k] + w / 2 + 0.01, a, w, color=colors[k], lw=0)
        bx.text(x[k] - w / 2 - 0.01, b + 2, str(b), ha="center", va="bottom", fontsize=7.5, color=INK2)
        bx.text(x[k] + w / 2 + 0.01, a + 2, str(a), ha="center", va="bottom", fontsize=7.5, color=INK2)
    bx.set_xticks(x, ["$k=0$", "$k=1$", "$k=2$"])
    bx.set_ylim(0, 140)
    bx.set_ylabel("survivors (of 100 per order)")
    bx.set_xlabel("best-fit template order")
    bx.set_title("(b) Survivors by gate")
    bx.grid(False, axis="x")
    from matplotlib.patches import Patch
    bx.legend(handles=[Patch(color=MUTED, alpha=0.35, lw=0, label="stability only"),
                       Patch(color=MUTED, lw=0, label="stability + Leibniz")],
              loc="upper center", ncols=2, handlelength=1.2, columnspacing=1.0)
    handles = [plt.Line2D([], [], color=colors[k], marker=markers[k], label=names[k]) for k in range(3)]
    fig.legend(handles=handles, loc="lower center", ncols=3, bbox_to_anchor=(0.5, -0.07))
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    save(fig, "fig_stencil_matched")


def integration() -> None:
    rows = load("integration_run.json")["results"]["rows"]
    h = np.array([r["h"] for r in rows])
    series = [
        ("rm_max", "route mismatch RM", C1, "o", "slope 1"),
        ("ft_trap_max", "trapezoid FT defect (raw $\\ell^2$)", C2, "s", "slope 1/2"),
        ("integral_left_weighted_l2_error_max", "left rule vs exact", C3, "^", "slope 1"),
        ("integral_trap_weighted_l2_error_max", "trapezoid vs exact", C4, "D", "slope 2"),
    ]
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    for key, name, c, mk, slope in series:
        y = np.array([r[key] for r in rows])
        ax.plot(h, y, color=c, marker=mk, label=name)
        label_end(ax, h[0], y[0], slope, color=INK2, dx=6, dy={"rm_max": 3, "integral_left_weighted_l2_error_max": -3}.get(key, 0))
    left = np.array([r["ft_left_max"] for r in rows])
    ax.plot(h, left, color=MUTED, marker="x", ls=":", lw=1.0, label="left FT residual (roundoff only)")
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xlim(h[-1] / 1.3, h[0] * 2.0)
    ax.set_xticks(h, [f"1/{round(1 / v)}" for v in h])
    ax.minorticks_off()
    ax.set_xlabel("grid step $h$")
    ax.set_ylabel("maximum over test family")
    ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5))
    save(fig, "fig_integration")


def holonomy() -> None:
    d = load("holonomy_run.json")
    res = d["results"]
    h = np.array([r["h"] for r in res])
    rm = np.array([r["rm"] for r in res])
    ea = np.array([r["route_A_rms_error"] for r in res])
    eb = np.array([r["route_B_rms_error"] for r in res])
    p, c = d["fit"]["p"], d["fit"]["c"]
    fig, ax = plt.subplots(figsize=(4.6, 2.9))
    ax.plot(h, rm, color=C1, marker="o", label="relative route mismatch RM$(h)$")
    hh = np.geomspace(h[-1], h[0], 50)
    ax.plot(hh, np.exp(c) * hh**p, color=C1, lw=0.8, ls="--", alpha=0.8)
    label_end(ax, h[0], rm[0], f"fit $p={p:.2f}$", dx=6)
    ax.plot(h, ea, color=C2, marker="s", label="route A error vs exact $g'(\\varphi)$")
    ax.plot(h, eb, color=C3, marker="^", label="route B error vs exact $g'(\\varphi)$")
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xlim(h[-1] / 1.3, h[0] * 2.2)
    ax.set_xticks(h, [f"1/{round(1 / v)}" for v in h])
    ax.minorticks_off()
    ax.set_xlabel("grid step $h$")
    ax.set_ylabel("relative mismatch / RMS error")
    ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5))
    save(fig, "fig_holonomy")


def prime() -> None:
    d = load("prime_run.json")
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.6))
    titles = {"conv": "(a) $\\Re(s)>1$, one-sided completion",
              "strip": "(b) $0<\\Re(s)<1$, symmetrized completion"}
    for ax, key in zip(axes, ["conv", "strip"]):
        rows = d["results"][key]
        N = np.array([r["N"] for r in rows])
        for k, name, c, mk in [("rm2", "$\\mathrm{RM}_2$ (route mismatch)", C1, "o"),
                               ("errS2", "$\\mathrm{Err}_S$ (additive vs $\\zeta$)", C2, "s"),
                               ("errP2", "$\\mathrm{Err}_P$ (Euler vs $\\zeta$)", C3, "^")]:
            ax.plot(N, [r[k] for r in rows], color=c, marker=mk, label=name)
        ax.set_xscale("log", base=2)
        ax.set_yscale("log")
        ax.set_xticks(N, [str(n) for n in N])
        ax.minorticks_off()
        ax.set_xlabel("cutoff $N$")
        ax.set_title(titles[key], fontsize=8.5)
    axes[0].set_ylabel("relative $\\ell^2$ diagnostic")
    axes[0].set_ylim(0.03, 0.4)
    axes[0].set_yticks([0.05, 0.1, 0.2], ["0.05", "0.1", "0.2"])
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncols=3, bbox_to_anchor=(0.5, -0.07))
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    save(fig, "fig_prime")


def passivity() -> None:
    d = load("passivity_run.json")
    res = {float(r["lambda"]): r for r in d["results"]}
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(6.6, 2.7), gridspec_kw={"width_ratios": [1.3, 1]})
    for lam, c, mk in [(1.0, C1, "o"), (0.4, C2, "s"), (0.0, C3, "^")]:
        z = np.array([complex(a, b) for a, b in res[lam]["roots"]])
        arg = np.angle(z)
        arg = np.where(arg < -np.pi + 1e-9, np.pi, arg)
        ax.scatter(arg, np.abs(z), color=c, marker=mk, s=22 if lam else 30, zorder=3,
                   edgecolors="white", linewidths=0.6, label=f"$\\lambda={lam:g}$")
    ax.axhline(1.0, color=INK2, lw=0.8)
    ax.text(0, 1.15, "unit circle $|z|=1$", color=INK2, fontsize=7, ha="center")
    ax.set_yscale("log")
    ax.set_xlim(-3.3, 3.3)
    ax.set_xticks([-np.pi, -np.pi / 2, 0, np.pi / 2, np.pi], ["$-\\pi$", "$-\\pi/2$", "0", "$\\pi/2$", "$\\pi$"])
    ax.set_xlabel("argument of zero")
    ax.set_ylabel("modulus $|z|$")
    ax.set_title("(a) Zeros of $Z_\\lambda$")
    ax.legend(loc="lower left", ncols=3, handletextpad=0.2, columnspacing=0.8)
    ax.set_ylim(0.08, 15)

    lams = np.array(sorted(res, reverse=True))
    mean = np.array([res[l]["mean_dev"] for l in lams])
    mx = np.array([res[l]["max_dev"] for l in lams])
    bx.axhspan(1e-17, 1e-13, color=GRID, lw=0)
    bx.text(0.5, 1.2e-16, "floating-point roundoff", color=INK2, fontsize=7, ha="center")
    bx.plot(lams, mx, color=C1, marker="o", label="max_dev")
    bx.plot(lams, mean, color=C2, marker="s", label="mean_dev")
    bx.set_yscale("log")
    bx.set_ylim(3e-17, 30)
    bx.set_xlim(1.05, -0.05)
    bx.set_xlabel("$\\lambda$ (1 = mixed signs, 0 = nonnegative)")
    bx.set_ylabel("radial deviation from $|z|=1$")
    bx.set_title("(b) Distance from the circle")
    bx.legend(loc="center left")
    fig.tight_layout()
    save(fig, "fig_passivity")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    stencil()
    integration()
    holonomy()
    prime()
    passivity()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
