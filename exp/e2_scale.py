"""E2 (paper Sec. VI, Fig. 3): oracle cost vs |r| and |dom| (Thm B).

GeoNames with a growing number of cities (cities500.txt for the largest sizes).
For each size: certify the city-side FDs (inverse blocking, family-wise alpha/m,
shared oracle caches) and record oracle calls, samples, proxy-build and
certification wall-clock; compare with canonicalize-all (B4, |dom X|+|dom Y|),
pairwise blocked self-join (B5, #candidate pairs) and the sample-only
estimator (B7) at the same per-FD call budget.
Output: results/icde27/e2_geonames<tag>.json
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
from semfd.baselines import pairwise_join, sample_only  # noqa: E402
from semfd.certify import certify, g3_codes  # noqa: E402
from semfd.data import geonames  # noqa: E402
from semfd.oracle import calls_split, total_calls  # noqa: E402

FDS = [("city", "country"), ("city", "admin1"), ("admin1", "country"), ("city", "tz"),
       ("city", "country_e8"), ("city", "country_src8"), ("city", "tz_src8"), ("admin1", "city")]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", type=int, nargs="+", default=[1000, 4000, 16000, 64000, 128000])
    ap.add_argument("--source", default="cities500.txt")
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--theta0", type=float, default=0.9)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    outp = ROOT / f"results/icde27/e2_geonames{a.tag}.json"
    res = []
    for C in a.sizes:
        for s in range(a.seeds):
            t0 = time.perf_counter()
            ds = geonames(n_cities=C, seed=s, source=a.source)
            t_load = time.perf_counter() - t0
            attrs = ds.attrs()
            t_proxy = time.perf_counter() - t0 - t_load
            ent = ds.entity_codes(attrs)
            orcs = ds.oracles(inverse=True)
            af = a.alpha / len(FDS)
            rec = {"n_cities": C, "seed": s, "rows": len(ds.df), "source": a.source,
                   "distinct": {k: len(v.vals) for k, v in attrs.items()},
                   "sec": {"load": t_load, "proxy": t_proxy,
                           "proxy_per_attr": {k: v.build_sec for k, v in attrs.items()}},
                   "fds": []}
            t1 = time.perf_counter()
            for x, y in FDS:
                ax, ay = attrs[x], attrs[y]
                g3 = g3_codes(ent[x][ax.codes], ent[y][ay.codes])
                tc = time.perf_counter()
                r = certify(ax, ay, orcs[x], orcs[y], a.theta0, a.delta, af,
                            np.random.default_rng(zlib.crc32(f"e2|{C}|{s}|{x}|{y}".encode())), inverse=True)
                r["sec"] = time.perf_counter() - tc
                fo = ds.oracles()
                b5 = pairwise_join(ax, ay, fo[x], fo[y])
                fo = ds.oracles()
                b7 = sample_only(ax, ay, fo[x], fo[y], r["samples"],
                                 np.random.default_rng(zlib.crc32(f"e2b7|{C}|{s}|{x}|{y}".encode())))
                rec["fds"].append({"fd": f"{x}->{y}", "g3": g3, "truth": bool(g3 <= a.delta), "ours": r,
                                   "canon_cost": (0 if ds.exact[x] else len(ax.vals)) +
                                                 (0 if ds.exact[y] else len(ay.vals)),
                                   "b5_pairwise": b5, "b7_sample": b7})
            rec["sec"]["certify_total"] = time.perf_counter() - t1
            rec["run_calls"] = total_calls(orcs)
            rec["run_calls_fwd_inv"] = calls_split(orcs)
            rec["canon_all"] = int(sum(len(attrs[k].vals) for k in {"city", "country", "admin1"}))
            res.append(rec)
            print(f"C={C} s={s} rows={rec['rows']} distinct city={rec['distinct']['city']} "
                  f"proxy={t_proxy:.0f}s run_calls={rec['run_calls']} canon_all={rec['canon_all']} | "
                  + " ".join(f"{f['fd']}:{'C' if f['ours']['certified'] else '-'}{'T' if f['truth'] else 'F'}"
                             f"/{f['ours']['calls']}" for f in rec["fds"]), flush=True)
            outp.write_text(json.dumps(res, indent=1))
