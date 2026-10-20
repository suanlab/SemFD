"""P0b: high-cardinality pilot on GeoNames cities15000 (real aliases).

Entity identity is known (geonameid / country code / admin1 code), so the
canonicalizer oracle is exact. We vary the number of cities C to locate the
crossover between g3 certification cost and canonicalize-all cost
(pilot study).

Design choices:
  - cities restricted to unique asciiname, admin1 restricted to unique names
    (homonyms would need a tuple-level oracle -- paper #2 problem);
  - aliases = ASCII-only alternate names (the field is mostly transliterations).

Proxies at scale (no dense V x V matrices):
  - syntactic: char 3-gram TF-IDF cosine top-k (sparse) + rapidfuzz ratio on edges
  - semantic:  bge-small cosine top-k (batched dense)
  - partition pi: connected components of candidate edges with
                  hybrid = (ratio + cos)/2 >= theta
  - neighbours N(x) = top-k TF-IDF  U  top-k embedding
"""

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from rapidfuzz.distance import Indel
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.feature_extraction.text import TfidfVectorizer

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "pilot")]
from certify import blocking_recall, certify_g3, g3_codes  # noqa: E402
from p0_data import _drop, _typo, layer1  # noqa: E402

GEO = ROOT / "data/geonames"
CITIES = "cities15000.txt"          # semfd.data.geonames(source=...) may switch to cities500.txt
DELTA = 0.05
COUNTRY_ALIASES = {
    "US": ["USA", "United States of America", "US"], "GB": ["UK", "Great Britain", "Britain"],
    "DE": ["Deutschland", "Federal Republic of Germany"], "RU": ["Russian Federation"],
    "CN": ["PRC", "People's Republic of China"], "KR": ["Republic of Korea"],
    "IR": ["Persia", "Islamic Republic of Iran"], "NL": ["Holland"], "IN": ["Bharat"],
    "JP": ["Nippon"], "BR": ["Brasil"], "MX": ["Mexico", "United Mexican States"],
    "ES": ["Espana"], "IT": ["Italia"], "FR": ["French Republic"], "CH": ["Schweiz"],
}


def load(n_cities, seed):
    cols = ["gid", "name", "ascii", "alt", "lat", "lon", "fclass", "fcode", "cc", "cc2",
            "a1", "a2", "a3", "a4", "pop", "elev", "dem", "tz", "mod"]
    c = pd.read_csv(GEO / CITIES, sep="\t", header=None, names=cols,
                    dtype=str, keep_default_na=False, quoting=3)
    c["key"] = c["ascii"].map(layer1)
    c = c[c["key"].map(c["key"].value_counts()) == 1]
    a1 = pd.read_csv(GEO / "admin1CodesASCII.txt", sep="\t", header=None,
                     names=["code", "name", "ascii", "gid"], dtype=str, keep_default_na=False)
    a1["key"] = a1["ascii"].map(layer1)
    a1 = a1[a1["key"].map(a1["key"].value_counts()) == 1]
    a1name = dict(zip(a1["code"], a1["ascii"]))
    c["a1code"] = c["cc"] + "." + c["a1"]
    c = c[c["a1code"].isin(a1name)]
    cname = {}
    for line in (GEO / "countryInfo.txt").read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            f = line.split("\t")
            cname[f[0]] = f[4]
    c = c[c["cc"].isin(cname)]
    c = c.sample(n=min(n_cities, len(c)), random_state=seed)
    c["pop"] = c["pop"].astype(float)
    return c, a1name, cname


def ascii_alts(s, own):
    out = []
    for a in s.split(","):
        a = a.strip()
        if 3 <= len(a) <= 40 and a.isascii() and any(ch.isalpha() for ch in a) \
                and layer1(a) != own:
            out.append(a)
    return out


