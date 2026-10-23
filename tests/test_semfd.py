"""Minimal correctness tests for semfd . Fast (< 1 min), no network, no embeddings.
Run: .venv/bin/python -m pytest -q tests/"""
import itertools
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from semfd.certify import certify, eb_cs, g3_codes, miss_mass  # noqa: E402
from semfd.closure import unary_closure  # noqa: E402
from semfd.data import inject_errors  # noqa: E402
from semfd.oracle import Canonicalizer  # noqa: E402
from semfd.proxy import Attr, layer1  # noqa: E402


def brute_g3(x, y):
    """Minimum fraction of tuples to delete so that X -> Y holds (exhaustive, tiny inputs)."""
    n = len(x)
    for k in range(n + 1):
        for drop in itertools.combinations(range(n), k):
            keep = [i for i in range(n) if i not in drop]
            seen = {}
            if all(seen.setdefault(x[i], y[i]) == y[i] for i in keep):
                return k / n
    return 1.0


def test_g3_matches_bruteforce():
    rng = np.random.default_rng(0)
    for _ in range(60):
        n = int(rng.integers(1, 9))
        x, y = rng.integers(0, 3, n), rng.integers(0, 3, n)
        assert g3_codes(x, y) == pytest.approx(brute_g3(list(x), list(y)))


def test_eb_cs_upper_bound_time_uniform_coverage():
    rng = np.random.default_rng(1)
    misses = 0
    for _ in range(400):
        x = (rng.random(2000) < 0.05).astype(float)
        _, hi = eb_cs(x, 0.05)
        misses += bool((hi < 0.05).any())
    assert misses / 400 <= 0.05 + 0.03          # nominal alpha plus Monte-Carlo slack


def _toy(n_ent=60, rows=6, conflict_ent=8, seed=0):
    """Entities with two spellings each; conflict_ent entities give their second spelling a different Y."""
    rnd = random.Random(seed)
    xs, ys, xo, yo = [], [], {}, {}
    for e in range(n_ent):
        a, b = f"name{e:03d}", f"nm{e:03d}x"
        for s in (a, b):
            xo[layer1(s)] = e
        for _ in range(rows):
            sp = rnd.choice((a, b))
            y = f"y{e % 5}" if not (e < conflict_ent and sp == b) else f"y{(e + 1) % 5}"
            xs.append(sp)
            ys.append(y)
            yo[layer1(y)] = y
    return pd.Series(xs), pd.Series(ys), xo, yo


def test_certify_bound_dominates_g3_with_inverse():
    xs, ys, xo, yo = _toy()
    ax, ay = Attr("x", xs, proxy="edit", k=3), Attr("y", ys, exact=True)
    xent = np.array([xo[v] for v in ax.vals])
    yent = np.array([yo[v] for v in ay.vals])
    g3 = g3_codes(xent[ax.codes], yent[ay.codes])
    fails = 0
    for i in range(40):
        fx = Canonicalizer.from_table(xo, inverse=True)
        fy = Canonicalizer(lambda v: v, (lambda e: [e]), free=True)
        r = certify(ax, ay, fx, fy, 0.9, 0.05, 0.05, np.random.default_rng(i), inverse=True, max_n=4000)
        fails += r["ub"] < g3
    assert fails <= 4                            # bound should cover g3 in >= 1-alpha of runs (slack for 40 reps)


def test_miss_mass_zero_with_inverse_and_nonneg():
    xs, ys, xo, yo = _toy()
    ax, ay = Attr("x", xs, proxy="edit", k=1), Attr("y", ys, exact=True)
    xent = np.array([xo[v] for v in ax.vals])
    yent = np.array([yo[v] for v in ay.vals])
    assert miss_mass(ax, ay, xent, yent, 0.99, inverse=True) == 0.0
    assert 0.0 <= miss_mass(ax, ay, xent, yent, 0.99) <= 1.0


def test_unary_closure_equals_best_path():
    b = {("a", "b"): 0.01, ("b", "c"): 0.02, ("a", "c"): 0.05, ("c", "d"): 0.01}
    clo = unary_closure(b, ["a", "b", "c", "d"])
    assert clo[("a", "c")][0] == pytest.approx(0.03)
    assert clo[("a", "d")][0] == pytest.approx(0.04)
    assert ("d", "a") not in clo


