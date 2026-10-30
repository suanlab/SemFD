"""E24 (pre-registered in literature/prereg_e24_group_baseline_2026-10-31.md): entity-group (modal) estimator
under a complete inverse, against the system, on E18's unary discovery setting.

Same candidates, oracles (complete inverse), alpha/|C|, confidence sequence, stopping rule and per-candidate random
streams as E1b/E18. Variants:
  plain   the system (hybrid proxy witness, audit over proxy neighbours U alias class); must equal E18 'plain'
  group   for a sampled tuple t: S = f_X^{-1}(f_X(t[X])) restricted to dom(X), G = tuples with X-value in S,
          B = 1 - (largest Y-entity count in G) / |G|; E[B] = g3 exactly. Every distinct Y-value in G is
          canonicalized (cached).
Output: results/icde27/e24_group_<dataset><tag>.json
"""

import argparse
import json
import resource
import sys
import time
import zlib
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semfd.certify import certify, eb_cs, g3_codes  # noqa: E402
from semfd.data import LOADERS  # noqa: E402
from semfd.oracle import calls_split, total_calls  # noqa: E402
from semfd.probes import base_attr as base  # noqa: E402


class Groups:
    """Per X-value code, the counts of Y-value codes among its tuples (no oracle calls)."""

    def __init__(self, ax, ay):
        self.ax, self.ay = ax, ay
        self.xidx = {v: i for i, v in enumerate(ax.vals)}
        order = np.lexsort((ay.codes, ax.codes))
        xs, ys = ax.codes[order], ay.codes[order]
        b = np.flatnonzero(np.r_[True, xs[1:] != xs[:-1], True])
        self.ycount = {}
        for s, e in zip(b[:-1], b[1:]):
            yv, cnt = np.unique(ys[s:e], return_counts=True)
            self.ycount[int(xs[s])] = list(zip(yv.tolist(), cnt.tolist()))

    def b_value(self, xi, fx, fy):
        """B_grp for a tuple whose X-value code is xi; charges calls through fx/fy (cached)."""
        same = {self.xidx[v] for v in fx.aliases(fx(self.ax.vals[xi])) if v in self.xidx} | {xi}
        tot, by_ent = 0, Counter()
        for xj in same:
            for yc, c in self.ycount.get(xj, ()):
                by_ent[fy(self.ay.vals[yc])] += c
                tot += c
        return 1.0 - max(by_ent.values()) / tot


def certify_group(ax, ay, fx, fy, delta, alpha, rng, max_n=20000, batch=100):
    """Same sequential test as semfd.certify.certify (one-sided EB CS, U < delta certifies, L >= delta stops)."""
    grp = Groups(ax, ay)
    c0 = fx.calls + (fy.calls if fy is not fx else 0)
    y0 = fy.calls
    n, bs, memo = len(ax.codes), [], {}
    lo = hi = np.array([0.0])
    while len(bs) < max_n:
        for t in rng.integers(0, n, size=min(batch, max_n - len(bs))):
            xi = int(ax.codes[t])
            if xi not in memo:
                memo[xi] = grp.b_value(xi, fx, fy)
            bs.append(memo[xi])
        lo, hi = eb_cs(bs, alpha)
        if hi[-1] < delta or lo[-1] >= delta:
            break
    calls = fx.calls + (fy.calls if fy is not fx else 0) - c0
    return {"certified": bool(hi[-1] < delta), "ub": min(1.0, float(hi[-1])), "lb": max(0.0, float(lo[-1])),
            "mean": float(np.mean(bs)), "samples": len(bs), "calls": int(calls),
            "y_calls": int(fy.calls - y0) if fy is not fx else None}


def run_variant(ds, attrs, cands, truth, delta, alpha, theta0, seed, name):
    orcs = ds.oracles(inverse=True)
    af = alpha / len(cands)
    t0 = time.perf_counter()
    cert, recs = set(), []
    for x, y in cands:
        rng = np.random.default_rng(zlib.crc32(f"e1b|{seed}|{x}|{y}".encode()))
        if name == "plain":
            r = certify(attrs[x], attrs[y], orcs[x], orcs[y], theta0, delta, af, rng, inverse=True)
        else:
            r = certify_group(attrs[x], attrs[y], orcs[x], orcs[y], delta, af, rng)
        if r["certified"]:
            cert.add((x, y))
        recs.append({"fd": f"{x}->{y}", "g3": float(truth[(x, y)]), "certified": r["certified"],
                     "samples": r["samples"], "calls": r["calls"], "y_calls": r.get("y_calls")})
    T = {c for c in cands if truth[c] <= delta}
    return {"false": sorted(f"{x}->{y}" for x, y in cert - T), "missed": sorted(f"{x}->{y}" for x, y in T - cert),
            "n_cert": len(cert), "calls": int(total_calls(orcs)), "calls_fwd_inv": calls_split(orcs),
            "canon_all": ds.canon_all_cost(attrs, list(attrs)), "sec": time.perf_counter() - t0, "fds": recs}


def run_one(ds, delta, alpha, theta0, k, seed, which):
    attrs = ds.attrs(proxy="hybrid", k=k)
    names = list(attrs)
    ent = ds.entity_codes(attrs)
    cands = [(x, y) for x in names for y in names if x != y and base(x) != base(y) and (x, y) not in ds.exclude]
    truth = {(x, y): g3_codes(ent[x][attrs[x].codes], ent[y][attrs[y].codes]) for x, y in cands}
    out = {}
    for name in which:
        r = run_variant(ds, attrs, cands, truth, delta, alpha, theta0, seed, name)
        out[name] = r
        print(f"{ds.name} seed={seed} {name}: false={r['false']} missed={r['missed']} calls={r['calls']} "
              f"{r['calls_fwd_inv']} canon_all={r['canon_all']} sec={r['sec']:.1f}", flush=True)
    return {"dataset": ds.name, "seed": seed, "rows": len(ds.df), "n_cands": len(cands),
            "n_true": sum(g <= delta for g in truth.values()), "variants": out}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="geonames")
    ap.add_argument("--kw", default="{}")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--theta0", type=float, default=0.9)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--tag", default="")
    ap.add_argument("--variants", nargs="+", default=["plain", "group"])
    a = ap.parse_args()
    outp = ROOT / f"results/icde27/e24_group_{a.dataset}{a.tag}.json"
    res = {"args": vars(a), "runs": []}
    for s in range(a.seeds):
        ds = LOADERS[a.dataset](seed=s, **json.loads(a.kw))
        res["runs"].append(run_one(ds, a.delta, a.alpha, a.theta0, a.k, s, a.variants))
        res["peak_rss_mb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        outp.write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
