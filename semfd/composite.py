"""Composite left-hand sides X = (A, B) (multi-attribute FDs).

The oracle of X is the product of component oracles, f_X(a, b) = (f_A(a), f_B(b)),
still a function (hence transitive) and charged through the COMPONENT caches,
so a component value canonicalized for one FD is free for every other.
The proxy partition of X is the product of component partitions; the
neighbours of (a, b) are the composite values present in r whose components are
equal or proxy neighbours; inverse access is the product of component alias
classes intersected with the composite values present in r.
"""

import numpy as np

SEP = "\x1f"


class CompositeOracle:
    def __init__(self, parts):
        self.parts = parts                      # list of component Canonicalizers
        self.present = None                     # set of composite strings in r (set by CompositeAttr)
        self.free = all(p.free for p in parts)

    def __call__(self, v):
        return tuple(p(c) for p, c in zip(self.parts, v.split(SEP)))

    def aliases(self, e):
        classes = [p.aliases(ei) if p.inverse is not None else [] for p, ei in zip(self.parts, e)]
        out = []
        if all(classes):
            import itertools
            for combo in itertools.product(*classes):
                key = SEP.join(combo)
                if key in self.present:
                    out.append(key)
        return out

    @property
    def inverse(self):
        return True if all(p.inverse is not None for p in self.parts) else None

    @property
    def calls(self):
        """Always 0: calls are charged to the component oracles, so count cost as the change in
        sum(p.calls for p in parts), as exp/e9_multi.py does, never from this attribute."""
        return 0


class CompositeAttr:
    """Duck-types semfd.proxy.Attr for certify(): vals, codes, nbrs, exact, partition()."""

    def __init__(self, attrs):
        self.parts = attrs
        self.name = "+".join(a.name for a in attrs)
        self.exact = all(a.exact for a in attrs)
        comp = np.stack([a.codes for a in attrs], 1)
        uniq, self.codes = np.unique(comp, axis=0, return_inverse=True)
        self.codes = self.codes.ravel()
        self.uniq = uniq
        if any(SEP in v for a in attrs for v in a.vals):
            raise ValueError(f"a value of {self.name} contains the composite separator {SEP!r}")
        self.vals = [SEP.join(a.vals[c] for a, c in zip(attrs, row)) for row in uniq]
        index = {tuple(row): i for i, row in enumerate(uniq)}
        by_part = [dict() for _ in attrs]           # component code -> composite codes
        for i, row in enumerate(uniq):
            for j, c in enumerate(row):
                by_part[j].setdefault(int(c), []).append(i)
        nb = []
        for i, row in enumerate(uniq):
            cand = set()
            for j, (a, c) in enumerate(zip(attrs, row)):
                for c2 in a.nbrs[int(c)]:            # vary one component among its proxy neighbours
                    other = list(row)
                    other[j] = int(c2)
                    k = index.get(tuple(other))
                    if k is not None:
                        cand.add(k)
            cand.discard(i)
            nb.append(np.array(sorted(cand), np.int64))
        self.nbrs = nb

    def partition(self, theta):
        labs = np.stack([a.partition(theta)[self.uniq[:, j]] for j, a in enumerate(self.parts)], 1)
        return np.unique(labs, axis=0, return_inverse=True)[1].ravel()

    def oracle(self, comp_orcs):
        o = CompositeOracle(comp_orcs)
        o.present = set(self.vals)
        return o