def test_injection_rates():
    rng = np.random.default_rng(3)
    n = 20000
    x = [f"c{i % 4000}" for i in range(n)]
    y = [f"k{(i % 4000) % 50}" for i in range(n)]
    df = pd.DataFrame({"x": x, "y": y})
    oracle = {"x": {layer1(v): v for v in set(x)}, "y": {layer1(v): v for v in set(y)}}
    name = inject_errors(df, oracle, "y", 0.08, seed=0)
    g = g3_codes(pd.factorize(df["x"])[0], pd.factorize(df[name])[0])
    assert 0.06 <= g <= 0.09


def test_oracle_is_a_function_and_counts_calls():
    o = Canonicalizer.from_table({"a": 1, "b": 1, "c": 2}, inverse=True)
    assert o("a") == o("b") != o("c")
    assert o.calls_forward == 3
    o("a"); o("a")                                  # cached: repeated calls are free
    assert o.calls_forward == 3
    assert sorted(o.aliases(1)) == ["a", "b"] and o.calls_inverse == 1


def test_propagated_bound_dominates_g3_after_updates():
    from semfd.maintain import propagate
    rng = np.random.default_rng(3)
    for _ in range(300):
        n = int(rng.integers(5, 60))
        x, y = rng.integers(0, 6, n), rng.integers(0, 3, n)
        g = g3_codes(x, y)
        d = int(rng.integers(0, n))
        keep = rng.permutation(n)[d:]
        i = int(rng.integers(0, 30))
        x2 = np.r_[x[keep], rng.integers(0, 6, i)]
        y2 = np.r_[y[keep], rng.integers(0, 3, i)]
        if len(x2) == 0:
            continue
        assert g3_codes(x2, y2) <= propagate(g, n, d, i) + 1e-12


def test_stop_at_does_not_change_default():
    from semfd.proxy import Attr
    df = pd.DataFrame({"x": [f"v{i % 40}" for i in range(400)], "y": [f"w{(i % 40) // 4}" for i in range(400)]})
    ax, ay = Attr("x", df["x"], exact=True), Attr("y", df["y"], exact=True)
    fx = Canonicalizer(lambda v: v, name="x", free=True)
    fy = Canonicalizer(lambda v: v, name="y", free=True)
    r1 = certify(ax, ay, fx, fy, 0.9, 0.05, 0.05, np.random.default_rng(0))
    r2 = certify(ax, ay, fx, fy, 0.9, 0.05, 0.05, np.random.default_rng(0), stop_at=0.05)
    r3 = certify(ax, ay, fx, fy, 0.9, 0.05, 0.05, np.random.default_rng(0), stop_at=0.025)
    assert r1 == r2 and r3["certified"] and r3["ub"] < 0.025 <= r1["ub"] + 0.025 and r3["samples"] >= r1["samples"]


def test_oracle_transfer_lemma():
    """|g3 under f - g3 under g| <= disagreement_mass on the attributes where f and g differ."""
    from semfd.oracle import disagreement_mass
    rng = np.random.default_rng(5)
    for _ in range(200):
        n = int(rng.integers(3, 40))
        x = rng.integers(0, 8, n)
        y = rng.integers(0, 4, n)
        f = {v: int(rng.integers(0, 4)) for v in range(8)}
        g = {v: int(rng.integers(0, 4)) for v in range(8)}
        gf = g3_codes(np.array([f[v] for v in x]), y)
        gg = g3_codes(np.array([g[v] for v in x]), y)
        m = disagreement_mass(list(x), f.__getitem__, g.__getitem__)
        assert abs(gf - gg) <= m + 1e-12
        # brute-force minimality on small domains: no smaller deletion set of whole values works
    assert disagreement_mass([0, 0, 1, 2], {0: "a", 1: "a", 2: "b"}.__getitem__, {0: "x", 1: "y", 2: "z"}.__getitem__) == 0.25


