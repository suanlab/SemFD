"""E11 (paper Sec. VI, "Proxies and the miss mass"): incomplete inverse access, and what the audit catches.

Part A. Real alias services rarely list every in-data spelling of an entity. Here an alias lookup
returns each in-data spelling of the entity only with probability p (a fixed hash of the value, so
the same spellings are missing on every call); p = 1 is the complete inverse of the main
experiments, p = 0 leaves the proxy neighbors only. The certificate is run unchanged, as if the
inverse were complete (nu_bar = 0), over all unary candidates (family-wise alpha, shared caches).
Recorded per run: false certifications and missed true FDs against the oracle truth, oracle calls,
and the measured miss mass nu of every candidate under that incomplete inverse (Thm 1).

Part A' (--official). A systematic incomplete inverse: the alias lookup returns only an entity's registered
names (GeoNames: the ASCII name and GeoNames alternate names, country aliases; Tax: the clean value, the state's
full name and the USPS-style city abbreviations), never typos, drops or other noise, which are left to the proxy.
Output tag _official; the tuple mass covered by the registered names is recorded per attribute.

Part B (p = 1). For every candidate, the exact mean of B over all tuples split into the mass caught
by condition (i) and the mass caught only by condition (ii) (the cross-cluster audit), next to the
oracle g3 and the string-level g3, so the audit's contribution on natural candidates is visible.
Output: results/icde27/e11_partial_inverse_<dataset><tag>.json
"""

import argparse
import hashlib
import json
import sys
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semfd.certify import certify, g3_codes, witness  # noqa: E402
from semfd.data import LOADERS  # noqa: E402
from semfd.oracle import Canonicalizer, total_calls  # noqa: E402
from semfd.probes import base_attr as base, is_probe_fd  # noqa: E402


REG = {}          # --official: base attribute -> set of registered (Layer-1) names


def keep(v, p, seed, attr=None):
    if p == "official":
        return v in REG.get(base(attr), ())
    if p >= 1:
        return True
    h = int(hashlib.sha1(f"{seed}|{v}".encode()).hexdigest()[:8], 16) / 16 ** 8
    return h < p


def oracles(ds, p, seed):
    out, by_table = {}, {}
    for a in ds.exact:
        if a in ds.oracle:
            key = id(ds.oracle[a])
            if key not in by_table:
                tab, by_ent = ds.oracle[a], {}
                for v, e in tab.items():
                    if keep(v, p, seed, a):
                        by_ent.setdefault(e, []).append(v)
                by_table[key] = Canonicalizer(tab.__getitem__, lambda e, b=by_ent: b.get(e, []), name=a)
            out[a] = by_table[key]
        else:
            out[a] = Canonicalizer(lambda v: v, lambda e: [e], name=a, free=ds.exact[a])
    return out


def nu_partial(ax, ay, xent, yent, theta, tab, p, seed, attr=None):
    """Miss mass of Thm 1 when N(a) = proxy neighbors + the kept spellings of a's entity."""
    lab, rep, prio = witness(ax, ay, theta)
    by_ent = {}
    for v, e in enumerate(xent):
        by_ent.setdefault(e, []).append(v)
    known = np.array([tab is None or keep(ax.vals[v], p, seed, attr) for v in range(len(ax.vals))])
    bad = np.zeros(len(xent), bool)
    for vs in by_ent.values():
        if len(vs) < 2:
            continue
        for i in vs:
            ri, nb = rep.get(int(lab[i])), set(ax.nbrs[i].tolist())
            if ri is None:
                continue
            for j in vs:
                if i == j or lab[i] == lab[j] or j in nb or known[j]:
                    continue
                rj = rep.get(int(lab[j]))
                if rj is not None and yent[ri] != yent[rj] and prio[lab[i]] < prio[lab[j]]:
                    bad[i] = True
                    break
    return float(bad[ax.codes].mean())


def b_split(ax, ay, xent, yent, theta):
    """Exact tuple mass with B = 1 by condition (i), and by condition (ii) only (complete inverse)."""
    lab, rep, prio = witness(ax, ay, theta)
    by_ent = {}
    for v, e in enumerate(xent):
        by_ent.setdefault(e, []).append(v)
    ii = np.zeros(len(xent), bool)
    for vs in by_ent.values():
        for i in vs:
            ri = rep.get(int(lab[i]))
            for j in vs:
                if lab[j] == lab[i]:
                    continue
                rj = rep.get(int(lab[j]))
                if rj is not None and ri is not None and yent[rj] != yent[ri] and prio[lab[j]] > prio[lab[i]]:
                    ii[i] = True
                    break
    tl = lab[ax.codes]
    rep_y = np.array([yent[rep[int(c)]] for c in tl])
    cond_i = yent[ay.codes] != rep_y
    return float(cond_i.mean()), float((~cond_i & ii[ax.codes]).mean())


