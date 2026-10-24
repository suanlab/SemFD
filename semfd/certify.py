"""g3 repair certificate (paper Thm 1 soundness, Thm 2 certification and cost).

certify(ax, ay, fx, fy, theta, delta, alpha, rng) samples tuples i.i.d.,
evaluates B(t) = 1[t not in K(C)] with cached canonicalizer calls, and runs
the anytime-valid WSR empirical-Bernstein confidence sequence on E[B].
Certified  <=>  upper bound U < delta.  The guarantee is g3 <= U + nu(N)
(Thm A); with inverse=True and a complete inverse oracle, nu = 0 (Cor A2).
"""

import math

import numpy as np


def eb_cs(xs, alpha, c=0.5, sides=1):
    """Predictable-plug-in empirical-Bernstein confidence sequence for the
    mean of [0,1] observations (Waudby-Smith & Ramdas, JRSS-B 2024, Thm 2);
    running intersection (lower, upper). sides=1: each bound is a one-sided
    level-alpha sequence (log(1/alpha)); only the UPPER bound carries the
    certification guarantee, the lower one is used solely to stop early for
    futility, which cannot affect validity. sides=2: two-sided (log(2/alpha))."""
    xs = np.asarray(xs, float)
    t = np.arange(1, len(xs) + 1)
    mu = (0.5 + np.cumsum(xs)) / (t + 1)
    mu_prev = np.r_[0.5, mu[:-1]]
    var = (0.25 + np.cumsum((xs - mu) ** 2)) / (t + 1)
    var_prev = np.r_[0.25, var[:-1]]
    L = math.log(sides / alpha)
    lam = np.minimum(np.sqrt(2 * L / (var_prev * t * np.log1p(t))), c)
    psi = (-np.log1p(-lam) - lam) / 4
    s_l = np.cumsum(lam)
    center = np.cumsum(lam * xs) / s_l
    width = (L + np.cumsum(4 * (xs - mu_prev) ** 2 * psi)) / s_l
    return np.maximum.accumulate(center - width), np.minimum.accumulate(center + width)


def g3_codes(xc, yc):
    """g3 of X->Y over integer codes (exact, used for ground truth)."""
    order = np.lexsort((yc, xc))
    x, y = xc[order], yc[order]
    b = np.flatnonzero(np.r_[True, x[1:] != x[:-1], True])
    keep = sum(np.unique(y[s:e], return_counts=True)[1].max() for s, e in zip(b[:-1], b[1:]))
    return 1 - keep / len(x)


def witness(ax, ay, theta):
    """Proxy partition, per-cluster representative (the most frequent Layer-1 Y string among the
    cluster's tuples, ties to the smallest code) and cluster priority (#tuples, ties by id).
    Free: no oracle calls."""
    lab = ax.partition(theta)
    tl = lab[ax.codes]
    order = np.lexsort((ay.codes, tl))
    t_s, y_s = tl[order], ay.codes[order]
    rep = {}
    b = np.flatnonzero(np.r_[True, t_s[1:] != t_s[:-1], True])
    for s, e in zip(b[:-1], b[1:]):
        ys, cnt = np.unique(y_s[s:e], return_counts=True)
        rep[int(t_s[s])] = int(ys[cnt.argmax()])
    size = np.bincount(tl, minlength=lab.max() + 1)
    prio = size * (lab.max() + 1) + np.arange(lab.max() + 1)
    return lab, rep, prio


def witness_from(lab, ax, ay):
    """Representative and priority for an arbitrary partition `lab` of dom(X) (as in witness())."""
    tl = lab[ax.codes]
    order = np.lexsort((ay.codes, tl))
    t_s, y_s = tl[order], ay.codes[order]
    rep = {}
    b = np.flatnonzero(np.r_[True, t_s[1:] != t_s[:-1], True])
    for s, e in zip(b[:-1], b[1:]):
        ys, cnt = np.unique(y_s[s:e], return_counts=True)
        rep[int(t_s[s])] = int(ys[cnt.argmax()])
    size = np.bincount(tl, minlength=lab.max() + 1)
    prio = size * (lab.max() + 1) + np.arange(lab.max() + 1)
    return rep, prio


