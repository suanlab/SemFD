"""E25 entry probe (pre-registered): SEC EDGAR filer names as a
natural-alias table, cik as the oracle. Exact g3 on Layer-1 strings vs under the cik oracle for a fixed candidate
list; share of multi-name ciks. No sampling, no oracle-call accounting. Writes results/icde27/e25_sec_probe.json.
"""

import hashlib
import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from rapidfuzz.distance import Levenshtein

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semfd.certify import g3_codes  # noqa: E402
from semfd.proxy import layer1  # noqa: E402

SEC = ROOT / "data/sec"
QUARTERS = [f"{y}q{q}" for y in range(2015, 2025) for q in range(1, 5)]
COLS = ["cik", "name", "former", "sic", "countryba", "stprba", "cityba", "fye", "form"]
CANDIDATES = [("name", "sic"), ("name", "stprba"), ("name", "countryba"), ("name", "cityba"), ("name", "fye"),
              ("sic", "name"), ("stprba", "name"), ("cityba", "name")]
DELTA = 0.05


def load():
    frames, sha = [], {}
    for q in QUARTERS:
        p = SEC / f"sub_{q}.txt"
        sha[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
        frames.append(pd.read_csv(p, sep="\t", usecols=COLS, dtype=str, keep_default_na=False, encoding="latin-1"))
    return pd.concat(frames, ignore_index=True), sha


def main():
    df, sha = load()
    n_raw = len(df)
    for c in COLS:
        if c != "cik":
            df[c] = df[c].map(layer1)
    ciks_per_name = df.groupby("name")["cik"].nunique()
    ambiguous = set(ciks_per_name[ciks_per_name > 1].index)
    dropped = int(df["name"].isin(ambiguous).sum())
    df = df[~df["name"].isin(ambiguous)].reset_index(drop=True)
    names_per_cik = df.groupby("cik")["name"].nunique()
    multi = set(names_per_cik[names_per_cik > 1].index)
    multi_share = float(df["cik"].isin(multi).mean())
    far = tot = 0
    for _, g in df[df["cik"].isin(multi)].groupby("cik")["name"]:
        for a, b in combinations(sorted(set(g)), 2):
            tot += 1
            far += Levenshtein.normalized_similarity(a, b) < 0.9
    code = lambda s: pd.factorize(s)[0]
    string_codes = {c: code(df[c]) for c in COLS}
    oracle_codes = dict(string_codes, name=code(df["cik"]))
    rows = []
    for x, y in CANDIDATES:
        gs = float(g3_codes(string_codes[x], string_codes[y]))
        go = float(g3_codes(oracle_codes[x], oracle_codes[y]))
        rows.append({"fd": f"{x}->{y}", "g3_strings": gs, "g3_oracle": go, "diff": go - gs,
                     "true_oracle": go < DELTA, "true_strings": gs < DELTA})
        print(rows[-1], flush=True)
    c1 = any(r["true_oracle"] and r["fd"].startswith("name->") for r in rows)
    c2 = any(abs(r["diff"]) >= DELTA / 2 or r["true_oracle"] != r["true_strings"] for r in rows)
    c3 = multi_share >= 0.01
    res = {"design": "literature/prereg_rb_sec_probe_2026-11-03.md", "quarters": [QUARTERS[0], QUARTERS[-1]],
           "sha256_sub": sha, "rows_raw": n_raw, "rows_dropped_ambiguous_name": dropped,
           "ambiguous_names": len(ambiguous), "rows": len(df), "ciks": int(df["cik"].nunique()),
           "names": int(df["name"].nunique()), "multi_name_ciks": len(multi), "multi_name_tuple_share": multi_share,
           "multi_name_pairs": tot, "multi_name_pairs_lev_below_0.9": int(far), "candidates": rows,
           "criteria": {"1_true_name_lhs": c1, "2_gap_or_flip": c2, "3_multi_share_ge_1pct": c3},
           "pass": bool(c1 and c2 and c3)}
    out = ROOT / "results/icde27/e25_sec_probe.json"
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k not in ("sha256_sub", "candidates")}, indent=1), flush=True)


if __name__ == "__main__":
    main()
