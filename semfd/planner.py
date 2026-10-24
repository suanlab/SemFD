"""Planners evaluated in the paper (Sec. VI) and NOT used by the system: certify, or resolve outright when cheaper.

Per-FD planner (E1b variant):

Run the certificate with a call cap equal to what canonicalize-all of the
non-exact sides would still cost given the shared cache. If the cap is hit,
canonicalize the remaining values (the cache makes earlier calls count) and
decide by the exact g3 on the canonical codes -- deterministic, no alpha spent
(falling back after a partial run is not peeking: the exact decision has no error).
Cost: forward calls <= |dom X| + |dom Y| + one batch of overshoot (<= batch*(3+3K));
inverse alias calls come ON TOP (review 2026-10-16: up to ~2x canonicalize-all).
"""

import numpy as np

from .certify import certify, g3_codes


def remaining(at, f):
    return 0 if f.free else sum(v not in f.cache for v in at.vals)


def prepass(attrs, orcs, v_thresh):
    """Canonicalize every non-exact attribute with at most v_thresh distinct
    values up front (shared by all FDs; a heuristic, not a cost optimality guarantee)."""
    done = []
    for a, at in attrs.items():
        if not orcs[a].free and len(at.vals) <= v_thresh:
            for v in at.vals:
                orcs[a](v)
            done.append(a)
    return done


def certify_or_resolve(ax, ay, fx, fy, theta, delta, alpha, rng, inverse=True, **kw):
    tot = lambda: fx.calls + (fy.calls if fy is not fx else 0)
    c0 = tot()
    cap = remaining(ax, fx) + (remaining(ay, fy) if fy is not fx else 0)
    r = None
    if cap > 0:
        r = certify(ax, ay, fx, fy, theta, delta, alpha, rng, inverse=inverse, max_calls=cap, **kw)
        if not r["budget_hit"]:
            r["mode"] = "certificate"
            return r
    r = r or {"samples": 0}
    xid, yid = {}, {}                     # exact ids, no hash() collisions
    xe = np.array([xid.setdefault(fx(v), len(xid)) for v in ax.vals])
    ye = np.array([yid.setdefault(fy(v), len(yid)) for v in ay.vals])
    g = g3_codes(xe[ax.codes], ye[ay.codes])
    r.update({"mode": "resolved", "certified": bool(g <= delta), "ub": float(g), "lb": float(g),
              "calls": int(tot() - c0)})
    return r


class RunPlanner:  # evaluated in exp/e13_planner.py; not used by the system (paper Sec. VI)
    """Run-level planner that charges forward AND inverse calls (paper Sec. V).

    Each oracle (shared by an attribute and its probe copies) gets a budget R_k: the forward calls that resolving
    its values outright would still cost when the run starts. A candidate is certified with a call cap equal to the
    smallest remaining budget of its unresolved sides; when the cap is hit, or once every side is resolved, the
    candidate is decided exactly on the resolved values (no alpha spent; falling back is not peeking). After each
    candidate, an oracle is resolved outright when its calls so far (forward + inverse) reach R_k, or when, after
    `pilot` candidates that use it, its calls per candidate times the candidates that use it would reach R_k.
    Cost per oracle <= 2 R_k plus one batch of overshoot, counting alias lookups."""

    def __init__(self, orcs, attr_vals, cands, pilot=5):
        from collections import Counter
        orcs = {a: o for a, o in orcs.items() if a in attr_vals}
        self.orc = {id(o): o for o in orcs.values() if not o.free}
        self.grp = {a: id(o) for a, o in orcs.items() if not o.free}
        self.vals = {}
        for a, k in self.grp.items():
            self.vals.setdefault(k, set()).update(attr_vals[a])
        self.R = {k: sum(v not in self.orc[k].cache for v in vs) for k, vs in self.vals.items()}
        self.S0 = {k: self.orc[k].calls for k in self.R}
        self.uses = Counter(k for c in cands for k in {self.grp[a] for a in c if a in self.grp})
        self.done, self.res, self.pilot = Counter(), set(), pilot
        self.n_resolved_cands = 0

    def spent(self, k):
        return self.orc[k].calls - self.S0[k]

    def resolve(self, k):
        if k not in self.res:
            f = self.orc[k]
            for v in self.vals[k]:
                f(v)
            self.res.add(k)

    def decide(self, sides, delta, certify_fn, exact_g3):
        """sides: attribute names of the candidate; certify_fn(cap) -> certify() result; exact_g3() -> g3 on the
        resolved values (called only after every side is resolved)."""
        ks = {self.grp[a] for a in sides if a in self.grp}
        open_ = [k for k in ks if k not in self.res]
        r = None
        if open_:
            cap = min(self.R[k] - self.spent(k) for k in open_)
            if cap > 0:
                r = certify_fn(cap)
                if r["budget_hit"]:
                    r = None
                else:
                    r["mode"] = "certificate"
        if r is None:
            for k in ks:
                self.resolve(k)
            g = exact_g3()
            r = {"mode": "resolved", "certified": bool(g <= delta), "ub": float(g), "lb": float(g)}
            self.n_resolved_cands += 1
        for k in ks:
            self.done[k] += 1
            if k not in self.res and (self.spent(k) >= self.R[k] or (
                    self.done[k] >= self.pilot and self.spent(k) / self.done[k] * self.uses[k] >= self.R[k])):
                self.resolve(k)
        return r