def make_table(n_cities, rows_per_city=5, rho=0.2, seed=0):
    rng = random.Random(seed)
    c, a1name, cname = load(n_cities, seed)
    w = np.sqrt(c["pop"].to_numpy())
    w /= w.sum()
    pick = np.random.default_rng(seed).choice(len(c), size=rows_per_city * len(c), p=w)
    oracle = {a: {} for a in ("city", "country", "admin1")}
    # Collision guard: every CLEAN surface is reserved for its own entity before any variant is
    # generated, per attribute, so a variant can never claim another entity's clean name (or an earlier variant's key).
    taken = {"city": {}, "country": {}, "admin1": {}}
    for _, r in c.iterrows():
        taken["city"][r["key"]] = r["gid"]
        taken["country"].setdefault(layer1(cname[r["cc"]]), r["cc"])
        taken["admin1"].setdefault(layer1(a1name[r["a1code"]]), r["a1code"])
    rows = []
    recs = c.to_dict("records")
    for i in pick:
        r = recs[i]
        vals = {}
        for attr, ent, clean, aliases in (
                ("city", r["gid"], r["ascii"], ascii_alts(r["alt"], r["key"])),
                ("country", r["cc"], cname[r["cc"]], COUNTRY_ALIASES.get(r["cc"], [])),
                ("admin1", r["a1code"], a1name[r["a1code"]], [])):
            v = clean
            if rng.random() < rho:
                kinds = ["typo", "drop"] + (["alias", "alias"] if aliases else [])
                k = rng.choice(kinds)
                v = rng.choice(aliases) if k == "alias" else (
                    _typo(clean, rng) if k == "typo" else _drop(clean, rng))
            if rng.random() < 0.2:
                v = v.upper() if rng.random() < 0.5 else v.lower()
            key = layer1(v)
            if oracle[attr].get(key, ent) != ent or taken[attr].get(key, ent) != ent:
                v, key = clean, layer1(clean)      # ambiguous variant -> render clean
            oracle[attr].setdefault(key, ent)      # only after the checks: never records a colliding key
            vals[attr] = v
        vals["tz"] = r["tz"]
        vals["fcode"] = r["fcode"]
        rows.append(vals)
    return pd.DataFrame(rows), oracle


# ------------------------------------------------------------------ proxies
def _embed(vals):
    from embedding_backend import embed, set_model
    set_model("BAAI/bge-small-en-v1.5")
    return np.asarray(embed(list(vals)), dtype=np.float32)


def topk_dense(E, k, batch=4096):
    n = len(E)
    out = np.empty((n, k), dtype=np.int64)
    for s in range(0, n, batch):
        S = E[s:s + batch] @ E.T
        S[np.arange(len(S)), np.arange(s, s + len(S))] = -1
        out[s:s + batch] = np.argpartition(-S, k, axis=1)[:, :k]
    return out


def topk_tfidf(vals, k, batch=4096):
    M = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 3)).fit_transform(vals)
    n = M.shape[0]
    out = np.empty((n, k), dtype=np.int64)
    MT = M.T.tocsr()
    for s in range(0, n, batch):
        S = (M[s:s + batch] @ MT).toarray()
        S[np.arange(len(S)), np.arange(s, s + len(S))] = -1
        out[s:s + batch] = np.argpartition(-S, k, axis=1)[:, :k]
    return out


