"""N1 probe (literature/improvement_plan_2026-10-28.md, item N1): is there a NATURAL candidate on Walmart-Amazon
(DeepMatcher benchmark, gold product matches) where the cross-cluster audit could change a decision?
Probe only, not an experiment: no certification runs. Pass criterion fixed in the plan before running:
some candidate with g3_oracle <= 2*delta and mu_i < delta <= mu (the audit's mass covers the gap to delta).

Brand oracle: union-find over Layer-1 brand strings linked by a gold match (Walmart row ~ Amazon row), so two
spellings are one brand iff some matched product carries both. Unlinked spellings stay singletons (the oracle is
incomplete for unmatched rows; this is recorded, not repaired). Two tables: the 2,308 matched rows, and all rows.
Output: results/icde27/n1_probe_wa.json
"""

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "exp"))
from semfd.certify import g3_codes  # noqa: E402
from semfd.data import Dataset  # noqa: E402
from semfd.proxy import layer1  # noqa: E402
from e11_partial_inverse import b_split  # noqa: E402

DELTA, THETA = 0.05, 0.9


def load():
    A = pd.read_csv(ROOT / "data/wa/tableA.csv", dtype=str, keep_default_na=False)
    B = pd.read_csv(ROOT / "data/wa/tableB.csv", dtype=str, keep_default_na=False)
    M = pd.read_csv(ROOT / "data/wa/matches.csv", dtype=str)
    a = pd.DataFrame({"src": "walmart", "id": "A" + A["custom_id"], "brand": A["brand"], "modelno": A["modelno"],
                      "category": A["groupname"], "price": A["price"]})
    b = pd.DataFrame({"src": "amazon", "id": "B" + B["custom_id"], "brand": B["brand"], "modelno": B["modelno"],
                      "category": B["category1"], "price": B["price"]})
    df = pd.concat([a, b], ignore_index=True)
    df = df[df["brand"].str.strip() != ""].reset_index(drop=True)
    df["modelno"] = df["modelno"].map(lambda s: re.sub(r"[^a-z0-9]", "", s.lower()))
    df["price"] = df["price"].map(lambda s: re.sub(r"[^0-9.]", "", s))
    pairs = [("A" + x, "B" + y) for x, y in zip(M["id1"], M["id2"])]
    return df, pairs


def brand_oracle(df, pairs):
    par = {}
    find = lambda x: x if par.setdefault(x, x) == x else find(par[x])
    br = dict(zip(df["id"], df["brand"].map(layer1)))
    for x, y in pairs:
        if x in br and y in br:
            rx, ry = find(br[x]), find(br[y])
            if rx != ry:
                par[rx] = ry
    return {v: "brand:" + find(v) for v in df["brand"].map(layer1).unique()}


def main():
    df, pairs = load()
    orc = brand_oracle(df, pairs)
    matched = {i for p in pairs for i in p}
    out = {"delta": DELTA, "theta": THETA, "pass_rule": "g3_oracle <= 2 delta and mu_i < delta <= mu", "tables": {}}
    for name, d in (("matched", df[df["id"].isin(matched)].reset_index(drop=True)), ("all", df)):
        cols = ["brand", "modelno", "category", "price"]
        ds = Dataset(f"wa_{name}", d[cols], {c: c != "brand" for c in cols}, {"brand": orc})
        attrs = ds.attrs()
        ent = ds.entity_codes(attrs)
        raw = {c: np.arange(len(attrs[c].vals)) for c in attrs}
        nb = attrs["brand"].vals
        rows = []
        for x in cols:
            for y in cols:
                if x == y or "brand" not in (x, y):
                    continue
                ax, ay = attrs[x], attrs[y]
                g_or = float(g3_codes(ent[x][ax.codes], ent[y][ay.codes]))
                g_raw = float(g3_codes(raw[x][ax.codes], raw[y][ay.codes]))
                ci, cii = b_split(ax, ay, ent[x], ent[y], THETA)
                rows.append({"fd": f"{x}->{y}", "g3_oracle": g_or, "g3_raw": g_raw, "mu_i": ci, "mu": ci + cii,
                             "passes": bool(g_or <= 2 * DELTA and ci < DELTA <= ci + cii)})
                print(name, rows[-1], flush=True)
        out["tables"][name] = {"rows": len(d), "brands_raw": len(nb),
                               "brand_entities": len(set(orc[v] for v in nb)), "candidates": rows}
    out["passes"] = any(r["passes"] for t in out["tables"].values() for r in t["candidates"])
    (ROOT / "results/icde27/n1_probe_wa.json").write_text(json.dumps(out, indent=1))
    print("PASS" if out["passes"] else "FAIL")


if __name__ == "__main__":
    main()
