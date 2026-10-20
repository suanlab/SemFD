"""Certified closure (paper Thm 4; technical report).

Given certified bounds U[(X, Y)] for FDs with single-attribute sides, derive
valid (not necessarily minimal) bounds for every FD implied by Armstrong's
rules, at zero oracle cost:
  transitivity  min-plus closure (shortest paths) over the attribute graph;
  augmentation  g3(XW -> Y) <= g3(X -> Y)  (keep the best single LHS attribute);
  union         g3(X -> YZ) <= g3(X -> Y) + g3(X -> Z).
Each bound is a sum over a support set Sigma' whose premises are counted once
(Prop 1), so summing along a simple path is valid. The simultaneous guarantee
holds with probability >= 1 - sum of the premises' alphas.
"""

import itertools


def unary_closure(bounds, attrs):
    """bounds: {(x, y): U}. Returns {(x, y): (U*, path)} for every derivable
    pair, by Floyd-Warshall in the (min, +) semiring."""
    D = {(x, y): (u, (x, y)) for (x, y), u in bounds.items()}
    for x in attrs:
        D[(x, x)] = (0.0, (x,))
    for k in attrs:
        for i in attrs:
            if (i, k) not in D:
                continue
            for j in attrs:
                if (k, j) not in D:
                    continue
                u = D[(i, k)][0] + D[(k, j)][0]
                if u < D.get((i, j), (float("inf"),))[0]:
                    D[(i, j)] = (u, D[(i, k)][1] + D[(k, j)][1][1:])
    return {p: v for p, v in D.items() if p[0] != p[1]}


def derived_bound(lhs, rhs, closure):
    """Valid bound for lhs -> rhs (tuples of attributes) from the unary closure,
    or None if not derivable this way."""
    total = 0.0
    for y in rhs:
        if y in lhs:
            continue
        best = min((closure[(x, y)][0] for x in lhs if (x, y) in closure), default=None)
        if best is None:
            return None
        total += best
    return total


def derived_fds(bounds, attrs, max_lhs=2, delta=None):
    """All FDs lhs -> y (|lhs| <= max_lhs, y not in lhs) derivable from the
    certified unary set, with their bounds (optionally only those <= delta)."""
    clo = unary_closure(bounds, attrs)
    out = {}
    for m in range(1, max_lhs + 1):
        for lhs in itertools.combinations(attrs, m):
            for y in attrs:
                if y in lhs:
                    continue
                u = derived_bound(lhs, (y,), clo)
                if u is not None and (delta is None or u <= delta):
                    out[(lhs, y)] = u
    return out