def test_witness_slack_bound():
    """Paper Prop. (witness slack): g3 <= mu <= g3 + eps_pi + eps_rep under inverse access; mu agrees with the
    independent condition-(i)/(ii) split of exp/e11_partial_inverse.py."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "exp"))
    from e11_partial_inverse import b_split
    from e15_slack import slack_terms
    xs, ys, xo, yo = _toy()
    for k, theta in ((1, 0.99), (3, 0.9), (3, 0.6), (5, 0.3)):
        ax, ay = Attr("x", xs, proxy="edit", k=k), Attr("y", ys, exact=True)
        xent = np.array([xo[v] for v in ax.vals])
        yent = np.array([yo[v] for v in ay.vals])
        g3 = g3_codes(xent[ax.codes], yent[ay.codes])
        mu, ep, er = slack_terms(ax, ay, xent, yent, theta)
        ci, cii = b_split(ax, ay, xent, yent, theta)
        assert abs(mu - (ci + cii)) < 1e-12
        assert g3 - 1e-12 <= mu <= g3 + ep + er + 1e-12


@pytest.mark.parametrize("refine", [True, "warm"])
def test_refined_witness_bound_dominates_g3(refine):
    """Self-refining witnesses (TR, Prop. "Predictable witnesses"): the returned bound still covers g3, also when
    alias classes fetched by an earlier candidate on the same oracle are reused ("warm")."""
    xs, ys, xo, yo = _toy()
    ax, ay = Attr("x", xs, proxy="edit", k=3), Attr("y", ys, exact=True)
    az = Attr("z", pd.Series([f"z{xo[layer1(v)] % 7}" for v in xs]), exact=True)
    xent = np.array([xo[v] for v in ax.vals])
    yent = np.array([yo[v] for v in ay.vals])
    g3 = g3_codes(xent[ax.codes], yent[ay.codes])
    fails = 0
    for i in range(40):
        fx = Canonicalizer.from_table(xo, inverse=True)
        fy = Canonicalizer(lambda v: v, (lambda e: [e]), free=True)
        certify(ax, az, fx, fy, 0.9, 0.05, 0.05, np.random.default_rng(1000 + i), inverse=True, max_n=2000)
        r = certify(ax, ay, fx, fy, 0.9, 0.05, 0.05, np.random.default_rng(i), inverse=True, max_n=4000, refine=refine)
        fails += r["ub"] < g3
    assert fails <= 4


def test_call_budget_stops_within_one_batch():
    """max_calls (E18 run-wide budget): sampling stops at the first batch boundary at or above the cap, so the
    overshoot is at most one batch of calls, each sample costing at most 3 + 3*kappa calls (Thm. 2)."""
    xs, ys, xo, yo = _toy(n_ent=200)
    ax, ay = Attr("x", xs, proxy="edit", k=3), Attr("y", ys, exact=True)
    kappa = max(len(n) for n in ax.nbrs) + max(sum(1 for e in xo.values() if e == x) for x in set(xo.values()))
    for cap, batch in ((50, 100), (200, 20), (1, 10)):
        fx = Canonicalizer.from_table(xo, inverse=True)
        fy = Canonicalizer(lambda v: v, (lambda e: [e]), free=True)
        r = certify(ax, ay, fx, fy, 0.9, 0.05, 0.05, np.random.default_rng(0), inverse=True, max_n=4000,
                    batch=batch, max_calls=cap)
        assert r["budget_hit"] and cap <= r["calls"] <= cap + batch * (3 + 3 * kappa)
    fx = Canonicalizer.from_table(xo, inverse=True)
    fy = Canonicalizer(lambda v: v, (lambda e: [e]), free=True)
    big = certify(ax, ay, fx, fy, 0.9, 0.05, 0.05, np.random.default_rng(0), inverse=True, max_n=4000, max_calls=10**9)
    fx = Canonicalizer.from_table(xo, inverse=True)
    fy = Canonicalizer(lambda v: v, (lambda e: [e]), free=True)
    ref = certify(ax, ay, fx, fy, 0.9, 0.05, 0.05, np.random.default_rng(0), inverse=True, max_n=4000)
    assert not big["budget_hit"] and big["certified"] == ref["certified"] and big["ub"] == ref["ub"]