def registry(dataset, ds, seed, kw):
    """Registered names per attribute (Layer-1), as an alias service would list them."""
    from semfd.proxy import layer1
    if dataset == "geonames":
        sys.path[:0] = [str(ROOT / "pilot")]
        import p0b_geonames
        c, a1name, cname = p0b_geonames.load(kw.get("n_cities", 1000), seed)
        city = set(c["key"])
        for alt, key in zip(c["alt"], c["key"]):
            city |= {layer1(x) for x in p0b_geonames.ascii_alts(alt, key)}
        country = {layer1(v) for v in cname.values()} | {layer1(x) for v in p0b_geonames.COUNTRY_ALIASES.values() for x in v}
        return {"city": city, "country": country, "admin1": {layer1(v) for v in a1name.values()}}
    if dataset == "tax":
        import pandas as pd
        from semfd.data import _abbr_variants
        c = pd.read_csv(ROOT / "data/tax/clean.csv", dtype=str, keep_default_na=False)
        sname = {}
        for line in (ROOT / "data/geonames/admin1CodesASCII.txt").read_text(encoding="utf-8").splitlines():
            f = line.split("\t")
            if f[0].startswith("US."):
                sname[f[0][3:]] = f[2]
        reg = {x: {layer1(v) for v in c[x].unique()} for x in ("f_name", "city", "state")}
        reg["state"] |= {layer1(sname[v]) for v in c["state"].unique() if v in sname}
        reg["city"] |= {layer1(w) for v in c["city"].unique() for w in _abbr_variants(v)}
        return reg
    raise ValueError(f"no registry for {dataset}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="geonames")
    ap.add_argument("--kw", default="{}")
    ap.add_argument("--fractions", type=float, nargs="+", default=[1.0, 0.8, 0.5, 0.0])
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--theta0", type=float, default=0.9)
    ap.add_argument("--tag", default="")
    ap.add_argument("--official", action="store_true", help="inverse returns registered names only (Part A')")
    a = ap.parse_args()
    outp = ROOT / f"results/icde27/e11_partial_inverse_{a.dataset}{a.tag}{'_official' if a.official else ''}.json"
    res = {"args": vars(a), "runs": [], "audit_split": []}
    for s in range(a.seeds):
        ds = LOADERS[a.dataset](seed=s, **json.loads(a.kw))
        attrs = ds.attrs()
        ent = ds.entity_codes(attrs)
        names = list(attrs)
        cands = [(x, y) for x in names for y in names if x != y and base(x) != base(y)]
        truth = {(x, y): g3_codes(ent[x][attrs[x].codes], ent[y][attrs[y].codes]) for x, y in cands}
        af = a.alpha / len(cands)
        if a.official:
            REG.clear()
            REG.update(registry(a.dataset, ds, s, json.loads(a.kw)))
            res.setdefault("coverage", []).append(
                {"seed": s, **{x: float(np.isin(attrs[x].codes, [i for i, v in enumerate(attrs[x].vals) if v in REG.get(x, ())]).mean())
                               for x in REG if x in attrs}})
        if s == 0 and not a.official:
            for x, y in cands:
                if ds.exact[x]:
                    continue
                ci, cii = b_split(attrs[x], attrs[y], ent[x], ent[y], a.theta0)
                res["audit_split"].append({"fd": f"{x}->{y}", "probe": is_probe_fd(f"{x}->{y}"), "g3": truth[(x, y)],
                                           "g3_string": g3_codes(attrs[x].codes, attrs[y].codes),
                                           "mass_i": ci, "mass_ii_only": cii})
        for p in (["official"] if a.official else a.fractions):
            orcs = oracles(ds, p, s)
            cert, nus = set(), {}
            for x, y in cands:
                r = certify(attrs[x], attrs[y], orcs[x], orcs[y], a.theta0, a.delta, af,
                            np.random.default_rng(zlib.crc32(f"e11|{s}|{p}|{x}|{y}".encode())), inverse=True)
                if r["certified"]:
                    cert.add((x, y))
                if not ds.exact[x]:
                    nus[f"{x}->{y}"] = nu_partial(attrs[x], attrs[y], ent[x], ent[y], a.theta0,
                                                  ds.oracle.get(x), p, s, x)
            T = {c for c in cands if truth[c] <= a.delta}
            rec = {"seed": s, "p": p, "n_cands": len(cands), "n_true": len(T),
                   "false": sorted(f"{x}->{y}" for x, y in cert - T),
                   "missed": sorted(f"{x}->{y}" for x, y in T - cert),
                   "calls": total_calls(orcs), "nu_max": max(nus.values(), default=0.0),
                   "nu_mean": float(np.mean(list(nus.values()))) if nus else 0.0,
                   "nu_over_0.01": sum(v > 0.01 for v in nus.values()), "nu": nus}
            res["runs"].append(rec)
            print(f"seed={s} p={p} false={len(rec['false'])} {rec['false']} missed={len(rec['missed'])} "
                  f"calls={rec['calls']} nu_max={rec['nu_max']:.4f}", flush=True)
            outp.write_text(json.dumps(res, indent=1))
