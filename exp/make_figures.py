"""Paper figures from results/icde27/*.json -> paper/fig_*.pdf.
Palette: dataviz reference slots 1-3 (validated; slot 3 has <3:1 contrast, so
every series is also direct-labelled and has its own marker shape)."""

import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
R, OUT = ROOT / "results/icde27", ROOT / "paper"
C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
ALLOW_PARTIAL = "--allow-partial" in sys.argv     # otherwise a missing input is an error, not a silently thinner figure


def need(p):
    if p.exists():
        return True
    if ALLOW_PARTIAL:
        print(f"skipping missing {p}", file=sys.stderr)
        return False
    raise FileNotFoundError(f"{p} is required (run its experiment, or pass --allow-partial)")


plt.rcParams.update({"font.size": 8, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
                     "lines.linewidth": 2, "pdf.fonttype": 42})


def fig_scale():
    runs = json.loads((R / "e2_geonames.json").read_text())
    by = defaultdict(list)
    for r in runs:
        by[r["n_cities"]].append(r)
    C = np.array(sorted(by))
    rows = np.array([by[c][0]["rows"] for c in C])
    ours = np.array([np.mean([r["run_calls"] for r in by[c]]) for c in C])
    canon = np.array([np.mean([r["canon_all"] for r in by[c]]) for c in C])
    pairs = np.array([np.mean([sum(f["b5_pairwise"]["calls"] for f in r["fds"]) for r in by[c]]) for c in C])
    fig, ax = plt.subplots(figsize=(3.4, 2.3))
    for y, col, mk, lab in ((pairs, C3, "s", "pairwise self-join (pair judgements)"),
                            (canon, C2, "^", "canonicalize-all"), (ours, C1, "o", "certificate (ours)")):
        ax.plot(rows, y, color=col, marker=mk, markersize=5, markeredgecolor="white", markeredgewidth=1)
        values = [[sum(f["b5_pairwise"]["calls"] for f in rr["fds"]) if mk == "s"
                   else rr["canon_all"] if mk == "^" else rr["run_calls"] for rr in by[c]] for c in C]
        ax.fill_between(rows, [min(v) for v in values], [max(v) for v in values], color=col, alpha=.15)
        ax.annotate(lab, (rows[-1], y[-1]), xytext=(-4, 6), textcoords="offset points", ha="right",
                    color=INK, fontsize=7)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("rows (GeoNames, 5 per city on average)")
    ax.set_ylabel("oracle calls per run")
    ax.grid(True, which="major", color=GRID, linewidth=0.6)
    fig.tight_layout()
    fig.savefig(OUT / "fig_e2_scale.pdf")


def fig_power():
    fig, ax = plt.subplots(figsize=(3.4, 2.3))
    for name, col, mk in (("geonames", C1, "o"), ("tax", C2, "^")):
        p = R / f"e3_{name}.json"
        if not need(p):
            continue
        e = json.loads(p.read_text())
        pts = sorted((f["EB"], f["cert_rate"], f["false_cert_rate"]) for f in e["fds"] if f["EB"] < 0.12)
        g, c, fc = map(np.array, zip(*pts))
        z, n = 1.959963984540054, e["reps"]
        center = (c + z*z/(2*n))/(1+z*z/n)
        half = z*np.sqrt(c*(1-c)/n + z*z/(4*n*n))/(1+z*z/n)
        ax.errorbar(g, c, yerr=np.vstack([c-(center-half), (center+half)-c]).clip(min=0),
                    fmt="none", ecolor=col, capsize=2, linewidth=.8)
        ax.plot(g, c, color=col, marker=mk, markersize=5, markeredgecolor="white", markeredgewidth=1,
                linestyle="none", label={"geonames": "GeoNames 4k", "tax": "Tax 200k"}[name])
    d = e["delta"]
    ax.axvline(d, color=MUTED, linewidth=1, linestyle="--")
    ax.annotate(f"δ = {d}", (d, 0.3), xytext=(4, 0), textcoords="offset points", color=MUTED, fontsize=7)
    ax.legend(frameon=False, loc="upper right", fontsize=7, labelcolor=INK)
    ax.set_xlabel("$\\mathbb{E}[B]$ (upper bound on oracle $g_3$) of the FD")
    ax.set_ylabel(f"certified rate ({e['reps']} runs)")
    ax.set_ylim(-0.03, 1.05)
    ax.grid(True, color=GRID, linewidth=0.6)
    fig.tight_layout()
    fig.savefig(OUT / "fig_e3_power.pdf")


def fig_cost():
    """Our oracle calls split into forward + inverse vs canonicalize-all (E1b unary, E9 two-attribute)."""
    rows = []
    for key, nice in (("geonames_16k", "Geo"), ("tax", "Tax"), ("ndc", "NDC")):
        for kind, f, fk, ck in (("unary", f"e1b_{key}.json", "ours_calls_fwd_inv", "canon_all"),
                                ("2-attr", f"e9_{key}.json", "calls_fwd_inv", "canon_all")):
            p = R / f
            if not need(p):
                continue
            runs = json.loads(p.read_text())
            if fk not in runs[0]:
                raise KeyError(f"{p} has no {fk}: rerun its experiment")
            fw = np.mean([r[fk][0] for r in runs])
            iv = np.mean([r[fk][1] for r in runs])
            rows.append((f"{nice}\n{kind}", fw, iv, np.mean([r[ck] for r in runs])))
    if not rows:
        return
    fig, ax = plt.subplots(figsize=(3.4, 2.2))
    x = np.arange(len(rows))
    w = 0.38
    ax.bar(x - w / 2 - 0.01, [r[1] for r in rows], w, color=C1, label="ours: forward")
    ax.bar(x - w / 2 - 0.01, [r[2] for r in rows], w, bottom=[r[1] for r in rows], color=C3, label="ours: inverse")
    ax.bar(x + w / 2 + 0.01, [r[3] for r in rows], w, color=C2, label="canonicalize-all", hatch="////",
           edgecolor="white", linewidth=0)
    ax.set_xticks(x, [r[0] for r in rows], fontsize=6.5)
    ax.set_ylabel("oracle calls per run")
    ax.legend(frameon=False, fontsize=6.5, labelcolor=INK)
    ax.grid(True, axis="y", color=GRID, linewidth=0.6)
    fig.tight_layout()
    fig.savefig(OUT / "fig_cost.pdf")


if __name__ == "__main__":
    fig_scale()
    fig_power()
    fig_cost()
    print("ok")
