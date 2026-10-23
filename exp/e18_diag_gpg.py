"""Diagnostic for E18 (MODIFY.md Sec. 8, H1 vs H2): why does the self-refining witness not recover GPG name -> sic?

Replays E18's candidate sequence (same oracles, complete inverse, alpha/|C|, random streams) for the plain, refine and
refine_warm variants and, for name -> sic only, computes from the oracle truth (diagnostic only, never an algorithm
input) the exact mean mu = E[B] of
  - the initial proxy witness, and
  - the final refined witness: the proxy partition with every alias class the run had applied split off as its own
    cluster (refine: classes fetched by this candidate; refine_warm: all classes fetched so far).
H1: mu_final stays near the target delta, so no amount of sampling certifies.  H2: mu_final is well below the target
and only the early batches (larger conditional means) keep the confidence sequence above it.
Output: results/icde27/e18_diag_gpg.json
"""

import json
import sys
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semfd.certify import certify, g3_codes, witness, witness_from  # noqa: E402
from semfd.data import LOADERS  # noqa: E402
from semfd.probes import base_attr as base  # noqa: E402

TARGET = ("name", "sic")


def mu_exact(lab, ax, ay, xent, yent):
    """E[B] for the witness given by partition lab (representatives and priorities as in certify), complete inverse."""
    rep, prio = witness_from(lab, ax, ay)
    tl = lab[ax.codes]
    ty = yent[ay.codes]
    cond_i = ty != np.array([yent[rep[int(c)]] for c in tl])
    ent_cl = {}
    for v, e in enumerate(xent):
        ent_cl.setdefault(e, set()).add(int(lab[v]))
    ii = np.zeros(len(xent), bool)
    for v, e in enumerate(xent):
        c = int(lab[v])
        ry = yent[rep[c]]
        ii[v] = any(prio[c2] > prio[c] and yent[rep[c2]] != ry for c2 in ent_cl[e])
    return float((cond_i | ii[ax.codes]).mean())


def main(seeds=3, delta=0.05, alpha=0.05, theta0=0.9, k=5):
    out = []
    for s in range(seeds):
        ds = LOADERS["gpg"](seed=s)
        attrs = ds.attrs(proxy="hybrid", k=k)
        ent = ds.entity_codes(attrs)
        names = list(attrs)
        cands = [(x, y) for x in names for y in names if x != y and base(x) != base(y) and (x, y) not in ds.exclude]
        af = alpha / len(cands)
        ax, ay = attrs[TARGET[0]], attrs[TARGET[1]]
        xent, yent = ent[TARGET[0]], ent[TARGET[1]]
        lab0, _, _ = witness(ax, ay, theta0)
        mu0 = mu_exact(lab0, ax, ay, xent, yent)
        g3 = float(g3_codes(xent[ax.codes], yent[ay.codes]))
        xidx = {v: i for i, v in enumerate(ax.vals)}
        for variant, kw in (("plain", {}), ("refine", {"refine": True}), ("refine_warm", {"refine": "warm"})):
            orcs = ds.oracles(inverse=True)
            for x, y in cands:
                rng = np.random.default_rng(zlib.crc32(f"e1b|{s}|{x}|{y}".encode()))
                if (x, y) != TARGET:
                    certify(attrs[x], attrs[y], orcs[x], orcs[y], theta0, delta, af, rng, inverse=True, **kw)
                    continue
                fx = orcs[x]
                n_before = len(fx.inv_cache)
                r = certify(ax, ay, fx, orcs[y], theta0, delta, af, rng, inverse=True, **kw)
                rec = {"seed": s, "variant": variant, "g3": g3, "mu_initial": mu0, "certified": bool(r["certified"]),
                       "ub": float(r["ub"]), "samples": int(r["samples"]), "calls": int(r["calls"]),
                       "mean_B": float(r.get("mean", np.nan)) if "mean" in r else None}
                if kw:
                    start = 0 if kw["refine"] == "warm" else n_before
                    lab = lab0.copy()
                    nxt = int(lab.max()) + 1
                    split = 0
                    for e_, vs in list(fx.inv_cache.items())[start:]:
                        ids = [xidx[v] for v in vs if v in xidx]
                        if ids:
                            lab[ids] = nxt
                            nxt += 1
                            split += 1
                    rec["mu_final"] = mu_exact(lab, ax, ay, xent, yent)
                    rec["classes_split"] = split
                out.append(rec)
                print(rec, flush=True)
    (ROOT / "results/icde27/e18_diag_gpg.json").write_text(json.dumps({"target": "->".join(TARGET), "delta": delta,
                                                                       "rows": out}, indent=1))


if __name__ == "__main__":
    main()
