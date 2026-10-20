"""P0 pilot (RESEARCH_DIRECTION.md section 5).

Question: do raw-similarity SFD tests (pairwise B&V/FastRFD-style or
cluster-then-exact quotient) make wrong decisions w.r.t. ORACLE equality,
and can proxy-guided oracle sampling certify the right decisions cheaply?

Violation measure (pair-conditional, g1-style):
    v(X->Y) = P[ Y unrelated | X related ]  over ordered pairs of distinct tuples,
accept X->Y iff v <= DELTA. "Related" is defined by the method under test;
the oracle defines the truth.

Methods
  exact              Layer-1 normalized string equality
  <b>-pair@eps       sim_b >= 1-eps            (non-transitive; B&V / FastRFD semantics)
  <b>-quot@eps       connected components of the sim_b >= 1-eps graph (engine semantics)
  oracle-canon       oracle canonicalizes every distinct value (cost = #distinct values)
  certified-<b>      importance-sample tuple pairs by proxy b, query the oracle on
                     value pairs (cached), anytime-valid empirical-Bernstein
                     confidence sequence on mu = E[1{O_X}(1{not O_Y} - DELTA)];
                     stop when the CS excludes 0 (accept if mu<0, reject if mu>0).
"""

import argparse
import json
import math
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "pilot"))
from p0_data import CANDIDATES, TYPES, layer1, make_table  # noqa: E402

DELTA = 0.05
ALPHA = 0.05
EPS_GRID = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5]
EMB_MODELS = {"minilm": "sentence-transformers/all-MiniLM-L6-v2",
              "bge": "BAAI/bge-small-en-v1.5"}


# ------------------------------------------------------------------ similarity
def edit_matrix(vals):
    n = len(vals)
    S = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            S[i, j] = S[j, i] = SequenceMatcher(None, vals[i], vals[j]).ratio()
    return S


def emb_matrix(vals, model):
    from embedding_backend import embed, set_model
    set_model(model)
    E = embed(list(vals))
    return np.clip(E @ E.T, 0, 1)


class Attr:
    """Distinct Layer-1 values of one attribute + proxy sims + oracle ids."""

    def __init__(self, name, series, oracle, backends):
        self.name = name
        self.vals = sorted({layer1(v) for v in series})
        self.idx = {v: i for i, v in enumerate(self.vals)}
        self.codes = np.array([self.idx[layer1(v)] for v in series])
        ent = [oracle[v] for v in self.vals]
        ids = {e: k for k, e in enumerate(sorted(set(ent)))}
        self.ent = np.array([ids[e] for e in ent])
        self.O = self.ent[:, None] == self.ent[None, :]          # oracle relation
        n = len(self.vals)
        if TYPES[name] == "exact":
            self.S = {b: np.eye(n) for b in backends}
        else:
            self.S = {}
            for b in backends:
                if b == "edit":
                    self.S[b] = edit_matrix(self.vals)
                elif b in EMB_MODELS:
                    self.S[b] = emb_matrix(self.vals, EMB_MODELS[b])
            for b in backends:
                if b.startswith("hyb-"):
                    self.S[b] = (self.S["edit"] + self.S[b[4:]]) / 2

    def rel(self, method, eps=None):
        if method == "exact":
            return np.eye(len(self.vals), dtype=bool)
        if method == "oracle":
            return self.O
        b, sem = method
        R = self.S[b] >= 1 - eps - 1e-12
        if sem == "pair":
            return R
        _, lab = connected_components(csr_matrix(R), directed=False)
        return lab[:, None] == lab[None, :]


# ------------------------------------------------------------- violation rate
class Pair:
    """Combination counts for candidate X->Y; pair weights over combos."""

    def __init__(self, ax, ay):
        combos, cnt = np.unique(np.stack([ax.codes, ay.codes], 1), axis=0,
                                return_counts=True)
        self.cx, self.cy = combos[:, 0], combos[:, 1]
        W = np.outer(cnt, cnt).astype(float)
        W[np.diag_indices_from(W)] -= cnt
        self.W = W / W.sum()
        self.ax, self.ay = ax, ay

    def v(self, RX, RY):
        rx = RX[np.ix_(self.cx, self.cx)]
        ry = RY[np.ix_(self.cy, self.cy)]
        den = (self.W * rx).sum()
        return float((self.W * rx * ~ry).sum() / den) if den > 0 else 0.0


# ------------------------------------------------------- certified sampling
def eb_cs(xs, alpha, c=0.5):
    """Predictable-plug-in empirical-Bernstein confidence sequence
    (Waudby-Smith & Ramdas, JRSS-B 2024, Thm 2) for the mean of [0,1]
    observations; anytime-valid, so it may be checked after every batch.
    Returns the running-intersection (lower, upper) after each observation."""
    xs = np.asarray(xs, float)
    t = np.arange(1, len(xs) + 1)
    mu = (0.5 + np.cumsum(xs)) / (t + 1)                  # mu_hat_t
    mu_prev = np.r_[0.5, mu[:-1]]                         # mu_hat_{t-1}
    var = (0.25 + np.cumsum((xs - mu) ** 2)) / (t + 1)    # sigma_hat^2_t
    var_prev = np.r_[0.25, var[:-1]]
    L = math.log(2 / alpha)
    lam = np.minimum(np.sqrt(2 * L / (var_prev * t * np.log1p(t))), c)
    psi = (-np.log1p(-lam) - lam) / 4
    s_l = np.cumsum(lam)
    center = np.cumsum(lam * xs) / s_l
    width = (L + np.cumsum(4 * (xs - mu_prev) ** 2 * psi)) / s_l
    return np.maximum.accumulate(center - width), np.minimum.accumulate(center + width)


