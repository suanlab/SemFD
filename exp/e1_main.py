"""E1 (paper Sec. VI): correctness main table.

Per dataset x seed x candidate FD, records
  truth   g3 on the oracle-canonical instance (and label g3 <= delta)
  B0      exact AFD on Layer-1 strings (g3 <= delta)
  B1      proxy-quotient AFD per theta (g3 values; tau sweeps done in tables)
  ours    certificate at a PRE-DECLARED theta (alpha), the theta-grid variant
          (each theta at alpha/|grid|, Bonferroni, pick the cheapest certified),
          and the inverse-assisted variant (nu = 0 by Cor A2)
Oracle caches are shared across the FDs of one run (system setting); calls are
reported per FD (increment) and per run (total). Output:
results/icde27/e1_<dataset>.json
"""

import argparse
import json
import sys
import time
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semfd.baselines import canonicalize_all, pairwise_join, sample_only  # noqa: E402
from semfd.certify import certify, g3_codes, miss_mass  # noqa: E402
from semfd.data import LOADERS  # noqa: E402


def run_one(ds, delta, alpha, theta0, grid, k, proxy, seed, fwer=True, nu_bar=0.01):
    t0 = time.perf_counter()
    attrs = ds.attrs(proxy=proxy, k=k)
    t_proxy = time.perf_counter() - t0
    ent = ds.entity_codes(attrs)
    truth = ds.truth(attrs, ent)
    tol = sorted({a for fd in ds.fds for a in fd if not ds.exact[a]})
    out = {"dataset": ds.name, "meta": ds.meta, "seed": seed, "delta": delta, "alpha": alpha,
           "theta0": theta0, "grid": grid, "k": k, "proxy": proxy, "rows": len(ds.df),
           "distinct": {a: len(attrs[a].vals) for a in attrs},
           "canon_all": ds.canon_all_cost(attrs, tol), "proxy_sec": t_proxy, "fds": []}
    # Family-wise: per-FD level alpha/m (Bonferroni over the m candidates), so the
    # probability of ANY false certification in a run is <= alpha (Thm C needs it).
    af = alpha / len(ds.fds) if fwer else alpha
    out["alpha_per_fd"] = af
    variants = {  # primary = inverse (all Track A oracles are cluster/id-derived: Cor A2, nu = 0)
        "inverse": dict(thetas=[theta0], a=af, inverse=True, nu_bar=0.0, audit=True),
        "alias_only": dict(thetas=[theta0], a=af, inverse=True, nu_bar=0.0, audit=True, ann=False),
        "grid_inverse": dict(thetas=grid, a=af / len(grid), inverse=True, nu_bar=0.0, audit=True),
        "ann_nubar": dict(thetas=[theta0], a=af, inverse=False, nu_bar=nu_bar, audit=True),
        "b9_noaudit": dict(thetas=[theta0], a=af, inverse=False, nu_bar=0.0, audit=False)}
    orcs = {v: ds.oracles(inverse=cfg["inverse"]) for v, cfg in variants.items()}
    for x, y in ds.fds:
        ax, ay = attrs[x], attrs[y]
        rec = {"fd": f"{x}->{y}", "g3": truth[(x, y)], "truth": bool(truth[(x, y)] <= delta),
               "canon_cost": (0 if ds.exact[x] else len(ax.vals)) + (0 if ds.exact[y] else len(ay.vals)),
               "b0_exact_g3": g3_codes(ax.codes, ay.codes),
               "b1_quot_g3": {str(th): g3_codes(ax.partition(th)[ax.codes], ay.partition(th)[ay.codes])
                              for th in sorted(set(grid) | {theta0})},
               "ours": {}}
        for v, cfg in variants.items():
            fx, fy = orcs[v][x], orcs[v][y]
            best, spent = None, 0
            for th in cfg["thetas"]:           # stop at the first certified theta
                r = certify(ax, ay, fx, fy, th, delta, cfg["a"],
                            np.random.default_rng(zlib.crc32(f"{seed}|{x}|{y}|{th}".encode())),
                            inverse=cfg["inverse"], nu_bar=cfg["nu_bar"], audit=cfg["audit"],
                            ann=cfg.get("ann", True))
                spent += r["calls"]
                best = r
                if r["certified"]:
                    break
            best["calls"] = spent
            best["nu"] = miss_mass(ax, ay, ent[x], ent[y], best["theta"], inverse=cfg["inverse"])
            rec["ours"][v] = best
        fo = ds.oracles()
        rec["b4_canon_all"] = canonicalize_all(ax, ay, fo[x], fo[y])
        fo = ds.oracles()
        rec["b5_pairwise"] = pairwise_join(ax, ay, fo[x], fo[y])
        rec["b7_sample"] = []
        for m in sorted({rec["ours"]["inverse"]["samples"], 1000, 5000}):
            fo = ds.oracles()
            rec["b7_sample"].append(sample_only(ax, ay, fo[x], fo[y], m,
                                                np.random.default_rng(zlib.crc32(f"b7|{seed}|{x}|{y}|{m}".encode()))))
        out["fds"].append(rec)
    for v in variants:
        out[f"run_calls_{v}"] = int(sum(o.calls for o in {id(o): o for o in orcs[v].values()}.values()))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="geonames")
    ap.add_argument("--kw", default="{}", help="JSON kwargs for the loader")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--theta0", type=float, default=0.9)
    ap.add_argument("--grid", type=float, nargs="+", default=[0.85, 0.9, 0.95])
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--proxy", default="hybrid")
    ap.add_argument("--tag", default="")
    ap.add_argument("--no-fwer", action="store_true", help="per-FD alpha instead of alpha/m")
    ap.add_argument("--nu-bar", type=float, default=0.01, help="declared ANN miss mass (ann_nubar variant)")
    a = ap.parse_args()
    kw = json.loads(a.kw)
    res = []
    outp = ROOT / f"results/icde27/e1_{a.dataset}{a.tag}.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    for s in range(a.seeds):
        ds = LOADERS[a.dataset](seed=s, **kw)
        r = run_one(ds, a.delta, a.alpha, a.theta0, a.grid, a.k, a.proxy, s, not a.no_fwer, a.nu_bar)
        res.append(r)
        print(f"{ds.name} seed={s} rows={r['rows']} canon_all={r['canon_all']} "
              "run_calls " + " ".join(f"{v}={r['run_calls_' + v]}" for v in r["fds"][0]["ours"]), flush=True)
        for f in r["fds"]:
            o = f["ours"]
            print(f"  {f['fd']:<22} g3={f['g3']:.3f} T={f['truth']!s:<5} exact={f['b0_exact_g3']:.3f} "
                  + " ".join(f"{v}:{'C' if z['certified'] else '-'}/{z['calls']}/{z['ub']:.3f}/nu{z['nu']:.3f}"
                             for v, z in o.items()), flush=True)
        outp.write_text(json.dumps(res, indent=1))
