"""E4 (paper Sec. VI): what certified closure buys (Thm C).

Workload view: candidates C (unary, probe-column pairs excluded) are split at
random into a certified half S and a held-out half H. S is certified at the
tighter target delta/2 (family-wise alpha/|S|, inverse blocking, shared cache).
For every FD in H, the closure of the certified part of S gives a bound at zero
oracle cost. We report, per split:
  coverage      fraction of oracle-true FDs in H whose derived bound <= delta,
  validity      derived bounds violated by the oracle truth (must be 0),
  tightness     derived bound vs oracle g3,
  calls         certifying S at delta/2, vs certifying H directly at delta
                (separate fresh cache), i.e. the calls closure saves.
Output: results/icde27/e4_<dataset><tag>.json
"""

import argparse
import json
import sys
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semfd.certify import certify, g3_codes  # noqa: E402
from semfd.closure import unary_closure  # noqa: E402
from semfd.data import LOADERS  # noqa: E402
from semfd.oracle import total_calls  # noqa: E402
from semfd.probes import base_attr as base  # noqa: E402


def cert_all(pairs, attrs, orcs, target, alpha, theta0, salt):
    out = {}
    c0 = total_calls(orcs)
    for x, y in pairs:
        out[(x, y)] = certify(attrs[x], attrs[y], orcs[x], orcs[y], theta0, target, alpha / max(len(pairs), 1),
                              np.random.default_rng(zlib.crc32(f"{salt}|{x}|{y}".encode())), inverse=True)
    return out, total_calls(orcs) - c0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="geonames")
    ap.add_argument("--kw", default='{"n_cities": 16000}')
    ap.add_argument("--splits", type=int, default=5)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--theta0", type=float, default=0.9)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    ds = LOADERS[a.dataset](seed=0, **json.loads(a.kw))
    attrs = ds.attrs()
    names = list(attrs)
    ent = ds.entity_codes(attrs)
    cands = [(x, y) for x in names for y in names if x != y and base(x) != base(y)]
    truth = {c: g3_codes(ent[c[0]][attrs[c[0]].codes], ent[c[1]][attrs[c[1]].codes]) for c in cands}
    res = {"dataset": ds.name, "delta": a.delta, "alpha": a.alpha, "n_cands": len(cands),
           "n_true": sum(g <= a.delta for g in truth.values()), "splits": []}
    outp = ROOT / f"results/icde27/e4_{a.dataset}{a.tag}.json"
    for sp in range(a.splits):
        rng = np.random.default_rng(sp)
        perm = rng.permutation(len(cands))
        S = [cands[i] for i in perm[: len(cands) // 2]]
        H = [cands[i] for i in perm[len(cands) // 2:]]
        rS, callsS = cert_all(S, attrs, ds.oracles(inverse=True), a.delta / 2, a.alpha, a.theta0, f"S{sp}")
        bounds = {c: r["ub"] for c, r in rS.items() if r["certified"]}
        clo = unary_closure(bounds, names)
        rH, callsH = cert_all(H, attrs, ds.oracles(inverse=True), a.delta, a.alpha, a.theta0, f"H{sp}")
        Ht = [c for c in H if truth[c] <= a.delta]
        derived = {c: clo[c] for c in H if c in clo}
        rec = {"split": sp, "S": len(S), "H": len(H), "H_true": len(Ht), "calls_S_half_delta": int(callsS),
               "calls_H_direct": int(callsH),
               "S_false_certified": sum(r["certified"] and truth[c] > a.delta / 2 for c, r in rS.items()),
               "H_direct_certified_true": sum(rH[c]["certified"] for c in Ht),
               "H_covered_by_closure": sum(c in derived and derived[c][0] <= a.delta for c in Ht),
               "H_false_covered": sum(c in derived and derived[c][0] <= a.delta and truth[c] > a.delta for c in H),
               "derived_violations": sum(truth[c] > u for c, (u, _) in derived.items()),
               "tightness": [{"fd": f"{c[0]}->{c[1]}", "bound": derived[c][0], "g3": truth[c],
                              "path": list(derived[c][1])} for c in derived]}
        res["splits"].append(rec)
        print({k: v for k, v in rec.items() if k != "tightness"}, flush=True)
        outp.write_text(json.dumps(res, indent=1, default=lambda o: o.item()))
