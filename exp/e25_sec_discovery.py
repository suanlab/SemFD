"""E25 (R-B) full run (pre-registered, literature/prereg_rb_sec_full_2026-11-03.md): SEC EDGAR filer names, cik as the
oracle. Reuses exp/e1b_discovery.run_one (complete inverse, baselines, closure) and the E11 incomplete-inverse
procedure unchanged; the loader lives here so that semfd/ is not modified. Writes results/icde27/e25_sec_discovery.json.
"""

import json
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "exp")]
from semfd.certify import certify, g3_codes  # noqa: E402
from semfd.data import Dataset  # noqa: E402
from semfd.oracle import total_calls  # noqa: E402
from semfd.proxy import layer1  # noqa: E402
import e1b_discovery as e1b  # noqa: E402
import e11_partial_inverse as e11  # noqa: E402

OUT = ROOT / "results/icde27/e25_sec_discovery.json"
QUARTERS = [f"{y}q{q}" for y in range(2015, 2025) for q in range(1, 5)]
COLS = ["name", "cik", "sic", "countryba", "stprba", "cityba", "fye"]


def sec(seed=0):
    """SEC DERA Financial Statement Data Sets, sub.txt 2015q1-2024q4 (U.S. Government work; data/sec/fetch.sh).
    One row per submission. Oracle for the filer name = its cik. Names filed under several ciks are dropped."""
    d = pd.concat([pd.read_csv(ROOT / f"data/sec/sub_{q}.txt", sep="\t", usecols=COLS, dtype=str,
                               keep_default_na=False, encoding="latin-1") for q in QUARTERS], ignore_index=True)
    for c in COLS:
        if c not in ("name", "cik"):
            d[c] = d[c].map(layer1)
    key = d["name"].map(layer1)
    homonym = (d.groupby(key)["cik"].transform("nunique") > 1).to_numpy()
    df = d[~homonym][COLS].reset_index(drop=True)
    oracle = {"name": dict(zip(df["name"].map(layer1), df["cik"]))}
    exact = {a: a != "name" for a in COLS}
    return Dataset(f"sec{len(df)}", df, exact, oracle, [], {"seed": seed, "quarters": [QUARTERS[0], QUARTERS[-1]],
                                                            "homonym_rows_dropped": int(homonym.sum())},
                   exclude={("name", "cik"), ("cik", "name")})


def partial(ds, s, p, delta=0.05, alpha=0.05, theta=0.9):
    attrs = ds.attrs()
    ent = ds.entity_codes(attrs)
    names = list(attrs)
    cands = [(x, y) for x in names for y in names if x != y and (x, y) not in ds.exclude]
    truth = {(x, y): g3_codes(ent[x][attrs[x].codes], ent[y][attrs[y].codes]) for x, y in cands}
    orcs, cert, nus = e11.oracles(ds, p, s), set(), {}
    for x, y in cands:
        r = certify(attrs[x], attrs[y], orcs[x], orcs[y], theta, delta, alpha / len(cands),
                    np.random.default_rng(zlib.crc32(f"e11|{s}|{p}|{x}|{y}".encode())), inverse=True)
        if r["certified"]:
            cert.add((x, y))
        if not ds.exact[x]:
            nus[f"{x}->{y}"] = e11.nu_partial(attrs[x], attrs[y], ent[x], ent[y], theta, ds.oracle.get(x), p, s, x)
    T = {c for c in cands if truth[c] <= delta}
    return {"seed": s, "p": p, "n_cands": len(cands), "n_true": len(T),
            "false": sorted(f"{x}->{y}" for x, y in cert - T), "missed": sorted(f"{x}->{y}" for x, y in T - cert),
            "calls": total_calls(orcs), "nu_max": max(nus.values(), default=0.0), "nu": nus}


def main(seeds=range(3)):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    res = {"design": "literature/prereg_rb_sec_full_2026-11-03.md", "complete": [], "partial": []}
    for s in seeds:
        ds = sec(seed=s)
        res["meta"] = {**ds.meta, "rows": len(ds.df)}
        r = e1b.run_one(ds, 0.05, 0.05, 0.9, 5, s)
        r["string_vs_oracle_flips"] = sorted(
            f"{x}->{y}" for x in COLS for y in COLS if x != y and (x, y) not in ds.exclude
            and f"{x}->{y}" in r["truth"]
            and (g3_codes(pd.factorize(ds.df[x].map(layer1))[0], pd.factorize(ds.df[y].map(layer1))[0]) <= 0.05)
            != (r["truth"][f"{x}->{y}"] <= 0.05))
        res["complete"].append(r)
        print(f"seed={s} cands={r['n_cands']} true={r['n_true']} ours={r['ours']} calls={r['ours_calls_total']} "
              f"canon_all={r['canon_all']} tane_raw={r['b3_tane_raw']} tane_norm={r['b3_tane_norm']} b9={r['b9_noaudit']}"
              f" false={r['false_lists']} flips={r['string_vs_oracle_flips']}", flush=True)
        OUT.write_text(json.dumps(res, indent=1))
        for p in (0.5, 0.0):
            q = partial(ds, s, p)
            res["partial"].append(q)
            print(f"seed={s} p={p} false={q['false']} missed={q['missed']} calls={q['calls']} nu_max={q['nu_max']:.4f}",
                  flush=True)
            OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