def certify(pair, proxy, lam=0.3, gamma=4.0, max_n=30000, batch=200, rng=None):
    """Sequentially certify v <= DELTA (accept) or v > DELTA (reject).

    Sampling distribution over ordered combo pairs:
        q = lam * u + (1-lam) * u * h / E_u[h],   h = sim_X^gamma,
    which is defensive (weights u/q <= 1/lam) so the estimate is unbiased
    whatever the proxy. Oracle calls are counted per distinct unordered
    value pair; Layer-1-identical values are related for free.
    """
    ax, ay = pair.ax, pair.ay
    u = pair.W.ravel()
    sx = ax.S[proxy][np.ix_(pair.cx, pair.cx)].ravel() ** gamma
    h = sx / (u @ sx)
    q = lam * u + (1 - lam) * u * h
    q /= q.sum()
    w = np.divide(u, q, out=np.zeros_like(u), where=q > 0)
    lo_y, hi_y = -DELTA / lam, (1 - DELTA) / lam
    K = len(pair.cx)
    cache = {}
    calls = {"x": 0, "y": 0}

    def oracle(attr, i, j, key):
        if i == j:
            return True
        k = (attr.name, min(i, j), max(i, j))
        if k not in cache:
            cache[k] = bool(attr.O[i, j])
            calls[key] += 1
        return cache[k]

    xs = []
    n = 0
    while n < max_n:
        draws = rng.choice(len(q), size=batch, p=q)
        for d in draws:
            a, b = divmod(int(d), K)
            z = 0.0
            if oracle(ax, pair.cx[a], pair.cx[b], "x"):
                z = (0.0 if oracle(ay, pair.cy[a], pair.cy[b], "y") else 1.0) - DELTA
            xs.append((z * w[d] - lo_y) / (hi_y - lo_y))
        n += batch
        lo, hi = eb_cs(np.array(xs), ALPHA)
        zero = (0 - lo_y) / (hi_y - lo_y)
        if hi[-1] < zero:
            return True, n, calls["x"] + calls["y"]
        if lo[-1] > zero:
            return False, n, calls["x"] + calls["y"]
    return None, n, calls["x"] + calls["y"]


# ----------------------------------------------------------------------- main
def run(seed, rho, backends, n_rows, do_cert):
    df, oracle = make_table(n_rows=n_rows, rho=rho, seed=seed)
    attrs = {a: Attr(a, df[a], oracle[a], backends) for a in df.columns}
    out = {"seed": seed, "rho": rho, "fds": []}
    for x, y, truth in CANDIDATES:
        P = Pair(attrs[x], attrs[y])
        rec = {"fd": f"{x}->{y}", "truth": truth,
               "v_oracle": P.v(attrs[x].rel("oracle"), attrs[y].rel("oracle")),
               "v_exact": P.v(attrs[x].rel("exact"), attrs[y].rel("exact"))}
        for b in backends:
            for sem in ("pair", "quot"):
                rec[f"{b}-{sem}"] = {
                    str(e): P.v(attrs[x].rel((b, sem), e), attrs[y].rel((b, sem), e))
                    for e in EPS_GRID}
        if do_cert:
            rng = np.random.default_rng(seed)
            for b in do_cert:
                t0 = time.perf_counter()
                dec, n, calls = certify(P, b, rng=rng)
                rec[f"cert-{b}"] = {"decision": dec, "samples": n, "calls": calls,
                                    "sec": time.perf_counter() - t0}
        out["fds"].append(rec)
    tol = [a for a in df.columns if TYPES[a] == "tolerance"]
    out["oracle_canon_calls"] = int(sum(len(attrs[a].vals) for a in tol))
    out["distinct_pairs_tol"] = int(sum(len(attrs[a].vals) * (len(attrs[a].vals) - 1) // 2
                                        for a in tol))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--rhos", type=float, nargs="+", default=[0.1, 0.2, 0.3])
    ap.add_argument("--rows", type=int, default=3000)
    ap.add_argument("--backends", nargs="+",
                    default=["edit", "minilm", "bge", "hyb-bge"])
    ap.add_argument("--cert", nargs="*", default=["edit", "hyb-bge"])
    ap.add_argument("--out", default=str(ROOT / "results/p0/p0_raw.json"))
    a = ap.parse_args()
    res = []
    for rho in a.rhos:
        for s in range(a.seeds):
            t0 = time.perf_counter()
            res.append(run(s, rho, a.backends, a.rows, a.cert))
            print(f"rho={rho} seed={s} done in {time.perf_counter() - t0:.1f}s", flush=True)
    Path(a.out).write_text(json.dumps(res, indent=1))
    print("wrote", a.out)
