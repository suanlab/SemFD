"""Oracle-using baselines (paper Sec. VI, Methods).

B4  canonicalize-all: call f on every distinct value of X and Y, then exact g3.
B5  pairwise semantic self-join (FDJ/BARGAIN-style with T_P = 1): the oracle
    judges every blocked candidate pair (ANN edges) of X and of Y; connected
    components of confirmed pairs give the resolved instance; then exact g3.
    Cost unit = one pair judgement. Correct only up to blocking recall.
B7  sample-only estimator (Kivinen-Mannila / Cormode et al.): canonicalize the
    values of m uniformly sampled tuples and accept iff the sample g3 <= delta.
    Biased low (sampled groups are smaller), which is the sqrt(N) effect.
"""

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from .certify import g3_codes


def canonicalize_all(ax, ay, fx, fy):
    xid, yid = {}, {}
    xe = np.array([xid.setdefault(fx(v), len(xid)) for v in ax.vals])
    ye = np.array([yid.setdefault(fy(v), len(yid)) for v in ay.vals])
    calls = (0 if ax.exact else len(ax.vals)) + (0 if ay.exact else len(ay.vals))
    return {"g3": g3_codes(xe[ax.codes], ye[ay.codes]), "calls": calls}


def _resolve_pairs(at, f):
    n = len(at.vals)
    if at.exact or n < 2:
        return np.arange(n), 0
    pairs = {(min(a, b), max(a, b)) for a, nb in enumerate(at.nbrs) for b in nb if a != b}
    pairs = np.array(sorted(pairs), dtype=np.int64).reshape(-1, 2)
    ok = np.fromiter((f(at.vals[a]) == f(at.vals[b]) for a, b in pairs), bool, len(pairs))
    A = coo_matrix((np.ones(ok.sum()), (pairs[ok, 0], pairs[ok, 1])), shape=(n, n))
    return connected_components(A, directed=False)[1], len(pairs)


def pairwise_join(ax, ay, fx, fy):
    """Pair judgements are simulated with the canonicalizer (f(a) == f(b)),
    but each distinct pair is charged one call, as a yes/no judge would be."""
    lx, cx = _resolve_pairs(ax, fx)
    ly, cy = _resolve_pairs(ay, fy)
    return {"g3": g3_codes(lx[ax.codes], ly[ay.codes]), "calls": cx + cy}


def sample_only(ax, ay, fx, fy, m, rng):
    t = rng.integers(0, len(ax.codes), size=m)
    xv = [fx(ax.vals[i]) for i in ax.codes[t]]
    yv = [fy(ay.vals[i]) for i in ay.codes[t]]
    xid, yid = {}, {}
    xe = np.array([xid.setdefault(v, len(xid)) for v in xv])
    ye = np.array([yid.setdefault(v, len(yid)) for v in yv])
    calls = (0 if ax.exact else len(set(ax.codes[t].tolist()))) + \
        (0 if ay.exact else len(set(ay.codes[t].tolist())))
    return {"g3": g3_codes(xe, ye), "calls": calls, "m": m}
