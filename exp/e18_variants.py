"""E18 (paper Sec. VI; pre-registered in literature/prereg_e18_2026-10-23.md): variants of unary discovery.

Same candidates, oracles (complete inverse), alpha/|C| and per-candidate random streams as E1b, so every variant is
paired with E1b's plain run (the 'plain' variant must reproduce e1b_*.json exactly). Variants:
  plain              hybrid proxy, audit over proxy neighbours U alias class (the system)
  refine             self-refining witness, alias classes fetched by this candidate only
  refine_warm        self-refining witness, also alias classes fetched by earlier candidates (shared cache)
  tfidf_union        TF-IDF proxy, same audit
  hybrid_aliasonly   audit over the alias class only (ann=False; nu = 0 under a complete inverse)
  tfidf_aliasonly
  budget_<gamma>     plain under a run-wide budget gamma * C_full (C_full = canonicalize-all forward calls):
                     once forward + inverse calls reach it, certification stops, the remaining values of every
                     tolerant attribute are resolved (spellings already listed by a fetched alias class are known
                     and cost nothing), and the current and remaining candidates are decided by the exact g3.
                     Cost <= gamma * C_full + one batch + C_full.
Output: results/icde27/e18_variants_<dataset><tag>.json
"""

import argparse
import json
import resource
import sys
import time
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semfd.certify import certify, g3_codes  # noqa: E402
from semfd.data import LOADERS  # noqa: E402
from semfd.oracle import calls_split, total_calls  # noqa: E402
from semfd.probes import base_attr as base  # noqa: E402

VARIANTS = {"plain": ("hybrid", {}), "refine": ("hybrid", {"refine": True}),
            "refine_warm": ("hybrid", {"refine": "warm"}), "tfidf_union": ("tfidf", {}),
            "hybrid_aliasonly": ("hybrid", {"ann": False}), "tfidf_aliasonly": ("tfidf", {"ann": False})}
GAMMAS = (0.25, 0.5, 1.0)

def exact_ids(f, vals, known):
    """Entity ids of vals from the cache or from fetched alias classes (no call), else one forward call."""
    m = {}
    out = []
    for v in vals:
        e = f.cache[v] if v in f.cache else known.get(v)
        if e is None:
            e = f(v)
        out.append(m.setdefault(e, len(m)))
    return np.array(out)


def run_variant(ds, attrs, cands, truth, delta, alpha, theta0, seed, kw, gamma=None):
    orcs = ds.oracles(inverse=True)
    uniq = list({id(o): o for o in orcs.values() if not o.free}.values())
    c_full = ds.canon_all_cost(attrs, list(attrs))
    af = alpha / len(cands)
    spent = lambda: sum(o.calls for o in uniq)
    t0 = time.perf_counter()
    cert, recs, fallback = set(), [], None
    for i, (x, y) in enumerate(cands):
        rng = np.random.default_rng(zlib.crc32(f"e1b|{seed}|{x}|{y}".encode()))
        mode = "certificate"
        if gamma is not None and fallback is None:
            cap = gamma * c_full - spent()
            r = None
            if cap > 0:
                r = certify(attrs[x], attrs[y], orcs[x], orcs[y], theta0, delta, af, rng, inverse=True,
                            max_calls=cap, **kw)
            if r is None or r["budget_hit"]:
                known = {id(o): {v: e for e, vs in o.inv_cache.items() for v in vs} for o in uniq}
                before = spent()
                ids = {a: exact_ids(orcs[a], attrs[a].vals, known[id(orcs[a])])
                       if not orcs[a].free else np.arange(len(attrs[a].vals)) for a in attrs}
                fallback = {"at_candidate": i, "spent_before": before, "resolve_calls": spent() - before}
        if fallback is not None:
            mode = "resolved"
            g = g3_codes(ids[x][attrs[x].codes], ids[y][attrs[y].codes])
            ok = bool(g <= delta)
        else:
            if gamma is None:
                r = certify(attrs[x], attrs[y], orcs[x], orcs[y], theta0, delta, af, rng, inverse=True, **kw)
            ok = r["certified"]
        if ok:
            cert.add((x, y))
        recs.append({"fd": f"{x}->{y}", "g3": float(truth[(x, y)]), "mode": mode, "certified": ok})
    T = {c for c in cands if truth[c] <= delta}
    calls = total_calls(orcs)
    return {"false": sorted(f"{x}->{y}" for x, y in cert - T), "missed": sorted(f"{x}->{y}" for x, y in T - cert),
            "n_cert": len(cert), "calls": int(calls), "calls_fwd_inv": calls_split(orcs), "canon_all": c_full,
            "gamma": gamma, "overshoot": None if fallback is None else max(0, fallback["spent_before"] - gamma * c_full),
            "within_bound": None if gamma is None else bool(calls <= (1 + gamma) * c_full + (
                0 if fallback is None else max(0, fallback["spent_before"] - gamma * c_full))),
            "fallback": fallback, "sec": time.perf_counter() - t0, "fds": recs}


def run_one(ds, delta, alpha, theta0, k, seed, which):
    ent, out, built = None, {}, {}
    for name in which:
        proxy, kw = VARIANTS.get(name, ("hybrid", {}))
        if proxy not in built:
            t0 = time.perf_counter()
            built[proxy] = (ds.attrs(proxy=proxy, k=k), time.perf_counter() - t0)
        attrs, t_proxy = built[proxy]
        if ent is None:
            names = list(attrs)
            ent = ds.entity_codes(attrs)
            cands = [(x, y) for x in names for y in names if x != y and base(x) != base(y) and (x, y) not in ds.exclude]
            truth = {(x, y): g3_codes(ent[x][attrs[x].codes], ent[y][attrs[y].codes]) for x, y in cands}
        gamma = float(name.split("_")[1]) if name.startswith("budget_") else None
        r = run_variant(ds, attrs, cands, truth, delta, alpha, theta0, seed, kw, gamma)
        r["proxy"], r["proxy_sec"] = proxy, t_proxy
        out[name] = r
        print(f"{ds.name} seed={seed} {name}: false={r['false']} missed={r['missed']} calls={r['calls']} "
              f"{r['calls_fwd_inv']} canon_all={r['canon_all']} fallback={r['fallback']} sec={r['sec']:.1f}", flush=True)
    return {"dataset": ds.name, "seed": seed, "rows": len(ds.df), "n_cands": len(cands),
            "n_true": sum(g <= delta for g in truth.values()), "variants": out}


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
    ap.add_argument("--variants", nargs="+", default=list(VARIANTS) + [f"budget_{g}" for g in GAMMAS])
    a = ap.parse_args()
    outp = ROOT / f"results/icde27/e18_variants_{a.dataset}{a.tag}.json"
    res = {"args": vars(a), "runs": []}
    for s in range(a.seeds):
        ds = LOADERS[a.dataset](seed=s, **json.loads(a.kw))
        res["runs"].append(run_one(ds, a.delta, a.alpha, a.theta0, a.k, s, a.variants))
        res["peak_rss_mb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        outp.write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
