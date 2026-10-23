"""E20 (pre-registered, literature/prereg_e20_2026-10-24.md): oracle cost with N, D and |C| varied separately.

GeoNames, complete inverse, family-wise alpha/|C|, shared oracle caches within a run, 2 seeds.
  rows  : the 16k-city table with every row repeated r = 1, 4, 16 times (N grows, every domain and g3 fixed;
          row repetition is a control for N only).
  dom   : 4k, 16k and 64k cities (all drawn from cities500.txt), each table resampled uniformly with replacement to the same N = 60,000 rows
          (D grows, N fixed; g3 recomputed on the resampled table).
  cands : the 16k-city table, nested subsets of its unary candidates (fixed random order) of size 8, 16, 32 and all.
rows/dom use the eight FDs of E2. Records calls (forward, inverse), samples, decisions, canonicalize-all cost, and the
alias-class sizes that bound kappa.
Output: results/icde27/e20_scaling.json
"""

import json
import sys
import time
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semfd.certify import certify, g3_codes  # noqa: E402
from semfd.data import geonames  # noqa: E402
from semfd.oracle import calls_split, total_calls  # noqa: E402
from semfd.probes import base_attr as base  # noqa: E402

FDS = [("city", "country"), ("city", "admin1"), ("admin1", "country"), ("city", "tz"),
       ("city", "country_e8"), ("city", "country_src8"), ("city", "tz_src8"), ("admin1", "city")]
DELTA, ALPHA, THETA = 0.05, 0.05, 0.9


def with_rows(ds, df):
    return type(ds)(ds.name, df.reset_index(drop=True), ds.exact, ds.oracle, ds.fds, ds.meta)


def run(ds, cands, tag, seed):
    t0 = time.perf_counter()
    attrs = ds.attrs()
    ent = ds.entity_codes(attrs)
    orcs = ds.oracles(inverse=True)
    af = ALPHA / len(cands)
    fds, samples = [], 0
    for x, y in cands:
        g3 = float(g3_codes(ent[x][attrs[x].codes], ent[y][attrs[y].codes]))
        r = certify(attrs[x], attrs[y], orcs[x], orcs[y], THETA, DELTA, af,
                    np.random.default_rng(zlib.crc32(f"e20|{tag}|{seed}|{x}|{y}".encode())), inverse=True)
        samples += r["samples"]
        fds.append({"fd": f"{x}->{y}", "g3": g3, "certified": bool(r["certified"]), "samples": r["samples"],
                    "calls": r["calls"]})
    tol = [a for a in attrs if not ds.exact[a]]
    cls = {}
    for a in tol:
        tab = ds.oracle.get(a)
        if tab:
            sizes = pd.Series([tab[v] for v in attrs[a].vals]).value_counts()
            cls[a] = {"max": int(sizes.max()), "mean": float(sizes.mean())}
    T = {f["fd"] for f in fds if f["g3"] <= DELTA}
    C = {f["fd"] for f in fds if f["certified"]}
    return {"tag": tag, "seed": seed, "rows": len(ds.df), "n_cands": len(cands),
            "distinct": {a: len(attrs[a].vals) for a in attrs},
            "calls": int(total_calls(orcs)), "calls_fwd_inv": calls_split(orcs), "samples": int(samples),
            "canon_all": int(ds.canon_all_cost(attrs, sorted({a for c in cands for a in c}))),
            "false": sorted(C - T), "missed": sorted(T - C), "alias_class": cls,
            "max_nbrs": {a: int(max(len(n) for n in attrs[a].nbrs)) for a in tol},
            "sec": time.perf_counter() - t0, "fds": fds}


def main(seeds=2):
    out = []
    path = ROOT / "results/icde27/e20_scaling.json"
    for s in range(seeds):
        base16 = geonames(n_cities=16000, seed=s)
        for r in (1, 4, 16):
            ds = with_rows(base16, pd.concat([base16.df] * r))
            out.append(run(ds, FDS, f"rows_x{r}", s))
            print(out[-1]["tag"], s, out[-1]["rows"], out[-1]["calls"], out[-1]["samples"], flush=True)
            path.write_text(json.dumps(out, indent=1))
        for c in (4000, 16000, 64000):
            ds0 = geonames(n_cities=c, seed=s, source="cities500.txt")   # one source for all three sizes
            df = ds0.df.sample(n=60000, replace=True, random_state=s)
            out.append(run(with_rows(ds0, df), FDS, f"dom_{c}", s))
            print(out[-1]["tag"], s, out[-1]["distinct"]["city"], out[-1]["calls"], out[-1]["samples"], flush=True)
            path.write_text(json.dumps(out, indent=1))
        names = list(base16.exact)
        cands = [(x, y) for x in names for y in names if x != y and base(x) != base(y) and (x, y) not in base16.exclude]
        order = [cands[i] for i in np.random.default_rng(100 + s).permutation(len(cands))]
        for m in (8, 16, 32, len(order)):
            out.append(run(base16, order[:m], f"cands_{m}", s))
            print(out[-1]["tag"], s, out[-1]["calls"], out[-1]["samples"], flush=True)
            path.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
