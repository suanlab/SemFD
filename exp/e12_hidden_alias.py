"""E12 (paper Sec. VI, "Hidden aliases"): the failure that motivates inverse access (Theorem 3).

On GeoNames (16k cities, rho=0.5), inject a two-source conflict city -> country_hid only on tuples whose city
spelling is a GeoNames alternate name of its entity that lies outside the proxy's k-NN of every other in-data
spelling of that entity, in both directions (hybrid proxy: TF-IDF top-k and embedding top-k, so the spelling is
outside the top-k of each). The proxy cannot link these spellings to their entity, so certification with neighbor
sets only (declared nu_bar) cannot see the conflict, while the inverse (alias list) returns them.
Per seed: true and string g3, the inverse and neighbor-only certificates (certified, U, calls), the measured miss
mass nu of the neighbor-only run, and the injected mass. Output: results/icde27/e12_hidden_alias.json
"""

import argparse
import json
import sys
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "pilot")]
from semfd.certify import certify, g3_codes, miss_mass  # noqa: E402
from semfd.data import LOADERS  # noqa: E402
from semfd.proxy import Attr, layer1  # noqa: E402


def hidden_aliases(ax, tab, alias_of):
    """Codes of city spellings that are alternate names of their entity, are not its most frequent spelling, and
    share no k-NN edge (either direction) with any other in-data spelling of the entity."""
    ent = [tab[v] for v in ax.vals]
    cnt = np.bincount(ax.codes, minlength=len(ax.vals))
    by = {}
    for i, e in enumerate(ent):
        by.setdefault(e, []).append(i)
    nb = [set(map(int, r)) for r in ax.nbrs]
    out = {}
    for e, vs in by.items():
        if len(vs) < 2:
            continue
        maj = max(vs, key=lambda i: (cnt[i], -i))
        for v in vs:
            if v == maj or ax.vals[v] not in alias_of.get(e, ()):
                continue
            if all(u not in nb[v] and v not in nb[u] for u in vs if u != v):
                out.setdefault(e, []).append(v)
    return out, cnt


def run(seed, target, rho, n_cities, k, theta0, delta, alpha_fd, nu_bar):
    import p0b_geonames
    ds = LOADERS["geonames"](seed=seed, n_cities=n_cities, rho=rho)
    c, _, _ = p0b_geonames.load(n_cities, seed)
    alias_of = {g: {layer1(a) for a in p0b_geonames.ascii_alts(alt, key)} for g, alt, key in zip(c["gid"], c["alt"], c["key"])}
    ax = Attr("city", ds.df["city"], proxy="hybrid", k=k)
    tab = ds.oracle["city"]
    hid, cnt = hidden_aliases(ax, tab, alias_of)
    same = {}                               # the check the claim rests on: no k-NN edge to an oracle-equal spelling
    for i, val in enumerate(ax.vals):
        same.setdefault(tab[val], set()).add(i)
    for e, vs in hid.items():
        for v in vs:
            assert not (same[e] - {v}) & set(map(int, ax.nbrs[v]))
            assert all(v not in set(map(int, ax.nbrs[u])) for u in same[e] - {v})
    n = len(ax.codes)
    avail = sum(cnt[v] for vs in hid.values() for v in vs) / n
    rng = np.random.default_rng(seed + 5000)
    ents = sorted(hid, key=str)
    rng.shuffle(ents)
    chosen, mass = [], 0.0
    for e in ents:
        if mass >= target:
            break
        chosen.append(e)
        mass += sum(cnt[v] for v in hid[e]) / n
    hidden_codes = {v for e in chosen for v in hid[e]}
    yo = ds.oracle["country"]
    col = ds.df["country"].to_numpy(dtype=object).copy()
    ye = np.array([yo[layer1(v)] for v in col], dtype=object)
    alt = {}
    for i in np.flatnonzero(np.isin(ax.codes, list(hidden_codes))):
        key = int(ax.codes[i])
        if key not in alt:
            while True:
                j = int(rng.integers(n))
                if ye[j] != ye[i]:
                    alt[key] = col[j]
                    break
        col[i] = alt[key]
    ds.df["country_hid"] = col
    ds.oracle["country_hid"] = yo
    ds.exact["country_hid"] = False
    ay = Attr("country_hid", ds.df["country_hid"], proxy="hybrid", k=k)
    ent = ds.entity_codes({"city": ax, "country_hid": ay})
    g3 = g3_codes(ent["city"][ax.codes], ent["country_hid"][ay.codes])
    rec = {"seed": seed, "rows": n, "hidden_alias_mass_available": avail, "injected_mass": mass,
           "n_hidden_spellings": len(hidden_codes), "examples": [ax.vals[v] for v in sorted(hidden_codes)[:5]],
           "g3": g3, "g3_string": g3_codes(ax.codes, ay.codes), "truth": bool(g3 <= delta), "ours": {}}
    for v, inv, nb_ in (("inverse", True, 0.0), ("ann_nubar", False, nu_bar)):
        orcs = ds.oracles(inverse=inv)
        r = certify(ax, ay, orcs["city"], orcs["country_hid"], theta0, delta, alpha_fd,
                    np.random.default_rng(zlib.crc32(f"e12|{seed}|{v}".encode())), inverse=inv, nu_bar=nb_)
        r["nu"] = miss_mass(ax, ay, ent["city"], ent["country_hid"], theta0, inverse=inv)
        rec["ours"][v] = r
    return rec


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--target", type=float, default=0.08)
    ap.add_argument("--rho", type=float, default=0.5)
    ap.add_argument("--n-cities", type=int, default=16000)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--theta0", type=float, default=0.9)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--alpha-fd", type=float, default=0.05 / 13, help="E1 GeoNames per-FD level (alpha / 13 FDs)")
    ap.add_argument("--nu-bar", type=float, default=0.01)
    a = ap.parse_args()
    res = {"config": vars(a), "runs": []}
    for s in range(a.seeds):
        r = run(s, a.target, a.rho, a.n_cities, a.k, a.theta0, a.delta, a.alpha_fd, a.nu_bar)
        res["runs"].append(r)
        print(f"seed={s} avail={r['hidden_alias_mass_available']:.3f} injected={r['injected_mass']:.3f} g3={r['g3']:.3f} "
              f"str={r['g3_string']:.3f} " + " ".join(f"{v}:{'C' if z['certified'] else '-'}/U={z['ub']:.3f}/"
                                                      f"calls={z['calls']}/nu={z['nu']:.3f}" for v, z in r["ours"].items()),
              flush=True)
    out = ROOT / "results/icde27/e12_hidden_alias.json"
    out.write_text(json.dumps(res, indent=1, default=float))
