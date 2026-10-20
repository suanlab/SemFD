"""Per-FD planner (paper Sec. V): certify, but never pay more than resolving.

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
    values up front (shared by all FDs; P0: certification cannot beat this)."""
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
