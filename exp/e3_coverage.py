"""E3 (paper Sec. VI, Fig. 4): empirical coverage of the certificate.

The guarantee's randomness is the tuple sampling, so the data is fixed and the
sampler is repeated R times per FD. FDs are planted near delta (near-miss
injected errors and two-source conflicts at several rates). Per FD we compute
  g3     oracle truth,
  EB     the exact mean of the audited indicator B over all tuples (the
         quantity the confidence sequence covers; g3 <= EB by Thm A),
and report over the R runs
  P[U < EB]              miscoverage of the CS at its stopping time (<= alpha),
  P[certified & g3 > delta]  false-certification rate (<= alpha).
Output: results/icde27/e3_<dataset><tag>.json
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semfd.certify import certify, g3_codes, witness  # noqa: E402
from semfd.data import LOADERS  # noqa: E402


def exact_mean_B(ax, ay, fx, fy, theta, inverse=True):
    """E[B] over uniform tuples, by evaluating B once per distinct (x, y)."""
    lab, rep, prio = witness(ax, ay, theta)
    xv, yv = ax.vals, ay.vals
    xidx = {v: i for i, v in enumerate(xv)}
    pairs, cnt = np.unique(np.stack([ax.codes, ay.codes], 1), axis=0, return_counts=True)
    bad_x = {}
    tot = 0
    for (xi, yi), n in zip(pairs, cnt):
        c = int(lab[xi])
        r = rep[c]
        ry = fy(yv[r])
        if fy(yv[yi]) != ry:
            tot += n
            continue
        if xi not in bad_x:
            same = {xidx[v] for v in fx.aliases(fx(xv[xi])) if v in xidx} if inverse else set()
            b = False
            for xj in np.union1d(ax.nbrs[xi], np.fromiter(same, np.int64, len(same))):
                cj = int(lab[xj])
                rj = rep.get(cj)
                if rj is None or cj == c or rj == r or prio[cj] < prio[c]:
                    continue
                if (xj in same or fx(xv[xj]) == fx(xv[xi])) and fy(yv[rj]) != ry:
                    b = True
                    break
            bad_x[xi] = b
        tot += n * bad_x[xi]
    return tot / len(ax.codes)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="geonames")
    ap.add_argument("--kw", default='{"n_cities": 4000, "near_miss": [0.03, 0.04, 0.05, 0.06, 0.07], '
                                    '"conflict": [0.04, 0.06, 0.07]}')
    ap.add_argument("--reps", type=int, default=500)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--theta0", type=float, default=0.9)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    ds = LOADERS[a.dataset](seed=a.seed, **json.loads(a.kw))
    attrs = ds.attrs()
    ent = ds.entity_codes(attrs)
    orcs = ds.oracles(inverse=True)
    out = {"dataset": ds.name, "meta": ds.meta, "reps": a.reps, "delta": a.delta, "alpha": a.alpha,
           "theta0": a.theta0, "fds": []}
    outp = ROOT / f"results/icde27/e3_{a.dataset}{a.tag}.json"
    for x, y in ds.fds:
        ax, ay = attrs[x], attrs[y]
        g3 = g3_codes(ent[x][ax.codes], ent[y][ay.codes])
        EB = exact_mean_B(ax, ay, orcs[x], orcs[y], a.theta0)
        runs = [certify(ax, ay, orcs[x], orcs[y], a.theta0, a.delta, a.alpha,
                        np.random.default_rng(10_000 * a.seed + i), inverse=True) for i in range(a.reps)]
        rec = {"fd": f"{x}->{y}", "g3": g3, "EB": EB,
               "miscover_EB": float(np.mean([r["ub"] < EB for r in runs])),
               "miscover_g3": float(np.mean([r["ub"] < g3 for r in runs])),
               "cert_rate": float(np.mean([r["certified"] for r in runs])),
               "false_cert_rate": float(np.mean([r["certified"] and g3 > a.delta for r in runs])),
               "samples_mean": float(np.mean([r["samples"] for r in runs])),
               "ub": [r["ub"] for r in runs]}
        out["fds"].append(rec)
        print(f"{rec['fd']:<24} g3={g3:.4f} EB={EB:.4f} miscov(EB)={rec['miscover_EB']:.3f} "
              f"cert={rec['cert_rate']:.3f} falsecert={rec['false_cert_rate']:.3f} "
              f"n~{rec['samples_mean']:.0f}", flush=True)
        outp.write_text(json.dumps(out))
