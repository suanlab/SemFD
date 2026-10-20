"""E7 (paper Sec. VI): guarantees are oracle-relative -- how does oracle error
propagate? The ground-truth canonicalizer of every tolerant attribute is
replaced by a corrupted one (semfd.oracle.noisy: per-value split/merge errors at
rate p; still a function, so still transitive). We certify the dataset's FDs
against the noisy oracle (inverse blocking, family-wise alpha) and score the
decisions against BOTH the noisy-oracle truth (the guarantee's reference) and
the clean truth (what the user wants).
Output: results/icde27/e7_<dataset><tag>.json
"""

import argparse
import copy
import json
import sys
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semfd.certify import certify  # noqa: E402
from semfd.data import LOADERS  # noqa: E402
from semfd.oracle import noisy, total_calls  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="geonames")
    ap.add_argument("--kw", default='{"n_cities": 16000}')
    ap.add_argument("--ps", type=float, nargs="+", default=[0.0, 0.01, 0.02, 0.05, 0.1])
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--theta0", type=float, default=0.9)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    ds = LOADERS[a.dataset](seed=0, **json.loads(a.kw))
    attrs = ds.attrs()
    clean = ds.truth(attrs, ds.entity_codes(attrs))
    res = {"dataset": ds.name, "delta": a.delta, "alpha": a.alpha, "runs": []}
    outp = ROOT / f"results/icde27/e7_{a.dataset}{a.tag}.json"
    for p in a.ps:
        for s in range(a.seeds):
            nds = copy.copy(ds)
            memo = {}
            nds.oracle = {k: memo.setdefault(id(t), noisy(t, p, seed=s)) for k, t in ds.oracle.items()}
            ntruth = nds.truth(attrs, nds.entity_codes(attrs))
            orcs = nds.oracles(inverse=True)
            af = a.alpha / len(ds.fds)
            rec = {"p": p, "seed": s, "fds": []}
            for x, y in ds.fds:
                r = certify(attrs[x], attrs[y], orcs[x], orcs[y], a.theta0, a.delta, af,
                            np.random.default_rng(zlib.crc32(f"e7|{p}|{s}|{x}|{y}".encode())), inverse=True)
                rec["fds"].append({"fd": f"{x}->{y}", "certified": r["certified"], "ub": r["ub"],
                                   "g3_clean": float(clean[(x, y)]), "g3_noisy": float(ntruth[(x, y)]), "calls": r["calls"]})
            F = rec["fds"]
            rec["false_vs_noisy"] = int(sum(f["certified"] and f["g3_noisy"] > a.delta for f in F))
            rec["false_vs_clean"] = int(sum(f["certified"] and f["g3_clean"] > a.delta for f in F))
            rec["missed_vs_clean"] = int(sum(not f["certified"] and f["g3_clean"] <= a.delta for f in F))
            rec["calls"] = total_calls(orcs)
            res["runs"].append(rec)
            print(f"p={p} s={s} false(noisy)={rec['false_vs_noisy']} false(clean)={rec['false_vs_clean']} "
                  f"missed(clean)={rec['missed_vs_clean']} calls={rec['calls']} | "
                  + " ".join(f"{f['fd']}:{'C' if f['certified'] else '-'}{f['g3_clean']:.3f}/{f['g3_noisy']:.3f}"
                             for f in F), flush=True)
            outp.write_text(json.dumps(res, indent=1))
