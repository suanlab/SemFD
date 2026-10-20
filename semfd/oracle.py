"""Canonicalizer oracles (paper Def. 1, Prop. 1).

An oracle for attribute A is a function f_A: value -> entity id. Its kernel is
an equivalence relation, so the transitivity Lemma 4 needs holds by
construction. Cost = one call per distinct value (cached); comparing ids is
free. Optional inverse access f_A^{-1}(e) ∩ dom(A) (ER ground-truth clusters,
KB aliases) costs one call per entity.
"""

import hashlib


class Canonicalizer:
    def __init__(self, fn, inverse=None, name="", free=False):
        """free=True: identity comparison on an exact (identifier-like) attribute;
        no oracle is consulted, so no calls are charged."""
        self.fn, self.inverse, self.name, self.free = fn, inverse, name, free
        self.cache, self.inv_cache = {}, {}

    @classmethod
    def from_table(cls, table, inverse=False, name=""):
        """Exact oracle from a value -> entity mapping (ground truth)."""
        inv = None
        if inverse:
            by_ent = {}
            for v, e in table.items():
                by_ent.setdefault(e, []).append(v)
            inv = lambda e: by_ent.get(e, [])
        return cls(table.__getitem__, inv, name)

    def __call__(self, v):
        if v not in self.cache:
            self.cache[v] = self.fn(v)
        return self.cache[v]

    def aliases(self, e):
        if self.inverse is None:
            return []
        if e not in self.inv_cache:
            self.inv_cache[e] = list(self.inverse(e))
        return self.inv_cache[e]

    @property
    def calls(self):
        return 0 if self.free else len(self.cache) + len(self.inv_cache)

    @property
    def calls_forward(self):
        return 0 if self.free else len(self.cache)

    @property
    def calls_inverse(self):
        return 0 if self.free else len(self.inv_cache)

    def reset(self):
        self.cache.clear()
        self.inv_cache.clear()


def noisy(table, p, seed=0):
    """Deterministic per-value corruption of a ground-truth table: with
    probability p a value is mapped to a fresh singleton id (a 'split' error)
    or, with equal probability, to another value's entity (a 'merge' error).
    Still a function, hence still transitive (Prop D)."""
    vals = sorted(table)
    ents = sorted(set(table.values()), key=str)
    out = {}
    for v in vals:
        h = int(hashlib.sha1(f"{seed}|{v}".encode()).hexdigest(), 16)
        u = (h % 10**6) / 10**6
        if u >= p:
            out[v] = table[v]
        elif (h >> 20) % 2:
            out[v] = ("__split__", v)
        else:
            out[v] = ents[(h >> 21) % len(ents)]
    return out


def total_calls(orcs):
    """Total oracle calls over a dict attr -> Canonicalizer, counting shared
    oracles (probe copies of one attribute) once."""
    return int(sum(o.calls for o in {id(o): o for o in orcs.values()}.values()))


def calls_split(orcs):
    """(forward, inverse) oracle calls over a dict attr -> oracle, shared oracles counted once."""
    u = {id(o): o for o in orcs.values()}.values()
    return (int(sum(getattr(o, "calls_forward", 0) for o in u)), int(sum(getattr(o, "calls_inverse", 0) for o in u)))


def disagreement_mass(codes, f, g):
    """Smallest tuple mass to delete so that two oracles f, g induce the same partition on the
    remaining values of one attribute (oracle-transfer lemma, paper Sec. IV).

    codes: per-tuple value (any hashable); f, g: value -> entity. Values are grouped into cells
    (f-class, g-class); the kept cells must form a matching between f-classes and g-classes, and
    a maximum-weight matching (weights = tuple counts) gives the minimum. Returns the deleted
    fraction of tuples."""
    from collections import Counter
    from scipy.optimize import linear_sum_assignment
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    cnt = Counter(codes)
    cell = Counter()
    for v, n in cnt.items():
        cell[(f(v), g(v))] += n
    fi = {e: i for i, e in enumerate(dict.fromkeys(a for a, _ in cell))}
    gi = {e: i for i, e in enumerate(dict.fromkeys(b for _, b in cell))}
    nf, ng = len(fi), len(gi)
    r = [fi[a] for a, _ in cell]
    c = [nf + gi[b] for _, b in cell]
    k, lab = connected_components(coo_matrix(([1] * len(r), (r, c)), shape=(nf + ng, nf + ng)), directed=False)
    comp = {}
    for (a, b), w in cell.items():
        comp.setdefault(lab[fi[a]], []).append((fi[a], gi[b], w))
    kept = 0
    for items in comp.values():
        if len(items) == 1:
            kept += items[0][2]
            continue
        rows = {x: i for i, x in enumerate(dict.fromkeys(a for a, _, _ in items))}
        cols = {x: i for i, x in enumerate(dict.fromkeys(b for _, b, _ in items))}
        import numpy as np
        W = np.zeros((len(rows), len(cols)))
        for a, b, w in items:
            W[rows[a], cols[b]] = w
        ri, ci = linear_sum_assignment(W, maximize=True)
        kept += W[ri, ci].sum()
    total = sum(cnt.values())
    return float(1 - kept / total)