class BigAttr:
    def __init__(self, name, series, oracle, exact, k=5):
        self.name = name
        self.vals = sorted({layer1(v) for v in series})
        idx = {v: i for i, v in enumerate(self.vals)}
        self.codes = np.array([idx[layer1(v)] for v in series])
        ents = [oracle[v] if oracle else v for v in self.vals]
        eid = {e: j for j, e in enumerate(sorted(set(ents)))}
        self.ent = np.array([eid[e] for e in ents])
        n = len(self.vals)
        self.exact = exact
        if exact or n < 3:
            self.nbrs = [np.array([], int)] * n
            self.edges = (np.array([], int), np.array([], int), np.array([]))
            return
        kk = min(k, n - 1)
        E = _embed(self.vals)
        nb = np.concatenate([topk_tfidf(self.vals, kk), topk_dense(E, kk)], 1)
        self.nbrs = [np.unique(r) for r in nb]
        src = np.repeat(np.arange(n), nb.shape[1])
        dst = nb.ravel()
        ratio = np.array([Indel.normalized_similarity(self.vals[a], self.vals[b])
                          for a, b in zip(src, dst)])
        cos = (E[src] * E[dst]).sum(1)
        self.edges = (src, dst, (ratio + np.clip(cos, 0, 1)) / 2)

    def partition(self, theta):
        n = len(self.vals)
        if self.exact or len(self.edges[0]) == 0:
            return np.arange(n)
        s, d, h = self.edges
        m = h >= theta
        A = coo_matrix((np.ones(m.sum()), (s[m], d[m])), shape=(n, n))
        return connected_components(A, directed=False)[1]


FDS = [("city", "country"), ("city", "admin1"), ("admin1", "country"),
       ("country", "admin1"), ("fcode", "country"), ("admin1", "city"),
       ("tz", "country"), ("country", "tz")]
TYPES = {"city": False, "country": False, "admin1": False, "tz": True, "fcode": True}


def run(n_cities, rho, seed, thetas, k):
    t0 = time.perf_counter()
    df, oracle = make_table(n_cities, rho=rho, seed=seed)
    attrs = {a: BigAttr(a, df[a], oracle.get(a), TYPES[a], k) for a in TYPES}
    t_build = time.perf_counter() - t0
    out = {"n_cities": n_cities, "rows": len(df), "rho": rho, "seed": seed, "k": k,
           "distinct": {a: len(attrs[a].vals) for a in attrs}, "build_sec": t_build,
           "fds": []}
    for x, y in FDS:
        ax, ay = attrs[x], attrs[y]
        g3o = g3_codes(ax.ent[ax.codes], ay.ent[ay.codes])
        rec = {"fd": f"{x}->{y}", "g3_oracle": g3o, "truth": bool(g3o <= DELTA),
               "canon_cost": (0 if ax.exact else len(ax.vals)) + (0 if ay.exact else len(ay.vals)),
               "raw_quot_g3": {}, "cert": {}}
        for th in thetas:
            rec["raw_quot_g3"][str(th)] = g3_codes(ax.partition(th)[ax.codes],
                                                   ay.partition(th)[ay.codes])
            lab = ax.partition(th)
            c = certify_g3(ax.codes, ay.codes, ax.ent, ay.ent, lab, ax.nbrs, DELTA,
                           np.random.default_rng(seed))
            c["recall"] = blocking_recall(lab, ax.nbrs, ax.ent)
            rec["cert"][str(th)] = c
        out["fds"].append(rec)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cities", type=int, nargs="+", default=[1000, 4000, 16000])
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--rho", type=float, default=0.2)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--thetas", type=float, nargs="+", default=[0.85, 0.9, 0.95])
    ap.add_argument("--out", default=str(ROOT / "results/p0/p0b_geonames.json"))
    a = ap.parse_args()
    res = []
    for C in a.cities:
        for s in range(a.seeds):
            r = run(C, a.rho, s, a.thetas, a.k)
            res.append(r)
            print(f"C={C} seed={s} rows={r['rows']} distinct={r['distinct']} "
                  f"build={r['build_sec']:.0f}s", flush=True)
            for f in r["fds"]:
                best = min(f["cert"].values(), key=lambda z: z["calls"] if z["certified"] else 1e18)
                print(f"   {f['fd']:<16} g3*={f['g3_oracle']:.3f} truth={f['truth']!s:<5} "
                      f"canon={f['canon_cost']:>6} " + " ".join(
                          f"[{t}:{'C' if z['certified'] else '-'} calls={z['calls']} ub={z['ub']:.3f} "
                          f"rec={z["recall"]:.2f}/{z["recall_refined"]:.2f}]" for t, z in f["cert"].items()), flush=True)
            Path(a.out).write_text(json.dumps(res, indent=1))
