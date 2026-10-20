"""E9: FDs with a two-attribute left-hand side, {A, B} -> Y.

Candidates: all unordered pairs of non-probe attributes and every other non-probe
attribute as RHS. Truth = g3 on the oracle-canonical instance <= delta.
  B3   Desbordante Tane (g3 <= delta, max_lhs = 2) on raw strings: X -> Y is
       accepted if a discovered FD has LHS subset of X and RHS Y.
  ours certificate with composite oracle/partition/neighbours (semfd.composite),
       inverse blocking (nu = 0), family-wise alpha / m, shared component caches.
Output: results/icde27/e9_<dataset><tag>.json
"""

import argparse
import itertools
import json
import sys
import time
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semfd.certify import certify, g3_codes  # noqa: E402
from semfd.composite import CompositeAttr  # noqa: E402
from semfd.data import LOADERS  # noqa: E402
from semfd.oracle import calls_split, total_calls  # noqa: E402
from semfd.probes import is_probe_attr  # noqa: E402



def tane2(df, delta):
    import desbordante
    a = desbordante.afd.algorithms.Tane()
    a.load_data(table=df.astype(str))
    a.execute(error=delta, max_lhs=2, afd_error_measure="g3")
    cols = list(df.columns)
    return [(frozenset(cols[i] for i in f.lhs_indices), cols[f.rhs_index]) for f in a.get_fds()]


def run_one(ds, delta, alpha, theta0, seed):
    names = [a for a in ds.exact if not is_probe_attr(a)]
    attrs = ds.attrs()
    ent = ds.entity_codes(attrs)
    orcs = ds.oracles(inverse=True)
    cands = [(lhs, y) for lhs in itertools.combinations(names, 2) for y in names if y not in lhs]
    t0 = time.perf_counter()
    found = tane2(ds.df[names], delta)
    t_tane = time.perf_counter() - t0
    af = alpha / len(cands)
    recs = []
    comp_cache = {}
    t1 = time.perf_counter()
    for lhs, y in cands:
        if lhs not in comp_cache:
            comp_cache[lhs] = CompositeAttr([attrs[a] for a in lhs])
        cx = comp_cache[lhs]
        xo = cx.oracle([orcs[a] for a in lhs])
        xent = np.unique(np.stack([ent[a][attrs[a].codes] for a in lhs], 1), axis=0, return_inverse=True)[1].ravel()
        g3 = g3_codes(xent, ent[y][attrs[y].codes])
        raw = g3_codes(cx.codes, attrs[y].codes)
        c0 = total_calls(orcs)
        r = certify(cx, attrs[y], xo, orcs[y], theta0, delta, af,
                    np.random.default_rng(zlib.crc32(f"e9|{seed}|{'+'.join(lhs)}|{y}".encode())), inverse=True)
        tane_acc = any(L <= set(lhs) and R == y for L, R in found)
        recs.append({"lhs": list(lhs), "rhs": y, "g3": float(g3), "raw_g3": float(raw), "truth": bool(g3 <= delta),
                     "tane": bool(tane_acc), "certified": r["certified"], "ub": r["ub"],
                     "calls": int(total_calls(orcs) - c0)})
    t_cert = time.perf_counter() - t1
    T = [r for r in recs if r["truth"]]
    F = [r for r in recs if not r["truth"]]
    out = {"dataset": ds.name, "seed": seed, "n_cands": len(cands), "n_true": len(T), "rows": len(ds.df),
           "tane": {"false": sum(r["tane"] for r in F), "missed": sum(not r["tane"] for r in T)},
           "ours": {"false": sum(r["certified"] for r in F), "missed": sum(not r["certified"] for r in T)},
           "calls": total_calls(orcs), "calls_fwd_inv": calls_split(orcs), "canon_all": ds.canon_all_cost(attrs, names),
           "sec": {"tane": t_tane, "certify": t_cert}, "fds": recs}
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="geonames")
    ap.add_argument("--kw", default="{}")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--theta0", type=float, default=0.9)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    outp = ROOT / f"results/icde27/e9_{a.dataset}{a.tag}.json"
    res = []
    for s in range(a.seeds):
        ds = LOADERS[a.dataset](seed=s, **json.loads(a.kw))
        r = run_one(ds, a.delta, a.alpha, a.theta0, s)
        res.append(r)
        print(f"{r['dataset']} seed={s} cands={r['n_cands']} true={r['n_true']} tane={r['tane']} ours={r['ours']} "
              f"calls={r['calls']} canon_all={r['canon_all']} sec={r['sec']}", flush=True)
        outp.write_text(json.dumps(res, indent=1))
