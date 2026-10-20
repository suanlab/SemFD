"""Generic g3 repair certificate (pilot version of semfd/certify.py).

Cost model: the oracle is a CANONICALIZER --
one call maps a distinct value to its entity id (an LLM "normalize this
value", or an ER ground-truth lookup); comparing canonical ids is free.
Calls are cached per (attribute, distinct value). Canonicalize-all therefore
costs (#distinct X values + #distinct Y values), the baseline we must beat.

Inputs are integer codes over distinct Layer-1 values:
  xc, yc     per-tuple value codes for X and Y
  xent, yent value code -> oracle entity id (only read through `canon`)
  lab        proxy partition pi of X values (cluster id per X value)
  nbrs       per X value, candidate neighbour X values (ANN stand-in)
"""

import numpy as np

from p0_pilot import ALPHA, eb_cs


def g3_codes(xc, yc):
    """g3 of X->Y on resolved integer codes."""
    order = np.lexsort((yc, xc))
    x, y = xc[order], yc[order]
    bounds = np.flatnonzero(np.r_[True, x[1:] != x[:-1], True])
    keep = 0
    for a, b in zip(bounds[:-1], bounds[1:]):
        keep += np.unique(y[a:b], return_counts=True)[1].max()
    return 1 - keep / len(x)


def cluster_priority(lab, xc):
    """Priority of each X-cluster = #tuples (ties broken by cluster id); on a
    rep conflict only the LOWER-priority cluster's tuples leave K."""
    size = np.bincount(lab[xc], minlength=lab.max() + 1)
    return size * (lab.max() + 1) + np.arange(lab.max() + 1)


def blocking_recall(lab, nbrs, xent, rep=None, yent=None, prio=None):
    """A(N) recall (pilot-only: needs truth). With rep/yent/prio given, the
    refined condition of Lemma 4': only oracle-equal pairs (a, b) in different
    clusters whose reps conflict, checked from the lower-priority side a."""
    by_ent = {}
    for v, e in enumerate(xent):
        by_ent.setdefault(e, []).append(v)
    need = cov = 0
    nb = [set(n) for n in nbrs]
    for vs in by_ent.values():
        for i in vs:
            for j in vs:
                if i == j or lab[i] == lab[j]:
                    continue
                if rep is not None:
                    ri, rj = rep.get(lab[i]), rep.get(lab[j])
                    if ri is None or rj is None or yent[ri] == yent[rj] \
                            or prio[lab[i]] > prio[lab[j]]:
                        continue
                need += 1
                cov += j in nb[i]
    return cov / need if need else 1.0


def miss_mass(lab, nbrs, xent, rep, yent, prio, xc):
    """nu(N): fraction of TUPLES whose X-value a has an oracle-equal b in a
    higher-priority cluster with a conflicting rep and b not in N(a).
    Lemma 4'': g3 <= P[t not in K(C)] + nu(N) without any recall assumption
    (removing those tuples restores consistency). Pilot-only: needs truth."""
    by_ent = {}
    for v, e in enumerate(xent):
        by_ent.setdefault(e, []).append(v)
    nb = [set(n) for n in nbrs]
    bad_val = np.zeros(len(xent), bool)
    for vs in by_ent.values():
        if len(vs) < 2:
            continue
        for i in vs:
            for j in vs:
                if i == j or lab[i] == lab[j] or j in nb[i]:
                    continue
                ri, rj = rep.get(lab[i]), rep.get(lab[j])
                if ri is not None and rj is not None and yent[ri] != yent[rj] \
                        and prio[lab[i]] < prio[lab[j]]:
                    bad_val[i] = True
                    break
    return float(bad_val[xc].mean())


def certify_g3(xc, yc, xent, yent, lab, nbrs, delta, rng, max_n=20000, batch=100):
    """Returns dict(certified, ub, samples, calls). Upper confidence bound on
    E[1{t not in K(C)}] >= g3 (valid under A(N)); certify iff ub < delta."""
    n = len(xc)
    tl = lab[xc]
    rep = {}
    for c in np.unique(tl):
        ys, cnt = np.unique(yc[tl == c], return_counts=True)
        rep[c] = ys[cnt.argmax()]
    prio = cluster_priority(lab, xc)
    seen_x, seen_y = {}, {}

    def cx(v):
        if v not in seen_x:
            seen_x[v] = xent[v]
        return seen_x[v]

    def cy(v):
        if v not in seen_y:
            seen_y[v] = yent[v]
        return seen_y[v]

    bs, hi = [], [1.0]
    while len(bs) < max_n:
        for t in rng.integers(0, n, size=batch):
            xi, c = xc[t], tl[t]
            r = rep[c]
            bad = cy(yc[t]) != cy(r)
            if not bad:
                for xj in nbrs[xi]:
                    rj = rep.get(lab[xj])
                    if rj is None or lab[xj] == c or rj == r or prio[lab[xj]] < prio[c]:
                        continue              # no tuples / same cluster / same rep / lower priority
                    if cx(xj) == cx(xi) and cy(rj) != cy(r):
                        bad = True
                        break
            bs.append(float(bad))
        lo, hi = eb_cs(np.array(bs), ALPHA)
        if hi[-1] < delta or lo[-1] >= delta:
            break
    return {"certified": bool(hi[-1] < delta), "ub": float(hi[-1]),
            "recall_refined": blocking_recall(lab, nbrs, xent, rep, yent, prio),
            "nu": miss_mass(lab, nbrs, xent, rep, yent, prio, xc),
            "samples": len(bs), "calls": len(seen_x) + len(seen_y),
            "calls_x": len(seen_x), "calls_y": len(seen_y)}


def topk_union(sims, k):
    """N(x) = top-k neighbours under each proxy similarity matrix (dense)."""
    nb = None
    for S in sims:
        S = S.copy()
        np.fill_diagonal(S, -1)
        kk = min(k, S.shape[1] - 1)
        idx = np.argpartition(-S, kk, axis=1)[:, :kk]
        nb = idx if nb is None else np.concatenate([nb, idx], 1)
    return [np.unique(r) for r in nb]
