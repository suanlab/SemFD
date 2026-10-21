"""E1b (paper Sec. VI, Table II): discovery mode over ALL unary candidates X -> Y.

Compares, against oracle truth (g3 on the canonical instance <= delta):
  B3   Desbordante Tane AFD discovery (g3 <= delta, max_lhs = 1) on the raw
       strings and on Layer-1-normalised strings ("normalize-then-FD")
  B1   proxy-quotient AFD at the pre-declared theta (g3 of the quotient <= delta)
  ours certification of every candidate (inverse blocking, family-wise alpha/m,
       oracle caches shared across candidates), then certified closure (Thm C):
       FDs with |LHS| <= 2 derived at zero oracle cost, checked against truth.
Output: results/icde27/e1b_<dataset><tag>.json
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
from semfd.closure import derived_fds  # noqa: E402
from semfd.data import LOADERS  # noqa: E402
from semfd.planner import certify_or_resolve, prepass  # noqa: E402
from semfd.oracle import calls_split  # noqa: E402
from semfd.probes import base_attr as base  # noqa: E402
from semfd.proxy import layer1  # noqa: E402


def tane(df, delta):
    import desbordante
    a = desbordante.afd.algorithms.Tane()
    a.load_data(table=df.astype(str))
    a.execute(error=delta, max_lhs=1, afd_error_measure="g3")
    cols = list(df.columns)
    found, const = set(), set()
    for f in a.get_fds():
        if len(f.lhs_indices) == 0:
            const.add(cols[f.rhs_index])
        else:
            found.add((cols[f.lhs_indices[0]], cols[f.rhs_index]))
    return {(x, y) for x in cols for y in cols if x != y and ((x, y) in found or y in const)}


def combo(codes):
    return np.unique(np.stack(codes, 1), axis=0, return_inverse=True)[1].ravel()


def run_one(ds, delta, alpha, theta0, k, seed, v_thresh=2000):
    t0 = time.perf_counter()
    attrs = ds.attrs(k=k)
    t_proxy = time.perf_counter() - t0
    names = list(attrs)
    ent = ds.entity_codes(attrs)
    cands = [(x, y) for x in names for y in names if x != y and base(x) != base(y) and (x, y) not in ds.exclude]
    truth = {(x, y): g3_codes(ent[x][attrs[x].codes], ent[y][attrs[y].codes]) for x, y in cands}
    raw = ds.df[names]
    norm = raw.apply(lambda s: s.map(layer1))
    t1 = time.perf_counter()
    C = set(cands)
    b3_raw, b3_norm = tane(raw, delta) & C, tane(norm, delta) & C
    t_tane = time.perf_counter() - t1
    b1 = {(x, y) for x, y in cands
          if g3_codes(attrs[x].partition(theta0)[attrs[x].codes],
                      attrs[y].partition(theta0)[attrs[y].codes]) <= delta}
    orcs = ds.oracles(inverse=True)
    a_fd = alpha / len(cands)
    ours, cert = {}, set()
    t2 = time.perf_counter()
    for x, y in cands:
        r = certify(attrs[x], attrs[y], orcs[x], orcs[y], theta0, delta, a_fd,
                    np.random.default_rng(zlib.crc32(f"e1b|{seed}|{x}|{y}".encode())), inverse=True)
        ours[f"{x}->{y}"] = r
        if r["certified"]:
            cert.add((x, y))
    t_cert = time.perf_counter() - t2
    orcs9, cert9 = ds.oracles(), set()                # B9: no neighbour/purity audit (unsound)
    for x, y in cands:
        r = certify(attrs[x], attrs[y], orcs9[x], orcs9[y], theta0, delta, a_fd,
                    np.random.default_rng(zlib.crc32(f"e1b9|{seed}|{x}|{y}".encode())), audit=False)
        if r["certified"]:
            cert9.add((x, y))
    orcs_p = ds.oracles(inverse=True)                 # planner variant (fresh shared cache)
    pre = prepass(attrs, orcs_p, v_thresh)
    planned, cert_p = {}, set()
    for x, y in cands:
        r = certify_or_resolve(attrs[x], attrs[y], orcs_p[x], orcs_p[y], theta0, delta, a_fd,
                               np.random.default_rng(zlib.crc32(f"e1b|{seed}|{x}|{y}".encode())))
        planned[f"{x}->{y}"] = r
        if r["certified"]:
            cert_p.add((x, y))
    bounds = {(x, y): ours[f"{x}->{y}"]["ub"] for x, y in cert}
    der = derived_fds(bounds, names, max_lhs=2, delta=delta)
    der_eval = []
    for (lhs, y), u in der.items():
        g = g3_codes(combo([ent[a][attrs[a].codes] for a in lhs]), ent[y][attrs[y].codes])
        der_eval.append({"lhs": list(lhs), "rhs": y, "bound": u, "g3": g, "violated": bool(g > u)})
    T = {c for c in cands if truth[c] <= delta}

    def score(S):
        return {"n": len(S), "false": len(S - T), "missed_true": len(T - S)}
    canon_all = ds.canon_all_cost(attrs, names)
    uniq = lambda o: {id(v): v for v in o.values()}.values()
    return {"dataset": ds.name, "seed": seed, "delta": delta, "alpha": alpha, "alpha_per_fd": a_fd,
            "theta0": theta0, "rows": len(ds.df), "n_cands": len(cands), "n_true": len(T),
            "truth": {f"{x}->{y}": g for (x, y), g in truth.items()},
            "b3_tane_raw": score(b3_raw), "b3_tane_norm": score(b3_norm), "b1_quotient": score(b1),
            "ours": score(cert), "ours_calls_total": int(sum(o.calls for o in uniq(orcs))),
            "ours_calls_fwd_inv": calls_split(orcs),
            "planner": score(cert_p), "planner_calls_total": int(sum(o.calls for o in uniq(orcs_p))),
            "b9_noaudit": score(cert9), "b9_calls_total": int(sum(o.calls for o in uniq(orcs9))),
            "planner_resolved": sum(r["mode"] == "resolved" for r in planned.values()),
            "planner_prepass": pre, "v_thresh": v_thresh,
            "canon_all": canon_all, "ours_detail": ours,
            "false_lists": {"b3_raw": sorted(f"{x}->{y}" for x, y in b3_raw - T),
                            "b3_norm": sorted(f"{x}->{y}" for x, y in b3_norm - T),
                            "b1": sorted(f"{x}->{y}" for x, y in b1 - T),
                            "ours": sorted(f"{x}->{y}" for x, y in cert - T),
                            "planner": sorted(f"{x}->{y}" for x, y in cert_p - T),
                            "b9": sorted(f"{x}->{y}" for x, y in cert9 - T)},
            "missed_lists": {m: sorted(f"{x}->{y}" for x, y in T - S) for m, S in
                             (("b3_raw", b3_raw), ("b1", b1), ("ours", cert), ("b9", cert9))},
            "derived": {"n_certified_base": len(cert), "n_derived_total": len(der),
                        "n_violating_bound": sum(d["violated"] for d in der_eval), "list": der_eval},
            "sec": {"proxy": t_proxy, "tane": t_tane, "certify": t_cert}}


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
    ap.add_argument("--v-thresh", type=int, default=2000, help="planner: canonicalize attrs with <= this many values")
    a = ap.parse_args()
    outp = ROOT / f"results/icde27/e1b_{a.dataset}{a.tag}.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    res = []
    for s in range(a.seeds):
        ds = LOADERS[a.dataset](seed=s, **json.loads(a.kw))
        r = run_one(ds, a.delta, a.alpha, a.theta0, a.k, s, a.v_thresh)
        res.append(r)
        print(f"{r['dataset']} seed={s} cands={r['n_cands']} true={r['n_true']} | "
              + " ".join(f"{m}={r[m]}" for m in ("b3_tane_raw", "b3_tane_norm", "b1_quotient", "b9_noaudit", "ours"))
              + f" planner={r['planner']} | calls={r['ours_calls_total']} planner_calls={r['planner_calls_total']}"
              f" (resolved {r['planner_resolved']}) canon_all={r['canon_all']} | derived="
              f"{r['derived']['n_derived_total']} viol={r['derived']['n_violating_bound']}", flush=True)
        print("   false:", r["false_lists"], flush=True)
        outp.write_text(json.dumps(res, indent=1))
