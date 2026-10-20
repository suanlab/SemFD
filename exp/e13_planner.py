"""E13 (paper Sec. V-VI, "Planner"): the run-level planner, charging forward and inverse calls.

Runs semfd.planner.RunPlanner over the same candidate sets, oracles and random streams as E1b (all unary
candidates) and E9 (two-attribute left-hand sides), and records decisions against the oracle truth, oracle calls
(forward + inverse), how many candidates and oracles were resolved outright, and canonicalize-all.
The certificate-only numbers are in e1b_*.json / e9_*.json. Output: results/icde27/e13_planner_<dataset><tag>.json
"""

import argparse
import itertools
import json
import sys
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semfd.certify import certify, g3_codes  # noqa: E402
from semfd.composite import CompositeAttr  # noqa: E402
from semfd.data import LOADERS  # noqa: E402
from semfd.oracle import calls_split, total_calls  # noqa: E402
from semfd.planner import RunPlanner  # noqa: E402
from semfd.probes import base_attr as base, is_probe_attr  # noqa: E402


def combo(codes):
    return np.unique(np.stack(codes, 1), axis=0, return_inverse=True)[1].ravel()


def run_one(ds, mode, delta, alpha, theta0, k, seed, pilot):
    attrs = ds.attrs(k=k)
    ent = ds.entity_codes(attrs)
    if mode == "unary":
        names = list(attrs)
        cands = [((x,), y) for x in names for y in names if x != y and base(x) != base(y)]
        key = lambda lhs, y: f"e1b|{seed}|{lhs[0]}|{y}"
    else:
        names = [a for a in ds.exact if not is_probe_attr(a)]
        cands = [(lhs, y) for lhs in itertools.combinations(names, 2) for y in names if y not in lhs]
        key = lambda lhs, y: f"e9|{seed}|{'+'.join(lhs)}|{y}"
    orcs = ds.oracles(inverse=True)
    plan = RunPlanner(orcs, {a: attrs[a].vals for a in names}, [lhs + (y,) for lhs, y in cands], pilot=pilot)
    af = alpha / len(cands)
    comp = {}

    def ids(a):
        f, m = orcs[a], {}
        return np.array([m.setdefault(f(v), len(m)) for v in attrs[a].vals])

    recs, T, C = [], set(), set()
    for lhs, y in cands:
        if len(lhs) == 1:
            ax = attrs[lhs[0]]
            xo = orcs[lhs[0]]
            g3 = g3_codes(ent[lhs[0]][ax.codes], ent[y][attrs[y].codes])
        else:
            if lhs not in comp:
                comp[lhs] = CompositeAttr([attrs[a] for a in lhs])
            ax = comp[lhs]
            xo = ax.oracle([orcs[a] for a in lhs])
            g3 = g3_codes(combo([ent[a][attrs[a].codes] for a in lhs]), ent[y][attrs[y].codes])
        rng = np.random.default_rng(zlib.crc32(key(lhs, y).encode()))
        r = plan.decide(lhs + (y,), delta,
                        lambda cap: certify(ax, attrs[y], xo, orcs[y], theta0, delta, af, rng, inverse=True,
                                            max_calls=cap),
                        lambda: g3_codes(combo([ids(a)[attrs[a].codes] for a in lhs]), ids(y)[attrs[y].codes]))
        name = f"{'+'.join(lhs)}->{y}"
        if g3 <= delta:
            T.add(name)
        if r["certified"]:
            C.add(name)
        recs.append({"fd": name, "g3": float(g3), "mode": r["mode"], "certified": r["certified"], "ub": r["ub"]})
    inv = {id(o): a for a, o in orcs.items()}
    return {"dataset": ds.name, "mode": mode, "seed": seed, "rows": len(ds.df), "n_cands": len(cands), "n_true": len(T),
            "false": sorted(C - T), "missed": sorted(T - C), "calls": total_calls(orcs), "calls_fwd_inv": calls_split(orcs),
            "canon_all": ds.canon_all_cost(attrs, names), "resolved_cands": plan.n_resolved_cands,
            "resolved_oracles": sorted(inv[k] for k in plan.res),
            "budget": {inv[k]: v for k, v in plan.R.items()}, "pilot": pilot, "fds": recs}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="geonames")
    ap.add_argument("--kw", default="{}")
    ap.add_argument("--mode", choices=["unary", "pairs"], default="unary")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--theta0", type=float, default=0.9)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--pilot", type=int, default=5)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    out = ROOT / f"results/icde27/e13_planner_{a.dataset}{a.tag}_{a.mode}.json"
    res = []
    for s in range(a.seeds):
        ds = LOADERS[a.dataset](seed=s, **json.loads(a.kw))
        r = run_one(ds, a.mode, a.delta, a.alpha, a.theta0, a.k, s, a.pilot)
        res.append(r)
        print(f"{ds.name} {a.mode} seed={s} false={len(r['false'])} missed={len(r['missed'])} calls={r['calls']} "
              f"{r['calls_fwd_inv']} canon_all={r['canon_all']} resolved cands={r['resolved_cands']}/{r['n_cands']} "
              f"oracles={r['resolved_oracles']}", flush=True)
        out.write_text(json.dumps(res, indent=1))
