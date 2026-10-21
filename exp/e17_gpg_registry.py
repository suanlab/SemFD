"""E17 (paper Sec. VI, "A second dataset with a real register"): natural aliases in the UK gender pay gap reports
and how much of them the Companies House register returns.

For the employer-name attribute of semfd.data.gpg (oracle = company number), records: companies, spellings,
companies with several spellings; for those, the share of their spellings that the register lists (current or
previous name, Layer-1 match) and the share of spellings with no proxy edge, in either direction, to another spelling
of the same company (hybrid proxy, k=5: aliases the neighbor sets cannot find); the tuple mass covered by registered
spellings; and up to 10 examples of renames. Output: results/icde27/e17_gpg_registry.json
"""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semfd.data import companies_house_names, gpg  # noqa: E402
from semfd.proxy import Attr  # noqa: E402

if __name__ == "__main__":
    ds = gpg()
    reg, fname = companies_house_names()
    ax = Attr("name", ds.df["name"], proxy="hybrid", k=5)
    tab = ds.oracle["name"]
    ent = [tab[v] for v in ax.vals]
    cnt = np.bincount(ax.codes, minlength=len(ax.vals))
    by = {}
    for i, e in enumerate(ent):
        by.setdefault(e, []).append(i)
    nb = [set(map(int, r)) for r in ax.nbrs]
    multi = {e: vs for e, vs in by.items() if len(vs) > 1}
    registered = np.array([ax.vals[i] in reg.get(ent[i], ()) for i in range(len(ax.vals))])
    hidden = np.zeros(len(ax.vals), bool)
    for vs in multi.values():
        for v in vs:
            hidden[v] = all(u not in nb[v] and v not in nb[u] for u in vs if u != v)
    mv = [v for vs in multi.values() for v in vs]
    ex = [sorted(ax.vals[v] for v in vs) for e, vs in multi.items() if any(hidden[v] for v in vs)][:10]
    res = {"register_file": fname, "rows": len(ax.codes), "companies": len(by), "spellings": len(ax.vals),
           "companies_in_register": sum(e in reg for e in by), "multi_spelling_companies": len(multi),
           "multi_spelling_rows": int(sum(cnt[v] for v in mv)),
           "share_spellings_registered_multi": float(np.mean([registered[vs].mean() for vs in multi.values()])),
           "tuple_mass_registered": float(cnt[registered].sum() / cnt.sum()),
           "spellings_without_proxy_edge_multi": int(hidden[mv].sum()), "spellings_multi": len(mv),
           "tuple_mass_without_proxy_edge": float(cnt[hidden].sum() / cnt.sum()),
           "hidden_registered": int((hidden & registered).sum()), "examples_hidden": ex}
    (ROOT / "results/icde27/e17_gpg_registry.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "examples_hidden"}, indent=1), flush=True)
    for e in ex:
        print(e, flush=True)
