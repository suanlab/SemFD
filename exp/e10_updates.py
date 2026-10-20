"""E10 (paper Sec. VI, "Under change"): certificates while the table changes.

GeoNames (cities500): the generated table is split into an initial version r_0 (half of the
rows) and a pool; each of T versions inserts `ins` x |r_0| pool rows (new cities and new
spellings of known ones) and deletes `dele` x |r_0| random current rows. The oracle is fixed.
All unary candidates (as in E1b) are decided at every version by four policies:

  cold      re-run discovery from scratch on every version (fresh oracle caches)
  warm      re-run every candidate on every version, reusing the oracle cache
  maintain  keep a certified FD while its propagated bound (semfd.maintain) stays <= delta;
            re-run (warm cache) only candidates whose bound exceeds delta or that were not
            certified; certification samples until U < stop_at (slack for later versions)
  canon     incremental canonicalize-all: pays only for distinct values not seen before
            (and decides every candidate exactly)

Inverse access is realistic: an alias lookup returns the spellings present in the data at query
time, so cached alias lists go stale; every version clears the inverse caches of the warm and
maintain policies and pays for its lookups again (forward canonicalizations stay cached, the
oracle is fixed).
Levels: version j runs its certificates at alpha/2^(j+1)/|C| (semfd.maintain.alpha_schedule),
so the guarantee covers all versions at once with probability >= 1 - alpha.
Recorded per version: cumulative oracle calls per policy, re-certifications, false
certifications against the oracle truth of that version, and propagated bounds below truth.
Output: results/icde27/e10_updates<tag>.json
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
from semfd.certify import certify, g3_codes  # noqa: E402
from semfd.data import geonames  # noqa: E402
from semfd.maintain import alpha_schedule, propagate  # noqa: E402
from semfd.oracle import Canonicalizer, total_calls  # noqa: E402
from semfd.probes import base_attr as base  # noqa: E402
from semfd.proxy import Attr  # noqa: E402


def version_attrs(ds, rows):
    sub = ds.df.iloc[rows].reset_index(drop=True)
    return {a: Attr(a, sub[a], exact=ds.exact[a]) for a in ds.exact}


def entity_codes(ds, attrs):
    out = {}
    for a, at in attrs.items():
        tab = ds.oracle.get(a)
        ents = [tab[v] if tab else v for v in at.vals]
        eid = {e: i for i, e in enumerate(dict.fromkeys(ents))}
        out[a] = np.array([eid[e] for e in ents])
    return out


def oracles(ds, present):
    """Inverse-access oracles whose alias lists contain only spellings in `present` (attr -> set),
    mutated in place as versions change."""
    out, by_table = {}, {}
    for at in ds.exact:
        if at in ds.oracle:
            key = id(ds.oracle[at])
            if key not in by_table:
                tab, by_ent = ds.oracle[at], {}
                for v, e in tab.items():
                    by_ent.setdefault(e, []).append(v)
                cur = present.setdefault(key, set())
                by_table[key] = Canonicalizer(tab.__getitem__, lambda e, b=by_ent, c=cur: [v for v in b.get(e, []) if v in c],
                                              name=at)
            out[at] = by_table[key]
        else:
            out[at] = Canonicalizer(lambda v: v, lambda e: [e], name=at, free=ds.exact[at])
    return out


def calls(orcs, inv_paid):
    return total_calls(orcs) + inv_paid


def run(ds, a, seed):
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(ds.df))
    n0 = len(perm) // 2
    cur, pool = list(perm[:n0]), list(perm[n0:])
    n_ins, n_del = int(a.ins * n0), int(a.dele * n0)
    names = list(ds.exact)
    cands = [(x, y) for x in names for y in names if x != y and base(x) != base(y)]
    present = {}
    orc = {p: oracles(ds, present) for p in ("warm", "maintain")}
    inv_paid = {"warm": 0, "maintain": 0}
    cum = {"cold": 0, "canon": 0}
    seen = {}                                     # oracle table id -> distinct values seen (canon)
    state = {}                                    # maintain: fd -> (U, N at certification, D, I)
    out = {"seed": seed, "n0": n0, "ins": n_ins, "del": n_del, "candidates": len(cands), "versions": []}
    for j in range(a.versions + 1):
        if j > 0:
            ins = pool[:n_ins]
            pool = pool[n_ins:]
            drop = set(rng.choice(len(cur), n_del, replace=False).tolist())
            cur = [r for i, r in enumerate(cur) if i not in drop] + ins
            for fd, (u, n, d, i_) in list(state.items()):
                state[fd] = (u, n, d + n_del, i_ + n_ins)
        t0 = time.perf_counter()
        attrs = version_attrs(ds, cur)
        for at in names:
            if at in ds.oracle:
                present.setdefault(id(ds.oracle[at]), set())
        for key in present:
            present[key].clear()
        for at in names:
            if at in ds.oracle:
                present[id(ds.oracle[at])].update(attrs[at].vals)
        for p in ("warm", "maintain"):          # stale alias lists: pay again in this version
            seen_o = {id(o): o for o in orc[p].values()}.values()
            inv_paid[p] += sum(len(o.inv_cache) for o in seen_o if not o.free)
            for o in seen_o:
                o.inv_cache.clear()
        ent = entity_codes(ds, attrs)
        truth = {(x, y): g3_codes(ent[x][attrs[x].codes], ent[y][attrs[y].codes]) for x, y in cands}
        new_vals = 0
        for at in names:
            if ds.exact[at] or at not in ds.oracle:
                continue
            s = seen.setdefault(id(ds.oracle[at]), set())
            before = len(s)
            s.update(attrs[at].vals)
            new_vals += len(s) - before
        cum["canon"] += new_vals
        af = alpha_schedule(a.alpha, j) / len(cands)
        rec = {"version": j, "rows": len(cur), "canon_new_values": new_vals, "rerun": 0, "kept_free": 0,
               "false_cert": {"cold": 0, "warm": 0, "maintain": 0}, "missed_true": {"cold": 0, "warm": 0, "maintain": 0},
               "bound_below_truth": 0, "true_fds": int(sum(g <= a.delta for g in truth.values()))}
        cold = oracles(ds, present)
        for x, y in cands:
            ax, ay = attrs[x], attrs[y]
            key = f"{x}->{y}"
            g = truth[(x, y)]
            for pol, o in (("cold", cold), ("warm", orc["warm"])):
                r = certify(ax, ay, o[x], o[y], a.theta0, a.delta, af,
                            np.random.default_rng(zlib.crc32(f"e10|{pol}|{seed}|{j}|{key}".encode())), inverse=True)
                rec["false_cert"][pol] += int(r["certified"] and g > a.delta)
                rec["missed_true"][pol] += int(not r["certified"] and g <= a.delta)
            st = state.get(key)
            bound = propagate(*st) if st else 1.0
            if st and bound <= a.delta:
                rec["kept_free"] += 1
                rec["bound_below_truth"] += int(g > bound + 1e-12)
                cert = True
            else:
                rec["rerun"] += 1
                o = orc["maintain"]
                r = certify(ax, ay, o[x], o[y], a.theta0, a.delta, af,
                            np.random.default_rng(zlib.crc32(f"e10|maintain|{seed}|{j}|{key}".encode())),
                            inverse=True, stop_at=a.stop_at)
                cert = r["certified"]
                if cert:
                    state[key] = (r["ub"], len(cur), 0, 0)
                else:
                    state.pop(key, None)
            rec["false_cert"]["maintain"] += int(cert and g > a.delta)
            rec["missed_true"]["maintain"] += int(not cert and g <= a.delta)
        cum["cold"] += total_calls(cold)
        rec["cum_calls"] = {"cold": cum["cold"], "warm": calls(orc["warm"], inv_paid["warm"]),
                            "maintain": calls(orc["maintain"], inv_paid["maintain"]), "canon": cum["canon"]}
        rec["sec"] = time.perf_counter() - t0
        out["versions"].append(rec)
        print(f"seed={seed} v={j} rows={len(cur)} rerun={rec['rerun']} kept={rec['kept_free']} "
              f"calls={rec['cum_calls']} false={rec['false_cert']} missed={rec['missed_true']} "
              f"below={rec['bound_below_truth']} {rec['sec']:.0f}s", flush=True)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-cities", type=int, default=32000)
    ap.add_argument("--source", default="cities500.txt")
    ap.add_argument("--versions", type=int, default=10)
    ap.add_argument("--ins", type=float, default=0.02, help="inserted rows per version, fraction of |r_0|")
    ap.add_argument("--dele", type=float, default=0.01, help="deleted rows per version, fraction of |r_0|")
    ap.add_argument("--stop-at", type=float, default=0.025, help="maintain policy: sample until U < stop_at")
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--theta0", type=float, default=0.9)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    outp = ROOT / f"results/icde27/e10_updates{a.tag}.json"
    res = {"args": vars(a), "runs": []}
    for s in range(a.seeds):
        ds = geonames(n_cities=a.n_cities, seed=s, source=a.source)
        res["runs"].append(run(ds, a, s))
        outp.write_text(json.dumps(res, indent=1))
