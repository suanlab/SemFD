"""E11 (paper Sec. VI, "Proxies and the miss mass"): incomplete inverse access, and what the audit catches.

Part A. Real alias services rarely list every in-data spelling of an entity. Here an alias lookup
returns each in-data spelling of the entity only with probability p (a fixed hash of the value, so
the same spellings are missing on every call); p = 1 is the complete inverse of the main
experiments, p = 0 leaves the proxy neighbors only. The certificate is run unchanged, as if the
inverse were complete (nu_bar = 0), over all unary candidates (family-wise alpha, shared caches).
Recorded per run: false certifications and missed true FDs against the oracle truth, oracle calls,
and the measured miss mass nu of every candidate under that incomplete inverse (Thm 1).

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


def keep(v, p, seed):
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
                    if keep(v, p, seed):
                        by_ent.setdefault(e, []).append(v)
                by_table[key] = Canonicalizer(tab.__getitem__, lambda e, b=by_ent: b.get(e, []), name=a)
            out[a] = by_table[key]
        else:
            out[a] = Canonicalizer(lambda v: v, lambda e: [e], name=a, free=ds.exact[a])
    return out


def nu_partial(ax, ay, xent, yent, theta, tab, p, seed):
    """Miss mass of Thm 1 when N(a) = proxy neighbors + the kept spellings of a's entity."""
    lab, rep, prio = witness(ax, ay, theta)
    by_ent = {}
    for v, e in enumerate(xent):
        by_ent.setdefault(e, []).append(v)
    known = np.array([tab is None or keep(ax.vals[v], p, seed) for v in range(len(ax.vals))])
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
    a = ap.parse_args()
    outp = ROOT / f"results/icde27/e11_partial_inverse_{a.dataset}{a.tag}.json"
    res = {"args": vars(a), "runs": [], "audit_split": []}
    for s in range(a.seeds):
        ds = LOADERS[a.dataset](seed=s, **json.loads(a.kw))
        attrs = ds.attrs()
        ent = ds.entity_codes(attrs)
        names = list(attrs)
        cands = [(x, y) for x in names for y in names if x != y and base(x) != base(y)]
        truth = {(x, y): g3_codes(ent[x][attrs[x].codes], ent[y][attrs[y].codes]) for x, y in cands}
        af = a.alpha / len(cands)
        if s == 0:
            for x, y in cands:
                if ds.exact[x]:
                    continue
                ci, cii = b_split(attrs[x], attrs[y], ent[x], ent[y], a.theta0)
                res["audit_split"].append({"fd": f"{x}->{y}", "probe": is_probe_fd(f"{x}->{y}"), "g3": truth[(x, y)],
                                           "g3_string": g3_codes(attrs[x].codes, attrs[y].codes),
                                           "mass_i": ci, "mass_ii_only": cii})
        for p in a.fractions:
            orcs = oracles(ds, p, s)
            cert, nus = set(), {}
            for x, y in cands:
                r = certify(attrs[x], attrs[y], orcs[x], orcs[y], a.theta0, a.delta, af,
                            np.random.default_rng(zlib.crc32(f"e11|{s}|{p}|{x}|{y}".encode())), inverse=True)
                if r["certified"]:
                    cert.add((x, y))
                if not ds.exact[x]:
                    nus[f"{x}->{y}"] = nu_partial(attrs[x], attrs[y], ent[x], ent[y], a.theta0,
                                                  ds.oracle.get(x), p, s)
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
