"""E15 (paper Sec. III, "Witness slack"): where the gap between E[B] and g3 comes from.

Under inverse access, for the fixed witness of Algorithm 1 (proxy partition pi at theta, representative = most
frequent Layer-1 Y string of the cluster, priority = cluster size), the general witness-slack proposition states
    g3 <= mu <= g3 + eps_pi + eps_rep,
where eps_pi is the fraction of tuples whose X-entity is not "consistent" in pi (some cluster holding its values also
holds another entity's values, or its clusters' representatives are not all one Y-entity r_e), and eps_rep sums,
over consistent X-entities e, the tuples lost because r_e is chosen by string frequency: (m_e - n_e(r_e)) / N, with
m_e the count of e's most frequent Y-entity. Computed exactly over all tuples
(evaluation only, no oracle calls are counted) for every candidate of the E1 curated lists, seed 0, defaults.
Output: results/icde27/e15_slack.json
"""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semfd.certify import g3_codes, witness  # noqa: E402
from semfd.data import LOADERS  # noqa: E402
from semfd.probes import is_probe_fd  # noqa: E402


def slack_terms(ax, ay, xent, yent, theta):
    """Exact mu (complete inverse), eps_pi and eps_rep for X -> Y. xent / yent: entity id per value code."""
    lab, rep, prio = witness(ax, ay, theta)
    n = len(ax.codes)
    tx, ty = xent[ax.codes], yent[ay.codes]
    tl = lab[ax.codes]
    # mu: B(t) = 1 if t[Y] is not oracle-equal to rep(pi(t[X]))  (condition (i)), or condition (ii) fails: some
    # oracle-equal X value lies in a strictly higher-priority cluster whose representative conflicts.
    rep_y = np.array([yent[rep[int(c)]] for c in tl])
    cond_i = ty != rep_y
    best = {}                                   # per X-entity: highest-priority cluster among its values
    for v, e in enumerate(xent):
        c = int(lab[v])
        if e not in best or prio[c] > prio[best[e]]:
            best[e] = c
    # condition (ii) for value v (cluster c): exists v' with same entity, prio(c') > prio(c), rep(c') != rep(c) as entity
    ent_clusters = {}
    for v, e in enumerate(xent):
        ent_clusters.setdefault(e, set()).add(int(lab[v]))
    ii_val = np.zeros(len(xent), bool)
    for v, e in enumerate(xent):
        c = int(lab[v])
        ry = yent[rep[c]] if c in rep else None
        for c2 in ent_clusters[e]:
            if prio[c2] > prio[c] and c2 in rep and yent[rep[c2]] != ry:
                ii_val[v] = True
                break
    mu = float((cond_i | ii_val[ax.codes]).mean())
    # eps_pi: tuples of X-entities that are not consistent (a cluster mixes entities, or reps disagree)
    clus_ents = {}
    for v, c in enumerate(lab):
        clus_ents.setdefault(int(c), set()).add(xent[v])
    exact = {e: all(len(clus_ents[c]) == 1 for c in cs) and len({yent[rep[c]] for c in cs}) == 1
             for e, cs in ent_clusters.items()}
    is_exact_t = np.array([exact[e] for e in tx])
    eps_pi = float((~is_exact_t).mean())
    # eps_rep over exact entities
    eps_rep = 0
    order = np.lexsort((ty, tx))
    sx, sy = tx[order], ty[order]
    b = np.flatnonzero(np.r_[True, sx[1:] != sx[:-1], True])
    for s, e_ in zip(b[:-1], b[1:]):
        e = sx[s]
        if not exact[e]:
            continue
        ys, cnt = np.unique(sy[s:e_], return_counts=True)
        ry = yent[rep[next(iter(ent_clusters[e]))]]
        eps_rep += cnt.max() - (cnt[ys == ry][0] if (ys == ry).any() else 0)
    return mu, eps_pi, eps_rep / n


if __name__ == "__main__":
    out = []
    for name, kw in (("geonames", {"n_cities": 16000}), ("tax", {}), ("ndc", {})):
        ds = LOADERS[name](seed=0, **kw)
        attrs = ds.attrs()
        ent = ds.entity_codes(attrs)
        for x, y in ds.fds:
            if ds.exact[x]:
                continue
            g3 = g3_codes(ent[x][attrs[x].codes], ent[y][attrs[y].codes])
            mu, ep, er = slack_terms(attrs[x], attrs[y], ent[x], ent[y], 0.9)
            out.append({"dataset": name, "fd": f"{x}->{y}", "probe": is_probe_fd(f"{x}->{y}"), "g3": g3, "mu": mu,
                        "eps_pi": ep, "eps_rep": er, "holds": bool(g3 - 1e-12 <= mu <= g3 + ep + er + 1e-12)})
            print(name, f"{x}->{y}", f"g3={g3:.4f} mu={mu:.4f} eps_pi={ep:.4f} eps_rep={er:.4f} holds={out[-1]['holds']}",
                  flush=True)
    (ROOT / "results/icde27/e15_slack.json").write_text(json.dumps(out, indent=1))