def certify(ax, ay, fx, fy, theta, delta, alpha, rng, inverse=False, nu_bar=0.0,
            audit=True, max_n=20000, batch=100, max_calls=None, ann=True, stop_at=None, refine=False):
    """fx, fy: Canonicalizer oracles keyed by Layer-1 value strings (shared
    caches across FDs are allowed; calls are reported as the increase).

    Decision: certified iff U + nu_bar < delta (Thm A), so the sequential test
    targets delta - nu_bar. With inverse=True (complete inverse oracle) nu = 0
    by Cor A2 and nu_bar should be 0. audit=False drops the neighbour/purity
    check (B9 ablation: Cormode-style modal-rep estimator under a proxy
    partition) and is NOT sound when the proxy over-splits entities.

    stop_at (default: the target) lets sampling continue until U < stop_at - nu_bar, which
    leaves slack for maintenance under updates (semfd.maintain); the decision is unchanged,
    U < delta - nu_bar, and remains valid because the sequence is time-uniform.

    refine (needs inverse): before each batch, every entity whose alias class was fetched in
    EARLIER batches becomes its own cluster (its in-data spellings, removed from their proxy
    clusters), and representatives/priorities are recomputed. The witness used for a sample
    depends only on information obtained before it, so each conditional mean of B is >= g3
    (Thm 1 holds for any witness). The bound before the running intersection covers the weighted
    average of these means; the returned running minimum is only an upper bound on the fixed g3
    (TR, Prop. "Predictable witnesses"), which is all the decision uses. No extra calls.
    refine=True ignores alias classes fetched before this call (shared caches), so runs stay
    comparable; refine="warm" also uses them (fetched by earlier candidates, hence before any
    sample of this one)."""
    if max_n < 0 or batch <= 0:
        raise ValueError("max_n must be nonnegative and batch must be positive")
    if len(ax.codes) == 0 or len(ax.codes) != len(ay.codes):
        raise ValueError("attributes must have equal, nonzero row counts")
    target = delta - nu_bar
    stop = target if stop_at is None else min(stop_at - nu_bar, target)
    lab, rep, prio = witness(ax, ay, theta)
    tl = lab[ax.codes]
    xv, yv = ax.vals, ay.vals
    xidx = {v: i for i, v in enumerate(xv)} if inverse else None
    if refine:
        lab = lab.copy()
        nxt, n_ref = int(lab.max()) + 1, (0 if refine == "warm" else len(fx.inv_cache))   # True: earlier fetches unused
    c0 = fx.calls + (fy.calls if fy is not fx else 0)
    n = len(ax.codes)
    bs = []
    lo = hi = np.array([0.0])
    budget_hit = False
    while len(bs) < max_n:
        if max_calls is not None and fx.calls + (fy.calls if fy is not fx else 0) - c0 >= max_calls:
            budget_hit = True
            break
        if refine and inverse and len(fx.inv_cache) > n_ref:
            for e, vs in list(fx.inv_cache.items())[n_ref:]:
                ids = [xidx[v] for v in vs if v in xidx]
                if ids:
                    lab[ids] = nxt
                    nxt += 1
            n_ref = len(fx.inv_cache)
            rep, prio = witness_from(lab, ax, ay)
            tl = lab[ax.codes]
        for t in rng.integers(0, n, size=min(batch, max_n - len(bs))):
            xi, c = int(ax.codes[t]), int(tl[t])
            r = rep[c]
            ry = fy(yv[r])
            bad = fy(yv[ay.codes[t]]) != ry
            if not bad and audit:
                same = set()
                if inverse:               # f(b) = f(a) known for aliases: no X-call on b
                    same = {xidx[v] for v in fx.aliases(fx(xv[xi])) if v in xidx}
                al = np.fromiter(same, np.int64, len(same))
                # ann=False with a COMPLETE inverse: the alias class alone satisfies Cor A2 (nu = 0)
                for xj in (np.union1d(ax.nbrs[xi], al) if ann or not inverse else al):
                    cj = int(lab[xj])
                    rj = rep.get(cj)
                    if rj is None or cj == c or rj == r or prio[cj] < prio[c]:
                        continue          # free proxy-side filters
                    if (xj in same or fx(xv[xj]) == fx(xv[xi])) and fy(yv[rj]) != ry:
                        bad = True
                        break
            bs.append(float(bad))
        lo, hi = eb_cs(bs, alpha)
        if hi[-1] < stop or lo[-1] >= target:
            break
    calls = fx.calls + (fy.calls if fy is not fx else 0) - c0
    if not bs:
        lo, hi = np.array([0.0]), np.array([1.0])
    return {"certified": bool(hi[-1] < target), "nu_bar": nu_bar, "audit": audit, "budget_hit": budget_hit, "ub": min(1.0, float(hi[-1])), "lb": max(0.0, float(lo[-1])),
            "mean": float(np.mean(bs)) if bs else None, "samples": len(bs), "calls": int(calls),
            "theta": theta, "alpha": alpha}


def miss_mass(ax, ay, xent, yent, theta, inverse=False):
    """nu(N) of Thm A, computed from full truth (evaluation only).
    xent/yent: entity id per value code. With inverse=True the candidate set
    includes all oracle-equal values, so nu = 0 by Cor A2."""
    if inverse:
        return 0.0
    lab, rep, prio = witness(ax, ay, theta)
    by_ent = {}
    for v, e in enumerate(xent):
        by_ent.setdefault(e, []).append(v)
    bad = np.zeros(len(xent), bool)
    for vs in by_ent.values():
        if len(vs) < 2:
            continue
        for i in vs:
            ri, nb = rep.get(int(lab[i])), set(ax.nbrs[i].tolist())
            if ri is None:
                continue
            for j in vs:
                if i == j or lab[i] == lab[j] or j in nb:
                    continue
                rj = rep.get(int(lab[j]))
                if rj is not None and yent[ri] != yent[rj] and prio[lab[i]] < prio[lab[j]]:
                    bad[i] = True
                    break
    return float(bad[ax.codes].mean())
